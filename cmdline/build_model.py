#!/usr/bin/env python

import sys
import os
import re

from amara import bindery
from amara.lib import U

LINK_PAT = re.compile('@(\w+)')

T0 = '''<!DOCTYPE html>
<html lang="en">
  
  <head>
    <title>MARC21 :: Link Data Vocabulary</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <link href="{base}/css/bootstrap.css" rel="stylesheet" />
    <link href="{base}/css/bootstrap-responsive.css" rel="stylesheet" />
    <link href="{base}/css/style.css" rel="stylesheet" />
    
    <script type="text/javascript" src="{base}/js/jquery.js"></script>
    <script type="text/javascript" src="{base}/js/bootstrap-modal.js"></script>
    
    <script type="text/javascript">
      $('#myModal').modal(options)
    </script>
    
  </head>
  
  <body>
    
    <div class="navbar navbar-fixed-top">

      <div class="navbar-inner">

        <div class="container">
          <a class="brand" href="#">MARC21 Linked Data
            <span class="tagline">
              <span style="padding-left: 20px; font-size: 70%; color: grey;">Vocabulary Navigator</span>
            </span>
          </a> 
      
          <ul class="nav pull-right">
            <li class="active"><a href="#">Browse</a></li>
            <li><a href="#">Contribute</a></li>
            <li class="divider-vertical"></li>
            <li>
              <form class="navbar-search pull-right">
                <input type="text" class="search-query" placeholder="Search Vocabulary">
              </form>
            </li>
          </ul>
          
        </div>

      </div>
    </div>
    
    <div class="body container-fluid">

      <div class="this-nav row-fluid">
        <div class="span12" style="margin-top: 50px;">
          <ul class="breadcrumb">
{breadcrumbs}
          </ul>
        </div>
      </div>

      <div class="this row-fluid">
    <div class="span12">
      <h1 class="this-name">{clslabel}</h1>
      <h3 class="this-description">{clstag}</h3>
      <br />
    </div>
      </div>

      <div class="vocabulary-display">

{tables}

      </div> <!-- vocabulary-display -->

      <div class="specific-types-display">

        <div class="row-fluid">
         <div class="span12">

          <h3 class="specific-types-text">More specific types</h3>

      <ul class="list">
{specifictypes}
      </ul>
      
    </div>

  </div>

      </div> <!-- specific-types-display -->

    </div> <!-- container-fluid -->
    
    <div class="footer">
      <div class="container">
        <p>MARCR.org is a joint effort of <a href = "http://loc.gov/">US Library of Congress</a> and <a href="http://zepheira.com/">Zepheira</a></p>
      </div>
    </div>

  </body>
</html>
'''#.format(vocabulary_display_sections)


T1 = '''        <div class="row-fluid vocabulary-display-section">
      
      <div class="span12">
        
        <div class="section-text parent">{0}</div>
        
        <table class="table table-striped table-bordered">
          <thead>
                <tr>
        <th class="span2">Property</th>
        <th class="span2">Expected Value</th>
        <th class="span6">Description</th>
        <th class="span2">Related MARC Code</th>
        <th class="span2">Related RDA Code</th>
                </tr>
          </thead>
              <tbody>

{1}

              </tbody>
            </table>
        
      </div> <!-- span12 -->
      
    </div> <!-- vocabulary-display-section -->
'''#.format(properties)


T2 = '''\
            <tr>
          <td>{0}</td>
          <td>{1}</td>
          <td>{2}</td>
          <td>{3}</td>
          <td>{4}</td>
            </tr>
'''


CLASSES = {}

def run(modelsource=None, output=None, base=''):
    indoc = bindery.parse(modelsource)
    #Build a graph of the classes
    for cls in indoc.model.class_:
        CLASSES[cls.id] = (cls, U(cls.isa).split() if cls.isa else [])

    #Now fix up all the parents, replacing IDs with the actual XML
    for clsid, (cls, parents) in CLASSES.items():
        parents = [ CLASSES[p][0] for p in parents ]
        CLASSES[clsid] = (cls, parents)

    def handle_inline_links(text):
        '''
        A transform that takes inline links and expamnds them
        '''
        def replace(match):
            eid = match.group(1)
            return '<a href="{0}/{1}/index.html">{2}</a>'.format(base, eid, CLASSES[eid][0].label)
        return LINK_PAT.sub(replace, text)


    #Now build the pages
    for clsid, (maincls, parents) in CLASSES.items():
        ancestors = []
        def add_ancestors(cls):
            for p in CLASSES[cls.id][1]:
                add_ancestors(p)
            ancestors.append(cls)
            return
        add_ancestors(maincls)
        basedir = os.path.join(output, U(maincls.id).encode('utf-8'))
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        outf = open(os.path.join(basedir, 'index.html'), 'w')

        class_chunks = []
        breadcrumb_chunks = []
        #for outcls in ancestors + [maincls]:
        for outcls in ancestors:
            property_chunks = []
            for prop in outcls.property:
                typedesc = handle_inline_links(U(prop.typedesc))
                description = handle_inline_links(U(prop.description))
                property_chunks.append(T2.format(
                    U(prop.label),
                    typedesc,
                    description,
                    U(prop.marcref),
                    U(prop.rdaref)))

            header = 'Properties from <A href="../{0}/index.html">{1}</a>'.format(U(outcls.id), U(outcls.label))
            class_chunks.append(T1.format(header, ''.join(property_chunks)))
            if outcls == maincls:
                breadcrumb_chunks.append('<li class="active">{0}</li>'.format(U(outcls.label)))
            else:
                breadcrumb_chunks.append('<li><a href="../{0}/index.html">{1}</a> <span class="divider">/</span></li>'.format(U(outcls.id), U(outcls.label)))

        childclasses = [ cls for (clsid, (cls, parents)) in CLASSES.items() if maincls in parents ]

        specific_chunks = [ '<li><a href="../{0}/index.html">{1}</a></li>\n'.format(U(cls.id), U(cls.label)) for cls in childclasses ]

        outf.write(T0.format(
            base=base,
            breadcrumbs=''.join(breadcrumb_chunks),
            clslabel=maincls.label,
            clstag=maincls.tagline,
            tables=''.join(class_chunks),
            specifictypes=(''.join(specific_chunks if specific_chunks else '(None)')),
            ))

        outf.close()


from akara.thirdparty import argparse #Yes! Yes! Import not at top

if __name__ == '__main__':
    #build_model.py --base=/vocab bibframe.xml /tmp/bibframe
    parser = argparse.ArgumentParser()
    #parser.add_argument('-o', '--output')
    parser.add_argument('model', metavar='source', type=argparse.FileType('r'),
                        help='The model file')
    parser.add_argument('output_root', metavar='output_base',
                        help='Root directory for the output (will be created if not present)')
    parser.add_argument('-b', '--base', metavar="SITE_BASE_URL", dest="baseurl", default='',
                        help="Base URL for the generated site")
    args = parser.parse_args()
    run(modelsource=args.model, output=args.output_root, base=args.baseurl)
    #indoc = bindery.parse(sys.argv[1])
    args.model.close()

