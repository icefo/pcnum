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
    # todo: fix bug when you search for multiples stuff like dc:subject {'contain': ['laudantium', 'omnis']}
    # only one is searched : {'dc:subject': {'$regex': '.*laudantium.*'}, 'dc:format.duration': {'$lt': 60}}
    # fix this gui side or server side ?
    client = MongoClient('mongodb://localhost:27017/')
    db = client['test-database']
    videos_metadata = db['videos_metadata']

    eyy = {}

    for dc_item, dict_query in arg.items():
        print(dc_item, dict_query)
        for query_type, query in dict_query.items():
            if query_type == "equal":
                eyy[dc_item] = query[0]
            elif query_type == "contain":
                eyy[dc_item] = {"$regex": ".*" + query[0] + ".*"}
            elif query_type == "greater":
                eyy[dc_item] = {"$gt": query[0]}
            elif query_type == "inferior":
                eyy[dc_item] = {"$lt": query[0]}

    result_list = []
    for post in videos_metadata.find(eyy, {'_id': False}).sort([("dc:format.duration", ASCENDING)]):
        result_list.append(post)
        print(post)

    print(eyy)
    return result_list

server.register_function(search)
server.register_function(launch_digitise)  # , 'add')


# Run the server's main loop
try:
    server.serve_forever()
except KeyboardInterrupt:
    server.server_close()