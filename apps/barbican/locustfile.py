#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import argparse
import json
import locust
import random
from locust import HttpUser, TaskSet, events
from locust.clients import HttpSession
from test_utils import get_string_bytes
from urllib.parse import urlparse

LEN_SMALL = 32
LEN_MEDIUM = 4096

COUNT_SMALL = 200
COUNT_MEDIUM = 200

PATH_SMALL = [None] * COUNT_SMALL
PATH_MEDIUM = [None] * COUNT_MEDIUM

token = ''
@events.request_success.add_listener
def dummy(request_type, name, response_time, response_length, **kw):
    return

@events.request_failure.add_listener
def dummy2(request_type, name, response_time, response_length, **kw):
    return

@events.init.add_listener
def barbican_init(environment, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host')
    args, unknown = parser.parse_known_args()
    print(args.host)

    client = HttpSession(args.host, locust.events.request_success, locust.events.request_failure)

    print('Creating secrets')

    for i in range(COUNT_SMALL):
        secret_json = json.dumps({'value': get_string_bytes(LEN_SMALL)})
        resp = client.post('/v1/secrets',
                name='/v1/secrets small',
                data=secret_json,
                headers={'Content-Type': 'application/json',
                    'X-Project-Id': '12345'})
        resp.raise_for_status()
        resp_data = json.loads(resp.content)
        PATH_SMALL[i] = urlparse(resp_data['secret_ref']).path

    for i in range(COUNT_MEDIUM):
        secret_json = json.dumps({'value': get_string_bytes(LEN_MEDIUM)})
        resp = client.post('/v1/secrets',
                name='/v1/secrets medium',
                data=secret_json,
                headers={'Content-Type': 'application/json',
                    'X-Project-Id': '12345'})
        resp.raise_for_status()
        resp_data = json.loads(resp.content)
        PATH_MEDIUM[i] = urlparse(resp_data['secret_ref']).path

def getsmall(l):
    l.client.get(PATH_SMALL[random.randint(0, COUNT_SMALL - 1)],
            name='/v1/secrets small',
            headers={'X-Project-Id': '12345'})

def getmedium(l):
    l.client.get(PATH_MEDIUM[random.randint(0, COUNT_MEDIUM - 1)],
            name='/v1/secrets medium',
            headers={'X-Project-Id': '12345'})

class ClientBehavior(TaskSet):
    tasks = {getsmall:10, getmedium:10}

class Client(HttpUser):
    tasks = [ClientBehavior]
    min_wait = 0
    max_wait = 0
