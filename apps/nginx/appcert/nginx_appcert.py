#!/usr/bin/python3
#
# Copyright (c) Fortanix, Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Nginx test using standard nginx container.


from test_nginx import test_nginx_appcert

if __name__ == '__main__' :
    test_nginx_appcert()
