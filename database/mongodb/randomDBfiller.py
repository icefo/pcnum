# Create the random data
from faker import Factory
import random
from datetime import datetime
fake = Factory.create('fr_FR')
# seed to get always the same random data
fake.seed(4321)
# create the vuid (video unique identifier)
counter = 0

dublin_random_list = []
for _ in range(0, 4000):
    bla = datetime.now().replace(microsecond=0).isoformat()
    dublin_random =\
        {   "dc:identifier": counter,
            "dc:rights": "usage libre pour l'éducation",
            "dc:source": "VHS",
            "dc:type": "video",
            "dcterms:modified": bla,
            'dc:contributor': [fake.name(), fake.name(), fake.name()],
            'dc:creator': fake.name(),
            'dc:description': fake.text(max_nb_chars=200),
            'dcterms:abstract': fake.text(max_nb_chars=50),
            'dcterms:created': fake.random_int(min=1900, max=2010),
            'dc:format': {"size_ratio": "4/3", "duration": fake.random_int(min=20, max=320)},
            'dc:language': random.choice(("en", "fr")),
            'dc:publisher': fake.company(),
            'dc:subject': [fake.sentence(nb_words=6, variable_nb_words=True), fake.sentence(nb_words=6, variable_nb_words=True)],
            'dc:title': fake.sentence(nb_words=3, variable_nb_words=True),
            'files_path': {"h264": "/random/path"}
        }
    dublin_random_list.append(dublin_random)
    counter += 1

from pymongo import MongoClient, ASCENDING

client = MongoClient("mongodb://localhost:27017/")

db = client['metadata']

db['metadata'].drop()

videos_metadata = db['videos_metadata_collection']

dicto =\
    {
        "dc:rights": "usage libre pour l'éducation",
        "dc:source": "VHS",
        "dc:type": "image",
        "dcterms:modified": "$currentDate",
        'dc:contributor': fake.name(),
        'dc:creator': fake.name(),
        'dc:description': fake.text(max_nb_chars=200),
        'dcterms:abstract': fake.text(max_nb_chars=50),
        'dcterms:created': fake.random_int(min=1900, max=2010),
        'dc:format': {"size_ratio": "4/3", "duration": fake.random_int(min=20, max=320)},
        'dc:language': random.choice(("en", "fr")),
        'dc:publisher': fake.company(),
        'dc:subject': [fake.sentence(nb_words=6, variable_nb_words=True), fake.sentence(nb_words=6, variable_nb_words=True)],
        'dc:title': fake.sentence(nb_words=3, variable_nb_words=True)
    }

# I'm just terribly lazy; this create an index for all the fields
for key in dicto.keys():
    db['videos_metadata_collection'].create_index([(key, ASCENDING )])

db['videos_metadata_collection'].create_index([("dc:identifier", ASCENDING )], unique=True)


# Insert the metadata in the database
videos_metadata.insert(dublin_random_list)

print(videos_metadata.find({'dc:description': {"$regex": ".*consequatur.*"}, 'dc:language': "fr"}).explain())

for post in videos_metadata.find({'dc:description': {"$regex": ".*consequatur.*"}, 'dc:language': "fr"}):
    print(post)