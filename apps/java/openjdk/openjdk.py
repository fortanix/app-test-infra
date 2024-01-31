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


class TestOpenjdk(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestOpenjdk, self).__init__(run_args)

    def run(self):
        os.chdir(os.path.dirname(__file__))

        # This test is special. The container is just called openjdk, not zapps/openjdk.
        # -XX:-UsePerfData disables writing hsperfdata, which matters because
        # it uses writeable mmaps.
        container = self.container(image='openjdk',
                                   image_version='8u181-jre',
                                   registry='library',
                                   memsize='256M',
                                   entrypoint=[
                                    '/usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java',
                                    '-Xmx4m',
                                    '-cp',
                                    '/root',
                                    'HelloWorld'
                                   ],
                                   java_mode='OPENJDK',
                                   rw_dirs = ['/root'])
        container.prepare()
        container.copy_file('classes/HelloWorld.class', '/root/');

        self.info('Running java hello world...', end='')

        container.run_and_compare_stdout(['Hello, World'])

        self.info(' done.')

        return True

if __name__ == '__main__':
    test_app.main(TestOpenjdk)
