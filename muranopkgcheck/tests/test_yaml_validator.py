#    Copyright (c) 2016 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock
import unittest

from muranopkgcheck.validators import base


class YamlValidatorTest(unittest.TestCase):
    def setUp(self):
        self.pkg = mock.Mock()
        self.pkg.search_for.return_value = ['sth']
        self.fmock = mock.Mock()
        self.document = mock.Mock()
        self.pkg.read.return_value = self.fmock
        self.v = base.YamlValidator(self.pkg, '***')

    def test_checker_with_ast(self):
        c = mock.Mock()
        c.return_value = 'ok'
        self.fmock.yaml.return_value = [{}]
        self.v.add_checker(c)
        self.v.run()
        c.assert_called_once_with({})
        self.pkg.search_for.assert_called_once_with('***')

    def test_run_single_with_key_checker(self):
        c = mock.Mock()
        c.return_value = 'ok'
        self.fmock.yaml.return_value = [{'key': 'whatever'}]
        self.v.add_checker(c, 'key')
        self.v.run()
        c.assert_called_once_with('whatever')
        self.pkg.search_for.assert_called_once_with('***')

    def test_two_keys_unknown_key(self):
        c = mock.Mock()
        c.return_value = None
        self.fmock.yaml.return_value = [{'key': 'whatever',
                                         'unknown': ''}]
        self.v.add_checker(c, 'key')
        errors = self.v.run()
        c.assert_called_once_with('whatever')
        self.pkg.search_for.assert_called_once_with('***')
        self.assertIn('Unknown keyword "unknown"', next(errors).message)

    def test_missing_required_key(self):
        c = mock.Mock()
        self.fmock.yaml.return_value = [{}]
        self.v.add_checker(c, 'key')
        errors = self.v.run()
        self.pkg.search_for.assert_called_once_with('***')
        self.assertIn('Missing required key "key"', next(errors).message)
