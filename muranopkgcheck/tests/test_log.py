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

from muranopkgcheck import log
from muranopkgcheck.tests import base


class LogTest(base.TestCase):

    @mock.patch('muranopkgcheck.log.logging')
    def test_get_logger(self, m_log):
        fake_logger = log.getLogger('fake')
        m_log.getLogger.assert_called_once_with('fake')
        self.assertEqual(fake_logger, log._loggers['fake'])
        self.assertEqual(fake_logger, m_log.getLogger.return_value)
        m_log.reset_mock()
        fake_logger = log.getLogger('fake')
        m_log.assert_not_called()
        self.assertEqual(fake_logger, log._loggers['fake'])

    @mock.patch('muranopkgcheck.log.logging')
    def test_setup(self, m_log):
        fake_handler = m_log.StreamHandler.return_value
        fake_formatter = m_log.Formatter.return_value
        fake_logger = mock.Mock()
        fake_old_handler = mock.Mock()
        fake_logger.handlers = [fake_old_handler]
        log._loggers['fake'] = fake_logger

        log.setup(log_format='fake_format', level=42)

        m_log.StreamHandler.assert_called_once_with()
        fake_handler.setFormatter.assert_called_once_with(fake_formatter)
        fake_logger.setLevel.assert_called_once_with(42)
        fake_logger.removeHandler.assert_called_once_with(fake_old_handler)
        fake_logger.addHandler.assert_called_once_with(fake_handler)

    def test_setup_ext_logging(self):
        fake_logging = mock.Mock()
        log.setup(external_logging=fake_logging)
        self.assertEqual(log._logging, fake_logging)
        log.getLogger('fake_name')
        fake_logging.getLogger.assert_called_once_with('fake_name')
