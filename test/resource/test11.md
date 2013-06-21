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
   bf:class-ddc “353.5372430942” ] ;
* bf:note "Better government for older people"
* bf:note "Public sector national report"
* bf:series "Independence and well-being; 5"
* bf:hasInstance <http://bnb.data.bl.uk/id/resource/015816022Instance1BLprint> ;
* bf:hasInstance <http://bnb.data.bl.uk/id/resource/015816022Instance2BLhtml> ;
* bf:hasInstance <http://bnb.data.bl.uk/id/resource/015816022Instance3BLpdf> .

# Authority

* id: <http://bnb.data.bl.uk/id/organization/AuditCommission>;
* label "Audit Commission for Local Authorities and the National Health Service in England and Wales".

# Instance 

* id: <http://bnb.data.bl.uk/id/resource/015816022Instance1BLprint>;
* instanceOf: <http://bnb.data.bl.uk/id/resource/015816022W> ;
* isbn “1862404828” ;
* extent "71p. ; ill., charts (col.) ; 30cm" ;
* publication: http://bnb.data.bl.uk/id/organization/AuditCommission>

bf:carrierType “volume” ;
bfp:hasItem <resource/015816022Item1BLprint> ;
bfp:hasItem <resource/015816022Item2BLprint>  .

# 

 [a bf:ProviderEntity ;
   bf:providerName "Audit Commission" ; 
   bf:providerPlace "London"  ; 
   bf:providerDate "2004"  ] ;






# Annotation Holdings

* id: <http://library.local.org/annotation/i1>
* annotates: <http://bibframe.org/examples/shusterman/test001/i1>
* assertedBy: <http://library.local.org/people/mary>
* date: 2013-05-30

