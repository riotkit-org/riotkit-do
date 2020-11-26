"""
Packaging
=========

Utilities related to finding resources of installed RKD
"""

import os
import sys
from distutils.sysconfig import get_python_lib
from typing import List, Optional, Callable


def find_resource_directory(path: str, additional_paths: list = None) -> Optional[str]:
    return _find(path, os.path.isdir)


def find_resource_file(path: str) -> Optional[str]:
    return _find(path, os.path.isfile)


def get_possible_paths(path: str) -> List[str]:
    """
    Finds possible paths to resources, considering PACKAGE and USER directories first, then system-wide directories

    :param path:
    :return:
    """

    return [
        # eg. ./rkd/misc/banner.txt
        os.path.dirname(os.path.realpath(__file__)) + '/misc/' + path,

        # eg. /home/andrew/.local/lib/python3.8/site-packages/usr/share/rkd/banner.txt
        get_user_site_packages() + '/usr/share/rkd/' + path,

        # eg. /usr/lib/python3.8/site-packages/usr/share/rkd/banner.txt
        _get_global_site_packages() + '/usr/share/rkd/' + path,

        # eg. /usr/share/rkd/banner.txt
        '/usr/share/rkd/' + path
    ]


def get_user_site_packages() -> str:
    """
    Finds a user or venv site-packages directory
    :return:
    """

    return next(p for p in sys.path if 'site-packages' in p)


def _find(path: str, method: Callable) -> Optional[str]:
    for checked_path in get_possible_paths(path):
        if method(checked_path):
            return checked_path

    return None


def _get_global_site_packages() -> str:
    return get_python_lib()

