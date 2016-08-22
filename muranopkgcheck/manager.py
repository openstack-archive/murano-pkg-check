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

import itertools
import types

import stevedore

from muranopkgcheck import error
from muranopkgcheck import log
from muranopkgcheck import pkg_loader
from muranopkgcheck.validators import VALIDATORS

LOG = log.get_logger(__name__)


class Formatter(object):

    def format(self, error):
        pass


class PlainTextFormatter(Formatter):

    def format(self, errors):
        lines = []
        for e in errors:
            if e.filename:
                lines.append('{filename}:{line}:{column}: {code} {message}'
                             ''.format(**e.to_dict()))
            else:
                lines.append('{code} {message}'
                             ''.format(**e.to_dict()))

        return '\n'.join(lines)


class Manager(object):

    def __init__(self, pkg_path):
        self.pkg = pkg_loader.load_package(pkg_path)
        self.validators = VALIDATORS
        self.plugins = None

    def _to_list(self, error_chain, select=None, ignore=None):
        errors = []
        while True:
            try:
                e = next(error_chain, None)
                if e is None:
                    break
            except Exception:
                LOG.exception('Checker failed')
                e = error.report.E000(
                    'Checker failed more information in logs')

            if isinstance(e, types.GeneratorType):
                errors.extend(self._to_list(e, select, ignore))
            else:
                if ((select and e.code not in select)
                   or (ignore and e.code in ignore)):
                    continue
                errors.append(e)

        return sorted(errors, key=lambda err: err.code)

    def load_plugins(self):
        if self.plugins is not None:
            return
        self.plugins = stevedore.ExtensionManager(
            'muranopkgcheck.plugins', invoke_on_load=True,
            propagate_map_exceptions=True,
            on_load_failure_callback=self.failure_hook)
        plugin_validators = list(itertools.chain(
            *(p.obj.validators() for p in self.plugins)
        ))
        self.validators += plugin_validators

    @staticmethod
    def failure_hook(_, ep, err):
        LOG.error('Could not load %r: %s', ep.name, err)
        raise err

    def validate(self, validators=None, select=None, ignore=None):
        validators = validators or self.validators
        report_chains = []
        for validator in validators:
            v = validator(self.pkg)
            report_chains.append(v.run())
        return self._to_list(itertools.chain(*report_chains), select, ignore)
