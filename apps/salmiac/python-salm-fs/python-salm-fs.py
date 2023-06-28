#!/usr/bin/python3
#
# Copyright (C) 2022 Fortanix, Inc. All Rights Reserved.
#
# Test to check file writes and reads data between flushing
# the kernel filesystem cache

from test_app import TestApp, main, SMARTKEY_ENDPOINT
import os

class TestPythonSalmFS(TestApp):

    def __init__(self, run_args, test_arg_list):
        super(TestPythonSalmFS, self).__init__(run_args, [])

    def run(self):
        #TODO: Update test to not use environment variables to pass VSK details
        dsm_endpoint_env_var = 'FS_VSK_ENDPOINT={}'.format(SMARTKEY_ENDPOINT)
        dsm_api_key = 'FS_API_KEY={}'.format(os.getenv('FORTANIX_API_KEY', None))
        container = self.container('python', registry='docker.io', image_version='slim-bullseye',
                                   memsize='2048M',
                                   entrypoint=['/root/read-write.py'],
                                   enable_overlay_fs_persistence=True,
                                   container_env=['ENCLAVEOS_DEBUG=debug', 'RUST_LOG=info',
                                                  dsm_endpoint_env_var,
                                                  dsm_api_key])
        container.copy_to_input_image(['flushcache.sh', 'read-write.py', 'testfile'], '/root/')
        container.prepare()
        container.run()
        container.wait(expected_status=0)

        expected_output = ['RO layer testfile contains expected data',
                           '### Test 1 complete ###',
                           'File /root/testfile2 contains expected data',
                           '### Test 2 complete ###',
                           '### Test 3 part 1 complete ###',
                           'File /root/testfile3 contains expected data',
                           '### Test 3 part 2 complete ###']
        container.run_and_search_multiple_lines_logs(expected_lines=expected_output, rerun=True)

        return True

if __name__ == '__main__':
    main(TestPythonSalmFS)