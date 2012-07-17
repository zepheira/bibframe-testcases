'''
Declarations used to elucidate MARC model
'''

FIELD_RENAMINGS = {
'100a': 'name',
'100d': 'date',
'110a': 'name',
'110d': 'date',
'111a': 'name',
'111d': 'date',
'600a': 'name',
'600d': 'date',
'610a': 'name',
'650a': 'name',
'650d': 'date',
'651a': 'name',
'651d': 'date',
'260a': 'name',
'260b': 'name',
'260c': 'publishedOn',
'260e': 'name',
'260f': 'name',
'260g': 'manufacturerOn',
}


MATERIALIZE = {
'100': ('author', {'marcType': 'Person'}),
'110': ('author', {'marcType': 'Organization'}),
'111': ('author', {'marcType': 'Meeting'}),
'260a': ('publishedAt', {'marcType': 'Place'}),
'260b': ('publisher', {'marcType': 'Organization'}),
'260e': ('manufacturedAt', {'marcType': 'Place'}),
'260f': ('manufacturer', {'marcType': 'Organization'}),
'600': ('subject', {'marcType': 'Person'}),
'610': ('subject', {'marcType': 'Organization'}),
'650': ('subject', {'marcType': 'Topic'}),
'651': ('subject', {'marcType': 'Place'}),
}


DEMATERIALIZE = {
'010a': 'LCCN',
'020a': 'ISBN',
'300a': 'physicalDescription',
'245a': 'title',
'250a': 'edition',
'260c': 'publishedOn',
'500a': 'generalNote',
'520a': 'summary',
'245a': 'title',
'250a': 'edition',
'520a': 'summary',
}


WORK_FIELDS = set([
'010',
'040a',
'041a',
'041b',
'100a',
'100b',
'100c',
'100d',
'100e',
'110a',
'110b',
'110c',
'110d',
'111a',
'111c',
'111d',
'111f',
'130a',
'130d',
'130f',
'130l',
'130h',
'240a',
'240g',
'240d',
'240k',
'240l',
'243a',
'245a',
'245b',
'245c',
'245f',
'245g',
'245k',
'246a',
'246f',
'310a',
'310b',
'362a',
'362z',
'490a',
'500a',
'501a',
'504a',
'505a',
'510a',
'510b',
'510c',
'510u',
'520a',
'520b',
'520c',
'520u',
'521a',
'521b',
'522a',
'600a',
'600c',
'600d',
'600v',
'600x',
'600y',
'600z',
'600e',
'610a',
'610b',
'610c',
'610d',
'610v',
'610x',
'610y',
'610z',
'610e',
'611a',
'611b',
'611c',
'611d',
'611v',
'611x',
'611y',
'611z',
'611e',
'630a',
'630b',
'630c',
'630d',
'630v',
'630x',
'630y',
'630z',
'630e',
'650a',
'650b',
'650c',
'650d',
'650v',
'650x',
'650y',
'650z',
'651a',
'651b',
'651c',
'651d',
'651v',
'651x',
'651y',
'651z',
'700a',
'700b',
'700c',
'700d',
'700e',
'710a',
'710b',
'710c',
'710d',
'711a',
'711c',
'711d',
'711f',
'730a',
'730d',
'730f',
'730l',
'730h',
])

INSTANCE_FIELDS = set([
'020a',
'020c',
'022a',
'050a',
'050b',
'055a',
'055b',
'060a',
'060b',
'070a',
'070b',
'082a',
'082b',
'0822',
'086a',
'245h',
'250a',
'250b',
'260a',
'260b',
'260c',
'260e',
'260f',
'260g',
'300a',
'300b',
'300c',
'300e',
'340a',
'340b',
'340c',
'340d',
'506a',
'506b',
'506c',
'506d',
'506e',
'506f',
'506u',
'850a',
'852a',
'852b',
'852e',
'852h',
'8521',
'856u',
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

