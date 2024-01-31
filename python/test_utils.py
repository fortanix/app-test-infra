#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Library of utilities for tests.
import glob
import junit_xml
import os
import random
import shutil
import sqlite3
import string
import subprocess
import time

zircon_panic_msg = 'EnclaveOS has encountered an internal error'
zircon_panic_msg_binary = zircon_panic_msg.encode('utf-8')

# Try to remove a file or directory, ignoring errors if it does not exist.
def remove_ignore_nonexistent(path):
    try:
        os.remove(path)
    except OSError:
        pass

# Remove files/directories matching a shell glob, like test* or test??.
def remove_glob(path):
    for filename in glob.glob(path):
        remove_ignore_nonexistent(filename)

# Return the input string s with any unprintable characters removed.
def remove_invalid_characters(s):
    return ''.join([x for x in s if ord(x) >= 32 and ord(x) <= 127])

# Parse a time string of the form <number>[<units>]. Returns the time in seconds.
# The optional character units denotes the units for <number>:
# s - seconds
# m - minutes
# h - hours
# If no units are specified in the string, default_units will be used for the units.
#
# For example:
# parse_time_string('1s') => 1
# parse_time_string('2m') => 120
# parse_time_string('45', default_units='m') => 2700
# parse_time_string('1h', default_units='s') => 3600

def parse_time_string(value, default_units='s'):
    try:
        if value.endswith('s'):
            default_units = 's'
            value_int = int(value[:-1])
        elif value.endswith('m'):
            default_units = 'm'
            value_int = int(value[:-1])
        elif value.endswith('h'):
            default_units = 'h'
            value_int = int(value[:-1])
        else:
            value_int = int(value)
    except Exception:
        raise TestException('Unable to parse time string {}'.format(value))

    if default_units == 'h':
        value_int *= 60
        default_units = 'm'
    if default_units == 'm':
        value_int *= 60
        default_units = 's'

    if default_units != 's':
        raise TestException('Invalid default time unit {}'.format(default_units))

    return value_int

class TestException(Exception):
    pass

class TimeoutException(TestException):
    pass

def random_string(len):
    return ''.join(random.choice(string.ascii_lowercase) for x in range(len))

# Schema Version 1 had "runtime" as an integer, but it was unused.
# Version 2 makes this a "real" number of seconds.
CURRENT_SCHEMA_VERSION = 2
RESULTS_DB_FILE = 'test-results.sqlite3'

class TestResults(object):
    def __init__(self, use_db=True):
        self._total = 0
        self._count = {}
        # record a start time at creation of this results object.
        self.start_time = time.time()

        if not use_db:
            self.conn = None
        else:
            self.conn = sqlite3.connect(os.path.join(os.environ['TEST_BASE_DIR'], RESULTS_DB_FILE))

            db_schema_version = None
            try:
                cur = self.conn.execute('SELECT version FROM schema_version')
                db_schema_version = cur.fetchone()[0]
            except Exception as e:
                print('Error retrieving test results database schema version: {}'.format(e))

            if db_schema_version is None or db_schema_version != CURRENT_SCHEMA_VERSION:
                # If the database is not just missing or out of date, but corrupt, this may
                # not be sufficient to reset it. That should be rare.
                print('Initializing test results database')
                self.conn.execute('DROP TABLE IF EXISTS schema_version')
                self.conn.execute('CREATE TABLE schema_version (version INTEGER)')
                self.conn.execute('INSERT INTO schema_version VALUES (?)', (CURRENT_SCHEMA_VERSION,))
                self.conn.execute('DROP TABLE IF EXISTS test_results')

                # If you change the definition of the results table here, you also
                # need to update CURRENT_SCHEMA_VERSION, above.
                self.conn.execute('CREATE TABLE test_results (run_id TEXT, date TEXT, suite TEXT, testname TEXT, testcase TEXT, result TEXT, message TEXT, runtime REAL)')
                self.conn.commit()

    # Submit a test result to the database
    def submit(self, suite: str, testname: str, testcase: str, result, message: str, runtime: float = -1):
        """
        result: is either a bool success or an enum value {PASSED, FAILED, SKIPPED, ERROR}
        runtime: is a floating point number of seconds, obtained as a difference of calls to time.time()
                 If the value provided is zero, the time should be considered unknown.
                 If the time provided is negative, (default), we calculate the time since this object was created.
        """
        if result == True:
            result = 'PASSED'
        elif result == False:
            result = 'ERROR'
        if result not in ('PASSED', 'FAILED', 'SKIPPED', 'ERROR'):
            raise ValueError('Invalid test result {}'.format(result))

        # handle runtime estimate if not provided
        if runtime < 0:
            runtime = time.time() - self.start_time
        # in the case of sequential tests, update the start_time estimate to now
        self.start_time = time.time()

        self._total += 1
        if result in self._count:
            self._count[result] += 1
        else:
            self._count[result] = 1

        if self.conn:
            values = (os.getenv('ZIRCON_MAKE_TIMESTAMP'), suite, testname, testcase, result, message, runtime)
            self.conn.execute('INSERT INTO test_results (run_id, date, suite, testname, testcase, result, message, runtime) ' +
                              'VALUES (?, DATETIME("now"), ?, ?, ?, ?, ?, ?)', values)
            self.conn.commit()

    def count(self):
        return self._total

    def all_pass(self):
        assert(self._total == sum(self._count.values()))
        return self._total != 0 and self._count.get('PASSED', 0) == self._total

    @staticmethod
    def dump(fh, run_id):
        conn = sqlite3.connect(os.path.join(os.environ['TEST_BASE_DIR'], RESULTS_DB_FILE))

        results_dict = {}

        cur = conn.execute('SELECT suite, testname, testcase, result, message FROM test_results WHERE run_id = ? ORDER BY suite',
                (run_id,))
        for row in cur:
            (suite, testname, testcase, result, message) = row
            if suite not in results_dict:
                results_dict[suite] = []

            # The first argument is the test method name. The second argument is the
            # classname. For java tests, one class could have one or more test
            # methods, so the class name is actually the higher-level name.
            tc = junit_xml.TestCase(testcase, '{}.{}'.format(suite, testname))
            if result == 'ERROR':
                tc.add_error_info('{}: {}'.format(result, message))
            elif result == 'SKIPPED':
                tc.add_skipped_info('{}: {}'.format(result, message))
            elif result != 'PASSED':
                tc.add_failure_info('{}: {}'.format(result, message))

            results_dict[suite].append(tc)

        suites = [junit_xml.TestSuite(k, v) for (k, v) in results_dict.items()]

        junit_xml.TestSuite.to_file(fh, suites)

