'''
Routines for various data fix-ups & lookups
'''
import urllib, time

import requests # http://docs.python-requests.org/en/latest/index.html
import amara
from amara.lib import U

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


#Getting book covers: & other info
# * http://room329.com/2010/11/how-to-find-a-cover-image-for-a-book-with-an-isbn/
# * http://stackoverflow.com/questions/106963/how-can-i-lookup-data-about-a-book-from-its-barcode-number
# * 

