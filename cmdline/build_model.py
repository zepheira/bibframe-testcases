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
    
    <link href="/css/bootstrap.css" rel="stylesheet" />
    <link href="/css/bootstrap-responsive.css" rel="stylesheet" />
    <link href="/css/style.css" rel="stylesheet" />
    
    <script type="text/javascript" src="/js/jquery.js"></script>
    <script type="text/javascript" src="/js/bootstrap-modal.js"></script>
    
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
{0}
          </ul>
        </div>
      </div>

      <div class="this row-fluid">
    <div class="span12">
      <h1 class="this-name">{1}</h1>
      <h3 class="this-description">{2}</h3>
      <br />
    </div>
      </div>

      <div class="vocabulary-display">

{3}

      </div> <!-- vocabulary-display -->

    </div> <!-- container-fluid -->
    
    <div class="footer">
      <div class="container">
        <p>MARCR.org is a joint effort of <a href = "http://loc.gov/">US Library of Congress</a> and <a href="http://zepheira.com/">Zepheira</a></p>
      </div>
    </div>

  </body>
</html>
'''#.format(vocabulary_display_sections)


T1 = '''
            <li><a href="../../index.html">Resource</a> <span class="divider">/</span></li>
            <li><a href="../index.html">Bibliographic</a> <span class="divider">/</span></li>
            <li><a href="../index.html">Physical</a> <span class="divider">/</span></li>
            <li class="active">Cartographic</li>
'''


T2 = '''        <div class="row-fluid vocabulary-display-section">
      
      <div class="span12">
        
        <div class="section-text parent">Properties from <A href = "../../../">Resource</a></div>
        
        <table class="table table-striped table-bordered">
          <thead>
                <tr>
        <th class="span2">Property</th>
        <th class="span2">Expected Value</th>
        <th class="span6">Description</th>
        <th class="span2">Related MARC Code</th>
                </tr>
          </thead>
              <tbody>

{0}

              </tbody>
            </table>
        
      </div> <!-- span12 -->
      
    </div> <!-- vocabulary-display-section -->
'''#.format(properties)


T3 = '''\
            <tr>
          <td>{0}</td>
          <td>{1}</td>
          <td>{2}</td>
          <td>{3}</td>
            </tr>
'''


CLASSES = {}

if __name__ == "__main__":
    #python builder.py bibframe.xml /tmp/bibframe
    indoc = bindery.parse(sys.argv[1])
    name_base = sys.argv[2]

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
            return '<a href"{0}">{1}</a>'.format('../' + eid, CLASSES[eid][0].label)
        return LINK_PAT.sub(replace, text)


    #Now build the pages
    for clsid, (cls, parents) in CLASSES.items():
        ancestors = []
        def add_ancestors(cls):
            for p in CLASSES[cls.id][1]:
                add_ancestors(p)
            ancestors.append(cls)
            return
        add_ancestors(cls)
        basedir = os.path.join(name_base, U(cls.id).encode('utf-8'))
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        outf = open(os.path.join(basedir, 'index.html'), 'w')

        class_chunks = []
        breadcrumb_chunks = []
        #for outcls in ancestors + [cls]:
        for outcls in ancestors:
            property_chunks = []
            for prop in outcls.property:
                typedesc = handle_inline_links(U(prop.typedesc))
                description = handle_inline_links(U(prop.description))
                property_chunks.append(T3.format(
                    U(prop.label),
                    typedesc,
                    description,
                    U(prop.marcref)))

            class_chunks.append(T2.format(''.join(property_chunks)))
            if outcls == cls:
                breadcrumb_chunks.append('<li class="active">{0}</li>'.format(U(outcls.label)))
            else:
                breadcrumb_chunks.append('<li><a href="/{0}/index.html">{1}</a> <span class="divider">/</span></li>'.format(U(outcls.id), U(outcls.label)))

        outf.write(T0.format(''.join(breadcrumb_chunks), cls.label, cls.tagline, ''.join(class_chunks)))

        outf.close()

