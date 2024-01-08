#!/usr/bin/python3

import argparse
import test_app
from test_utils import get_max_enclave_size


class TestSize01(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestSize01, self).__init__(run_args, [])
        parser = argparse.ArgumentParser(description='Max enclave size test')
        self.args = parser.parse_args(test_arg_list)

    def run(self):
        max_enclave_size_not_64, max_enclave_size_64 = get_max_enclave_size()
        print('max_enclave_size_not_64 ', max_enclave_size_not_64, 'max_enclave_size_64 ',
              max_enclave_size_64)

        size_requested = ''
        size_requested_in_bytes = 0
        # trying to allocate 2 * MAXIMUM SIZE ALLOWED
        if (max_enclave_size_64 == (1 << 36)):
            size_requested = '128G'
            size_requested_in_bytes = 1 << 37
        elif (max_enclave_size_64 == (1 << 37)):
            size_requested = '256G'
            size_requested_in_bytes = 1 << 38
        print('max_enclave_size_temp = ', size_requested)
        assert(size_requested_in_bytes > max_enclave_size_64)

        expected_error_message = 'Requested enclave size of ' + str(size_requested_in_bytes) +  \
                                 ' exceeds maximum size of ' + str(max_enclave_size_64) + \
                                 ' supported by the CPU'

        container = self.container('zapps/python', image_version='2020112709-cd72bb3',
                                    entrypoint=['/bin/ls'],
                                    rw_dirs=['/'] , memsize = size_requested,
                                    zircon_panic_expected=True,
                                    expected_status=1
                                    )

        container.prepare()
        return container.run_and_search_logs(expected_error_message)

    def get_timeout(self):
        return 5 * 60

if __name__ == '__main__':
    test_app.main(TestSize01)
