#!/usr/bin/python3
#
# Copyright (C) 2018 Fortanix, Inc. All Rights Reserved.
#
# Websphere test

import filecmp
import os
from test_app import TestApp, main
from test_utils import TestException
import time

class TestWebsphere(TestApp):
    retries = 60
    saved_file = 'index.html'
    expected_index_file = None

    def __init__(self, run_args, test_arg_list):
        super(TestWebsphere, self).__init__(run_args)

    def run(self):
        try:
            os.remove(TestWebsphere.saved_file)
        except OSError:
            pass

        port = 9080

        # Note about rw_dirs - Filesystem directories with read-write permission. It is recommended we
        # specify directories with this permission cautiously (if these directories contain executable
        # content it could potentially be a security vulnerability).
        # For open-liberty-servers the ${server.output.dir} or WLP_OUTPUT_DIR specifies the directory
        # where the server should write files to (includes the workarea, logs and other runtime
        # generated files. Source: https://openliberty.io/docs/ref/config/
        extra_container_args = {}
        image_version = None
        if os.environ['PLATFORM'] == "nitro":
            input_image = 'websphere-liberty'
            image_version = '23.0.0.2-full-java17-openj9'
            extra_container_args['registry'] ='library'
            TestWebsphere.expected_index_file = 'nitro-output.html'
            extra_container_args['container_env'] = {'ENCLAVEOS_DISABLE_DEFAULT_CERTIFICATE' : 'true'}
        else:
            input_image = 'zapps/websphere-liberty'
            TestWebsphere.expected_index_file = 'reference-output.html'

        container = self.container(input_image, memsize='2G',
                                   ports={ port: None }, image_version=image_version,
                                   rw_dirs=['/logs', '/opt/ibm'],
                                   manifest_env=['WLP_SKIP_BOOTSTRAP_AGENT=1'],
                                   java_mode='LIBERTY-JRE',
                                   thread_num=128,                                   
                                   **extra_container_args)
        container.prepare()
        container.run()

        # We need to look up what host ports these got mapped to by Docker.
        http_port = container.get_port_mapping(port)

        print('websphere running with http on port {}'.format(http_port))

        # Wait for the server to start
        for _ in range(TestWebsphere.retries):
            retval = os.system('wget -nv -O {} http://localhost:{}'.format(TestWebsphere.saved_file, http_port))
            if (retval == 0):
                break
            time.sleep(15)

        if not os.path.isfile(TestWebsphere.saved_file):
            raise TestException('Unable to connect with HTTP')

        tries = 0
        while True:
            tries = tries + 1
            if tries > TestWebsphere.retries:
                raise TestException("Didn't get correct index file after {} attempts", TestWebsphere.retries)

            retval = os.system('wget -nv -O {} http://localhost:{}'.format(TestWebsphere.saved_file, http_port))

            if not os.path.isfile(TestWebsphere.saved_file):
                raise TestException('Unable to connect')

            if filecmp.cmp(TestWebsphere.saved_file, TestWebsphere.expected_index_file):
                break

            # Early in startup, websphere returns a different index page.
            # If we get the alternate index page, retry.
            if not filecmp.cmp(TestWebsphere.saved_file, 'alternate-output.html'):
                raise TestException('Websphere returned incorrect data');

            print('Got alternate index page, retry')

            time.sleep(5)

        return True

if __name__ == '__main__':
    main(TestWebsphere)
