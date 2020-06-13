RKD - RiotKit DO
================

.. image:: ./docs/background.png


.. image:: https://api.travis-ci.com/riotkit-org/riotkit-do.svg?branch=master
.. image:: https://img.shields.io/badge/stability-stable-green.svg
.. image:: https://img.shields.io/github/v/release/riotkit-org/riotkit-do?include_prereleases   :alt: GitHub release (latest by date including pre-releases)
.. image:: https://img.shields.io/pypi/v/rkd   :alt: PyPI


Task executor - balance between Makefile and Gradle [see documentation_], designed with :heart: by RiotKit for DevOps.

Stop doing hacks in Makefile, use Python snippets for advanced usage, for the rest use simple few lines of Bash, share code between your projects using Python Packages.

.. code:: bash

    # 1) via PIP
    pip install rkd

    # 1) via PIPENV
    pipenv install rkd

    # 2) rkd :rkd:create-structure

Please check available releases there: https://pypi.org/project/rkd/#history

**Goals:**

- Define tasks as simple as in Makefile
- Reuse code as simple as in Gradle (using extensions that provides tasks. Extensions are installable from PIP)
- Simple configuration in Python
- Write tasks code in Python as simple as possible

Rules
-----

-  No hooks eg. task.executeAfter(otherTask), no complex dependencies
-  No in-memory state between tasks. State could be only changed in files/database/kv-store like it is in other build systems
-  No dynamic tasks names eg. by turning on Publish component it should
   not create tasks eg. :publishIWAToDockerRegistry (where IWA is the
   project name)
-  Don't pack too many features into the core, do this in external modules. Keep the RKD core clean!
-  Full static analysis, you can work on makefile.py and on task's code in PyCharm with full code completion!
-  Do early validation. Runtime validation for long running builds is a pain-in-the-ass for the user.
-  Show clear error messages as much as it is possible. Task not found? Tell the user - do not leave a stack trace. Import error in makefile.py? Tell the user + add stack trace. RESPECT TIME OF ALL OF US! :)
-  Do not overuse libraries in RKD core - it must be installable in any environment, including Docker. Libraries count should be small, and the libraries cannot depend on GCC/G++

Documentation
-------------

Please read the documentation_ here_.

.. _documentation: https://riotkit-do.readthedocs.io/en/latest/
.. _here: https://riotkit-do.readthedocs.io/en/latest/

From authors
------------

We are grassroot activists for social change, so we created RKD especially in mind for those fantastic initiatives:

- RiotKit (https://riotkit.org)
- International Workers Association (https://iwa-ait.org)
- Anarchistyczne FAQ (http://anarchizm.info) a translation of Anarchist FAQ (https://theanarchistlibrary.org/library/the-anarchist-faq-editorial-collective-an-anarchist-faq)
- Federacja Anarchistyczna (http://federacja-anarchistyczna.pl)
- Związek Syndykalistów Polski (https://zsp.net.pl) (Polish section of IWA-AIT)
- Komitet Obrony Praw Lokatorów (https://lokatorzy.info.pl)
- Solidarity Federation (https://solfed.org.uk)
- Priama Akcia (https://priamaakcia.sk)

Special thanks to `Working Class History <https://twitter.com/wrkclasshistory>`_ for very powerful samples that we could use in our unit tests.
