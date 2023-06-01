#!/usr/bin/python3
#
# Copyright (C) 2018 Fortanix, Inc. All Rights Reserved.
#
# Nginx test using standard nginx container.

import filecmp
import json
import os
import time
from OpenSSL import crypto
from test_app import MalborkContainer, TestApp, main, get_zone_cert_local_malbork, get_ip_address
from test_utils import TestException
from test_utils import remove_ignore_nonexistent

class TestNginxAppconfig(TestApp):
    retries = 60
    saved_file = 'index.html'
    saved_ssl_file = 'ssl.html'

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
            print(e)
            return False

    def __init__(self, run_args, test_arg_list):
        super(TestNginxAppconfig, self).__init__(run_args, [])

    def run(self):
        remove_ignore_nonexistent(TestNginxAppconfig.saved_file)
        remove_ignore_nonexistent(TestNginxAppconfig.saved_ssl_file)

        # Our nginx container serves HTTP on port 80 and HTTPS on port 443. In order for our client program to
        # interact with the nginx process without itself running in the same network namespace as nginx, we ask
        # Docker to pass these ports through to the host. By requesting port 'None', we ask for a random host port
        # so we don't have to worry about port conflicts with other software running on the test host.
        malbork_container = MalborkContainer()
        malbork_container.start()
        env_malbork=malbork_container.get_env_var()
        os.environ.update(env_malbork)
        node_url = malbork_container.get_node_base_url()

        ports = {
            80: None,
            443: None,
        }

        # Obtain the CA certificate from malbork backend
        ca_cert = malbork_container.get_zone_cert()
        if not ca_cert:
            raise TestException('Unable to get CA cert')

        ca_path = "/etc/nginx/nginx_ca.crt"
        ca_cert_info = json.dumps({"ca_certificates" : [
            {
                "caPath" : ca_path,
                "caCert" : ca_cert,
                "system" : 'undefined'
            }
        ]})

        cert_info = json.dumps({"certificates": [
            {
                "issuer": "MANAGER_CA",
                "subject": "Fortanix-nginx-curated-app",
                "keyType": "rsa",
                "keyParam": { "size": 2048 },
                "keyPath": "/etc/nginx/nginx-key.pem",
                "certPath": "/etc/nginx/nginx-cert.pem",
            }
        ]})
        manifest_options = {
            'appconfig.em_ip' : '127.0.0.1',
            'appconfig.em_hostname' : 'nodes.localhost',
            'appconfig.skip_server_verify' : 'true',
            'appconfig.port' : '9090',
         }

        container = self.container('nginx', memsize='2G', image_version='1.15.2',
                registry='library',  network_mode='bridge',
                certificates=cert_info,
                container_env={'NODE_AGENT_BASE_URL':node_url},
                ports=ports, ca_certificates=ca_cert_info, manifest_options=manifest_options,
                rw_dirs=['/var/cache/nginx', '/var/run', '/run', '/etc/nginx'],
                hostname='Fortanix-nginx-curated-app')

        scriptDirectory = os.path.dirname(os.path.realpath(__file__))
        ref_file = os.path.join(scriptDirectory, 'reference-output.html')
        ssl_conf = os.path.join(scriptDirectory, 'ssl.conf')

        container.prepare()
        # Following key and cert at path below will be generated by manager
        #'nginx-cert.pem' --> '/etc/nginx'
        #'nginx-key.pem' -->  '/etc/nginx'
        container.copy_file(ssl_conf, '/etc/nginx/conf.d')
        container.run()

        # Check if the CA certificate was installed in the trust store
        status = container.check_CA_trust_store('/etc/ssl/certs/ca-certificates.crt', ca_cert)
        if status is not True:
            print("CA cert was not installed in the trust store.")

        # We are using global bridge network from test_app
        # So don't need to port map but use IP.
        http_port = 80
        https_port = 443
        nginx_ip = container.get_my_ip()

        print('Nginx running with http on ip {} port {} and https on port {}'.format(nginx_ip, http_port, https_port))
        # nginx can take a while before it's serving requests, especially
        # on SGX. Try hitting it with wget a few times until it's serving
        # requests.
        for _ in range(TestNginxAppconfig.retries):
            retval = os.system('wget -nv -O {} http://{}:{}'.format(
                TestNginxAppconfig.saved_file, nginx_ip, http_port))
            if (retval == 0):
                break
            time.sleep(2)

        if not os.path.isfile(TestNginxAppconfig.saved_file):
            raise TestException('Unable to connect with HTTP')

        if not filecmp.cmp(TestNginxAppconfig.saved_file, ref_file):
            raise TestException('nginx returned incorrect data')

        # Copy the server cert file from the container. The server cert's issuer
        # is manually verified here. We can't pass the CA cert file to wget as it also
        # checks for hostname-CN match which will fail in this test. We have not yet
        # set the hostname for the container and supported DNS resolution.
        copied_cert_file = './nginx-cert.pem'
        copied_ca_file = './ca_path'
        container.copy_file_from_container('/etc/nginx/nginx-cert.pem',copied_cert_file)
        container.copy_file_from_container(ca_path, copied_ca_file)
        retval = self.verifyIssuer(copied_cert_file, copied_ca_file)
        if retval is not True:
            raise TestException('Unable to verify certificate.')
        else:
            self.info('Certificate issuer has been verified manually. ')
        remove_ignore_nonexistent(copied_ca_file)
        remove_ignore_nonexistent(copied_cert_file)

        retval = os.system('wget --no-check-certificate -nv -O {} https://{}:{}'.format(
            TestNginxAppconfig.saved_ssl_file, nginx_ip, https_port))

        if (retval != 0):
            raise TestException('nginx wget fail over HTTPS');

        if not os.path.isfile(TestNginxAppconfig.saved_ssl_file):
            raise TestException('Unable to connect with HTTPS')

        if not filecmp.cmp(TestNginxAppconfig.saved_ssl_file, ref_file):
            raise TestException('nginx returned incorrect data over HTTPS');

        return True

if __name__ == '__main__':
    main(TestNginxAppconfig)