def is_sgx():
    return 'SGX' in os.environ and os.environ['SGX']

def manifest_file(file):
    if file:
        if is_sgx():
            return file + '.manifest.sgx'
        else:
            return file + '.manifest'
    else:
        return None

# Wait until an http or https server is serving a particular path.
# If port is 0, we will connect to a default port of 80 for http and 443 for https.
# Specifying insecure=True can be used to skip SSL server certificate verification.
# headers allows specifying a list of HTTP headers to be sent with the request.
def wait_for_server(protocol='http', server='127.0.0.1', port=0, path='', retries=60, insecure=False, headers=[]):
    if port != 0:
        server += ':{}'.format(port)
    target = '{}://{}'.format(protocol, server)
    if not path.startswith('/'):
        target += '/'
    target += path

    args = ['/usr/bin/wget', '-t', '1', '-O', 'wait-for-server-output', target]
    for header in headers:
        args.append('--header={}'.format(header))

    if insecure:
        args.append('--no-check-certificate')

    print(' '.join(args))

    for r in range(retries):
        try:
            subprocess.check_call(args)
            break
        except subprocess.CalledProcessError as e:
            if r == retries - 1:
                print('Server failed to start')
                raise e
            time.sleep(1)

# process test results of python-numpy, python-pandas, python-scipy
class PythonAppTest:
    def __init__(self, test_container, expected_count):

        self.container_name = test_container.name
        self.platform = os.environ['PLATFORM']
        self.expected_results_count = expected_count
        self.results_count = 0

    def process_results(self):

        failures = set()
        errors = set()
        expected_failures = set()
        expected_errors = set()

        with open('logs/{}.stdout.0'.format(self.container_name), 'r') as f:
            lines = f.read().splitlines()
            last_line = lines[-1]
            self.count_results(last_line)

            is_failure = False
            is_error = False
            for line in lines:
                if ' Test' in line:
                    test_name = self.get_test_name(line)
                    if not test_name:
                        continue
                    if is_failure:
                        failures.add(test_name)
                    elif is_error:
                        errors.add(test_name)
                    continue

                if '= FAILURES =' in line:
                    is_error = False
                    is_failure = True
                elif '= ERRORS =' in line:
                    is_failure = False
                    is_error = True

        with open('expected-failures.{}'.format(self.platform), 'r') as f:
            for test_name in f:
                test_name = test_name.rstrip('\n')
                expected_failures.add(test_name)

        with open('expected-errors.{}'.format(self.platform), 'r') as f:
            for test_name in f:
                test_name = test_name.rstrip('\n')
                expected_errors.add(test_name)

        self.check_results(expected_failures, failures, 'FAILED')
        self.check_results(expected_errors, errors, 'ERROR')

        # As for a single test case, please disbale following self.check_results_count()
        self.check_results_count()

        return True

    def check_results(self, expected, results, result_status):
        for test_name in results:
            if test_name not in expected:
                error_message = 'test \"{}\" is not expected to be {}.'.format(test_name, result_status)
                self.result(test_name, result_status, error_message)

    def get_test_name(self, line):
        start_index = line.find(' Test') + 1
        end_index = start_index + 4
        if (line[end_index] == ' '):
            return None
        while line[end_index] != ' ':
            end_index += 1
        return line[start_index : end_index]

    def count_results(self, last_line):
        cur_count = 0
        found_first_space = False
        for character in last_line:
            if not found_first_space:
                if character == ' ':
                    found_first_space = True
                continue

            if character == '.':
                break

            digit = ord(character)
            if digit <= ord('9') and digit >= ord('0'):
                cur_count = cur_count * 10 + digit - ord('0')

            else:
                self.results_count += cur_count
                cur_count = 0

    def check_results_count(self):
        if self.results_count != self.expected_results_count:
            error_message = 'Number of results: {} does not match expected result number: {}'.format(str(self.results_count), str(self.expected_results_count))
            error_message += ' Please disable this count check if you are running a single test.'
            raise TestException(error_message)

