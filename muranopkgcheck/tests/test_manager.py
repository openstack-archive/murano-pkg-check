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

        formater = manager.PlainTextFormatter()
        fake_yaml_node = FakeYamlNode('Fake!!!')

        errors = [error.report.E007('Fake!!!', fake_yaml_node)]
        self.assertEqual('fake:1:1: E007 Fake!!!', formater.format(errors))


class ManagerTest(base.TestCase):

    @mock.patch('muranopkgcheck.manager.pkg_loader')
    def test_validate(self, m_pkg_loader):
        fake_error = error.report.E007('Fake!')

        def error_generator():
            yield fake_error
        MockValidator = mock.Mock()
        m_validator = MockValidator.return_value
        m_validator.run.return_value = (e for e in [
            fake_error,
            error_generator()
        ])
        mgr = manager.Manager('fake')
        errors = mgr.validate(validators=[MockValidator])
        self.assertEqual([fake_error, fake_error], errors)
        m_pkg_loader.load_package.assert_called_once_with('fake')
