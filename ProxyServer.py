#!/usr/bin/env python
import sys, threading
from socket import *

# readConfig reads the file specified in pathToFile
# and returns two values:
# 1. the value specified as 'port' from pathToFile.
# (note: if no values is specified as 'port', 80 will be used.
#        if multiple values are specified as 'port', the final value will be used)
# 2. a list containing all values specified as 'block' from pathToFile
#
# Comments in pathToFile are denoted with # and extend to the end of the line
def readConfig(pathToFile):
	commentCharacter = '#'
	port = 80
	websitesToBlock = []
	with open(pathToFile) as config:
		line = config.readline()
		while line:
			commentCharacterIndex = line.find(commentCharacter)
			if commentCharacterIndex != -1:
				line = line[0:commentCharacterIndex]
			lineSplit = line.split()
			try:
				if lineSplit[0] == 'port':
					port = lineSplit[1]
				if lineSplit[0] == 'block':
					websitesToBlock.append(lineSplit[1])
			except IndexError:
				pass
			line = config.readline()
	return int(port), websitesToBlock

# listToHTMLul takes a list [pythonList] as a parameter
# and returns the string representation of [pythonList]
# as an unordered HTML list.
# 
# i.e. [pythonList] = ['GET', 'POST']
# returns: '<ul><li>GET</li><li>POST</li></ul>'
def listToHTMLul(pythonList):
	htmlUL = '<ul>'
	for pythonListElement in pythonList:
		htmlUL+='<li>'+str(pythonListElement)+'</li>'
	return htmlUL+'</ul>'

# getRequestMethod takes a HTTP request as a parameter and
# returns the requested HTTP method (i.e. GET, POST, HEAD)
def getRequestMethod(httpRequestString):
	# A new line can be a single "\n" or a character pair "\r\n"
	headers = httpRequestString.splitlines()
	# The first line is of the form '[REQUEST_METHOD] [REQUESTED_FILE] [HTTP_VERSION]'
	requestMethodLine = headers[0]
	requestMethodLineSplit = requestMethodLine.split()
	return requestMethodLineSplit[0]

def handleHTTPRequest(httpRequestString, websitesToBlock):
	supportedHTTPMethods = ['GET']
	host = 'stackoverflow.com'
	ulSupportedHTTPRequestMethods = listToHTMLul(supportedHTTPMethods)
	requestMethod = getRequestMethod(httpRequestString)
	if (requestMethod not in  supportedHTTPMethods):
		ulSupportedHTTPRequestMethods = listToHTMLul(supportedHTTPMethods)
		proxyHTTPResponse = 'HTTP/1.1 400 Bad Request\nConnection: Closed\n\n<!DOCTYPE html><html><head><title>HTTP/1.1 400 Bad Request</title></head><body><h1>HTTP/1.1 400 Bad Request</h1><p>Your HTTP '+requestMethod+' request could not be handled.  ProxyServer only supports the following HTTP request methods:</p>'+ulSupportedHTTPRequestMethods+'</body></html>'
	elif (host in websitesToBlock):
		proxyHTTPResponse = 'HTTP/1.1 403 Forbidden\nConnection: Closed\n\n<!DOCTYPE html><html><head><title>HTTP/1.1 403 Forbidden</title></head><body><h1>HTTP/1.1 403 Forbidden</h1><p>Your HTTP '+requestMethod+' request could not be handled.  The host \''+host+'\' has been blocked.</body></html>'
	else:
		proxyHTTPResponse = 'HTTP/1.1 200 OK\nConnection: Closed\n\n<!DOCTYPE html><html><head><title>HTTP/1.1 200 OK</title></head><body><h1>HTTP/1.1 200 OK</h1></body></html>'
	return proxyHTTPResponse

# A requestThread object is a 3-tuple comprised
# of a connectionSocket, an address, and a list 
# of websites to block read from proxy_config.
# 
# When a requestThread object is run, it will
# accept a HTTP request from a client and run
# handleHTTPRequest(clientHTTPRequestString, self.websitesToBlock)
class requestThread (threading.Thread):
	def __init__(self, connectionSocket, addr, websitesToBlock):
		threading.Thread.__init__(self)
		self.connectionSocket = connectionSocket
		self.addr = addr
		self.websitesToBlock = websitesToBlock
	def run(self):
		ipAddressPortNumber = self.addr[0]+':'+str(self.addr[1])
		print 'TCP connection opened with: '+ipAddressPortNumber
#		httpResponseSentString = 'Connection closed by client before HTTP response sent.'
		clientHTTPRequestString = self.connectionSocket.recv(1024)
		print clientHTTPRequestString
		messageFromProxyServer = handleHTTPRequest(clientHTTPRequestString, self.websitesToBlock)
		self.connectionSocket.send(messageFromProxyServer)
		self.connectionSocket.close()
		print 'TCP connection closed with: '+ipAddressPortNumber #+'. '+httpResponseSentString

# main() will create TCP connections with connected
# clients.  Concurrent connections will be accepted.
#
# Upon connection, the client will submit a HTTP
# request.  If the HTTP request is in [supportedHTTPMethods],
# and they are not requesting a website in
# [websitesToBlock] their HTTP request will be handled
# and returned to the client.
#
# If the HTTP request is not in [supportedMethods], a
# HTTP/1.1 400 Bad Request response will be returened
# to the client.
#
# If they are requesting a website in [websitesToBlock],
# a HTTP/1.1 403 Forbidden response will be returened
# to the client.
def main():
	if len(sys.argv) == 2:
		# read [locationOfConfig] to get port to listen on and list of websites to block
		serverPort, websitesToBlock = readConfig(sys.argv[1])
		serverSocket = socket(AF_INET, SOCK_STREAM)
		serverSocket.bind(('',serverPort))
		serverSocket.listen(1)
		serverPortString = str(serverPort)
		print gethostname()+' listening on port '+serverPortString
		try:
			while True:
				connectionSocket, addr = serverSocket.accept()
				# start a new thread and pass connectionSocket and addr
				requestThread(connectionSocket, addr, websitesToBlock).start()
		except KeyboardInterrupt:
			print '\nServer '+gethostname()+' listening on port '+serverPortString+' stopped with ctl+c'
	else:
		print 'ERROR: Invalid number of arguments'

# commmand must be of form "./ProxyConfig [locationOfConfig]"
main()