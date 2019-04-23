========================
Team and repository tags
========================

.. image:: https://governance.openstack.org/tc/badges/murano-pkg-check.svg
    :target: https://governance.openstack.org/tc/reference/tags/index.html

.. Change things from this point on

===============================
murano-pkg-check
===============================

Murano package validator tool

After checking out tool from repository easiest method to run tool is to run

.. code-block:: console

  tox -e venv -- murano-pkg-check -h

This command will display help for murano-pkg-validator

If you installed it from PYPI you can use:
.. code-block:: console

  murano-pkg-check -h

To run validator in directory apache-app just run:
.. code-block:: console

  murano-pkg-check apache-app

It will print all errors there are on package.

.. code-block:: console

  murano-pkg-check --discovery murano-apps

Will search for all packages under directory `murano-apps`. It will print all
errors and warnings for all packages found.

* Free software: Apache license
* Documentation: http://docs.openstack.org/developer/murano-pkg-check
* Source: http://opendev.org/openstack/murano-pkg-check
* Bugs: http://bugs.launchpad.net/murano

