#btframework

import sys
import itertools
from pymarc import MARCReader #pip install pymarc #http://pypi.python.org/pypi/pymarc/
from pymarc.marcxml import record_to_xml

TEMPLATE_TOP = '''\
<?xml version="1.0" encoding="UTF-8"?>
<marc:collection xmlns:marc="http://www.loc.gov/MARC21/slim">
'''

TEMPLATE_BOTTOM = '''\
</marc:collection>
'''

def marc2marcxml(marcfp, limit=None, out=sys.stdout):
    '''
    Convert a sequence of MARC21 records to one MARCXML document

    python -c "import sys, btframework; btframework.marc2marcxml(sys.stdin, 3)" < HARVARDRECORDS/data/HLOM/ab.bib.01.20120727.full.mrc
    '''
    reader = MARCReader(marcfp)
    if limit is not None:
        reader = itertools.islice(reader, limit)

    print >> out, TEMPLATE_TOP
    for rec in reader:
        print >> out, record_to_xml(rec, namespace=True)
    print >> out, TEMPLATE_BOTTOM

