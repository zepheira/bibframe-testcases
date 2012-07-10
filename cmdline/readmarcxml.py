'''
readmarcml - the main MARCXML parser, produces the base layer of JSON
'''
#take a MARCXML file, interprets its records, and does some augmentation, creating multiple Exhibit JSON files

#Authority files: http://en.wikipedia.org/wiki/Authority_control

import re
import os
import time
import logging
import urllib
import string
import itertools

import requests # http://docs.python-requests.org/en/latest/index.html
import requests_cache # pip install requests_cache

import amara
from amara.lib.util import coroutine
from amara.thirdparty import httplib2, json
from amara.lib import U
from amara.lib.util import element_subtree_iter

from btframework.marc import process_leader, process_008

#SLUGCHARS = r'a-zA-Z0-9\-\_'
#OMIT_FROM_SLUG_PAT = re.compile('[^%s]'%SLUGCHARS)
#OMIT_FROM_SLUG_PAT.sub('_', t).lower().decode('utf-8')
#slug_from_title = lambda t: OMIT_FROM_SLUG_PAT.sub('_', t).lower().decode('utf-8')

FALINKFIELD = u'856u'
#CATLINKFIELD = u'010a'
CATLINKFIELD = u'LCCN'
CACHEDIR = os.path.expanduser('~/tmp')

VIAF_GUESS_FNAME = u'viafFromHeuristic'
IDLC_GUESS_FNAME = u'idlcFromHeuristic'

RENAME = {
'100a': 'name',
'100d': 'date',
'110a': 'name',
'110d': 'date',
'111a': 'name',
'111d': 'date',
'600a': 'name',
'600d': 'date',
'610a': 'name',
'650a': 'name',
'650d': 'date',
'651a': 'name',
'651d': 'date',
'260a': 'name',
'260b': 'name',
'260c': 'publishedOn',
'260e': 'name',
'260f': 'name',
'260g': 'manufacturerOn',
}


MATERIALIZE = {
'100': ('author', {'marcType': 'Person'}),
'110': ('author', {'marcType': 'Organization'}),
'111': ('author', {'marcType': 'Meeting'}),
'260a': ('publishedAt', {'marcType': 'Place'}),
'260b': ('publisher', {'marcType': 'Organization'}),
'260e': ('manufacturedAt', {'marcType': 'Place'}),
'260f': ('manufacturer', {'marcType': 'Organization'}),
'600': ('subject', {'marcType': 'Person'}),
'610': ('subject', {'marcType': 'Organization'}),
'650': ('subject', {'marcType': 'Topic'}),
'651': ('subject', {'marcType': 'Place'}),
}


DEMATERIALIZE = {
'010a': 'LCCN',
'020a': 'ISBN',
'300a': 'physicalDescription',
'245a': 'title',
'250a': 'edition',
'260c': 'publishedOn',
'500a': 'generalNote',
'520a': 'summary',
'245a': 'title',
'250a': 'edition',
'520a': 'summary',
}


#These are rules that are applied to materialize one subobject from another
#None for now
TERTIARY_RULES = {
}

requests_cache.configure(os.path.join(CACHEDIR, 'cache'))


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


def lucky_viaf_template(qfunc):
    '''
    Used for searching OCLC for VIAF records
    '''
    def lucky_viaf(item):
        q = qfunc(item)
        query = urllib.urlencode({'query' : q, 'maximumRecords': 1, 'httpAccept': 'application/rss+xml'})
        url = 'http://viaf.org/viaf/search?' + query
        #print >> sys.stderr, url
        r = requests.get(url)
        doc = amara.parse(r.content)
        answer = U(doc.xml_select(u'/rss/channel/item/link'))
        #print >> sys.stderr, answer
        time.sleep(2) #Be polite!
        return answer
    return lucky_viaf


