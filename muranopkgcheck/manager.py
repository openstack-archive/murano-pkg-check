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
import pprint
import sys
import types

import six
import stevedore

from muranopkgcheck import error
from muranopkgcheck.i18n import _
from muranopkgcheck.i18n import _LE
from muranopkgcheck import log
from muranopkgcheck import pkg_loader
from muranopkgcheck.validators import VALIDATORS

LOG = log.getLogger(__name__)

error.register.E000(description='Check failed')


@six.add_metaclass(abc.ABCMeta)
class Formatter(object):

    @abc.abstractmethod
    def format(self, error):
        pass    # pragma: no cover


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

    def __init__(self, pkg_path, quiet_load=False, loader=None):
        if loader:
            self.pkg = loader(pkg_path)
        else:
            self.pkg = pkg_loader.load_package(pkg_path, quiet=quiet_load)
        self.validators = list(VALIDATORS)
        self.plugins = None

    def _to_list(self, error_chain, select=None, ignore=None):
        errors = []
        while True:
            try:
                e = next(error_chain)
            except StopIteration:
                break
            except Exception:
                exc_info = sys.exc_info()
                tb = exc_info[2]
                while tb.tb_next:
                    tb = tb.tb_next
                validator_class = tb.tb_frame.f_locals.get('self')
                check_name = tb.tb_frame.f_code.co_name
                check_locals = tb.tb_frame.f_locals.copy()
                check_locals.pop('self', None)
                if validator_class:
                    msg = (_('Checker {} from {} failed!'
                             '').format(check_name,
                                        validator_class.__class__.__name__))
                else:
                    msg = (_('Checker {} failed!'
                             '').format(check_name))
                LOG.error('{} {}\n{}'.format(msg,
                                             _('Checker locals:'),
                                             pprint.pformat(check_locals)),
                          exc_info=exc_info)
                e = error.report.E000(
                    msg + _(' See more information in logs.'))
            if isinstance(e, types.GeneratorType):
                errors.extend(self._to_list(e, select, ignore))
            else:
                if ((select and e.code not in select) or
                        (ignore and e.code in ignore)):
                    LOG.debug('Skipped: {code} {message}'
                              ''.format(**e.to_dict()))
                    continue
                LOG.debug('Reported: {code} {message}'
                          ''.format(**e.to_dict()))
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
        LOG.error(_LE('Could not load {plugin}: {error}'
                      '').format(plugin=ep.name, error=err))
        raise err

    def validate(self, validators=None, select=None, ignore=None,
                 only_errors=False):
        validators = validators or self.validators
        report_chains = []
        for validator in validators:
            v = validator(self.pkg)
            report_chains.append(v.run())
        issues = self._to_list(itertools.chain(*report_chains), select, ignore)
        if only_errors:
            return [err for err in issues if err.is_error()]
        else:
            return issues
