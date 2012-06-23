'''
augment_lccn - augments the base layer of JSON, adding to each record what it can glean from Dublin Core sourced at lccn.log.gov

'''
#lccn_decorator - takes an Exhibit JSON with LCCN URLs and augments them with the info from that record


import os
import time
import logging
#import urllib
#import string
import itertools

import requests # http://docs.python-requests.org/en/latest/index.html
import requests_cache # pip install requests_cache
from requests.exceptions import ConnectionError

from amara.lib.util import coroutine
from amara.thirdparty import httplib2, json
from amara.lib import U
from amara.lib.util import element_subtree_iter


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



def dcxml2json(source):
    import amara
    try:
        doc = amara.parse(source)
    except Exception as e:
        import traceback; traceback.print_exc(e)
        print >> sys.stderr, source
        raise StopIteration
    elems = element_subtree_iter(doc)
    elems.next() #Discard top-level DC element
    for elem in elems:
        yield elem.xml_local, U(elem)


def records2json(recs, sink, logger=logging):
    '''
    
    '''
    @coroutine
    def receive_items():
        '''
        Receives each record and processes it by creating an item
        dict which is then forwarded to the sink
        '''
        ix = 1
        while True:
            rec = yield

            if rec.get(u'lccn_processing_status') is None:
                rec.get(u'lccn_processing_status')
                catlink = rec.get(u'cat_link')
                if catlink:
                    try:
                        r = requests.get(catlink + '/dc')
                        ecount = {}
                        for k, v in dcxml2json(r.content):
                            #count = ecount.set_default(k, 0)
                            count = ecount.get(k, 0)
                            ecount[k] = count + 1
                            cstr = unicode(count) if count else u''
                            rec[u'dc_' + k + cstr] = v
                        status = r.headers['status']
                        rec[u'lccn_processing_status'] = status if status != "403 Forbidden" else None
                    except requests.exceptions.ConnectionError as e:
                        import traceback; traceback.print_exc(e)
                        rec[u'lccn_processing_status'] = None
                else:
                    rec[u'lccn_processing_status'] = u'UNKNOWN'

            sink.send(rec)
            ix += 1
            print >> sys.stderr, '.',
            #Current LCCN Permalink guidelines do not permit robots and recommend that software programs
            #submit a total of no more than 10 requests per minute, regardless of the number of machines
            #used to submit requests.
            #http://www.loc.gov/homepage/legal.html#security
            time.sleep(7)

        return

    target = receive_items()

    for rec in recs:
        #target.send(map(string.strip, row))
        target.send(rec)

    target.close()
    return


import amara
from datachef.exhibit import emitter

if __name__ == "__main__":
    #python -m btframework.marccuncher sample-files.xml > /tmp/lcsample.json

    import sys

    outf = sys.stdout
    em = emitter.emitter(outf)

    recs = json.load(open(sys.argv[1]))['items']

    #outf = open(name_base + '.json', 'w')
    if len(sys.argv) > 2:
        count = int(sys.argv[2])
        recs = itertools.islice(recs, count)

    records2json(recs, em)
    em.send(emitter.ITEMS_DONE_SIGNAL)

    #emitter.send(TYPES1)
    em.send(None)
    em.close()

