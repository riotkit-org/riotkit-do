import re
from typing import Tuple, List, Union, Dict
from .model import ArgumentBlock


TOKEN_SEPARATOR = ' '
TOKEN_BEGIN_BLOCK = '{@'
TOKEN_BEGIN_BLOCK_ENDING = '{/@'
TOKEN_CLOSING_BLOCK = '}'
TOKEN_BLOCK_REFERENCE_OPENING = '[[[$RKT_BLOCK'
TOKEN_BLOCK_REFERENCE_CLOSING = ']]]'
TEMPORARY_SEPARATOR = '[[[$_RKD_SEP]]]'


def strip_empty_elements(to_strip: list) -> list:
    if not to_strip[0]:
        del to_strip[0]

    if not to_strip[-1]:
        del to_strip[-1]

    return to_strip


def parse_blocks(commandline: List[str]) -> Tuple[List[str], dict]:
    """
    Examples:
        :aaa {@rescue :rollback --env=test-2} :deploy --env=test {/@}
        :bbb {@rescue :rollback @error :notify "Failed" @retry 3}:deploy --env=test{/@}

        Given we have ":bbb {@rescue :rollback @error :notify "Failed" @retry 3}:deploy --env=test{/@}"
        Then we extract it into ":bbb [[[$_RKD_GROUP_1]]]" + list of objects [ArgumentBlock] with one element
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

            # 2. Find closing "}" of the "{@"
            if not closing_match:
                raise Exception('Parsing exception: Closing not found for {@ opened at %i' % cursor)

            cursor = closing_match + 1  # after "{@block}"
            header = commandline_as_str[opening_match:closing_match]
            inner_arguments = parse_block_header(header)

            # 3. Find {/@...} - block ending
            block_ending_content = TOKEN_BEGIN_BLOCK_ENDING + TOKEN_CLOSING_BLOCK
            block_ending_match = commandline_as_str.find(block_ending_content, cursor)

            if not block_ending_match:
                raise Exception('Block ending - %s not found' % block_ending_content)

            body = strip_empty_elements(
                commandline_as_str[closing_match + 1:block_ending_match].split(TEMPORARY_SEPARATOR)
            )
            cursor = block_ending_match + len(block_ending_content)  # after "{/@}"

            if TOKEN_BEGIN_BLOCK in str(body):
                raise Exception('Nesting blocks "{}" not allowed, attempted inside block "{}"'.format(TOKEN_BEGIN_BLOCK, header))

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
                raise Exception('Block "{}" contains invalid modifier, raised error: {}'.format(header, str(e)))

        else:
            cursor += 1

    return commandline_as_str.split(TEMPORARY_SEPARATOR), collected_blocks


def parse_block_header(block_header: str) -> Dict[str, Union[str, int]]:
    parsed = re.findall('@(retry|rescue|error)([^@]*)', block_header)  # @todo: Verify unknown modifiers
    as_dict = {}

    if not parsed:
        raise Exception('Cannot parse block header "{}"'.format(block_header))

    for result in parsed:
        result: List[str]
        name = result[0].strip()

        if name in as_dict:
            raise Exception('Cannot declare "{}" twice in block "{}'.format(name, block_header))

        as_dict[name] = result[1].strip()

    return as_dict
