#!/usr/bin/env python3

from riotkit.pbs import get_setup_attributes
from setuptools import setup, find_namespace_packages

setup(
    **get_setup_attributes(root_dir='./', git_root_dir='../../'),
    packages=find_namespace_packages(include='rkd.*', exclude=('tests',)),
)
