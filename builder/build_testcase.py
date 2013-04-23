#!/usr/bin/env python

import sys
import os
import re

from amara import bindery
from amara.bindery import html
from amara.lib import U, inputsource
from amara.lib.iri import absolutize, matches_uri_syntax

import markdown
import rdflib

TEST_ID_BASE = 'http://bibframe.org/test/'

#markdown.markdown(some_text, extensions=[MyExtension(), 'path.to.my.ext', 'footnotes'])

#CLASSES = {}

TURTLE_TOP_TEMPLATE = u'''@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix bf: <http://bibframe.org/vocab/> .
@prefix identifiers: <http://id.loc.gov/vocabulary/identifiers/> .
@prefix cnt: <http://www.w3.org/2011/content#> .
@prefix dcterms: <http://purl.org/dc/terms/> .

'''

TURTLE_RESOURCE_TEMPLATE = u'''
<{rid}>
'''

def run(text=None, dest=''):
    stem = os.path.splitext(os.path.split(text)[-1])[0]
    text = open(text, 'r').read()
    h = markdown.markdown(text)
    doc = html.markup_fragment(inputsource.text(h.encode('utf-8')))
    #print doc.xml_encode()
    output = TURTLE_TOP_TEMPLATE

    sections = doc.xml_select(u'//h1')
    for sect in sections:
        rtype = U(sect)
        fields = U(sect.xml_select(u'following-sibling::p'))
        fields = dict(map(lambda y: [part.strip() for part in y.split(u':', 1)], fields.split(u'\n')))
        desc = U(sect.xml_select(u'following-sibling::h2[.="Description/following-sibling::p"]'))
        note = U(sect.xml_select(u'following-sibling::h2[.="Note/following-sibling::p"]'))
        rid = absolutize(fields[u'id'], TEST_ID_BASE)
        del fields[u'id']
        atype = None
        output += TURTLE_RESOURCE_TEMPLATE.format(rid=rid)
        if rtype.startswith(u'Annotation'):
            #Derive the actual annotation type
            rtype, atype = rtype.split()
            output += u'    a bf:{atype}, bf:{rtype} ;\n'.format(rtype=rtype, atype=atype)
        else:
            output += u'    a bf:{rtype} ;\n'.format(rtype=rtype)

        #print fields
        for k, v in fields.items():
            if matches_uri_syntax(v):
                output += u'    bf:{k} <{v}> ;\n'.format(k=k, v=v)
            else:
                output += u'    bf:{k} "{v}" ;\n'.format(k=k, v=v)
        output = output.rsplit(u';\n', 1)[0]
        output += u'.\n'

    turtlefname = os.path.join(dest, stem + os.path.extsep + 'turtle')
    turtlef = open(turtlefname, 'w')
    turtlef.write(output)
    turtlef.close()

    g = rdflib.Graph()
    result = g.parse(turtlefname, format='n3')
    print "Generated", len(g), "triples:"
    for stmt in g: print stmt

    return


if __name__ == '__main__':
    from akara.thirdparty import argparse #Import not at top pace PEP8
    #build_testcase.py test/resource/test1.md -d /tmp
    parser = argparse.ArgumentParser()
    #parser.add_argument('testspec', metavar='testspec', type=argparse.FileType('r'),
    #                    help='The test spec')
    parser.add_argument('testspec', metavar='testspec',
                        help='The test spec')
    parser.add_argument('-d', '--dest', metavar="TEST_FILES_DEST", dest="dest", default='.',
                        help="Destination folder for test files")
    args = parser.parse_args()
    run(text=args.testspec, dest=args.dest)
    #indoc = bindery.parse(sys.argv[1])
    #args.testspec.close()

