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
from muranopkgcheck.validators import base


SUPPORTED_FORMATS = frozenset(['1.0', '1.1', '1.2', '1.3', '1.4'])
METHOD_KEYWORDS = frozenset(['Body', 'Arguments', 'Usage', 'Scope', 'Meta'])
METHOD_ARGUMENTS_KEYWORDS = frozenset(['Contract', 'Usage', 'Meta'])
PROPERTIES_KEYWORDS = frozenset(['Contract', 'Usage', 'Default', 'Meta'])
PROPERTIES_USAGE_VALUES = frozenset(['In', 'Out', 'InOut', 'Const', 'Static',
                                     'Runtime', 'Config'])
CLASSNAME_REGEX = re.compile('^[A-Za-z_]\w*$')
METHOD_NAME_REGEX = re.compile('^[A-Za-z_\.][\w]*$')


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
            yield error.report.E025('Wrong namespace of import "{0}"'
                                    .format(import_), import_)

    def _valid_name(self, value):
        if value.startswith('__') or \
           not CLASSNAME_REGEX.match(value):
            yield error.report.E011('Invalid class name "{0}"'.format(value),
                                    value)
        elif not (value != value.lower() and value != value.upper()):
            yield error.report.W011('Invalid class name "{0}"'.format(value),
                                    value)

    def _valid_extends(self, value, can_be_list=True):
        if can_be_list and isinstance(value, list):
            for cls in value:
                yield self._valid_extends(cls, False)
        elif isinstance(value, six.string_types):
            if not self._check_ns_fqn_name(value):
                yield error.report.E025('Wrong FNQ of extended class "{0}"'
                                        .format(value), value)
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
                yield error.report.W048('Contract is not valid yaql "{0}"'
                                        .format(contract), contract)
        else:
            yield error.report.W048('Contract is not valid yaql "{0}"'
                                    .format(contract), contract)

    def _valid_properties(self, properties):
        if not isinstance(properties, dict):
            yield error.report.E026('Properties should be a dict', properties)
            return
        for property_name, property_data in six.iteritems(properties):
            usage = property_data.get('Usage')
            if usage:
                if usage not in PROPERTIES_USAGE_VALUES:
                    yield error.report.E042('Not allowed usage '
                                            '"{0}"'.format(usage),
                                            usage)
            contract = property_data.get('Contract')
            if contract is not None:
                yield self._valid_contract(contract)
            else:
                yield error.report.E047('Missing Contract in property "{0}"'
                                        .format(property_name), property_name)
            yield self._valid_keywords(property_data.keys(),
                                       PROPERTIES_KEYWORDS)

    def _valid_namespaces(self, value):
        if not isinstance(value, dict):
            yield error.report.E044('Wrong type of namespace', value)
            return

        for name, fqn in six.iteritems(value):
            if not self._check_fqn_name(fqn):
                yield error.report.E060('Wrong namespace fqn "{0}"'
                                        .format(fqn), fqn)
            if not self._check_name(name) and name != '=':
                yield error.report.E060('Wrong name for namespace '
                                        '"{0}"'.format(fqn), fqn)

    def _valid_methods(self, value):
        for method_name, method_data in six.iteritems(value):
            if not isinstance(method_data, dict):
                if method_data:
                    yield error.report.E046('Method is not a dict',
                                            method_name)
                return
            if not METHOD_NAME_REGEX.match(method_name):
                yield error.report.E054('Invalid name of method "{0}"'
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
            yield error.report.E045('Body is not a list or scalar/yaql '
                                    'expression', body)
        else:
            yield self.code_structure.codeblock(body)

    def _valid_scope(self, scope):
        if self._loaded_pkg.format_version >= '1.4':
            if scope is not None and scope not in ('Public', 'Session'):
                yield error.report.E044('Wrong Scope "{0}"'.format(scope),
                                        scope)
        else:
            yield error.report.E044('Scope is not supported version '
                                    'earlier than 1.3"', scope)

    def _valid_method_usage(self, usage):
        if usage == 'Action':
            if self._loaded_pkg.format_version >= '1.4':
                yield error.report.W045('Usage "{0}" is deprecated since 1.4'
                                        .format(usage), usage)
        elif usage in frozenset(['Static', 'Extension']):
            if self._loaded_pkg.format_version <= '1.3':
                yield error.report.W045('Usage "{0}" is available from 1.3'
                                        .format(usage), usage)
        elif usage != 'Runtime':
            yield error.report.W045('Unsupported usage type "{0}" '
                                    .format(usage), usage)

    def _valid_arguments(self, arguments):
        if not isinstance(arguments, list):
            yield error.report.E046('Methods arguments should be a list',
                                    arguments)
            return
        for argument in arguments:
            if not isinstance(argument, dict) or len(argument) != 1:
                yield error.report.E046('Methods single argument should be a '
                                        'one key dict', argument)
            else:
                name = next(six.iterkeys(argument))
                if not self._check_name(name):
                    yield error.report.E054('Invalid name of argument "{0}"'
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
            yield error.report.E052('Arguments usage is available since 1.4 ',
                                    usage)
        if usage not in frozenset(['Standard', 'VarArgs', 'KwArgs']):
            yield error.report.E053('Usage is invalid value "{0}"'
                                    .format(usage), usage)
