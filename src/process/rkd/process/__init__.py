#!/usr/bin/env python3

"""
Process
=======

Library that wraps standard "subprocess" library, adding a correct output capturing capabilities.
By default standard "subprocess" library writes directly to descriptors, bypassing sys.stdout and sys.stderr
making it impossible to capture the text for logging.

"""
import io
import os
import sys
import subprocess
import termios
import tty
import pty
import select
import fcntl
import struct
from typing import Tuple, Callable
from typing import Optional
from typing import Union
from threading import Thread
from contextlib import contextmanager
from time import time
from . import env as rkd_env

ON_POSIX = 'posix' in sys.builtin_module_names
TEXT_BUFFER_CALLBACK_DEFINITION = Optional[Callable[[str], None]]


@contextmanager
def switched_workdir(workdir: str):
    old_cwd = os.getcwd()
    os.chdir(workdir)

    try:
        yield
    finally:
        os.chdir(old_cwd)


class TextBuffer(object):
    text: str
    size: int
    callback: TEXT_BUFFER_CALLBACK_DEFINITION

    def __init__(self, buffer_size: int, callback: TEXT_BUFFER_CALLBACK_DEFINITION = None):
        self.text = ''
        self.size = buffer_size
        self.callback = callback

    def write(self, text: str):
        buf_len = len(self.text)
        txt_len = len(text)

        if buf_len + txt_len > self.size:
            missing_len = (buf_len + txt_len) - self.size
            self.trim_left_by(missing_len)

        self.text += text

        if self.callback:
            self.callback(text)

    def trim_left_by(self, chars: int):
        self.text = self.text[chars:]

    def get_value(self) -> str:
        return self.text


class ProcessState(object):
    has_exited: bool
    exception: Exception = None

    def __init__(self):
        self.has_exited = False


def check_call(command: str, script_to_show: Optional[str] = '',
               use_subprocess: bool = False,
               cwd: Union[str, None] = None,
               env: dict = None,
               output_capture_callback: TEXT_BUFFER_CALLBACK_DEFINITION = None):
    """
    Another implementation of subprocess.check_call(), in comparison - this method writes output directly to
    sys.stdout and sys.stderr, which makes output capturing possible

    :param command: Command to execute
    :param script_to_show: Command to show that it failed
    :param use_subprocess: (Optional) Use subprocess.check_call() directly. Could simplify some cases.
    :param cwd: (Optional) Change current working directory
    :param env: (Optional) Append environment variables
    :param output_capture_callback: Optional callback that can read each buffered text

    :return:
    """

    if rkd_env.is_subprocess_compat_mode() or use_subprocess:
        subprocess.check_call(command, shell=True)
        return

    os.environ['PYTHONUNBUFFERED'] = "1"

    try:
        old_tty = termios.tcgetattr(sys.stdin)
    except termios.error:
        old_tty = None
    except io.UnsupportedOperation:
        old_tty = None

    try:
        sys.stdin.fileno()
    except io.UnsupportedOperation:
        old_tty = None

    # merge system environment with environment from parameters
    if env:
        merged_env = dict(os.environ)
        merged_env.update(env)
        env = merged_env

    is_interactive_session = old_tty is not None
    process_state = ProcessState()
    primary_fd = None
    replica_fd = None
    process: Optional[subprocess.Popen] = None

    try:
        if is_interactive_session:
            tty.setraw(sys.stdin.fileno())

        # open a virtual terminal
        primary_fd, replica_fd = pty.openpty()

        # little hack: give thread a time to warm up
        command = 'sleep 0.03 && ' + command

        process = subprocess.Popen(command, shell=True, stdin=replica_fd, stdout=replica_fd, stderr=replica_fd,
                                   bufsize=0, close_fds=ON_POSIX, universal_newlines=True, preexec_fn=os.setsid,
                                   cwd=cwd if cwd else os.getcwd(), env=env if env else None)

        out_buffer = TextBuffer(buffer_size=1024 * 10, callback=output_capture_callback)
        fd_thread = Thread(
            target=push_output,
            args=(
                process, primary_fd,
                out_buffer, process_state,
                is_interactive_session,
                lambda: clean_up_on_process_exit(old_tty, process_state, is_interactive_session,
                                                 primary_fd, replica_fd, process)
            )
        )

        fd_thread.daemon = True
        fd_thread.start()

        exit_code = process.wait()
    finally:
        clean_up_on_process_exit(old_tty, process_state, is_interactive_session, primary_fd, replica_fd, process)

    if process_state.exception:
        raise process_state.exception

    if exit_code > 0:
        raise subprocess.CalledProcessError(
            exit_code, script_to_show if script_to_show else command,
            stderr=out_buffer.get_value() if out_buffer else '',
            output=out_buffer.get_value() if out_buffer else ''
        )


