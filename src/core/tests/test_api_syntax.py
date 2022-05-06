#!/usr/bin/env python3

from rkd.core.api.testing import BasicTestingCase
from rkd.core.api.syntax import parse_path_into_subproject_prefix, merge_workdir


class TestApiSyntax(BasicTestingCase):
    def test_parse_path_into_subproject_prefix(self):
        self.assertEqual(':subproject1:subproject2:subproject3',
                         parse_path_into_subproject_prefix('subproject1/subproject2/subproject3'))

    def test_merge_workdir_leaves_task_workdir_if_not_in_subproject(self):
        self.assertEqual('build/', merge_workdir(
            task_workdir='build/',
            subproject_workdir=''
        ))

    def test_merge_workdir_leaves_absolute_path_for_task_even_if_in_subproject(self):
        self.assertEqual('/var/www/html', merge_workdir(
            task_workdir='/var/www/html',
            subproject_workdir='docs'
        ))

    def test_merge_workdir_concatenates_workdir_when_task_has_workdir_and_in_subproject(self):
        self.assertEqual('infrastructure/docs', merge_workdir(
            task_workdir='docs',
            subproject_workdir='infrastructure'
        ))
