#!/usr/bin/env python3

import os
import sys
import subprocess
import termios
import tty
import pty
import select
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


class ProcessState(object):
    has_exited: bool

    def __init__(self):
        self.has_exited = False


def check_call(command: str, script: Optional[str] = ''):
    if os.getenv('RKD_COMPAT_SUBPROCESS') == 'true':
        subprocess.check_call(command, shell=True)
        return

    os.environ['PYTHONUNBUFFERED'] = "1"

    old_tty = termios.tcgetattr(sys.stdin)
    process_state = ProcessState()

    try:
        tty.setraw(sys.stdin.fileno())

        # open a virtual terminal
        primary_fd, replica_fd = pty.openpty()

        process = subprocess.Popen(command, shell=True, stdin=replica_fd, stdout=replica_fd, stderr=replica_fd,
                                   bufsize=64, close_fds=ON_POSIX, universal_newlines=False, preexec_fn=os.setsid)

        out_buffer = TextBuffer(buffer_size=1024 * 10)
        fd_thread = Thread(target=push_output, args=(process, primary_fd, out_buffer, process_state))
        fd_thread.daemon = True
        fd_thread.start()

        exit_code = process.wait()
    finally:
        process_state.has_exited = True
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)

    if exit_code > 0:
        raise subprocess.CalledProcessError(
            exit_code, script if script else command, stderr=out_buffer.get_value(), output=out_buffer.get_value()
        )


def push_output(process, primary_fd, out_buffer: TextBuffer, process_state: ProcessState):
    while process.poll() is None:
        r, w, e = select.select([sys.stdin, primary_fd], [], [])

        if sys.stdin in r:
            d = os.read(sys.stdin.fileno(), 10240)
            os.write(primary_fd, d)

        elif primary_fd in r:
            o = os.read(primary_fd, 10240)

            # propagate to stdout
            if o:
                sys.stdout.write(o.decode('utf-8'))
                sys.stdout.flush()
                out_buffer.write(o.decode('utf-8'))

        if process_state.has_exited:
            return True


def direct_debug_msg(text: str) -> None:
    fd = open('/dev/stderr', 'w')
    fd.write(text + "\n")
    fd.close()
