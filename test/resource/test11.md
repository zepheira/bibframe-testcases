# Header

## label

Model Holdings and Items

## description

(from the BIBFRAME HOLDINGS POINT PAPER USE CASES) Print and electronic objects (sharing an electronic resource with another Legal Deposit library): The British Library holds Print, PDF and HTML copies of a report ‘Support for carers of older people’. The National Library of Scotland does not hold the report itself but as a Legal Deposit library its users are allowed access to the digital copy held in the British Library. On checking the British Library holdings one copy was purchased by the Library and is available for lending via its Document Supply Service while the electronic copies in PDF and HTML format were deposited under the Legal Deposit Act and are only available for reference purposes in the Library’s Reading Room at St Pancras. The PDF copy is available to the National Library of Scotland (and other Legal Deposit Libraries).

## id

test11

## issues

* modeling holdings
* annotations
* inclusion of item class

## tags

* holdings
* annotations
* items

## created

2012-06-20

## status

open

# LanguageMaterial

* id: <http://bnb.data.bl.uk/id/resource/015816022W>
* label: "Support for carers of older people";
* author <http://bnb.data.bl.uk/id/organization/AuditCommission> ;
* bf:classification [a bf:classificationEntity
   bf:class-ddc "353.5372430942" ] ;
* bf:note "Better government for older people"
* bf:note "Public sector national report"
* bf:series "Independence and well-being; 5"
* bf:hasInstance <http://bnb.data.bl.uk/id/resource/015816022Instance1BLprint> ;
* bf:hasInstance <http://bnb.data.bl.uk/id/resource/015816022Instance2BLhtml> ;
* bf:hasInstance <http://bnb.data.bl.uk/id/resource/015816022Instance3BLpdf> .

# Authority

* id: <http://bnb.data.bl.uk/id/organization/AuditCommission>;
* label "Audit Commission for Local Authorities and the National Health Service in England and Wales".

# Instance Volume

* id: <http://bnb.data.bl.uk/id/resource/015816022Instance1BLprint>
* instanceOf: <http://bnb.data.bl.uk/id/resource/015816022W>
* isbn "1862404828"
* extent "71p. ; ill., charts (col.) ; 30cm"
* publication: <http://bnb.data.bl.uk/id/provider/12345>
* hasItem <http://bnb.data.bl.uk/id/resource/015816022Item1BLprint>
* hasItem <http://bnb.data.bl.uk/id/resource/015816022Item2BLprint>

# Event ProviderEntity 

* id: <http://bnb.data.bl.uk/id/provider/12345>
* provider: <http://bnb.data.bl.uk/id/organization/AuditCommission>
* providerPlace "London"
* providerDate "2004"

# Instance Item

* id: <http://bnb.data.bl.uk/id/resource/015816022Item1BLprint>
* itemOf <http://bnb.data.bl.uk/id/resource/015816022Instance1BL> ;
* methodOfAcquisition "Legal Deposit" ;
* physicalCondition "Page 1 missing" ;
* shelfmark "C.199.b.134" ;
* hasHoldingAnnotation <http://bnb.data.bl.uk/id/resource/015816022HoldingAnnotation1BLprint> .

# Annotation Holding

* id: <http://bnb.data.bl.uk/id/resource/015816022HoldingAnnotation1BLprint>
* annotates: <http://bnb.data.bl.uk/id/resource/015816022Item1BLprint> ;
* annotationAssertedBy "British Library" ;
* annotationBody [ 
   bfp:location "British Library" ;
   bfp:subLocation "St Pancras Reading Rooms" ;
   bfp:subLocation "Humanities and Social Sciences" ] .

# Instance Item

* id: <http://bnb.data.bl.uk/id/resource/015816022Item2BLprint>
* itemOf <http://bnb.data.bl.uk/id/resource/015816022Instance1BL>
* methodOfAcquisition "Purchase"
* shelfmark "m06/.34483"
* hasHoldingAnnotation <http://bnb.data.bl.uk/id/resource/015816022HoldingAnnotation2BLprint> .

# Annotation Holdings 

* id: <http://bnb.data.bl.uk/id/resource/015816022HoldingAnnotation2BLprint>
* annotates: <http://bnb.data.bl.uk/id/resource/015816022Item2BLprint>
* annotationAssertedBy: "British Library" ;
* annotationBody [ 
   bfp:location "British Library" ;
   bfp:subLocation "Document Supply Services" ;
   bfp:availability "Available for loan" ;
   bfp:copyrightFee "25.00" ] .

# Instance WebPage 

* id: <http://bnb.data.bl.uk/id/resource/015816022Instance2BLhtml>
* instanceOf: <http://bnb.data.bl.uk/id/resource/015816022W>
* title "Support for carers of older people"
* publication: <http://bnb.data.bl.uk/id/provider/23456>
* note "From title page (viewed 2006)"
* encodingFormat "HTML"
* hasItem <http://bnb.data.bl.uk/id/resource/015816022Item3BLhtml>

# Event ProviderEntity

* id: <http://bnb.data.bl.uk/id/provider/23456>
* provider: <http://bnb.data.bl.uk/id/organization/AuditCommission>
* providerPlace: "London"
* providerDate: "2006"

# Instance Item

* id: <http://bnb.data.bl.uk/id/resource/015816022Item3BLhtml>
* itemOf: <http://bnb.data.bl.uk/id/resource/015816022Instance2BL>
* methodOfAcquisition: "Legal Deposit"
* shelfmark "m06/.34484"
* hasHoldingAnnotation <http://bnb.data.bl.uk/id/resource/015816022HoldingAnnotation3BLonline>

# Annotation Holding

* id: <http://bnb.data.bl.uk/id/resource/015816044H4>
* annotates: <http://bnb.data.bl.uk/id/resource/015816022Instance3BL>
* annotationAssertedBy "National Library of Scotland"
* annotationBody [ 
   bfp:location "National Library of Scotland" ;
   bfp:location "British Library" ;
   bfp:accessRestrictions "Single user, single LDL" ] .