def get_string_bytes(str_len):
    l = string.ascii_lowercase + string.ascii_uppercase + '0123456789' + '/+'
    str = ''.join(random.choice(l) for i in range(str_len))
    return str

def get_max_enclave_size():
    import cpuid_impl
    """
    {leaf} %eax
    {subleaf} %ecx, 0 in most cases
    {reg_id} idx of [%eax, %ebx, %ecx, %edx], 0-based
    """
    cpu = cpuid_impl.CPUID()
    leaf = 0x12
    subleaf = 0
    reg_id = 3
    regs = cpu(leaf, subleaf)
    exponent_not64 = regs[reg_id] & 0xff
    exponent_64 = (regs[reg_id] >> 8) & 0xff
    enc_size_not64 = 1 << exponent_not64
    enc_size_64 = 1 << exponent_64
    return enc_size_not64, enc_size_64

# we have a similar function here remove_invalid_characters which removes unprintable
# characters, whereas this function takes a bytes string and replaces any invalid
# character with '?'
def replace_non_printable_characters(strb):
    str = ""
    printable_chars = bytes(string.printable, 'utf-8')

    for chb in strb:
        if (chb not in printable_chars):
            # replacing the non-printable characters with '?'
            str += '?'
        else:
            str += chr(chb)

    return str

def check_and_decode(strb):
  str = ""
  try:
      str = strb.decode("utf-8")
  except  Exception as e:
      str = replace_non_printable_characters(strb)
  return str

def scan_line_join_and_decode(result_op):
  str = ""
  for rowb in result_op:
      str += check_and_decode(rowb)
  return str

def sgx2_supported():
    import cpuid_impl
    '''
    Returns a boolean indicating whether SGX2 is supported on this machine.
    SGX2 requires that both the hardware support SGX2 and the driver supports
    SGX2.
    '''
    cpuid = cpuid_impl.CPUID()

    # Technically, Intel recommends checking leaf 0 of CPUID to verify
    # that the extended features leaf is implemented by the CPU, but all
    # 64-bit CPUs support the extended feature leaf.
    values = cpuid(cpuid_impl.LEAF_EXTENDED_FEATURES, 0)
    if (values[1] & cpuid_impl.FEATURE_7_0_EBX_SGX) == 0:
        # No SGX, so SGX2 obviously not supported.
        return False

    values = cpuid(cpuid_impl.LEAF_SGX)
    if (values[0] & cpuid_impl.FEATURE_12_0_EAX_SGX2) == 0:
        # SGX2 feature bit not set.
        return False

    return True
def get_locust_version():
    version = os.popen('locust -V').read().lower()
    return version

def is_newer_locust():
    locust_version = get_locust_version()
    f = locust_version.find('locust 1.4.1') >= 0
    return f

def is_valid_keysize(size):
    return int(size) >= 2048 and int(size) % 2 == 0

