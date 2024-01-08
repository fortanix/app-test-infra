#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Stub for running tensorflow_serving container. The test is currently
# disabled. The test is using a container built by hand by Navlok
# instead of having the build scripts in zircon-apps, and the client
# program needs to be run by hand.
#

import test_app


class TestTensorflow(test_app.TestApp):
    def __init__(self, run_args, _):
        super(TestTensorflow, self).__init__(run_args, [])

    def run(self):
        container = self.container('demo-input-app',
                                   image_version='faster_rcnn_resnet_serving',
                                   #image_version='debug',
                                   registry='navlok',
                                   # For manual testing, using the host network
                                   # is easier. The host network shouldn't be
                                   # used when the test is automated.
                                   network_mode='host',
                                   rw_dirs='/',
                                   memsize='4G')
        container.prepare()
        container.run()

        time.sleep(120)
        return True

if __name__ == '__main__':
    test_app.main(TestTensorflow)
