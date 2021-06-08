#!/usr/bin/env python3

from setuptools import setup, find_namespace_packages

setup(
    setup_requires=['pbr'],
    pbr=True,
    packages=find_namespace_packages(include='rkd.*', exclude=('tests',))
)
