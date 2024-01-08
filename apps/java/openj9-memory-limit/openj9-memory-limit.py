#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import os
import test_app
from datetime import datetime


def get_time_stamp():
    now = datetime.now()
    return now.strftime("%H:%M:%S")

class TestOpenJ9Mem(test_app.TestApp):
    default_timeout_s = 360

    def prepare_continer(self, max_mem):
        container = self.container(image='zapps/openjdk8-openj9',
                                   entrypoint=[
                                    '/opt/java/openjdk/bin/java',
                                    '-cp',
                                    '/root',
                                    'HelloWorld'
                                    ],
                                   memsize=max_mem, java_mode='OPENJ9',
                                   rw_dirs=['/root'],
                                   image_version = '2020051101-59d7e44')
        container.prepare()
        container.copy_file('classes/HelloWorld.class', '/root/');
        self.info('Running java hello world...', end='')
        return container;

    def run_container(self, max_mem):
        container=self.prepare_continer(max_mem);
        print("{}: Starting Container with max_mem = {}".format(get_time_stamp(), max_mem))
        container.run_and_search_logs('Hello, World', (self.run_count != 0))
        self.run_count = self.run_count + 1;



    def iterate_sizes(self):
        for max_mem in ['1G', '2G', '4G']:
            try:
                self.run_container(max_mem);
                print("Test: {} max_mem={} passed".format(get_time_stamp(), max_mem))
            except Exception as e:
                print("Test: {} max_mem={} failed - {}".format(get_time_stamp(),
                                                               max_mem, e));
                return False
        return True


    def __init__(self, run_args, test_arg_list):
        super(TestOpenJ9Mem, self).__init__(run_args)
        self.run_count=0;

    def get_timeout(self):
        return self.default_timeout_s

    def run(self):
        os.chdir(os.path.dirname(__file__))
        if self.iterate_sizes():
            self.info('done.')
            return True
        return False

if __name__ == '__main__':
    test_app.main(TestOpenJ9Mem)
