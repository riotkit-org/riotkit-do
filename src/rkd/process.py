#!/usr/bin/env python3

import os
import sys
import subprocess
from io import FileIO
from typing import Optional
from threading import Thread

ON_POSIX = 'posix' in sys.builtin_module_names


class TextBuffer(object):
    text: str
    size: int

    def __init__(self, buffer_size: int):
        self.text = ''
        self.size = buffer_size

    def write(self, text: str):
        buf_len = len(self.text)
        txt_len = len(text)

        if buf_len + txt_len > self.size:
            missing_len = (buf_len + txt_len) - self.size
            self.trim_left_by(missing_len)

        self.text += text

    def trim_left_by(self, bytes: int):
        self.text = self.text[bytes:]

    def get_value(self) -> str:
        return self.text


def check_call(command: str, stdin=None, script: Optional[str] = ''):
    if os.getenv('RKD_COMPAT_SUBPROCESS') == 'true':
        subprocess.check_call(command, stdin=stdin, shell=True)
        return

    os.environ['PYTHONUNBUFFERED'] = "1"

    process = subprocess.Popen(command, shell=True, stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               bufsize=1, close_fds=ON_POSIX, universal_newlines=True)

    out_buffer = TextBuffer(buffer_size=1024 * 10)
    stdout_thread = Thread(target=push_output, args=(process.stdout, sys.stdout, out_buffer))
    stdout_thread.daemon = True
    stdout_thread.start()

    exit_code = process.wait()

    if exit_code > 0:
        raise subprocess.CalledProcessError(
            exit_code, script if script else command, stderr=out_buffer.get_value(), output=out_buffer.get_value()
        )


def push_output(input_stream: FileIO, output_stream, out_buffer: TextBuffer):
    for line in iter(input_stream.readline, ''):
        output_stream.write(line)
        output_stream.flush()
        out_buffer.write(line)

    input_stream.close()


# def _debug(msg):
#     with open('/dev/stdout', 'w') as f:
#         f.write(str(msg))
