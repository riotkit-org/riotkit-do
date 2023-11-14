import inspect
import re
import shutil
import sys
import os
import subprocess
from tabulate import tabulate
from io import StringIO
from traceback import format_exc as py_format_exception
from json import dumps as json_encode
from json import loads as json_decode
from copy import deepcopy
from time import sleep
from typing import List, Callable, Union
from getpass import getpass
from contextlib import contextmanager
from datetime import datetime
from ..exception import InterruptExecution


this = sys.modules[__name__]
this.IS_CAPTURING_DESCRIPTORS = False

LEVEL_PRIORITY_INTERNAL = 999
LEVEL_PRIORITY_DEBUG = 37
LEVEL_PRIORITY_INFO = 36
LEVEL_PRIORITY_WARNING = 33
LEVEL_PRIORITY_ERROR = 31
LEVEL_PRIORITY_FATAL = 20

LEVEL_INTERNAL = 'internal'
LEVEL_DEBUG = 'debug'
LEVEL_INFO = 'info'
LEVEL_WARNING = 'warning'
LEVEL_ERROR = 'error'
LEVEL_FATAL = 'fatal'

LOG_LEVELS = {
    LEVEL_INTERNAL: LEVEL_PRIORITY_INTERNAL,
    LEVEL_DEBUG: LEVEL_PRIORITY_DEBUG,
    LEVEL_INFO: LEVEL_PRIORITY_INFO,
    LEVEL_WARNING: LEVEL_PRIORITY_WARNING,
    LEVEL_ERROR: LEVEL_PRIORITY_ERROR,
    LEVEL_FATAL: LEVEL_PRIORITY_FATAL
}

LOG_LEVEL_FORMATTING_MAPPING = {
    'internal': "\x1B[0m%TEXT%\x1B[0m",
    'debug':    "\x1B[0m%TEXT%\x1B[0m",
    'info':     "\x1B[1m%TEXT%\x1B[0m",
    'warn':     "\x1B[93m%TEXT%\x1B[0m",
    'error':    "\x1B[91m%TEXT%\x1B[0m",
    'fatal':    "\x1B[91m\x1B[5m%TEXT%\x1B[0m"
}

OUTPUT_PROCESSOR_CALLABLE_DEF = Callable[[Union[str, bytes], str], Union[str, bytes]]


class ReadableStreamType(object):
    def __init__(self, handle):
        if isinstance(handle, str):
            handle = StringIO(handle)

        self.__handle = handle

    def read(self, n: int = None):
        return self.__handle.read(n)


class StandardOutputReplication(object):
    _out_streams: list
    _fileno: int

    def __init__(self, out_streams: list, fileno: int = None):
        self._out_streams = out_streams
        self._fileno = fileno

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
        return self._fileno

    def flush(self):
        pass


