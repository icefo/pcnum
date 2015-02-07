__author__ = 'adrien'

import datetime
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')

db = client['test-database']

db['posts-collection'].drop()

posts = db['posts-collection']


post = \
[
    {"vuid": 0, 'actor': ['jessica well', 'marion partner'], 'producer': ['mistervilain', 'fatguy'], 'title': "once upon a time"},
    {"vuid": 1, 'actor': ['george waschinton', 'Tom backery'], 'producer': ['fatrichguy', 'fatguy'], 'title': "You're not going away"}
]


post_id = posts.insert(post)

# print(db.collection_names())

for post in posts.find({"actor": {"$regex": "^jes"}, "title": {"$regex": "^Yo"}}):
    print(post)