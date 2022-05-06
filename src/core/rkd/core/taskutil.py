
import os
import sys
from typing import Union
from subprocess import check_output, Popen, DEVNULL, CalledProcessError
from tempfile import NamedTemporaryFile
from abc import ABC as AbstractClass, abstractmethod
from copy import deepcopy
from rkd.process import check_call
from .api.inputoutput import IO
from . import env


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

        if env.binary_name():
            return env.binary_name()

        binary = sys.argv[0]
        sys_executable_basename = os.path.basename(sys.executable)

        if "-m unittest" in binary or "-m pytest" in binary:
            return binary.split(' ')[0] + ' -m rkd.core'

        if binary.endswith('/pytest') or binary.endswith('/py.test'):
            return sys_executable_basename + ' -m rkd.core'

        # as a Python module: "python -m rkd.core" for example
        if binary[:-3] == '.py':
            return '%s -m %s' % (sys.executable, os.path.basename(os.path.dirname(binary)))

        if sys_executable_basename.startswith('python'):
            return binary

        # using a script eg. "rkd"
        return sys.executable

    def sh(self, cmd: str, capture: bool = False, verbose: bool = False, strict: bool = True,
           env: dict = None, use_subprocess: bool = False) -> Union[str, None]:
        """ Executes a shell script in bash. Throws exception on error.
            To capture output set capture=True
        """

        self.io().debug('sh(%s)' % cmd)
        is_debug = self.io().is_log_level_at_least('debug')

        # cmd without environment variables
        original_cmd = deepcopy(cmd)

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

        if not capture:
            with NamedTemporaryFile() as bash_temp_file:
                bash_temp_file.write(bash_script.encode('utf-8'))
                bash_temp_file.flush()

                check_call('bash ' + bash_temp_file.name,
                           script_to_show=original_cmd if not is_debug else bash_script,
                           use_subprocess=use_subprocess)

            return

        read, write = os.pipe()
        os.write(write, bash_script.encode('utf-8'))
        os.close(write)

        return check_output('bash', shell=True, stdin=read).decode('utf-8')

    def py(self, code: str = '', become: str = None, capture: bool = False,
           script_path: str = None, arguments: str = '') -> Union[str, None]:

        """Executes a Python code in a separate process"""

        if (not code and not script_path) or (code and script_path):
            raise Exception('You need to provide only one of "code" or "script_path"')

        read, write = os.pipe()
        os.write(write, code.encode('utf-8'))
        os.close(write)

        cmd = 'python'
        py_temp_file = None

        if script_path:
            cmd += ' ' + script_path + ' '

        if code:
            with NamedTemporaryFile(delete=False) as py_temp_file:
                py_temp_file.write(code.encode('utf-8'))
                py_temp_file.flush()

            cmd += ' ' + py_temp_file.name

        if become:
            cmd = "sudo -E -u %s %s" % (become, cmd)

        os.environ['RKD_BIN'] = self.get_rkd_binary()
        os.environ['RKD_CTX_PY_PATH'] = ":".join(reversed(sys.path))

        if not capture:
            check_call(cmd + ' ' + arguments, script_to_show=code)
            os.unlink(py_temp_file.name) if py_temp_file else None
            return

        if capture:
            out = check_output(cmd + ' ' + arguments, shell=True, stdin=read).decode('utf-8')
            os.unlink(py_temp_file.name) if py_temp_file else None

            return out

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

    def rkd(self, args: list, verbose: bool = False, capture: bool = False) -> str:
        """ Spawns an RKD subprocess
        """

        bash_opts = 'set -x; ' if verbose else ''
        args_str = ' '.join(args)

        return self.sh(bash_opts + ' %%RKD%% --no-ui %s' % args_str, capture=capture)
