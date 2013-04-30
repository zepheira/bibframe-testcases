#!/usr/bin/env python

import sys
import os
import re
import itertools

from amara import bindery
from amara.bindery import html
from amara.lib import U, inputsource
from amara.lib.iri import absolutize, matches_uri_syntax
from amara.thirdparty import json

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


HTML_RAPTOR_TEMPLATE = u'''<body>
  <table id="triples" border="1">
    <tr>
      <th>Subject</th>
      <th>Predicate</th>
      <th>Object</th>
    </tr>
    {0}
  </table>
</body>
</html>
'''


HTML_TRIPLE_TEMPLATE = u'''
    <tr class="triple">
      {0}
    </tr>
'''


def run(text=None, dest=''):
    stem = os.path.splitext(os.path.split(text)[-1])[0]
    text = open(text, 'r').read()
    h = markdown.markdown(text.decode('utf-8'))
    doc = html.markup_fragment(inputsource.text(h.encode('utf-8')))
    #print doc.xml_encode()
    output = TURTLE_TOP_TEMPLATE

    #The top section contains all the test metadata
    testinfofname = os.path.join(dest, stem + os.path.extsep + 'json')
    testinfof = open(testinfofname, 'w')
    top_section_fields = U(doc.xml_select(u'//h1/preceding-sibling::p'))
    fields = dict(map(lambda y: [part.strip() for part in y.split(u':', 1)], top_section_fields.split(u'\n')))
    testinfo = fields
    json.dump(testinfo, testinfof, indent=4)
    testinfof.close()

    sections = doc.xml_select(u'//h1')
    for sect in sections:
        rtype = U(sect)
        fields = U(sect.xml_select(u'following-sibling::p'))
        fields = dict(map(lambda y: [part.strip() for part in y.split(u':', 1)], fields.split(u'\n')))
        desc = U(sect.xml_select(u'following-sibling::h2[.="Description"]/following-sibling::p'))
        note = U(sect.xml_select(u'following-sibling::h2[.="Note"]/following-sibling::p'))
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

    turtlefname = os.path.join(dest, stem + os.path.extsep + 'ttl')
    turtlef = open(turtlefname, 'w')
    turtlef.write(output)
    turtlef.close()

    g = rdflib.Graph()
    result = g.parse(turtlefname, format='n3')

    rdfxfname = os.path.join(dest, stem + os.path.extsep + 'rdf')
    rdfxf = open(rdfxfname, 'w')
    g.serialize(rdfxf, format='xml')
    rdfxf.close()

    tbody = ''
    output = HTML_RAPTOR_TEMPLATE.format(tbody)
    htmlfname = os.path.join(dest, stem + os.path.extsep + 'html')
    htmlf = open(htmlfname, 'w')
    for stmt in g:
        tr = ''
        for part in stmt:
            if isinstance(part, rdflib.URIRef):
                tr += '<td><span class="uri"><a href="{0}">{1}</a></span></td>'.format(part, part)
            else:
                tr += '<td><span class="literal"><span class="value">{0}</a></span></span></td>'.format(part)
        output += HTML_TRIPLE_TEMPLATE.format(tr)

        print stmt
    htmlf.write(output)
    htmlf.close()
    #print "Generated", len(g), "triples:"
    #for stmt in g: print stmt

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

