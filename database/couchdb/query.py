__author__ = 'adrien'
import couchdb

couch = couchdb.Server()

# db = couch.create("test-database")
db = couch["test-database"]

for doc in db.iterview("_design/__main__/_view/hey", 200):
    print(doc)