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
import os
import re
import zipfile

import six
import yaml

from muranopkgcheck import consts
from muranopkgcheck import log
from muranopkgcheck import yaml_loader

LOG = log.get_logger(__name__)


class FileWrapper(object):

    def __init__(self, pkg, path):
        self._path = path
        with pkg.open_file(path) as file_:
            self._raw = file_.read()

        with pkg.open_file(path) as file_:
            try:
                self._yaml = list(yaml.load_all(file_, yaml_loader.YamlLoader))
            except yaml.YAMLError:
                self._yaml = None

    def raw(self):
        return self._raw

    def yaml(self):
        return self._yaml


@six.add_metaclass(abc.ABCMeta)
class BaseLoader(object):
    def __init__(self, path):
        self.path = path
        self._cached_files = dict()
        self.format = consts.DEFAULT_FORMAT
        self.format_version = consts.DEFAULT_FORMAT_VERSION

    @classmethod
    @abc.abstractmethod
    def _try_load(cls, path):
        pass

    @classmethod
    def try_load(cls, path):
        loader = cls._try_load(path)
        if loader is not None and loader.exists(consts.MANIFEST_PATH):
            loader.try_set_format()
            return loader

    @abc.abstractmethod
    def list_files(self, subdir=None):
        pass

    @abc.abstractmethod
    def open_file(self, path, mode='r'):
        pass

    @abc.abstractmethod
    def exists(self, name):
        pass

    def search_for(self, regex='.*', subdir=None):
        r = re.compile(regex)
        return (f for f in self.list_files(subdir) if r.match(f))

    def read(self, path):
        if path in self._cached_files:
            return self._cached_files[path]
        self._cached_files[path] = FileWrapper(self, path)
        return self._cached_files[path]

    def try_set_format(self):
        if self.exists(consts.MANIFEST_PATH):
            manifest = self.read(consts.MANIFEST_PATH).yaml()
            if manifest and 'Format' in manifest:
                if '/' in str(manifest['Format']):
                    fmt, version = manifest['Format'].split('/', 1)
                    self.format = fmt
                    self.format_version = version
                else:
                    self.format_version = str(manifest['Format'])


class DirectoryLoader(BaseLoader):

    @classmethod
    def _try_load(cls, path):
        if os.path.isdir(path):
            return cls(path)
        return None

    def open_file(self, path, mode='r'):
        return open(os.path.join(self.path, path), mode)

    def list_files(self, subdir=None):
        path = self.path
        if subdir is not None:
            path = os.path.join(path, subdir)

        files = []
        for dirpath, dirnames, filenames in os.walk(path):
            files.extend(
                os.path.relpath(
                    os.path.join(dirpath, filename), self.path)
                for filename in filenames)
        if subdir is None:
            return files
        subdir_len = len(subdir)
        return [file_[subdir_len:].lstrip('/') for file_ in files]

    def exists(self, name):
        return os.path.exists(os.path.join(self.path, name))


class ZipLoader(BaseLoader):

    def __init__(self, path):
        super(ZipLoader, self).__init__(path)
        self._zipfile = zipfile.ZipFile(self.path)

    @classmethod
    def _try_load(cls, path):
        try:
            return cls(path)
        except (IOError, zipfile.BadZipfile):
            return None

    def open_file(self, name, mode='r'):
        return self._zipfile.open(name, mode)

    def list_files(self, subdir=None):
        files = self._zipfile.namelist()
        if subdir is None:
            return files
        subdir_len = len(subdir)
        return [file_[subdir_len:].lstrip('/') for file_ in files
                if file_.startswith(subdir)]

    def exists(self, name):
        try:
            self._zipfile.getinfo(name)
            return True
        except KeyError:
            pass

        if not name.endswith('/'):
            try:
                self._zipfile.getinfo(name + '/')
                return True
            except KeyError:
                pass
        return False


PACKAGE_LOADERS = [DirectoryLoader, ZipLoader]


def load_package(path):
    for loader_cls in PACKAGE_LOADERS:
        loader = loader_cls.try_load(path)
        if loader is not None:
            return loader
        else:
            LOG.debug("{} failed to load '{}'"
                      "".format(loader_cls.__name__, path))
    else:
        raise ValueError("Cannot load package: '{}'".format(path))
