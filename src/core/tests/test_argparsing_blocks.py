#!/usr/bin/env python3

import pytest
from rkd.core.api.testing import BasicTestingCase
from rkd.core.argparsing.blocks import parse_block_header, parse_blocks
from rkd.core.argparsing.model import ArgumentBlock
from rkd.core.exception import CommandlineParsingError


@pytest.mark.argparsing
class ArgParsingBlocksTest(BasicTestingCase):
    #
    # parse_block_header()
    #

    def test_parse_block_header_simple_case(self):
        parsed = parse_block_header('{@retry 2')

        self.assertEqual(parsed, {'retry': '2'})

    def test_parse_block_header_multiple_modifiers_case(self):
        parsed = parse_block_header('{@retry 2 @error :notify @retry-block 3')

        self.assertEqual({'retry': '2', 'error': ':notify', 'retry_block': '3'}, parsed)

    def test_parse_block_header_unknown_modifier_raises_exception(self):
        with self.assertRaises(CommandlineParsingError) as exc:
            parse_block_header('{@commune-de-paris')

        self.assertEqual('Block "{@commune-de-paris" contains invalid modifier, '
                         'raised error: Unknown modifier "commune-de-paris"',
                         str(exc.exception))

    def test_parse_block_header_raises_error_on_doubled_modifier(self):
        with self.assertRaises(CommandlineParsingError) as exc:
            parse_block_header('{@retry 2 @retry 3')

        self.assertEqual('Cannot declare "retry" twice in block "{@retry 2 @retry 3',
                         str(exc.exception))

    #
    # parse_Blocks()
    #

    def test_parse_blocks_simple_case(self):
        commandline, blocks = parse_blocks(['{@rescue :rollback --env=test-2}', ':deploy', '--env=test', '{/@}'])

        self.assertEqual(['[[[$RKT_BLOCK1]]]'], commandline, msg='Expected that exactly one block will be returned')

        # test first (and only one) block body
        block: ArgumentBlock = blocks['[[[$RKT_BLOCK1]]]']
        self.assertEqual([':deploy', '--env=test'], block.body, msg='Expected that body will be parsed')

        # Notice: At this stage, the block is syntax parsed, next stage is filling up object by CommandlineParsingHelper
        #         That's why on_rescue and other fields could be empty on this stage
        self.assertEqual({'rescue': ':rollback --env=test-2', 'error': ''}, block._raw_attributes,
                         msg='Expected a parsed header that should contain modifier as a key and action/value as value')

    def test_parse_blocks_does_not_erase_non_block_elements(self):
        commandline, blocks = parse_blocks([':before', '{@error :notify}', ':hello', '{/@}', ':after'])

        self.assertEqual([':before', '[[[$RKT_BLOCK1]]]', ':after'], commandline)
        self.assertEqual(1, len(blocks))

    def test_parse_blocks_raises_parser_error_when_block_has_no_ending(self):
        with self.assertRaises(CommandlineParsingError) as exc:
            parse_blocks([':hello', '{@error :notify}', ':test'])

        self.assertEqual('Parsing exception: Block ending - {/@} not found',
                         str(exc.exception))

    def test_parse_blocks_raises_error_on_nested_blocks(self):
        with self.assertRaises(CommandlineParsingError) as exc:
            parse_blocks([':hello', '{@error :notify}', '{@rescue}', ':test', '{/@}', '{/@}'])

        self.assertEqual('Nesting blocks "{@" not allowed, attempted inside block "{@error :notify"',
                         str(exc.exception))
