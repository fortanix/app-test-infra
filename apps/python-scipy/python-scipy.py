#!/usr/bin/python3

import test_app
import os

class TestPythonScipy(test_app.TestApp):
    def run(self):
        container = self.container(
            'zapps/python-scipy', memsize='2G', rw_dirs=['/'], thread_num=512)
        container.prepare()
        container.run()
        container.wait()
        container.stop()
        return True

    def get_timeout(self):
      if os.environ.get('PLATFORM', 'linux') == 'sgx':
        return 4 * 60 * 60
      else:
        return 1 * 60 * 60

if __name__ == '__main__':
    test_app.main(TestPythonScipy)
