#!/usr/bin/python3
#
# Copyright (C) 2018-2019, 2021 Fortanix, Inc. All Rights Reserved.
#
# Nginx test using wrk to download files from the server.
#
# This test is not a particularly realistic performance test, since the client and server will run on the same
# host. It does however test nginx stability in the face of a large number of requests. We have had multiple
# bugs in the past that have prevented this test from running successfully.
#
# This test may be run for a longer or shorter duration by passing a parameter "duration=<time>" at the end
# of the test command line. <time> may be specified as a number plus the suffix 's' for seconds, 'm' for minutes,
# or 'h' for hours. The default unit is seconds.
#

import os
import pandas
import time
from test_app import NativeContainer, TestApp, main
from test_utils import TestException, parse_time_string


class TestNginxWrk(TestApp):
    retries = 15
    EMAIL_CONTENT_FILE = 'email_content_file.html'

    def __init__(self, run_args, test_arg_list):
        super(TestNginxWrk, self).__init__(run_args)

        # The test script exercises 4 different sizes and exercises both HTTP and HTTPS. Each
        # combination is run for this many seconds. The default duration of 10s gives us about
        # a 3 minute runtime (plus startup time), which is reasonable for a CI run.
        duration = str(run_args.benchmark_duration) + 's'

        # I don't know if there's a way to parse the test-specific arguments using an argument parser. We
        # could restructure the test_app.main function and test_app.TestApp class so the subclass can add
        # test-specific arguments to the base argument parser.
        for arg in test_arg_list:
            arg = arg.strip()
            if arg.startswith('duration='):
                (_, duration) = arg.split('=', 1)
            else:
                raise TestException('Unknown additional argument: {}'.format(arg))

        self.duration = duration
        print ("== Duration for each benchmark param run is: {} ==".format(self.duration))

    def get_timeout(self):
        custom_timeout = 15 * parse_time_string(self.duration)
        return max(custom_timeout, self.default_timeout_s)

    # Function to parse the output and generate an html file to send via email
    def output_parser(self, http_port, https_port, output_of = 'Converted'):
        f = open('output.txt', 'r')
        lines = f.readlines()
        f.close()
        benchmark_result = dict()
        flag = False
        http_port = str(http_port)
        https_port = str(https_port)
        for line in lines:
            if http_port in line and 'Running' in line:
                key_size = line.split()[-1].split('/')[-1]
                if key_size in benchmark_result.keys():
                    benchmark_result[key_size]['HTTP'] = key_size
                    flag = 'HTTP'
                else:
                    benchmark_result[key_size] = dict()
                    benchmark_result[key_size]['HTTP'] = key_size
                    flag = 'HTTP'
            if https_port in line and 'Running' in line:
                key_size = line.split()[-1].split('/')[-1]
                if key_size in benchmark_result.keys():
                    benchmark_result[key_size]['SSL'] = key_size
                    flag = 'SSL'
                else:
                    benchmark_result[key_size] = dict()
                    benchmark_result[key_size]['SSL'] = key_size
                    flag = 'SSL'
            if 'Requests/sec' in line:
                req_per_sec = line.split()[-1]
                benchmark_result[key_size][flag] = req_per_sec
            else:
                continue

        print (benchmark_result)
        tabular_output = pandas.DataFrame(benchmark_result).T
        f = open('Nginx-Benchmark-Numbers.txt', 'a')
        f.write(output_of)
        f.write('\n')
        f.close()
        tabular_output.to_csv('Nginx-Benchmark-Numbers.txt', sep='\t', mode='a', header=True)
        f = open('Nginx-Benchmark-Numbers.txt', 'a')
        f.write('\n')
        f.write('=================================')
        f.write('\n')
        f.close()
        print (tabular_output)


    def create_and_run_nginx_benchmark(self):
        ports = {
            80: None,
            443: None,
        }


        container = self.container('zapps/nginx-bench', memsize='2G', network_mode='bridge',
                                   image_version='2021081711-6b31d3f',
                                   rw_dirs=['/var/cache/nginx', '/var/run','/run', '/etc/nginx'],
                                   ports=ports)
        container.prepare()
        container.run()

        http_port = container.get_port_mapping(80)
        https_port = container.get_port_mapping(443)


        # Wait until the server is serving requests. This can take a while especially on SGX.
        up = False
        for _ in range(TestNginxWrk.retries):
            retval = os.system('wget -nv -O /dev/null http://localhost:{}/1k'.format(http_port))
            if retval == 0:
                up = True
                break
            time.sleep(1)

        if not up:
            raise TestException('nginx is not responding')

        client = NativeContainer('zapps/nginx-client', network_mode='host',
                                 entrypoint=['/root/run.sh', 'localhost', str(http_port), str(https_port), self.duration],
                                 run_args=self.run_args)
        client.prepare()
        client.copy_file('run.sh', '/root')
        client.run()

        client.container.wait()
        client.copy_file_from_container('output.txt', 'output.txt')

        # We check that the server is still responding after running the wrk workload.
        # We've had issues in the past where the nginx server stops responding to requests
        # in the middle of the wrk workload. wrk assumes that the server is just overloaded
        # and doesn't return an error if there are failed connection attempts.
        retval = os.system('wget -nv -O /dev/null http://localhost:{}/1k'.format(http_port))
        if retval != 0:
            raise TestException('nginx not responding to http requests after wrk')

        self.output_parser(http_port, https_port, output_of = self.run_args.container_env)


    def run(self):
        self.create_and_run_nginx_benchmark()
        return True

if __name__ == '__main__':
    main(TestNginxWrk)
