#!/usr/bin/env python3

import os
import sys
import subprocess
from typing import Optional
from threading import Thread
from io import StringIO


def check_call(command: str, stdin=None, script: Optional[str] = ''):
    if os.getenv('RKD_COMPAT_SUBPROCESS') == 'true':
        subprocess.check_call(command, stdin=stdin, shell=True)
        return

    os.environ['PYTHONUNBUFFERED'] = "1"

    stdout_pipe_r, stdout_pipe_w = os.pipe()
    # stderr_pipe_r, stderr_pipe_w = os.pipe()

    # keep the last 1024 characters of stderr
    err_buffer = StringIO()
    out_buffer = StringIO()

    process = subprocess.Popen(command, shell=True, stdin=stdin, stdout=stdout_pipe_w, stderr=subprocess.STDOUT,
                               bufsize=1)

    stdout_thread = Thread(target=_copy_stream, args=(stdout_pipe_r, sys.stdout, process, out_buffer))
    stdout_thread.daemon = True
    stdout_thread.start()

    # stderr_thread = Thread(target=_copy_stream, args=(stderr_pipe_r, sys.stderr, process, err_buffer))
    # stderr_thread.daemon = True
    # stderr_thread.start()

    exit_code = process.wait()

    if exit_code > 0:
        raise subprocess.CalledProcessError(
            exit_code, script if script else command, stderr=err_buffer.getvalue(), output=out_buffer.getvalue()
        )


def _copy_stream(in_stream_fd: int, out_stream, process: subprocess.Popen, copy: StringIO = None):
    buffer_wrote_size = 0

    while process.poll() is None:
        read = os.read(in_stream_fd, 1024).decode('utf-8')
        out_stream.write(read)

        if copy:
            if buffer_wrote_size >= 1024:
                copy.truncate()

            buffer_wrote_size += len(read)
            copy.write(read)

    read = os.read(in_stream_fd, 1024 * 1024 * 10).decode('utf-8')
    out_stream.write(read)
