__author__ = 'adrien'

import datetime
from pymongo import MongoClient, ASCENDING

client = MongoClient('mongodb://localhost:27017/')

db = client['test-database']

# db['videos'].drop()

videos_metadata = db['videos_metadata']


# videos_metadata.update({"vuid": 0}, {"$set": {"producer": ["Updated !",], "date": "svdv"}})

print(videos_metadata.find({'dc:subject': {"$regex": ".*consequatur.*"}, 'dc:language': "fr"}).sort([("dc:format.duration", ASCENDING)]).explain())

for post in videos_metadata.find({'dc:subject': {"$regex": ".*consequatur.*"}, 'dc:language': "fr"}).sort([("dc:format.duration", ASCENDING)]):
    print(post)