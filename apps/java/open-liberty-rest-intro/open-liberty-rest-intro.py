#!/usr/bin/python3

import argparse
import filecmp
import json
import os
import test_app
import time
from test_utils import TestException


class TestOLRestIntro(test_app.TestApp):
    retries = 60
    saved_home_file = 'index.html'
    saved_properties_file = 'properties.html'

    def __init__(self, run_args, test_arg_list):
        super(TestOLRestIntro, self).__init__(run_args, [])
        parser = argparse.ArgumentParser(description='Open Liberty Rest Test')
        self.args = parser.parse_args(test_arg_list)

    def run(self):
        os.chdir(os.path.dirname(__file__))

        ports = { 9080: None }

        # Note about rw_dirs - Filesystem directories with read-write permission. It is recommended we
        # specify directories with this permission cautiously (if these directories contain executable
        # content it could potentially be a security vulnerability).
        # For open-liberty-servers the ${server.output.dir} or WLP_OUTPUT_DIR specifies the directory
        # where the server should write files to (includes the workarea, logs and other runtime
        # generated files. Source: https://openliberty.io/docs/ref/config/
        container = self.container('zapps/open-liberty-rest-intro',
                                   ports=ports,
                                   java_mode='OPENJ9',
                                   memsize='2048M',
                                   rw_dirs=['/target/liberty/wlp', '/usr/lib','/opt/java'],
                                   encrypted_dirs=['/tmp'],
                                   thread_num=1024,
                                   auto_remove=False)
        container.prepare()
        container.run()

        # TODO: Can we get this from the container, instead of hard coding it
        app_name = 'guide-rest-intro'
        url = 'http://localhost:{}/{}/'.format(container.get_port_mapping(9080), app_name)
        service_url = url + 'System/properties/'
        running = False
        for i in range(TestOLRestIntro.retries):
            ret = os.system('wget -nv -O /dev/null {}'.format(service_url))
            if ret == 0:
                running = True
                print('Open Liberty Rest Service is responsive, continuing to test')
                break
            time.sleep(15)

        if not running:
            raise TestException('Open Liberty Rest Service is not responding')

        ret = os.system('wget -O {} {}'.format(TestOLRestIntro.saved_home_file, url))
        if ret != 0:
            raise TestException('Unable to get home page')

        if not filecmp.cmp(TestOLRestIntro.saved_home_file, 'reference_home_file.html'):
            raise TestException('Web service returned incorrect index data')

        ret = os.system('wget -O {} {}'.format(TestOLRestIntro.saved_properties_file, service_url))
        if ret != 0:
            raise TestException('Unable to get system properties')

        # We can't compare the system properties file using filecmp because
        # it contains a property (kernel launch time) which varies with
        # every run. Here we remove that property and then compare the
        # json files
        with open(TestOLRestIntro.saved_properties_file, "r") as read_file:
            file_data = json.load(read_file)
        del file_data['kernel.launch.time']

        with open('reference_properties_file.html', "r") as read_ref_file:
            ref_file_data = json.load(read_ref_file)
        del ref_file_data['kernel.launch.time']

        if file_data != ref_file_data:
            raise TestException('Web service returned incorrect properties data')

        return True

if __name__ == '__main__':
    test_app.main(TestOLRestIntro)