def lucky_idlc_template(qfunc):
    '''
    Used for searching OCLC for VIAF records
    '''
    def lucky_idlc(item):
        q = qfunc(item)
        query = urllib.quote(q)
        url = 'http://id.loc.gov/authorities/label/' + query
        r = requests.head(url)
        #print >> sys.stderr, url, item[u'code']
        answer = r.headers['X-URI']
        #print >> sys.stderr, answer
        time.sleep(2) #Be polite! Kevin Ford says 1-2 secs pause is OK
        return answer
    return lucky_idlc


AUGMENTATIONS = {
    #('600', ('a', 'd'), lucky_google_template(lambda item: 'site:viaf.org {0}, {1}'.format(item['a'], item['d'])), u'viaf_guess'), #VIAF Cooper, Samuel, 1798-1876

    ('600', ('name', 'date'), lucky_viaf_template(lambda item: 'cql.any all "{0}, {1}"'.format(item['name'].encode('utf-8'), item['date'].encode('utf-8'))), VIAF_GUESS_FNAME), #VIAF Cooper, Samuel, 1798-1876
    ('600', ('name', 'date'), lucky_idlc_template(lambda item: '{0}{1}'.format(item['name'].encode('utf-8'), item['date'].rstrip('.').encode('utf-8'))), IDLC_GUESS_FNAME), #VIAF Cooper, Samuel, 1798-1876
    ('100', ('name', 'date'), lucky_idlc_template(lambda item: '{0}{1}'.format(item['name'].encode('utf-8'), item['date'].rstrip('.').encode('utf-8'))), IDLC_GUESS_FNAME), #VIAF Cooper, Samuel, 1798-1876
    ('110', ('name', 'date'), lucky_idlc_template(lambda item: '{0}{1}'.format(item['name'].encode('utf-8'), item['date'].rstrip('.').encode('utf-8'))), IDLC_GUESS_FNAME), #VIAF Cooper, Samuel, 1798-1876
    ('111', ('name', 'date'), lucky_idlc_template(lambda item: '{0}{1}'.format(item['name'].encode('utf-8'), item['date'].rstrip('.').encode('utf-8'))), IDLC_GUESS_FNAME), #VIAF Cooper, Samuel, 1798-1876
    ('610', ('name',), lucky_idlc_template(lambda item: item['name'].encode('utf-8')), IDLC_GUESS_FNAME),
    ('650', ('name',), lucky_idlc_template(lambda item: item['name'].encode('utf-8')), IDLC_GUESS_FNAME),
    ('651', ('name',), lucky_idlc_template(lambda item: item['name'].encode('utf-8')), IDLC_GUESS_FNAME),
}


class subobjects(object):
    def __init__(self, exhibit_sink):
        self.ix = 0
        self.exhibit_sink = exhibit_sink
        return

    def add(self, props):
        objid = 'obj_' + str(self.ix + 1)
        code = props[u'code']
        item = {
            u'id': objid,
            u'type': 'Object',
        }
        for k, v in props.items():
            #Try to substitute Marc field code names with friendlier property names
            lookup = code + k
            if lookup in RENAME:
                subst = RENAME[lookup]
                k = subst

            #print >> sys.stderr, lookup, k
            item[k] = v
            #item[key+code] = sfval

        #Work out the item's catalogue link
        lcid = item.get(CATLINKFIELD)
        if code == '010' and lcid:
            item['catLink'] = 'http://lccn.loc.gov/' + ''.join(lcid.split())


        for (acode, aparams, afunc, key) in AUGMENTATIONS:
            if code == acode and all(( item.get(p) for p in aparams )):
                #Meets the criteria for this augmentation
                val = afunc(item)
                if val is not None: item[key] = val

        self.exhibit_sink.send(item)
        self.ix += 1
        return objid


