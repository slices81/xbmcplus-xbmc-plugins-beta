#!/usr/bin/python
# -*- coding: utf-8 -*-
import BaseHTTPServer
import sys

HOST_NAME = 'localhost'
PORT_NUMBER = int(sys.argv[2])

key = sys.argv[1]

class StoppableHTTPServer(BaseHTTPServer.HTTPServer):
	def serve_forever(s):
		s.stop = False
		while not s.stop:
			s.handle_request()

class StoppableHttpRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	_key = ''

	def do_QUIT(s):
		s.send_response(200)
		s.end_headers()
		s.server.stop = True
		print 'Server stopped'
	
	def do_HEAD(s):
		s.send_response(200)
		s.send_header('Content-type', 'text/plain')
		s.end_headers()
	
	def do_GET(s):
		if 'stop' in s.path:
			s.do_QUIT()
		else:
			try:
				s.send_response(200)
				s.send_header('Content-type', 'text/plain')
				s.end_headers()
				f = open(s._key, 'rb')
				data = f.read()
				s.wfile.write(data)
				f.close()
			except IOError:
				s.send_error(404, 'File Not Found: %s' % s.path)
			return

if __name__ == '__main__':
	StoppableHttpRequestHandler._key = key
	server = StoppableHTTPServer((HOST_NAME, PORT_NUMBER), StoppableHttpRequestHandler)
	server.serve_forever()
#	sys.exit()