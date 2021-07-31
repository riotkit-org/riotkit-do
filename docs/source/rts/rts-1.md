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
The actual Tasks, the Customizations are defined in simplified Python syntax or in YAML document syntax, those cannot be extended again.

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
