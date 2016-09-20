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

from muranopkgcheck.i18n import _LE

errors = dict()


class CheckError(Exception):

    def __init__(self, code, message, filename=None,
                 line=0, column=0, source=None):
        self.code = code
        self.message = message
        self.filename = filename
        self.line = line
        self.column = column
        self.source = source

    def to_dict(self):
        fields = ('code', 'message', 'filename', 'line', 'column', 'source')
        serialized = {}
        for f in fields:
            serialized[f] = self.__getattribute__(f)
        return serialized

    def is_warning(self):
        return self.code.split(':')[-1].startswith('W')

    def is_error(self):
        return self.code.split(':')[-1].startswith('E')

    def __repr__(self):
        return 'CheckError({0})'.format(self.message)


class Report(object):

    def __init__(self, errors, prefix=None):
        self.prefix = prefix
        self.errors = errors

    def __getattr__(self, code):
        code = ':'.join((self.prefix, code)) if self.prefix else code

        def _report(message, yaml_obj=None, filename=None):
            meta = getattr(yaml_obj, '__yaml_meta__', None)
            kwargs = {}
            if meta is not None:
                kwargs['line'] = meta.line + 1
                kwargs['column'] = meta.column + 1
                kwargs['source'] = meta.get_snippet()
                kwargs['filename'] = filename or meta.name
            return CheckError(code=code, message=message, **kwargs)
        if code not in self.errors:
            raise ValueError(_LE('Error {} was not registered').format(code))
        return _report


class Register(object):

    def __init__(self, errors, prefix=None):
        self.prefix = prefix
        self.errors = errors

    def __getattr__(self, code):
        code = ':'.join((self.prefix, code)) if self.prefix else code
        if code in self.errors:
            raise ValueError(_LE('Error {} is already registered')
                             .format(code))

        def _register(**kwargs):
            props = kwargs.copy()
            props['code'] = code
            self.errors[code] = props
        return _register

report = Report(errors)
register = Register(errors)
