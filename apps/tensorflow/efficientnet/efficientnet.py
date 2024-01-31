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


class TestTf(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestTf, self).__init__(run_args, [])

    def run(self):

        # We need to have some containers with some models in the ecr to enable this test.
        # when this test is enabled, change rw_dirs to have only the necessary
        # of directories
        container = self.container('efficientnet', image_version='latest', registry='latest',
                                    rw_dirs=['/'], memsize='8192M', thread_num=512 )
        container.prepare()
        container.run()
        status = container.container.wait()['StatusCode']
        if (status != 0):
            print("Container returned non zero status : {}".format(status))
            raise

        return True

    def get_timeout(self):
      if os.environ.get('PLATFORM', 'linux') == 'sgx':
        return 4 * 60 * 60
      else:
        return 1 * 60 * 60

if __name__ == '__main__':
  test_app.main(TestTf)
