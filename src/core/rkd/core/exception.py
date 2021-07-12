from typing import List
from jsonschema import ValidationError
from .argparsing.model import TaskArguments


class RiotKitDoException(Exception):
    pass


class HandledExitException(Exception):
    """
    Signal to exit RKD without any message, as the error was already handled
    """


class ContextException(RiotKitDoException):
    pass


class TaskNotFoundException(ContextException):
    pass


# +=================================
# + EXECUTOR and RESOLVER EXCEPTIONS
# +=================================
class TaskExecutionException(RiotKitDoException):
    pass


class InterruptExecution(TaskExecutionException):
    pass


class ExecutionRetryException(TaskExecutionException):
    """Internal signal to retry a task"""

    args: List[TaskArguments]

    def __init__(self, args: List[TaskArguments] = None):
        if args is None:
            args = []

        self.args = args


class TaskResolvingException(TaskExecutionException):
    pass


class AggregatedResolvingFailure(TaskExecutionException):
    def __init__(self, exceptions: List[Exception]):
        self.exceptions = exceptions


# +==================================================
# + EXECUTOR EXCEPTIONS -> Task rescheduling signals
# +==================================================
class ExecutionRescheduleException(TaskExecutionException):
    """Internal signal to put extra task into resolve/schedule queue of TaskResolver"""

    tasks_to_schedule: List[TaskArguments]

    def __init__(self, tasks_to_schedule: List[TaskArguments]):
        self.tasks_to_schedule = tasks_to_schedule


class ExecutionRescueException(ExecutionRescheduleException):
    """Internal signal to call a rescue set of tasks in case of given task fails"""


class ExecutionErrorActionException(ExecutionRescheduleException):
    """Internal signal to call an error notification in case when given task fails"""


# +=============================
# + TASK DECLARATION EXCEPTIONS
# -----------------------------
#   When inputs are invalid
# +=============================
class TaskDeclarationException(ContextException):
    pass


class LifecycleConfigurationException(TaskDeclarationException):
    @classmethod
    def from_invalid_method_used(cls, task_full_name: str, method_names: str) -> 'LifecycleConfigurationException':
        return cls(f'Attributes or methods: {method_names} are not allowed ' +
                   f'to be used in configure() of "{task_full_name}" task. Make sure you are not trying to do ' +
                   'anything tricky. configure() method purpose is to use exposed methods by authors of base task ' +
                   'to customize extended task with custom configuration based on specific logic')


class UndefinedEnvironmentVariableUsageError(TaskDeclarationException):
    pass


class EnvironmentVariableNotUsed(TaskDeclarationException):
    pass


class EnvironmentVariableNameNotAllowed(TaskDeclarationException):
    def __init__(self, var_name: str):
        super().__init__('Environment variable with this name "' + var_name + '" cannot be declared, it probably a' +
                         ' commonly reserved name by operating systems')


class TaskFactoryException(TaskDeclarationException):
    @classmethod
    def from_missing_extends(cls, func):
        raise cls(f'{func} needs to have "extends" parameter defined with an annotation')

    @classmethod
    def from_method_not_allowed_to_be_inherited(cls, method):
        raise cls(f'Method {method} is not allowed to be inherited')

    @classmethod
    def from_method_not_allowed_to_be_defined_for_inheritance(cls, method):
        raise cls(f'Method {method} is not allowed to be defined for inheritance')


class UserInputException(RiotKitDoException):
    pass


class BlockDefinitionLogicError(RiotKitDoException):
    @staticmethod
    def from_both_rescue_and_error_defined():
        return BlockDefinitionLogicError('Block "{0:s}" cannot define both @rescue and @error'.format(task.block().body))


class NotSupportedEnvVariableError(UserInputException):
    pass


class YamlParsingException(ContextException):
    """Logic or syntax errors in makefile.yaml"""

    @classmethod
    def from_subproject_not_a_list(cls):
        return cls('"subprojects" should be a list containing subdirectories to subprojects')

    @classmethod
    def from_not_a_string(cls, key: str):
        return cls(f'"{key}" should be of a string type')


class YAMLFileValidationError(YamlParsingException):
    """Errors related to schema validation"""

    def __init__(self, err: ValidationError):
        super().__init__('YAML schema validation failed at path "%s" with error: %s' % (
            '.'.join(list(map(str, list(err.path)))),
            str(err.message)
        ))


class ParsingException(ContextException):
    """Errors related to parsing YAML/Python syntax"""

    @classmethod
    def from_import_error(cls, import_str: str, class_name: str, error: Exception) -> 'ParsingException':
        return cls(
            'Import "%s" is invalid - cannot import class "%s" - error: %s' % (
                import_str, class_name, str(error)
            )
        )

    @classmethod
    def from_class_not_found_in_module_error(cls, import_str: str, class_name: str,
                                             import_path: str) -> 'ParsingException':
        return cls(
            'Import "%s" is invalid. Class or method "%s" not found in module "%s"' % (
                import_str, class_name, import_path
            )
        )


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


class RuntimeException(RiotKitDoException):
    pass


class MissingInputException(RuntimeException, KeyError):
    def __init__(self, arg_name: str, env_name: str):
        if not env_name:
            super().__init__('"%s" switch not defined' % (arg_name))
            return

        super().__init__('Either "%s" switch not defined, either "%s" was not defined in environment' % (
            arg_name, env_name
        ))


class CommandlineParsingError(RuntimeException):
    @staticmethod
    def from_block_header_parsing_exception(block_header: str) -> 'CommandlineParsingError':
        return CommandlineParsingError('Cannot parse block header "{}"'.format(block_header))

    @staticmethod
    def from_block_modifier_declared_twice(name: str, block_header: str) -> 'CommandlineParsingError':
        return CommandlineParsingError('Cannot declare "{}" twice in block "{}'.format(name, block_header))

    @staticmethod
    def from_block_unknown_modifier(header: str, e: Exception) -> 'CommandlineParsingError':
        return CommandlineParsingError('Block "{}" contains invalid modifier, raised error: {}'.format(header, str(e)))

    @staticmethod
    def from_nested_blocks_not_allowed(token: str, header: str) -> 'CommandlineParsingError':
        return CommandlineParsingError('Nesting blocks "{}" not allowed, attempted inside block "{}"'
                                       .format(token, header))

    @staticmethod
    def from_block_closing_not_found(pos: int):
        return CommandlineParsingError('Parsing exception: Closing character "}" not found for {@ opened at %i' % pos)

    @staticmethod
    def from_block_ending_not_found(block: str):
        return CommandlineParsingError('Parsing exception: Block ending - %s not found' % block)
