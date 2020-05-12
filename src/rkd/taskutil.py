
import os
import sys
from typing import Union
from subprocess import check_call, check_output, Popen, DEVNULL, PIPE as SUBPROCESS_PIPE, CalledProcessError, STDOUT as SUBPROCESS_STDOUT
from threading import Thread
from abc import ABC as AbstractClass, abstractmethod
from .inputoutput import IO


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

    def sh(self, cmd: str, capture: bool = False, verbose: bool = False, strict: bool = True,
           env: dict = None) -> Union[str, None]:
        """ Executes a shell script in bash. Throws exception on error.
            To capture output set capture=True
        """

        # set strict mode, it can be disabled manually
        if strict:
            cmd = 'set -euo pipefail; ' + cmd

        if env:
            for name, value in env.items():
                cmd = (" export %s='%s';\n" % (name, value)) + cmd

        if verbose:
            cmd = 'set -x; ' + cmd

        bash_script = "#!/bin/bash -eopipefail \n" + cmd
        read, write = os.pipe()
        os.write(write, bash_script.encode('utf-8'))
        os.close(write)

        if not capture:
            process = Popen('bash', shell=True, stdin=read, stdout=SUBPROCESS_PIPE, stderr=SUBPROCESS_STDOUT)

            stdout_thread = Thread(target=self._copy_stream, args=(process.stdout, sys.stdout, process))
            stdout_thread.daemon = True
            stdout_thread.start()
            stderr = ''

            exit_code = process.wait()

            if exit_code > 0:
                raise CalledProcessError(exit_code, cmd, None, stderr)

            return

        return check_output('bash', shell=True, stdin=read).decode('utf-8')

    @staticmethod
    def _copy_stream(in_stream, out_stream, process: Popen):
        while process.poll() is None:
            for line in iter(in_stream.readline, ''):
                out_stream.write(line.decode('utf-8'))

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
            check_call(cmd, shell=True)
            return

        return check_output(cmd, shell=True).decode('utf-8')

    def rkd(self, args: list, verbose: bool = False) -> str:
        """ Spawns an RKD subprocess
        """

        bash_opts = 'set -x; ' if verbose else ''
        args_str = ' '.join(args)

        return self.sh(bash_opts + ' rkd --no-ui %s' % args_str)
