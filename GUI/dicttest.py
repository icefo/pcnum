__author__ = 'adrien'

# mam = {'dc:stuff': {"contain": ['eyyyyyyyyyyyyyyyyyyyyy']} }
# search_dict = {}
# dc_combobox_text = "dc:stuff"
# query_type = "contain"
# data_widget_text_value = "eyyyyyyyyyyyyyyyyyyyyy"
#
#
# if "bla" is not "":
#     try:
#         search_dict[dc_combobox_text][query_type].append(data_widget_text_value)
#     except KeyError:
#         try:
#             search_dict[dc_combobox_text][query_type] = [data_widget_text_value]
#         except KeyError:
#             search_dict[dc_combobox_text] = {query_type: [data_widget_text_value]}
#
# print(search_dict)

dico = {'dcterms:accessRights': {'contain': ['ycyxyxc']}, 'dc:description': {'equal': ['asdasd\nas\nd\nad']}, 'dc:date': {'equal': ['09 avr 2015']}}

# {'dc:subject': {"$regex": ".*consequatur.*"}, 'dc:language': "fr"}

eyy = {}

for dc_items, dict_query in dico.items():
    print(dc_items, dict_query)
    for query_type, query in dict_query.items():
        if query_type == "equal":
            eyy[dc_items] = query[0]
        elif query_type == "contain":
            eyy[dc_items] = {"$regex": ".*" + query[0] + ".*"}

print(eyy)

