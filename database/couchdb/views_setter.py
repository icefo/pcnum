from database.couchdb.couchview import CouchView

class CountTypes(CouchView):
    """ Count the number of documents available, per type. """

    @staticmethod
    def map(doc):
        """ Emit the document type for each document. """
        if 'doc_type' in doc:
            yield (doc['doc_type'], 1)

    @staticmethod
    def reduce(keys, values, rereduce):
        """ Sum the values for each type. """
        return sum(values)

class Hey(CouchView):

    @staticmethod
    def map(doc):
        if doc['dcterms:created']:
            yield (doc['dcterms:created'], doc)

couch_views = [
    Hey()
    # Put other view classes here
]

import couchdb

couch = couchdb.Server()

# db = couch.create("test-database")
db = couch["test-database"]

couchdb.design.ViewDefinition.sync_many(db, couch_views, remove_missing=True)