from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
from time import sleep

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

server.register_function(launch_digitise)  # , 'add')


# Run the server's main loop
try:
    server.serve_forever()
except KeyboardInterrupt:
    server.server_close()