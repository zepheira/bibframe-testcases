'''
readmarcml - the main MARCXML parser, produces the base layer of JSON
'''
#take a MARCXML file, interprets its records, and does some augmentation, creating multiple Exhibit JSON files

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


#SLUGCHARS = r'a-zA-Z0-9\-\_'
#OMIT_FROM_SLUG_PAT = re.compile('[^%s]'%SLUGCHARS)
#OMIT_FROM_SLUG_PAT.sub('_', t).lower().decode('utf-8')
#slug_from_title = lambda t: OMIT_FROM_SLUG_PAT.sub('_', t).lower().decode('utf-8')

FALINKFIELD = u'856u'
CATLINKFIELD = u'010a'
CACHEDIR = os.path.expanduser('~/tmp')

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
        doc = amara.parse(url)
        answer = U(doc.xml_select(u'/rss/channel/item/link'))
        print >> sys.stderr, answer
        time.sleep(5) #Be polite!
        return answer
    return lucky_viaf


#FORGET IT LUCKY GOOGLE IS DEAD!
#http://code.google.com/p/google-ajax-apis/issues/detail?id=43#c103
def lucky_google_template(qfunc):
    def lucky_google(item):
        q = qfunc(item)
        query = urllib.urlencode({'q' : q})
        url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&' + query
        print >> sys.stderr, url
        json_content = json.load(urllib.urlopen(url))
        results = json_content['responseData']['results']
        answer = results[0]['url'].encode('utf-8') + '\n'
        time.sleep(5) #Be polite!
        return answer
    return lucky_google


AUGMENTATIONS = {
    #('600', ('a', 'd'), lucky_google_template(lambda item: 'site:viaf.org {0}, {1}'.format(item['a'], item['d'])), u'viaf_guess'), #VIAF Cooper, Samuel, 1798-1876
    ('600', ('a', 'd'), lucky_viaf_template(lambda item: 'cql.any all "{0}, {1}"'.format(item['a'].encode('utf-8'), item['d'].encode('utf-8'))), u'viaf_guess'), #VIAF Cooper, Samuel, 1798-1876
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
            item[k] = v
            #item[key+code] = sfval

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
            #leader = rec.xml_select(u'ma:leader', prefixes=PREFIXES)

            item = {
                u'id': recid,
                u'label': recid,
                #u'label': u'{0}, {1}'.format(row['TPNAML'], row['TPNAMF']),
                u'leader': leader,
                u'type': u'MarcRecord',
            }
            for cf in rec.xml_select(u'ma:controlfield', prefixes=PREFIXES):
                key = u'cftag_' + U(cf.xml_select(u'@tag'))
                val = U(cf)
                if list(cf.xml_select(u'ma:subfield', prefixes=PREFIXES)):
                    for sf in cf.xml_select(u'ma:subfield', prefixes=PREFIXES):
                        code = U(sf.xml_select(u'@code'))
                        sfval = U(sf)
                        item[key+code] = sfval
                else:
                    item[key] = val

            for df in rec.xml_select(u'ma:datafield', prefixes=PREFIXES):
                code = U(df.xml_select(u'@tag'))
                key = u'dftag_' + code
                val = U(df)
                if list(df.xml_select(u'ma:subfield', prefixes=PREFIXES)):
                    subid = sfhandler.add(code, ( (U(sf.xml_select(u'@code')), U(sf)) for sf in df.xml_select(u'ma:subfield', prefixes=PREFIXES) ))
                    item.setdefault(key, []).append(subid)
                else:
                    item[key] = val

            #Work out the item's finding aid link
            link = item.get(u'dftag_' + FALINKFIELD)
            if link:
                item['fa_link'] = link
                r = requests.get(link)
                if r.history: #If redirects were encountered
                    resolvedlink = r.history[-1].headers['location']
                    item['fa_resolvedlink'] = resolvedlink

            sink1.send(item)

            item2 = {
                u'id': recid,
                u'label': recid,
                u'type': u'MarcRecord',
            }

            #Work out the item's catalogue link
            lcid = item.get(u'dftag_' + CATLINKFIELD)
            if lcid:
                item2['cat_link'] = 'http://lccn.loc.gov/' + ''.join(lcid.split())

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
