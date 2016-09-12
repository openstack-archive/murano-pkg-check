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
from muranopkgcheck.i18n import _
from muranopkgcheck.validators import base

UI_VERSION = frozenset(('1.0', '1', '2', '2.0', '2.1', '2.2', '2.3'))
FIELDS_TYPE = frozenset(('string', 'boolean', 'text', 'integer', 'password',
                         'clusterip', 'floatingip', 'domain', 'databaselist',
                         'table', 'flavor', 'keypair', 'image', 'azone',
                         'psqlDatabase', 'network', 'choice'))
BOOL_FIELDS = frozenset(('required', 'hidden'))
STR_FIELDS = frozenset(('name', 'label', 'description',
                        'descriptionTitle', 'regexpValidator', 'helpText'))
INT_FIELDS = frozenset(('minLength', 'maxLength', 'minValue', 'maxValue'))

error.register.E081(description='Value should be boolean')
error.register.E083(description='Wrong name in UI file')
error.register.E084(description='Application is not a dict')
error.register.E100(description='Not valid FQN or known type')
error.register.W082(description='Incorrect version of UI file')
error.register.W100(description='Not known type. Probably typo')


class UiValidator(base.YamlValidator):
    def __init__(self, loaded_package):
        super(UiValidator, self).__init__(loaded_package, 'UI/.*\.yaml$')
        self.add_checker(self._valid_forms, 'Forms', False)
        self.add_checker(self._null_checker, 'Templates', False)
        self.add_checker(self._valid_application, 'Application', False)
        self.add_checker(self._valid_version, 'Version', False)

    def _valid_application(self, application):
        if not isinstance(application, dict):
            yield error.report.E084(_('Application is not a dict'),
                                    application)
            return
        for name, value in six.iteritems(application):
            if not self._check_name(name):
                if name != '?':
                    yield error.report.E083(_('Wrong name in UI file "{}"')
                                            .format(name), name)

    def _valid_version(self, version):
        if str(version) not in UI_VERSION:
            yield error.report.W082(_('Incorrect version of UI file "{}"')
                                    .format(version), version)

    def _valid_forms(self, forms):
        for named_form in forms:
            for name, form in six.iteritems(named_form):
                yield self._valid_form(form['fields'])
                yield self._valid_keywords(form.keys(),
                                           ('fields', 'validators'))

    def _valid_form(self, form):
        for named_params in form:
            for key, value in six.iteritems(named_params):
                if key in STR_FIELDS:
                    if not isinstance(value, six.string_types):
                        yield error.report.E040(_('Value of {} should be '
                                                  'string not "{}"')
                                                .format(key, value), key)
                elif key in BOOL_FIELDS:
                    if not isinstance(value, bool):
                        yield error.report.E081(_('Value of {} should be '
                                                  'boolean not "{}"')
                                                .format(key, value), key)
                elif key in INT_FIELDS:
                    if not isinstance(value, int):
                        yield error.report.E082(_('Value of {} should be '
                                                  'int not "{}"')
                                                .format(key, value), key)
                elif key == 'type':
                    yield self._valid_field_type(value)

    def _valid_field_type(self, fqn, can_be_list=True):
        if isinstance(fqn, list):
            for elem in fqn:
                yield self._valid_field_type(elem, False)
        elif self._check_fqn_name(fqn):
            if '.' not in fqn and fqn not in FIELDS_TYPE:
                yield error.report.W100('"{0}" is not known type. '
                                        'Probably a typo'.format(fqn), fqn)
        else:
            yield error.report.E100('"{0}" is not valid FQN or known type'
                                    .format(fqn), fqn)
