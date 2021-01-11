"""
Packaging
=========

Utilities related to finding resources of installed RKD
"""

import os
import sys
from distutils.sysconfig import get_python_lib
from typing import List, Optional, Callable
from . import env


def find_resource_directory(path: str) -> Optional[str]:
    return _find(path, os.path.isdir)


def find_resource_file(path: str) -> Optional[str]:
    return _find(path, os.path.isfile)


def get_possible_paths(path: str) -> List[str]:
    """
    Finds possible paths to resources, considering PACKAGE and USER directories first, then system-wide directories

    :param path:
    :return:
    """

    # <sphinx_resources-get_possible_paths>
    dist_name = env.distribution_name()  # RKD_DIST_NAME env variable

    paths = [
        # eg. ~/.local/share/rkd/banner.txt
        os.path.expanduser(('~/.local/share/%s/' + path) % dist_name),

        # eg. /home/andrew/.local/lib/python3.8/site-packages/rkd/misc/banner.txt
        (get_user_site_packages() + '/%s/misc/' + path) % dist_name,

        # eg. /usr/lib/python3.8/site-packages/rkd/misc/banner.txt
        (_get_global_site_packages() + '/%s/misc/' + path) % dist_name,

        # eg. /usr/share/rkd/banner.txt
        ('/usr/share/%s/' + path) % dist_name
    ]
    # </sphinx_resources-get_possible_paths>

    # eg. ./rkd/misc/banner.txt
    global_module_path = _get_current_script_path() + '/misc/' + path

    # installed module directory should be less important to allow customizations
    if "site-packages" in global_module_path:
        paths.append(global_module_path)
    else:  # local development directory
        paths = [global_module_path] + paths

    return paths


def get_user_site_packages() -> str:
    """
    Finds a user or venv site-packages directory
    :return:
    """

    try:
        return next(p for p in sys.path if 'site-packages' in p)
    except StopIteration:
        return _get_global_site_packages()


def _find(path: str, method: Callable) -> Optional[str]:
    for checked_path in get_possible_paths(path):
        if method(checked_path):
            return checked_path

    return None


def _get_global_site_packages() -> str:
    return get_python_lib()


def _get_current_script_path() -> str:
    return os.path.dirname(os.path.realpath(__file__))