class IO:
    """ Interacting with input and output - stdout/stderr/stdin, logging """

    silent = False
    log_level = LEVEL_PRIORITY_INFO
    output_processors: List[OUTPUT_PROCESSOR_CALLABLE_DEF]

    def __init__(self):
        self.output_processors = []

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
        sys.stdout = StandardOutputReplication(outputs_stdout, sys.stdout.fileno())
        sys.stderr = StandardOutputReplication(outputs_stderr, sys.stderr.fileno())

        # 5. Action!
        yield

        # 6. Revert standard out/err
        sys.stdout = sys_stdout
        sys.stderr = sys_stderr

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
            raise Exception(f'Invalid log level name "{desired_level_name}"')

        self.log_level = LOG_LEVELS[desired_level_name]

    def is_log_level_at_least(self, log_level: str) -> bool:
        return self.log_level >= LOG_LEVELS[log_level]

    def get_log_level(self) -> str:
        for name, severity in LOG_LEVELS.items():
            if severity == self.log_level:
                return name

        raise Exception('Log level not set')

    #
    # Standard output/error
    #

    def _stdout(self, text):
        sys.stdout.write(text)

    def _stderr(self, text):
        sys.stderr.write(text)

    def out(self, text):
        """ Standard output """
        self._stdout(self._process_output(text, 'stdout'))

    def outln(self, text):
        """ Standard output + newline """
        self.out(text + "\n")

    def err(self, text):
        """ Standard error """
        self._stderr(self._process_output(text, 'stderr'))

    def errln(self, text):
        """ Standard error + newline """
        self.err(text + "\n")

    def opt_errln(self, text):
        """ Optional errln() """

        if not self.is_silent():
            self.errln(text)

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

    def internal(self, text):
        """
        Logger: internal
        Should be used only by RKD core for more intensive logging
        """
        if self.log_level < LEVEL_PRIORITY_INTERNAL:
            return

        text = inspect.stack()[1][3] + ' ~> ' + text
        self.log(text, 'internal')

    def internal_lifecycle(self, text):
        """
        Should be used only by RKD core for more intensive logging
        :param text:
        :return:
        """

        if self.log_level < LEVEL_PRIORITY_INTERNAL:
            return

        self.opt_outln("\x1B[93m[LIFECYCLE] %s\x1B[0m " % text)

    def debug(self, text):
        """Logger: debug

        """
        if self.log_level >= LEVEL_PRIORITY_DEBUG:
            self.log(text, 'debug')

    def info(self, text):
        """Logger: info

        """

        if self.log_level >= LEVEL_PRIORITY_INFO:
            self.log(text, 'info')

    def warn(self, text):
        """Logger: warn

        """

        if self.log_level >= LEVEL_PRIORITY_WARNING:
            self.log(text, 'warn')

    def error(self, text):
        """Logger: error

        """

        if self.log_level >= LEVEL_PRIORITY_ERROR:
            self.err_log(text, 'error')

    def critical(self, text):
        """Logger: critical

        """

        if self.log_level >= LEVEL_PRIORITY_FATAL:
            self.err_log(text, 'critical')

    def log(self, text, level: str):
        if not self.is_silent():
            self.outln(self._format_log(text, level))

    def err_log(self, text, level: str):
        if not self.is_silent():
            self.errln(self._format_log(text, level))

    def _format_log(self, text, level: str) -> str:
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        level = LOG_LEVEL_FORMATTING_MAPPING[level].replace('%TEXT%', level)

        return "\x1B[2m[%s]\x1B[0m[%s]: \x1B[2m%s\x1B[0m" % (current_time, level, text)

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

    def print_separator(self, status: bool = None):
        """
        Prints a text separator (optional output)
        """

        color = '37m'

        if status is True:
            color = '92m'
        elif status is False:
            color = '91m'

        self.opt_outln(f"\x1B[{color}%s\x1B[0m" % ("-" * get_terminal_width()))

    #
    #  Statuses
    #

    def success_msg(self, text):
        """Success message (optional output)
        """

        self.opt_outln("\x1B[92m%s\x1B[0m" % text)

    def error_msg(self, text):
        """Error message
        """

        self.errln("\x1B[91m%s\x1B[0m" % text)

    def warn_msg(self, text) -> None:
        """Warning message (optional output)"""

        self.opt_outln("\x1B[33m%s\x1B[0m" % text)

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

    def add_output_processor(self, callback: OUTPUT_PROCESSOR_CALLABLE_DEF):
        """
        Registers a output processing callback
        Each byte outputted by this IO instance will go through a set of registered processors

        Example use cases:
            - Hide sensitive information (secrets)
            - Reformat output
            - Strip long stdouts from commands
            - Change colors
            - Add/remove formatting

        :param callback:
        :return:
        """

        self.output_processors.append(callback)

    def _process_output(self, text, origin: str):
        """
        Process output by passing it through multiple registered processors
        :param text:
        :param origin:
        :return:
        """

        for txt_filter in self.output_processors:
            try:
                processed = txt_filter(text, origin)

                if type(processed) != str:
                    raise Exception('Output processor must return a str')

                text = processed

            # do not allow exceptions in core output buffering module, unless we are debugging
            except Exception:
                if self.log_level >= LEVEL_PRIORITY_DEBUG:
                    raise

                pass

        return text

    @staticmethod
    def format_table(header: list, body: list, tablefmt: str = "simple",
                     floatfmt: str = 'g',
                     numalign: str = "decimal",
                     stralign: str = "left",
                     missingval: str = '',
                     showindex: str = "default",
                     disable_numparse: bool = False,
                     colalign: str = None):

        """Renders a table

        Parameters:
            header:
            body:
            tablefmt:
            floatfmt:
            numalign:
            stralign:
            missingval:
            showindex:
            disable_numparse:
            colalign:

        Returns:
            Formatted table as string
        """

        return tabulate(body, headers=header, floatfmt=floatfmt, numalign=numalign, tablefmt=tablefmt,
                        stralign=stralign, missingval=missingval, showindex=showindex,
                        disable_numparse=disable_numparse, colalign=colalign)


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


