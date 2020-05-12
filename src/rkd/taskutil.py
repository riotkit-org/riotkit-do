
import os
import sys
from typing import Union
from time import sleep
from subprocess import check_call, check_output, Popen, DEVNULL, PIPE as SUBPROCESS_PIPE, CalledProcessError
from queue import Queue
from threading import Thread
from abc import ABC as AbstractClass


class TaskUtilities(AbstractClass):
    """
    Internal helpers for TaskInterface implementations
    """

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
            process = Popen('bash', shell=True, stdin=read, stdout=SUBPROCESS_PIPE, stderr=SUBPROCESS_PIPE, bufsize=1,
                            close_fds='posix' in sys.builtin_module_names)

            out_queue = Queue()
            stdout_thread = Thread(target=self._enqueue_output, args=(process.stdout, out_queue))
            stdout_thread.daemon = True
            stdout_thread.start()

            err_queue = Queue()
            stderr_thread = Thread(target=self._enqueue_output, args=(process.stderr, err_queue))
            stderr_thread.daemon = True
            stderr_thread.start()

            stderr = ''

            # subprocess is having issues with giving stdout and stderr streams directory as arguments
            # that's why the streams are copied there
            def flush():
                if not out_queue.empty():
                    out_line = out_queue.get(timeout=.1)
                    sys.stdout.write(out_line.decode('utf-8'))

                if not err_queue.empty():
                    err_line = err_queue.get(timeout=.1)
                    stderr = err_line.decode('utf-8')
                    sys.stderr.write(stderr)

            while process.poll() is None:
                flush()
                sleep(0.01)  # important: to not dry the CPU (no sleep = full cpu usage at one core)

            flush()
            exit_code = process.wait()

            if exit_code > 0:
                raise CalledProcessError(exit_code, cmd, None, stderr)

            return

        return check_output('bash', shell=True, stdin=read).decode('utf-8')

    @staticmethod
    def _enqueue_output(out, queue: Queue):
        for line in iter(out.readline, b''):
            queue.put(line)
        out.close()

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

    def rkd(self, args: list) -> str:
        """ Spawns an RKD subprocess
        """

        args_str = ' '.join(args)
        return self.exec('rkd --no-ui %s' % args_str, capture=True, background=False)
