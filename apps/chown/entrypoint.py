#!/usr/bin/python3

#
# Test for various chmod and chown scenarios.
#
# This test is intended to be run in the zapps/ubuntu test container,
# which does some necessary setup such as adding a test user account.
# It's also expected that the pre-run script has been run outside of zircon
# to set up unix domain sockets on the host filesystem in /test/sock1 and
# /test/sock2.
# 

import multiprocessing
import os
import shutil
import stat
import sys

TESTDIR = 'testdir'
TESTSUBDIR = 'testdir/subdir'
TESTUSER_UID = 1000

SOCK1 = 'sock1'
SOCK2 = 'sock2'
FILE1 = 'file1'
FILE2 = 'file2'
FILE2_SYMLINK = 'file2-symlink'

success = True

# Owner has R/W/X permissions, group and other have no permissions.
MODE_0700 = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
MODE_MASK = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO

# Try to create the test subdirectory as the non-root test user. This is
# expected to fail because the test user lack sufficient filesystem permission.
# We have to run this in a subprocess because once the initial process
# changes users from root to a non-root user, it can't change back to root.
def test_create_dir():
    os.setuid(TESTUSER_UID)

    try:
        os.mkdir(TESTSUBDIR)
    except PermissionError as pe:
        print('os.mkdir("{}") as user {} failed with permission error as expected'.format(TESTSUBDIR, TESTUSER_UID))
        exit(0)

    print('os.mkdir("{}") as user {} did not fail as expected'.format(TESTSUBDIR, TESTUSER_UID))
    exit(1)

# chmod/fchmod test case for a different aspect of ZIRC-1248. This test case
# uses a regular file that we change the permissions to remove all
# read/write/exec permissions. The current process won't be able to open
# this file, but it should still be able to do chmod/fchmod on it.
# This test case needs to run as a non-root user, since root is able
# to open files even if the file permissions should prevent it.
def test_fchmod():
    os.setuid(TESTUSER_UID)

    try:
        os.unlink(FILE1)
    except Exception:
        pass

    with open(FILE1, 'wb') as fh:
        # First one we always expect to succeed
        os.fchmod(fh.fileno(), 0)
        # Second one triggered ZIRC-1248 when it was present.
        os.fchmod(fh.fileno(), MODE_0700)

        # Change back to 0 to try regular chmod.
        os.fchmod(fh.fileno(), 0)

    os.chmod(FILE1, MODE_0700)
    info = os.stat(FILE1)
    if info.st_mode & MODE_MASK != MODE_0700:
        raise Exception('File mode was not 0700 after chmod')

# Check that the file is owned by the specified uid.
def check_owner(path, uid):
    info = os.lstat(path)
    if info.st_uid != uid:
        raise Exception('File {} was not owned by uid {}'.format(path, uid))

# The base test directory needs to be accessible by the test user, so we use
# the /test directory, which is created in the base image.
os.chdir(sys.argv[1])

# Test that chmod on an unopenable file succeeds. In this case, we use
# a unix domain socket that was created outside of zircon. Regression test
# for ZIRC-1248.
info = os.stat(SOCK1)
if info.st_mode & MODE_MASK != MODE_MASK:
    raise Exception('Initial file mode for "{}" was incorrect'.format(SOCK1))
os.chmod(SOCK1, MODE_0700)
info = os.stat(SOCK1)
if info.st_mode & MODE_MASK != MODE_0700:
    raise Exception('File mode was incorrect after chmod')

# Test that chown on an unopenable file succeeds. Same as the above test case,
# but with chown instead of chmod.
info = os.stat(SOCK2)
if info.st_uid != 0 or info.st_gid != 0:
    raise Exception('Initial file owner or group for "{}" was incorrect'.format(SOCK2))
os.chown(SOCK2, TESTUSER_UID, TESTUSER_UID)
info = os.stat(SOCK2)
if info.st_uid != TESTUSER_UID or info.st_gid != TESTUSER_UID:
    print('{} had uid {} gid {}'.format(SOCK2, info.st_uid, info.st_gid))
    raise Exception('Chown of "{}" did not change owner or group'.format(SOCK2))

# fchmod test case.
child = multiprocessing.Process(target=test_fchmod)
child.start()
child.join()
if child.exitcode != 0:
    print('test_fchmod case child exited with code {}'.format(child.exitcode))
    exit(1)

shutil.rmtree(TESTDIR, ignore_errors=True)
os.mkdir(TESTDIR)
os.chmod(TESTDIR, MODE_0700)

# Check that child process running as non-root user cannot write to a
# directory where it does not have permissions.
child = multiprocessing.Process(target=test_create_dir)
child.start()
child.join()
if child.exitcode != 0:
    print('test_create_dir test case child exited with code {}'.format(child.exitcode))
    exit(1)

# lchown test. Create a file and a symbolic link, then test lchown and chown
# on the symlink. lchown on the symlink should change the owner of the symlink,
# while chown on the symlink should change the owner of the linked-to file.
with open(FILE2, 'w') as fh:
    fh.write('file2 contents')

os.symlink(FILE2, FILE2_SYMLINK)
check_owner(FILE2, 0)
check_owner(FILE2_SYMLINK, 0)

os.lchown(FILE2_SYMLINK, TESTUSER_UID, TESTUSER_UID)
check_owner(FILE2, 0)
check_owner(FILE2_SYMLINK, TESTUSER_UID)

os.chown(FILE2_SYMLINK, TESTUSER_UID, TESTUSER_UID)
check_owner(FILE2_SYMLINK, TESTUSER_UID)

# Now change the owner of the test directory, and try creating a subdirectory
# as a non-root user.
os.chown(TESTDIR, TESTUSER_UID, TESTUSER_UID)
os.chmod(TESTDIR, MODE_0700)

os.setuid(TESTUSER_UID)
os.mkdir(TESTSUBDIR)

print("chown test case passed")
exit(0)

