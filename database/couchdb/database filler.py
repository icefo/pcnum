
# Create the random data
import couchdb
from faker import Factory
import random
from datetime import datetime

couch = couchdb.Server()

couch.delete("test-database")

db = couch.create("test-database")

fake = Factory.create('fr_FR')
# seed to get always the same random data
fake.seed(4321)
# create the vuid (video unique identifier)
counter = 0

dublin_random_list = []

for _ in range(0, 4000):
    bla = datetime.now().replace(microsecond=0).isoformat()
    dublin_random =\
        {   "_id": str(counter),
            "dc:identifier": str(counter),
            "dc:rights": "usage libre pour l'éducation",
            "dc:source": "VHS",
            "dc:type": "video",
            "dcterms:modified": bla,
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
    dublin_random_list.append(dublin_random)
    counter += 1

for status in db.update(dublin_random_list):
    print(status)