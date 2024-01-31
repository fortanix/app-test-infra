#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
from locust import HttpUser, TaskSet, events


def getmain(l):
    l.client.get('/', verify=False)

def login(l):
    USER_CREDENTIALS = [
        ("user1", "password"),
    ]
    user, passw = USER_CREDENTIALS.pop()
    email = user+ 'ftx.com'
    l.client.post("/login", {"email":email, "pwd":passw}, verify=False)

def signup(l):
    USER_CREDENTIALS = [
        ("user1", "password"),
    ]
    user, passw = USER_CREDENTIALS.pop()
    email = user+ 'ftx.com'
    l.client.post("/signUp", {"name":user, "email":email, "rpwd":passw}, verify=False)


def payment(l):
    USER_CREDENTIALS = [
        ("user1", "password"),
    ]
    user, passw = USER_CREDENTIALS.pop()
    {"card-holder-name":user, "card-number":"123312", "expiry-month":"11", "expiry-year":"2013", "cvv":"1234"}
    l.client.post("/pay", verify=False)

class ClientBehavior(TaskSet):
    tasks = {getmain, signup, login}

class Client(HttpUser):
    tasks = [ClientBehavior]
    min_wait = 0
    max_wait = 0
