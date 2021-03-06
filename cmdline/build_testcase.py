#!/usr/bin/env python

import sys
import os
import cgi
#import re
#import itertools
#import copy

#from amara import bindery
from amara.bindery import html
from amara.lib import U, inputsource
from amara.lib.iri import absolutize, matches_uri_syntax
from amara.thirdparty import json

import markdown
import rdflib

# See below
# from rdfextras.tools import rdf2dot
# import pydot
# import codecs

import subprocess
from subprocess import Popen

import time
import random
import base64

from bibframe.testcases.data_path import data_path

TEST_ID_BASE = 'http://bibframe.org/test/'

#markdown.markdown(some_text, extensions=[MyExtension(), 'path.to.my.ext', 'footnotes'])

#CLASSES = {}

TURTLE_TOP_TEMPLATE = u'''@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix bf: <http://bibframe.org/vocab/> .
@prefix bfp: <http://bibframe.org/vocab-proposed/> .
@prefix identifiers: <http://id.loc.gov/vocabulary/identifiers/> .
@prefix cnt: <http://www.w3.org/2011/content#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix btest: <http://bibframe.org/test/> .

'''

TURTLE_RESOURCE_TEMPLATE = u'''
<{rid}>
'''


HTML_RAPTOR_TEMPLATE = u'''<body>
  <table class="table table-striped table-bordered" id="triples">
    <thead>
    <tr>
      <th class="span4">Subject</th>
      <th class="span4">Predicate</th>
      <th class="span4">Object</th>
    </tr>
    </thead>
    <tbody>
    {0}
    </tbody>
  </table>
'''


HTML_TRIPLE_TEMPLATE = u'''
    <tr class="triple">
      {0}
    </tr>
'''

TESTS_LINKS_TEMPLATE = u'''
    <a href="{0}.html">{0}</a>
'''

JSON2BASE64ENCODE = '{"normalized":true,"title":"BIBFRAME :: Test Suite Harness","url":"/tools/tests/","hash":".//tools/tests/index.html?&_suid=%ID%","data":{"components":{"f1":{"type":"facet","state":{"selection":["%F1VAL%"],"selectMissing":false}},"f2":{"type":"facet","state":{"selection":["%F2VAL%"],"selectMissing":false}},"f3":{"type":"facet","state":{"selection":["%F3VAL%"],"selectMissing":false}},"tile-default-0":{"type":"view","state":{"orderedViewFrame":{"orders":[{"property":"label","forward":true,"ascending":true}],"showAll":true,"showDuplicates":false,"grouped":true,"page":0}}},"tests":{"type":"viewPanel","state":{"viewIndex":0}}},"state":1,"lengthy":true},"id":"%ID%","cleanUrl":"/tools/tests/","hashedUrl":"/tools/tests//tools/tests/index.html?&_suid=%ID%"}'
BASE64_LINK = u'''
    <a href="index.html#%BASE64%">%LABEL%</a>
'''

FIELDS_TO_SHRED = [u'tag', u'issues']

HTML_MAIN_TEMPLATE = open(os.path.join(data_path, 'test-template.html')).read().decode('utf-8')


def shred_if_needed(key, value):
    if key in FIELDS_TO_SHRED:
        return [ i.strip() for i in value.split(',') ]
    else:
        return value


#FIXME: Isn't this just itertools.islice?
def results_until(items, end_criteria):
    for node in items:
        if node.xml_select(end_criteria):
            break
        else:
            yield node


