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

    def __repr__(self):
        return 'CheckError({0})'.format(self.message)


def error(code, message, filename=None, line=0, column=0, source=None):
    return CheckError(code=code, message=message, filename=filename,
                      line=line, column=column, source=source)


def _report(code):
    def _report_(message, yaml_obj=None, filename=None):
        meta = getattr(yaml_obj, '__yaml_meta__', None)
        kwargs = {}
        if meta is not None:
            kwargs['line'] = meta.line + 1
            kwargs['column'] = meta.column + 1
            kwargs['source'] = meta.get_snippet()
            kwargs['filename'] = filename or meta.name
        return CheckError(code=code, message=message, **kwargs)
    return _report_


class Report(object):
    def __getattr__(self, name):
        return _report(name)

report = Report()
