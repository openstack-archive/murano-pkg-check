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


import os.path

import semantic_version
import six

from muranopkgcheck import consts
from muranopkgcheck import error
from muranopkgcheck.i18n import _
from muranopkgcheck.validators import base
from muranopkgcheck import yaml_loader

error.register.E030(description='Not supported format')
error.register.E050(description='File is present in Manifest, '
                                'but not in filesystem')
error.register.E070(description='Tags should be a list')
error.register.E071(description='Type is invalid')
error.register.E072(description='UI is not a string')
error.register.E073(description='Invalid FullName')
error.register.E074(description='Logo is not a string')
error.register.W020(description='File is not present in Manifest, '
                                'but it is in filesystem')
error.register.W030(description='Not supported format version')
error.register.W073(description='There is no UI file')
error.register.W074(description='There is no Logo file')


class ManifestValidator(base.YamlValidator):
    def __init__(self, loaded_package):
        super(ManifestValidator, self).__init__(loaded_package,
                                                'manifest.yaml$')
        self.add_checker(self._valid_format, 'Format', False)
        self.add_checker(self._valid_string, 'Author', False)
        self.add_checker(self._valid_version, 'Version', False)
        self.add_checker(self._valid_fullname, 'FullName')
        self.add_checker(self._valid_string, 'Name', False)
        self.add_checker(self._valid_classes, 'Classes', False)
        self.add_checker(self._valid_tags, 'Tags', False)
        self.add_checker(self._valid_require, 'Require', False)
        self.add_checker(self._valid_type, 'Type')
        self.add_checker(self._valid_description, 'Description')
        self.add_checker(self._valid_ui, 'UI', False)
        self.add_checker(self._valid_logo, 'Logo', False)
        self.add_checker(self._valid_logo_ui_existance)

    def _valid_description(self, desc):
        if not isinstance(desc, six.string_types) and\
                not isinstance(desc, yaml_loader.YamlNull):
            yield error.report.E030('Value is not valid string "{0}"'
                                    .format(desc), desc)

    def _valid_format(self, value):
        format_ = str(value).split('/', 1)
        if len(format_) > 1:
            if format_[0] != 'MuranoPL':
                yield error.report.W030(_('Not supported format "{}"'
                                          '').format(value), value)
                return
        ver = format_[-1]
        if str(ver) not in ['1.0', '1.1', '1.2', '1.3', '1.4']:
            yield error.report.W030(_('Not supported format version "{}"'
                                      '').format(value), value)

    def _valid_fullname(self, fullname):
        if not self._check_fqn_name(fullname):
            yield error.report.E073(_('Invalid FullName "{}"')
                                    .format(fullname), fullname)

    def _valid_tags(self, value):
        if not isinstance(value, list):
            yield error.report.E070(_('Tags should be a list'), value)

    def _valid_require(self, value):
        if not isinstance(value, dict):
            yield error.report.E005(_('Require is not a dict type'), value)
            return
        for fqn, ver in six.iteritems(value):
            if not self._check_fqn_name(fqn):
                yield error.report.E005(_('Require key is not valid FQN "{}"'
                                          '').format(fqn), fqn)

    def _valid_type(self, value):
        if value not in ('Application', 'Library'):
            yield error.report.E071(_('Type is invalid "{}"').format(value),
                                    value)

    def _valid_version(self, version):
        try:
            semantic_version.Version.coerce(str(version))
        except ValueError:
            yield error.report.E071(_('Version format should be compatible '
                                      'with SemVer not "{}"'
                                      '').format(version), version)

    def _valid_logo_ui_existance(self, ast):
        if 'Logo' not in ast:
            yield self._valid_logo('logo.png')
        if 'UI' not in ast:
            yield self._valid_ui('ui.yaml')

    def _valid_ui(self, value):
        if isinstance(value, six.string_types):
            pkg_type = self._loaded_pkg.read(
                consts.MANIFEST_PATH).yaml()[0]['Type']
            if pkg_type == 'Library':
                return
            if not self._loaded_pkg.exists(os.path.join('UI', value)):
                yield error.report.W073(_('There is no UI file "{}"'
                                          '').format(value), value)
        else:
            yield error.report.E072(_('UI is not a string'), value)

    def _valid_logo(self, value):
        if isinstance(value, six.string_types):
            pkg_type = self._loaded_pkg.read(
                consts.MANIFEST_PATH).yaml()[0]['Type']
            if pkg_type == 'Library':
                return
            if not self._loaded_pkg.exists(value):
                yield error.report.W074(_('There is no Logo file "{}"'
                                          '').format(value), value)
        else:
            yield error.report.E074(_('Logo is not a string'), value)

    def _valid_classes(self, value):
        if not isinstance(value, dict):
            yield error.report.E074(_('Classes section should be a dict'),
                                    value)
            return

        files = set(value.values())
        existing_files = set(self._loaded_pkg.search_for('.*',
                                                         'Classes'))
        for fname in files - existing_files:
            yield error.report.E050(_('File "{}" is present in Manifest, '
                                      'but not in filesystem'
                                      '').format(fname), fname)
        for fname in existing_files - files:
            yield error.report.W020(_('File "{}" is not present in Manifest, '
                                      'but it is in filesystem'
                                      '').format(fname), fname)
