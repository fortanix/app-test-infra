#!/usr/bin/python3

import json
import os
import random
import string
import subprocess
import test_app
import time
from test_utils import TestException


class TestElasticSearch(test_app.TestApp):
    default_timeout_s = 60 * 60
    ES_REQUEST_PORT   = 9200
    ES_NODE_COMM_PORT = 9300
    retries           = 100
    saved_index_file  = 'saved_index_file.html'
    expected_index_file = 'reference_index_file.html'
    delay_server_check_status = 5 * 60

    def run(self):
        manifest_env = [ 'discovery.type=single-node' ]
        ports = {
            self.ES_REQUEST_PORT: None,
            self.ES_NODE_COMM_PORT: None,
        }

        # TODO: Need to figure out where elasticsearch puts its data and set rw_dirs more appropriately.
        # TODO: Documentation for elastisearch indicates that system limits should allow 4096 threads. A casual search
        # did not find a way to force elasticsearch to use fewer threads. The converter supports at most 2048 threads
        # right now.
        #
        # Elasticsearch also needs /tmp to be read/write rather than EFS. It wants to mmap a file under /tmp, and
        # we don't currently support that. ZIRC-743.
        extra_container_args = {}
        image_version = None
        random_password = None
        if os.environ['PLATFORM'] == "nitro":
            random_password = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(14))
            input_image = 'elasticsearch'
            image_version = '8.7.0'
            extra_container_args['registry'] ='library'
            extra_container_args['container_env'] = {'ELASTIC_PASSWORD' : random_password,
                                                     'discovery.type' : 'single-node',
                                                     'xpack.security.enabled' : 'true',
                                                     'ENCLAVEOS_DISABLE_DEFAULT_CERTIFICATE' : 'true'}
            TestElasticSearch.expected_index_file = 'reference_index_file_nitro.html'
            TestElasticSearch.delay_server_check_status = 60 # in seconds

        else:
            input_image = 'zapps/elasticsearch'
            image_version = '2020081711-6522b77'

        container = self.container(image=input_image, image_version=image_version, ports=ports,
                                   memsize='4G', manifest_env=manifest_env, nitro_memsize='2G',
                                   rw_dirs=['/var', '/tmp', '/run'], thread_num=2048,
                                   **extra_container_args)
        container.prepare()
        container.run()

        # Delay to allow the server to come up
        time.sleep(TestElasticSearch.delay_server_check_status)
        if random_password:
            url = 'http://elastic:{}@{}:{}/'.format(random_password, container.get_my_ip(), self.ES_REQUEST_PORT)
        else:
            url = 'http://{}:{}/'.format(container.get_my_ip(), self.ES_REQUEST_PORT)

        self.info('Testing if the Elasticsearch is up...')
        running = False
        for i in range(TestElasticSearch.retries):
            ret = os.system('wget -q -O {} {}'.format(TestElasticSearch.saved_index_file, url))
            if ret == 0:
                running = True
                print('Elasticsearch is responsive, continuing to test')
                break
            time.sleep(15)

        if not running or not os.path.isfile(TestElasticSearch.saved_index_file):
            raise TestException('Elasticsearch is not responding')

        # We can't compare the properties like uuid and container name using
        # filecmp because it varies with every run. Here we remove those
        # properties and then compare the json files
        with open(TestElasticSearch.saved_index_file, "r") as read_file:
            file_data = json.load(read_file)
        del file_data['name']
        del file_data['cluster_uuid']

        with open(TestElasticSearch.expected_index_file, "r") as read_ref_file:
            ref_file_data = json.load(read_ref_file)
        del ref_file_data['name']
        del ref_file_data['cluster_uuid']

        if file_data != ref_file_data:
            raise TestException('Web service returned incorrect properties data')

        # Run some standard queries and ensure they succeed by checking
        # output of each response
        query_result = subprocess.check_output(['/usr/bin/python3', 'queries.py',
                                                '-i' , container.get_my_ip(),
                                                '-p', str(self.ES_REQUEST_PORT),
                                                '-k', str(random_password)])
        with open('reference_query_file.html', "rb") as r:
            ref_query_data = r.read()
            if query_result != ref_query_data:
                raise TestException('Web service returned incorrect query data')

        return True

if __name__ == '__main__':
    test_app.main(TestElasticSearch)
