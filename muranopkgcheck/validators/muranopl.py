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

import re

import six

from muranopkgcheck.checkers import code_structure
from muranopkgcheck.checkers import yaql_checker
from muranopkgcheck import error
from muranopkgcheck.i18n import _
from muranopkgcheck.validators import base


SUPPORTED_FORMATS = frozenset(['1.0', '1.1', '1.2', '1.3', '1.4'])
METHOD_KEYWORDS = frozenset(['Body', 'Arguments', 'Usage', 'Scope', 'Meta'])
METHOD_ARGUMENTS_KEYWORDS = frozenset(['Contract', 'Usage', 'Meta'])
PROPERTIES_KEYWORDS = frozenset(['Contract', 'Usage', 'Default', 'Meta'])
PROPERTIES_USAGE_VALUES = frozenset(['In', 'Out', 'InOut', 'Const', 'Static',
                                     'Runtime', 'Config'])
CLASSNAME_REGEX = re.compile('^[A-Za-z_]\w*$')
METHOD_NAME_REGEX = re.compile('^[A-Za-z_\.][\w]*$')

error.register.E011(description='Invalid class name')
error.register.E025(description='Wrong namespace or FNQ of extended class')
error.register.E026(description='Properties should be a dict')
error.register.E042(description='Not allowed usage')
error.register.E044(description='Wrong type of namespace')
error.register.E045(description='Body is not a list or scalar/yaql expression')
error.register.E046(description='Method is not a dict')
error.register.E047(description='Missing Contract in property')
error.register.E052(description='Arguments usage is available since 1.4')
error.register.E053(description='Usage is invalid value ')
error.register.E054(description='Invalid name of method "{}"')
error.register.E060(description='Wrong namespace fqn')
error.register.W045(description='Unsupported usage type')
error.register.W011(description='Invalid class name')
error.register.W048(description='Contract is not valid yaql')


