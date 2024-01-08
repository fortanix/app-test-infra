#!/usr/bin/python3

import test_app


class TestStaticClient(test_app.TestApp):
    def run(self):
        container = self.container('zapps/static', memsize='128M')
        container.prepare()
        container.run_and_compare_stdout(['Hello world'])
        return True

if __name__ == '__main__':
    test_app.main(TestStaticClient)