#
# Helper functions for read-only filesystem regression tests
#
def rofs_create(path, dir=None):
    rdir = None
    if dir is not None:
        rdir = dir
    else:
        rdir = 'rofs_mount'
    os.mkdir(path +"/" + rdir)
    with open(path + "/" + rdir +"/"+ 'file_exist', "w") as text_file:
        text_file.write("Plain Text file1 that exists")
    os.mkdir(path +"/" + rdir + "/" + rdir)
    with open(path + "/" + rdir + "/"+ rdir + "/" + 'file_exist', "w") as text_file:
        text_file.write("Plain Text file1 that exists")
    os.mknod(path + "/" + rdir + "/" + 'empty_file')

def rofs_copy_file(src, dst_dir):
    shutil.copy2(src, dst_dir, follow_symlinks=True)

# Delete any leftover test files from a previous run
def rofs_cleanup(dir=None):
    rdir = None
    if dir is not None:
        rdir = dir
    else:
        rdir = 'rofs_mount'
    fs_file_cleanup(rdir)

def get_hash_dirname(dirname):
    return '{}_hash'.format(dirname)

def get_hash_dir(hash_dirname):
    cwd = os.getcwd()
    return cwd + '/' + hash_dirname + cwd

def hash_dir_create(dirname):
    hash_dirname = get_hash_dirname(dirname)
    if os.path.exists(hash_dirname):
        try:
            shutil.rmtree(hash_dirname)
        except OSError:
            pass
    try:
        os.makedirs(get_hash_dir(hash_dirname))
    except OSError:
        pass

def hash_dir_cleanup(dirname):
    hash_dirname = get_hash_dirname(dirname)
    try:
        shutil.rmtree(hash_dirname)
    except OSError:
        pass

#
# Helper functions for encrypted filesystem
#
def create_efs_key_folder(efs_keys_dir):
    os.mkdir(efs_keys_dir)

def clean_efs_keys(efs_keys_dir):
    shutil.rmtree(efs_keys_dir, ignore_errors=True)

# Delete any leftover test files from a previous run
def efs_cleanup(dirlist, efs_keys_dir):
    for d in dirlist:
        fs_file_cleanup(d)
    clean_efs_keys(efs_keys_dir)

# recursive setup few directories
def efs_setup(data='rand', efs_mount='efs_mount',
              plain_mount='plain_mount',
              efs_keys_dir='efs-keys',
              create_symlink=True):
    # create directory efs_mount
    fs_create(".", 2, data, efs_mount, create_symlink)
    try:
        # copy the directory for plain mount
        shutil.copytree(efs_mount, plain_mount, symlinks=True, dirs_exist_ok=True)
        with open(efs_mount +"/"+ 'file3', "w") as text_file:
            if data=='rand':
                text_file.write('b'*random.randint(200,500))
            else:
                text_file.write('0'*300)
    except:
        pass
    create_efs_key_folder(efs_keys_dir)

#
# Other setup/cleanup helper functions
#

def fs_create(path, level, data='rand', dirname='efs_mount', create_symlink=True):
    if level == 0:
        return
    os.mkdir(path +"/" + dirname)
    with open(path + "/" + dirname +"/"+ 'file1', "w") as text_file:
        text_file.write("Plain Text file1 for efs to encrypt")
    with open(path + "/" + dirname +"/"+ 'file2', "wb") as text_file:
        if data=='rand':
            text_file.write(os.urandom(random.randint(20000, 50000)))
        else:
            text_file.write('0'.encode() * 33333)
    if create_symlink:
        os.symlink('file1', path + "/" + dirname +"/"+ 'symlink')
        os.symlink(dirname, path + "/" + dirname +"/"+ 'symlink_dir')
    fs_create(path +"/"+ dirname, level-1, data, dirname, create_symlink)


# Removes any file or directory recursively
def fs_file_cleanup(filepath):
    try:
        shutil.rmtree(filepath)
    except:
        pass

def fs_create_sized_file(name, size):
    with open(name, "wb") as f:
        f.write(os.urandom(size))



# XOR two byte values and return a byte
# Convert them to ints to avoid python error message
def xor_bytes( a, b ) :
  as_int = lambda XX : int.from_bytes( XX, byteorder = 'big' )
  return ( as_int( a ) ^ as_int( b ) ).to_bytes( 1, 'big' )

# Change a byte in a binary file
# @ff : Binary file in which byte will be changed
# @location : location in the file where the byte will be changed
# @byte : Byte value to be XORed with location in file
def alter_file( ff, location, byte = b'h' ) :
  ff.seek( location )
  target_byte = ff.read( 1 )  # read single byte
  ff.seek( location )
  ff.write( xor_bytes( target_byte, byte ) )

def check_conv_logs(path=None, match_str=None):
    if path:
        with open(path, "r") as f:
            conv_logs = f.read()
    if match_str is not None and match_str in conv_logs:
        return True
    return False