from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
from time import sleep
from pymongo import MongoClient, ASCENDING


# use asyncio event loop instead ?

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

# Create server
server = SimpleXMLRPCServer(("localhost", 8000), requestHandler=RequestHandler)
server.register_introspection_functions()


# Register a function under a different name
def launch_digitise(listo):
    print(listo[0])
    sleep(5)
    print(listo[1])
    return "Okayyyyy"

def search(arg):
    db_client = MongoClient('mongodb://localhost:27017/')
    db = db_client['test-database']
    videos_metadata = db['videos_metadata']

    mongo_query = {"$and": []}
    for dc_item, dict_query in arg.items():
        print(dc_item, dict_query)
        for query_type, query in dict_query.items():
            if query_type == "equal":
                for query_item in query:
                    mongo_query["$and"].append({dc_item: {"$regex": query_item, "$options": "i"}})
            elif query_type == "contain":
                for query_item in query:
                    mongo_query["$and"].append({dc_item: {"$regex": ".*" + query_item + ".*", "$options": "i"}})
            elif query_type == "greater":
                mongo_query["$and"].append({dc_item: {"$gt": query[0]}})
            elif query_type == "inferior":
                mongo_query["$and"].append({dc_item: {"$lt": query[0]}})

    print(mongo_query)
    result_list = []
    for post in videos_metadata.find(mongo_query, {'_id': False}).sort([("dc:format.duration", ASCENDING)]):
        result_list.append(post)
        #print(post)

    db_client.close()
    return result_list

server.register_function(search)
server.register_function(launch_digitise)


# Run the server's main loop
try:
    server.serve_forever()
except KeyboardInterrupt:
    server.server_close()