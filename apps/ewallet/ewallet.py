#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import json
import os
import subprocess
import test_app
import time
import traceback
from OpenSSL import crypto
from test_utils import (TestException, get_locust_version,
                        remove_ignore_nonexistent)

NUM_TRIALS         = 10
MANAGER_HTTP_PORT  = 8042
MANGAER_HTTPS_PORT = 8040
DB_PORT            = 3306
NGINX_HTTP_PORT    = 80
NGINX_HTTPS_PORT   = 443
EWALLET_PORT       = 9090
locust_log = 'locust.log'

class TestEwallet(test_app.TestApp):
    saved_file = 'index.html'
    saved_ssl_file = 'ssl.html'
    if ('weekly' in os.environ['CI_FREQ']):
        heartbeat_sleep_time = 30
    else:
        heartbeat_sleep_time = 30
    heartbeat_interval = 5
    expected_heartbeat_count = (heartbeat_sleep_time / heartbeat_interval)
    # We might not want to fail for a few heartbeat counts falling short owing to scheduling delays.
    # For longer durations like 12 hours, with one second freq, the avg frequency was slightly less than one.
    # Also we could always miss one beat due to timing of the query.
    heartbeat_low = int((expected_heartbeat_count - 1)*0.9)
    # The extra allowance on top of expected_heartbeat_count is to allow for delay in python quering the counts.
    # Since heartbeat_interval is 5 seconds, an allowance of 1 heartbeat seems ok.
    heartbeat_high = expected_heartbeat_count + 1

    def verifyIssuer(self, cert_filename, cacert_filename):
        with open(cert_filename, 'r') as f:
            cert_str = f.read()
        certificate = crypto.load_certificate(crypto.FILETYPE_PEM, cert_str)

        try:
            store = crypto.X509Store()

            with open(cacert_filename, 'r') as f1:
                ca_cert_str = f1.read()

            ca_certificate = crypto.load_certificate(crypto.FILETYPE_PEM, ca_cert_str)
            store.add_cert(ca_certificate)
            store_ctx = crypto.X509StoreContext(store, certificate)
            store_ctx.verify_certificate()
            return True

        except Exception as e:
            traceback.print_exc()
            return False

    def __init__(self, run_args, test_arg_list):
        # This test is a little special, because it needs multiple containers to run. If you want to run
        # with pre-converted containers, instead of using the --converted-image option, you need to pass
        # additional arguments ewallet_image ewallet_db_image ewallet_nginx_image.
        super(TestEwallet, self).__init__(run_args, [])

        self.converted_images = None
        if len(test_arg_list) > 0:
            if len(test_arg_list) != 3:
                raise ValueError('Run test with test_arg_list ewallet_image ewallet_db_image ewallet_nginx_image')

            self.converted_images = test_arg_list

    def run(self):
        os.chdir(os.path.dirname(__file__))

        remove_ignore_nonexistent(TestEwallet.saved_file)
        remove_ignore_nonexistent(TestEwallet.saved_ssl_file)

        nginx_container = None
        db_container = None
        app_container = None

        if self.converted_images:
            assert(len(self.converted_images) == 3)
            converted_app = self.converted_images[0]
            converted_db = self.converted_images[1]
            converted_nginx = self.converted_images[2]
        else:
            converted_app = None
            converted_db = None
            converted_nginx = None

        # Start the EM to obtain app certs
        malbork_container = test_app.MalborkContainer()
        malbork_container.start()
        env_malbork=malbork_container.get_env_var()
        os.environ.update(env_malbork)
        node_url = malbork_container.get_node_base_url()

        # Generating a set of random names for the containers. These can be used as hostnames
        # for the containers in a production environment. For the CI test, they are used as
        # the container names. When all containers are running on the same network bridge,
        # the container names can be used as domain names for them to communicate amongst
        # themselves.
        nginx_name = test_app.gen_hostname('Ftx-ewallet-nginx')
        app_name = test_app.gen_hostname('Ftx-ewallet-app')
        db_name = test_app.gen_hostname('Ftx-ewallet-db')

        # Obtain the CA certificate from malbork backend
        ca_cert = malbork_container.get_zone_cert()
        if not ca_cert:
            raise TestException('Unable to get CA cert')

        # __________ DB container ___________
        self.info('Starting mysql...', end='', flush=True)

        db_env_var = {
            'NODE_AGENT_BASE_URL'   : node_url,
            'EWALLET_USER'          : app_name,
        }

        db_cert_info = json.dumps({ "certificates": [
            {
                "issuer"   : "MANAGER_CA",
                "subject"  : db_name,
                "keyType"  : "rsa",
                "keyParam" : { "size": 2048 },
                "keyPath"  : "/etc/mysql/server-key.pem",
                "certPath" : "/etc/mysql/server-cert.pem",
            }
        ]})

        db_ca_path = "/etc/mysql/cacert.pem"
        db_ca_cert_info = json.dumps({"ca_certificates" : [
            {
                "caPath" : db_ca_path,
                "caCert" : ca_cert,
                "system" : "true"
            }
        ]})

        db_app_info = json.dumps({"app": {"heartbeat" : "true", "name": db_name}})

        db_container = self.container('zapps/ewallet-db',
                                      converted_image=converted_db,
                                      memsize='2048M', thread_num=80,
                                      network_mode='bridge',
                                      container_env=db_env_var,
                                      allow_some_env=['EWALLET_USER'],
                                      certificates=db_cert_info,
                                      ca_certificates=db_ca_cert_info,
                                      app=db_app_info,
                                      name=db_name,
                                      rw_dirs= ["/var/lib/_mysql", "/run", "/etc/mysql"])
        db_container.prepare()
        db_container.run()
        db_url = 'https://{}:{}'.format(db_container.get_my_ip(), DB_PORT)
        self.info('Mysql is running on {}'.format(db_url))

        # Check if the CA certificate was installed in the trust store
        status = db_container.check_CA_trust_store('/etc/ssl/certs/ca-certificates.crt', ca_cert)
        if status is not True:
            raise TestException("CA cert was not installed in the trust store.")

        # __________ EWALLET container ___________
        self.info('Starting ewallet...', end='', flush=True)

        ewallet_cert_file = '/etc/ewallet/cert.pem'
        ewallet_key_file  = '/etc/ewallet/key.pem'
        ewallet_ca_file   = '/etc/ssl/certs/ca-cert.pem'

        app_env_var = [
            'MYSQL_USER=ewallet',
            'MYSQL_PASSWORD=password',
            'MYSQL_HOST={}'.format(db_name),
            'SERVER_CERT_FILE={}'.format(ewallet_cert_file),
            'SERVER_KEY_FILE={}'.format(ewallet_key_file),
            'CA_CERT_FILE={}'.format(ewallet_ca_file),
            'MYSQL_CHECK_HOSTNAME=False',
        ]

        app_cert_info = json.dumps({"certificates": [
            {
                "issuer"    : "MANAGER_CA",
                "subject"   : app_name,
                "keyType"   : "rsa",
                "keyParam"  : { "size": 2048 },
                "keyPath"   : ewallet_key_file,
                "certPath"  : ewallet_cert_file,
            }
        ]})

        app_ca_cert_info = json.dumps({"ca_certificates" : [
            {
                "caPath" : ewallet_ca_file,
                "caCert" : ca_cert,
                "system" : "false"
            }
        ]})

        # Testing for auto enable of heartbeat, below two should be equivalent
        app_info = json.dumps({"app": {"heartbeat" : "true", "name": app_name}})

        app_container = self.container('zapps/ewallet',
                                       memsize='1G',
                                       converted_image=converted_app,
                                       network_mode='bridge',
                                       manifest_env=app_env_var,
                                       container_env={'NODE_AGENT_BASE_URL': node_url},
                                       certificates=app_cert_info,
                                       ca_certificates=app_ca_cert_info,
                                       rw_dirs=["/etc/ewallet"],
                                       app=app_info,
                                       name=app_name)
        app_container.prepare()
        app_container.run()
        app_url = 'https://{}:{}/'.format(app_name, EWALLET_PORT)
        self.info('Ewallet is running on https://{}:{}'.format(app_container.get_my_ip(), EWALLET_PORT))

        # Check if the CA certificate was installed in the trust store
        status = app_container.check_CA_trust_store('/etc/ssl/certs/ca-certificates.crt', ca_cert)
        if status is not False:
            raise TestException("CA cert was installed in the trust store even when system was set to false.")

        # __________ NGINX container ___________
        self.info('Starting nginx...', end='', flush=True)
        nginx_ports = {
            NGINX_HTTP_PORT : None,
            NGINX_HTTPS_PORT: None
        }

        nginx_env_var = {
            'NODE_AGENT_BASE_URL' : node_url,
            'PROXY_PASS_URL'      : app_url,
        }

        nginx_cert_info = json.dumps({ "certificates" : [
            {
                "issuer"    : "MANAGER_CA",
                "subject"   : nginx_name,
                "keyType"   : "rsa",
                "keyParam"  : { "size": 2048 },
                "keyPath"   : "/etc/nginx/nginx-key.pem",
                "certPath"  : "/etc/nginx/nginx-cert.pem",
            }
        ]})

        nginx_ca_path = "/etc/nginx/cacert.crt"
        nginx_ca_cert_info = json.dumps({"ca_certificates" : [
            {
                "caPath" : nginx_ca_path,
                "caCert" : ca_cert,
                "system" : "undefined"
            }
        ]})

        nginx_app_info = json.dumps({"app": {"heartbeat" : "true", "name": nginx_name}})

        nginx_container = self.container('zapps/ewallet-nginx',
                                         converted_image=converted_nginx,
                                         memsize='1024M', thread_num=32,
                                         network_mode='bridge', ports=nginx_ports,
                                         container_env=nginx_env_var,
                                         allow_some_env=['PROXY_PASS_URL'],
                                         certificates=nginx_cert_info,
                                         ca_certificates=nginx_ca_cert_info,
                                         app=nginx_app_info,
                                         name=nginx_name,
                                         rw_dirs=['/var/cache/nginx', '/etc/nginx'])

        nginx_container.prepare()
        nginx_container.run()
        nginx_https_port = nginx_container.get_port_mapping(NGINX_HTTPS_PORT)
        nginx_url = 'https://localhost:{}/'.format(nginx_https_port)
        test_network = 'container:{}'.format(nginx_container.container.short_id)

        self.info('Nginx is running on {}'.format(nginx_url))

        # Check if the CA certificate was installed in the trust store
        nginx_container.check_CA_trust_store('/etc/ssl/certs/ca-certificates.crt', ca_cert)

        sleep_time = 300
        self.info('Sleeping {} seconds to give services a chance to start running'.format(sleep_time))
        time.sleep(sleep_time)
        self.info('Waiting until nginx is responding')
        running = False
        output = ''
        for i in range(20):
            try:
                output = subprocess.check_output(['curl', '-s', '-X' 'POST',
                                                  '-d' 'name=user1&email=user@ftx.com&rpwd=password',
                                                  '--insecure', nginx_url + 'signUp'])
                if output.strip() == b'{"id": 1}':
                    running = True
                    print('nginx is responsive, continuing on to test')
                    break
                else:
                    # xxx debugging
                    print('curl output is {}'.format(output))
            except subprocess.CalledProcessError:
                pass
            time.sleep(10)

        if not running:
            print('last wget output: {}'.format(output))
            raise TestException('web server not responding')

        # Copy the server cert file from the container. The server cert's issuer
        # is manually verified here. We can't pass the CA cert file to wget as it also
        # checks for hostname-CN match which will fail in this test. We have not yet
        # set the hostname for the container and supported DNS resolution.
        copied_cert_file = './nginx-cert.pem'
        copied_ca_file = './ca_path'
        nginx_container.copy_file_from_container('/etc/nginx/nginx-cert.pem', copied_cert_file)
        nginx_container.copy_file_from_container(nginx_ca_path, copied_ca_file)
        retval = self.verifyIssuer(copied_cert_file, copied_ca_file)
        if retval is not True:
            raise TestException('Unable to verify certificate.')
        else:
            self.info('Certificate issuer has been verified manually. ')
        remove_ignore_nonexistent(copied_ca_file)
        remove_ignore_nonexistent(copied_cert_file)
        locust_version = get_locust_version()
        print('locust_version = ', locust_version)
        time_s = 20
        locust_result = subprocess.call(['locust',
                                         '--headless',
                                         '--only-summary',
                                         '--locustfile=locustfile.py',
                                         '--users=1',
                                         '--run-time={}s'.format(time_s),
                                         '--spawn-rate=100',
                                         '--loglevel=INFO',
                                         '--logfile={}'.format(locust_log),
                                         '--host={}'.format(nginx_url)])

        heartbeat_count_list = malbork_container.get_heartbeat_count(app_list=[app_name])
        start = heartbeat_count_list[0]['message_count']
        time.sleep(self.heartbeat_sleep_time)
        heartbeat_count_list = malbork_container.get_heartbeat_count(app_list=[app_name])
        diff = heartbeat_count_list[0]['message_count'] - start

        if (diff < self.heartbeat_low  or diff > self.heartbeat_high):
            self.error('Expected heartbeats {}, range:({} - {}), received {}'\
                    .format(self.expected_heartbeat_count, self.heartbeat_low, self.heartbeat_high, diff));
            return False

        self.info(' done')

        if locust_result != 0:
            self.error('HTTP testing with locust failed')
            return False
        else:
            return True
    def get_timeout(self):
        # default time out + sleep_time
        return (self.default_timeout_s + self.heartbeat_sleep_time)

if __name__ == '__main__':
    test_app.main(TestEwallet)
