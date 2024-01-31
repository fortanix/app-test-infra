#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
'''
Script to run basic queries on elastic search
_________________________________________________________
1. Run the elastic search docker image:
  docker run -it 513076507034.dkr.ecr.us-west-1.amazonaws.com/zapps/elasticsearch:es7.1openjdk
_________________________________________________________
On another terminal, login into the same machine:
2. Get the ip address of the elastic search container:
 sudo docker ps
 sudo docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' <container-id>

3. Access the server using curl:
  curl <container-ip>:9200

4. Run this script by passing the correct ip and port:
  python queries.py -i <container-ip> -p 9200 -k <user-password>

'''
import argparse
import requests

#number of retrails for each search query
NumRetrails = 5

def run_queries(ip_address, port, password):
    user_credentials= ''
    if password:
        user_credentials = 'elastic:{}@'.format(password)
    base_url = "http://{}{}:{}".format(user_credentials, ip_address, port)

    print('-------------- query1: indexing query1 --------------')
    url = "{}/twitter/_doc/1".format(base_url)
    data = '\n{\n    "user": "kimchy",\n    "post_date": "2009-11-15T13:12:00",\n    "message": "Trying out Elasticsearch, so far so good?"\n}'
    params = (
        ('pretty', ''),
    )
    headers = {'Content-Type': 'application/json',}
    response = requests.put(url,data=data,headers=headers,params=params)
    print(response)

    print('-------------- query2: indexing query2 --------------')
    url = '{}/twitter/_doc/2'.format(base_url)
    headers = {
        'Content-Type': 'application/json',
    }
    params = (
        ('pretty', ''),
    )
    data = '\n{\n    "user": "kimchy",\n    "post_date": "2009-11-15T14:12:12",\n    "message": "Another tweet, will it be indexed?"\n}'
    response = requests.put(url, headers=headers, params=params, data=data)
    print(response)

    print('------------- query3: indexing query3 ---------------')
    url = '{}/twitter/_doc/3'.format(base_url)
    headers = {
        'Content-Type': 'application/json',
    }
    params = (
        ('pretty', ''),
    )
    data = '\n{\n    "user": "elastic",\n    "post_date": "2010-01-15T01:46:38",\n    "message": "Building the site, should be kewl"\n}'
    response = requests.put(url, headers=headers, params=params, data=data)
    print(response)

    #search results contains a lot statistical data for the every query which varies across differents runs
    #shards are data units used in Elastic Search and will be unique for each query


    print('-------------- query4: search query1 ----------------')
    url = '{}/twitter/_search'.format(base_url)
    params = (
        ('q', 'user:kimchy'),
        ('pretty', 'true'),
    )
    res = requests.get(url, params=params)
    print(res)

    print('------------- query5: search query2 ------------------')
    headers = {
        'Content-Type': 'application/json',
    }
    params = (
        ('pretty', 'true'),
    )
    data = '\n{\n    "query" : {\n        "match_all" : {}\n    }\n}'
    res = requests.post(url, headers=headers, params=params, data=data)
    print(res)

    print('-------------- query6: search query3 ------------------')
    headers = {
        'Content-Type': 'application/json',
    }
    params = (
        ('pretty', 'true'),
    )
    data = '\n{\n    "query" : {\n        "range" : {\n            "post_date" : { "from" : "2009-11-15T13:00:00", "to" : "2009-11-15T14:00:00" }\n        }\n    }\n}'
    res = requests.post(url, headers=headers, params=params, data=data)
    print(res)

    #-------------- End ---------------------------------
    print("Done.")

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ip')
    parser.add_argument('-p', '--port')
    parser.add_argument('-k', '--key')
    args = parser.parse_args()
    ip = args.ip
    port = args.port
    password = args.key

    run_queries(ip, port, password)
