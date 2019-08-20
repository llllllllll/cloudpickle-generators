##############################################################################
# The function "pytest_ignore_collect" below is
# Copyright (c) 2016, Datadog <info@datadoghq.com>
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Datadog nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL DATADOG BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
##############################################################################
import os
import re
import sys
import pytest

import cloudpickle_generators

cloudpickle_generators.register()

PY_DIR_PATTERN = re.compile(r'^py[23][0-9]$')


@pytest.mark.hookwrapper
def pytest_ignore_collect(path, config):
    """
    Skip directories defining a required minimum Python version
    Example::
        File: tests/contrib/vertica/py35/test.py
        Python 2.7: Skip
        Python 3.4: Skip
        Python 3.5: Collect
        Python 3.6: Collect
    """

    # From https://github.com/DataDog/dd-trace-py/blob/
    # bd600cc7a8e582d0bae87fe2994b5471e2f1a49a/conftest.py

    outcome = yield

    # Was not ignored by default behavior
    if not outcome.get_result():
        # DEV: `path` is a `LocalPath`
        path = str(path)
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        dirname = os.path.basename(path)

        # Directory name match `py[23][0-9]`
        if PY_DIR_PATTERN.match(dirname):
            # Split out version numbers into a tuple: `py35` -> `(3, 5)`
            min_required = tuple((int(v) for v in dirname.strip('py')))

            # If the current Python version does not meet the minimum required,
            # skip this directory
            if sys.version_info[0:2] < min_required:
                outcome.force_result(True)
