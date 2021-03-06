# ProxyServer

[Read me on GitHub!](https://github.com/SeanCooke/ProxyServer)

## Commands
BUILD COMMAND: `$ make all`
RUN COMMAND: `$ ./ProxyServer proxy_config`
CLEAN COMMAND: `$ make clean`

## Testing
ProxyServer can forward requested files over the Internet from servers to browsers through both `$ telnet` and configuring your browser to utilize ProxyServer.

### Examples
    $ telnet [hostname] [port-specified-in-proxy_config]<enter>
    GET cs.rochester.edu/u/amosayye/ HTTP/1.1<enter>
    <enter>

    $ telnet [hostname] [port-specified-in-proxy_config]<enter>
    GET www.greens.org/about/software/editor.txt HTTP/1.1<enter>
    <enter>

    $ telnet [hostname] [port-specified-in-proxy_config]<enter>
    GET www.york.ac.uk/teaching/cws/wws/webpage1.html HTTP/1.1<enter>
    <host>

    $ telnet [hostname] [port-specified-in-proxy_config]<enter>
    GET www.campustry.com/forms/index.php HTTP/1.1<enter>
    <enter>

ProxyServer will block HTTP requests to hosts specified in the file `proxy_config`.  By default the host `stackoverflow.com` is blocked in `proxy_config`.  If we issue the request

    $ telnet [hostname] [port-specified-in-proxy_config]<enter>
    GET stackoverflow.com HTTP/1.1<enter>
    <enter>

We will recieve a HTTP 403 Forbidden response.

ProxyServer only supports the HTTP GET request method over HTTP.  If we try to issue anything other than a GET request such as:

    $ telnet [hostname] [port-specified-in-proxy_config]<enter>
    POST www.campustry.com/forms/index.php HTTP/1.1<enter>
    <enter>

We will recieve a HTTP 400 Bad Request response.

ProxyServer only supports the HTTP protocol.  If we try to issue anything other than a HTTP request such as:

    $ telnet [hostname] [port-specified-in-proxy_config]<enter>
    CONNECT www.google.com:443 HTTP/1.1<enter>
    <enter>

We will recieve a HTTP 400 Bad Request response.

The client may shut down ProxyServer by issuing a `QUIT` request as seen below:

    $ telnet [hostname] [port-specified-in-proxy_config]<enter>
    QUIT<enter>
    <enter>

To prevent persistant connections, ProxyServer adds the header `Connection: close` to all HTTP requests.

## The Config File
On startup, the proxy server reads a config file (specified as the only argument to `ProxyServer`) to get the port number the server should be run on and a list of websites to be blocked by the proxy server.  Comments in the config file are denoted with a `#` and extend to the end of the line on which they appear.

A port number can be  specified in the config file by including the line `port x` where `x` is the desired port number.  The last port number read will be used.  Exclusion of this line will use the default HTTP port of 80.

A website can be blocked on this proxy server by including the line `block y` in the config file where `y` is the hostname of a website that is wished to be blocked.  Any number of `block y` lines can be specified.

## Concurrent Connections
Multiple simultaneous service requests in parallel are handled with multithreading.  In ProxyServer, the server listens at a fixed port on the main thread.  When a TCP connection request is recieved, a new thread is spawned and the request is handled in the new thread.

Concurrent connections can be tested by using `$ telnet` to connect to ProxyServer from one terminal window and before issuing a request, `$ telnet` to ProxyServer from a second terminal window.  Complete a request on the second terminal window then complete a request on the first terminal window as seen below:

    TERMINAL ONE
    $ telnet [hostname] [port-specified-in-proxy_config]<enter>
    
    TERMINAL TWO
    $ telnet [hostname] [port-specified-in-proxy_config]<enter>
    GET cs.rochester.edu/u/amosayye/ HTTP/1.1<enter>
    <enter>
    
    TERMINAL ONE
    GET www.greens.org/about/software/editor.txt HTTP/1.1<enter>
    <enter>

## References
* Base server code modified from chapter 2.7.2 of __Computer Networking: A Top-Down Approach (7th Edition)__ by Kurose and Ross.
* Modified code on multithreading found [here](http://www.tutorialspoint.com/python/python_multithreading.htm).
* Modified code on receiving large data objects over sockets found [here](https://docs.python.org/3/library/socket.html#example).
