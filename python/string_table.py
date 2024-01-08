#
# String table access. This module loads the generated build-specific string
# table, and makes the symbols available via this module. The generated
# string table is found relative to the path in the ENCLAVEOS_RUNTIME
# environment variable. We try to provide error messages indicating what
# is wrong when things don't work out.
#

import os
import sys

if 'ENCLAVEOS_RUNTIME' in os.environ:
    # TODO: this is only correct for build trees. when installed,
    # string_table.py must be placed in the same directory as any
    # installed python scripts.
    sys.path.append(os.path.join(os.environ['ENCLAVEOS_RUNTIME'], '..', 'codegen', 'python'))

try:
    from generated_string_table import *
except ImportError as e:
    raise RuntimeError('''Unable to import generated string table. Maybe your ENCLAVEOS_RUNTIME
environment variable is not correct, or the string table has not been built?''')
