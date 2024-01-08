#!/usr/bin/python3

import os
import test_app
from test_utils import PythonAppTest


class TestPythonNumpy(test_app.TestApp):

    def run(self):

        self.container = self.container('zapps/python-numpy',
                                    rw_dirs=['/'])
        # to run a partiular test, add -t option in dockerfile CMD
        # example: -t /usr/local/lib/python3.7/site-packages/ \
        # numpy-1.19.0.dev0+f1a247f-py3.7-linux-x86_64.egg/ \
        # numpy/core/tests/test_memmap.py::TestMemmap::test_filename

        # in case output log is incomplete, please modify MAX_LOG_LINES like following line
        # container.MAX_LOG_LINES = 5 * container.MAX_LOG_LINES
        self.container.prepare()
        self.container.run()
        self.container.container.wait()
        self.container.stop()
        return True

    def get_timeout(self):
        if os.environ['PLATFORM'] == 'sgx':
            return 120 * 60
        else:
            return 60 * 60

    def postprocess(self):
        test_results = PythonAppTest(self.container, 10879)
        return test_results.process_results()

if __name__ == '__main__':
    test_app.main(TestPythonNumpy)
