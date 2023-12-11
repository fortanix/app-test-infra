#!/usr/bin/python3

import argparse
import json
import os
import pexpect
import requests
import test_app

TOMCAT_PORT = 8080
DB_PORT = 3306

class TestSpring(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestSpring, self).__init__(run_args, [])
        parser = argparse.ArgumentParser(description='Spring demo test')
        self.args = parser.parse_args(test_arg_list)

    def run(self):
        os.chdir(os.path.dirname(__file__))

        db_container = None
        app_container = None
        converted_app = None
        converted_db = None
        db_name = test_app.gen_hostname('Fortanix-spring-db-')
        app_name = test_app.gen_hostname('Fortanix-spring-app-')

        db_container = self.container('zapps/spring-mysql-db',
                                      converted_image=converted_db,
                                      image_version='2023111911-5dba604',
                                      memsize='2048M',
                                      thread_num=130,
                                      manifest_env=['MALLOC_ARENA_MAX=1'],
                                      network_mode='bridge',
                                      name=db_name,
                                      encrypted_dirs=['/var/lib/mysql', '/tmp','/run/mysqld'],
                                      rw_dirs=['/var/lib/_mysql', '/etc/mysql'],
                                      pexpect=True)

        db_container.prepare()
        db_container.run()

        try:
            db_container.expect(r'mysqld: Shutdown complete')
            db_container.expect(r'ready for connections')
        except pexpect.ExceptionPexpect as e:
            db_container.dump_output()
            self.info('')
            self.error('Failed to start mysql master due to exception : {}'.format(e))
            return False

        db_url = '{}:{}'.format(db_container.get_my_ip(), DB_PORT)
        self.info('mysql db is running on {}'.format(db_url))

        app_container = self.container('zapps/spring-mysql-app',
                                       converted_image=converted_app,
                                       memsize='2048M',
                                       thread_num=80,
                                       network_mode='bridge',
                                       name=app_name,
                                       pexpect=True,
                                       rw_dirs=['/tmp', '/usr/lib', '/root/gs-accessing-data-mysql'],
                                       java_mode='OPENJDK')
        app_container.prepare()

        # We want to update the address of db in the application properties
        app_container.copy_file_from_container('/root/gs-accessing-data-mysql/complete/src/main/resources/application.properties',
                                               './application.properties')

        with open('application.properties') as f:
            contents = f.read().replace('localhost', db_container.get_my_ip())
            contents = contents.replace('/db_example', '/db_example?enabledTLSProtocols=TLSv1.2')

        #contents += 'logging.level.root=WARN\n'

        with open('application.properties', "w") as f:
            f.write(contents)

        app_container.copy_file('application.properties',
                                '/root/gs-accessing-data-mysql/complete/src/main/resources/');

        app_container.run()

        try:
            app_container.expect(r'Tomcat started on port')
        except pexpect.ExceptionPexpect as e:
            app_container.dump_output()
            self.info('')
            self.error('Failed to start spring app due to exception : {}'.format(e))
            return False

        app_url = 'http://{}:{}'.format(app_container.get_my_ip(), TOMCAT_PORT)
        self.info('Spring app is running on {}'.format(app_url))

        params = (
            ('name', 'Test'),
            ('email', 'someemail@emailprovider.com'),
        )

        try:
            response = requests.get('{}/demo/add'.format(app_url), params=params)
            if response.status_code == requests.codes.ok:
                r = response.text
                if r != u'Saved':
                    return False
            else:
                return False
        except Exception as e:
            self.info('add request failed, exception : {}'.format(e))
            return False


        try:
            response = requests.get('{}/demo/all'.format(app_url))
            db_entry = None
            if response.status_code == requests.codes.ok:
                db_entry = json.loads(response.text)[0]
            else:
                return False

            if db_entry['email'] == u'someemail@emailprovider.com' and db_entry['name'] == u'Test':
                self.info('fetch all request passed\n')
                return True
            else:
                self.info('fetch all request failed\n')
                return False
        except Exception as e:
            self.info('fetch all request failed, exception : {}'.format(e))
            return False

if __name__ == '__main__':
    test_app.main(TestSpring)
