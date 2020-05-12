

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


class EnvironmentVariableNotUsed(TaskException):
    pass


class UserInputException(Exception):
    pass


class NotSupportedEnvVariableError(UserInputException):
    pass


class YamlParsingException(ContextException):
    """ Logic or syntax errors in makefile.yaml """


class DeclarationException(ContextException):
    """ Something wrong with the makefile.py/makefile.yaml """
