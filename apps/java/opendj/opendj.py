#!/usr/bin/python3

import ldap3
import os
import sys
import test_app
import time

LDAP_PORT = 1389
RETRIES = 1800

def check_modules():
    # n.b. ldap3 version 2.2.4 claims that it is version 2.2.2, yuck
    bad_version = "2.2.3"

    if ldap3.__version__ == bad_version:
        print("Your python3-ldap3 module version will not work with this test.")
        print("Your module version: {}".format(ldap3.__version__))
        print("Please run pip3 install ldap3==2.2.4")
        print("You may need to first uninstall the old version of "
              "python3-ldap3")

        sys.exit(1)

class TestOpenDJ(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestOpenDJ, self).__init__(run_args)

    def run(self):
        os.chdir(os.path.dirname(__file__))

        self.info('Starting OpenDJ...', end='')

        ports = {
            LDAP_PORT: None
        }

        container = self.container(
            'zapps/opendj',
            entrypoint=[
                '/usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java',
                '-Xmx512m',
                '-client',
                '-Dorg.opends.server.scriptName=start-ds',
                'org.opends.server.core.DirectoryServer',
                '--configClass',
                'org.opends.server.extensions.ConfigFileHandler',
                '--configFile',
                '/opt/opendj/config/config.ldif',
                '--nodetach'
            ],
            rw_dirs=['/opt/opendj'],
            manifest_env=[
                'JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64/jre',
                'LANG=C.UTF-8',
                'CONFIG_FILE=/opt/opendj/config/config.ldif',
                'PID_FILE=/opt/opendj/logs/server.pid',
                'LOG_FILE=/opt/opendj/logs/server.out',
                'INSTANCE_ROOT=/opt/opendj',
                'INSTALL_ROOT=/opt/opendj',
                'CLASSPATH=/opt/opendj/classes:/opt/opendj/lib/bootstrap.jar',
            ],
            java_mode='OPENJDK',
            memsize='2G', # ZIRC-5538 this failed on SGX soak with less memory.
            thread_num=512,
            ports=ports)
        container.prepare()
        container.run()

        self.info('waiting for server to be ready')

        for r in range(RETRIES):
            try:
                server = ldap3.Server('localhost:{}'.format(container.get_port_mapping(LDAP_PORT)), get_info=ldap3.ALL)
                conn = ldap3.Connection(server, 'cn=Directory Manager', 'password', auto_bind=True, raise_exceptions=True)
                break
            except Exception as e:
                if r == RETRIES - 1:
                    self.info('Timed out waiting for server to start')
                    raise(e)
                time.sleep(1)
            
        
        self.info(' done.')

        inetOrgPersonDef = ldap3.ObjectDef(['inetOrgPerson'], conn)

        reader = ldap3.Reader(conn, inetOrgPersonDef, 'dc=example,dc=com').search()

        cns = list(map(lambda e: e.cn, reader))

        QUERY_COUNT = 100

        for i in range(0, QUERY_COUNT):
            reader = ldap3.Reader(conn, inetOrgPersonDef, 'dc=example,dc=com', 'cn:=%s' % cns[i]).search()
            if len(list(reader)) != 1:
                self.error('Wrong number of results for cn=%s' % cns[i])
                print(list(reader))
                return False

        self.info('Successfully performed %d queries' % QUERY_COUNT)

        return True

if __name__ == '__main__':
    check_modules()
    test_app.main(TestOpenDJ)
