#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Test to check file writes and reads data between flushing
# the kernel filesystem cache and container restarts.
#
# Also check username and hostname listed in the enclave
# kernel

import os
from test_app import SMARTKEY_ENDPOINT, TestApp, main


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
                                   container_env=['ENCLAVEOS_DEBUG=debug',
                                                  'RUST_LOG=info',
                                                  'ENCLAVEOS_DISABLE_DEFAULT_CERTIFICATE=true',
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
                           '### Test 3 part 2 complete ###',]

        #                   'Linux version 4.14.246 (root@Linux) (gcc version 9.4.0 (Ubuntu 9.4.0-1ubuntu1~20.04.2))']
        # Last expected_output is a sub test for SALM-352 which ensures the use of updated linux kernel
        container.run_and_search_multiple_lines_logs(expected_lines=expected_output, rerun=True)

        return True

if __name__ == '__main__':
    main(TestPythonSalmFS)
