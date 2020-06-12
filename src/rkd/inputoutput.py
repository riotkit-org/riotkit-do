
import re
import sys
import os
import subprocess
from typing import List
from contextlib import contextmanager
from datetime import datetime


this = sys.modules[__name__]
this.IS_CAPTURING_DESCRIPTORS = False

LEVEL_DEBUG = 37
LEVEL_INFO = 36
LEVEL_WARNING = 33
LEVEL_ERROR = 31
LEVEL_FATAL = 20

LOG_LEVELS = {
    'debug': LEVEL_DEBUG,
    'info': LEVEL_INFO,
    'warning': LEVEL_WARNING,
    'error': LEVEL_ERROR,
    'fatal': LEVEL_FATAL
}

LOG_LEVEL_FORMATTING_MAPPING = {
    'debug':   "\x1B[0m%TEXT%\x1B[0m",
    'info':    "\x1B[1m%TEXT%\x1B[0m",
    'warn':    "\x1B[93m%TEXT%\x1B[0m",
    'error':   "\x1B[91m%TEXT%\x1B[0m",
    'fatal':   "\x1B[91m\x1B[5m%TEXT%\x1B[0m"
}


class StandardOutputReplication(object):
    _out_streams: list

    def __init__(self, out_streams: list):
        self._out_streams = out_streams

    def write(self, buf):
        for stream in self._out_streams:
            try:
                stream.write(buf)
            except TypeError:
                try:
                    stream.write(buf.encode('utf-8'))
                except AttributeError:
                    stream.write(str(buf))

        self.flush()

    def fileno(self):
        return 1

    def flush(self):
        pass


