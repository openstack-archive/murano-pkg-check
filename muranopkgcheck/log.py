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

CRITICAL = logging.CRITICAL
ERROR = logging.ERROR
WARNING = logging.WARNING
INFO = logging.INFO
DEBUG = logging.DEBUG

LOG_FORMAT = "%(asctime)s %(name)s:%(lineno)d %(levelname)s %(message)s"
DEFAULT_LEVEL = logging.DEBUG
LOG_HANDLER = None
LOG_LEVEL = DEFAULT_LEVEL


def setup(log_format=LOG_FORMAT, level=DEFAULT_LEVEL):
    console_log_handler = logging.StreamHandler()
    console_log_handler.setFormatter(logging.Formatter(log_format))
    global LOG_HANDLER, LOG_LEVEL
    LOG_HANDLER = console_log_handler
    LOG_LEVEL = level


def get_logger(name):
    logger = logging.getLogger(name)
    for h in logger.handlers:
        logger.removeHandler(h)
    logger.addHandler(LOG_HANDLER)
    logger.setLevel(LOG_LEVEL)
    return logger

setup()
