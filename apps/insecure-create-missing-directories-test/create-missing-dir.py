#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import test_app
import test_utils

class TestMissingDirsCreate(test_app.TestApp):
    def run(self):
        missing_dir_name = '/missing-dir'
        present_dir_name = '/root'

        # Test Case 1: insecure_create_missing_directories=true and no missing dir supplied
        # Expectation: Success
        container = self.container('zapps/static', memsize='128M', insecure_create_missing_directories=True)
        container.prepare()

        # Test Case 2: insecure_create_missing_directories=false and no missing dir supplied
        # Expectation: Success
        container = self.container('zapps/static', memsize='128M', insecure_create_missing_directories=False)
        container.prepare()

        # Test Case 3: insecure_create_missing_directories=True and missing dir supplied
        # Expectation: Success
        container = self.container('ubuntu',
                                    registry='library',
                                    image_version='20.04',
                                    memsize='128M',
                                    insecure_create_missing_directories=True,
                                    encrypted_dirs=['/missing-dir'],
                                    entrypoint=['/usr/bin/stat', '-c', '\"%a%G\"',
                                                 missing_dir_name])
        container.prepare()
        container.run_and_compare_stdout(['777root'])

        # Test Case 4: insecure_create_missing_directories=False and missing dir supplied
        # Expectation: Conversion failure
        err_msg = '/opt/fortanix/enclave-os/bin/integrity-info compute /missing-dir /opt/fortanix/enclave-os/rofs-hashes/03.hashes'
        status = False
        try:
            container = self.container('ubuntu',
                                        registry='library',
                                        image_version='20.04',
                                        memsize='128M',
                                        insecure_create_missing_directories=False,
                                        encrypted_dirs=['/missing-dir'],
                                        entrypoint=['/usr/bin/ls', '-l', missing_dir_name])
            container.prepare()
        except Exception as e :
            status = test_utils.check_conv_logs(path='logs/4.conv.err', match_str=err_msg)
        if (not status):
            return status

        # Test Case 5:  insecure_create_missing_directories is not explicitly set
        # (default is false) and missing dir supplied.
        # Expectation: Conversion failure
        status = False
        try:
            container = self.container('ubuntu',
                                        registry='library',
                                        image_version='20.04',
                                        memsize='128M',
                                        encrypted_dirs=['/missing-dir'],
                                        entrypoint=['/usr/bin/ls', '-l', missing_dir_name])
            container.prepare()
        except Exception as e :
            status = test_utils.check_conv_logs(path='logs/5.conv.err', match_str=err_msg)
        if (not status):
            return status

        # Test Case 6:  insecure_create_missing_directories is set to true and
        # some existing directory is set
        # Expectation: Conversion should succeed and no change to the existing
        # directory
        status = False
        expected_string = "700root"
        container = self.container('ubuntu',
                                    registry='library',
                                    image_version='20.04',
                                    memsize='128M',
                                    encrypted_dirs=[present_dir_name],
                                    insecure_create_missing_directories=True,
                                    entrypoint=['/usr/bin/stat', '-c', '\"%a%G\"', present_dir_name])
        container.prepare()
        container.run_and_compare_stdout([expected_string])
        return True

if __name__ == '__main__':
    test_app.main(TestMissingDirsCreate)
