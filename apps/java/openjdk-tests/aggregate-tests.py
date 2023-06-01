#!/usr/bin/python3

# Parse a file of Java results and aggregate it to the third
# directory level if possible.

# Go from:

# javax/sql/testng/test/rowset/RowSetMetaDataTests.java Test results: passed: 1
# javax/sql/testng/test/rowset/RowSetProviderTests.java Test results: passed: 1
# javax/sql/testng/test/rowset/RowSetWarningTests.java Test results: passed: 1
# javax/sql/testng/util/PropertyStubProvider.java Test results: passed: 1
# javax/sql/testng/util/StubArray.java Test results: passed: 1

# to:

# javax/sql/testng 5 0 0 0

# If paths are shorter than three names, deal with it.  Note that
# shorter names don't include the totals from longer names that
# may be hiercically below them:

# jdk/lambda  29 0 1 0
# jdk/lambda/separate  4 0 3 1

import sys
import os
import string

def process_file(f):
    total = dict()
    for l in f:
        word = l.strip().split()
        if len(word) < 5:
            exit(1)
        while len(word) > 5 and word[3] != 'no':
            word = word[1:]
        #print('*{}*'.format(word[0]))
        if word[0] == 'ZirconTotal:':
            continue
        name = word[0].split('/')
        title = ''
        for i in range(min(len(name), 3)):
            if name[i].find('.java') != -1 or name[i].find('.sh') != -1:
                break
            if len(title):
                title += '/'
            title += name[i]
        if title not in total:
            total[title] = dict()
        # "no tests selected" appears occasionally
        if word[3] == 'no':
            continue
        if word[3] in total[title]:
            total[title][word[3]] += int(word[4])
        else:
            total[title][word[3]] = int(word[4])

    vals = ['passed:', 'failed:', 'error:', 'hung:']
    for i in total:
        print(i, end = ' ')
        for w in vals:
            if w in total[i]:
                print(' {}'.format(total[i][w]), end = '')
            else:
                print(' 0', end = '')
        print()

if len(sys.argv) < 2:
    process_file(sys.stdin)
else:
    for file in sys.argv[1:]:
        process_file(open(file, "r"))
