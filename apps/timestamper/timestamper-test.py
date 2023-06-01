#!/usr/bin/python3
#
# Copyright (C) 2019 Fortanix, Inc. All Rights Reserved.
#
# Run timestamper test.  Our timestamp query script is in the same
# docker image as the timestamper server.  We convert and run the
# server in Zircon, and then run the query script natively.
#
# Copied from the nginx-wrk tests, which warns that "this test is
# not a particularly realistic performance test, since the client
# and server will run on the same  host."
#

import os
from test_app import DEFAULT_IMAGE_VERSION, DOCKER_REGISTRY, main, \
                     NativeContainer, TestApp
from test_utils import TestException, parse_time_string
import time


class TestTimestamper(TestApp):
    retries = 30
    # Only necessary until we rebuild zapps:
    version = '20190917-7b34e11'

    def __init__(self, run_args, test_arg_list):
        super(TestTimestamper, self).__init__(run_args)

        self.zircon_benchmark = {}

    def create_and_run_timestamper_benchmark(self):
        ports = {
            8318: None,
        }

        server = self.container('zapps/timestamper',
                                network_mode='bridge',
                                memsize='512M',
                                rw_dirs=['/'],
                                image_version=self.version,
                                ports=ports)
        server.prepare()
        server.run()

        timestamp_port = server.get_port_mapping(8318);

        # Wait until the server is serving requests. This can take
        # a while, especially on SGX.
        up = False
        for _ in range(TestTimestamper.retries):
            # For better or worse, this logs each error as it fails;
            # all the rest of the tests do this, so perhaps it's a win.
            retval = os.system('wget -nv -O /dev/null --timeout 10 {}:{}/'
                               .format('http://localhost', timestamp_port))
            if retval == 0:
                up = True
                break
            time.sleep(1)

        if not up:
            raise TestException('timestamper is not responding')

        # Note that if we want to reproduce thread memory leak
        # errors, we can pass a third argument for number of
        # operations to the entrypoint.  This defaults to 1,000,
        # but 42,000 will definitely trigget the issue.
        client = NativeContainer('zapps/timestamper',
                                 image_version=self.version,
                                 network_mode='container:{}'
                                    .format(server.container.name),
                                 entrypoint=['/root/ts-query.py'],
                                 run_args=self.run_args)
        client.prepare()
        client.run()

        client.container.wait()
        client_result = client.container.logs().decode('utf-8')

        server.container.stop()
        server_result = server.container.logs().decode('utf-8')

        if 'ops/sec' not in client_result:
            print(client_result)
            print(server_result)
            raise TestException('no client benchmark results')

        # This is unlikely to happen if the client ran successfully
        if 'POST /' not in server_result:
            print(client_result)
            print(server_result)
            raise TestException('server log of responses missing')

        # Pull and report the results
        for l in client_result.splitlines():
            if 'sec' in l:
                print('Results:  {}'.format(l))

        return True

    def run(self):
        return self.create_and_run_timestamper_benchmark()

if __name__ == '__main__':
    main(TestTimestamper)
