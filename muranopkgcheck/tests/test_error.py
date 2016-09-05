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

from muranopkgcheck import error
from muranopkgcheck.tests import base


class LogTest(base.TestCase):

    @mock.patch('muranopkgcheck.error.CheckError')
    def test_errors(self, m_error):
        errors = dict()
        register = error.Register(errors, prefix='PRE')
        report = error.Report(errors, prefix='PRE')
        register.F042(description='Fake error')
        self.assertRaises(ValueError, register.__getattr__,
                          code='F042')
        self.assertEqual({'PRE:F042': {'code': 'PRE:F042',
                                       'description': 'Fake error'}},
                         errors)
        yaml_obj = mock.MagicMock(__yaml_meta__=mock.Mock(line=1,
                                                          column=1))
        type(yaml_obj.__yaml_meta__).name = mock.PropertyMock(
            return_value='fake.yaml')
        yaml_obj.__yaml_meta__.get_snippet.return_value = 'fake_code'
        report.F042('It is an error!', yaml_obj)
        m_error.assert_called_once_with(
            code='PRE:F042',
            column=2,
            line=2,
            filename='fake.yaml',
            message='It is an error!',
            source='fake_code')
        self.assertRaises(ValueError, report.__getattr__,
                          code='FAKE')
