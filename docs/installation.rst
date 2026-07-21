********************************************************************************
Installation
********************************************************************************

Install from source
===================

.. code-block:: bash

    git clone https://github.com/BlockResearchGroup/compas_lca.git
    cd compas_lca
    pip install -e .

For development, install with the "dev" requirements:

.. code-block:: bash

    pip install -e ".[dev]"


LCA database
============

Download the LCA database archive (see the repository README for the download
link), unzip it, and move the extracted folder into the ``data`` directory so
that the following path exists:

.. code-block:: bash

    data/lca_database


Environment configuration
=========================

* Add your LLM API key(s) to a ``.env`` file in the project root.
* Specify project configurations in ``config.yaml``.
* Supported indicator values for ``config.yaml`` are listed in
  ``src/compas_lca/inventory/constants.py`` under ``OBD_INDICATOR_NAME``.
