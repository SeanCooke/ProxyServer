#!/usr/bin/env python
import sys, threading, os
from socket import *

# readConfig reads the file specified in pathToFile
# Comments in pathToFile are denoted with # and extend to the end of the line.
#
# input arguments:
# 1. pathToFile -  the path to a the config file
#
# return values:
# 1. int(port) - the value specified as 'port' from pathToFile.
# (note: if no values is specified as 'port', 80 will be used.
#        if multiple values are specified as 'port', the final value will be used)
# 2. websitesToBlock - a list containing all values specified as 'block' from pathToFile
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

# preventPersistantConnections prevents persistant HTTP connections
# by explicitly setting the connection to be closed
#
# input arguments:
# 1. requestMethodLine - the first line of the HTTP request as a string
#						 i.e. "GET /about/software/editor.txt HTTP/1.1"
# 2. httpRequestHeaders -  a python dictionary containing a list of all
# 						   HTTP headers in name/value pairs
#
# return values:
# 1. httpRequest+'\n\n' - a complete HTTP request concatinated from
#						  requestMethodLine and httpRequestHeaders
#						  with the header 'Connection: close'
def preventPersistantConnections(requestMethodLine, httpRequestHeaders):
	httpRequest = requestMethodLine
	httpRequestHeaders['Connection'] = 'close'
	for key, value in httpRequestHeaders.iteritems():
		 httpRequest+='\n'+key+': '+value
	return httpRequest+'\n\n'

# concatenateList takes a python list as a parameter and returns
# the elements of the list between [startIndex] and [endIndex]
# inclusive with [concatCharacter]
#
# input arguments:
# pythonList - a list of elements we wish to concatenate
# startIndex - an integer representing the first element of
#              [pythonList] to include in the concatenation
# endIndex - an integer representing the last element of [pythonList]
#            to include in the concatenation
# concatCharacter - the character to concatenate all elements between
#                   pythonList[startIndex] and pythonList[endIndex] with
#
# return values:
# returnString - a string representing all elements between pythonList[startIndex]
#                and pythonList[endIndex] with [concatCharacter] between them
def concatenateList(pythonList, startIndex, endIndex, concatCharacter):
	returnString = ''
	for index in range(startIndex, endIndex):
		returnString = returnString + pythonList[index] + concatCharacter
	returnString = returnString[:-1]
	return returnString

# getPortNumberFromHostname will extract a port number
# from a string containing either a hostname and port number
# or a string containing solely a hostname.  If a port number
# is not specified, a default port number from [protocol] will
# be used.
#
# input arguments:
# protocol - a string representing the protocol used
# hostPortNumber - a string representing the hostname (and possibly
# port number) used
#
# return values:
# host - a string representing the hostname to which the request
#        is being made
# portNumber - an integer representing the port number to which
#              the request is being made
def getPortNumberFromHostname(protocol, hostPortNumber):
	portDeliminiter = ':'
	# if there is a colon in hostPortNumber, that is
	# the port number.  Otherwise a default port number
	# will be used.
	if portDeliminiter in hostPortNumber:
		hostPortNumberSplit = hostPortNumber.split(portDeliminiter)
		try:
			host = hostPortNumberSplit[0]
		except IndexError:
			host = ''
		try:
			portNumber = int(hostPortNumberSplit[1])
		except IndexError:
			portNumber = 80
	else:
		host = hostPortNumber
		if(protocol.lower() == 'http' or protocol.lower() == ''):
			portNumber = 80
		elif(protocol.lower() == 'https'):
			portNumber = 443
	return host, portNumber

