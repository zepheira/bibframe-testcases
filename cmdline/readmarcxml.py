#!/usr/bin/env python
'''
readmarcml - the main MARCXML parser, produces the base layer of JSON
'''
#take a MARCXML file, interprets its records, and does some augmentation, creating multiple Exhibit JSON files

#Authority files: http://en.wikipedia.org/wiki/Authority_control

import re
import os
import time
import logging
import string
import itertools

import requests # http://docs.python-requests.org/en/latest/index.html
import requests_cache # pip install requests_cache

import amara
from amara.lib.util import coroutine
from amara.thirdparty import httplib2, json
from amara.lib import U
from amara.lib.util import element_subtree_iter

from btframework.marc import *
from btframework.marcspecialfields import canonicalize_isbns, process_leader, process_008
from btframework.augment import lucky_viaf_template, lucky_idlc_template, DEFAULT_AUGMENTATIONS

#SLUGCHARS = r'a-zA-Z0-9\-\_'
#OMIT_FROM_SLUG_PAT = re.compile('[^%s]'%SLUGCHARS)
#OMIT_FROM_SLUG_PAT.sub('_', t).lower().decode('utf-8')
#slug_from_title = lambda t: OMIT_FROM_SLUG_PAT.sub('_', t).lower().decode('utf-8')

FALINKFIELD = u'856u'
#CATLINKFIELD = u'010a'
CATLINKFIELD = u'LCCN'
CACHEDIR = os.path.expanduser('~/tmp')

requests_cache.configure(os.path.join(CACHEDIR, 'cache'))

NON_ISBN_CHARS = re.compile(u'\D')

def invert_dict(d):
    #http://code.activestate.com/recipes/252143-invert-a-dictionary-one-liner/#c3
    #See also: http://pypi.python.org/pypi/bidict
        #Though note: http://code.activestate.com/recipes/576968/#c2
    inv = {}
    for k, v in d.iteritems():
        keys = inv.setdefault(v, [])
        keys.append(k)
    return inv

#One of the records gives us:

#http://hdl.loc.gov/loc.mss/eadmss.ms009216

#Which links for METS download to:

#http://hdl.loc.gov/loc.mss/eadmss.ms009216.4

#Which redirects to:

#http://findingaids.loc.gov/mastermets/mss/2009/ms009216.xml

PREFIXES = {u'ma': 'http://www.loc.gov/MARC21/slim', u'me': 'http://www.loc.gov/METS/'}

#RSS1_PREFIXES = {u'rss': ''}


def dcxml2json(source):
    import amara
    try:
        doc = amara.parse(source)
    except:
        print >> sys.stderr, source
        raise
    elems = element_subtree_iter(doc)
    elems.next() #Discard top-level DC element
    for elem in elems:
        yield elem.xml_local, U(elem)

#ISBNNU_PAT = 'http://isbn.nu/{0}.xml'
ISBNNU_PAT = 'http://isbn.nu/{0}'
OPENLIBRARY_COVER_PAT = 'http://covers.openlibrary.org/b/isbn/{0}-M.jpg'
#http://catalog.hathitrust.org/api/volumes/brief/json/isbn:0030110408 -> http://catalog.hathitrust.org/Record/000578050

class subobjects(object):
    def __init__(self, exhibit_sink):
        self.ix = 0
        self.exhibit_sink = exhibit_sink
        return

    def add(self, props, sink=None):
        sink = sink or self.exhibit_sink
        objid = 'obj_' + str(self.ix + 1)
        code = props[u'code']
        item = {
            u'id': objid,
            u'label': objid,
            u'type': 'Object',
        }
        for k, v in props.items():
            #Try to substitute Marc field code names with friendlier property names
            lookup = code + k
            if lookup in FIELD_RENAMINGS:
                subst = FIELD_RENAMINGS[lookup]
                k = subst

            #print >> sys.stderr, lookup, k
            item[k] = v
            #item[key+code] = sfval

        for (acode, aparams, afunc, key) in DEFAULT_AUGMENTATIONS:
            #if code == acode: print >> sys.stderr, (item, aparams)
            if code == acode and all(( item.get(p) for p in aparams )):
                #Meets the criteria for this augmentation
                val = afunc(item)
                if val is not None: item[key] = val

        sink.send(item)
        self.ix += 1
        print >> sys.stderr, '.',
        return objid


        #Work out the item's catalogue link
        lcid = item.get(CATLINKFIELD)
        if code == '010' and lcid:
            item['catLink'] = 'http://lccn.loc.gov/' + ''.join(lcid.split())



