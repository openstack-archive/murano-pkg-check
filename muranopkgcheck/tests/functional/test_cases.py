#    Copyright (c) 2016 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import io
import os

import oslotest.base
import six
import testscenarios
import yaml

from muranopkgcheck import consts
from muranopkgcheck import manager
from muranopkgcheck import pkg_loader


class DictLoader(pkg_loader.BaseLoader):

    @classmethod
    def _try_load(cls, pkg):
        if consts.MANIFEST_PATH in pkg:
            return cls(pkg)
        return None

    def __init__(self, pkg):
        super(DictLoader, self).__init__('')
        self.pkg = pkg

    def open_file(self, path, mode='r'):
        if self.pkg[path]['format'] == 'raw':
            sio = io.BytesIO(six.b(self.pkg[path]['content']))
            setattr(sio, 'name', path)
        elif self.pkg[path]['format'] == 'yaml':
            content = yaml.safe_dump(self.pkg[path]['content'])
            sio = io.BytesIO(six.b(content))
            setattr(sio, 'name', path)
        else:
            raise ValueError('Unknown type of content')
        return sio

    def list_files(self, subdir=None):
        files = self.pkg.keys()
        if subdir is None:
            return files
        subdir_len = len(subdir)
        return [file_[subdir_len:].lstrip('/') for file_ in files
                if file_.startswith(subdir)]

    def exists(self, name):
        return name in self.pkg


class DictFormatter(manager.Formatter):

    def format(self, error):
        return sorted([{'code': e.code, 'msg': e.message} for e in error],
                      key=lambda item: item['code'])


def load_cases():
    cases_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'cases')
    cases_files = [os.path.join(cases_path, f)for f in os.listdir(cases_path)
                   if os.path.isfile(os.path.join(cases_path, f))]
    cases = []
    for cases_file in cases_files:
        with open(cases_file) as f:
            cases.extend(list(yaml.load_all(f)))
    return cases

cases = load_cases()


class TestCase(testscenarios.WithScenarios, oslotest.base.BaseTestCase):

    """Test case base class for all unit tests."""

    scenarios = cases

    def test_foo(self):
        m = manager.Manager(self.pkg, loader=DictLoader)
        errors = m.validate()
        fmt = DictFormatter()
        self.assertEqual(self.expected, fmt.format(errors))
