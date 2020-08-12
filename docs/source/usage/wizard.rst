.. _Wizard:

Creating installer wizards with RKD
===================================

**Wizard** is a component designed to create comfortable installers, where user has to answer a few questions
to get the task done.


Concept
-------

- User answers questions invoked by :code:`ask()` method calls
- At the end the :code:`finish()` is called, which acts as a commit, saves answers into :code:`.rkd/tmp-wizard.json` by default and into the :code:`.env` file (depends on if to_env=true was specified)
- Next RKD task executed can read :code:`.rkd/tmp-wizard.json` looking for answers, the answers placed in .env are already loaded automatically as part of standard mechanism of environment variables support

Example Wizard
--------------

.. code:: python

    from rkd.api.inputoutput import Wizard

    # self is the TaskInterface instance, in Makefile.yaml it would be "this", in Python code it is "self"
    Wizard(self)\
        .ask('Service name', attribute='service_name', regexp='([A-Za-z0-9_]+)', default='redis')\
        .finish()


.. code:: bash

    Service name [([A-Za-z0-9_]+)] [default: redis]:
        -> redis

**Example of application that is using Wizard to ask interactive questions**

.. image:: https://github.com/riotkit-org/rkd-coop/raw/master/docs/demo.gif

Using Wizard results internally
-------------------------------

Wizard is designed to keep the data on the disk, so you can access it in any other task executed, but this is not mandatory.
You can skip committing changes to disk by not using :code:`finish()` which **is flushing data to json and to .env files.**

Use :code:`wizard.answers` to see all answers that would be put into json file, and :code:`wizard.to_env` to browse all environment variables that would be set in .env if :code:`finish()` would be used.

Example of loading stored values by other task
----------------------------------------------

Wizard stores values into file and into .env file, so it can read it from file after it was stored there.
This allows you to separate Wizard questions into one RKD task, and the rest of logic/steps into other RKD tasks.

.. code:: python

    from rkd.api.inputoutput import Wizard

    # ... assuming that previously the Wizard was completed by user and the finish() method was called ...

    wizard = Wizard(self)
    wizard.load_previously_stored_values()

    print(wizard.answers, wizard.to_env)


API
---

.. autoclass:: rkd.api.inputoutput.Wizard
   :members:
