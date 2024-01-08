#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Test to check that conversion fails with a relevant
# error message when input or output image registry
# credentials are incorrect

import json
import os
import test_app
import test_utils


class TestInvalidAuthConfig(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestInvalidAuthConfig, self).__init__(run_args, [])

    def run(self):
        status = False
        try:
            container = self.container('ajannu/private', registry='library',
                                       image_version='ns-app-nitro-1', allow_docker_pull_failure=True,
                                       input_auth_config = json.dumps({ "username":"ajannu", "password":"wrongpassword"}),
                                       memsize="2048M",
                                       cpu_count=2)
            container.prepare()
        except test_utils.TestException as e:
            if os.environ['PLATFORM'] == 'nitro':
                status = test_utils.check_conv_logs(path='logs/1.conv.err', match_str="unauthorized: incorrect username or password")
            else:
                status = test_utils.check_conv_logs(path='logs/1.conv.err', match_str="invalid input image auth credentials")

        return status


if __name__ == '__main__':
    test_app.main(TestInvalidAuthConfig)
