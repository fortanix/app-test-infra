#!/usr/bin/python3

import test_app


class TestPythonPandas(test_app.TestApp):
    def run(self):
        container = self.container('zapps/python-pandas', memsize='512M', rw_dirs=['/'])
        container.prepare()
        container.run()
        container.wait()
        container.stop()
        return True

if __name__ == '__main__':
    test_app.main(TestPythonPandas)
