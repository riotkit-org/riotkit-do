#!/usr/bin/env python3

import unittest
from rkd.aliasgroups import parse_alias_groups_from_env, AliasGroup


class AliasGroupsTest(unittest.TestCase):
    def test_parsed_count_matches(self):
        self.assertEqual(2, len(parse_alias_groups_from_env(':harbor->:hb,:harbor->')))
        self.assertEqual(0, len(parse_alias_groups_from_env('')))

    def test_resolves_from_empty_alias_destination_name(self):
        """Resolves :harbor:start into :harbor"""

        parsed = parse_alias_groups_from_env('->:harbor')
        self.assertEqual(':harbor:start', parsed[0].get_aliased_task_name(':start'))

    def test_resolves_single_level_group(self):
        parsed = parse_alias_groups_from_env(':iwa->:international-workers-association')
        self.assertEqual(':international-workers-association:strike', parsed[0].get_aliased_task_name(':iwa:strike'))

    def test_resolves_multiple_level_group(self):
        parsed = parse_alias_groups_from_env(':wl->:workers:liberation')
        self.assertEqual(':workers:liberation:strike', parsed[0].get_aliased_task_name(':wl:strike'))

    def test_not_resolves_anything(self):
        parsed = parse_alias_groups_from_env(':iwa->:international-workers-association')
        self.assertEqual(None, parsed[0].get_aliased_task_name(':capitalism:sucks'))