def run(sourcefname=None, dest=''):
    index = []
    indexstem = 'index'
    def process_file(fname):
        stem, ext = os.path.splitext(os.path.split(fname)[-1])
        print stem, ext
        text = open(fname, 'r').read()
        if ext == '.ttl':
            from_turtle(text, dest, stem)
        elif ext == '.md':
            turtle, tcinfo = from_markdown(text, dest, stem, index)
            from_turtle(turtle, dest, stem, tcinfo)

    if os.path.isdir(sourcefname):
        files = os.listdir(sourcefname)
        files.sort()
        for fname in files:
            fname = os.path.join(sourcefname, fname)
            print "Processing", fname
            process_file(fname)
    else:
        stem, ext = os.path.splitext(os.path.split(sourcefname)[-1])
        indexstem = stem
        process_file(sourcefname)

    testinfofname = os.path.join(dest, indexstem + os.path.extsep + 'json')
    testinfof = open(testinfofname, 'w')
    json.dump({u'items': index}, testinfof, indent=4)
    testinfof.close()
    return


def from_markdown(md, dest, stem, index):
    h = markdown.markdown(md.decode('utf-8'))
    doc = html.markup_fragment(inputsource.text(h.encode('utf-8')))
    #print doc.xml_encode()
    output = TURTLE_TOP_TEMPLATE
    graphoutput = TURTLE_TOP_TEMPLATE

    #The top section contains all the test metadata
    top_section_fields = results_until(doc.xml_select(u'//h1[1]/following-sibling::h2'), u'self::h1')

    #Note: Top level fields are rendered into dicts, others are turned into lists of tuples
    #fields = dict(map(lambda y: [part.strip() for part in y.split(u':', 1)], U(top_section_fields).split(u'\n')))
    fields = {}
    #subsections = top_section_fields[0].xml_select(u'following-sibling::h2')
    fields["relatedtests"] = ""
    for s in top_section_fields:
        prop = U(s).strip()
        value = s.xml_select(u'./following-sibling::p|following-sibling::ul')
        if value:
            #Encoding to XML makes it a string again, so turn it back to Unicode
            #fields[property] = value[0].xml_encode().decode('utf-8')
            #Use XPath to strip markup
            if value[0].xml_local == u'ul':
                fields[prop] = [ li.xml_select(u'string(.)') for li in value[0].xml_select(u'./li') ]
                if prop == "relatedtests":
                    issues_links = ""
                    for i in fields[prop]:
                        issues_links += TESTS_LINKS_TEMPLATE.format(i) + ", "
                    if issues_links.endswith(', '):
                        issues_links = issues_links[:-2]
                    fields[prop] = issues_links
                elif prop == "issues":
                    issues_links = ""
                    for i in fields[prop]:
                        tid = time.time() + random.randint(1,1000)
                        tid = str(tid).replace('.', '')
                        json = JSON2BASE64ENCODE
                        json = json.replace('%ID', tid)
                        json = json.replace('%F1VAL%', i)
                        json = json.replace('"%F2VAL%"', '')
                        json = json.replace('"%F3VAL%"', '')
                        link = BASE64_LINK
                        link = link.replace('%BASE64%', base64.b64encode(json))
                        link = link.replace('%LABEL%', i)
                        issues_links += link + ", "
                    if issues_links.endswith(', '):
                        issues_links = issues_links[:-2]
                    fields["issueslinks"] = issues_links
                elif prop == "status":
                    issues_links = ""
                    for i in fields[prop]:
                        tid = time.time() + random.randint(1,1000)
                        tid = str(tid).replace('.', '')
                        json = JSON2BASE64ENCODE
                        json = json.replace('%ID', tid)
                        json = json.replace('"%F1VAL%"', '')
                        json = json.replace('"%F2VAL%"', '')
                        json = json.replace('%F3VAL%', i)
                        link = BASE64_LINK
                        link = link.replace('%BASE64%', base64.b64encode(json))
                        link = link.replace('%LABEL%', i)
                        issues_links += link + ", "
                    if issues_links.endswith(', '):
                        issues_links = issues_links[:-2]
                    fields["statuslinks"] = issues_links
            else:
                fields[prop] = value[0].xml_select(u'string(.)')
                # if prop.lower() == "description":
                #    fields["label"] = value[0].xml_select(u'string(.)')
                if prop.lower() == "id":
                    fields["test-id"] = value[0].xml_select(u'string(.)')

    # add fileroot to exhibit json
    fields['fileroot'] = stem

    testinfo = fields.copy()
    #for k, v in testinfo.items():
        #testinfo.append(shred_if_needed(k, v))
    #    testinfo[k] = shred_if_needed(k, v)
    index.append(testinfo)

    #output += TURTLE_RESOURCE_TEMPLATE.format(rid=TEST_ID_BASE + fields[u'id'])
    #output += u'    a bf:TestCase ;\n'
    #for k, v in fields.items():
    #    if matches_uri_syntax(v):
    #        output += u'    bf:{k} <{v}> ;\n'.format(k=k, v=v)
    #    else:
    #        output += u'    bf:{k} "{v}" ;\n'.format(k=k, v=v)
    #output = output.rsplit(u';\n', 1)[0]
    #output += u'.\n'

    sections = doc.xml_select(u'//h1[not(.="Header")]')
    for sect in sections:
        rtype = U(sect)
        #fields = U(sect.xml_select(u'following-sibling::p'))
        field_list = sect.xml_select(u'following-sibling::ul')[0]
        fields = []
        #fields = map(lambda y: [part.strip() for part in y.split(u':', 1)], fields.split(u'\n'))
        for li in field_list.xml_select(u'./li'):
            if U(li).strip():
                prop, val = [ part.strip() for part in U(li.xml_select(u'string(.)')).split(u':', 1) ]
                fields.append((prop, val))

        subsections = results_until(sect.xml_select(u'./following-sibling::h2'), u'self::h1')
        for s in subsections:
            prop = U(s).strip()
            value = s.xml_select(u'./following-sibling::p|following-sibling::ul')
            #print (prop, value)
            if value:
                #Encoding to XML makes it a string again, so turn it back to Unicode
                #fields[property] = value[0].xml_encode().decode('utf-8')
                #Use XPath to strip markup
                if value[0].xml_local == u'ul':
                    fields.append((prop, [ U(li.xml_select(u'string(.)')) for li in value[0].xml_select(u'./li') ]))
                else:
                    fields.append((prop, U(value[0].xml_select(u'string(.)'))))

        #desc = U(sect.xml_select(u'following-sibling::h2[.="Description"]/following-sibling::p'))
        #note = U(sect.xml_select(u'following-sibling::h2[.="Note"]/following-sibling::p'))
        to_remove = []
        for k, v in fields:
            if k == u'id':
                rid = absolutize(v, TEST_ID_BASE)
                to_remove.append((k, v))
        for pair in to_remove:
            fields.remove(pair)
        atype = None
        output += TURTLE_RESOURCE_TEMPLATE.format(rid=rid)
        if ' ' in rtype:
            #Derive the actual annotation type
            rtype, atype = rtype.split()
            output += u'    a bf:{atype}, bf:{rtype} ;\n'.format(rtype=rtype, atype=atype)
        else:
            output += u'    a bf:{rtype} ;\n'.format(rtype=rtype)

        #print fields
        for k, v in fields:
            if matches_uri_syntax(v):
                output += u'    bf:{k} <{v}> ;\n'.format(k=k, v=v)
            elif v.startswith("["):
                output += u'    bf:{k} {v} ;\n'.format(k=k, v=v)
            else:
                output += u'    bf:{k} "{v}" ;\n'.format(k=k, v=v)
        output = output.rsplit(u';\n', 1)[0]
        output += u'.\n'
        
        # Create RDf that only includes resource-resource relations
        # for graphical display
        graphoutput += TURTLE_RESOURCE_TEMPLATE.format(rid=rid)
        #print fields
        for k, v in fields:
            if matches_uri_syntax(v):
                graphoutput += u'    bf:{k} <{v}> ;\n'.format(k=k, v=v)
            elif v.startswith("["):
                graphoutput += u'    bf:{k} {v} ;\n'.format(k=k, v=v)
        graphoutput = graphoutput.rsplit(u';\n', 1)[0]
        graphoutput += u'.\n'

    turtlefname = os.path.join(dest, stem + os.path.extsep + 'ttl')
    turtlef = open(turtlefname, 'w')
    turtlef.write(output.encode('utf-8'))
    turtlef.close()
    
    eyecandyfname = os.path.join(dest, stem + "-eyecandy" + os.path.extsep + 'ttl')
    eyecandyf = open(eyecandyfname, 'w')
    eyecandyf.write(graphoutput.encode('utf-8'))
    eyecandyf.close()
    
    #Copying testinfo because from_turtle will modify it in place
    return output, testinfo.copy()


