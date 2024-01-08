import os
import random
from locust import HttpLocust, TaskSet


def get100(l):
    resp = l.client.get('/random/100/%d' % random.randint(1, 100))
    statinfo = os.stat('root/rootfs/htdocs/random/100/1')
    assert statinfo.st_size == len(resp.content)
    return resp

def get2k(l):
    resp = l.client.get('/random/2048/%d' % random.randint(1, 10))
    statinfo = os.stat('root/rootfs/htdocs/random/2048/1')
    assert statinfo.st_size == len(resp.content)
    return resp
def get10k(l):
    l.client.get('/random/10240/%d' % random.randint(1, 5))

def get100k(l):
    l.client.get('/random/102400/%d' % random.randint(1, 5))

def get1m(l):
    l.client.get('/random/1048576/%d' % random.randint(1, 3))

def get10m(l):
    resp = l.client.get('/random/10485760/%d' % random.randint(1, 3))
    statinfo = os.stat('root/rootfs/htdocs/random/10485760/1')
    assert statinfo.st_size == len(resp.content)
    return resp

def getpapers(l):
    l.client.get('/oscar-web/papers.php')

def getnews(l):
    resp = l.client.get('/oscar-web/news.php')
    return resp
def getpeople(l):
    resp = l.client.get('/oscar-web/people.php')
    return resp

def getprojects(l):
    l.client.get('/oscar-web/projects.php')


class ClientBehavior(TaskSet):
    tasks = {getnews:10, getpeople:10, getpapers:10, getprojects:10, get100:10, get2k:10, get10k:5, get100k:5, get1m:1, get10m:1}
    #tasks = {getnews, getpeople, getpapers, getprojects}

class Client(HttpLocust):
    task_set = ClientBehavior
    min_wait = 0
    max_wait = 0
