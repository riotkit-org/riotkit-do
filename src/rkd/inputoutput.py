
from contextlib import contextmanager
import sys

this = sys.modules[__name__]
this.IS_CAPTURING_DESCRIPTORS = False

LEVEL_DEBUG = 37
LEVEL_INFO = 36
LEVEL_WARNING = 33
LEVEL_ERROR = 31
LEVEL_FATAL = 41

LOG_LEVELS = {
    'debug': LEVEL_DEBUG,
    'info': LEVEL_INFO,
    'warning': LEVEL_WARNING,
    'error': LEVEL_ERROR,
    'fatal': LEVEL_FATAL
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
                stream.write(buf.encode('utf-8'))

    def flush(self):
        pass


class IO:
    """ Interacting with input and output - stdout/stderr/stdin, logging """

    silent = False
    log_level = LEVEL_INFO

    @contextmanager
    def capture_descriptors(self, target_file: str = None):
        """ Capture stdout and stderr per task """

        if this.IS_CAPTURING_DESCRIPTORS:
            self.warn('Deep call to capture_descriptors() will be ignored')
            return False

        this.IS_CAPTURING_DESCRIPTORS = True

        sys_stdout = sys.stdout
        sys_stderr = sys.stderr
        log_file = None

        if target_file:
            log_file = open(target_file, 'wb')
            sys.stdout = StandardOutputReplication([sys_stdout, log_file])
            sys.stderr = StandardOutputReplication([sys_stderr, log_file])
        else:
            sys.stdout = StandardOutputReplication([sys_stdout])
            sys.stderr = StandardOutputReplication([sys_stderr])

        yield
        sys.stdout = sys_stdout
        sys.stderr = sys.stderr

        if target_file:
            log_file.close()

        this.IS_CAPTURING_DESCRIPTORS = False

    #
    # Log level - mutable setting
    #
    def set_log_level(self, desired_level_name: str):
        if desired_level_name not in LOG_LEVELS:
            raise Exception('Invalid log level name')

        self.log_level = LOG_LEVELS[desired_level_name]

    def get_log_level(self) -> str:
        for name, severity in LOG_LEVELS.items():
            if severity == self.log_level:
                return name

        raise Exception('Unset log level')

    #
    # Standard output/error
    #

    def out(self, text):
        """ Standard output """
        sys.stdout.write(text)

    def outln(self, text):
        """ Standard output + newline """
        self.out(text)
        sys.stdout.write("\n")

    def err(self, text):
        """ Standard error """
        sys.stderr.write(text)

    def errln(self, text):
        """ Standard error + newline """
        self.err(text)
        sys.stderr.write("\n")

    def opt_out(self, text):
        """ Optional output - fancy output skipped in --silent mode """

        if not self.silent:
            self.out(text)

    def opt_outln(self, text):
        """ Optional output - fancy output skipped in --silent mode + newline """

        if not self.silent:
            self.outln(text)

    #
    # Logs
    #

    def debug(self, text):
        if self.log_level >= LEVEL_DEBUG:
            self.log(text)

    def info(self, text):
        if self.log_level >= LEVEL_INFO:
            self.log(text)

    def warn(self, text):
        if self.log_level >= LEVEL_WARNING:
            self.log(text)

    def error(self, text):
        if self.log_level >= LEVEL_ERROR:
            self.log(text)

    def critical(self, text):
        if self.log_level >= LEVEL_FATAL:
            self.log(text)

    def log(self, text):
        if not self.silent:
            self.outln(text)

    def print_group(self, text):
        self.opt_outln("\x1B[33m[%s]\x1B[0m" % text)

    #
    # Lines and separators
    #

    def print_line(self):
        self.outln('')

    def print_opt_line(self):
        self.opt_outln('')

    def print_separator(self):
        self.opt_outln("\x1B[37m%s\x1B[0m" % '-----------------------------------')

    #
    #  Statuses
    #

    def success_msg(self, text):
        self.opt_outln("\x1B[92m%s\x1B[0m" % text)

    def error_msg(self, text):
        self.opt_outln("\x1B[91m%s\x1B[0m" % text)

    def info_msg(self, text):
        self.opt_outln("\x1B[93m%s\x1B[0m" % text)


class SystemIO(IO):
    """ Used for logging outside of tasks """

    def capture_descriptors(self, target_file: str = None):
        pass