def clean_up_on_process_exit(old_tty, process_state: ProcessState, is_interactive_session: bool,
                             primary_fd, replica_fd, process: Optional[subprocess.Popen]):

    """
    Clean up on process end

    :param old_tty:
    :param process_state:
    :param is_interactive_session:
    :param primary_fd:
    :param replica_fd:
    :param process:
    :return:
    """

    # make sure the process is terminated. Case: Exception was raised during interaction with process, but process is
    #                                            still alive
    if process:
        process.terminate()

    process_state.has_exited = True

    if is_interactive_session:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)

    try:
        for fd in [primary_fd, replica_fd]:
            try:
                os.close(fd)
            except OSError:
                pass
    except NameError:
        pass


def push_output(process, primary_fd, out_buffer: TextBuffer, process_state: ProcessState,
                is_interactive_session: bool, on_error: callable):

    """
    Receive output from running process and forward to streams, capture

    :param process:
    :param primary_fd:
    :param out_buffer:
    :param process_state:
    :param is_interactive_session:
    :param on_error:
    :return:
    """

    poller = select.epoll()
    poller.register(primary_fd, select.EPOLLIN)

    # terminal window size updating
    terminal_update_time = 3  # 3 seconds
    last_terminal_update = time()
    should_update_terminal_size = True

    try:
        copy_terminal_size(sys.stdout, primary_fd)
    except OSError as e:
        if e.errno == 25:
            should_update_terminal_size = False
        else:
            raise

    if is_interactive_session:
        poller.register(sys.stdin, select.EPOLLIN)

    while process.poll() is None:
        for r, flags in poller.poll(timeout=0.01):
            try:
                if is_interactive_session and sys.stdin.fileno() is r:
                    d = os.read(r, 10240)
                    os.write(primary_fd, d)

                elif primary_fd is r:
                    o = os.read(primary_fd, 10240)

                    # terminal window size updating
                    if should_update_terminal_size and time() - last_terminal_update >= terminal_update_time:
                        copy_terminal_size(sys.stdout, primary_fd)
                        last_terminal_update = time()

                    # propagate to stdout
                    if o:
                        decoded = carefully_decode(o, 'utf-8')

                        sys.stdout.write(decoded)
                        sys.stdout.flush()
                        out_buffer.write(decoded)

                if process_state.has_exited:
                    return True

            except Exception as exc:
                process_state.exception = exc
                process_state.has_exited = True
                on_error()

                return


def carefully_decode(txt_as_bytes: bytes, enc: str) -> str:
    """
    Decode from BYTES to STR.
    In case of decode error attempt to decode a character-by-character to recover as much as possible

    :param txt_as_bytes:
    :param enc:
    :return:
    """

    try:
        return txt_as_bytes.decode(enc)
    except UnicodeDecodeError:
        decoded = ''

        for char in range(0, len(txt_as_bytes)):
            try:
                decoded += txt_as_bytes[char:char+1].decode(enc)
            except UnicodeDecodeError:
                pass

        return decoded


def direct_debug_msg(text: str) -> None:
    fd = open('/dev/stderr', 'w')
    fd.write(text + "\n")
    fd.close()


def copy_terminal_size(fd_from, fd_to):
    """
    Set a terminal size basing on other terminal

    :param fd_from:
    :param fd_to:
    :return:
    """

    col, row, x_pixels, y_pixels = get_terminal_size(fd_from)

    winsize = struct.pack("HHHH", row, col, x_pixels, y_pixels)
    fcntl.ioctl(fd_to, termios.TIOCSWINSZ, winsize)


def get_terminal_size(fd) -> Optional[Tuple[int, int, int, int]]:
    """
    Get size of a terminal

    :param fd: for example it can be sys.stdout
    :return:
    """

    if os.name == "posix":
        # http://bytes.com/topic/python/answers/607757-getting-terminal-display-size
        s = struct.pack("HHHH", 0, 0, 0, 0)
        x = fcntl.ioctl(fd.fileno(), termios.TIOCGWINSZ, s)
        rows, cols, x_pixels, y_pixels = struct.unpack("HHHH", x)

        return cols, rows, x_pixels, y_pixels

    # Windows is not supported (at least yet)
    return None
