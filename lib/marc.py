'''
Declarations used to elucidate MARC model
'''

MATERIALIZE = {
'100a': ('creator', {'marcrType': 'Person'}),
'110a': ('creator', {'marcrType': 'Person'}),
'111a': ('creator', {'marcrType': 'Person'}),

'260a': ('publishedAt', {'marcrType': 'Place'}),
'260b': ('publisher', {'marcrType': 'Organization'}),
'260c': ('publishDate', {'marcrType': 'Temporal'}),
'260e': ('manufacturedAt', {'marcrType': 'Place'}),
'260f': ('manufacturer', {'marcrType': 'Organization'}),
'260g': ('manufactureDate', {'marcrType': 'Temporal'}),
'263a': ('projectedPublicationDate', {'marcrType': 'Temporal'}),

'310b': ('publicationDateFreq', {'marcrType': 'Temporal'}),

'600a': ('subject', {'marcrType': 'Person'}),
'610a': ('subject', {'marcrType': 'Organization'}),
'611a': ('subject', {'marcrType': 'Meeting'}),
'630v': ('subject', {'marcrType': 'Genre'}),
'630h': ('subject', {'marcrType': 'Medium'}),
'630x': ('subject', {'marcrType': 'Topic'}),
'630y': ('subject', {'marcrType': 'Temporal'}),
'630z': ('subject', {'marcrType': 'Place'}),
'650a': ('subject', {'marcrType': 'Topic'}),
'650c': ('subject', {'marcrType': 'Place'}),
'650v': ('subject', {'marcrType': 'Genre'}),
'650x': ('subject', {'marcrType': 'Topic'}),
'650y': ('subject', {'marcrType': 'Temporal'}),
'650z': ('subject', {'marcrType': 'Place'}),
'651a': ('subject', {'marcrType': 'Place'}),
'651v': ('subject', {'marcrType': 'Genre'}),
'651x': ('subject', {'marcrType': 'Topic'}),
'651y': ('subject', {'marcrType': 'Temporal'}),
'651z': ('subject', {'marcrType': 'Topic'}),

'700a': ('creator', {'marcrType': 'Person'}),
'710a': ('creator', {'marcrType': 'Person'}),
'711a': ('creator', {'marcrType': 'Person'}),
}


FIELD_RENAMINGS = {
'010a': 'lccn',
'020a': 'isbn',
'022a': 'issn',
'050a': 'lcCallNumber',
'0503': 'material',
'082a': 'deweyNumber',

'100a': 'name',
'100d': 'date',
'110a': 'name',
'110d': 'date',
'111a': 'name',
'111d': 'date',
'130a': 'uniformTitle',

'222a': 'keyTitle',
'240a': 'uniformTitle',
'243a': 'collectiveUniformTitle',
'245a': 'title',
'247a': 'formerTitle',
'250a': 'edition',
'250b': 'edition',
'254a': 'musicalPresentation',
'255a': 'cartographicMathemiticalData',
'256a': 'computerFilecharacteristics',
'260a': 'name',
'260b': 'name',
'260c': 'publishedOn',
'260e': 'name',
'260f': 'name',
'260g': 'manufacturerOn',

#'300a': 'physicalDescription',
'300a': 'Extent',
'300b': 'physicalDesc',
'300c': 'dimensions',
'300e': 'accompanyingMaterial',
'300f': 'typeOfunit',
'300g': 'size',
'3003': 'materials',
'310a': 'publicationFreq',
'340a': 'physicalSubstance',
'340b': 'dimensions',
'340c': 'materialsApplied',
'340d': 'recordingTechnique',
'340e': 'physicalSupport',
'351a': 'orgazationMethod',
'351b': 'arrangement',
'351c': 'hierarchy',
'3513': 'materialsSpec',

'490a': 'series',

'500a': 'note',
'501a': 'note',
'502a': 'note',
'502b': 'note',
'502c': 'note',
'502d': 'note',
'502g': 'note',
'502o': 'note',
'504a': 'note',
'505a': 'note',
'506a': 'note',
'506b': 'note',
'506c': 'note',
'506u': 'note',
'507a': 'note',
'507b': 'note',
'508a': 'note',
'510a': 'note',
'510b': 'note',
'510c': 'note',
'510u': 'note',
'511a': 'note',
'513a': 'note',
'513b': 'note',
'515a': 'note',
'516a': 'note',
'518a': 'note',
'518d': 'note',
'518o': 'note',
'518p': 'note',
'520a': 'note',
'520b': 'note',
'520c': 'note',
'520u': 'note',
'521a': 'note',
'521b': 'note',
'522a': 'note',
'525a': 'note',
'583a': 'note',

'600a': 'name',
'600d': 'date',
'610a': 'name',
'650a': 'name',
'650d': 'date',
'651a': 'name',
'651d': 'date',
'630a': 'uniformTitle',
'630l': 'language',
}


WORK_FIELDS = set([
'010',
'028',
'035',
'040',
'041',
'100',
'110',
'111',
'111',
'130',
'210',
'222',
'240',
'243',
'245',
'245',
'246',
'247',
'310',
'310',
'321',
'321',
'362',
'490',
'500',
'501',
'502',
'502',
'504',
'505',
'507',
'508',
'510',
'511',
'513',
'515',
'516',
'518',
'520',
'521',
'522',
'525',
'583',
'600',
'610',
'611',
'630',
'650',
'651',
'700',
'710',
'711',
'730',
])


