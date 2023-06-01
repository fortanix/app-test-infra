#!/usr/bin/python3

import os
import subprocess
import test_app
import test_utils
import time
import argparse
from test_utils import get_locust_version

BARBICAN_PORT = 9311

retries = 600

locust_log = 'locust.log'

class TestBarbican(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestBarbican, self).__init__(run_args, [])
        parser = argparse.ArgumentParser(description='Barbican test')
        self.args = parser.parse_args(test_arg_list)

    def run(self):
        os.chdir(os.path.dirname(__file__))

        self.info('Starting barbican...')

        ports = {
            BARBICAN_PORT: None,
        }

        container = self.container('zapps/barbican', memsize='2048M',
                    thread_num=64, encrypted_dirs=['/tmp', '/var/lib/barbican'], ports=ports)
        container.prepare()
        container.run()

        port = container.get_port_mapping(BARBICAN_PORT)

        self.info('Waiting for barbican to serve requests')

        # On SGX, barbican takes much longer to start, so go to sleep for a while before even starting
        # to poll for the server.
        if test_utils.is_sgx():
            time.sleep(120)

        test_utils.wait_for_server(port=port, path='/v1/secrets', retries=retries, headers=['X-Project-Id: 12345'])

        self.info('Barbican started successfully')
        locust_version = get_locust_version()
        print('locust_version = ', locust_version)
        time_s = 5

        subprocess.check_output(['locust',
                                 '--headless',
                                 '--only-summary',
                                 '--locustfile=locustfile.py',
                                 '--users=10',
                                 '--run-time={}s'.format(time_s),
                                 '--spawn-rate=100',
                                 '--loglevel=INFO',
                                 '--logfile={}'.format(locust_log),
                                 '--host=http://127.0.0.1:{}'.format(port)])

        return True


if __name__ == '__main__':
    test_app.main(TestBarbican)
