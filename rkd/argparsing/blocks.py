"""
Commandline Blocks
==================

Blocks are adding error handling to pipeline of tasks, allowing to define fallback actions.
Can be used in shell, in TaskAliases.

Example:

.. code:: shell

    :prepare '{@rescue :rollback @error :notify "Failed" @retry 3}' :deploy --env=test{/@}


Rules:

    - @error and @rescue cannot exist together
    - Blocks cannot be nested

Available modifiers:

    - @error (execute a task, when any of task fails, break the pipeline. Good for notifications)
    - @rescue (execute a task, when any of task fails, don't break the pipeline if rescue action succeeds)
    - @retry (retry failed task up to X times, good for unstable tasks as a workaround until those tasks are not fixed)
    - @retry-block (retry whole block in case, when a single task fails)
"""

import re
from typing import Tuple, List, Union, Dict
from .model import ArgumentBlock
from ..exception import CommandlineParsingError

TOKEN_SEPARATOR = ' '
TOKEN_BEGIN_BLOCK = '{@'
TOKEN_BEGIN_BLOCK_ENDING = '{/@'
TOKEN_CLOSING_BLOCK = '}'
TOKEN_BLOCK_REFERENCE_OPENING = '[[[$RKT_BLOCK'
TOKEN_BLOCK_REFERENCE_CLOSING = ']]]'
TEMPORARY_SEPARATOR = '[[[$_RKD_SEP]]]'
ALLOWED_MODIFIERS = ['rescue', 'error', 'retry', 'retry-block']


def strip_empty_elements(to_strip: list) -> list:
    try:
        if not to_strip[0]:
            del to_strip[0]
    except KeyError:
        pass

    try:
        if not to_strip[-1]:
            del to_strip[-1]
    except KeyError:
        pass

    return to_strip


def parse_blocks(commandline: List[str]) -> Tuple[List[str], dict]:
    """
    Parses commandline into blocks. Uses a cursor-based methodology

    Examples:
        :aaa {@rescue :rollback --env=test-2} :deploy --env=test {/@}
        :bbb {@rescue :rollback @error :notify "Failed" @retry 3}:deploy --env=test{/@}

        Given we have ":bbb {@rescue :rollback @error :notify "Failed" @retry 3}:deploy --env=test{/@}"
        Then we extract it into ":bbb [[[$_RKD_GROUP_1]]]" + list of objects [ArgumentBlock] with one element

    :author: dkwebbie <github.com/dkwebbie>
    """

    # TEMPORARY_SEPARATOR allows to keep original data structure, as manual, primitive parsing can lose quoted strings
    # for example
    commandline_as_str = TEMPORARY_SEPARATOR.join(commandline)

    cursor = 0
    cursor_end = len(commandline_as_str)
    block_id = 0
    collected_blocks = {}

    while cursor < cursor_end:
        opening_match = commandline_as_str.find(TOKEN_BEGIN_BLOCK, cursor)

        # 1. Find opening "{@"
        if opening_match >= 0:
            block_id += 1
            cursor = opening_match  # after "{@"

            closing_match = commandline_as_str.find(TOKEN_CLOSING_BLOCK, cursor)

            # if accidentally closing tag was matched, then we do not have a match
            if commandline_as_str[closing_match - 3:closing_match] == "{/@":
                closing_match = 0

            # 2. Find closing "}" of the "{@"
            if closing_match < 0:
                raise CommandlineParsingError.from_block_closing_not_found(cursor)

            cursor = closing_match + 1  # after "{@block}"
            header = commandline_as_str[opening_match:closing_match]
            inner_arguments = parse_block_header(header)

            # 3. Find {/@...} - block ending
            block_ending_content = TOKEN_BEGIN_BLOCK_ENDING + TOKEN_CLOSING_BLOCK
            block_ending_match = commandline_as_str.find(block_ending_content, cursor)

            if block_ending_match < 0:
                raise CommandlineParsingError.from_block_ending_not_found(block_ending_content)

            body = strip_empty_elements(
                commandline_as_str[closing_match + 1:block_ending_match].split(TEMPORARY_SEPARATOR)
            )
            cursor = block_ending_match + len(block_ending_content)  # after "{/@}"

            if TOKEN_BEGIN_BLOCK in str(body):
                raise CommandlineParsingError.from_nested_blocks_not_allowed(TOKEN_BEGIN_BLOCK, header)

            block_token = ((TOKEN_BLOCK_REFERENCE_OPENING + '%i' + TOKEN_BLOCK_REFERENCE_CLOSING) % block_id)
            commandline_as_str = commandline_as_str[0:opening_match] + \
                                 block_token + \
                                 commandline_as_str[block_ending_match + len(block_ending_content):]

            # difference - we replace {@...}{/@} with eg. [[[$RKT_BLOCK1]]] - how many characters were removed
            after_replace_difference = ((block_ending_match + len(block_ending_content)) - opening_match) - len(block_token)
            cursor = cursor - after_replace_difference  # we are RIGHT after [[[$RKT_BLOCK1]]]

            try:
                collected_blocks[block_token.strip()] = ArgumentBlock(body=body, **inner_arguments)
            except TypeError as e:
                raise CommandlineParsingError.from_block_unknown_modifier(header, e)

        else:
            cursor += 1

    return commandline_as_str.split(TEMPORARY_SEPARATOR), collected_blocks


def parse_block_header(block_header: str) -> Dict[str, Union[str, int]]:
    """
    Parses a header ex. "{@retry 3"

    :author: dkwebbie <github.com/dkwebbie>
    """

    parsed = re.findall('@([a-z\-]+)([^@]*)', block_header)
    as_dict = {}

    if not parsed:
        raise CommandlineParsingError.from_block_header_parsing_exception(block_header)

    for result in parsed:
        result: List[str]
        name = result[0].strip()

        if name not in ALLOWED_MODIFIERS:
            raise CommandlineParsingError.from_block_unknown_modifier(block_header,
                                                                      Exception('Unknown modifier "%s"' % name))

        if name in as_dict:
            raise CommandlineParsingError.from_block_modifier_declared_twice(name, block_header)

        as_dict[name.replace('-', '_')] = result[1].strip()

    return as_dict
