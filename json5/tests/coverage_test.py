# Copyright 2014 Dirk Pranke. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from io import StringIO

from json5 import main
from json5.tests import main_test
from json5.host import Host


class CoverageTestMixin(object):
    def _host(self):
        return Host()

    def _call(self, host, args, stdin=None,
              returncode=None, out=None, err=None):
        if stdin:
          host.stdin = StringIO(unicode(stdin))
        else:
          host.stdin = StringIO()
        host.stdout = StringIO()
        host.stderr = StringIO()
        actual_ret = main(args, host)
        actual_out = host.stdout.getvalue()
        actual_err = host.stderr.getvalue()
        if returncode is not None:
            self.assertEqual(returncode, actual_ret)
        if out is not None:
            self.assertEqual(out, actual_out)
        if err is not None:
            self.assertEqual(err, actual_err)
        return actual_ret, actual_out, actual_err


class CoverageTestMain(CoverageTestMixin, main_test.MainTest):
    pass
