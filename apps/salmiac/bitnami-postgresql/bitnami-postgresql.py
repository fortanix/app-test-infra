#!/usr/bin/python3
#
# Copyright (C) 2023 Fortanix, Inc. All Rights Reserved.
#
# Test to convert and check that the postgresql server
# starts up. Note that we do not run any queries to test
# the functionality of the database yet.

import test_app
import time

class TestBitnamiPostgresql(test_app.TestApp):
    def run(self):
        status = False
        container = self.container(registry='docker.io', image='bitnami/postgresql',
                                   image_version='15.1.0-debian-11-r20', memsize='2048M',
                                   container_env=['ALLOW_EMPTY_PASSWORD=yes', 'ENCLAVEOS_DEBUG=debug', 'RUST_LOG=info']
                                   )
        container.prepare()
        container.run()

        server_ip = container.get_my_ip()

        # psql is the client which connects to the postgresql server
        # -h passes the server hostname/ip address
        # -l lists the databases available in the server
        # For additional operations, check psql --help
        # In this test, we only check that the client can talk to the server.
        # We do this by fetching the available databases in the server and
        # check the expected output on the client container.
        client_cmd = '/opt/bitnami/scripts/postgresql/entrypoint.sh psql -h {} -l'.\
                     format(server_ip)
        client_container = test_app.NativeContainer(registry='docker.io', image='bitnami/postgresql',
                                                    image_version='15.1.0-debian-11-r20', entrypoint= client_cmd)
        client_container.prepare()

        retry_count = 10
        while retry_count > 0:
            try:
                status = client_container.run_and_search_logs('3 rows')
                break
            except:
                time.sleep(10)
                pass
            retry_count = retry_count -1

        return status

if __name__ == '__main__':
    test_app.main(TestBitnamiPostgresql)

