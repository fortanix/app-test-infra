#!/usr/bin/python3
#
# Copyright (C) 2021 Fortanix, Inc. All Rights Reserved.
#
# Test to check if docker needs write permission on any
# files under /etc directory.
#
# The current list of default rw files include:
#  * /etc/hosts
#  * /etc/resolv.conf
#  * /etc/hostname

import test_app

class RwFiles(test_app.TestApp):
    def __init__(self, run_args, _):
        super(RwFiles, self).__init__(run_args, [])

    def run(self):
        rw_dirs = [
            '/root'
        ]

        encrypted_dirs = [
            '/efs',
        ]

        container = self.container('zapps/ubuntu', image_version='2021080415-d0612f8',
                                   rw_dirs=rw_dirs, encrypted_dirs=encrypted_dirs,
                                   memsize="128M",
                                   entrypoint=['/root/entrypoint.py'])
        container.prepare()
        container.copy_file('entrypoint.py', '/root')
        container.run()
        container.wait()
        return True

if __name__ == '__main__':
    test_app.main(RwFiles)