#def records2json(recs, work_sink, instance_sink, stub_sink, objects_sink, annotations_sink, logger=logging):
def records2json(recs, work_sink, instance_sink, objects_sink, annotations_sink, logger=logging):
    '''
    
    '''
    subobjs = subobjects(objects_sink)
    @coroutine
    def receive_items():
        '''
        Receives each record and processes it by creating an item
        dict which is then forwarded to the sink
        '''
        ix = 1
        while True:
            rec = yield
            recid = u'_' + str(ix)

            leader = U(rec.xml_select(u'ma:leader', prefixes=PREFIXES))
            work_item = {
                u'id': u'work' + recid,
                u'label': recid,
                #u'label': u'{0}, {1}'.format(row['TPNAML'], row['TPNAMF']),
                u'type': u'WorkRecord',
            }

            #Instance starts with same as work, with leader added
            instance_item = {
                u'leader': leader,
            }
            instance_item.update(work_item)
            instance_item[u'id'] = u'instance' + recid
            instance_item[u'type'] = u'InstanceRecord'
            work_item[u'instance'] = u'instance' + recid

            for cf in rec.xml_select(u'ma:controlfield', prefixes=PREFIXES):
                key = u'cftag_' + U(cf.xml_select(u'@tag'))
                val = U(cf)
                if list(cf.xml_select(u'ma:subfield', prefixes=PREFIXES)):
                    for sf in cf.xml_select(u'ma:subfield', prefixes=PREFIXES):
                        code = U(sf.xml_select(u'@code'))
                        sfval = U(sf)
                        #For now assume all leader fields are instance level
                        instance_item[key + code] = sfval
                else:
                    #For now assume all leader fields are instance level
                    instance_item[key] = val

            for df in rec.xml_select(u'ma:datafield', prefixes=PREFIXES):
                code = U(df.xml_select(u'@tag'))
                key = u'dftag_' + code
                val = U(df)
                if list(df.xml_select(u'ma:subfield', prefixes=PREFIXES)):
                    subfields = dict(( (U(sf.xml_select(u'@code')), U(sf)) for sf in df.xml_select(u'ma:subfield', prefixes=PREFIXES) ))
                    lookup = code
                    #See if any of the field codes represents a reference to an object which can be materialized
                    handled = False
                    if code in MATERIALIZE:
                        (subst, extra_props) = MATERIALIZE[code]
                        props = {u'code': code}
                        props.update(extra_props)
                        #props.update(other_properties)
                        props.update(subfields)
                        #work_item[FIELD_RENAMINGS.get(code, code)] = subid
                        subid = subobjs.add(props)
                        if code in INSTANCE_FIELDS:
                            instance_item.setdefault(subst, []).append(subid)
                        elif code in WORK_FIELDS:
                            work_item.setdefault(subst, []).append(subid)

                        handled = True

                    if code in MATERIALIZE_VIA_ANNOTATION:
                        (subst, extra_object_props, extra_annotation_props) = MATERIALIZE_VIA_ANNOTATION[code]
                        object_props = {u'code': code}
                        object_props.update(extra_object_props)
                        #props.update(other_properties)

                        #Separate annotation subfields from object subfields
                        object_subfields = subfields.copy()
                        annotation_subfields = {}
                        for k, v in object_subfields.items():
                            if code+k in ANNOTATIONS_FIELDS:
                                annotation_subfields[k] = v
                                del object_subfields[k]

                        object_props.update(object_subfields)
                        objectid = subobjs.add(object_props)

                        annid = u'annotation' + recid
                        annotation_item = {
                            u'id': annid,
                            u'label': recid,
                            subst: objectid,
                            #u'type': u'Annotation',
                        }
                        annotation_item.update(extra_annotation_props)
                        annotation_item.update(annotation_subfields)

                        annotations_sink.send(annotation_item)
                        print >> sys.stderr, '.',

                        if code in INSTANCE_FIELDS:
                            instance_item.setdefault('annotation', []).append(annid)
                        elif code in WORK_FIELDS:
                            work_item.setdefault('annotation', []).append(annid)
                        
                        #The actual subfields go to the annotations sink
                        #annotations_props = {u'annotates': instance_item[u'id']}
                        #annotations_props.update(props)
                        #subid = subobjs.add(annotations_props, annotations_sink)
                        #The reference is from the instance ID
                        #instance_item.setdefault(subst, []).append(subid)

                        handled = True



                        #work_item.setdefault(FIELD_RENAMINGS.get(code, code), []).append(subid)

                    #See if any of the field+subfield codes represents a reference to an object which can be materialized
                    if not handled:
                        for k, v in subfields.items():
                            lookup = code + k
                            if lookup in MATERIALIZE:
                                (subst, extra_props) = MATERIALIZE[lookup]
                                props = {u'code': code, k: v}
                                props.update(extra_props)
                                #print >> sys.stderr, lookup, k, props, 
                                subid = subobjs.add(props)
                                if lookup in INSTANCE_FIELDS or code in INSTANCE_FIELDS:
                                    instance_item.setdefault(subst, []).append(subid)
                                elif lookup in WORK_FIELDS or code in WORK_FIELDS:
                                    work_item.setdefault(subst, []).append(subid)
                                handled = True

                            else:
                                field_name = u'dftag_' + lookup
                                if lookup in FIELD_RENAMINGS:
                                    field_name = FIELD_RENAMINGS[lookup]
                                #Handle the simple field_nameitution of a label name for a MARC code
                                if lookup in INSTANCE_FIELDS or code in INSTANCE_FIELDS:
                                    instance_item.setdefault(field_name, []).append(v)
                                elif lookup in WORK_FIELDS or code in WORK_FIELDS:
                                    work_item.setdefault(field_name, []).append(v)


                #print >> sys.stderr, lookup, key
                elif not handled:
                    if code in INSTANCE_FIELDS:
                        instance_item[key] = val
                    elif code in WORK_FIELDS:
                        work_item[key] = val
                else:
                    if code in INSTANCE_FIELDS:
                        instance_item[key] = val
                    elif code in WORK_FIELDS:
                        work_item[key] = val

            #link = work_item.get(u'cftag_008')


            #Work out the item's finding aid link
            link = work_item.get(u'dftag_' + FALINKFIELD)
            if link:
                work_item['fa_link'] = link
                r = requests.get(link)
                if r.history: #If redirects were encountered
                    resolvedlink = r.history[-1].headers['location']
                    work_item['fa_resolvedlink'] = resolvedlink


            #Handle ISBNs re: https://foundry.zepheira.com/issues/1976
            new_instances = []

            isbns = instance_item.get('isbn', [])
            def isbn_list(isbns):
                isbn_tags = {}
                for isbn in isbns:
                    parts = isbn.split(None, 1)
                    #Remove any cruft from ISBNs. Leave just the digits
                    cleaned_isbn = NON_ISBN_CHARS.subn(u'', parts[0])[0]
                    if len(parts) == 1:
                        #FIXME: More generally strip non-digit chars from ISBNs
                        isbn_tags[cleaned_isbn] = None
                    else:
                        isbn_tags[cleaned_isbn] = parts[1]
                c14ned = canonicalize_isbns(isbn_tags.keys())
                for c14nisbn, variants in invert_dict(c14ned).items():
                    #We'll use the heuristic that the longest ISBN number is the best
                    variants.sort(key=len, reverse=True) # sort by descending length
                    yield variants[0], isbn_tags[variants[0]]
                return# list(isbnset)

            base_instance_id = instance_item[u'id']
            instance_ids = []
            subscript = ord(u'a')
            for subix, (inum, itype) in enumerate(isbn_list(isbns)):
                #print >> sys.stderr, subix, inum, itype
                subitem = instance_item.copy()
                subitem[u'isbn'] = inum
                subitem[u'id'] = base_instance_id + (unichr(subscript + subix) if subix else u'')
                if itype: subitem[u'isbnType'] = itype
                instance_ids.append(subitem[u'id'])
                new_instances.append(subitem)
                isbnnu_url = ISBNNU_PAT.format(inum)
                #q = qfunc(item)
                #print >> sys.stderr, url
                #r = requests.get(url)
                #doc = amara.parse(r.content)
                #print >> sys.stderr, answer
                subitem[u'isbnnu'] = isbnnu_url
                #U(doc.xml_select(u'/rss/channel/item/link'))
                subitem[u'openlibcover'] = OPENLIBRARY_COVER_PAT.format(inum)
                #time.sleep(2) #Be polite!

                #instance_item[u'isbn'] = isbns[0]

            if not new_instances:
                #Make sure it's created as an instance even if it has no ISBN
                new_instances.append(instance_item)
                instance_ids.append(base_instance_id)

            work_item[u'instance'] = instance_ids

            special_properties = {}
            for k, v in process_leader(leader):
                special_properties.setdefault(k, set()).add(v)

            for k, v in process_008(instance_item[u'cftag_008']):
                special_properties.setdefault(k, set()).add(v)

            #We get some repeated values out of leader & 008 processing, and we want to
            #Remove dupes so we did so by working with sets then converting to lists
            for k, v in special_properties.items():
                special_properties[k] = list(v)

            instance_item.update(special_properties)

            #reduce lists of just one item
            for k, v in work_item.items():
                if type(v) is list and len(v) == 1:
                    work_item[k] = v[0]
            work_sink.send(work_item)

            def send_instance(instance):
                for k, v in instance.items():
                    if type(v) is list and len(v) == 1:
                        instance[k] = v[0]
                instance_sink.send(instance)

            for ninst in new_instances:
                send_instance(ninst)

            #stub_item = {
            #    u'id': recid,
            #    u'label': recid,
            #    u'type': u'MarcRecord',
            #}

            #stub_sink.send(stub_item)
            ix += 1
            print >> sys.stderr, '+',

        return

    target = receive_items()

    for rec in recs:
        #target.send(map(string.strip, row))
        target.send(rec)

    target.close()
    return

