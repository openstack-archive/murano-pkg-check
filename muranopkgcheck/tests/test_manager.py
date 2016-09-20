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

from muranopkgcheck import error
from muranopkgcheck import manager
from muranopkgcheck.tests import base


class PlainTextFormatterTest(base.TestCase):

    def test_format(self):

        class FakeYamlMeta(object):

            def __init__(self):
                self.line = 0
                self.column = 0
                self.name = 'fake'

            def get_snippet(self):
                return 'fake'

        class FakeYamlNode(str):

            def __init__(self, value):
                super(FakeYamlNode, self).__init__()
                self.value = value
                self.__yaml_meta__ = FakeYamlMeta()

        formatter = manager.PlainTextFormatter()
        fake_yaml_node = FakeYamlNode('Fake!!!')
        errors = [error.report.E042('Fake!!!', fake_yaml_node)]
        self.assertEqual('fake:1:1: E042 Fake!!!', formatter.format(errors))


class ManagerTest(base.TestCase):

    def _assert_errors(self, expected, actual):
        expected_errors = list(expected)
        for e in actual:
            if e in expected_errors:
                expected_errors.remove(e)
            else:
                self.fail('Unexpected error {}'.format(e))
        self.assertEqual([], expected_errors, 'Expected errors left')

    @mock.patch('muranopkgcheck.manager.pkg_loader')
    @mock.patch('muranopkgcheck.manager.error.report')
    def test_validate(self, m_error, m_pkg_loader):
        fake_error = error.CheckError('W007', 'Fake')
        m_error.W007.return_value = fake_error
        fake_E000_error = error.CheckError('E000', 'Fake')
        m_error.E000.return_value = fake_E000_error

        def error_generator():
            yield fake_error

        def broken_checker():
            a = 0
            if 1 / a:
                yield fake_error

        def broken_method_checker(self):
            a = 0
            if 1 / a:
                yield fake_error

        mgr = manager.Manager('fake')
        m_pkg_loader.load_package.assert_called_once_with('fake', quiet=False)
        MockValidator = mock.Mock()
        m_validator = MockValidator.return_value

        def prepare_errors():
            return iter((fake_error, error_generator(), broken_checker(),
                         broken_method_checker(m_validator)))

        m_validator.run.return_value = prepare_errors()
        errors = mgr.validate(validators=[MockValidator])
        self._assert_errors(
            [fake_E000_error, fake_E000_error, fake_error, fake_error],
            errors)

        m_validator.run.return_value = prepare_errors()
        errors = mgr.validate(validators=[MockValidator], only_errors=True)
        self._assert_errors([fake_E000_error, fake_E000_error], errors)

        m_validator.run.return_value = prepare_errors()
        errors = mgr.validate(validators=[MockValidator], select=['W007'])
        self._assert_errors([fake_error, fake_error], errors)

        m_validator.run.return_value = prepare_errors()
        errors = mgr.validate(validators=[MockValidator], ignore=['E000'])
        self._assert_errors([fake_error, fake_error], errors)
