#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Nginx test using standard nginx container.

import argparse
import filecmp
import os
import time
from test_app import TestApp, main
from test_utils import TestException


class TestNginx(TestApp):
    retries = 15
    saved_file = 'index.html'
    saved_ssl_file = 'ssl.html'


    def __init__(self, run_args, test_arg_list):
        super(TestNginx, self).__init__(run_args, [])
        parser = argparse.ArgumentParser(description='Nginx test')
        self.args = parser.parse_args(test_arg_list)

    def run(self):
        try:
            os.remove(TestNginx.saved_file)
        except OSError:
            pass

        try:
            os.remove(TestNginx.saved_ssl_file)
        except OSError:
            pass

        # Our nginx container serves HTTP on port 80 and HTTPS on port 443. In order for our client program to
        # interact with the nginx process without itself running in the same network namespace as nginx, we ask
        # Docker to pass these ports through to the host. By requesting port 'None', we ask for a random host port
        # so we don't have to worry about port conflicts with other software running on the test host.
        ports = {
            80: None,
            443: None,
        }

        container = self.container('nginx', memsize='2G', image_version='1.15.2',
                registry='library', rw_dirs=['/var/cache/nginx',
                '/var/run','/run', '/etc/nginx'], ports=ports)
        container.prepare()
        container.copy_file('nginx-cert.pem', '/etc/nginx')
        container.copy_file('nginx-key.pem', '/etc/nginx')
        container.copy_file('ssl.conf', '/etc/nginx/conf.d')
        container.run()

        # We need to look up what host ports these got mapped to by Docker.
        http_port = container.get_port_mapping(80)
        https_port = container.get_port_mapping(443)

        print('nginx running with http on port {} and https on port {}'.format(http_port, https_port))

        # nginx can take a while before it's serving requests, especially
        # on SGX. Try hitting it with wget a few times until it's serving
        # requests.
        for _ in range(TestNginx.retries):
            retval = os.system('wget -nv -O {} http://localhost:{}'.format(TestNginx.saved_file, http_port))
            if (retval == 0):
                break
            time.sleep(1)

        if not os.path.isfile(TestNginx.saved_file):
            raise TestException('Unable to connect with HTTP')

        if not filecmp.cmp(TestNginx.saved_file, 'reference-output.html'):
            raise TestException('nginx returned incorrect data')

        # We pass --no-check-certificate because this test uses a self-signed SSL certificate.
        retval = os.system('wget --no-check-certificate -nv -O {} https://localhost:{}'.format(
            TestNginx.saved_ssl_file, https_port))

        if not os.path.isfile(TestNginx.saved_ssl_file):
            raise TestException('Unable to connect with HTTPS')

        if not filecmp.cmp(TestNginx.saved_ssl_file, 'reference-output.html'):
            raise TestException('nginx returned incorrect data over HTTPS');

        return True

if __name__ == '__main__':
    main(TestNginx)