#NO LONGER USED
#Handlers for various resolved links

class loc_findingaids(object):
    def match(self, uri):
        return uri.startswith('http://findingaids.loc.gov') and eadmss in uri

    def __call__(self, uri):
        '''
        Extract data/metadata from the uri
        '''
        return data


from datachef.exhibit import emitter

if __name__ == "__main__":
    #python readmarcxml.py sample-files.xml lcsample
    #python -m btframework.marccuncher sample-files.xml /tmp/lcsample

    import sys
    indoc = amara.parse(sys.argv[1])
    name_base = sys.argv[2]
    work_outf = open(name_base + '.work.json', 'w')
    instance_outf = open(name_base + '.instance.json', 'w')
    #stub_outf = open(name_base + '.stub.json', 'w')
    objects_outf = open(name_base + '.object.json', 'w')
    annotations_outf = open(name_base + '.annotations.json', 'w')

    work_emitter = emitter.emitter(work_outf)
    instance_emitter = emitter.emitter(instance_outf)
    #stub_emitter = emitter.emitter(stub_outf)
    objects_emitter = emitter.emitter(objects_outf)
    annotations_emitter = emitter.emitter(annotations_outf)

    recs = indoc.xml_select(u'/ma:collection/ma:record', prefixes=PREFIXES)

    #outf = open(name_base + '.json', 'w')
    if len(sys.argv) > 3:
        count = int(sys.argv[3])
        recs = itertools.islice(recs, count)

    #records2json(recs, work_emitter, instance_emitter, stub_emitter, objects_emitter, annotations_emitter)
    records2json(recs, work_emitter, instance_emitter, objects_emitter, annotations_emitter)
    work_emitter.send(emitter.ITEMS_DONE_SIGNAL)
    instance_emitter.send(emitter.ITEMS_DONE_SIGNAL)
    #stub_emitter.send(emitter.ITEMS_DONE_SIGNAL)
    objects_emitter.send(emitter.ITEMS_DONE_SIGNAL)
    annotations_emitter.send(emitter.ITEMS_DONE_SIGNAL)

    #emitter.send(TYPES1)
    work_emitter.send(None)
    instance_emitter.send(None)
    #stub_emitter.send(None)
    objects_emitter.send(None)
    annotations_emitter.send(None)
    work_emitter.close()
    instance_emitter.close()
    #stub_emitter.close()
    objects_emitter.close()
    annotations_emitter.close()
    #print >> sys.stderr, requests_cache.get_cache()
