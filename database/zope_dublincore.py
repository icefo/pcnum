__author__ = 'adrien'


# taken fom zope.dublincore
name_to_element = {
# unqualified DCMES 1.1
"Title": ("dc:title", ""),
"Creator": ("dc:creator", ""),
"Subject": ("dc:subject", ""),
"Description": ("dc:description", ""),
"Publisher": ("dc:publisher", ""),
"Contributor": ("dc:contributor", ""),
"Date": ("dc:date", "dcterms:"),
"Type": ("dc:type", ""),
"Format": ("dc:format", ""),
"Identifier": ("dc:identifier", ""),
"Source": ("dc:source", ""),
"Language": ("dc:language", ""),
"Relation": ("dc:relation", ""),
"Coverage": ("dc:coverage", ""),
"Rights": ("dc:rights", ""),
# qualified DCMES 1.1 (directly handled by Zope)
"Date.Created": ("dcterms:created", "dcterms:"),
"Date.Modified": ("dcterms:modified", "dcterms:"),
# qualified DCMES 1.1 (not used by Zope)
"Audience": ("dcterms:audience", ""),
"Audience.Education Level": ("dcterms:educationLevel", ""),
"Audience.Mediator": ("dcterms:mediator", ""),
"Coverage.Spatial": ("dcterms:spatial", ""),
"Coverage.Temporal": ("dcterms:temporal", ""),
"Date.Accepted": ("dcterms:accepted", "dcterms:"),
"Date.Available": ("dcterms:available", "dcterms:"),
"Date.Copyrighted": ("dcterms:copyrighted","dcterms:"),
"Date.Issued": ("dcterms:issued", "dcterms:"),
"Date.Submitted": ("dcterms:submitted", "dcterms:"),
"Date.Valid": ("dcterms:valid", "dcterms:"),
"Description.Abstract": ("dcterms:abstract", ""),
"Description.Table Of Contents": ("dcterms:tableOfContents", ""),
"Format": ("dc:format", ""),
"Format.Extent": ("dcterms:extent", ""),
"Format.Medium": ("dcterms:medium", ""),
"Identifier.Bibliographic Citation": ("dcterms:bibliographicCitation", ""),
"Relation.Is Version Of": ("dcterms:isVersionOf", ""),
"Relation.Has Version": ("dcterms:hasVersion", ""),
"Relation.Is Replaced By": ("dcterms:isReplacedBy", ""),
"Relation.Replaces": ("dcterms:replaces", ""),
"Relation.Is Required By": ("dcterms:isRequiredBy", ""),
"Relation.Requires": ("dcterms:requires", ""),
"Relation.Is Part Of": ("dcterms:isPartOf", ""),
"Relation.Has Part": ("dcterms:hasPart", ""),
"Relation.Is Referenced By": ("dcterms:isReferencedBy", ""),
"Relation.References": ("dcterms:references", ""),
"Relation.Is Format Of": ("dcterms:isFormatOf", ""),
"Relation.Has Format": ("dcterms:hasFormat", ""),
"Relation.Conforms To": ("dcterms:conformsTo", ""),
"Rights.Access Rights": ("dcterms:accessRights", ""),
"Title.Alternative": ("dcterms:alternative", ""),
}


dcterm_list = []

for value in name_to_element.values():
    dcterm_list.append(value[0])
    #print(value[0])

dcterm_list.sort()
counter = 0
for item in dcterm_list:
    if counter == 5:
        print("'",item,"'", ", ", sep="")
        counter = 0
    else:
        print("'",item,"'", end=", ",sep="")
    counter += 1