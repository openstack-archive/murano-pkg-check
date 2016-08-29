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

import logging

import six

CRITICAL = logging.CRITICAL
ERROR = logging.ERROR
WARNING = logging.WARNING
INFO = logging.INFO
DEBUG = logging.DEBUG

LOG_FORMAT = "%(name)s:%(lineno)d %(levelname)s %(message)s"
DEFAULT_LEVEL = logging.DEBUG
_loggers = {}
_logging = None


def setup(external_logging=None, log_format=LOG_FORMAT, level=DEFAULT_LEVEL):

    if external_logging:
        global _logging
        _logging = external_logging
        return

    console_log_handler = logging.StreamHandler()
    console_log_handler.setFormatter(logging.Formatter(log_format))
    global _loggers
    for logger in six.itervalues(_loggers):
        logger.setLevel(level)
        for h in logger.handlers:
            logger.removeHandler(h)
        logger.addHandler(console_log_handler)


def getLogger(name):
    global _logging, _loggers
    if _logging:
        return _logging.getLogger(name)
    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)
    return _loggers[name]
