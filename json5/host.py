# Copyright 2014 Google Inc. All rights reserved.
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

import fileinput
import os
import shutil
import sys
import tempfile


class Host(object):
    def __init__(self):
        self.stdout = sys.stdout

    def chdir(self, *comps):
        return os.chdir(self.join(*comps))

    def fileinput(self, files=None):
        return fileinput.input(files)

    def getcwd(self):
        return os.getcwd()

    def join(self, *comps):
        return os.path.join(*comps)

    def mkdtemp(self, **kwargs):
        return tempfile.mkdtemp(**kwargs)

    def print_(self, msg=u'', end=u'\n', stream=None):
        stream = stream or self.stdout
        stream.write(unicode(msg) + end)
        stream.flush()

    def rmtree(self, path):
        shutil.rmtree(path, ignore_errors=True)

    def write_text_file(self, path, contents):
        with open(path, 'w') as f:
            f.write(contents.encode('utf8'))
