
import os
import sys
from typing import Union
from subprocess import check_output, Popen, DEVNULL, CalledProcessError
from abc import ABC as AbstractClass, abstractmethod
from .inputoutput import IO
from .process import check_call


class TaskUtilities(AbstractClass):
    """
    Internal helpers for TaskInterface implementations
    """

    @abstractmethod
    def io(self) -> IO:
        pass

    def silent_sh(self, cmd: str, verbose: bool = False, strict: bool = True,
                  env: dict = None) -> bool:
        """
        sh() shortcut that catches errors and displays using IO().error_msg()
        """

        # kwargs is not used on purpose. For static analysis.

        try:
            self.sh(cmd=cmd, capture=False, verbose=verbose, strict=strict, env=env)
            return True

        except CalledProcessError as e:
            self.io().error_msg(str(e))
            return False

    @staticmethod
    def get_rkd_binary():
        """Gets the command how RKD was launched"""

        binary = sys.argv[0]

        # as a Python module: "python -m rkd" for example
        if binary[:-3] == '.py':
            return '%s -m %s' % (sys.executable, os.path.basename(os.path.dirname(binary)))

        # using a script eg. "rkd"
        return sys.executable

    def sh(self, cmd: str, capture: bool = False, verbose: bool = False, strict: bool = True,
           env: dict = None) -> Union[str, None]:
        """ Executes a shell script in bash. Throws exception on error.
            To capture output set capture=True
        """

        cmd = 'export PYTHONUNBUFFERED=1; ' + cmd

        # set strict mode, it can be disabled manually
        if strict:
            cmd = 'set -euo pipefail; ' + cmd

        if verbose:
            cmd = 'set -x; ' + cmd

        # append environment variables in order
        if env:
            env_str = ""

            for name, value in env.items():
                value = '' if value is None else str(value).replace('"', '\\"')
                env_str = env_str + (" export %s=\"%s\";\n" % (name, value))

            cmd = env_str + cmd

        bash_script = "#!/bin/bash -eopipefail \n" + cmd
        bash_script = bash_script.replace('%RKD%', self.get_rkd_binary())

        read, write = os.pipe()
        os.write(write, bash_script.encode('utf-8'))
        os.close(write)

        if not capture:
            check_call('bash', stdin=read, script=bash_script)
            return

        return check_output('bash', shell=True, stdin=read).decode('utf-8')

    def exec(self, cmd: str, capture: bool = False, background: bool = False) -> Union[str, None]:
        """ Starts a process in shell. Throws exception on error.
            To capture output set capture=True
        """

        if background:
            if capture:
                raise Exception('Cannot capture output from a background process')

            Popen(cmd, shell=True, stdout=DEVNULL, stderr=DEVNULL)
            return

        if not capture:
            check_call(cmd)
            return

        return check_output(cmd, shell=True).decode('utf-8')

    def rkd(self, args: list, verbose: bool = False) -> str:
        """ Spawns an RKD subprocess
        """

        bash_opts = 'set -x; ' if verbose else ''
        args_str = ' '.join(args)

        return self.sh(bash_opts + ' %%RKD%% --no-ui %s' % args_str)
