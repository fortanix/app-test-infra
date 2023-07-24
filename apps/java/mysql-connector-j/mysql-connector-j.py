#!/usr/bin/python3
#
# Copyright (C) 2019 Fortanix, Inc. All Rights Reserved.
#
# Description : This app test runs the mysql-connector-j test suite. The
# MySQL server runs outside zircon, while the test container runs in the
# zircon environment.
# Notes:
# 1. The detailed test report generated by the jdbc test infrastructure is
# copied to the build directory (./report/).
# 2. The summary of the tests are printed on the console. These results
# (particularly the pass percentage) don't match the report generated in
# step 1 as they don't include the unit tests yet.

import argparse
import os
import shutil
import test_app
import time

from bs4 import BeautifulSoup

class TestMySqlConnectorJ(test_app.TestApp):
    test_image_name = 'zapps/mysql-connector-j'

    db_image_name = 'mysql'
    db_image_version = '8.0.15'

    def getUnexpectedTestSet(self, inputfile, expected_results):
        soup = BeautifulSoup(inputfile, "lxml")
        tables = soup.find_all("table", attrs={"class":"details"})
        testset = []
        for table in tables:
            for row in table.find_all("tr")[1:]:
                testname = row.findAll("td")[1].get_text()
                if testname not in expected_results:
                    testerror = row.findAll("td")[3].get_text()
                    testset.append([testname, testerror])
        return testset

    def getExpectedTestSet(self, inputFile):
        testset = []
        with open(inputFile,'r') as f:
            testset = f.readlines()
        testset = [data.strip() for data in testset]
        return testset

    def removeFlakyTests(self, reported_flaky, expected_flaky):
       for ftest in reported_flaky:
           if ftest in expected_flaky:
               reported_flaky.remove(ftest)

       return reported_flaky

    def compareResults(self):

        status = True

        # Get the list of expected errors
        if os.environ['PLATFORM'] == 'sgx':
            expected_errors = self.getExpectedTestSet('sgx-expected-errors')
            expected_failures = self.getExpectedTestSet('sgx-expected-failures')
            expected_skipped = self.getExpectedTestSet('sgx-expected-skipped')
            expected_flaky = self.getExpectedTestSet('sgx-expected-flaky')
        else:
            expected_errors = self.getExpectedTestSet('linux-expected-errors')
            expected_failures = self.getExpectedTestSet('linux-expected-failures')
            expected_skipped = self.getExpectedTestSet('linux-expected-skipped')
            expected_flaky = self.getExpectedTestSet('linux-expected-flaky')

        # Compare test errors
        with open('./report/alltests-errors.html','r') as f:
            reported_errors_page = f.read()

        reported_errors = self.getUnexpectedTestSet(reported_errors_page, expected_errors)
        reported_errors = self.removeFlakyTests(reported_errors, expected_flaky)

        if len(reported_errors) != 0:
            print('Unexpected errors and their stack trace:')
            print(reported_errors)
            status = False

        # Compare test failures
        with open('./report/alltests-fails.html', 'r') as f:
            reported_fails_page = f.read()

        reported_failures = self.getUnexpectedTestSet(reported_fails_page, expected_failures)
        reported_failures = self.removeFlakyTests(reported_failures, expected_flaky)

        if len(reported_failures) != 0:
            print('Unexpected failures and their stack trace:')
            print(reported_failures)
            status = False

        # Compare skipped tests
        with open('./report/alltests-skipped.html', 'r') as f:
            reported_skipped_page = f.read()

        reported_skipped = self.getUnexpectedTestSet(reported_skipped_page, expected_skipped);

        if len(reported_skipped) != 0:
            print('Unexpected skipped tests and their stack trace:')
            print(reported_skipped)
            status = False

        return status

    # Override the get_timeout function to set custom app test timeouts
    def get_timeout(self):
        if os.environ['PLATFORM'] == 'sgx':
            return 3 * 60 * 60 * 1000
        else:
            return 120 * 60

    def parseResults(self):
        with open('./report/overview-summary.html', 'r') as f:
            page = f.read()

        parsed_page = BeautifulSoup(page, "lxml")
        tables = parsed_page.find_all("table", attrs={"class":"details"})
        total_tests, total_errors, total_skipped, total_failures = 0, 0, 0, 0

        print ()
        print ('-----RESULTS-----')
        print ('Testsuite                      tests --- errors --- failures --- skipped')
        print ()

        for table in tables:
            for row in table.find_all("tr")[1:]:
                rowdata = row.find_all("td")
                testname = str(rowdata[0].get_text())
                # Read and display only simple, regression and protocol x testsuite results
                if "testsuite" in testname:
                    print ("{:30}".format(testname), end="")
                    for i in range (1,5):
                        td = rowdata[i]
                        print ("{:12}".format(td.get_text()), end="")

                    total_tests += int(rowdata[1].get_text())
                    total_errors += int(rowdata[2].get_text())
                    total_failures += int(rowdata[3].get_text())
                    total_skipped += int(rowdata[4].get_text())
                    print ()

        print ()
        pass_percentage = round(((total_tests - total_errors - total_failures - total_skipped)/float(total_tests)*100) ,2)
        print ('Pass percentage is ' + str(pass_percentage) + '%')
        print ('----------')
        print ()


    def __init__(self, run_args, test_arg_list):
        super(TestMySqlConnectorJ, self).__init__(run_args, [])
        parser = argparse.ArgumentParser(description='MySql-Connector-J Test Suite')
        self.args = parser.parse_args(test_arg_list)

    def run(self):
        os.chdir(os.path.dirname(__file__))

        # __________ DB container ___________
        db_container = None

        # The post conversion entry point script allows us to run this container outside of the
        # zircon environment. For this app test, the mysql server runs outside zircon.
        post_conv_entry_point = "docker-entrypoint.sh mysqld --plugin-load-add=group_replication=group_replication.so --plugin-load-add=keyring_file=keyring_file.so --local-infile=TRUE --ssl"

        db_container = self.container(image=self.db_image_name,
                                      memsize='2G',
                                      ports={
                                             3306: None,
                                             33060: None
                                            },
                                      image_version=self.db_image_version,
                                      registry='library',
                                      encrypted_dirs=['/var/lib/mysql', '/etc/mysql', '/tmp', '/run/mysqld'],
                                      container_env={ 'MYSQL_ALLOW_EMPTY_PASSWORD': 'yes' },
                                      post_conv_entry_point=post_conv_entry_point)

        db_container.prepare()
        db_container.run()

        db_url = db_container.get_my_ip()
        self.info('Mysql server is active on ' + db_url)

        time.sleep(10)

        # Sometimes 10 seconds may not be enough for the mysql server to start
        # and accept connections. This block of code ensures that we wait for
        # the server to be ready before we start testing the JDBC test suite.
        server_running = False
        while(server_running != True):
            logs = db_container.logs()
            expected_substring = '[Server] /usr/sbin/mysqld: ready for connections.'
            for output in logs.stderr:
                if expected_substring in output:
                    server_running = True

        # __________ Mysql-connector-j test container ___________
        # Uncomment this line to run the test natively
        #post_conv_entry_point = "./entrypoint.sh"
        # reference: https://dev.mysql.com/doc/connector-j/8.0/en/connector-j-testing.html
        # Mysql-connector-j source code: https://github.com/mysql/mysql-connector-j
        post_conv_entry_point = None
        test_container = None

        # Test suite build properties which are provided to the tests - mysql server urls,
        # test class and methods to run etc. They need to be inserted by the entrypoint script
        # into the build.properties file
        mysql_prop = 'com.mysql.cj.testsuite.url=jdbc:mysql://' + db_url + ':3306/mysql?user=root&password='
        mysql_ssl_prop = 'com.mysql.cj.testsuite.url.openssl=jdbc:mysql://' + db_url + ':3306/mysql?user=root&password='
        mysqlx_prop = 'com.mysql.cj.testsuite.mysqlx.url=jdbc:mysql://root:@' + db_url + ':33060/mysql'
        mysqlx_ssl_prop = 'com.mysql.cj.testsuite.mysqlx.url.openssl=jdbc:mysql://root:@' + db_url + ':33060/mysql'
        test_class = 'com.mysql.cj.testsuite.test.class=com.mysql.cj.protocol.x.AsyncMessageReaderTest'
        test_methods = 'com.mysql.cj.testsuite.test.methods=testBug22972057_getNextMessageClass'

        test_env = [ 'MALLOC_ARENA_MAX=1' ,
                     '_JAVA_OPTIONS="-XX:CompressedClassSpaceSize=32m -XX:ReservedCodeCacheSize=16m -XX:-UseCompiler -XX:+UseSerialGC -XX:-UsePerfData -Xmx1024m"',
                     'ANT_HOME=/apache-ant-1.10.5',
                     'JAVA_HOME=/jvm/jdk1.8.0_211',
                     'PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/apache-ant-1.10.5/bin:/jvm/jdk1.8.0_211/bin',
                     'MYSQL_PROP={}'.format(mysql_prop),
                     'MYSQLX_PROP={}'.format(mysqlx_prop),
                     'MYSQL_SSL_PROP={}'.format(mysql_ssl_prop),
                     'MYSQLX_SSL_PROP={}'.format(mysqlx_ssl_prop),
                     # 'TEST_CLASS={}'.format(test_class),
                     # 'TEST_METHODS={}'.format(test_methods)
                   ]

        start_time = time.time()
        test_container = self.container(image=self.test_image_name,
                                        network_mode='host',
                                        manifest_env=test_env,
                                        memsize='8G',
                                        thread_num=80,
                                        # rw_dirs=['/'],
                                        rw_dirs=['/mysql-connector-j', '/tmp','/jvm', '/apache-ant-1.10.6', '/ant-extra-libs'],
                                        # mysql-connector-j test AsyncMessageReaderTest failed due to slow runing time of integrity check that caused high latency.
                                        # Since integrity check is mostly performed in '/jvm', '/apache-ant-1.10.6', '/ant-extra-libs' dirs when turned on,
                                        # we set these 3 dirs to rw for now and add mysql-connector-j test back to soak jobs. 
                                        # TODO: we should reset them back to ro once performance of integrity protection is improved enough. ZIRC-3065
                                        entrypoint=['/bin/bash', './entrypoint.sh'])
        test_container.prepare()
        test_container.run()
        test_container_output = test_container.container.wait()

        # Since we do not have a 100% pass rate at the moment, we ignore the container exit status
        if test_container_output['StatusCode']:
            print("Container returned non zero status = {}\n", test_container_output['StatusCode'])

        end_time = time.time()
        # Fetch the test report from the test container
        shutil.rmtree('report', ignore_errors=True)
        test_container.copy_dir_from_container('/mysql-connector-j/buildtest/junit/report/', './')

        # Display summary and time taken to run the test suite
        print ()
        hrs, rem = divmod(end_time - start_time, 3600)
        mins, secs = divmod(rem, 60)
        print ('Time taken to run the test suite (HH:MM:SS) = {:0>2}:{:0>2}:{:05.2f}'.format(int(hrs), int(mins), int(secs)))
        self.parseResults();

        # Compare expected errors, failure and skipped tests
        return self.compareResults();

if __name__ == '__main__':
    test_app.main(TestMySqlConnectorJ)