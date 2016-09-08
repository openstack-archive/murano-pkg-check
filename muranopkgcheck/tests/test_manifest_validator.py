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

from muranopkgcheck.tests import test_validator_helpers as helpers
from muranopkgcheck.validators import manifest
from muranopkgcheck import yaml_loader


class ManifestValidatorTests(helpers.BaseValidatorTestClass):
    def setUp(self):
        super(ManifestValidatorTests, self).setUp()
        self._oe_patcher = mock.patch('os.path.exists')
        self.exists = self._oe_patcher.start()
        self.exists.return_value = [True, True]
        self.loaded_package = mock.MagicMock()
        # self.loaded_package = mock.Mock()
        # self.loaded_package.read.return_value.yaml.return_value = [
        #     {'Type': 'Application'}]
        self.mv = manifest.ManifestValidator(self.loaded_package)

    def test_format_as_number(self):
        self.g = self.mv._valid_format(1.3)

    def test_description(self):
        self.g = self.mv._valid_description(yaml_loader.YamlNull())

    def test_description_string(self):
        self.g = self.mv._valid_description("lalal")

    def test_description_number(self):
        self.g = self.mv._valid_description(1.3)
        self.assertIn('Value is not valid string "1.3"',
                      next(self.g).message)

    def test_wrong_format(self):
        self.g = self.mv._valid_format('0.9')
        self.assertIn('Not supported format version "0.9"',
                      next(self.g).message)

    def test_valid_string(self):
        self.g = self.mv._valid_string([])
        self.assertIn('Value is not a string "[]"',
                      next(self.g).message)

    def test_heat_format(self):
        self.g = self.mv._valid_format('Heat/1.0')
        self.assertIn('Not supported format "Heat/1.0"',
                      next(self.g).message)

    def test_heat_format_invalid_version_also(self):
        self.g = self.mv._valid_format('Heat/0.1.0')
        self.assertIn('Not supported format "Heat/0.1.0"',
                      next(self.g).message)

    def test_unsupported_format(self):
        self.g = self.mv._valid_format('Heat.HOT')
        self.assertIn('Not supported format version "Heat.HOT"',
                      next(self.g).message)

    def test_type(self):
        self.g = self.mv._valid_type('Application')

    def test_wrong_type(self):
        self.g = self.mv._valid_type('Shared Library')
        self.assertIn('Type is invalid "Shared Library"', next(self.g).message)

    def test_incorrect_package_version(self):
        self.g = self.mv._valid_version('a1.3')
        self.assertIn('Version format should be compatible with SemVer '
                      'not "a1.3"', next(self.g).message)

    def test_wrong_require_type(self):
        self.g = self.mv._valid_require([1, 2, 3])
        self.assertIn('Require is not a dict type', next(self.g).message)

    def test_wrong_require_fqn(self):
        self.g = self.mv._valid_require({'io.murano!': '1.3.2'})
        self.assertIn('Require key is not valid FQN "io.murano!"',
                      next(self.g).message)

    def test_require(self):
        self.g = self.mv._valid_require({'aaa.bbb': '>= 1.0.0'})

    def test_not_existing_file(self):
        data = {'org.openstack.Flow': 'FlowClassifier.yaml',
                'org.openstack.Instance': 'Instance.yaml'}
        self.loaded_package.search_for.return_value = ['FlowClassifier.yaml']
        self.g = self.mv._valid_classes(data)
        self.assertIn('File "Instance.yaml" is present in Manifest, '
                      'but not in filesystem', next(self.g).message)

    def test_extra_file_in_directory(self):
        data = {'org.openstack.Instance': 'Instance.yaml'}
        self.loaded_package.search_for.return_value = ['FlowClassifier.yaml',
                                                       'Instance.yaml']
        self.g = self.mv._valid_classes(data)
        self.assertIn('File "FlowClassifier.yaml" is not present in Manifest, '
                      'but it is in filesystem', next(self.g).message)

    def test_classess_list(self):
        data = [{'org.openstack.Instance': 'Instance.yaml'}]
        self.loaded_package.search_for.return_value = ['FlowClassifier.yaml',
                                                       'Instance.yaml']
        self.g = self.mv._valid_classes(data)
        self.assertIn('Classes section should be a dict', next(self.g).message)

    def test_missing_ui_file(self):
        self.loaded_package.exists.return_value = False
        self.g = self.mv._valid_ui('ui.yaml')
        self.assertIn('There is no UI file "ui.yaml"',
                      next(self.g).message)

    def test_missing_logo_file(self):
        self.loaded_package.exists.return_value = False
        self.g = self.mv._valid_logo('logo.png')
        self.assertIn('There is no Logo file "logo.png"',
                      next(self.g).message)

    def test_wrong_logo_type(self):
        self.g = self.mv._valid_logo([1, 2, 3])
        self.assertIn('Logo is not a string', next(self.g).message)

    def test_wrong_ui_type(self):
        self.g = self.mv._valid_ui([1, 2, 3])
        self.assertIn('UI is not a string', next(self.g).message)

    def test_tags(self):
        self.g = self.mv._valid_tags(['whatever'])

    def test_tags_false(self):
        self.g = self.mv._valid_tags('whatever')
        self.assertIn('Tags should be a list', next(self.g).message)

    def test_logo_ui_existance(self):
        self.g = self.mv._valid_logo_ui_existance({'Logo': 0, 'UI': 0})

    def test_logo_ui_existance_false(self):
        self.loaded_package.exists.return_value = True
        self.g = self.mv._valid_logo_ui_existance({})

    def test_fullname_wrong(self):
        self.g = self.mv._valid_fullname('aaa.bbb.ccc#')
        self.assertIn('Invalid FullName "aaa.bbb.ccc#"', next(self.g).message)

    def test_fullname(self):
        self.g = self.mv._valid_fullname('invalid.fullname.!@#@')
        self.assertIn('Invalid FullName "invalid.fullname.!@#@"',
                      next(self.g).message)
