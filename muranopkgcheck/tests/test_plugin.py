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

from muranopkgcheck import manager
from muranopkgcheck import plugin
from muranopkgcheck.tests import test_validator_helpers as helpers
from muranopkgcheck import validators


class FakePlugin(plugin.Plugin):

    def validators(self):
        pass

    def errors(self):
        pass


class PluginTest(helpers.BaseValidatorTestClass):

    def test_plugin(self):
        fake = FakePlugin()
        self.assertIsNotNone(fake)

    @mock.patch('muranopkgcheck.manager.pkg_loader')
    @mock.patch('muranopkgcheck.manager.stevedore')
    def test_load_plugins(self, m_stevedore, m_pkg_loader):
        fake_validator = mock.Mock()
        fake_plugin = mock.Mock()
        fake_plugin.obj.validators.return_value = [fake_validator]
        m_stevedore.ExtensionManager.return_value = [fake_plugin]
        fake_manager = manager.Manager('fake')
        m_pkg_loader.load_package.assert_called_once_with('fake', quiet=False)
        fake_manager.load_plugins()
        m_stevedore.ExtensionManager.assert_called()
        self.assertEqual(validators.VALIDATORS + [fake_validator],
                         fake_manager.validators)

        m_stevedore.ExtensionManager.reset_mock()
        fake_manager.load_plugins()
        m_stevedore.ExtensionManager.assert_not_called()
