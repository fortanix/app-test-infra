#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# App test to ensure a non root user app can access CA cert in
# an encrypted directory. ZIRC-5075

import json
import test_app


class AppcertPermissions(test_app.TestApp):
    def __init__(self, run_args, _):
        super(AppcertPermissions, self).__init__(run_args, [])

    def run(self):
        rw_dirs = [
            '/root',
            '/test',
        ]

        # Obtain the CA certificate from malbork backend
        ca_cert = "-----BEGIN CERTIFICATE-----\n\
MIIEWDCCAsCgAwIBAgIUddagHPUE0iwLBeUM/eKiC8tOgnowDQYJKoZIhvcNAQEL\n\
BQAwMzExMC8GA1UEAwwoRGF0YXNoaWVsZCBNYXN0ZXIgWm9uZSBFbmNsYXZlIFpv\n\
bmUgUm9vdDAeFw0yMjAzMDkxNDA5MDFaFw0yNzAzMDkxNDA5MDFaMDMxMTAvBgNV\n\
BAMMKERhdGFzaGllbGQgTWFzdGVyIFpvbmUgRW5jbGF2ZSBab25lIFJvb3QwggGi\n\
MA0GCSqGSIb3DQEBAQUAA4IBjwAwggGKAoIBgQC/tZ/Bw2hXIIvTOCInfEMbrJcg\n\
FIhugOcm197A0x7xSGQQ8IQD6v+l76yyuQLNvnD/QCZZ+vUATFhPizDpxZ5CHW40\n\
g8LI6B1leHF2zPnK2CES4Bler1GiMdvsSoIL7oe6xDKwRhT338LElrujRlQgrCqD\n\
HeIn8lVzdtdWToFJDJTZWq1kctyh3AyFStP7zVCTrei5T1b6JJ8VUKhk2QJHEDF9\n\
TIcxp/6B207E019r/SYKv3LdT0L9A/8u/M2pPWDFk6tPpu64ZxTHEqD6CXpe+h49\n\
1nn6t178Ffm1OyuKKaQiZ40kPKM96Mu1A9KMJA0KH4QDoKooN6Fi9NHbtbFPwvpl\n\
xDdU69nXDlElVlRp7gn1tBzHTUqF3wMLAs4Yn4QNJCOcRp9+JRQYmI2TEfd4pLx7\n\
y2l7+gR88/fKM+ZRjeTgDcpU9YDP6amxhFL12gGsk7HuLqLwMWKl6ufVM9btBduN\n\
brPS5jP6prjq64Txi+1ISU2BAEPSK2XB/4q9KQMCAwEAAaNkMGIwDwYDVR0TAQH/\n\
BAUwAwEB/zAPBgNVHQ8BAf8EBQMDB4YAMB8GA1UdIwQYMBaAFKjzA/SglA8z90PG\n\
ikiSS5YdE+2lMB0GA1UdDgQWBBSo8wP0oJQPM/dDxopIkkuWHRPtpTANBgkqhkiG\n\
9w0BAQsFAAOCAYEAUxPIP2alvNIhp3R84u00l526AJ0+n7C4GmYgIJvwELyORj7S\n\
0EKCJC8/adA/nylgh3T0ZKdY5pu5LO1H7P68bV01X2KGdCGGdfX/CQL5cmlmGlsH\n\
gicPgvrtfuS/jjdBuoMskmWmecz/YbNhqlFtzQmHTgdstx2pW8egiPeAclKENUvd\n\
2NLG6fIPr9eIHcfMe9FLes2Ex4hxnpHXNKHrq+sx7Uc2PfVDXla47bBnd86P3rlS\n\
HmXRClS8Byn69Vr0fdGlBsQWH77yjSDJvxN1B3WmydmZ6lUz4zepFKdhyyASonL1\n\
1lnq1fVJhgzBp64dKvtXzAmaXar/lcEDRcIdbZbwNeLv/FxPstMmsfCvhlXHsPyB\n\
W1F0ajW1+Ti8ybgI1Q0GskTm0XNN0uM7aotdi3+VK9/+JCKQuR23HvE6velcGtN3\n\
2a8F/14AP1mfHykbxk2/+kXQsg9GB6ptpIYrv2Up2GDJvX/JH9DH1swzm63dpjUg\n\
igSPeiIq+u96U7K8\n-----END CERTIFICATE-----\n"

        # Place CA certificate in an encrypted directory
        ca_path = "/opt/fortanix/enclave-os/app-config/rw/cacert.pem"
        ca_cert_info = json.dumps({"ca_certificates" : [
            {
                "caPath" : ca_path,
                "caCert" : ca_cert,
                "system" : "false"
            }
        ]})

        # Test that a non root user can access ca cert from an encrypted directory
        container = self.container('zapps/ubuntu', image_version='2021080415-d0612f8',
                                   memsize='1G', rw_dirs=rw_dirs,
                                   entrypoint=['/test/entrypoint.py'], user='testuser',
                                   ca_certificates=ca_cert_info)
        container.prepare()
        container.copy_file('entrypoint.py', '/test')
        container.run()
        container.wait()
        return True

if __name__ == '__main__':
    test_app.main(AppcertPermissions)
