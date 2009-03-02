import SimpleXMLRPCServer

class AddressedXMLRPCRequestHandler(SimpleXMLRPCServer.SimpleXMLRPCRequestHandler):
    # custom dispatcher inserts requester's address as a parameter
    def _dispatch(self, method, params):
        try:
            func = self.server.funcs[method]
        except KeyError:
            raise Exception('method "%s" is not supported' % method)
        host, port = self.client_address    # port is not used
        params = params+(host,)
        return func(*params)
