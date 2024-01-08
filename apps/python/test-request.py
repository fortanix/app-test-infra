#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
'''
This test tries to send and receive huge amount of data to a webserver via http
post request with
'''

import requests
from http.server import CGIHTTPRequestHandler, HTTPServer
from multiprocessing import Manager, Process

REQUEST_SUCCESS_CODE = '<Response [200]>'
httpd = None

class Serv(CGIHTTPRequestHandler):

    def do_POST(self):
        try:
            self.send_response(200)
        except:
            self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        #disabling logs because the test is verified from the contents of stdout
        pass

def create_server():
    global httpd
    httpd = HTTPServer(('localhost', 0), Serv)

def run_server():
    httpd.serve_forever()

def client_func():

    K = 1024
    data_sizes = [ 16 * K, \
                   60237, \
                   32 * K, \
                   64 * K, \
                   128 * K, \
                   178574, \
                   200 * K
                 ]
                 # 60237 and 178574 are customer reported sizes in ZIRC-3744
                 # data size of 60237 was being posted but 178574 was failing

    port = ""
    url = ""
    success = True

    server_up = False
    while not server_up:
        try:
            port = str(httpd.socket.getsockname()[1])
            url = 'http://localhost:'+ str(port) + '/'
            requests.post(url, data=bytearray(1))
            server_up = True
        except Exception as err:
            pass

    for data_size in data_sizes:
        response_code = requests.post(url, data = bytearray(data_size))
        if( str(response_code).strip() != REQUEST_SUCCESS_CODE ):
            success = False

    if(success):
        print('test-request passed' )
    else:
        print('failed')

def start_tests():
    create_server()
    server_proc = Process(target=run_server)

    # setting this flag to true, all the child processes will be killed once the
    # parent exits
    server_proc.daemon=True
    server_proc.start()

    client_func()

if __name__ == '__main__':
    start_tests()
