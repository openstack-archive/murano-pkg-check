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


from muranopkgcheck import error
from muranopkgcheck.validators import base

KNOWN_FILES_DIR = frozenset(['manifest.yaml', 'UI', 'LICENSE', 'Classes'])
REQUIRED_FILES_DIR = frozenset(['manifest.yaml', 'LICENSE'])


class PackageValidator(base.BaseValidator):
    def __init__(self, loaded_package):
        super(PackageValidator, self).__init__(loaded_package, '')

    def run(self):
        yield self._known_directories()

    def _known_directories(self):
        files = set(self._loaded_pkg.search_for('^\w+$'))
        try:
            logo_file = next(self._loaded_pkg.search_for('^manifest.yaml$'))\
                .yaml()[0]['Logo']
        except Exception:
            logo_file = 'logo.png'
        for file_ in files - KNOWN_FILES_DIR - {logo_file}:
            yield error.report.W120('Unknown "{0}" in package directory'
                                    .format(file_), file_)
        for file_ in REQUIRED_FILES_DIR - files:
            yield error.report.W121('Missing "{0}" in package directory'
                                    .format(file_), file_)
