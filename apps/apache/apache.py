#!/usr/bin/python3

import argparse
import MySQLdb
import os
import requests
import subprocess
import test_app
from time import sleep


class TestApache(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestApache, self).__init__(run_args, [])
        parser = argparse.ArgumentParser(description='Apache test')
        self.args = parser.parse_args(test_arg_list)

    def generate_random_data(self):
        # Tuple of (file size, count of files)
        sizes = [(100, 100), (2*1024, 10), (10*1024, 5), (100*1024, 5), (1*1024*1024, 3), (10*1024*1024, 3)]
        webroot = 'root/rootfs/htdocs/random'
        os.makedirs(webroot, exist_ok=True)
        for (size, count) in sizes:
            os.makedirs('%s/%d' % (webroot, size), exist_ok = True)
            for n in range(1, count + 1):
                with open('%s/%d/%d' % (webroot, size, n), 'wb') as out_file:
                    out_file.write(os.urandom(size))

    def run(self):
        os.chdir(os.path.dirname(__file__))

        self.info('Starting httpd...', end='')
        memsize = '2048M'
        container = self.container('fortanix-httpd-2-php-5-sgx:20180109', memsize)
            # This will be needed later
            #env={
            #"APACHE_RUN_USER":"www-data", "APACHE_RUN_GROUP":"www-data",
            #"APACHE_RUN_DIR":"/var/run/apache2",
            #"APACHE_LOCK_DIR":"/var/lock/apache2",
            #"APACHE_LOG_DIR":"/var/log/apache2"
            #}
        container.prepare()
        container.run(
                app='/bin/httpd',
                args=["-X", # remove when ZIRC-348 fixes
                #args=['-D', 'FOREGROUND', # to enable debug 
                "-C", "ServerName 127.0.0.1",
                "-C" , "Listen 127.0.0.1:8000", 
                "-C" , "PidFile logs/httpd-127.0.0.1-8000.pid",  
                "-f", "/conf/httpd.conf"],
                options={
                    'sgx_enclave_size': memsize,
                    'sgx_thread_num': 5
                })

        # Wait till the server comes up
        resp = None
        for i in range(5):
            try:
                resp = requests.get('http://127.0.0.1:8000', timeout=20)
                break
            except Exception as e:
               # try again
                sleep(5)
        if (resp == None or resp.status_code != 200):
            container.dump_output()
            print('response from apache'+ resp.status_code)
            raise Exception('Apache not ready to server http://127.0.0.1:8000')

        self.info(' done.')
        self.info('Generating random data')
        self.generate_random_data()
        locust_result = subprocess.call(['locust',
            '--no-web',
            '--only-summary',
            '--locustfile=locustfile.py',
            '--clients=10',
            '--hatch-rate=200',
            '--num-request=2000',
            '--host=http://127.0.0.1:8000'])

        if locust_result != 0:
            self.error('HTTP testing with locust failed')
            return False
        else:
            return True

if __name__ == '__main__':
    test_app.main(TestApache)
