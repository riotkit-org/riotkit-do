"""
Centralized place for environment variables supported internally by RKD
=======================================================================

Idea is to make RKD core code clean of os.getenv() calls as much as possible.
The advantage is unified list of environment variables and always the same default values.

"""

import os
from typing import List

STR_BOOLEAN_TRUE = ['true', '1', 'yes']


def rkd_paths() -> List[str]:
    return os.getenv('RKD_PATH', '').split(':')


def rkd_depth() -> int:
    return int(os.getenv('RKD_DEPTH', 0))


def binary_name() -> str:
    return os.getenv('RKD_BIN')


def distribution_name() -> str:
    return os.getenv('RKD_DIST_NAME', 'rkd')


def audit_session_log_enabled() -> bool:
    return os.getenv('RKD_AUDIT_SESSION_LOG', '').lower() in STR_BOOLEAN_TRUE


def system_log_level() -> str:
    return os.getenv('RKD_SYS_LOG_LEVEL', 'info')


def is_subprocess_compat_mode() -> bool:
    return os.getenv('RKD_COMPAT_SUBPROCESS', '').lower() in STR_BOOLEAN_TRUE
