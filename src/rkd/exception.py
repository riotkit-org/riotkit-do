

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
    """Logic or syntax errors in makefile.yaml"""


class DeclarationException(ContextException):
    """Something wrong with the makefile.py/makefile.yaml """


class ContextFileNotFoundException(ContextException):
    """When makefile.py, makefile.yaml, makefile.yml not found (at least one needed)"""

    def __init__(self, path: str):
        super().__init__('The directory "%s" should contain at least makefile.py, makefile.yaml or makefile.yml' % path)


class PythonContextFileNotFoundException(ContextFileNotFoundException):
    """When makefile.py is not found"""

    def __init__(self, path: str):
        super().__init__('Python context file not found at "%s"' % path)


class NotImportedClassException(ContextException):
    """When class was not imported"""

    def __init__(self, exc: ImportError):
        super().__init__(
            'Your Makefile contains a reference to not available or not installed Python module "%s"' % str(exc)
        )


class EnvironmentVariablesFileNotFound(ContextException):
    """.env file specified, but not existing"""

    def __init__(self, path: str, lookup_paths: list):
        super().__init__(
            'Specified file "%s" as environment variable provider does not exist. Looked in: %s' % (
                path, str(lookup_paths)
            )
        )


class RuntimeException(Exception):
    pass


class MissingInputException(RuntimeException):
    def __init__(self, arg_name: str, env_name: str):
        super().__init__('Either "%s" switch not used, either "%s" was not defined in environment' % (
            arg_name, env_name
        ))