# parseRequestHostFile takes a string representing
# the protocol, host, and file requested to a proxy
# server and returns the protocol, hostname, port number
# and file requeted.  If no port number is specified and
# protocol is 'http', port will be 80.  If no port number
# is specified and protocol is 'https', port will be 443.
#
# input arguments:
# requestHostFile - a string representing the protocol,
# host, and file requested to a proxy server.
#
# return values:
# protocol - a string representing the protol requested
#			 in requestHostFile.
# host - a string representing the the host requested in
#        requestHostFile.
# portNumber - an integer representing the port number
#              requested in requestHostFile.  If no port
#              number is specified and protocol is 'http',
#              port will be 80.  If no port number is specified
#              and protocol is 'https', port will be 443.
# fileRequested - a string representing the file requested
#                 in requestHostFile.
def parseRequestHostFile(requestHostFile):
	protocolDelimiter = '://'
	# if a protocol is specified in the HTTP request
	if (protocolDelimiter in requestHostFile):
		slashOffset = 2
		requestHostFileSplit = requestHostFile.split(protocolDelimiter)
		try:
			protocol = requestHostFileSplit[0].lower()
		except IndexError:
			protocol = ''
		requestHostFileSplit = requestHostFile.split('/')
		try:
			hostPortNumber = requestHostFileSplit[2]
			host, portNumber = getPortNumberFromHostname(protocol, hostPortNumber)
		except IndexError:
			hostPortNumber = ''
		try:
			fileRequested = '/'+concatenateList(requestHostFileSplit, 3, len(requestHostFileSplit), '/')
		except IndexError:
			fileRequested = '/'
	# if no protocol is specified in the HTTP request
	else:
		protocol = ''
		requestHostFileSplit = requestHostFile.split('/', 1)
		try:
			hostPortNumber = requestHostFileSplit[0]
			host, portNumber = getPortNumberFromHostname(protocol, hostPortNumber)
		except IndexError:
			hostPortNumber = ''
		try:
			fileRequested = '/'+concatenateList(requestHostFileSplit, 1, len(requestHostFileSplit), '/')
		except IndexError:
			fileRequested = '/'
	return protocol, host, portNumber, fileRequested

# listToHTMLul takes a list [pythonList] as a parameter
# and returns the string representation of [pythonList]
# as an unordered HTML list.
# 
# i.e. [pythonList] = ['GET', 'POST']
# returns: '<ul><li>GET</li><li>POST</li></ul>'
#
# input arguments:
# 1. pythonList - a python list
#
# return values:
# htmlUL+</ul> - a string containing html that represents
#			     the python list as an unordered list
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
#
# input arguments:
# pythonList - a python list
#
# return values:
# spokenList.rstrip() - a string representing the way you would
#			   			write the items in the python list
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
#
# input arguments:
# headerList - a list where each element is a name/value pair separated by a
#			   colon
#
# return values:
# headerDict - a dictionary where each key is what was before the first colon
#			   in headerList and each value is what was after the first colon
#			   in headerList
def headerListToHeaderDict(headerList):
	headerDict = dict()
	for headerListElement in headerList:
		if headerListElement != '':
			headerListElementSplit = headerListElement.split(':', 1)
			try:
				key = headerListElementSplit[0].strip()
			except IndexError:
				key = ''
			try:
				value = headerListElementSplit[1].strip()
			except IndexError:
				value = ''	
			headerDict[key] = value
	return headerDict

# parseHTTPRequestString takes a string representaiton of a HTTP request and
# returns the requested hostname and file, the first line of the HTTP request
# and a dictionary of all HTTP request headers
#
# input arguments:
# clientHTTPRequestString - a string representing a complete HTTP request
#
# return values:
# 1. requestHostFile - a string representing the file requested in
#					   clientHTTPRequestString
# 2. requestMethodLine - a string representing the first line of the HTTP
#						 request (i.e. 'GET /index.html HTTP/1.1')			 
def parseHTTPRequestString(clientHTTPRequestString):
	# A new line can be a single "\n" or a character pair "\r\n"
	headers = clientHTTPRequestString.splitlines()
	# The first line is of the form '[REQUEST_METHOD] [REQUESTED_FILE] [HTTP_VERSION]'
	requestMethodLine = headers[0]
	# All remaining lines of the HTTP request are headers
	headers.remove(requestMethodLine)
	requestMethodLineSplit = requestMethodLine.split()
	requestHostFile = requestMethodLineSplit[1]
	return requestHostFile, requestMethodLine, headerListToHeaderDict(headers)

# getRequestMethod takes a string representaiton of a HTTP request and
# returns the HTTP request method for the request
#
# input arguments:
# clientHTTPRequestString - a string representing a complete HTTP request
#
# return values:
# requestMethod - a string representing the request method request in the HTTP request
def getRequestMethod(clientHTTPRequestString):
	# A new line can be a single "\n" or a character pair "\r\n"
	headers = clientHTTPRequestString.splitlines()
	# The first line is of the form '[REQUEST_METHOD] [REQUESTED_FILE] [HTTP_VERSION]'
	requestMethodLine = headers[0]
	requestMethodLineSplit = requestMethodLine.split()
	requestMethod = requestMethodLineSplit[0]
	return requestMethod

