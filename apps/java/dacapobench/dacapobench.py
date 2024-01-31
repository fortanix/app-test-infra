#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import argparse
import itertools
import os
import re
import statistics
import test_app

# By default, this test runs each dacapo benchmark once.
#
# In perf test mode, benchmarks are run several times to warm up the JIT code
# cache, and then several more times to compute an average running time.
#
# To run the perf test natively:
#  make FLAVOR=release EXTRA_APP_TEST_ARGS="--container-env native --test-arg=--perf" tools/app-test-infra/apps/java/dacapobench/run-app-test
# To run the perf test in zircon-sgx:
#  make PLATFORM=sgx FLAVOR=release EXTRA_APP_TEST_ARGS="--test-arg=--perf" tools/app-test-infra/apps/java/dacapobench/run-app-test
# To run the perf test for a single benchmark, add the following to EXTRA_APP_TEST_ARGS:
#  --test-arg=--benchmark --test-arg=batik

# If you want to do interactive experiments, consider uncommenting the line
# that sets /opt/java/openjdk/bin/java as the entrypoint, and converting with
# --allow-cmdline-arguments.

# h2 disabled because it is flaky. ZIRC-2519
# 'tradesoap' and 'tradebeans' are disabled because it is flaky. ZIRC-2514
BENCHMARKS = ['avrora', 'batik', 'eclipse', 'fop', 'jython', 'luindex',
              'lusearch-fix', 'pmd', 'sunflow', 'xalan']

WARMUP_ITERS = 10
TEST_ITERS = 10

class TestDacapoBench(test_app.TestApp):
    OUTPUT_FILE = 'results.txt'

    def __init__(self, run_args, test_arg_list):
        super(TestDacapoBench, self).__init__(run_args)
        parser = argparse.ArgumentParser(description='Dacapo Benchmarks')
        parser.add_argument('-b', '--benchmark', help='benchmark to run')
        parser.add_argument('-p', '--perf', action='store_true', help='perf test mode')
        self.args = parser.parse_args(test_arg_list)

    def run(self):
        os.chdir(os.path.dirname(__file__))

        kwargs = {
            'entrypoint': ['/dacapobench/run-benchmarks.sh'],
        }

        if self.args.perf:
            kwargs['entrypoint'].extend(['-n', str(WARMUP_ITERS + TEST_ITERS)])

        if self.args.benchmark:
            kwargs['entrypoint'].append(self.args.benchmark)
            benchmarks = [self.args.benchmark]
        else:
            benchmarks = BENCHMARKS

        # Useful if running interactively. See comment above.
        #kwargs['entrypoint'] = ['/opt/java/openjdk/bin/java']

        # Pin image version until ZIRC-3741 is fixed
        container = self.container(image='zapps/dacapobench',
                                   image_version='2020051101-59d7e44',
                                   java_mode='OPENJ9',
                                   memsize='2G',
                                   thread_num=512,
                                   rw_dirs=['/dacapobench'],
                                   **kwargs)
        container.prepare()
        logs = container.run_and_return_logs()
        pass_set = set()
        runtimes = {}
        # DaCapo prints the lines we're looking for on stderr.  For
        # compatibility with environments that don't separate stdout/stderr
        # (kubernetes), we look at both.
        for line in itertools.chain(logs.stdout, logs.stderr):
            def add_result(benchmark, warmup, runtime):
                pass_set.add(benchmark)
                if not warmup or warmup > WARMUP_ITERS:
                    runtimes.setdefault(benchmark, [])
                    runtimes[benchmark].append(runtime)

            m = re.search(r' (\S+) PASSED in (\d+) msec ', line)
            if m:
                benchmark = m.group(1)
                runtime = int(m.group(2))
                add_result(benchmark, None, runtime)

            m = re.search(r' (\S+) completed warmup (\d+) in (\d+) msec ', line)
            if m:
                benchmark = m.group(1)
                warmup = int(m.group(2))
                runtime = int(m.group(3))
                add_result(benchmark, warmup, runtime)

        for b in benchmarks:
            if b in pass_set:
                self.result(b, 'PASSED')
            else:
                self.result(b, 'FAILED')

        if self.args.perf:
            with open(TestDacapoBench.OUTPUT_FILE, 'w') as f:
                f.write('test,rt_avg,rt_stdev\n')
                for b in benchmarks:
                    rt = runtimes[b]
                    f.write('{},{:.0f},{:.0f}\n'.format(b, statistics.mean(rt), statistics.stdev(rt)))

        return True

if __name__ == '__main__':
    test_app.main(TestDacapoBench)
