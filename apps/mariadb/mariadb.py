#!/usr/bin/python3

import argparse
import MySQLdb
import os
import pexpect
import test_app
from test_utils import random_string

MYSQL_PORT = 3306

class TestMysql(test_app.TestApp):
    def __init__(self, run_args, test_arg_list):
        super(TestMysql, self).__init__(run_args, [])
        parser = argparse.ArgumentParser(description='Mysql test')
        self.args = parser.parse_args(test_arg_list)

    def do_sql(self, port, passwd):
        db = MySQLdb.connect(host='127.0.0.1', user='root', passwd=passwd, port=port)
        cur = db.cursor()
        cur.execute('drop database if exists test;')
        cur.execute('create database test;')
        cur.execute('use test')
        cur.execute('create table test (id integer primary key not null auto_increment, ' +
                'name varchar(255), ' +
                'num integer) ' +
                'engine innodb;')
        cur.execute('insert into test (name, num) values ("foo", 22);')
        cur.execute('commit;')

        cur.execute('select name, num from test')

        row = cur.fetchone()
        if row != ('foo', 22):
            print("Expected ('foo', 22), got", row)
            return False
        cur.execute('shutdown')

        return True

    def do_sql_rerun(self, port, passwd):
        db = MySQLdb.connect(host='127.0.0.1', user='root', passwd=passwd, port=port)
        cur = db.cursor()
        cur.execute('use test')
        cur.execute('select name, num from test')
        row = cur.fetchone()
        if row != ('foo', 22):
            print("Expected ('foo', 22), got", row)
            return False

        return True

    def run(self):
        os.chdir(os.path.dirname(__file__))

        ports = {
            MYSQL_PORT: None
        }

        persist_vol_name = test_app.gen_volume_name('test-mariadb-container')
        # Generate a random root password.
        passwd = random_string(8)
        # Environment variables needed for filesystem persistence in nitro since
        # mysql server is restarted and expects data to be persisted
        dsm_endpoint_env_var = 'FS_DSM_ENDPOINT={}'.format(test_app.SMARTKEY_ENDPOINT)
        dsm_api_key = 'FS_API_KEY={}'.format(os.getenv('FORTANIX_API_KEY', None))
        # Connection to DSM works only on bridge network in nitro
        nitro_args = {}
        if os.environ['PLATFORM'] == 'nitro':
            nitro_args = {'network':'bridge',
                          'container_env': [ 'MYSQL_ROOT_PASSWORD={}'.format(passwd),
                                             'ENCLAVEOS_DEBUG=debug',
                                             'RUST_LOG=info',
                                             dsm_endpoint_env_var,
                                             dsm_api_key,
                                             'ENCLAVEOS_DISABLE_DEFAULT_CERTIFICATE=true'] }

        container = self.container(
            'zapps/mariadb',
            memsize='2048M',
            thread_num=80,
            auto_remove=False,
            encrypted_dirs=['/var/lib/mysql', '/tmp','/run/mysqld'],
            rw_dirs=['/var/lib/_mysql', '/etc/mysql'],
            persistent_volume={persist_vol_name:'/var/lib/mysql'},
            ports=ports,
            pexpect=True,
            pexpect_tmo=1200,
            allow_some_env=['MYSQL_ROOT_PASSWORD'],
            manifest_env=['MYSQL_ROOT_PASSWORD={}'.format(passwd)],
            enable_overlay_fs_persistence=True,
            **nitro_args)
        container.prepare()
        container.run()

        mysql_port = container.get_port_mapping(MYSQL_PORT)
        print("mysql_port is {}".format(mysql_port))

        try:
            container.expect(r'mysqld: Shutdown complete')
            container.expect(r'ready for connections')
        except pexpect.ExceptionPexpect:
            container.dump_output()
            self.info('')
            self.error('Failed to start mysql.')
            return False

        success = self.do_sql(mysql_port, passwd)
        if success:
            print("Container run query done")

            container.rerun()
            try:
                container.expect(r'ready for connections')
            except pexpect.ExceptionPexpect:
                container.dump_output()
                self.info('')
                self.error('Failed to restart mysql container.')
                return False
            success = self.do_sql_rerun(container.get_port_mapping(MYSQL_PORT), passwd)
            if success:
                print("Container rerun query done")

        if not success:
            container.dump_output()
            self.info('')
            self.error('SQL test failed')
            return False
        else:
            self.info('SQL test successful')
            return True


if __name__ == '__main__':
    test_app.main(TestMysql)
