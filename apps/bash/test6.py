#!/usr/bin/env python3

"""
This script is to check environment variables are passed through correctly from
the ENV commands in a Dockerfile.
The 'setup' part of this test is in the zircon-apps/ubuntu/Dockerfile directory.
"""

import os, sys

def var_matches(key, val):
    if os.getenv(key) != val:
        print("ENV '{}' is '{}'; expected '{}'".format(
            key, os.getenv(key), val), file=sys.stderr)
        return False
    return True

expected = {
    'SIMPLE': 'passed',
    'UNDERSCORE_TEST': 'passed',
    'mysql-server-ip': 'localhost',
    'hasdigits99': 'passed',
    'lowercase': 'passed',
    'DQUOTED': 'passed',
    'SQUOTED': 'passed'
}

failed = False
for k,v in expected.items():
    if not var_matches(k, v):
        ''' SALM-302 Modify test6.py for nitro platforms. Environment variable keys
        are not expected to contain dashes according to IEEE Std 1003.1-2001.
        When extracting the enclave environment variables, such variables
        are omitted based on the shell. So remove this check to avoid test failures.
        '''
        if not (os.getenv('PLATFORM') == 'nitro'
                and k == 'mysql-server-ip'):
            failed = True

if failed:
    print("test6 failed")
else:
    print("test6 passed")
