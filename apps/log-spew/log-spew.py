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
from test_utils import TestException


class TestLogSpew(test_app.TestApp):
    def __init__(self, run_args, _):
        super(TestLogSpew, self).__init__(run_args, [])

    def run(self):
        container = self.container(test_app.BASE_UBUNTU_CONTAINER, registry='library',
                                   memsize='512M',
                                   image_version=test_app.BASE_UBUNTU_VERSION,
                                   entrypoint=[
                                    '/bin/bash',
                                    '-c', 'i=1; while [[ $i -lt 1000000 ]] ; do echo $i ; i=$((i + 1)) ; done'
                                   ])

        container.prepare()
        container.run()
        # If you created the container without pexpect=False, this wait will block forever because the pipe
        # for standard output will fill up and will block the container from running.
        container.container.wait()

        # The test infrastructure takes care of automatically stopping test containers, but we want to go
        # ahead and stop it now so the logs will be extracted.
        container.stop()

        # Check that the output was properly captured. We grabbed the output with timestamps, so be careful
        # with how we format our regular expressions.
        stdout_filename = 'logs/{}.stdout.0'.format(container.name)

        # We used to check for the beginning of the log output, but the log extraction code got changed to
        # only save the tail of the log. If we make changes to allow keeping all of the log, we can bring this
        # code back.
        #retval = os.system('grep -q " 1\$" {}'.format(stdout_filename))
        #if retval != 0:
        #    raise TestException('Could not find beginning of log output')
        retval = os.system('grep -q " 999999\$" {}'.format(stdout_filename))
        if retval != 0:
            raise TestException('Could not find end of log output')

        return True

if __name__ == '__main__':
    test_app.main(TestLogSpew)
