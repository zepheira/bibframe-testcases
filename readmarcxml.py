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

FRIENDLY_FIELD_OLD = {
'010a': 'LCCN',
'020a': 'ISBN',
'100a': ('authorName', {'type': 'Person'}),
'100d': 'date',
'110a': ('authorName', {'type': 'Organization'}),
'110d': 'date',
'111a': ('authorName', {'type': 'Meeting'}),
'111d': 'date',
'300a': 'physicalDescription',
'245a': 'title',
'250a': 'edition',
'260b': ('publisherName', {'type': 'Organization'}),
'260c': 'publishedOn',
'260a': ('publishedAt', {'type': 'Place'}),
'500a': 'generalNote',
'520a': 'summary',
'600a': ('subject', {'type': 'Person'}),
'600d': 'date',
'610a': ('subject', {'type': 'Organization'}),
'610d': 'date',
'650a': ('subject', {'type': 'Topic'}),
'650d': 'date',
'651a': ('subject', {'type': 'Place'}),
'651d': 'date',
}


FRIENDLY_FIELD = {
'010': 'LCCN',
'010a': 'LCCN',
'020': 'ISBN',
'020a': 'ISBN',
'100': 'author',
'100a': ('name', {'marcType': 'Person'}),
'100d': 'date',
'110': 'author',
'110a': ('name', {'marcType': 'Organization'}),
'110d': 'date',
'111': 'author',
'111a': ('name', {'marcType': 'Meeting'}),
'111d': 'date',
'300': 'physicalDescription',
'300a': 'physicalDescription',
'245': 'title',
'245a': 'title',
'250': 'edition',
'250a': 'edition',
'260': 'publisher',
'260b': ('name', {'marcType': 'Organization'}),
'260c': 'publishedOn',
'260a': ('publishedAt', {'marcType': 'Place'}),
'500a': 'generalNote',
'520': 'summary',
'520a': 'summary',
'600': 'subject',
'610': 'subject',
'650': 'subject',
'651': 'subject',
'600a': ('name', {'marcType': 'Person'}),
'600d': 'date',
'610a': ('name', {'marcType': 'Organization'}),
'610d': 'date',
'650a': ('name', {'marcType': 'Topic'}),
'650d': 'date',
'651a': ('name', {'marcType': 'Place'}),
'651d': 'date',
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
        print >> sys.stderr, url
        r = requests.get(url)
        doc = amara.parse(r.content)
        answer = U(doc.xml_select(u'/rss/channel/item/link'))
        print >> sys.stderr, answer
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
        print >> sys.stderr, url
        answer = r.headers['X-URI']
        print >> sys.stderr, answer
        time.sleep(7) #Be polite!
        return answer
    return lucky_idlc


#FORGET IT LUCKY GOOGLE IS DEAD!
#http://code.google.com/p/google-ajax-apis/issues/detail?id=43#c103
def lucky_google_template(qfunc):
    def lucky_google(item):
        q = qfunc(item)
        query = urllib.urlencode({'q' : q})
        url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&' + query
        print >> 'Searching:', sys.stderr, url
        json_content = json.load(urllib.urlopen(url))
        results = json_content['responseData']['results']
        answer = results[0]['url'].encode('utf-8') + '\n'
        time.sleep(5) #Be polite!
        return answer
    return lucky_google


AUGMENTATIONS = {
    #('600', ('a', 'd'), lucky_google_template(lambda item: 'site:viaf.org {0}, {1}'.format(item['a'], item['d'])), u'viaf_guess'), #VIAF Cooper, Samuel, 1798-1876

    ('600', ('name', 'date'), lucky_viaf_template(lambda item: 'cql.any all "{0}, {1}"'.format(item['name'].encode('utf-8'), item['date'].encode('utf-8'))), VIAF_GUESS_FNAME), #VIAF Cooper, Samuel, 1798-1876
    ('600', ('name', 'date'), lucky_idlc_template(lambda item: '{0}{1}'.format(item['name'].encode('utf-8'), item['date'].rstrip('.').encode('utf-8'))), IDLC_GUESS_FNAME), #VIAF Cooper, Samuel, 1798-1876
    ('110', ('name'), lucky_idlc_template(lambda item: '{0}'.format(item['name'].encode('utf-8'), item['date'].rstrip('.').encode('utf-8'))), IDLC_GUESS_FNAME), #VIAF Cooper, Samuel, 1798-1876
}


class subfield_handler(object):
    def __init__(self, exhibit_sink):
        self.ix = 0
        self.exhibit_sink = exhibit_sink
        return

    def add(self, code, pairs):
        objid = 'obj_' + str(self.ix + 1)
        item = {
            u'id': objid,
            u'code': code,
            u'type': 'Object',
        }
        for k, v in pairs:
            #Try to substitute Marc field code names with friendlier property names
            lookup = code+k
            if lookup in FRIENDLY_FIELD:
                subst = FRIENDLY_FIELD[lookup]
                #Handle the simple substitution of a label name for a MARC code
                if type(subst) != str:
                    #Break out the substitution name and the other properties, e.g. type
                    subst, other_properties = subst
                    item.update(other_properties)
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
                item[key] = val

        self.exhibit_sink.send(item)
        self.ix += 1
        return objid


def records2json(recs, sink1, sink2, sink3, logger=logging):
    '''
    
    '''
    sfhandler = subfield_handler(sink3)
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
                    subid = sfhandler.add(code, ( (U(sf.xml_select(u'@code')), U(sf)) for sf in df.xml_select(u'ma:subfield', prefixes=PREFIXES) ))
                    #Try to substitute Marc field code names with friendlier property names
                    lookup = code
                    if lookup in FRIENDLY_FIELD:
                        subst = FRIENDLY_FIELD[lookup]
                        #Handle the simple substitution of a label name for a MARC code
                        key = subst
                    print >> sys.stderr, lookup, key
                    item.setdefault(key, []).append(subid)
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