# handleHTTPRequest takes the HTTP request [httpRequestString] and a python list of 
# websites to block [websitesToBlock] and returns the HTTP response from the host
# specified in [httpRequestString].
#
# A HTTP 400 Bad Request error occurs if an unsupported method request occurs
# A HTTP 403 Forbidden error occurs if the host specified in [httpRequestString].
# is in [websitesToBlock]
#
# input arguments:
# httpRequestString - a string representing a complete HTTP request
# websitesToBlock - a list where each value is the hostname of a website to block
#
# return values:
# httpResponseSentString - a string to display on the ProxyServer terminal detailing
#						   what was sent (or not sent) to the client
# proxyHTTPResponse - the HTTP response from the requested server
def handleHTTPRequest(httpRequestString, websitesToBlock):
	supportedHTTPMethods = ['GET']
	ulSupportedHTTPRequestMethods = listToHTMLul(supportedHTTPMethods)
	requestMethod = getRequestMethod(httpRequestString)
	# if the request method is QUIT, shut down the server
	if requestMethod == 'QUIT':
		print 'Shutting down ProxyServer...'
		os._exit(1)
	else:
		requestHostFile, requestMethodLine, httpRequestHeaders = parseHTTPRequestString(httpRequestString)
		protocol, host, portNumber, fileRequested = parseRequestHostFile(requestHostFile)
		httpRequestHeaders['Host'] = host
		print 'protocol: '+protocol
		if (requestMethod not in supportedHTTPMethods or protocol not in ['http', '']):
			ulSupportedHTTPRequestMethods = listToHTMLul(supportedHTTPMethods)
			proxyHTTPResponse = 'HTTP/1.1 400 Bad Request\nConnection: close\n\n<!DOCTYPE html><html><head><title>HTTP/1.1 400 Bad Request</title></head><body><h1>HTTP/1.1 400 Bad Request</h1><p>Your HTTP '+requestMethod+' request could not be handled.  ProxyServer only supports the following HTTP request methods:</p>'+ulSupportedHTTPRequestMethods+'</body></html>'
			httpResponseSentString = 'No request sent to server. Request method other than '+listToSpokenList(supportedHTTPMethods)+' requested.'
		elif (host in websitesToBlock):
			proxyHTTPResponse = 'HTTP/1.1 403 Forbidden\nConnection: close\n\n<!DOCTYPE html><html><head><title>HTTP/1.1 403 Forbidden</title></head><body><h1>HTTP/1.1 403 Forbidden</h1><p>Your HTTP '+requestMethod+' request could not be handled.  The host \''+host+'\' has been blocked.</body></html>'
			httpResponseSentString = 'No request sent to server. Host \''+host+'\' is blocked.'
		else:
			# open TCP connection with [host] on port 80
			clientSocket = socket(AF_INET, SOCK_STREAM)
			clientSocket.connect((host, portNumber))
			# sending the [httpRequestString] that was sent to the proxy to [host] with the header 'Connection: close'
			requestMethodLine = requestMethod+' '+fileRequested+' HTTP/1.1'
			closedHTTPRequest = preventPersistantConnections(requestMethodLine, httpRequestHeaders)
			print '*****'
			print closedHTTPRequest
			print '*****'
			clientSocket.send(closedHTTPRequest)
			# receiving [httpRequestString] response form [host] in [proxyHTTPResponse]
			proxyHTTPResponse = ''
			# recieve all data from the server in 1024 bytes
			while True:
				dataFromServer = clientSocket.recv(1024)
				proxyHTTPResponse+=dataFromServer
				if not dataFromServer:
					break
			clientSocket.close()
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
	# input arguments:
	# 1. connectionSocket - a file descriptor of a socket
	# 2. addr - the port number on which the TCP connection socket is running
	# 3. websitesToBlock - a list containing all values specified as 'block' from pathToFile
	def __init__(self, connectionSocket, addr, websitesToBlock):
		threading.Thread.__init__(self)
		self.connectionSocket = connectionSocket
		self.addr = addr
		self.websitesToBlock = websitesToBlock
	def run(self):
		ipAddressPortNumber = self.addr[0]+':'+str(self.addr[1])
		print 'TCP connection opened with: '+ipAddressPortNumber
		httpResponseSentString = 'Connection closed by client before HTTP response sent.'
		clientHTTPRequestString = '***'
		while clientHTTPRequestString[-3:] not in ['\n\n\n', '\n\n\r', '\n\r\n', '\n\r\r', '\r\n\n', '\r\n\r', '\r\r\n', '\r\r\r']:
			clientHTTPRequestString += self.connectionSocket.recv(1024)
		clientHTTPRequestString = clientHTTPRequestString[3:]
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
			print '\nServer '+gethostname()+' listening on port '+serverPortString+' stopped with a keyboard interrupt.'
	else:
		print 'ERROR: Invalid number of arguments'

# commmand must be of form "./ProxyConfig [locationOfConfig]".
main()