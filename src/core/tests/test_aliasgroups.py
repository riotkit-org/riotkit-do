#!/usr/bin/env python3

from rkd.core.api.testing import BasicTestingCase
from rkd.core.aliasgroups import parse_alias_groups_from_env


class AliasGroupsTest(BasicTestingCase):
    def test_parsed_count_matches(self):
        self.assertEqual(2, len(parse_alias_groups_from_env(':harbor->:hb,:harbor->')))
        self.assertEqual(0, len(parse_alias_groups_from_env('')))

    def test_resolves_from_empty_alias_destination_name(self):
        """Resolves :harbor:start into :harbor"""

        parsed = parse_alias_groups_from_env('->:harbor')
        self.assertEqual(':harbor:start', parsed[0].append_alias_to_task(':start'))

    def test_resolves_single_level_group(self):
        parsed = parse_alias_groups_from_env(':iwa->:international-workers-association')
        self.assertEqual(':international-workers-association:strike', parsed[0].append_alias_to_task(':iwa:strike'))

    def test_resolves_multiple_level_group(self):
        parsed = parse_alias_groups_from_env(':wl->:workers:liberation')
        self.assertEqual(':workers:liberation:strike', parsed[0].append_alias_to_task(':wl:strike'))

    def test_not_resolves_anything(self):
        parsed = parse_alias_groups_from_env(':iwa->:international-workers-association')
        self.assertEqual(None, parsed[0].append_alias_to_task(':capitalism:sucks'))

    def test_removes_previous_group_name(self):
        parsed = parse_alias_groups_from_env('->:harbor')
        self.assertEqual(':start', parsed[0].get_aliased_task_name(':harbor:start'))
