from collections import OrderedDict


dc_list = [
    'dc:contributor', 'dc:creator', 'dc:description', 'dc:language', 'dc:publisher',
    'dc:subject', 'dc:title', 'dcterms:abstract', 'dcterms:accessRights',
    'dcterms:isPartOf', 'dcterms:tableOfContents', "dcterms:created"
]
dc_tooltip = ["entrer le nom des personnes ayant contribués au film",
              "maison d'édition, scénariste ou maitre de tournage"]

a = OrderedDict([("hvhuuhv", "bla"), ("bhbi", "blu")])

for b,c in a.items:
    print(b,c)