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

Status
------

There's a few API endpoints still to go to expose all features available in
Consul v0.6.0. If you need an endpoint that's not in the documentation, just
open an issue and I'll try and add it straight away.

Contributing
------------

py-consul is currently maintained by criteo folks.

Please reach out if you're interested in being a maintainer as well. Otherwise,
open a PR or Issue we'll try and respond as quickly as we're able.

Issue Labels
~~~~~~~~~~~~

:today!: Some triaging is in progress and this issue should be taken care of in
         a couple of hours!

:priority: There's a clear need to address this issue and it's likely a core
           contributor will take it on. Opening a PR for these is greatly
           appreciated!

:help wanted: This issue makes sense and would be useful. It's unlikely a core
              contributor will get to this though, so if you'd like to see it
              addressed please open a PR.

:question: The need for the issue isn't clear or needs clarification, so please
           follow up.  Issues in this state for a few months, without
           responses will likely will be closed.

PRs
~~~

Pull requests are very much appreciated! When you create a PR please ensure:

#. All current tests pass, including flake8
#. To add tests for your new features, if reasonable
#. To add docstrings for new api features you add and if needed link to these
   docstrings from the sphinx documentation
