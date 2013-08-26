#!/usr/bin/python
# -*- coding: utf-8 -*-
import _addoncompat
import simplejson
import urllib
import urllib2
import socket
from dns.resolver import Resolver
from httplib import HTTPConnection

TUNLRURL = 'http://tunlr.net/tunapi.php?action=getdns&version=1&format=json'

class MyHTTPConnection(HTTPConnection):
	_dnsproxy = []
	def connect(self):
		resolver = Resolver()
		resolver.nameservers = self._dnsproxy
		answer = resolver.query(self.host,'A')
		self.host = answer.rrset.items[0].address
		self.sock = socket.create_connection((self.host, self.port))

class MyHTTPHandler(urllib2.HTTPHandler):
	_dnsproxy = []
	def http_open(self, req):
		MyHTTPConnection._dnsproxy = self._dnsproxy 
		return self.do_open(MyHTTPConnection, req)

def prepare_dns_proxy():
	dnsproxy = []
	dnsproxy.append(_addoncompat.get_setting('dns_proxy'))
	MyHTTPHandler._dnsproxy = dnsproxy
	opener = urllib2.build_opener(MyHTTPHandler)
	return opener

def prepare_tunlr_dns():
	dnsproxy = []
	request = urllib2.Request(TUNLRURL)
	response = urllib2.urlopen(request)
	dnsdata = response.read()
	response.close()
	tunlr_dns = simplejson.loads(dnsdata)
	dnsproxy.append(tunlr_dns['dns1'])
	dnsproxy.append(tunlr_dns['dns2'])
	MyHTTPHandler._dnsproxy = dnsproxy
	opener = urllib2.build_opener(MyHTTPHandler)
	return opener

def prepare_us_proxy():
	us_proxy = 'http://' + _addoncompat.get_setting('us_proxy') + ':' + _addoncompat.get_setting('us_proxy_port')
	proxy_handler = urllib2.ProxyHandler({'http':us_proxy})
	if ((_addoncompat.get_setting('us_proxy_pass') is not '') and (_addoncompat.get_setting('us_proxy_user') is not '')):
		print 'Using authenticated proxy: ' + us_proxy
		password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
		password_mgr.add_password(None, us_proxy, _addoncompat.get_setting('us_proxy_user'), _addoncompat.get_setting('us_proxy_pass'))
		proxy_auth_handler = urllib2.ProxyBasicAuthHandler(password_mgr)
		opener = urllib2.build_opener(proxy_handler, proxy_auth_handler)
	else:
		print 'Using proxy: ' + us_proxy
		opener = urllib2.build_opener(proxy_handler)
	return opener

def getURL(url, values = None, referer = False, forwardheader = False, connectiontype = _addoncompat.get_setting('connectiontype')):
	try:
		old_opener = urllib2._opener
		if int(connectiontype) == 1:
			urllib2.install_opener(prepare_dns_proxy())
		elif int(connectiontype) == 2:
			urllib2.install_opener(prepare_us_proxy())
		elif int(connectiontype) == 3:
			urllib2.install_opener(prepare_tunlr_dns())
		print '_connection :: getURL :: url = ' + url
		if values is None:
			req = urllib2.Request(url)
		else:
			data = urllib.urlencode(values)
			req = urllib2.Request(url, data)
		if referer:
			req.add_header('Referer', referer)
		if forwardheader:
			req.add_header('X-Forwarded-For', forwardheader)
		req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:14.0) Gecko/20100101 Firefox/14.0.1')
		response = urllib2.urlopen(req)
		link = response.read()
		response.close()
		urllib2.install_opener(old_opener)
	except urllib2.HTTPError, error:
		print 'HTTP Error reason: ', error
		return error.read()
	else:
		return link
	
def getRedirect(url, values = None , referer = False, forwardheader = False, connectiontype = _addoncompat.get_setting('connectiontype')):
	try:
		proxyip = False
		old_opener = urllib2._opener
		if int(connectiontype) == 1:
			urllib2.install_opener(prepare_dns_proxy())
		elif int(connectiontype) == 2:
			urllib2.install_opener(prepare_us_proxy())
		elif int(connectiontype) == 3:
			urllib2.install_opener(prepare_tunlr_dns())
		print '_connection :: getRedirect :: url = ' + url
		if values is None:
			req = urllib2.Request(url)
		else:
			data = urllib.urlencode(values)
			req = urllib2.Request(url,data)
		if referer:
			req.add_header('Referer', referer)
		if proxyip:
			req.add_header('X-Forwarded-For', proxyip)
		elif forwardheader:
			req.add_header('X-Forwarded-For', forwardheader)
		req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:14.0) Gecko/20100101 Firefox/14.0.1')
		response = urllib2.urlopen(req)
		finalurl = response.geturl()
		response.close()
		urllib2.install_opener(old_opener)
	except urllib2.HTTPError, error:
		print 'HTTP Error reason: ', error
		return error.read()
	else:
		return finalurl

def getAMF(url, values, header, connectiontype = _addoncompat.get_setting('connectiontype')):
	try:
		old_opener = urllib2._opener
		if int(connectiontype) == 1:
			urllib2.install_opener(prepare_dns_proxy())
		elif int(connectiontype) == 2:
			urllib2.install_opener(prepare_us_proxy())
		elif int(connectiontype) == 3:
			urllib2.install_opener(prepare_tunlr_dns())
		print '_connection :: getAMF :: url = ' + url
		req = urllib2.Request(url, values, header)
		response = urllib2.urlopen(req)
		link = response.read()
		response.close()
		urllib2.install_opener(old_opener)
	except urllib2.HTTPError, error:
		print 'HTTP Error reason: ', error
		return error.read()
	else:
		return link