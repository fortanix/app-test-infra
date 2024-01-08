#!/usr/bin/env python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import http.server
import requests
import socket
import socketserver
import threading
import time

PORT = 8080
STARTUP_RETRIES = 10

Handler = http.server.SimpleHTTPRequestHandler

def run_server(address, port):
    with socketserver.TCPServer((address, port), Handler) as httpd:
        print("serving at {}:{}".format(address, port))

        httpd.serve_forever()

def connect_to_server(address, port):
    print("Connecting to server")
    url = 'http://{}:{}'.format(address, port)

    for _ in range(STARTUP_RETRIES):
        try:
            print('Fetching {}'.format(url))
            response = requests.get(url, timeout=10.0)

            if response.status_code != 200:
                raise Exception('Server returned status {}, but should be {}'.format(response.status_code, 200))

            if "Hello world" not in response.text:
                raise Exception('Server should serve index page, but returned {}'.format(response.text))

            print("Established a connection to a python web server!")
            return True
        except Exception as e:
            print('Connecting to server failed, sleeping for retry. Reason {}'.format(e))
            time.sleep(5)

    raise Exception('Failed to connect to server after {} retries'.format(STARTUP_RETRIES))

# Get hostname
hostname = socket.gethostname()
print("Hostname:", hostname)

if len(hostname) == 0:
    exit(1)

# Get FQDN
fqdn = socket.getfqdn()
print("FQDN:", fqdn)

if len(fqdn) == 0:
    exit(1)

ip_address = socket.gethostbyname(hostname)
print("Ip address of a hostname is:", ip_address)

web_server = threading.Thread(target=run_server, args=(ip_address, PORT))

# Kills server thread after main thread exits
web_server.daemon = True
web_server.start()

connect_to_server(ip_address, PORT)

print('test-hostname passed')
exit(0)
