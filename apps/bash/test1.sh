#!/bin/bash

if [ "$(/root/test2.sh)" = "Output from child process" ] && [ "$(/root/test5.sh)" = "test 5 passed" ]; then
    echo "test1 passed"
else
    echo "test1 failed"
fi