class MuranoPLValidator(base.YamlValidator):
    def __init__(self, loaded_package):
        super(MuranoPLValidator, self).__init__(loaded_package,
                                                'Classes/.*\.yaml$',
                                                True)
        self.yaql_checker = yaql_checker.YaqlChecker()
        self.code_structure = code_structure.CheckCodeStructure()

        self.add_checker(self._null_checker, 'Meta', False)
        self.add_checker(self._valid_name, 'Name', False)
        self.add_checker(self._valid_extends, 'Extends', False)
        self.add_checker(self._valid_methods, 'Methods', False)
        self.add_checker(self._valid_import, 'Import', False)
        self.add_checker(self._valid_namespaces, 'Namespaces', False)
        self.add_checker(self._valid_properties, 'Properties', False)

    def _valid_import(self, import_, can_be_list=True):
        if can_be_list and isinstance(import_, list):
            for imp in import_:
                yield self._valid_import(imp, False)
        elif not self._check_ns_fqn_name(import_):
            yield error.report.E025(_('Wrong namespace or FNQ of extended '
                                      'class "{0}"').format(import_), import_)

    def _valid_name(self, value):
        if value.startswith('__') or \
           not CLASSNAME_REGEX.match(value):
            yield error.report.E011(_('Invalid class name "{}"').format(value),
                                    value)
        elif not (value != value.lower() and value != value.upper()):
            yield error.report.W011(_('Invalid class name "{}"').format(value),
                                    value)

    def _valid_extends(self, value, can_be_list=True):
        if can_be_list and isinstance(value, list):
            for cls in value:
                yield self._valid_extends(cls, False)
        elif isinstance(value, six.string_types):
            if not self._check_ns_fqn_name(value):
                yield error.report.E025(_('Wrong FNQ of extended class "{}"'
                                          '').format(value), value)
        else:
            yield error.report.E025("Wrong type of Extends field", value)

    def _valid_contract(self, contract):
        if isinstance(contract, list):
            if len(contract) > 1:
                if len(contract) < 3:
                    if isinstance(contract[1], int):
                        return
                elif len(contract) < 4:
                    if isinstance(contract[1], int) and \
                            isinstance(contract[2], int):
                        return
                for con in contract:
                    yield self._valid_contract(con)
            elif len(contract) == 1:
                yield self._valid_contract(contract[0])
        elif isinstance(contract, dict):
            if not contract:
                return
            for c_key, c_value in six.iteritems(contract):
                yield self._valid_contract(c_key)
                yield self._valid_contract(c_value)
        elif isinstance(contract, six.string_types):
            if not self.yaql_checker(contract) or \
                    not contract.startswith('$.') and contract != '$':
                yield error.report.W048(_('Contract is not valid yaql "{}"'
                                          '').format(contract), contract)
        else:
            yield error.report.W048(_('Contract is not valid yaql "{}"'
                                      '').format(contract), contract)

    def _valid_properties(self, properties):
        if not isinstance(properties, dict):
            yield error.report.E026(_('Properties should be a dict'),
                                    properties)
            return
        for property_name, property_data in six.iteritems(properties):
            usage = property_data.get('Usage')
            if usage:
                if usage not in PROPERTIES_USAGE_VALUES:
                    yield error.report.E042(_('Not allowed usage "{}"'
                                              '').format(usage), usage)
            contract = property_data.get('Contract')
            if contract is not None:
                yield self._valid_contract(contract)
            else:
                yield error.report.E047(_('Missing Contract in property "{}"')
                                        .format(property_name), property_name)
            yield self._valid_keywords(property_data.keys(),
                                       PROPERTIES_KEYWORDS)

    def _valid_namespaces(self, value):
        if not isinstance(value, dict):
            yield error.report.E044(_('Wrong type of namespace'), value)
            return

        for name, fqn in six.iteritems(value):
            if not self._check_fqn_name(fqn):
                yield error.report.E060(_('Wrong namespace fqn '
                                          '"{}"').format(fqn), fqn)
            if not self._check_name(name) and name != '=':
                yield error.report.E060(_('Wrong name for namespace '
                                          '"{}"').format(fqn), fqn)

    def _valid_methods(self, value):
        for method_name, method_data in six.iteritems(value):
            if not isinstance(method_data, dict):
                if method_data:
                    yield error.report.E046(_('Method is not a dict'),
                                            method_name)
                return

            if not METHOD_NAME_REGEX.match(method_name):
                yield error.report.E054(_('Invalid name of method "{}"')
                                        .format(method_name), method_name)
            scope = method_data.get('Scope')
            if scope:
                yield self._valid_scope(scope)
            usage = method_data.get('Usage')
            if usage:
                yield self._valid_method_usage(usage)
            arguments = method_data.get('Arguments')
            if arguments:
                yield self._valid_arguments(arguments)
            body = method_data.get('Body')
            if body:
                yield self._valid_body(body)
            yield self._valid_keywords(method_data.keys(), METHOD_KEYWORDS)

    def _valid_body(self, body):
        if not isinstance(body, (list, six.string_types, dict)):
            yield error.report.E045(_('Body is not a list or scalar/yaql '
                                    'expression'), body)
        else:
            yield self.code_structure.codeblock(body)

    def _valid_scope(self, scope):
        if self._loaded_pkg.format_version >= '1.4':
            if scope is not None and scope not in ('Public', 'Session'):
                yield error.report.E044(_('Wrong Scope "{}"').format(scope),
                                        scope)
        else:
            yield error.report.E044(_('Scope is not supported version '
                                    'earlier than 1.3"'), scope)

    def _valid_method_usage(self, usage):
        if usage == 'Action':
            if self._loaded_pkg.format_version >= '1.4':
                yield error.report.W045(_('Usage "{}" is deprecated since 1.4'
                                          '').format(usage), usage)
        elif usage in frozenset(['Static', 'Extension']):
            if self._loaded_pkg.format_version <= '1.3':
                yield error.report.W045(_('Usage "{}" is available from 1.3')
                                        .format(usage), usage)
        elif usage != 'Runtime':
            yield error.report.W045(_('Unsupported usage type "{}" ')
                                    .format(usage), usage)

    def _valid_arguments(self, arguments):
        if not isinstance(arguments, list):
            yield error.report.E046(_('Methods arguments should be a list'),
                                    arguments)
            return
        for argument in arguments:
            if not isinstance(argument, dict) or len(argument) != 1:
                yield error.report.E046(_('Methods single argument should be '
                                          'a one key dict'), argument)
            else:
                name = next(six.iterkeys(argument))
                if not self._check_name(name):
                    yield error.report.E054(_('Invalid name of argument "{}"')
                                            .format(name), name)
                val = next(six.itervalues(argument))
                contract = val.get('Contract')
                if contract:
                    yield self._valid_contract(contract)
                usage = val.get('Usage')
                if usage:
                    yield self._valid_argument_usage(usage)
                yield self._valid_keywords(val, METHOD_ARGUMENTS_KEYWORDS)

    def _valid_argument_usage(self, usage):
        if self._loaded_pkg.format_version < '1.4':
            yield error.report.E052(_('Arguments usage is available '
                                      'since 1.4'), usage)
        if usage not in frozenset(['Standard', 'VarArgs', 'KwArgs']):
            yield error.report.E053(_('Usage is invalid value "{}"')
                                    .format(usage), usage)
