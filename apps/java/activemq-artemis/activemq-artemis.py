#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import csv
import os
import test_app
from bs4 import BeautifulSoup
from test_utils import is_sgx

# The scripts facilitates the running of activemq-artemis JMS test suite by
# specifying the required env var and then parsing the reports/results to match
#  with the expected result.

class TestJMS(test_app.TestApp):
    default_timeout_s = 3000
    def __init__(self, run_args, test_arg_list):
        super(TestJMS, self).__init__(run_args)

    def run(self):
        os.chdir(os.path.dirname(__file__))

        test_env = ['_JAVA_OPTIONS="-XX:CompressedClassSpaceSize=16m -XX:ReservedCodeCacheSize=16m -XX:-UseCompiler -XX:+UseSerialGC -XX:-UsePerfData -Xmx64m"',
                     'MALLOC_ARENA_MAX=1',
                   ]

        # The activemq-artemis build is flaky so it has been removed from the
        # zircon-apps build. Pin to a specific revision where it was built.
        container = self.container(image='zapps/activemq-artemis',
                                   image_version='20190702-3da0db6',
                                   memsize='1024M',
                                   rw_dirs = ['/'],
                                   manifest_env=test_env,
                                   thread_num=128)
        container.prepare()
        container.run()
        container.wait(expected_status=0)
        container.copy_dir_from_container('/activemq-artemis/tests/jms-tests/target/surefire-reports', './')
        if (self.compare_results() == False):
            print('Container output did not match expected output.\n')
            return False
        else:
            return True

    def compare_results(self):
        print("Comparing the expected and actual result")
        failed_result = []
        skipped_result = []
        filename = 'jms_results.csv'
        more_failures = False

        with open("jms_skipped_expected") as f:
            skipped_expected = f.readlines()
        skipped_expected = [x.strip() for x in skipped_expected]

        with open("jms_failed_expected") as f:
            failed_expected = f.readlines()
        failed_expected = [x.strip() for x in failed_expected]

        # For some reason, this test case is flaky under Linux, but not under SGX. ZIRC-2982.
        if not is_sgx():
            failed_expected.append('org.apache.activemq.artemis.jms.tests.AcknowledgementTest.testRecoverAutoACK')

        print ("Writing the full test report to " + os.getcwd() + "/" + filename)
        Path = "./surefire-reports/"
        filelist = os.listdir(Path)
        row = ["Name", "Tests", "Errors", "Skipped", "Failures"]
        with open(filename, 'w') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(row)
            for file in filelist:
                if file.endswith(".xml"):
                    infile = open(Path + file,"r")
                    contents = infile.read()
                    soup = BeautifulSoup(contents, "xml")
                    # Parsing the following line from each test report:
                    # <testsuite name="org.apache.activemq.artemis.jms.tests.util.JNDIUtilTest" time="16.35" tests="3" errors="0" skipped="0" failures="0">
                    row = [soup.find_all("testsuite")[0]['name'], \
                            soup.find_all("testsuite")[0]['tests'], \
                            soup.find_all("testsuite")[0]['errors'], \
                            soup.find_all("testsuite")[0]['skipped'], \
                            soup.find_all("testsuite")[0]['failures']]
                    writer.writerow(row)
                    # print(row)
                    for i in range(0, int(soup.find_all("testsuite")[0]['failures'])):
                        failed_result.append(soup.find_all("testsuite")[0]['name'] + "." + soup.find_all("testcase")[i]['name'])
                    for i in range(0, int(soup.find_all("testsuite")[0]['skipped'])):
                        skipped_result.append(soup.find_all("skipped")[i].parent["classname"] + "." + soup.find_all("skipped")[i].parent["name"])

        didnt_fail = list(set(failed_expected) - set(failed_result))
        new_fail = list(set(failed_result) - set(failed_expected))
        didnt_skip = list(set(skipped_expected) - set(skipped_result))
        new_skip = list(set(skipped_result) - set(skipped_expected))

        if (didnt_fail != []):
            print("Following unexpectedly tests passed this time:")
            print(didnt_fail)

        if (new_fail != []):
            more_failures = True
            print("Following tests failed this time:")
            print(new_fail)

        if (didnt_skip != []):
            print("Following tests were not skipped unexpectedly this time:")
            print(didnt_skip)

        if (new_skip != []):
            more_failures = True
            print("Following tests were skipped unexpectedly this time:")
            print(didnt_skip)

        if more_failures == True:
            return False
        else:
            return True

if __name__ == '__main__':
    test_app.main(TestJMS)
