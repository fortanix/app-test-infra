#!/usr/bin/python3
#
# Copyright (C) 2021 Fortanix, Inc. All Rights Reserved.
#
# Remove /.dockerenv and add a dummy /.dockerinit file to
# the container before starting the application. Then run the
# the app (which lists the root directory and tries to
# access one of those files). This should not result in
# a filesystem integrity failure.

import test_app


class UnprotectedFiles(test_app.TestApp):
    def __init__(self, run_args, _):
        super(UnprotectedFiles, self).__init__(run_args, [])

    def run(self):
        rw_dirs = [
            '/root',
            '/test',
        ]

        encrypted_dirs = [
            '/efs',
        ]

        container = self.container('zapps/ubuntu', memsize='128M', image_version='2021080415-d0612f8',
                                   rw_dirs=rw_dirs, encrypted_dirs=encrypted_dirs,
                                   entrypoint=['/root/entrypoint.sh'],
                                   post_conv_entry_point=['/root/post-conv-entrypoint.sh'])
        container.prepare()
        container.copy_file('entrypoint.sh', '/root')
        container.copy_file('post-conv-entrypoint.sh', '/root')
        container.copy_file('.dockerinit', '/')
        container.run()
        container.wait()
        return True

if __name__ == '__main__':
    test_app.main(UnprotectedFiles)
