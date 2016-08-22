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

import types
import unittest


class BaseValidatorTestClass(unittest.TestCase):
    def setUp(self):
        self._g = []

    def tearDown(self):
        problems = [p for p in self.g]
        for p in problems:
            print('Left errors:', p)
        self.assertEqual(len(problems), 0)

    def _linear(self, error_chain):
        for e in error_chain:
            if isinstance(e, types.GeneratorType):
                for w in self._linear(e):
                    yield w
            else:
                yield e

    def get_g(self):
        return self._g

    def set_g(self, value):
        self._g = self._linear(value)

    g = property(get_g, set_g)
