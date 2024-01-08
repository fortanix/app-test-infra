#!/usr/bin/python3

import os
import test_app


class TestSdkmsCli(test_app.TestApp):
    def run(self):
        container = self.container(
                'zapps/sdkms-cli',
                memsize='2G',
                thread_num=128,
                rw_dirs=['/root'],
                manifest_env=[
                    'MALLOC_ARENA_MAX=1',
                    'FORTANIX_API_KEY={}'.format(os.getenv('FORTANIX_API_KEY', '')),
                ])
        container.prepare()
        # The test container exports 'Test exportable object' and pipes to
        # sha256sum. This is the hash of the test object (an RSA key), in
        # PEM format, with no newline at the end of the footer line.
        container.run_and_compare_stdout(['319e69bf64139666b65a7dd71c11611a44118c7d4037a93d80dc1da535ee4946  -'])

        return True

if __name__ == '__main__':
    test_app.main(TestSdkmsCli)
