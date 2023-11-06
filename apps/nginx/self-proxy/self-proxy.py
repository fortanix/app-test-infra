#!/usr/bin/python3
#
# Copyright (C) 2021 Forttanix, Inc. All Rights Reserved.
#
# Nginx test for self-proxying a large file. Regression test for
# ZIRC-4794.
import os
import requests
import test_app
import test_utils
import time

TEST_FILE_SIZE = 10 * 1024 * 1024
STARTUP_RETRIES = 360

TEST_ITERS = 10

class SelfProxy(test_app.TestApp):
    def __init__(self, run_args, _):
        super(SelfProxy, self).__init__(run_args, [])

    def run(self):
        ports = {
            8080: None
        }

        rw_dirs = [
            '/etc/nginx',
            '/usr/share/nginx/html',
            '/var/cache/nginx',
        ]

        with open('data', 'wb') as fh:
            fh.truncate(TEST_FILE_SIZE)

        if os.environ['PLATFORM'] == "nitro":
            image_version = 'latest'
        else:
            image_version = '1.21.1'

        container = self.container('nginx', registry='library', ports=ports,
                                   memsize='256M', nitro_memsize='2G', image_version=image_version,
                                   rw_dirs=rw_dirs,
                                   container_env=['ENCLAVEOS_DISABLE_DEFAULT_CERTIFICATE=true'])
        container.copy_to_input_image(['default.conf'], '/etc/nginx/conf.d')
        container.copy_to_input_image(['data'], '/usr/share/nginx/html')
        container.prepare()
        container.run()

        host_port = container.get_port_mapping(8080)
        url = 'http://localhost:{}/index.html'.format(host_port)
        ready = False
        for _ in range(STARTUP_RETRIES):
            try:
                print('Fetching {}'.format(url))
                response = requests.get(url, timeout=1.0)
                ready = True
                break
            except Exception:
                print('Connecting to server failed, sleeping for retry')
                time.sleep(5)

        if not ready:
            raise test_utils.TimeoutException('Timed out waiting for server to be ready')

        # We read the large file several times, just to get more confidence that the server is actually working.
        for _ in range(TEST_ITERS):
            big_url = 'http://localhost:{}/data'.format(host_port, timeout=1.0)
            print('Fetching {}'.format(big_url))
            response = requests.get(big_url)
            if len(response.content) != TEST_FILE_SIZE:
                print('Response for large file had size {}'.format(len(response.content)))
                raise test_utils.TestException('Incorrect size for returned data')

        logs = container.logs()
        for line in logs.stdout and logs.stderr:
            if "Enclave console connection failure" in line:
                raise test_utils.TestException('Unexpected console connection failure observed')

        return True

if __name__ == '__main__':
    test_app.main(SelfProxy)