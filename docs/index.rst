BSP Python SDK
==============

Official Python SDK for the **Biological Sovereignty Protocol** (BSP).

Installation
------------

.. code-block:: bash

   pip install bsp-sdk

Quick start
-----------

.. code-block:: python

   from bsp_sdk import BSPClient
   import os

   client = BSPClient(
       ieo_domain  = "fleury.bsp",
       private_key = os.environ["BSP_IEO_PRIVATE_KEY"],
       environment = "mainnet",
   )

See ``examples/`` in the source tree for runnable end-to-end flows.

API reference
-------------

.. autosummary::
   :toctree: _autosummary
   :recursive:

   bsp_sdk

Modules
-------

.. toctree::
   :maxdepth: 2

   modules/client
   modules/beo
   modules/ieo
   modules/biorecord
   modules/access
   modules/exchange
   modules/crypto
   modules/types

Indices
-------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
