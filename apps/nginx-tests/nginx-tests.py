#!/usr/bin/python3
#
# Copyright (C) 2018 Fortanix, Inc. All Rights Reserved.
#
# Runs the nginx developer test suite.

import os
import re
from test_app import TestApp, main
from test_utils import remove_ignore_nonexistent

class TestNginxTests(TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestNginxTests, self).__init__(run_args, [])
        self.platform = None

        self.cur_test = None

    def run(self):
        # This is a per-test-case timeout, in seconds.
        if os.environ['PLATFORM'] == 'sgx' or os.environ['PLATFORM'] == 'sim':
            timeout = 600
            self.platform = 'sgx'
            self.expected_result_count = 240
        else:
            timeout = 300
            self.platform = 'linux'
            self.expected_result_count = 222

        container_env = [
            'TIMEOUT={}'.format(timeout),
            'PLATFORM={}'.format(self.platform),
        ]

        container = self.container('zapps/nginx-tests', container_env=container_env,
                                   memsize='512M',
                                   entrypoint=['/usr/bin/prove'],
                                   rw_dirs=['/'],
                                   post_conv_entry_point=['/home/nginx/run-nginx-tests.sh'])

        remove_ignore_nonexistent('nginx-tests.stdout.0')
        remove_ignore_nonexistent('nginx-tests.stderr.0')

        container.prepare()
        container.copy_file('increase-timeouts.py', '/home/nginx/')
        container.copy_file('run-nginx-tests.sh', '/home/nginx/')
        container.copy_file('expected-timeouts.{}'.format(self.platform), '/home/nginx/nginx-tests')
        container.run()
        container.container.wait()

        # Docker apparently has a limit on how much stdout/stderr it will keep. So our test script writes the
        # nginx test output to a file which we then retrieve from the container to parse for test outcome.
        container.copy_file_from_container('/tmp/test-runner.stdout', 'test-runner.stdout')
        container.copy_file_from_container('/tmp/test-runner.stderr', 'test-runner.stderr')

        return True

    def get_timeout(self):
        if os.environ['PLATFORM'] == 'sgx':
            # The test runner is pathologically slow on SGX, probably due to a large number of forks.
            # XXX - fix timeout after tests debugged.
            return 3 * 60 * 60 * 1000
            #return 30 * 60
        else:
            return 120 * 60

    def add_test_result(self, result, all_tests, result_map):
        assert(self.cur_test is not None)
        assert(self.cur_test not in all_tests)
        all_tests[self.cur_test] = result
        result_map[self.cur_test] = True
        self.cur_test = None

    def write_test_results(self, filename, tests_map):
        with open(filename, 'w') as fh:
            for test in sorted(tests_map.keys()):
                fh.write(test + '\n')

    def load_expected_results(self, filename):
        tests_map = {}
        with open('{}.{}'.format(filename, self.platform), 'r') as fh:
            for line in fh:
                tests_map[line.strip()] = True
        return tests_map

    def check_expected_outcome(self, result, all_tests, expected_map, results_map):
        for test in sorted(expected_map.keys()):
            if test in results_map:
                self.result(test, 'PASSED')
            else:
                try:
                    outcome = all_tests[test]
                except KeyError:
                    outcome = 'not run'
                message = 'Expected suite {} to {}, but it had outcome {}'.format(
                    test, result, outcome)
                self.error(message)
                self.result(test, 'FAILED', message)

    # The postprocess method is invoked after the test terminates, and only if the test succeeded. The infrastructure
    # will automatically extract the container's stdout and stderr for us.
    def postprocess(self):
        passes = {}
        failures = {}
        notests = {}
        timeouts = {}
        all_tests = {}

        with open('test-runner.stdout', 'r') as fh:
            for line in fh:
                line = line.rstrip('\n')

                if re.match('^Running test ', line):
                    assert(self.cur_test is None)
                    self.cur_test = line.replace('Running test ', '')
                    continue

                if line == 'Result: NOTESTS':
                    self.add_test_result('notests', all_tests, notests)
                elif line == 'Result: FAIL':
                    self.add_test_result('failed', all_tests, failures)
                elif line == 'Result: PASS':
                    self.add_test_result('passed', all_tests, passes)
                elif line == 'Result: TIMEOUT':
                    self.add_test_result('timedout', all_tests, timeouts)

        print('{} suites evaluated'.format(len(all_tests)))
        print('{} suites passed'.format(len(passes)))
        print('{} suites failed'.format(len(failures)))
        print('{} suites had no enabled tests'.format(len(notests)))
        print('{} suites timed out'.format(len(timeouts)))
        print('')

        # Output reports for passed/failed/notests/timeouts
        self.write_test_results('passes', passes)
        self.write_test_results('failures', failures)
        self.write_test_results('notests', notests)
        self.write_test_results('timeouts', timeouts)

        expected_passes = self.load_expected_results('expected-passes')
        expected_failures = self.load_expected_results('expected-failures')
        expected_notests = self.load_expected_results('expected-notests')

        # For now, we don't run tests that are expected to time out.
        #expected_timeouts = {}
        #self.load_expected_results('expected-timeouts', expected_timeouts)

        # Report any suites that didn't have the expected outcome
        self.check_expected_outcome('pass', all_tests, expected_passes, passes)
        self.check_expected_outcome('fail', all_tests, expected_failures, failures)
        self.check_expected_outcome('notests', all_tests, expected_notests, notests)

        print('Ran {} tests'.format(self.results.count()))

        # For now, we don't run tests that are expected to time out.
        # self.check_expected_outcome('timed out', all_tests, expected_timeouts, timeouts)

        # The primary results reporting mechanism is the calls to self.result()
        # in check_expected_outcome, and checks of the report results in
        # test_app.main. This is just a sanity-check. expected_result_count
        # includes only the results checked with check_expected_outcome, so
        # passes, failures, and notests, but not flaky or timeouts.
        if self.results.count() == self.expected_result_count:
            return True
        else:
            print('results count {} differs from expected {}'.format(self.results.count(), self.expected_result_count))
            return False


if __name__ == '__main__':
    main(TestNginxTests)
