Docker
======

:docker:tag
~~~~~~~~~~~
.. jinja:: docker_tag
   :file: source/templates/package-usage.rst

Performs a docker-style tagging of an image that is being released - example: 1.0.1 -> 1.0 -> 1 -> latest


**Example of usage:**

.. code:: bash

    rkd :docker:tag --image=quay.io/riotkit/filerepository:3.0.0-RC1 --propagate -rf debug


:docker:push
~~~~~~~~~~~~
.. jinja:: docker_push
   :file: source/templates/package-usage.rst

Does same thing and taking same arguments as **:docker:tag**, one difference - pushing already created tasks.

