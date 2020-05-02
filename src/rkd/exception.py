

class ContextException(Exception):
    pass


class TaskNotFoundException(ContextException):
    pass


class InterruptExecution(Exception):
    pass


class TaskException(ContextException):
    pass


class UndefinedEnvironmentVariableUsageError(TaskException):
    pass


class UserInputException(Exception):
    pass


class NotSupportedEnvVariableError(UserInputException):
    pass

