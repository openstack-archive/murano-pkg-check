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

import abc
import itertools
import re

import six

from muranopkgcheck import error
from muranopkgcheck.i18n import _

FQN_REGEX = re.compile('^([a-zA-Z_$][\w$]*\.)*[a-zA-Z_$][\w$]*$')
NAME_REGEX = re.compile('^[A-Za-z_][\w]*$')

error.register.E002(description='Yaml Error')
error.register.E005(description='YAML multi document is not allowed')
error.register.E020(description='Missing required key')
error.register.E021(description='Unknown keyword')
error.register.E040(description='Value should be string')
error.register.W010(description='Unknown keyword')


@six.add_metaclass(abc.ABCMeta)
class BaseValidator(object):

    def __init__(self, loaded_package, _filter='.*'):
        self._loaded_pkg = loaded_package
        self._filter = _filter

    @abc.abstractmethod
    def run(self):
        pass

    def _valid_string(self, value):
        if not isinstance(value, six.string_types):
            yield error.report.E040(_('Value is not a string "{}"'
                                      '').format(value), value)

    def _check_name(self, name):
        if isinstance(name, six.string_types) and NAME_REGEX.match(name):
            return True
        return False

    def _check_fqn_name(self, fqn):
        if isinstance(fqn, six.string_types) and FQN_REGEX.match(fqn):
            return True
        return False

    def _check_ns_fqn_name(self, ns_fqn):
        if isinstance(ns_fqn, six.string_types):
            if ':' in ns_fqn:
                ns, fqn = ns_fqn.split(':', 1)
                if NAME_REGEX.match(ns) and FQN_REGEX.match(fqn):
                    return True
            elif FQN_REGEX.match(ns_fqn):
                return True
        return False


class YamlValidator(BaseValidator):
    def __init__(self, loaded_package, _filter='.*', allows_multi=False):
        super(YamlValidator, self).__init__(loaded_package, _filter)
        self._checkers = {}
        self._allows_multi = allows_multi

    def add_checker(self, function, key=None, required=True):
        checkers = self._checkers.setdefault(key, {'checkers': [],
                                                   'required': False})
        checkers['checkers'].append(function)
        if key is None:
            checkers['required'] = False
        elif required:
            checkers['required'] = True

    def run(self):
        chain_of_suits = []
        for filename in self._loaded_pkg.search_for(self._filter):
            file_ = self._loaded_pkg.read(filename)
            chain_of_suits.append(self._run_single(file_))
        return itertools.chain(*chain_of_suits)

    def _run_single(self, file_):
        reports_chain = []

        def run_helper(name, checkers, data):
            for checker in checkers:
                result = checker(data)
                if result:
                    reports_chain.append(result)

        try:
            multi_documents = file_.yaml()
        except Exception as e:
            reports_chain.append([
                error.report.E002('Yaml Error: {0}'.format(e), e)])
        else:
            if multi_documents is None:
                multi_documents = [{}]

            if len(multi_documents) > 1 and not self._allows_multi:
                reports_chain.append([
                    error.report.E005(_('Multi document is not allowed in {}')
                                      .format(file_._path))])

            for ast in multi_documents:
                file_check = self._checkers.get(None)
                if file_check:
                    run_helper(None, file_check['checkers'], ast)
                for key, value in six.iteritems(ast):
                    checkers = self._checkers.get(key)
                    if checkers:
                        run_helper(key, checkers['checkers'], ast[key])
                    else:
                        reports_chain.append(self._unknown_keyword(key, value))
                missing = set(key for key, value in
                              six.iteritems(self._checkers)
                              if value['required']) - set(ast.keys())
                for m in missing:
                    reports_chain.append([
                        error.report.E020(_('Missing required key "{}"')
                                          .format(m), m)])

        return itertools.chain(*reports_chain)

    def _valid_keywords(self, present, known):
        unknown = set(present) - set(known)
        for u in unknown:
            yield error.report.E021(_('Unknown keyword "{}"').format(u), u)

    def _unknown_keyword(self, key, value):
        yield error.report.W010(_('Unknown keyword "{}"').format(key), key)

    def _null_checker(self, value):
        pass
