#!/usr/bin/python3
#
# Copyright (C) 2019 Fortanix, Inc. All Rights Reserved.
#
# Description : This app test runs all of the openjdk tests.
#

import os
import test_app
import time

from test_utils import TestException

class TestOpenJdk(test_app.TestApp):
    test_image_name = 'zapps/openjdk-tests'
    # We don't regularly build the openjdk tests image with zircon-apps builds
    # because it is 5GB large. The version here is identifying a manual build
    # that was pushed to the docker registry.
    test_image_version = '1'
    test_file = 'subset.tests'

    # Override the get_timeout function to set custom app test timeouts
    def get_timeout(self):
        if os.environ['PLATFORM'] == 'sgx':
            return 192 * 60 * 60
        else:
            return 160 * 60 * 60

    def __init__(self, run_args, test_arg_list):
        super(TestOpenJdk, self).__init__(run_args, [])
        if len(test_arg_list) > 0:
            if len(test_arg_list) > 1:
                raise TestException('too many arguments')
            else:
                self.test_file = test_arg_list[0]

    def run_test_dir(self, test_file):

        test_container = None

        test_env = [
            'MALLOC_ARENA_MAX=1',
            '_JAVA_OPTIONS="-XX:CompressedClassSpaceSize=32m -XX:ReservedCodeCacheSize=16m -XX:-UseCompiler -XX:+UseSerialGC -XX:-UsePerfData -Xmx960m -Xint -XX:+UseMembar"',
            'USE_ENCLAVEOS=1',
            'PLATFORM={}'.format(os.environ['PLATFORM']),
            # Save some time in a throw-away container:
            'SUPPRESS_CORE_DUMP=true',
        ]

        test_path = os.path.join("/root", test_file)
        post_conv_entry_point = '/root/entrypoint.sh ' + test_path
        test_container = self.container(image=self.test_image_name,
                                        image_version=self.test_image_version,
                                        network_mode='host',
                                        memsize='2G',
                                        thread_num=128,
                                        manifest_env=test_env,
                                        entrypoint=['/bin/bash'],
                                        rw_dirs=['/'],
                                        post_conv_entry_point=post_conv_entry_point)
        # Note that the resulting container, as started by our framework,
        # correctly runs /root/entrypoint.sh outside the enclave.
        # Alas, if the image is saved, it defaults to running the enclave,
        # so it's tougher to do useful debugging with this.  It appears that
        # when the converted docker image has no entrypoint, we get
        # a more useable test image without an explcit enclaveos-runner
        # entrypoint.
        test_container.prepare()
        start_time = time.time()
        test_container.run()
        test_container_output = test_container.container.wait()

        # Since we do not have a 100% pass rate at the moment, we ignore
        # the container exit status
        if test_container_output['StatusCode'] != 0:
            print("Container returned non zero status = {}\n".format(test_container_output['StatusCode']))

        end_time = time.time()

        # Display summary and time taken to run the test suite
        print ()
        hrs, rem = divmod(end_time - start_time, 3600)
        mins, secs = divmod(rem, 60)
        print ('Time was (HH:MM:SS) = {:0>2}:{:0>2}:{:05.2f}' \
            .format(int(hrs), int(mins), int(secs)))

        print('Attempting to copy test reports from the container')
        test_log = test_file + ".log"
        test_log_path = os.path.join("/root", test_log)
        test_full_log = test_file + "-full.log"
        test_full_log_path= os.path.join("/root", test_full_log)
        test_container.copy_file_from_container(test_log_path, test_log)
        test_container.copy_file_from_container(test_full_log_path,
                                                test_full_log)

        # File looks like:
        # com/oracle/net/sanity.sh Test results: passed: 1
        okay = False
        test_summary = open(test_log, "r")
        total = {}
        for line in test_summary:
            a = line.split()
            print(a[0], end = ' ')
            # Skip the "Test results:"
            if len(a) < 4:
                print("Line too short, no results: {}".format(line))
                return False
            for i in range(3, len(a), 2):
                which = a[i]
                # If at least one test passed, we might be okay
                if which == 'passed:':
                    okay = True
                value = a[i + 1]
                if value[-1] == ';':
                    value = value[:-1]
                print(which, value)
                if which in total:
                    total[which] += int(value)
                else:
                    total[which] = int(value)

        print('Total ', end = '')
        for which, value in total.items():
            # If we saw even one non-pass, we should fail
            if which != 'passed:':
                okay = False
            print(which, value, end=' ')
        print()
        return okay

    def run(self):
        os.chdir(os.path.dirname(__file__))

        return self.run_test_dir(self.test_file)

if __name__ == '__main__':
    test_app.main(TestOpenJdk)
