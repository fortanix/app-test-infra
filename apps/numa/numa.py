#!/usr/bin/python3

import test_app
from test_utils import TestException

class TestNuma(test_app.TestApp):
    def run(self):
        container = self.container(
                'zapps/numa',
                memsize='128M',
                image_version='20180920-9e6d276',
                entrypoint=['/usr/bin/numactl', '--show']
                )
        container.prepare()
        container.run()
        container.wait(expected_status=0)
        output = container.container.logs(stdout=True, stderr=False, timestamps=False, tail=100).decode('utf-8')
        # There should be a better check for the output. Currently the native
        # output and zircon's output will not be same.
        if output.endswith('No NUMA support available on this system.\n'):
            print('Invalid output:')
            print(output)
            raise TestException('Invalid script output')

        return True

if __name__ == '__main__':
    test_app.main(TestNuma)
