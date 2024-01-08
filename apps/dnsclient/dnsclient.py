#!/usr/bin/python3

import test_app


class TestDnsClient(test_app.TestApp):
    def run(self):
        container = self.container('zapps/dnsclient', memsize='128M')
        container.prepare()
        container.run_and_compare_stdout(['127.0.0.1', '127.0.0.1', '127.0.0.1'])
        return True

if __name__ == '__main__':
    test_app.main(TestDnsClient)