def records2json(recs, sink1, sink2, sink3, logger=logging):
    '''
    
    '''
    subobjs = subobjects(sink3)
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
            item = {
                u'id': recid,
                u'label': recid,
                #u'label': u'{0}, {1}'.format(row['TPNAML'], row['TPNAMF']),
                u'leader': leader,
                u'type': u'MarcRecord',
            }

            for k, v in process_leader(leader):
                item[k] = v

            for cf in rec.xml_select(u'ma:controlfield', prefixes=PREFIXES):
                key = u'cftag_' + U(cf.xml_select(u'@tag'))
                val = U(cf)
                if list(cf.xml_select(u'ma:subfield', prefixes=PREFIXES)):
                    for sf in cf.xml_select(u'ma:subfield', prefixes=PREFIXES):
                        code = U(sf.xml_select(u'@code'))
                        sfval = U(sf)
                        #item[key+'.'+code] = sfval
                        item[key + code] = sfval
                else:
                    item[key] = val

            for df in rec.xml_select(u'ma:datafield', prefixes=PREFIXES):
                code = U(df.xml_select(u'@tag'))
                key = u'dftag_' + code
                val = U(df)
                if list(df.xml_select(u'ma:subfield', prefixes=PREFIXES)):
                    subfields = dict(( (U(sf.xml_select(u'@code')), U(sf)) for sf in df.xml_select(u'ma:subfield', prefixes=PREFIXES) ))
                    #Try to substitute Marc field code names with friendlier property names
                    lookup = code
                    if lookup in MATERIALIZE:
                        (subst, extra_props) = MATERIALIZE[lookup]
                        props = {u'code': code}
                        props.update(extra_props)
                        #props.update(other_properties)
                        props.update(subfields)
                        subid = subobjs.add(props)
                        #item[RENAME.get(lookup, lookup)] = subid
                        item.setdefault(subst, []).append(subid)
                        #item.setdefault(RENAME.get(lookup, lookup), []).append(subid)

                    for k, v in subfields.items():
                        if lookup+k in MATERIALIZE:
                            (subst, extra_props) = MATERIALIZE[lookup+k]
                            props = {u'code': code, k: v}
                            props.update(extra_props)
                            print >> sys.stderr, lookup, k, props, 
                            subid = subobjs.add(props)
                            item.setdefault(subst, []).append(subid)

                    if lookup in RENAME:
                        subst = RENAME[lookup]
                        #Handle the simple substitution of a label name for a MARC code
                        key = subst

                    for k, v in subfields.items():
                        if lookup+k in DEMATERIALIZE:
                            item[DEMATERIALIZE[lookup+k]] = v

                    #print >> sys.stderr, lookup, key
                else:
                    item[key] = val

            #link = item.get(u'cftag_008')


            #Work out the item's finding aid link
            link = item.get(u'dftag_' + FALINKFIELD)
            if link:
                item['fa_link'] = link
                r = requests.get(link)
                if r.history: #If redirects were encountered
                    resolvedlink = r.history[-1].headers['location']
                    item['fa_resolvedlink'] = resolvedlink

            #reduce lists of just one item
            for k, v in item.items():
                if type(v) is list and len(v) == 1:
                    item[k] = v[0]

            sink1.send(item)

            item2 = {
                u'id': recid,
                u'label': recid,
                u'type': u'MarcRecord',
            }

            sink2.send(item2)
            ix += 1
            print >> sys.stderr, '.',

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
    outf1 = open(name_base + '.base.json', 'w')
    outf2 = open(name_base + '.stub.json', 'w')
    outf3 = open(name_base + '.object.json', 'w')

    emitter1 = emitter.emitter(outf1)
    emitter2 = emitter.emitter(outf2)
    emitter3 = emitter.emitter(outf3)

    recs = indoc.xml_select(u'/ma:collection/ma:record', prefixes=PREFIXES)

    #outf = open(name_base + '.json', 'w')
    if len(sys.argv) > 3:
        count = int(sys.argv[3])
        recs = itertools.islice(recs, count)

    records2json(recs, emitter1, emitter2, emitter3)
    emitter1.send(emitter.ITEMS_DONE_SIGNAL)
    emitter2.send(emitter.ITEMS_DONE_SIGNAL)
    emitter3.send(emitter.ITEMS_DONE_SIGNAL)

    #emitter.send(TYPES1)
    emitter1.send(None)
    emitter2.send(None)
    emitter3.send(None)
    emitter1.close()
    emitter2.close()
    emitter3.close()
