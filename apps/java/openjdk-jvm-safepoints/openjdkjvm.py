#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import os
import test_app


class TestOpenJDKJVM(test_app.TestApp):
    default_timeout_s = 1200

    def __init__(self, run_args, test_arg_list):
        super(TestOpenJDKJVM, self).__init__(run_args)

    def run(self):
        os.chdir(os.path.dirname(__file__))

        # Test 1: Basic functional test of openj9. This test case also runs
        # with an 8GB enclave (for SGX), since we have had issues with that
        # working in the past. (Note that the memsize parameter has no
        # effect on the Linux build.)
        #-Xmx1000m -XX:+UseCountedLoopSafepoints
        # This test uses the "11-jre-hotspot" tag. This image uses HotSpot JRE
        # and hotspot JRE is the JVM by openjdk (docs: https://adoptopenjdk.net/).
        # You can also look into the readme file here(https://hub.docker.com/_/adoptopenjdk)
        # Currently this test passes in zircon but fails in zircon-sgx. It goes
        # into an infinite loop. For the sake of experimenting, I tried returning
        # 0 without an actual mprotect(PROT_NONE) in the linux version of 
        # _DkVirtualMemoryProtect and the same issue got reproduced. Although we 
        # might need to make further changes to this test, at least this test
        # demonstrates that safepoints aren't working in sgx but works in zircon-sgx
        # because of lack of proper implementation of mprotect(PROT_NONE)

        container = self.container(image='adoptopenjdk',
                                   image_version='11-jre-hotspot',
                                   registry='library',
                                   memsize='8G',
                                   thread_num = 40,
                                   entrypoint=[
                                    #./build/linux-x86_64-server-release/images/jdk/bin/java   
                                    '/opt/java/openjdk/bin/java', 
                                    #'-Djava.compiler=j9jit16',
                                    '-XX:+UnlockDiagnosticVMOptions',
                                    '-XX:+PrintSafepointStatistics',
                                    #'GuaranteedSafepointInterval=100',
                                    '-XX:+SafepointALot',
                                    #'-XX:+UseLoopSafepoints',
                                    #'-XX:+UseCountedLoopSafepoints',
                                    #'-XX:ReservedCodeCacheSize=4096k',
                                    #'-Xmx1000m',
                                    #'-XX:+UseSerialGC',
                                    '-jar',
                                    '/benchmarks.jar',                                    
                                   ],
                                   #run_args = ["-prof stack"],
                                   rw_dirs=['/root', '/'])
        container.prepare()
        container.copy_file('classes/HelloWorld.class', '/')        
        container.copy_file('benchmarks.jar', '/')
        logs = container.run_and_return_logs()        
        
        return True

if __name__ == '__main__':
    test_app.main(TestOpenJDKJVM)
