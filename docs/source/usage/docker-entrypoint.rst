Docker entrypoints under control
================================

RKD has enough small footprint so that it can be used as an entrypoint in docker containers.
There are a few features that are making RKD very attractive to use in this role.

Environment variables
---------------------

Defined commandline :code:`--my-switch` can have optionally overridden value with environment variable. In docker it can help easily adjusting default values.

**Task needs to create an explicit declaration of environment variable:**

.. code:: python

    def get_declared_envs(self) -> Dict[str, ArgumentEnv]:
        return {
            'MY_SWITCH': ArgumentEnv(name='MY_SWITCH', switch='--switch-name', default=''),
        }

.. code:: python

    def execute(self, ctx: ExecutionContext) -> bool:
        # this one will look for a switch value, if switch has default value, then it will look for an environment variable
        ctx.get_arg_or_env('--my-switch')

Arguments propagation
---------------------

When setting :code:`ENTRYPOINT ["rkd", ":entrypoint"]` everything that will be passed as docker's CMD will be passed to rkd, so additional tasks and arguments can be appended.

Tasks customization
-------------------

It is a good practice to split your entrypoint into multiple tasks executed one-by-one.
This gives you a possibility to create new :code:`makefile.yaml/py` in any place and modify :code:`RKD_PATH` environment variable to add additional tasks or replace existing.
The RKD_PATH has always higher priority than current :code:`.rkd` directory.

**Possible options:**

- Create a bind-mount volume with additional :code:`.rkd/makefile.yaml`, add :code:`.rkd/makefile.yaml` into container and set RKD_PATH to point to :code:`.rkd` directory
- Create new docker image having original in :code:`FROM`, add :code:`.rkd/makefile.yaml` into container and set RKD_PATH to point to :code:`.rkd` directory

Massive files rendering with JINJA2
-----------------------------------

:code:`:j2:directory-to-directory` is a specially designed task to render JINJA2 templates recursively preserving a directory structure.
You can create for example :code:`templates/etc/nginx/nginx.conf.j2` and render :code:`./templates/etc` into :code:`/etc` with all files being copied on the fly.

**All jinja2 templates will have access to environment variables - with templating syntax you can define very advanced configuration files**

Privileges dropping
-------------------

Often in entrypoint there are cache/uploads permissions corrected, so the :code:`root` user is used. To migrate the application, to run the webserver the privileges could be dropped.

**Solutions:**

- In YAML syntax each task have a possible field to use: :code:`become: user-name-here`
- In Python class TaskInterface has method :code:`get_become_as()` that should return empty string or a username to use sudo with
- In commandline there is a switch :code:`--become=user-name-here` that can be used with most of the tasks
