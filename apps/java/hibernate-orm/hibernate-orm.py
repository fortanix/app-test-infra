#!/usr/bin/python3

#
# The scripts facilitates the runnign of hibernate-orm JPA test suite by
# spciffying the required env var and then parsing the reports to match with the
# expected result.
#
# Manifest env variables declared here:
# JPA_TEST : can be set to run a particular test from the hubernate-orm repository
# _JAVA_OPTIONS : memory constraints put to run the test using SGX
# JAVA_FLAGS : can be set to additional java flags that need to be applied to
#              the Java runtime for debug purpose.
#

import os
import test_app
from bs4 import BeautifulSoup


class TestJPA(test_app.TestApp):
    default_timeout_s = 3000
    def __init__(self, run_args, test_arg_list):
        super(TestJPA, self).__init__(run_args)

    def run(self):
        os.chdir(os.path.dirname(__file__))

        # test_env = { 'JPA_TEST' :  'org.hibernate.jpa.test.NamedQueryTransactionFailureTest.testNamedQueryWithMarkForRollbackOnlyFailure',
        test_env = [ 'JPA_TEST=org.hibernate.jpa.*',
                     '_JAVA_OPTIONS="-XX:CompressedClassSpaceSize=16m -XX:ReservedCodeCacheSize=16m -XX:-UseCompiler -XX:+UseSerialGC -XX:-UsePerfData -Xmx1024m"',
                     'MALLOC_ARENA_MAX=1',
                     'JAVA_FLAGS='
                   ]

        # This test should not use `latest` as an image version. Do not copy this when adding new app tests.
        container = self.container(image='zapps/hibernate-orm',
                                   image_version='latest',
                                   manifest_env=test_env,
                                   memsize='4G',
                                   thread_num=128, rw_dirs=['/'])
        container.prepare()
        container.run()
        container.wait(expected_status=1)
        container.copy_dir_from_container('/hibernate-orm/hibernate-core/target/reports/', './')
        if (self.evaluate_results() == False):
            print('Container output did not match expected output\n')
            return False
        else:
            return True

    def evaluate_results(self):
        with open('reports/tests/test/index.html','r') as f:
            reported_errors_page = f.read()

        print("Comparing the expected and actual result")
        soup = BeautifulSoup(reported_errors_page, "lxml")
        failed_result = []
        ignored_result = []
        more_failures = 0

        tables = soup.find_all('div', id='tab0')
        list_table = tables[0].find_all('li')
        for table in list_table:
            failed_result.append((((table).find_all('a')[1])['href']).replace("classes/", "", 1).replace("html#", "", 1))

        tables = soup.find_all('div', id='tab1')
        list_table = tables[0].find_all('li')
        for table in list_table:
            ignored_result.append((((table).find_all('a')[1])['href']).replace("classes/", "", 1).replace("html#", "", 1))

        with open("ignored_expected") as f:
            ignored_expected = f.readlines()
        ignored_expected = [x.strip() for x in ignored_expected]

        with open("failed_expected") as f:
            failed_expected = f.readlines()
        failed_expected = [x.strip() for x in failed_expected]

        failed_didnt = list(set(failed_expected) - set(failed_result))
        failed_new = list(set(failed_result) - set(failed_expected))
        ignored_didnt = list(set(ignored_expected) - set(ignored_result))
        ignored_new = list(set(ignored_result) - set(ignored_expected))

        if (failed_didnt != []):
            print("Following unexpectedly tests passed this time:")
            print(failed_didnt)

        if (failed_new != []):
            more_failures = 1
            print("Following tests failed this time:")
            print(failed_new)

        if (ignored_didnt != []):
            print("Following tests were not ignored unexpectedly this time:")
            print(ignored_didnt)

        if (ignored_new != []):
            more_failures = 1
            print("Following tests ignored unexpectedly this time:")
            print(ignored_didnt)

        if more_failures == 1:
            return False
        else:
            return True

if __name__ == '__main__':
    test_app.main(TestJPA)
