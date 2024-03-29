#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import io
import tarfile
import test_app


class TestFschecksum(test_app.TestApp):
    def run(self):
        print('\nTest 1: Normal checksum tests:')
        container = self.container('zapps/fschecksum', memsize='128M')
        container.prepare()
        container.run_and_compare_stdout(['All tests pass'])
        print('Test 1 passed\n')

        print('Test 2: Failure in integrity check of efs directory:')
        # make '/root' an efs
        container = self.container('zapps/fschecksum', memsize='128M',
                                   encrypted_dirs=['/root'],
                                   zircon_panic_expected='Test 2: Failure in integrity check of efs directory',
                                   expected_status=139)
        container.prepare()
        # create a dir in efs '/root' of container to intentionally fail integrity check
        self.create_spoiler_dir(container)
        container.run_and_search_logs('FS Integrity assert failed')
        print('Test 2 passed\n')
        return True

    def create_spoiler_dir(self, container):
        spoiler_archive = io.BytesIO()
        with tarfile.open('integrity_spoiler_dir.tar', mode='w', fileobj=spoiler_archive) as f:
            t = tarfile.TarInfo('integrity_spoiler_dir')
            t.type = tarfile.DIRTYPE
            t.mode = 0o0777
            f.addfile(t)
        spoiler_archive.seek(0)
        container.copy_tar_files(spoiler_archive, '/root')

if __name__ == '__main__':
    test_app.main(TestFschecksum)
