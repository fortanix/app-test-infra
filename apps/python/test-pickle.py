#!/usr/bin/python3
'''
This test tries to pickle and _pickle load and store with various data sizes
'''

import _pickle
import os
import pickle
import traceback

K = 1024
data_sizes = [ 16 * K, \
               60237, \
               32 * K, \
               64 * K, \
               128 * K, \
               178574, \
               200 * K
             ]

PICKLE_FILE_NAME = 'picklefile'
_PICKLE_FILE_NAME = '_picklefile'

def compare_arrays(array1, array2):
    if (len(array1) != len(array2)):
        return False
    l = len(array1)

    for i in range(0,l):
        if (array1[i]!=array2[i]):
            return False
    return True

# pickle load and store function
def pickle_store_file(data, size):
    try :
        pick_file = open(PICKLE_FILE_NAME + str(size), 'ab')
        pickle.dump(data, pick_file)
        pick_file.close()
    except Exception as e:
        traceback.print_exc()
        print('pickle_store_file failed for size = ' + str(size))
        raise

def pickle_load_file(size):
    try:
        pick_file = open(PICKLE_FILE_NAME + str(size), 'rb')
        data = pickle.load(pick_file)
        return data
    except Exception as e:
        traceback.print_exc()
        print('pickle_load_file failed')
        raise


# _pickle load and store function
def _pickle_store_file(data, size):
    try :
        pick_file = open(_PICKLE_FILE_NAME + str(size), 'ab')
        _pickle.dump(data, pick_file)
        pick_file.close()
    except Exception as e:
        traceback.print_exc()
        print('_pickle_store_file failed for size = ' + str(size))
        raise

def _pickle_load_file(size):
    try:
        pick_file = open(_PICKLE_FILE_NAME + str(size), 'rb')
        data = _pickle.load(pick_file)
        return data
    except Exception as e:
        traceback.print_exc()
        print('_pickle_load_file failed')
        raise

def test_pickle(size):
    data = bytearray(os.urandom(size))
    pickle_store_file(data, size)
    data_loaded = pickle_load_file(size)
    assert(compare_arrays(data, data_loaded))

def test__pickle(size):
    data = bytearray(os.urandom(size))
    _pickle_store_file(data, size)
    data_loaded = _pickle_load_file(size)
    assert(compare_arrays(data, data_loaded))


def start_all_tests(type):

    for size in data_sizes:
        #cleanup()
        if (type == 'pickle'):
            test_pickle(size)
        elif (type == '_pickle'):
            test__pickle(size)

def start_tests():
    start_all_tests('pickle')
    start_all_tests('_pickle')

start_tests()
print('test-pickle passed')
