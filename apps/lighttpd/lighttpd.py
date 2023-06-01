#!/usr/bin/python3

import argparse
import json
import os
import subprocess
import tarfile
import tempfile
import test_app
import test_utils
from test_utils import get_locust_version

LIGHTTPD_PORT = 8000

retries = 120

locust_log = 'locust.log'

class TestLighttpd(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestLighttpd, self).__init__(run_args, [])
        parser = argparse.ArgumentParser(description='Lighttpd test')
        parser.add_argument('-t', '--threads', type=int, help='number of server threads')
        self.args = parser.parse_args(test_arg_list)

    def generate_random_data(self, tar):
        # Tuple of (file size, count of files)
        sizes = [(100, 100), (2*1024, 10), (10*1024, 5), (100*1024, 5), (1*1024*1024, 3), (10*1024*1024, 3)]

        with tempfile.TemporaryDirectory() as tempdir:
            for (size, count) in sizes:
                os.makedirs(os.path.join(tempdir, str(size)), exist_ok=True)
                for n in range(1, count + 1):
                    with open(os.path.join(tempdir, str(size), str(n)), 'wb') as out_file:
                        out_file.write(os.urandom(size))

            tar = tarfile.open(tar, mode='w')
            tar.add(tempdir, arcname='html/random')
            tar.close()
            return

    def run(self):
        os.chdir(os.path.dirname(__file__))
        s = {}

        tar = os.getcwd() + '/test_lt.tar'
        self.generate_random_data(tar)
        s[tar] = '/'
        tar2 = os.getcwd() + '/tar2.tar'
        ret = self.create_tar_for_copying(['lighttpd.conf'], tar2)

        if (ret == False):
            raise Exception('Failed to create tar file')
        s[tar2] = '/etc/lighttpd/'

        self.info('Starting lighttpd...', end='')

        ports = {
            LIGHTTPD_PORT: None
        }
        dirs_to_copy = json.dumps(s)
        container = self.container('zapps/lighttpd', memsize='512M', ports=ports,
                rw_dirs=['/html'], dirs_to_copy=dirs_to_copy)
        container.prepare()

        container.run()

        port = container.get_port_mapping(LIGHTTPD_PORT)

        test_utils.wait_for_server(port=port, path='random/100/1', retries=retries)
        locust_result = 0
        time_s = 5
        locust_version = get_locust_version()
        print('locust_version = ', locust_version)

        locust_result = subprocess.call(['locust',
                                     '--headless',
                                     '--only-summary',
                                     '--locustfile=locustfile.py',
                                     '--users=10',
                                     '--run-time={}s'.format(time_s),
                                     '--spawn-rate=100',
                                     '--loglevel=INFO',
                                     '--logfile={}'.format(locust_log),
                                     '--host=http://127.0.0.1:{}'.format(port)])

        if locust_result != 0:
            container.dump_output()
            self.info('')
            self.error('HTTP testing with locust failed')
            return False
        else:
            return True

if __name__ == '__main__':
    test_app.main(TestLighttpd)
