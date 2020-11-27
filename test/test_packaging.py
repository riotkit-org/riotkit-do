#!/usr/bin/env python3

from unittest import mock
from rkd.api.testing import BasicTestingCase
import rkd.packaging


class TestPackaging(BasicTestingCase):
    def test_get_possible_paths_puts_local_development_path_in_first_priority(self):
        """
        When RKD is in development mode, and code is taken from local directory in current working directory
        then current working directory has FIRST priority.

        When RKD is installed, then the installation path in site-packages has lower priorite.
        :return:
        """

        with self.subTest('Local path - not installed will be first'):
            with mock.patch.object(rkd.packaging, '_get_current_script_path', return_value='/home/iwa/rkd'):
                paths = rkd.packaging.get_possible_paths('banner.txt')
                self.assertEqual('/home/iwa/rkd/misc/banner.txt', paths[0])

        with self.subTest('RKD installed as package will be last'):
            with mock.patch.object(rkd.packaging, '_get_current_script_path', return_value='/usr/lib/py/site-packages/rkd'):
                paths = rkd.packaging.get_possible_paths('banner.txt')
                self.assertEqual('/usr/lib/py/site-packages/rkd/misc/banner.txt', paths[-1])

    def test_find_resource_file(self):
        """Checks if file is found"""

        with self.subTest('Finds a one of defaults files'):
            self.assertIsNotNone(rkd.packaging.find_resource_file('banner.txt'))

        with self.subTest('Does not find a file'):
            self.assertIsNone(rkd.packaging.find_resource_file('this-name-does-not-exist'))

    def test_find_resource_directory(self):
        """Checks if directory is found"""

        with self.subTest('Looks and finds an "internal" directory'):
            self.assertIsNotNone(rkd.packaging.find_resource_directory('internal'))

        with self.subTest('Does not find a file'):
            self.assertIsNone(rkd.packaging.find_resource_directory('external-ths-does-not-exist'))

    def test_get_user_site_packages(self):
        self.assertIsNotNone(rkd.packaging.get_user_site_packages())
