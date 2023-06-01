#!/usr/bin/python3

import argparse
import filecmp
import os
import re
import test_app
import time
from test_utils import TestException

class TestOLMicroprofile(test_app.TestApp):
    retries = 60
    saved_home_file    = 'index.html'
    saved_health_file  = 'health.html'
    saved_openapi_file = 'openapi.html'

    def __init__(self, run_args, test_arg_list):
        super(TestOLMicroprofile, self).__init__(run_args, [])
        parser = argparse.ArgumentParser(description='Open Liberty Microprofile Test')
        self.args = parser.parse_args(test_arg_list)

    def run(self):
        os.chdir(os.path.dirname(__file__))

        ports = { 9080: None, 9443: None }

        # Note about rw_dirs - Filesystem directories with read-write permission. It is recommended we
        # specify directories with this permission cautiously (if these directories contain executable
        # content it could potentially be a security vulnerability).
        # For open-liberty-servers the ${server.output.dir} or WLP_OUTPUT_DIR specifies the directory
        # where the server should write files to (includes the workarea, logs and other runtime
        # generated files. Source: https://openliberty.io/docs/ref/config/

        container = self.container(image='zapps/open-liberty-microprofile-2',
                                   ports=ports,
                                   rw_dirs=['/wlp', '/usr/lib', '/opt/java'],
                                   encrypted_dirs=['/tmp'],
                                   memsize='2048M',
                                   thread_num=80,
                                   java_mode='OPENJ9')
        container.prepare()
        container.run()

        url = 'http://{}:{}/'.format(container.get_my_ip(), 9080)
        #TODO: ZIRC-1795. Open liberty unable to support SSL in zircon.
        #ssl_url = 'https://{}:{}/'.format(container.get_my_ip(), 9443)

        # __________ Open Liberty Server ___________
        self.info('Testing if the Open Liberty Server is up...')
        running = False
        for i in range(TestOLMicroprofile.retries):
            ret = os.system('wget -nv -O {} {}'.format(TestOLMicroprofile.saved_home_file, url))
            if ret == 0:
                running = True
                print('Open Liberty Server is responsive, continuing to test')
                break
            time.sleep(15)

        if not running or not os.path.isfile(TestOLMicroprofile.saved_home_file):
            raise TestException('Open Liberty Server is not responding')

        self.info('Open Liberty Server is running on {}'.format(url))

        if not filecmp.cmp(TestOLMicroprofile.saved_home_file, 'reference-index-file.html'):
            raise TestException('Web server returned incorrect index data')

        # __________ Microprofile health ___________
        self.info('Testing if the Microprofile health web app is up...')
        running = False
        for i in range(TestOLMicroprofile.retries):
            ret = os.system('wget -nv -O {} {}'.format(TestOLMicroprofile.saved_health_file, url + 'health/'))
            if ret == 0:
                running = True
                break
            time.sleep(15)

        if not running or not os.path.isfile(TestOLMicroprofile.saved_health_file):
            raise TestException('Microprofile health is not responding')

        if not filecmp.cmp(TestOLMicroprofile.saved_health_file, 'reference-health-file.html'):
            raise TestException('Microprofile health returned incorrect data')

        # __________ Microprofile OpenApi ___________
        self.info('Testing if the Microprofile OpenApi web app is up...')
        running = False
        for i in range(TestOLMicroprofile.retries):
            ret = os.system('wget -nv -O {} {}'.format(TestOLMicroprofile.saved_openapi_file, url + 'openapi/'))
            if ret == 0:
                running = True
                break
            time.sleep(15)

        if not running or not os.path.isfile(TestOLMicroprofile.saved_openapi_file):
            raise TestException('Microprofile OpenApi is not responding')

        # We can't compare the files entirely since they contain URL info which can differ
        # in different runs. Here we remove the URL and then compare the file data
        with open(TestOLMicroprofile.saved_openapi_file, "r") as read_file:
            saved_file_data = read_file.read()
        saved_file_modified_data = re.sub(r'http?:\/\/.*[\r\n]*', '', saved_file_data, flags=re.MULTILINE)
        with open('reference-openapi-file.html', "r") as read_ref_file:
            ref_file_data = read_ref_file.read()
        ref_file_modified_data = re.sub(r'http?:\/\/.*[\r\n]*', '', saved_file_data, flags=re.MULTILINE)
        if ref_file_modified_data != saved_file_modified_data:
            raise TestException('Microprofile OpenApi return incorrect data')

        return True

if __name__ == '__main__':
    test_app.main(TestOLMicroprofile)
