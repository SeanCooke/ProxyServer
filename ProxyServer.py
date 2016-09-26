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

# listToSpokenList takes a list as a parameter and returns
# the written description of the elements in the list.
#
# i.e. myList = [] returns ''
# myList = ['GET'] returns 'GET'
# myList = ['GET', 'POST'] returns 'GET and POST'
# myList = ['GET', 'POST', 'HEAD'] returns 'GET, POST, and HEAD'
def listToSpokenList(pythonList):
	pythonListIndex = 0
	pythonListLastElementIndex = len(pythonList)-1
	spokenList = ''
	andCharacter = ', and '
	for pythonListElement in pythonList:
		if pythonListIndex == 0:
			spokenList = pythonList[pythonListIndex]
		elif pythonListIndex == pythonListLastElementIndex:
			if len(pythonList) == 2:
				andCharacter = ' and '
			spokenList = spokenList+andCharacter+pythonList[pythonListIndex]
		else:
			spokenList = spokenList+', '+pythonList[pythonListIndex]
		pythonListIndex+=1
	return spokenList.rstrip()

# headerListToHeaderDict takes a list of HTML headers as a parameter and returns
# a dictionary containing the HTML headers in name/value pairs
#
# i.e. headerListToHeaderDict(['Host: www.campustry.com', 'Connection: keep-alive'])
# returns {'Host': 'www.campustry.com', 'Connection': 'keep-alive'}
def headerListToHeaderDict(headerList):
	headerDict = dict()
	for headerListElement in headerList:
		if headerListElement != '':
			headerListElementSplit = headerListElement.split(':', 1)
			key = headerListElementSplit[0].strip()
			try:
				value = headerListElementSplit[1].strip()
			except IndexError:
				value = ''	
			headerDict[key] = value
	return headerDict

# parseHTTPRequestString takes a string representaiton of a HTTP request and
# returns three values:
# 1. The request method
# 2. The requestd hostname and file
# 3. A dictionary of all HTTP request headers
def parseHTTPRequestString(clientHTTPRequestString):
	# A new line can be a single "\n" or a character pair "\r\n"
	headers = clientHTTPRequestString.splitlines()
	# The first line is of the form '[REQUEST_METHOD] [REQUESTED_FILE] [HTTP_VERSION]'
	requestMethodLine = headers[0]
	# All remaining lines of the HTTP request are headers
	headers.remove(requestMethodLine)
	requestMethodLineSplit = requestMethodLine.split()
	requestMethod = requestMethodLineSplit[0]
	requestHostFile = requestMethodLineSplit[1]
	return requestMethod, requestHostFile, headerListToHeaderDict(headers)

def handleHTTPRequest(httpRequestString, websitesToBlock):
	supportedHTTPMethods = ['GET']
	ulSupportedHTTPRequestMethods = listToHTMLul(supportedHTTPMethods)
	requestMethod, requestHostFile, httpRequestHeaders = parseHTTPRequestString(httpRequestString)
	host = httpRequestHeaders['Host']
	if (requestMethod not in  supportedHTTPMethods):
		ulSupportedHTTPRequestMethods = listToHTMLul(supportedHTTPMethods)
		proxyHTTPResponse = 'HTTP/1.1 400 Bad Request\nConnection: Closed\n\n<!DOCTYPE html><html><head><title>HTTP/1.1 400 Bad Request</title></head><body><h1>HTTP/1.1 400 Bad Request</h1><p>Your HTTP '+requestMethod+' request could not be handled.  ProxyServer only supports the following HTTP request methods:</p>'+ulSupportedHTTPRequestMethods+'</body></html>'
		httpResponseSentString = 'No request sent to server. Request method other than '+listToSpokenList(supportedHTTPMethods)+' requested.'
	elif (host in websitesToBlock):
		proxyHTTPResponse = 'HTTP/1.1 403 Forbidden\nConnection: Closed\n\n<!DOCTYPE html><html><head><title>HTTP/1.1 403 Forbidden</title></head><body><h1>HTTP/1.1 403 Forbidden</h1><p>Your HTTP '+requestMethod+' request could not be handled.  The host \''+host+'\' has been blocked.</body></html>'
		httpResponseSentString = 'No request sent to server. Host \''+host+'\' is blocked.'
	else:
		# open TCP connection with [host] on port 80
		clientSocket = socket(AF_INET, SOCK_STREAM)
		clientSocket.connect((host, 80))
		# sending the [httpRequestString] that was sent to the proxy to [host]
		clientSocket.send(httpRequestString)
		# receiving [httpRequestString] response form [host] in [proxyHTTPResponse]  
		proxyHTTPResponse = clientSocket.recv(1024)
		clientSocket.close()
		# proxyHTTPResponse = 'HTTP/1.1 200 OK\nConnection: Closed\n\n<!DOCTYPE html><html><head><title>HTTP/1.1 200 OK</title></head><body><h1>HTTP/1.1 200 OK</h1></body></html>'
		httpResponseSentString = 'Sent '+requestHostFile
	return httpResponseSentString, proxyHTTPResponse

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
		httpResponseSentString = 'Connection closed by client before HTTP response sent.'
		clientHTTPRequestString = self.connectionSocket.recv(1024)
		httpResponseSentString, messageFromProxyServer = handleHTTPRequest(clientHTTPRequestString, self.websitesToBlock)
		self.connectionSocket.send(messageFromProxyServer)
		self.connectionSocket.close()
		print 'TCP connection closed with: '+ipAddressPortNumber+'. '+httpResponseSentString

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