#!/usr/bin/python3
#
# Copyright (C) 2021 Fortanix, Inc. All Rights Reserved.
#
# This test exercises some behavior related to changing file ownership
# and processes changing user. This has to be done as an application test
# because our regression test infrastructure doesn't have a convenient way
# to run processes as root, which is (usually) required for chown.
#
# Regression test for ZIRC-1366.
#
# Most of the testing is done in Python wtih entrypoint.py. Most of the
# functionality we require is available in python. We don't really have
# build infrastructure for writing tests in C that will run inside of app
# containers.
# 

import test_app


class Chown(test_app.TestApp):
    def __init__(self, run_args, _):
        super(Chown, self).__init__(run_args, [])

    def run(self):
        rw_dirs = [
            '/root',
            '/test',
        ]

        encrypted_dirs = [
            '/efs',
        ]

        container = self.container('zapps/ubuntu', image_version='2021080415-d0612f8',
                                   rw_dirs=rw_dirs, encrypted_dirs=encrypted_dirs,
                                   memsize="128M",
                                   entrypoint=['/root/entrypoint.py'],
                                   post_conv_entry_point='/root/test-runner.sh')
        container.prepare()
        container.copy_files(['entrypoint.py', 'test-runner.sh'], '/root')
        container.run()
        container.wait()
        return True

if __name__ == '__main__':
    test_app.main(Chown)
