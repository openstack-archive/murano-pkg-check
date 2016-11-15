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
import zipfile

import six
import yaml
import yaml.error

from muranopkgcheck import consts
from muranopkgcheck import pkg_loader
from muranopkgcheck.tests import base


class FileWrapperTest(base.TestCase):

    @mock.patch('muranopkgcheck.pkg_loader.yaml')
    def test_file_wrapper(self, m_yaml):
        m_yaml.load_all.side_effect = yaml.load_all
        fake_pkg = mock.Mock()
        fake_pkg.open_file.side_effect = \
            lambda f: mock.mock_open(read_data=six.b('text'))()
        f = pkg_loader.FileWrapper(fake_pkg, 'fake_path')
        self.assertEqual(six.b('text'), f.raw())

        self.assertEqual(['text'], f.yaml())
        m_yaml.load_all.assert_called()

        self.assertEqual(['text'], f.yaml())
        m_yaml.load_all.reset_mock()
        m_yaml.load_all.assert_not_called()

        fake_pkg.open_file.side_effect = \
            lambda f: mock.mock_open(read_data=six.b('!@#$%'))()
        f = pkg_loader.FileWrapper(fake_pkg, six.b('fake_path'))
        self.assertEqual(six.b('!@#$%'), f.raw())
        self.assertRaises(yaml.error.YAMLError, f.yaml)


class FakeLoader(pkg_loader.BaseLoader):

    @classmethod
    def _try_load(cls, path):
        return cls(path)

    def open_file(self, path, mode='r'):
        pass

    def exists(self, name):
        if name == consts.MANIFEST_PATH:
            return True

    def list_files(self, subdir=None):
        if subdir is None:
            return ['1.yaml', '2.sh', 'sub/3.yaml']
        else:
            return ['3.yaml']


class BaseLoaderTest(base.TestCase):

    @mock.patch.object(FakeLoader, 'read')
    @mock.patch.object(FakeLoader, '_try_load')
    @mock.patch.object(FakeLoader, 'try_set_format')
    def test_try_load(self, m_format, m_load, m_read):
        m_read.return_value.yaml.return_value = [{'FullName': 'fake'}]
        m_load.return_value = FakeLoader('fake')
        fake_pkg = FakeLoader.try_load('fake')
        self.assertEqual(m_load.return_value, fake_pkg)
        m_load.assert_called_once_with('fake')
        m_format.assert_called_once_with({'FullName': 'fake'})

        m_format.reset_mock()
        m_read.return_value.yaml.return_value = [{}]
        self.assertIsNone(FakeLoader.try_load('fake'))
        m_format.assert_not_called()

        m_format.reset_mock()
        m_read.return_value.yaml.side_effect = yaml.error.YAMLError()
        self.assertIsNone(FakeLoader.try_load('fake'))
        m_format.assert_not_called()

    @mock.patch.object(FakeLoader, '_try_load')
    def test_try_set_version(self, m_load):
        m_file_wrapper = mock.Mock()
        m_file = m_file_wrapper.return_value
        m_file.yaml.return_value = [{'Format': 'Fake/42', 'FullName': 'fake'}]
        with mock.patch('muranopkgcheck.pkg_loader.FileWrapper',
                        m_file_wrapper):
            m_load.return_value = FakeLoader('fake')
            loader = FakeLoader.try_load('fake')
            self.assertEqual('Fake', loader.format)
            self.assertEqual('42', loader.format_version)
            m_file.yaml.assert_called_once_with()

            m_load.return_value = FakeLoader('fake')
            m_file.yaml.return_value = [{'Format': '4.2', 'FullName': 'fake'}]
            loader = FakeLoader.try_load('fake')
            self.assertEqual(consts.DEFAULT_FORMAT, loader.format)
            self.assertEqual('4.2', loader.format_version)

            m_load.return_value = FakeLoader('fake')
            m_file.yaml.return_value = [{'FullName': 'fake'}]
            loader = FakeLoader.try_load('fake')
            self.assertEqual(consts.DEFAULT_FORMAT, loader.format)
            self.assertEqual(consts.DEFAULT_FORMAT_VERSION,
                             loader.format_version)

    def test_search_for(self):
        fake = FakeLoader('fake')
        self.assertEqual(['1.yaml', 'sub/3.yaml'],
                         list(fake.search_for('.*\.yaml$')))
        self.assertEqual(['3.yaml'],
                         list(fake.search_for('.*\.yaml$', subdir='sub')))

    def test_read(self):
        fake = FakeLoader('fake')
        m_file_wrapper = mock.Mock()
        m_file = m_file_wrapper.return_value
        with mock.patch('muranopkgcheck.pkg_loader.FileWrapper',
                        m_file_wrapper):
            loaded = fake.read('fake')
            self.assertEqual(m_file, loaded)
            # check that cache works
            loaded = fake.read('fake')
            self.assertEqual(m_file, loaded)


