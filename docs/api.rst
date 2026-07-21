********************************************************************************
API Reference
********************************************************************************

.. figure:: /_images/data_model_containers.png
   :figclass: figure
   :class: figure-img img-fluid

   The two container types and their shared Matching Core:
   :doc:`compas_lca.model <api/compas_lca.model>` holds the building side
   (BuildingElement objects extracted from IFC and other model sources),
   :doc:`compas_lca.inventory <api/compas_lca.inventory>` holds the
   environmental side (InventoryItem objects extracted from EPDs), and
   :doc:`compas_lca.matching_core <api/compas_lca.matching_core>` defines the
   shared schema on which filtering and matching operate.

.. toctree::
    :maxdepth: 1

    api/compas_lca.project
    api/compas_lca.model
    api/compas_lca.inventory
    api/compas_lca.matching_core
