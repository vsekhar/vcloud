import http.server

class vhost_handler(http.server.BaseHTTPRequestHandler):

	def response(self, msg):
		self.send_response(200)
		self.send_header("Content-type", "text/plain")
		self.send_header("Content-length", len(msg))
		self.end_headers()
		encoded_msg = msg.encode('ascii')
		self.wfile.write(encoded_msg)
		
	def do_GET(self):
		(cmd, _, rest) = self.path.partition('/')
		self.response("You requested: %s" % cmd)

