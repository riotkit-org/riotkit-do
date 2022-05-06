import os

STR_BOOLEAN_TRUE = ['true', '1', 'yes']


def is_subprocess_compat_mode() -> bool:
    return os.getenv('RKD_COMPAT_SUBPROCESS', '').lower() in STR_BOOLEAN_TRUE
