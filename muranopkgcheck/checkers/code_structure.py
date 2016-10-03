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

from muranopkgcheck.checkers import yaql_checker
from muranopkgcheck import error


ASSIGMENT_KEY = re.compile('^\$.?[\w]')


def check_req(check, required=True):
    return locals()

error.register.E203(description='Value should be string type')
error.register.E200(description='No value should be here')
error.register.E204(description='Wrong code structure/assigment')
error.register.E202(description='Not a valid yaql expression')
error.register.W202(description='Not a valid yaql expression')
error.register.E201(description='Not a valid variable name')


CODE_STRUCTURE = {
    'Try': {
        'keywords': {
            'Try': check_req('codeblock'),
            'Catch': check_req('catchblock'),
            'Else': check_req('codeblock', False),
            'Finally': check_req('codeblock', False)}},
    'Parallel': {
        'keywords': {
            'Limit': check_req('codeblock', False),
            'Parallel': check_req('codeblock')},
    },
    'Repeat': {
        'keywords': {
            'Repeat': check_req('number'),
            'Do': check_req('codeblock')}},
    'If': {
        'keywords': {
            'If': check_req('predicate'),
            'Then': check_req('codeblock'),
            'Else': check_req('codeblock', False)}
    },
    'Break': {
        'keywords': {
            'Break': check_req('empty')}
    },
    'Return': {
        'Return': check_req('expression'),
    },
    'While': {
        'keywords': {
            'While': check_req('predicate'),
            'Do': check_req('codeblock')}
    },
    'For': {
        'keywords': {
            'For': check_req('string'),
            'In': check_req('expression'),
            'Do': check_req('codeblock')}
    },
    'Match': {
        'keywords': {
            'Match': check_req(('expression', 'codeblock')),
            'Value': check_req('expression'),
            'Default': check_req('codeblock', False),
        }
    },
    'Switch': {
        'keywords': {
            'Switch': check_req(('predicate', 'codeblock')),
            'Default': check_req('codeblock')}
    },
    'Throw': {
        'keywords': {
            'Throw': check_req('string'),
            'Message': check_req('string')}
    },
    'Continue': {
        'keywords': {
            'Continue': check_req('empty'),
        }
    },
    'Rethrow': {
        'keywords': {
            'Rethrow': check_req('empty'),
        }
    },
}


class CheckCodeStructure(object):
    def __init__(self):
        self._check_mappings = {
            'codeblock': self.codeblock,
            'catchblock': self.catchblock,
            'predicate': self.yaql,
            'empty': self.empty,
            'expression': self.yaql,
            'string': self.string,
            'number': self.yaql,
        }
        self._yaql_checker = yaql_checker.YaqlChecker()

    def string(self, value):
        if not isinstance(value, six.string_types):
            yield error.report.E203('Value of "{0}" should be a string'
                                    ''.format(value), value)

    def empty(self, value):
        if value:
            yield error.report.E200('Statement should be empty, not a '
                                    '"{0}"'.format(value), value)

    def yaql(self, value):
        if not self._yaql_checker(value):
            if isinstance(value, bool):
                return
            yield error.report.W202('"{0}" is not valid yaql expression'
                                    ''.format(value), value)

    def catchblock(self, catchblock):
        if isinstance(catchblock, list):
            for block in catchblock:
                yield self._single_catchblock(block)
        else:
            yield self._single_catchblock(catchblock)

    def _single_catchblock(self, catchblock):
        do = catchblock.get('Do')
        if not do:
            yield error.report.E204('Catch is missing "Do" block', catchblock)
        else:
            yield self.codeblock(do)
        yield self.string(catchblock.get('With', ''))
        yield self.string(catchblock.get('As', ''))

    def codeblock(self, codeblocks):
        if isinstance(codeblocks, list):
            for block in codeblocks:
                yield self._single_block(block)
        else:
            yield self._single_block(codeblocks)

    def _check_assigment(self, block):
        key = next(iter(block))
        if not isinstance(key, six.string_types) or\
                not ASSIGMENT_KEY.match(key):
            yield error.report.E201('"{0}" is not valid variable name'
                                    ''.format(key), key)

    def _single_block(self, block):
        if isinstance(block, dict):
            yield self._check_structure(block)
        elif isinstance(block, six.string_types):
            yield self.yaql(block)

    def _run_check(self, check, value):
        yield self._check_mappings[check](value)

    def _check_structure(self, block):
        for key, value in six.iteritems(CODE_STRUCTURE):
            if key in block:
                break
        else:
            if len(block.keys()) == 1:
                yield self._check_assigment(block)
            else:
                yield error.report.E204('Wrong code structure/assigment. '
                                        'Probably a typo', block)
            return

        keywords = value.get('keywords', {})
        kset = set(keywords.keys())
        block_keys_set = set(block.keys())
        for missing in (kset - block_keys_set):
            if keywords[missing]['required']:
                yield error.report.E204('Missing keyword "{0}" for "{1}" '
                                        'code structure'
                                        .format(missing, key), block)
        for unknown in (block_keys_set - kset - {key}):
            yield error.report.E201('Unknown keyword "{0}" in "{1}"'
                                    .format(unknown, key), unknown)
        for ckey, cvalue in six.iteritems(keywords):
            check = cvalue['check']
            data = block.get(ckey)
            if not data:
                continue
            if isinstance(check, tuple):
                for left, right in six.iteritems(data):
                    yield self._run_check(check[0], left)
                    yield self._run_check(check[1], right)
            else:
                yield self._run_check(check, data)
