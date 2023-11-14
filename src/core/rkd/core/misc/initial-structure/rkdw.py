#!/usr/bin/env python3

"""
<docs>
RKD Wrapper
===========

Bootstraps a virtual environment transparently and starts RKD.

Environment:
    ENVIRONMENT_TYPE: venv, pipenv or auto
    VENV_CREATION_ARGS: Additional arguments for pipenv or virtualenv
    WRAPPER_MODULE: Name of the python module to proxy (defaults to 'rkd.core')
    PYTHON_BIN: Python binary path or command name (defaults to 'python')
    LOCK_CACHE_TIME: How long to cache the .venv-lock (defaults to '3600'), when expired will again calculate checksums.
                     If checksums will differ then virtualenv will be recreated
    IS_DEBUG: Debug mode, set to "1" to enable
</docs>

Designed and developed by Riotkit, an anarchist tech-collective supporting various grassroot movements, including
anarchosyndicalist workers unions like IWA-AIT, tenants rights organizations, anti-repression Anarchist Black Cross and
Food Not Bombs.

:url: https://github.com/riotkit-org/riotkit-do
:license: Apache-2
:author:
"""

import os
import sys
import json
import subprocess
from glob import glob
from time import time

ENVIRONMENT_TYPE = os.getenv('RKD_ENV_TYPE', 'auto')  # venv, pipenv, auto
VENV_CREATION_ARGS = os.getenv('RKD_ENV_CREATION_ARGS', '')
WRAPPER_MODULE = os.getenv('RKD_ENV_WRAPPER_MODULE', 'rkd.core')
PYTHON_BIN = os.getenv('RKD_ENV_PYTHON_BIN', 'python')
LOCK_CACHE_TIME = int(os.getenv('RKD_ENV_LOCK_TIME', 3600))
IS_DEBUG = os.getenv('RKD_ENV_DEBUG') == '1'

CALL_ARGS = [PYTHON_BIN, '-m', WRAPPER_MODULE] + sys.argv[1:]
VENV_PATH = '.venv'
LOCK_PATH = './.rkd/.venv-lock'


class PluggableEnvironmentSupport(object):
    def wrap(self) -> None:
        pass

    def calculate_checksum(self) -> str:
        pass

    @staticmethod
    def is_active() -> bool:
        pass

    def create(self) -> None:
        pass

    @staticmethod
    def get_name() -> str:
        pass


class PipenvSupport(PluggableEnvironmentSupport):
    def wrap(self) -> None:
        subprocess.check_call(['pipenv', 'run'] + CALL_ARGS)

    def calculate_checksum(self) -> str:
        if not os.path.isfile('Pipfile.lock'):
            return 'no-checksum-for-pipfile'

        return subprocess.check_output(['sha256sum', 'Pipfile.lock'])

    @staticmethod
    def is_active() -> bool:
        return os.path.isfile('Pipenv.lock')

    def create(self) -> None:
        subprocess.check_call(
            f'pipenv install {VENV_CREATION_ARGS} 2>&1 > .rkd/.venv.log || (cat .rkd/.venv.log && exit 1)',
            shell=True
        )

    @staticmethod
    def get_name() -> str:
        return 'pipenv'


class VenvSupport(PluggableEnvironmentSupport):
    def wrap(self) -> None:
        out = subprocess.check_output(['/bin/bash', '-c', f'source {VENV_PATH}/bin/activate; env'])
        env = {}

        for line in out.decode('utf-8').split('\n'):
            try:
                env_name, env_value = line.split('=', maxsplit=1)
            except ValueError:
                continue

            env[env_name] = env_value

        subprocess.check_call(CALL_ARGS, env=env)

    def calculate_checksum(self) -> str:
        requirements = glob('requirement*.txt')
        checksum = ""

        if not requirements:
            return 'no-checksum'

        for requirement_file in requirements:
            checksum += subprocess.check_output(['sha256sum', requirement_file]).decode('utf-8')

        return checksum

    @staticmethod
    def is_active() -> bool:
        # always acts as a fallback
        return False

    def create(self) -> None:
        requirements = glob('requirement*.txt')
        args = ''

        for requirement_file in requirements:
            args += f" -r {requirement_file} "

        if not args:
            with open('requirements.txt', 'w') as f:
                f.write('rkd==' + self.get_latest_rkd_stable_version())

            args = " -r requirements.txt "

        subprocess.check_call(f'{PYTHON_BIN} -m virtualenv {VENV_CREATION_ARGS} {VENV_PATH}', shell=True)
        subprocess.check_call(f'''
            /bin/bash -c 'set -e; source "{VENV_PATH}/bin/activate"; pip install {args}'
        ''', shell=True)

    @staticmethod
    def get_latest_rkd_stable_version() -> str:
        response = subprocess.check_output(
            'curl --silent https://api.github.com/repos/riotkit-org/riotkit-do/releases/latest', shell=True
        )

        parsed = json.loads(response)

        return parsed['tag_name'][1:]

    @staticmethod
    def get_name() -> str:
        return 'venv'


def debug(msg: str) -> None:
    if os.getenv('RKD_SYS_LOG_LEVEL') in ['debug', 'internal']:
        print(f'DEBUG >> {msg}')


def lock_exists() -> bool:
    return os.path.isfile(LOCK_PATH)


def lock_cache_is_outdated() -> bool:
    if not lock_exists():
        return True

    if 0 < LOCK_CACHE_TIME <= time() - os.path.getmtime(LOCK_PATH):
        return True

    return False


def should_create_virtualenv(checksum: str) -> bool:
    if not lock_exists():
        return True

    with open(LOCK_PATH, 'r') as f:
        return f.read() == checksum


def write_lock(checksum: str):
    with open(LOCK_PATH, 'w') as f:
        f.write(checksum)


def detect_env_type() -> PluggableEnvironmentSupport:
    supported = [PipenvSupport, VenvSupport]

    for environment in supported:
        if environment.get_name() == ENVIRONMENT_TYPE:
            return environment()

    for environment in supported:
        if environment.is_active():
            return environment()

    return VenvSupport()


def main():
    environment = detect_env_type()
    subprocess.check_call(['mkdir', '-p', '.rkd'])

    # special case: support RKD development directory
    if os.path.isdir('rkd'):
        cwd = os.getcwd()
        os.putenv('PYTHONPATH', os.getenv('PYTHONPATH', '') + f':{cwd}/../process:{cwd}/../pythonic')

    if lock_cache_is_outdated():
        debug('Lock file outdated')
        checksum = environment.calculate_checksum()

        if should_create_virtualenv(checksum):
            debug('Creating virtual environment')
            environment.create()

        write_lock(checksum)

    debug('Running command')
    environment.wrap()


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as err:
        sys.exit(err.returncode)
