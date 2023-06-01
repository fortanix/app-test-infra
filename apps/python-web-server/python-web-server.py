#!/usr/bin/python3

import time
import requests
import test_app
import test_utils

STARTUP_RETRIES = 10
HOST_PORT = 8080

class TestPythonWebServer(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestPythonWebServer, self).__init__(run_args, [])

    def run(self):
        ports = {
            HOST_PORT: None
        }

        container = self.container('zapps/python-web-server',
                                   image_version='2022120209-aae7f4b',
                                   ports=ports,
                                   nitro_memsize="2048M",
                                   cpu_count=2)
        container.prepare()
        container.run()

        assigned_port = container.get_port_mapping(HOST_PORT)
        url = 'http://localhost:{}'.format(assigned_port)

        for _ in range(STARTUP_RETRIES):
            try:
                print('Fetching {}'.format(url))
                response = requests.get(url, timeout=10.0)

                if response.status_code != 200:
                    raise test_utils.TestException('Server returned status {}, but should be {}'.format(response.status_code, 200))

                if "Hello world" not in response.text:
                    raise test_utils.TestException('Server should serve index page, but returned {}'.format(response.text))

                print("Established a connection to a python web server!")
                return True
            except Exception as e:
                print('Connecting to server failed, sleeping for retry. Reason {}'.format(e))
                time.sleep(5)

        raise test_utils.TestException('Failed to connect to server after {} retries'.format(STARTUP_RETRIES))


if __name__ == '__main__':
    test_app.main(TestPythonWebServer)
