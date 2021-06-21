#!/usr/bin/env python3
import glob
import os
import subprocess
import tempfile
from unittest import mock
from rkd.core.api.testing import BasicTestingCase
from rkd.process import check_call
import rkd.core.packaging

TESTS_DIR = os.path.dirname(os.path.realpath(__file__))
NAMESPACE_DIR = TESTS_DIR + '/../../'


class TestPackaging(BasicTestingCase):
    def test_get_possible_paths_puts_local_development_path_in_first_priority(self):
        """
        When RKD is in development mode, and code is taken from local directory in current working directory
        then current working directory has FIRST priority.

        When RKD is installed, then the installation path in site-packages has lower priorite.
        :return:
        """

        with self.subTest('Local path - not installed will be first'):
            with mock.patch.object(rkd.core.packaging, '_get_current_script_path', return_value='/home/iwa/rkd'):
                paths = rkd.core.packaging.get_possible_paths('banner.txt')
                self.assertEqual('/home/iwa/rkd/misc/banner.txt', paths[0])

        with self.subTest('RKD installed as package will be last'):
            with mock.patch.object(rkd.core.packaging, '_get_current_script_path', return_value='/usr/lib/py/site-packages/rkd'):
                paths = rkd.core.packaging.get_possible_paths('banner.txt')
                self.assertEqual('/usr/lib/py/site-packages/rkd/misc/banner.txt', paths[-1])

    def test_find_resource_file(self):
        """Checks if file is found"""

        with self.subTest('Finds a one of defaults files'):
            self.assertIsNotNone(rkd.core.packaging.find_resource_file('banner.txt'))

        with self.subTest('Does not find a file'):
            self.assertIsNone(rkd.core.packaging.find_resource_file('this-name-does-not-exist'))

    def test_find_resource_directory(self):
        """Checks if directory is found"""

        with self.subTest('Looks and finds an "internal" directory'):
            self.assertIsNotNone(rkd.core.packaging.find_resource_directory('internal'))

        with self.subTest('Does not find a file'):
            self.assertIsNone(rkd.core.packaging.find_resource_directory('external-ths-does-not-exist'))

    def test_get_user_site_packages(self):
        self.assertIsNotNone(rkd.core.packaging.get_user_site_packages())

    def test_get_user_site_packages_fallbacks_when_no_user_site_packages_directory(self):
        with mock.patch('sys.path', returns_value=[]):
            self.assertEqual(rkd.core.packaging._get_global_site_packages(), rkd.core.packaging.get_user_site_packages())

    def test_functionally_package_contains_complete_misc_directory(self):
        """
        "misc" directory is essential for RKD to work. There were issues with packaging this directory that contains
        non-python files.

        This test is installing RKD inside of a virtual environment and checking installed files.

        :return:
        """

        with tempfile.TemporaryDirectory() as tempdir:
            subprocess.check_output(['python', '-m', 'venv', tempdir])
            out = subprocess.check_output(
                '''
                    bash --init-file {tempdir}/bin/activate -c "source {tempdir}/bin/activate; 
                        set -xe;
                        pip install riotkit.pbs;
                        
                        cd {namespace_dir}/process;
                            rm -rf build/ dist/;
                            ./setup.py install;
                        
                        cd {namespace_dir}/core;
                            rm -rf build/ dist/;
                            ./setup.py install;
                    "
                '''.format(tempdir=tempdir, namespace_dir=NAMESPACE_DIR),
                shell=True,
                cwd='/tmp'
            )

            self.assertIn('copying build/lib/rkd/core/misc/internal/schema/org.riotkit.rkd-yaml-v1.json', out.decode('utf-8'))
            self.assertIn('copying build/lib/rkd/core/misc/initial-structure/.rkd/logs/.gitkeep', out.decode('utf-8'))



def scantree(path):
    """Recursively yield DirEntry objects for given directory."""
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            yield from scantree(entry.path)
        else:
            yield entry
