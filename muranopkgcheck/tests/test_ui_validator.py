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
from muranopkgcheck.validators import ui


class UiValidatorTest(helpers.BaseValidatorTestClass):
    def setUp(self):
        super(UiValidatorTest, self).setUp()
        self.package = mock.Mock()
        self.ui_validator = ui.UiValidator(self.package)

    def test_forms(self):
        forms = [
            {'name1': {
                'fields': [{
                    'name': 'whatever',
                    'type': 'integer',
                    'label': 'sth',
                    'description': 'something'
                }]}}]
        self.g = self.ui_validator._valid_forms(forms)

    def test_forms_required_bool(self):
        forms = [
            {'name1': {
                'fields': [{
                    'name': 'whatever',
                    'type': 'integer',
                    'label': 'sth',
                    'description': 'something',
                    'required': 2,
                }]}}]
        self.g = self.ui_validator._valid_forms(forms)
        self.assertIn('Value of', next(self.g).message)

    def test_forms_hidden_bool(self):
        forms = [
            {'name1': {
                'fields': [{
                    'name': 'whatever',
                    'type': 'integer',
                    'label': 'sth',
                    'description': 'something',
                    'hidden': 2,
                }]}}]
        self.g = self.ui_validator._valid_forms(forms)
        self.assertIn('Value of', next(self.g).message)

    def test_version(self):
        self.g = self.ui_validator._valid_version('0.9')
        self.assertIn('Incorrect version of UI file "0.9"',
                      next(self.g).message)

    def test_aplication_list(self):
        self.g = self.ui_validator._valid_application([])
        self.assertIn('Application is not a dict',
                      next(self.g).message)

    def test_aplication_wrong_name(self):
        self.g = self.ui_validator._valid_application({
            '??': 'fasdf.dfas.dfd'})
        self.assertIn('Wrong name in UI file "??"',
                      next(self.g).message)
