Python client for `Consul.io <http://www.consul.io/>`_
======================================================

Fork intent
-----------

The origin project https://github.com/cablehead/python-consul is not maintained
since 2018.  As we're not able to get in touch with the maintainer (cablehead)
to merge and release our PRs, we've forked the project in order to continue the
maintenance of the project.  We also renamed the project to be able to upload
on pypi; see https://pypi.org/project/py-consul/

Example
-------

.. code:: python

    import consul

    c = consul.Consul()

    # poll a key for updates
    index = None
    while True:
        index, data = c.kv.get('foo', index=index)
        print data['Value']

    # in another process
    c.kv.put('foo', 'bar')

Installation
------------

::

    pip install py-consul

**Note:** When using py-consul library in environment with proxy server, setting of ``http_proxy``, ``https_proxy`` and ``no_proxy`` environment variables can be required for proper functionality.

Contributing
------------

py-consul is currently maintained by Criteo folks.

Please reach out if you're interested in being a maintainer as well. Otherwise,
open a PR or Issue we'll try and respond as quickly as we're able.

When you create a PR please ensure:

#. To add tests for your new features, if reasonable
#. To add docstrings for new api features you may add
