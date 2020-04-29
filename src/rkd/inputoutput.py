
from contextlib import contextmanager
import sys

this = sys.modules[__name__]
this.IS_CAPTURING_DESCRIPTORS = False


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
    silent = False

    @contextmanager
    def capture_descriptors(self, target_file: str = None):
        """ Capture stdout and stderr per task """

        if this.IS_CAPTURING_DESCRIPTORS:
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

    def out(self, text):
        print(text)

    def info(self, text):
        self.log(text)

    def log(self, text):
        if not self.silent:
            print(text)


class SystemIO(IO):
    """ Used for logging outside of tasks """

    def capture_descriptors(self, target_file: str = None):
        pass