INSTANCE_FIELDS = set([
'020',
'022',
'050',
'055',
'060',
'070',
'082',
'086',
'250',
'254',
'255',
'256',
'257',
'260',
'263',
'300',
'306',
'340',
'351',
'506',
'850',
'852',
'856',
])


def process_leader(leader):
    """
    http://www.loc.gov/marc/marc2dc.html#ldr06conversionrules

    >>> from btframework.marc import process_leader
    >>> list(process_leader('03495cpcaa2200673 a 4500'))
    [('resourceType', 'Collection'), ('resourceType', 'mixed materials'), ('resourceType', 'Collection')]
    """
    broad_06 = dict(
        a="Text",
        c="Text",
        d="Text",
        e="Image",
        f="Image",
        g="Image",
        i="Sound",
        j="Sound",
        k="Image",
        m="Software",
        p="Collection",
        t="Text")
    
    detailed_06 = dict(
        a="language material",
        c="printed music",
        d="manuscript music",
        e="cartographic material",
        f="manuscript cartographic material",
        g="projected medium",
        i="nonmusical sound recording",
        j="musical sound recording",
        k="2-dimensional nonprojectable graphic",
        m="computer file",
        o="kit",
        p="mixed materials",
        r="3-dimensional artifact or naturally occurring object",
        t="manuscript language material")
    
    _06 = leader[6]
    if _06 in broad_06.keys():
        yield 'resourceType', broad_06[_06]
    if _06 in detailed_06.keys():
        yield 'resourceType', detailed_06[_06]
    if leader[7] in ('c', 's'):
        yield 'resourceType', 'Collection'


def process_008(info):
    """
    http://www.loc.gov/marc/umb/um07to10.html#part9

    >>> from btframework.marc import process_008
    >>> list(process_008('790726||||||||||||                 eng  '))
    [('date', '1979-07-26')]
    """
    audiences = {
        'a':'preschool',
        'b':'primary',
        'c':'pre-adolescent',
        'd':'adolescent',
        'e':'adult',
        'f':'specialized',
        'g':'general',
        'j':'juvenile'}

    media = {
        'a':'microfilm',
        'b':'microfiche',
        'c':'microopaque',
        'd':'large print',
        'f':'braille',
        'r':'regular print reproduction',
        's':'electronic'
        }

    types = {
        "a":"abstracts/summaries",
        "b":"bibliographies (is one or contains one)",
        "c":"catalogs",
        "d":"dictionaries",
        "e":"encyclopedias",
        "f":"handbooks",
        "g":"legal articles",
        "i":"indexes",
        "j":"patent document",
        "k":"discographies",
        "l":"legislation",
        "m":"theses",
        "n":"surveys of literature",
        "o":"reviews",
        "p":"programmed texts",
        "q":"filmographies",
        "r":"directories",
        "s":"statistics",
        "t":"technical reports",
        "u":"standards/specifications",
        "v":"legal cases and notes",
        "w":"law reports and digests",
        "z":"treaties"}
    
    govt_publication = {
        "i":"international or intergovernmental publication",
        "f":"federal/national government publication",
        "a":"publication of autonomous or semi-autonomous component of government",
        "s":"government publication of a state, province, territory, dependency, etc.",
        "m":"multistate government publication",
        "c": "publication from multiple local governments",
        "l": "local government publication",
        "z":"other type of government publication",
        "o":"government publication -- level undetermined",
        "u":"unknown if item is government publication"}

    genres = {
        "0":"not fiction",
        "1":"fiction",
        "c":"comic strips",
        "d":"dramas",
        "e":"essays",
        "f":"novels",
        "h":"humor, satires, etc.",
        "i":"letters",
        "j":"short stories",
        "m":"mixed forms",
        "p":"poetry",
        "s":"speeches"}

    biographical = dict(
        a="autobiography",
        b='individual biography',
        c='collective biography',
        d='contains biographical information')
    
    #info = field008
    #ARE YOU FRIGGING KIDDING ME?! NON-Y2K SAFE?!
    year = info[0:2]
    century = '19' if int(year) > 30 else '20' #I guess we can give an 18 year berth before this breaks ;)
    yield 'date', '{}{}-{}-{}'.format(century, year, info[2:4], info[4:6])
    for i, field in enumerate(info):
        try:
            if i < 23 or field in ('#',  ' ', '|'):
                continue
            elif i == 23:
                yield 'medium', media[info[23]]
            elif i >= 24 and i <= 27:
                yield 'resourceType', types[info[i]]
            elif i == 28:
                yield 'resourceType', govt_publication[info[28]]
            elif i == 29 and field == '1':
                yield 'resourceType', 'conference publication'
            elif i == 30 and field == '1':
                yield 'resourceType', 'festschrift'
            elif i == 33:
                if field != 'u': #unknown
                        yield 'resourceType', genres[info[33]]
            elif i == 34:
                try:
                    yield 'resourceType', biographical[info[34]]
                except KeyError :
                    # logging.warn('something')
                    pass
            else:
                continue
        except KeyError:
            # ':('
            pass

#TODO languages