class Wizard(object):
    _max_retries: int = 3
    answers: dict
    io: 'IO'
    task: 'TaskInterface'
    to_env: dict
    sleep_time = 1
    filename: str

    def __init__(self, task: 'TaskInterface', filename: str = 'tmp-wizard.json'):
        self.answers = {}
        self.task = task
        self.io = task.io()
        self.to_env = {}
        self.filename = filename

    def ask(self, title: str, attribute: str, regexp: str = '', to_env: bool = False, default: str = None,
            choices: list = [], secret: bool = False) -> 'Wizard':
        """Asks user a question

        Usage:
            .. code:: python

                wizard = Wizard(self)
                wizard.ask('In which year the Spanish social revolution has begun?',
                           attribute='year',
                           choices=['1936', '1910'])
                wizard.finish()
        """

        retried = 0
        value = None
        full_text_to_ask = title

        if choices and regexp:
            raise Exception('Please choose between regexp and choices validation.')

        if regexp:
            full_text_to_ask += " [%s]" % regexp

        if default:
            full_text_to_ask += " [default: %s]" % default

        if choices:
            full_text_to_ask += " [%s]" % ', '.join(choices)

        full_text_to_ask += ": "

        while value is None or not self.is_valid(value, regexp, choices):
            self.io.out(full_text_to_ask + "\n -> ")
            value = self.input(secret=secret)

            if default and not value.strip():
                value = default

            if retried >= self._max_retries:
                raise InterruptExecution('Invalid value given')

            if self.is_valid(value, regexp):
                break

            retried += 1
            sleep(self.sleep_time)

        if to_env:
            self.to_env[attribute] = value
            return self

        self.answers[attribute] = value
        return self

    def input(self, secret: bool = False):
        """
        (Internal) Extracted for unit testing to make testing easier
        """

        if os.getenv('__WIZARD_INPUT'):
            return os.getenv('__WIZARD_INPUT')

        if secret:
            return getpass(prompt='')

        return input()

    @staticmethod
    def is_valid(value: any, regexp: str = '', choices: list = []):
        if choices:
            return value in choices

        if regexp:
            return re.match(regexp, value) is not None

        return True

    def load_previously_stored_values(self):
        """Load previously saved values"""

        if os.path.isfile('.rkd/' + self.filename):
            with open('.rkd/' + self.filename, 'rb') as f:
                self.answers = json_decode(f.read())

        self.to_env = deepcopy(os.environ)

    def finish(self) -> 'Wizard':
        """Commit all pending changes into json and .env files"""

        self.io.info('Writing to .rkd/' + self.filename)
        with open('.rkd/' + self.filename, 'wb') as f:
            f.write(json_encode(self.answers).encode('utf-8'))

        self.io.info('Writing to .env')
        for attribute, value in self.to_env.items():
            self.task.rkd(
                [':env:set', '--name="%s"' % attribute, '--value="%s"' % value],
                verbose=False,
                capture=True
            )

        return self


def clear_formatting(text: str) -> str:
    text = re.sub('\x1B\\[([0-9]+)m', '', text)

    return text


def output_formatted_exception(exc: Exception, title: str, io: IO):
    """Formats a catched exception and displays as user-friendly by default (without a stack trace)

    When at least there is a "debug" level of error reporting, then an original stack trace would be displayed
    Everything goes through the RKD's IO, not directly to the stdout/stderr. The stderr is used there naturally.
    """

    try:
        io.errln('During "%s" a critical error happened' % title)
        io.print_line()

        if io.is_log_level_at_least('debug'):
            io.errln(py_format_exception())
            return

        cause = exc.__cause__

        while cause is not None:
            io.errln('\x1B[91m(Caused by) %s: \x1B[93m%s\x1B[0m' % (
                cause.__class__.__name__,
                indent_new_lines(str(cause), 4)
            ))

            cause = cause.__cause__

        io.errln('\x1B[91m%s: \x1B[93m%s\x1B[0m' % (exc.__class__.__name__, indent_new_lines(str(exc), 4)))
        io.print_line()
        io.errln('\x1B[37mRetry with "-rl debug" switch before failed task to see stacktrace\x1B[0m')

    except Exception:
        print('FATAL: During exception formatting there was an unrecoverable error')
        print(py_format_exception())
        sys.exit(1)

    return


def indent_new_lines(text: str, num: int = 4):
    """Inserts spaces at the beginning of each new line"""

    return text.replace("\n", "\n" + (" " * num))


class UnbufferedStdout(object):
    """Executes flush() after each write"""

    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def writelines(self, datas):
        self.stream.writelines(datas)
        self.stream.flush()

    def fileno(self):
        return self.stream.fileno()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


def get_environment_copy() -> dict:
    """
    Get a securely copied environment variables copy without allowing to modify the global state
    """

    return dict(deepcopy(os.environ))


# reused from PyTest
def get_terminal_width() -> int:
    width, _ = shutil.get_terminal_size(fallback=(80, 24))

    # The Windows get_terminal_size may be bogus, let's sanify a bit.
    if width < 40:
        width = 80

    return width
