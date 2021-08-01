RTS-1: Extendable tasks
=======================

Abstract
--------

Most of the existing build tools like GNU Make, SCons, Meson in opinion of RKD developers does not have enough good
possibilities to share tasks across different projects, which means those tools are not scaling well.

Motivation
----------

In order to provide a perfect DevOps tool that will allow sharing the code of universal mechanisms between projects, even organizations
this RKD Tech Specification was designed.

Inspired how it looks in Gradle we decided to create a simplified DevOps tool that will be universal, will allow to install any task set as a Python package
and then use it to manage databases, servers, build projects, generate configs and all other things that could be automated, parametrized.

Rationale
---------

Common practice is to extract complex and universal mechanisms to separate packages, in our case it is a Python package.
Packages can be shared across projects, even organizations, using already good and known mechanism - PyPI/PIP and Virtual Environment.

Inside project structure an already prepared mechanism can be imported from an installed package, then local project tasks can be created
with already prepared configuration that is specific to the local project.

Vocabulary
----------

- `Task`: `Task` that actually runs, can be invoked and will produce result.
- `Base Task`: Task that acts like a template, other `Task` needs to be created from it and properly configured.
- `Decorator`: Marks an extended method that it should be executed instead of parent method, or before parent method, or after parent method. No decorator means replacing parent method. Internally in RKD Core called also `Markers`.


Base tasks vs Customizations
----------------------------

Base Tasks are possible to be defined ONLY as Python classes inside Python modules (modules can be also local).
The actual Tasks, the Customizations are defined in a simplified Python syntax or in YAML document syntax, those cannot be extended again.
Regular Tasks are also possible to be written in pure Python as classes, there are no limits.


**Example of a Task that extends a Base Task, which means it is a Customization of a Base Task:**

```yaml
version: org.riotkit.rkd/yaml/v1
imports:
    - rkd.php.script.PhpScriptTask
tasks:
    :yaml:test:php:
        extends: rkd.php.script.PhpScriptTask
        # @before_parent is a Decorator, there could be only one decorator used
        configure@before_parent: |
            self.version = '7.2-alpine'
        inner_execute@after_parent: |
            print('IM AFTER PARENT')
            return True
        input: |
            # this is a PHP language
            var_dump(getcwd());
            var_dump(phpversion());
```

To create project-specific Base Task that extend other Base Task there is a requirement to define it as a Python class, and do it in a Pythonic way.

**Example of a Base Task that extends other Base Task:**

```python
import os
from typing import Optional

from rkd.core.execution.lifecycle import ConfigurationLifecycleEvent
from rkd.core.standardlib.docker import RunInContainerBaseTask


class PhpScriptTask(RunInContainerBaseTask):
    """
    Execute a PHP code (using a docker container)
    Can be extended - this is a base task.

    Inherits settings from `RunInContainerBaseTask`.

    Configuration:
        script: Path to script to load instead of stdin (could be a relative path)
        version: PHP version. Leave None to use default 8.0-alpine version

    """

    script: Optional[str]
    version: Optional[str]

    def __init__(self):
        super().__init__()
        self.user = 'www-data'
        self.entrypoint = 'sleep'
        self.command = '9999999'
        self.script = None
        self.version = None

    def configure(self, event: ConfigurationLifecycleEvent) -> None:
        # please note: there is parent method called - RunInContainerBaseTask.configure(event)
        super().configure(event)

        self.docker_image = '{image}:{version}'.format(
            image=event.ctx.get_arg_or_env('--image'),
            version=self.version if self.version else event.ctx.get_arg_or_env('--php')
        )

        self.mount(local=os.getcwd(), remote=os.getcwd())
        
    # ...
```

Syntax
------

There exists actually three available syntax styles.

********************************
1. Python Class: Classic syntax
********************************

Classic syntax has no limits, it's main purpose is to define Base Tasks, that could be extended later **due to its native construct could be packaged as PyPI/PIP package.**

```python
import os
from argparse import ArgumentParser
from rkd.core.api.syntax import TaskDeclaration
from rkd.core.api.contract import TaskInterface, ExecutionContext

class GetEnvTask(TaskInterface):
    """Gets environment variable value"""

    def get_name(self) -> str:
        return ':get'

    def get_group_name(self) -> str:
        return ':env'

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--name', '-e', help='Environment variable name', required=True)

    def execute(self, context: ExecutionContext) -> bool:
        self.io().out(os.getenv(context.get_arg('--name'), ''))

        return True


IMPORTS = [
    TaskDeclaration(GetEnvTask())
]
```

***************************
2. Simplified Python syntax
***************************

Allows writing Tasks that extends Base Tasks in a very easy and short manner.

