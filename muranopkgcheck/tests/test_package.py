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
from muranopkgcheck.validators import package


class PackageValidatorTests(helpers.BaseValidatorTestClass):
    def setUp(self):
        super(PackageValidatorTests, self).setUp()
        self.loaded_package = mock.Mock()
        self.pv = package.PackageValidator(self.loaded_package)

    def test_known_files(self):
        self.loaded_package.search_for.return_value = [
            'manifest.yaml', 'LICENSE', 'logo']
        self.g = self.pv.run()
        self.assertIn('Unknown "logo" in the package',
                      next(self.g).message)

    def test_known_files_missing_req(self):
        self.loaded_package.search_for.return_value = [
            'manifest.yaml', 'logo.png']
        self.g = self.pv.run()
        self.assertIn('Missing "LICENSE" in the package',
                      next(self.g).message)
