#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# JTA Test using Narayana Toolkit

import argparse
import os
from test_app import TestApp, main


class TestJTA(TestApp):
    test_timeout = 1500
    file_name = 'jtatests01.txt'
    test_log_file = '/narayana/qa/TEST-org.jboss.jbossts.qa.junit.testgroup.TestGroup_'

    def __init__(self, run_args, test_arg_list):
        super(TestJTA, self).__init__(run_args, [])
        parser = argparse.ArgumentParser(description='JTA Narayana test')
        self.args = parser.parse_args(test_arg_list)

    def get_timeout(self):
        return self.test_timeout

    def run(self):
        # This test should not use `latest` as an image version. Do not copy this when adding new app tests.
        container = self.container('narayana-jta-tests-image',
                                    memsize='2G',
                                    image_version='latest',
                                    thread_num = 128,
                                    rw_dirs = ['/'],
                                    java_mode='OPENJDK')

        container.prepare()
        container.run()
        container.wait()
        logs = container.logs()
        print (logs.stdout)
        print (logs.stderr)
        cwd = os.path.dirname(os.path.realpath(__file__))
        full_path = os.path.join(cwd, self.file_name)
        container.copy_file_from_container(self.test_log_file + self.file_name, full_path)
        out = any("BUILD SUCCESSFUL" in s for s in logs.stdout)
        if out:
            container.save_log_file()
        return (out)

if __name__ == '__main__':
    main(TestJTA)
