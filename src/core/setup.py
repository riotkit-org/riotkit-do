#!/usr/bin/env python3

# =================================================================
#  RiotKit's setuptools wrapper
#  ----------------------------
#  - Does not use PBR (because of requirements.txt enforcement)
#  - Uses setup.json as input dictionary to setup()
#  - Uses setuptools_scm to know self version
# =================================================================

import os
from pkg_resources import parse_requirements
from setuptools import setup, find_namespace_packages
from setuptools_scm import get_version
from json import load as json_load


ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
current_version = get_version(root=ROOT_DIR + '/../../')
parts = current_version.split('.')
next_minor_version = '.'.join([parts[0], str(int(parts[1]) + 1)])

# loads metadata from config.json
with open(ROOT_DIR + '/setup.json') as f:
    setup_attributes = json_load(f)

# sets long description
if os.path.isfile(ROOT_DIR + '/README.md'):
    with open(ROOT_DIR + '/README.md', 'r') as f:
        setup_attributes['long_description'] = f.read()
        setup_attributes['long_description_content_type'] = 'text/markdown'

elif os.path.isfile(ROOT_DIR + '/README.rst'):
    with open(ROOT_DIR + '/README.rst', 'r') as f:
        setup_attributes['long_description'] = f.read()
        setup_attributes['long_description_content_type'] = 'text/x-rst; charset=UTF-8'


def calculate_requirements():
    requirements = []

    # external requirements (3rd party libraries)
    if os.path.isfile(ROOT_DIR + '/requirements-external.txt'):
        with open(ROOT_DIR + '/requirements-external.txt') as f:
            for requirement in parse_requirements(f.read()):
                requirements.append(str(requirement))

    # other subpackages from same repository will be added as: >= current_version but < next_minor_version
    # example:
    #     current_version = 3.1.5-dev1
    #     next_minor_version = 3.2
    #
    # where both versions are calculated from CURRENT GIT repository
    if os.path.isfile('requirements-subpackages.txt'):
        with open('requirements-subpackages.txt') as f:
            for line in f.readlines():
                if not line.strip():
                    continue

                requirements.append(line.strip() + '>=' + current_version + ', < ' + next_minor_version)

    return requirements


def local_scheme(version):
    return ""


setup(
    **setup_attributes,
    use_scm_version={
        "root": ROOT_DIR + '/../../',
        "local_scheme": local_scheme
    },
    setup_requires=['setuptools_scm'],
    packages=find_namespace_packages(include='rkd.*', exclude=('tests',)),
    include_package_data=True,
    install_requires=calculate_requirements()
)
