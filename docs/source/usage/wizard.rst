Creating installer wizards with RKD
===================================

**Wizard** is a component designed to create comfortable installers, where user has to answer a few questions
to get the task done.


Concept
-------

- User answers questions invoked by :code:`ask()` method calls
- At the end the :code:`finish()` is called, which acts as a commit, saves answers into :code:`.rkd/tmp-wizard.json` by default and into the :code:`.env` file (depends on if to_env=true was specified)
- Next RKD task executed can read :code:`.rkd/tmp-wizard.json` looking for answers, the answers placed in .env are already loaded automatically as part of standard mechanism of environment variables support

Example
-------

.. code:: python

    from rkd.inputoutput import Wizard

    # self is the TaskInterface instance, in Makefile.yaml it would be "this", in Python code it is "self"
    Wizard(self)\
        .ask('Service name', attribute='service_name', regexp='([A-Za-z0-9_]+)', default='redis')\
        .finish()


.. code:: bash

    Service name [([A-Za-z0-9_]+)] [default: redis]:
        -> redis


API
---

.. autoclass:: rkd.inputoutput.Wizard
   :members:
