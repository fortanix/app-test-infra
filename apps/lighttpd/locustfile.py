#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import random
from locust import HttpUser, TaskSet


def get100(l):
    l.client.get('/random/100/%d' % random.randint(1, 100))

def get2k(l):
    l.client.get('/random/2048/%d' % random.randint(1, 10))

def get10k(l):
    l.client.get('/random/10240/%d' % random.randint(1, 5))

def get100k(l):
    l.client.get('/random/102400/%d' % random.randint(1, 5))

def get1m(l):
    l.client.get('/random/1048576/%d' % random.randint(1, 3))

def get10m(l):
    l.client.get('/random/10485760/%d' % random.randint(1, 3))

class ClientBehavior(TaskSet):
    tasks = {get100:10, get2k:10, get10k:5, get100k:5, get1m:1, get10m:1}

class Client(HttpUser):
    tasks = [ClientBehavior]
    min_wait = 0
    max_wait = 0
