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

import six

from muranopkgcheck import error
from muranopkgcheck.validators import base

UI_VERSION = frozenset(['1.0', '1', '2', '2.0', '2.1', '2.2', '2.3'])
FIELDS_TYPE = frozenset(['string', 'boolean', 'text', 'integer', 'password',
                         'clusterip', 'floatingip', 'domain', 'databaselist',
                         'table', 'flavor', 'keypair', 'image', 'azone',
                         'psqlDatabase', 'network'])


class UiValidator(base.YamlValidator):
    def __init__(self, loaded_package):
        super(UiValidator, self).__init__(loaded_package, 'UI/.*\.yaml$')
        self.add_checker(self._valid_forms, 'Forms', False)
        self.add_checker(self._null_checker, 'Templates', False)
        self.add_checker(self._valid_application, 'Application', False)
        self.add_checker(self._valid_version, 'Version', False)

    def _valid_application(self, application):
        if not isinstance(application, dict):
            yield error.report.E084('Application is not a dict', application)
            return
        for name, value in six.iteritems(application):
            if not self._check_name(name):
                if name != '?':
                    yield error.report.E083('Wrong name in UI file "{0}"'
                                            .format(name), name)

    def _valid_version(self, version):
        if str(version) not in UI_VERSION:
            yield error.report.W082('Incorrect version of UI file "{0}"'
                                    .format(version), version)

    def _valid_forms(self, forms):
        for named_form in forms:
            for name, form in six.iteritems(named_form):
                yield self._valid_form(form['fields'])
                yield self._valid_keywords(form.keys(), frozenset(['fields']))

    def _valid_form(self, form):
        for named_params in form:
            for key, value in six.iteritems(named_params):
                if key == 'required':
                    if not isinstance(value, bool):
                        yield error.report.E081('Value of {0} should be '
                                                'boolean not "{1}"'
                                                .format(key, value), key)
                elif key == 'hidden':
                    if not isinstance(value, bool):
                        yield error.report.E081('Value of {0} should be '
                                                'boolean "{1}"'
                                                .format(key, value), key)
                elif key in frozenset(['requirements', 'errorMessages',
                                       'choices', 'widgetMedia',
                                       'validators']):
                    pass
                elif key == 'type':
                    yield self._valid_field_type(value)
                else:
                    yield self._valid_string(value)

    def _valid_field_type(self, fqn, can_be_list=True):
        if isinstance(fqn, list):
            for elem in fqn:
                yield self._valid_field_type(elem, False)
        elif self._check_fqn_name(fqn):
            if '.' not in fqn and fqn not in FIELDS_TYPE:
                yield error.report.W100('"{0}" is not know type probably typo'
                                        .format(fqn), fqn)
        else:
            yield error.report.E100('"{0}" is not valid FQN or known type'
                                    .format(fqn), fqn)
