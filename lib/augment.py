'''
Routines for various data fix-ups & lookups
'''
import urllib, time, sys

#import requests # http://docs.python-requests.org/en/latest/index.html
#import requests_cache # pip install requests_cache
import amara
from amara.thirdparty import httplib2, json
from amara.lib import U

#requests_cache.configure(os.path.join(CACHEDIR, 'cache'))

CACHEDIR = '/tmp/.cache'

H = httplib2.Http(CACHEDIR)
H.follow_all_redirects = True

VIAF_GUESS_FNAME = u'viafFromHeuristic'
IDLC_GUESS_FNAME = u'idlcFromHeuristic'


def lucky_viaf_template(qfunc):
    '''
    Used for searching OCLC for VIAF records
    '''
    def lucky_viaf(item):
        q = qfunc(item)
        query = urllib.urlencode({'query' : q, 'maximumRecords': 1, 'httpAccept': 'application/rss+xml'})
        url = 'http://viaf.org/viaf/search?' + query
        #print >> sys.stderr, url
        #r = requests.get(url)
        #doc = amara.parse(r.content)
        response, content = H.request(url, 'GET')
        doc = amara.parse(content)
        answer = U(doc.xml_select(u'/rss/channel/item/link'))
        #print >> sys.stderr, answer
        if not response.fromcache:
            time.sleep(2) #Be polite!
        return answer
    return lucky_viaf


def lucky_idlc_template(qpattern):
    '''
    Used for searching OCLC for VIAF records
    '''
    if not callable(qpattern):
        qpattern = lambda item, qp=qpattern: qp.format(**dict([ (k, v.encode('utf-8')) for k, v in item.iteritems() ]))

    def lucky_idlc(item):
        q = qpattern(item)
        query = urllib.quote(q)
        url = 'http://id.loc.gov/authorities/label/' + query
        #r = requests.head(url)
        #print >> sys.stderr, url, item[u'code']
        #answer = r.headers['X-URI']
        #print >> sys.stderr, answer
        response, content = H.request(url, 'HEAD')
        answer = response['x-uri'] #['X-URI']
        if not response.fromcache:
            time.sleep(2) #Be polite! Kevin Ford says 1-2 secs pause is OK
        return answer
    return lucky_idlc


def lucky_idlc_org_template(qpattern):
    '''
    Used for searching OCLC for VIAF records
    '''
    if not callable(qpattern):
        qpattern = lambda item, qp=qpattern: qp.format(**dict([ (k, v.encode('utf-8')) for k, v in item.iteritems() ]))

    def lucky_idlc(item):
        q = qpattern(item)
        query = urllib.quote(q)
        url = 'http://id.loc.gov/vocabulary/organizations/{0}.html'.format(query)
        response, content = H.request(url, 'HEAD')
        #answer = response['x-uri'] #['X-URI']
        #r = requests.head(url)
        #print >> sys.stderr, url, item[u'code']
        #answer = r.headers['X-URI']
        answer = response['x-uri'] #['X-URI']
        #print >> sys.stderr, answer
        if not response.fromcache:
            time.sleep(2) #Be polite! Kevin Ford says 1-2 secs pause is OK
        return answer
    return lucky_idlc


def lucky_viaf_template(qpattern):
    '''
    Used for searching OCLC for VIAF records
    '''
    if not callable(qpattern):
        qpattern = lambda item, qp=qpattern: qp.format(**dict([ (k, v.encode('utf-8')) for k, v in item.iteritems() ]))

    def lucky_viaf(item):
        q = qpattern(item)
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


def finding_aid_lookup_template(qpattern):
    '''
    Used for searching OCLC for VIAF records
    '''
    if not callable(qpattern):
        qpattern = lambda item, qp=qpattern: qp.format(**dict([ (k, v.encode('utf-8')) for k, v in item.iteritems() ]))

    def lucky_viaf(item):
        #Work out the item's finding aid link
        link = work_item.get(u'dftag_' + FALINKFIELD)
        if link:
            work_item['fa_link'] = link

            r = requests.get(link)
            if r.history: #If redirects were encountered
                resolvedlink = r.history[-1].headers['location']
                work_item['fa_resolvedlink'] = resolvedlink




