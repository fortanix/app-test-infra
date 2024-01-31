#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Running app test free-radius. ZIRC-4360. This is a server based
# application. This test doesn't send requests to the server for processing
# yet. It only checks if the server is up and running.

import test_app
import time


class TestFreeRadius(test_app.TestApp):
    retries = 10

    def run(self):
        container = self.container(
                'zapps/free-radius',
                image_version='2021081012-7386dc9',
                memsize='512M')
        container.prepare()
        container.run()

        for i in range(TestFreeRadius.retries):
            logs = container.container.logs()
            if b'Ready to process requests' in logs:
                print('Server is ready to process requests.')
                return True
            print('Unable to check if app is ready to process requests, retrying in 10 seconds...')
            time.sleep(10)

        return False

if __name__ == '__main__':
    test_app.main(TestFreeRadius)
