#!/usr/bin/env python3

import os
from pkg_resources import parse_requirements
from setuptools import setup, find_namespace_packages
from setuptools_scm import get_version


ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
current_version = get_version(root=ROOT_DIR + '/../../')
parts = current_version.split('.')
next_minor_version = '.'.join([parts[0], str(int(parts[1]) + 1)])


def calculate_requirements():
    requirements = []

    with open(ROOT_DIR + '/requirements-prod.txt') as f:
        for requirement in parse_requirements(f.read()):
            requirements.append(str(requirement))

    # other subpackages will be added as: >= current_version but < next_minor_version
    # example:
    #     current_version = 3.1.5-dev1
    #     next_minor_version = 3.2
    if os.path.isfile('requirements-subpackages.txt'):
        with open('requirements-subpackages.txt') as f:
            for line in f.readlines():
                if not line.strip():
                    continue

                requirements.append(line.strip() + '>=' + current_version + ', < ' + next_minor_version)

    return requirements


setup(
    setup_requires=['pbr', 'setuptools_scm'],
    pbr=True,
    packages=find_namespace_packages(include='rkd.*', exclude=('tests',)),
    include_package_data=True,
    install_requires=calculate_requirements()
)
