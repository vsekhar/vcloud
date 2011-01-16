import http.server
import vhosthandler

class vhost(http.server.HTTPServer):
	pass

def run_forever(vhost_port):
	server_address = ('', vhost_port)
	httpd = vhost(server_address, vhosthandler.vhost_handler)
	httpd.serve_forever()