class IO:
    """ Interacting with input and output - stdout/stderr/stdin, logging """

    silent = False
    log_level = LEVEL_INFO

    @contextmanager
    def capture_descriptors(self, target_files: List[str] = None, stream=None, enable_standard_out: bool = True):
        """Capture stdout and stderr from a block of code - use with 'with'"""

        if target_files is None:
            target_files = []

        if this.IS_CAPTURING_DESCRIPTORS:
            self.debug('Deep call to capture_descriptors()')

        this.IS_CAPTURING_DESCRIPTORS = True

        sys_stdout = sys.stdout
        sys_stderr = sys.stderr
        log_files = []

        outputs_stdout = []
        outputs_stderr = []

        # 1. Prepare standard out/err
        if enable_standard_out:
            outputs_stdout.append(sys_stdout)
            outputs_stderr.append(sys_stderr)

        # 2. Prepare logs
        for target_file in target_files:
            subprocess.call(['mkdir', '-p', os.path.dirname(target_file)])

            log_file = open(target_file, 'wb', buffering=0)
            log_file.no_flush = True
            log_files.append(log_file)

            outputs_stdout.append(log_file)
            outputs_stderr.append(log_file)

        # 3. Prepare StringIO
        if stream:
            outputs_stdout.append(stream)
            outputs_stderr.append(stream)

        # 4. Mock
        sys.stdout = StandardOutputReplication(outputs_stdout)
        sys.stderr = StandardOutputReplication(outputs_stderr)

        # 5. Action!
        yield

        # 6. Revert standard out/err
        sys.stdout = sys_stdout
        sys.stderr = sys.stderr

        # 7. Clean up: close all log files
        for log_file in log_files:
            log_file.close()

        this.IS_CAPTURING_DESCRIPTORS = False

    def inherit_silent(self, io: 'SystemIO'):
        self.silent = io.is_silent(consider_ui=False)

    def is_silent(self) -> bool:
        """Is output silent? In silent mode OPTIONAL MESSAGES are not shown"""

        return self.silent

    #
    # Log level - mutable setting
    #
    def set_log_level(self, desired_level_name: str):
        if desired_level_name not in LOG_LEVELS:
            raise Exception('Invalid log level name')

        self.log_level = LOG_LEVELS[desired_level_name]

    def is_log_level_at_least(self, log_level: str) -> bool:
        return self.log_level >= LOG_LEVELS[log_level]

    def get_log_level(self) -> str:
        for name, severity in LOG_LEVELS.items():
            if severity == self.log_level:
                return name

        raise Exception('Unset log level')

    #
    # Standard output/error
    #

    def _stdout(self, text):
        sys.stdout.write(text)

    def _stderr(self, text):
        sys.stderr.write(text)

    def out(self, text):
        """ Standard output """
        self._stdout(text)

    def outln(self, text):
        """ Standard output + newline """
        self.out(text)
        self._stdout("\n")

    def err(self, text):
        """ Standard error """
        self._stderr(text)

    def errln(self, text):
        """ Standard error + newline """
        self.err(text)
        self._stderr("\n")

    def opt_out(self, text):
        """ Optional output - fancy output skipped in --silent mode """

        if not self.is_silent():
            self.out(text)

    def opt_outln(self, text):
        """ Optional output - fancy output skipped in --silent mode + newline """

        if not self.is_silent():
            self.outln(text)

    #
    # Logs
    #

    def debug(self, text):
        """Logger: debug

        """
        if self.log_level >= LEVEL_DEBUG:
            self.log(text, 'debug')

    def info(self, text):
        """Logger: info

        """

        if self.log_level >= LEVEL_INFO:
            self.log(text, 'info')

    def warn(self, text):
        """Logger: warn

        """

        if self.log_level >= LEVEL_WARNING:
            self.log(text, 'warn')

    def error(self, text):
        """Logger: error

        """

        if self.log_level >= LEVEL_ERROR:
            self.log(text, 'error')

    def critical(self, text):
        """Logger: critical

        """

        if self.log_level >= LEVEL_FATAL:
            self.log(text, 'critical')

    def log(self, text, level: str):
        if not self.is_silent():
            current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            level = LOG_LEVEL_FORMATTING_MAPPING[level].replace('%TEXT%', level)

            self.outln("\x1B[2m[%s]\x1B[0m[%s]: \x1B[2m%s\x1B[0m" % (current_time, level, text))

    def print_group(self, text):
        """Prints a colored text inside brackets [text] (optional output)

        """

        self.opt_outln("\x1B[33m[%s]\x1B[0m" % text)

    #
    # Lines and separators
    #

    def print_line(self):
        """Prints a newline

        """

        self.outln('')

    def print_opt_line(self):
        """Prints a newline (optional output)
        """

        self.opt_outln('')

    def print_separator(self):
        """Prints a text separator (optional output)
        """
        self.opt_outln("\x1B[37m%s\x1B[0m" % '-----------------------------------')

    #
    #  Statuses
    #

    def success_msg(self, text):
        """Success message (optional output)
        """

        self.opt_outln("\x1B[92m%s\x1B[0m" % text)

    def error_msg(self, text):
        """Error message (optional output)
        """

        self.opt_outln("\x1B[91m%s\x1B[0m" % text)

    def info_msg(self, text):
        """Informational message (optional output)
        """

        self.opt_outln("\x1B[93m%s\x1B[0m" % text)

    #
    # Standard formatting
    #
    def h1(self, text):
        """Heading #1 (optional output)
        """

        self.opt_outln("\x1B[93m  ##> %s\x1B[0m" % text)

    def h2(self, text):
        """Heading #2 (optional output)
        """

        self.opt_outln("\x1B[93m   ===> %s\x1B[0m" % text)

    def h3(self, text):
        """Heading #3 (optional output)
        """

        self.opt_outln("\x1B[33m    --> %s\x1B[0m" % text)

    def h4(self, text):
        """Heading #3 (optional output)
        """

        self.opt_outln("\x1B[33m     ... %s\x1B[0m" % text)


class SystemIO(IO):
    """ Used for logging outside of tasks """

    _ui = True

    def capture_descriptors(self, target_file: str = None, stream=None, enable_standard_out: bool = True):
        pass

    def set_display_ui(self, ui: bool):
        self._ui = ui

    def is_silent(self, consider_ui: bool = True) -> bool:
        if consider_ui and not self._ui:
            return True

        return self.silent


class NullSystemIO(SystemIO):
    def _stdout(self, text):
        pass

    def _stderr(self, text):
        pass


class BufferedSystemIO(SystemIO):
    _buffer = ''

    def _stdout(self, text):
        self._buffer += text

    def _stderr(self, text):
        self._buffer += text

    def get_value(self):
        return self._buffer

    def clear_buffer(self):
        self._buffer = ''


def clear_formatting(text: str) -> str:
    text = re.sub("\\x1B\[([0-9]+)m", '', text)

    return text
