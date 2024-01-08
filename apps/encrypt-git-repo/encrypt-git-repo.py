#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import test_app
from test_utils import TestException


# Test for ZIRC-5252 - Encrypt a directory containing
# a git repository
class TestEncryptGitRepo(test_app.TestApp):
    def run(self):
        echo_string = 'hello from fortanix'
        container = self.container(
                'zapps/encrypt-git-repo',
                memsize='128M',
                image_version='2022022309-41fb514', encrypted_dirs=['/sgxtop'],
                entrypoint=['/usr/bin/echo', echo_string]
                )
        container.prepare()
        container.run()
        container.wait(expected_status=0)
        output = container.container.logs(stdout=True, stderr=False, timestamps=False, tail=100).decode('utf-8')
        if echo_string not in output:
            raise TestException('Expected string not found in output')

        return True

if __name__ == '__main__':
    test_app.main(TestEncryptGitRepo)