def from_turtle(turtle, dest, stem, tcinfo):
    tcinfo['turtle'] = cgi.escape(turtle)
    tcinfo['stem'] = stem.decode('utf-8')
    tcinfo['dest'] = dest.decode('utf-8')
    g = rdflib.Graph()
    result = g.parse(data=turtle, format='n3')

    rdfxfname = os.path.join(dest, stem + os.path.extsep + 'rdf')
    rdfxf = open(rdfxfname, 'w')
    g.serialize(rdfxf, format='xml')
    rdfxf.close()
    tcinfo['rdf'] = cgi.escape(open(rdfxfname).read()).decode('utf-8')

    # The below totally works, but not what I was expecting.
    # Resulting visualization is just CRAAAAAZY!
    # But, who knows, perhaps there is something that could be done
    #try:
    #    dotfname = os.path.join(dest, stem + os.path.extsep + 'dot')
    #    # dotf = open(dotfname, 'w')
    #    dotf = codecs.open(dotfname, "w", "utf-8")
    #    rdf2dot.rdf2dot(g, dotf)
    #    dotf.close()
    #xcept:
    #    print 'PROBLEM CREATING dot FILE FOR ' + stem

    #try:
    #    pngfname = os.path.join(dest, stem + os.path.extsep + 'png')
    #    dot = pydot.graph_from_dot_file(dotfname)
    #    dot.write_png(pngfname)
    #except:
    #    print 'PROBLEM CREATING png FROM dot FILE FOR ' + stem

    eyecandyfname = os.path.join(dest, stem + "-eyecandy" + os.path.extsep + 'ttl')
    dotfname = os.path.join(dest, stem + os.path.extsep + 'dot')
    rapperCmd = "rapper -i turtle -o dot " + eyecandyfname + " > " + dotfname
    print rapperCmd
    xresult, xerrors = Popen([rapperCmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()

    pngfname = os.path.join(dest, stem + os.path.extsep + 'png')
    dotCmd = "dot -Tpng " + dotfname + " > " + pngfname
    print dotCmd
    xresult, xerrors = Popen([dotCmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()

    tbody = ''
    for stmt in g:
        tr = ''
        for part in stmt:
            if isinstance(part, rdflib.URIRef):
                tr += u'<td><span class="uri"><a href="{0}">{1}</a></span></td>'.format(part, part)
            else:
                tr += u'<td><span class="literal"><span class="value">{0}</a></span></span></td>'.format(part)
        tbody += HTML_TRIPLE_TEMPLATE.format(tr)

        print stmt

    output = HTML_RAPTOR_TEMPLATE.format(tbody)

    tcinfo['html'] = output
    htmlfname = os.path.join(dest, stem + os.path.extsep + 'html')
    htmlf = open(htmlfname, 'w')

    htmlf.write(HTML_MAIN_TEMPLATE.format(**tcinfo).encode('utf-8'))
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
                        help='Test spec file, or a directory with only such files')
    parser.add_argument('-d', '--dest', metavar="TEST_FILES_DEST", dest="dest", default='.',
                        help="Destination folder for test files")
    args = parser.parse_args()
    run(sourcefname=args.testspec, dest=args.dest)
    #indoc = bindery.parse(sys.argv[1])
    #args.testspec.close()

