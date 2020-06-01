
from typing import List
from typing import Optional

"""
Alias Groups
============

RKD_ALIAS_GROUPS

Allows to define aliases to groups eg. task :harbor:start can be started with just :start when alias is ':harbor->'
It is a feature that allows to create custom RKD distributions with "main tasks" shown, while the rest hidden, while the 
python package could be still imported regularly into RKD and used with :harbor:start - without having custom 
binary/distribution
"""


class AliasGroup(object):
    def __init__(self, src: str, dst: str):
        self._src = src
        self._dst = dst

    def get_aliased_task_name(self, task_name) -> Optional[str]:
        if task_name[0:len(self._src)] == self._src:
            return self._dst + task_name[len(self._src):]

        return None


def parse_alias_groups_from_env(value: str) -> List[AliasGroup]:
    groups = value.replace(' ', '').split(',')
    parsed = []

    for group in groups:
        try:
            src, dst = group.split('->')
        except ValueError:
            continue

        parsed.append(AliasGroup(src, dst))

    return parsed