```python
from rkd.core.api.contract import ExecutionContext
from rkd.core.api.syntax import ExtendedTaskDeclaration
from rkd.core.api.decorators import before_parent, without_parent, after_parent, extends
from rkd.core.execution.lifecycle import ConfigurationLifecycleEvent
from rkd.php.script import PhpScriptTask

@extends(PhpScriptTask)
def MyTask():
    @without_parent
    def configure(task: PhpScriptTask, event: ConfigurationLifecycleEvent):
        task.version = '7.2-alpine'
        
    def inner_execute(task: PhpScriptTask, ctx: ExecutionContext):
        print('IM AFTER PARENT')
        return True

    def stdin():
        return """
            var_dump(getcwd());
            var_dump(phpversion());
        """
    
    return [configure, inner_execute, stdin]

IMPORTS = [
    ExtendedTaskDeclaration(name=':php', task=MyTask)
]
```


***********************
3. Document/YAML syntax
***********************

Has similar purpose as `Simplified Python syntax`, but should be simpler for non-programmers like System Administrators, or just for people that likes YAML declarations.

```yaml
version: org.riotkit.rkd/yaml/v1
imports:
    - rkd.php.script.PhpScriptTask
tasks:
    :yaml:test:php:
        extends: rkd.php.script.PhpScriptTask
        configure@before_parent: |
            self.version = '7.2-alpine'
        inner_execute@after_parent: |
            print('IM AFTER PARENT')
            return True
        input: |
            var_dump(getcwd());
            var_dump(phpversion());

    # defining classic shell tasks is easiest with YAML syntax
    :yaml:test:multi:
        steps:
            - |
                #!bash
                echo "Hello world from Bash"
            - |
                #!python
                print("Hello from Python")
            - ps aux
            - ls -la
```

Execute and Inner Execute concept
---------------------------------

- `def execute(ctx: ExecutionContext) -> bool` is a main method that performs action of a task, as a result a boolean should be returned.
- `def inner_execute(ctx: ExecutionContext) -> bool` is a method that OPTIONALLY can be called by implementation of `execute()` method, to perform some e.g., transactional task

Base Tasks can implement a `execute()` and leave a possibility for a Customizations by calling `inner_execute(ctx)` from the inside of `execute()`, but not every Base Task may implement this. You need to carefully read docs for given Base Task.

**What are the cases for inner_execute?**
- execute() launches a docker container, invokes `inner_execute()`, then removes the container. This allows to use the container from inside of `inner_execute(ctx)` method
- execute() prepares required files, then invokes `inner_execute()` to perform some user-defined action, at the end cleans the workspace

Table of method names
---------------------

Despite three different syntax styles, there are slight differences the developer/ops needs to be aware of.

| Simplified Python                                                       | Python Class                                         | YAML                        | Description                                                                     |
|-------------------------------------------------------------------------|------------------------------------------------------|-----------------------------|---------------------------------------------------------------------------------|
| get_steps(task: MultiStepLanguageAgnosticTask) -> List[str]:            | get_steps                                            | steps: [""]                 | List of steps in any language (only if extending MultiStepLanguageAgnosticTask) |
| stdin()                                                                 | -                                                    | input: ""                   | Standard input text                                                             |
| @extends(Class) decorator on a main method                              | class Name(BaseClass)                                | extends: package.name.Class | Which Base Task should be extended                                              |
| execute(task: BaseClassNameTask, ctx: ExecutionContext):                | execute(self, ctx: ExecutionContext)                 | execute: ""                 | Python code to execute                                                          |
| inner_execute(task: BaseClassNameTask, ctx: ExecutionContext):          | inner_execute(self, ctx: ExecutionContext)           | inner_execute: ""           | Python code to execute inside inner_execute (if implemented by Base Task)       |
| compile(task: BaseClassNameTask, event: CompilationLifecycleEvent):     | compile(self, event: CompilationLifecycleEvent):     | -                           | Python code to execute during Context compilation process                       |
| configure(task: BaseClassNameTask, event: ConfigurationLifecycleEvent): | configure(self, event: ConfigurationLifecycleEvent): | configure: ""               | Python code to execute during Task configuration process                        |
| get_description()                                                       | get_description(self)                                | description: ""             | Task description                                                                |
| get_group_name()                                                        | get_group_name()                                     | -                           | Group name                                                                      |
| internal=True in TaskDeclaration                                        | internal=True in TaskDeclaration                     | internal: False             | Is task considered internal? (hidden on :tasks list)                            |
| become in TaskDeclaration (or commandline switch)                       | become in TaskDeclaration (or commandline switch)    | become: root                | Change user for task execution time                                             |
| workdir in TaskDeclaration                                              | workdir in TaskDeclaration                           | workdir: /some/path         | Change working directory for task execution time                                |
| configure_argparse(task: BaseClassNameTask, parser: ArgumentParser)     | configure_argparse(self, parser: ArgumentParser)     | arguments                   | Configure argparse.ArgumentParser object                                        |
