from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
from time import sleep
from pymongo import MongoClient, ASCENDING

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
    client = MongoClient('mongodb://localhost:27017/')
    db = client['test-database']
    videos_metadata = db['videos_metadata']

    eyy = {}

    for dc_items, dict_query in arg.items():
        print(dc_items, dict_query)
        for query_type, query in dict_query.items():
            if query_type == "equal":
                eyy[dc_items] = query[0]
            elif query_type == "contain":
                eyy[dc_items] = {"$regex": ".*" + query[0] + ".*"}

    for post in videos_metadata.find(eyy).sort([("dc:format.duration", ASCENDING)]):
        print(post)
    return "aleeeeluya"

server.register_function(search)
server.register_function(launch_digitise)  # , 'add')


# Run the server's main loop
try:
    server.serve_forever()
except KeyboardInterrupt:
    server.server_close()