#Getting book covers: & other info
# * http://room329.com/2010/11/how-to-find-a-cover-image-for-a-book-with-an-isbn/
# * http://stackoverflow.com/questions/106963/how-can-i-lookup-data-about-a-book-from-its-barcode-number
# * 

#The list of augmentations patterns to be applied to each record

#(  u'600', - the MARC data field code to be applied to these augmentations
#   (u'subject', u'date'), - the trigger properties for the lookup.  Only performed if all these are present. Use the BTFramework vocab name
#   lucky_google_template(lambda item: 'site:viaf.org {0}, {1}'.format(item['a'], item['d'])), - the lookup function or URL reference template used for the lookup
#   u'viaf_guess'), #the property name to be used to reference the result of this lookup

DEFAULT_AUGMENTATIONS = {
    #('600', ('a', 'd'), lucky_google_template(lambda item: 'site:viaf.org {0}, {1}'.format(item['a'], item['d'])), u'viaf_guess'), #VIAF Cooper, Samuel, 1798-1876

    #First the easy ones
    ('600', ('label', 'date'), lucky_viaf_template('cql.any all "{label}, {date}"'), VIAF_GUESS_FNAME), #VIAF Cooper, Samuel, 1798-1876
    ('852', ('code',), lucky_idlc_org_template('{code}'), IDLC_GUESS_FNAME),

    #These need some extra preprocessing for successful lookup in ID.LOC.GOV, so are a bit more complex
    ('600', ('label', 'date'), lucky_idlc_template(lambda item: '{0}{1}'.format(item['label'].encode('utf-8'), item['date'].rstrip('.').encode('utf-8'))), IDLC_GUESS_FNAME),
    ('100', ('label', 'date'), lucky_idlc_template(lambda item: '{0}{1}'.format(item['label'].encode('utf-8'), item['date'].rstrip('.').encode('utf-8'))), IDLC_GUESS_FNAME),
    ('110', ('label', 'date'), lucky_idlc_template(lambda item: '{0}{1}'.format(item['label'].encode('utf-8'), item['date'].rstrip('.').encode('utf-8'))), IDLC_GUESS_FNAME),
    ('111', ('label', 'date'), lucky_idlc_template(lambda item: '{0}{1}'.format(item['label'].encode('utf-8'), item['date'].rstrip('.').encode('utf-8'))), IDLC_GUESS_FNAME),
    ('610', ('label',), lucky_idlc_template(lambda item: item['label'].encode('utf-8')), IDLC_GUESS_FNAME),
    ('611', ('label',), lucky_idlc_template(lambda item: item['label'].encode('utf-8')), IDLC_GUESS_FNAME),
    ('650', ('label',), lucky_idlc_template(lambda item: item['label'].encode('utf-8')), IDLC_GUESS_FNAME),
    ('651', ('label',), lucky_idlc_template(lambda item: item['label'].encode('utf-8')), IDLC_GUESS_FNAME),

    ('700', ('label', 'date'), lucky_idlc_template(lambda item: '{0}{1}'.format(item['label'].encode('utf-8'), item['date'].rstrip('.').encode('utf-8'))), IDLC_GUESS_FNAME),
    ('710', ('label', 'date'), lucky_idlc_template(lambda item: '{0}{1}'.format(item['label'].encode('utf-8'), item['date'].rstrip('.').encode('utf-8'))), IDLC_GUESS_FNAME),
    ('711', ('label', 'date'), lucky_idlc_template(lambda item: '{0}{1}'.format(item['label'].encode('utf-8'), item['date'].rstrip('.').encode('utf-8'))), IDLC_GUESS_FNAME),

}
#852a': ('institution
