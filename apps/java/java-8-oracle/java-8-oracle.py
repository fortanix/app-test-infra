#!/usr/bin/python3

import os
import test_app

# Test to check if the Hello World program works on the oracle-java8 platform with
# custom jvm options:
# CompressedClassSpaceSize - Size of region for compressed class pointers (1 GB by default)
# ReservedCodeCacheSize - Maximum code cache size reserved by the compiler (32-48 MB by default)
# +UseSerialGC - Use the serial garbage collector which uses a single thread
# -UsePerfData - Disable usage of JVM monitoring and performance testing
# -UseCompiler - Disable usage of the JIT compiler

# MALLOC_ARENA_MAX is an env variable used by glibc memory allocator. By default it creates
# one arena per thread until the max value is reached.
class TestOracleJava8(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestOracleJava8, self).__init__(run_args)

    def run(self):
        os.chdir(os.path.dirname(__file__))

        # This test should not use `latest` as an image version. Do not copy this when adding new app tests.
        container = self.container(image='oracle-java8',
                                   image_version='latest',
                                   registry='relateiq',
                                   memsize='256M',
                                   entrypoint=[
                                      '/usr/lib/jvm/java-8-oracle/jre/bin/java',
                                      '-Xmx4m',
                                      '-cp',
                                      '/root',
                                      'HelloWorld'
                                   ],
                                   java_mode='JAVA-ORACLE',
                                   rw_dirs=['/root'])
        container.prepare()
        container.copy_file('classes/HelloWorld.class', '/root/');

        self.info('Running java hello world...', end='')

        container.run_and_compare_stdout(['Hello, World'])

        self.info(' done.')

        return True

if __name__ == '__main__':
    test_app.main(TestOracleJava8)
