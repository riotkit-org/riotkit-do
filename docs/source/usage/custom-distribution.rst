Custom distribution
===================

RiotKit Do can be used as a transparent framework for writing tasks for various usage, especially for specialized usage.
To simplify usage for end-user RKD allows to create a custom distribution.


**Custom distribution allows to:**

- Define custom 'binary' name eg. "harbor" instead of "rkd"
- Hide unnecessary tasks in custom 'binary' (filter by groups - whitelist)
- Make shortcuts to tasks: Skip writing group name, make a group name to be appended by default


Example
~~~~~~~

.. code:: python

    import os
    from rkd import main as rkd_main

    def env_or_default(env_name: str, default: str):
        return os.environ[env_name] if env_name in os.environ else default

    def main():
        os.environ['RKD_WHITELIST_GROUPS'] = env_or_default('RKD_WHITELIST_GROUPS', ':env,:harbor,')
        os.environ['RKD_ALIAS_GROUPS'] = env_or_default('RKD_ALIAS_GROUPS', '->:harbor')
        os.environ['RKD_UI'] = env_or_default('RKD_UI', 'false')
        rkd_main()


    if __name__ == '__main__':
        main()


.. code:: bash

    $ harbor :tasks
    [global]
    :sh                                               # Executes shell scripts
    :exec                                             # Spawns a shell process
    :init                                             # :init task is executing ALWAYS. That's a technical, core task.
    :tasks                                            # Lists all enabled tasks
    :version                                          # Shows version of RKD and of all loaded tasks

    [harbor]
    :compose:ps                                       # List all containers
    :start                                            # Create and start containers
    :stop                                             # Stop running containers
    :remove                                           # Forcibly stop running containers and remove (keeps volumes)
    :service:list                                     # Lists all defined containers in YAML files (can be limited by --profile selector)
    :service:up                                       # Starts a single service
    :service:down                                     # Brings down the service without deleting the container
    :service:rm                                       # Stops and removes a container and it's images
    :pull                                             # Pull images specified in containers definitions
    :restart                                          # Restart running containers
    :config:list                                      # Gets environment variable value
    :config:enable                                    # Enable a configuration file - YAML
    :config:disable                                   # Disable a configuration file - YAML
    :prod:gateway:reload                              # Reload gateway, regenerate missing SSL certificates
    :prod:gateway:ssl:status                          # Show status of SSL certificates
    :prod:gateway:ssl:regenerate                      # Regenerate all certificates with force
    :prod:maintenance:on                              # Turn on the maintenance mode
    :prod:maintenance:off                             # Turn on the maintenance mode
    :git:apps:update                                  # Fetch a git repository from the remote
    :git:apps:update-all                              # List GIT repositories
    :git:apps:set-permissions                         # Make sure that the application would be able to write to allowed directories (eg. upload directories)
    :git:apps:list                                    # List GIT repositories

    [env]
    :env:get                                          # Gets environment variable value
    :env:set                                          # Sets environment variable in the .env file


    Use --help to see task environment variables and switches, eg. rkd :sh --help, rkd --help


**Notices for above example:**

- No need to type eg. :harbor:config:list - just :config:list (RKD_ALIAS_GROUPS used)
- No "rkd" group is displayed (RKD_WHITELIST_GROUPS used)
- There is no information about task name (RKD_UI used)


Read more in :ref:`global environment variables`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
