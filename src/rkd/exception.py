

class ContextException(Exception):
    pass


class TaskNotFoundException(ContextException):
    pass


class InterruptExecution(Exception):
    pass