class DirectoryLoaderTest(base.TestCase):

    @mock.patch.object(pkg_loader.DirectoryLoader, 'read')
    @mock.patch.object(pkg_loader.DirectoryLoader, 'try_set_format')
    @mock.patch.object(pkg_loader.DirectoryLoader, 'exists')
    def _load_fake_pkg(self, m_exists, m_try_set_format, m_read):
        with mock.patch('muranopkgcheck.pkg_loader.os.path.isdir') as m_isdir:
            m_read.return_value.yaml.return_value = [{'FullName': 'fake'}]
            m_exists.return_value = True
            m_isdir.return_value = True
            loader = pkg_loader.DirectoryLoader.try_load('fake')
            m_try_set_format.assert_called_once_with({'FullName': 'fake'})
            return loader

    def test_try_load(self):
        # NOTE(sslypushenko) Using mock.patch here as decorator breaks pdb
        pkg = self._load_fake_pkg()
        self.assertEqual('fake', pkg.path)
        with mock.patch('muranopkgcheck.pkg_loader.os.path.isdir') as m_isdir:
            m_isdir.return_value = False
            pkg = pkg_loader.DirectoryLoader.try_load('fake')
            self.assertIsNone(pkg)

    def test_list_files(self):
        # NOTE(sslypushenko) Using mock.patch here as decorator breaks pdb
        pkg = self._load_fake_pkg()
        with mock.patch('muranopkgcheck.pkg_loader.os.walk') as m_walk:
            m_walk.return_value = (item for item in [
                ('fake', ['subdir'], ['1', '2']),
                ('fake/subdir', [], ['3', '4']),
            ])
            self.assertEqual(['1', '2', 'subdir/3', 'subdir/4'],
                             pkg.list_files())
            m_walk.return_value = (item for item in [
                ('fake/subdir', [], ['3', '4']),
            ])
            self.assertEqual(['3', '4'],
                             pkg.list_files(subdir='subdir'))

    def test_exist(self):
        # NOTE(sslypushenko) Using mock.patch here as decorator breaks pdb
        pkg = self._load_fake_pkg()
        with mock.patch('muranopkgcheck.pkg_loader'
                        '.os.path.exists') as m_exists:
            m_exists.return_value = True
            self.assertTrue(pkg.exists('1.yaml'))
            m_exists.return_value = False
            self.assertFalse(pkg.exists('1.yaml'))


class ZipLoaderTest(base.TestCase):

    @mock.patch.object(pkg_loader.ZipLoader, 'read')
    @mock.patch.object(pkg_loader.ZipLoader, 'try_set_format')
    @mock.patch.object(pkg_loader.ZipLoader, 'exists')
    @mock.patch('muranopkgcheck.pkg_loader.zipfile')
    def _load_fake_pkg(self, m_zip, m_exists, m_try_set_format, m_read):
        m_zip_file = m_zip.ZipFile.return_value
        m_read.return_value.yaml.return_value = [{'FullName': 'fake'}]
        m_exists.return_value = True
        loader = pkg_loader.ZipLoader.try_load('fake')
        m_try_set_format.assert_called_once_with({'FullName': 'fake'})
        m_zip.ZipFile.assert_called_once_with('fake')
        return loader, m_zip_file

    def test_try_load(self):
        pkg, _ = self._load_fake_pkg()
        self.assertEqual('fake', pkg.path)
        with mock.patch('muranopkgcheck.pkg_loader.zipfile.ZipFile') as m_zip:
            m_zip.side_effect = zipfile.BadZipfile
            pkg = pkg_loader.ZipLoader.try_load('fake')
            self.assertIsNone(pkg)

    @mock.patch.object(pkg_loader.ZipLoader, 'read')
    @mock.patch.object(pkg_loader.ZipLoader, 'try_set_format')
    @mock.patch.object(pkg_loader.ZipLoader, 'exists')
    @mock.patch('muranopkgcheck.pkg_loader.zipfile')
    def test_try_load_from_bytesio(self, m_zip, m_exists, m_try_set_format,
                                   m_read):
        m_read.return_value.yaml.return_value = [{'FullName': 'fake'}]
        m_exists.return_value = True
        m_content = six.b('fake')
        loader = pkg_loader.ZipLoader.try_load(six.BytesIO(m_content))
        self.assertIsNotNone(loader)
        m_try_set_format.assert_called_once_with({'FullName': 'fake'})
        m_zip.ZipFile.assert_called()

    def test_list_files(self):
        pkg, m_zip = self._load_fake_pkg()
        m_zip.namelist.return_value = ['1', '2', 'sub/', 'sub/3', 'sub/4']
        self.assertEqual(['1', '2', 'sub/3', 'sub/4'],
                         pkg.list_files())
        self.assertEqual(['3', '4'],
                         pkg.list_files(subdir='sub'))

    def test_exist(self):
        pkg, m_zip = self._load_fake_pkg()
        self.assertTrue(pkg.exists('1.yaml'))
        m_zip.getinfo.side_effect = KeyError
        self.assertFalse(pkg.exists('1.yaml'))
        m_zip.getinfo.side_effect = [KeyError, None]
        self.assertTrue(pkg.exists('sub'))
        m_zip.getinfo.side_effect = [KeyError, KeyError]
        self.assertFalse(pkg.exists('sub'))
