#!/usr/bin/python3

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
