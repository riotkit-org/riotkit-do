#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    setup_requires=['pbr'],
    pbr=True,
    package_dir={'': './'},
    packages=find_packages(where='./'),
    include_package_data=True,
    package_data={
        'rkd': [
            'misc/*',
            'misc/**/*',
            'misc/initial-structure/.rkd/*',
            'misc/initial-structure/.rkd/**/*',
            'misc/initial-structure/.rkd/logs/.gitkeep',
            'misc/internal/**/*'
        ]
    }
)
