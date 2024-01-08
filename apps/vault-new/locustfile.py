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
import os
import random
from locust import HttpUser, TaskSet, events
from locust.clients import HttpSession
from test_utils import get_string_bytes

LEN_SMALL = 32
LEN_MEDIUM = 4096
LEN_LARGE = 65536

COUNT_SMALL = 200
COUNT_MEDIUM = 200
COUNT_LARGE = 20

token = os.environ['VAULT_DEV_ROOT_TOKEN_ID']

@events.request_success.add_listener
def dummy(request_type, name, response_time, response_length, **kw):
    return

@events.request_failure.add_listener
def dummy2(request_type, name, response_time, response_length, **kw):
    return
@events.init.add_listener
def vault_init(environment, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host')
    args, unknown = parser.parse_known_args()
    print(args.host)
    print ('Initializing vault')

    client = HttpSession(args.host, locust.events.request_success, locust.events.request_failure)
    print ('Vault root token is %s' % token)

    print ('Creating secrets')

    for i in range(COUNT_SMALL):
        secret_json = json.dumps({'value': get_string_bytes(LEN_SMALL)})
        resp = client.put('/v1/secret/small%d' % i,
                          name='/v1/secret/*',
                          data=secret_json,
                          headers={'Content-Type': 'application/json',
                                   'X-Vault-Token': token})
        resp.raise_for_status()

    for i in range(COUNT_MEDIUM):
        secret_json = json.dumps({'value': get_string_bytes(LEN_MEDIUM)})
        resp = client.put('/v1/secret/medium%d' % i,
                          name='/v1/secret/*',
                          data=secret_json,
                          headers={'Content-Type': 'application/json',
                                   'X-Vault-Token': token})
        resp.raise_for_status()

    for i in range(COUNT_LARGE):
        secret_json = json.dumps({'value': get_string_bytes(LEN_LARGE)})
        resp = client.put('/v1/secret/large%d' % i,
                          name='/v1/secret/*',
                          data=secret_json,
                          headers={'Content-Type': 'application/json',
                                   'X-Vault-Token': token})
        resp.raise_for_status()

def getsmall(l):
    l.client.get('/v1/secret/small%d' % random.randint(0, COUNT_SMALL - 1),
            name='/v1/secret/small*',
            headers={'X-Vault-Token': token})

def getmedium(l):
    l.client.get('/v1/secret/medium%d' % random.randint(0, COUNT_MEDIUM - 1),
            name='/v1/secret/medium*',
            headers={'X-Vault-Token': token})

def getlarge(l):
    l.client.get('/v1/secret/large%d' % random.randint(0, COUNT_LARGE - 1),
            name='/v1/secret/large*',
            headers={'X-Vault-Token': token})

class ClientBehavior(TaskSet):
    tasks = {getsmall:10, getmedium:10, getlarge:1}

class Client(HttpUser):
    tasks = [ClientBehavior]
    min_wait = 0
    max_wait = 0
