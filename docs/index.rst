********************************************************************************
compas_lca
********************************************************************************

.. rst-class:: lead

AI-based Life Cycle Assessment (LCA) report generation for IFC building models.

``compas_lca`` normalizes building data (from IFC) and environmental data (EPDs)
into a unified schema — the *Matching Core* — that enables precise, customizable,
and deterministic matching based on semantic and functional constraints.

.. figure:: /_images/matching_overview.png
   :figclass: figure
   :class: figure-img img-fluid

   Building elements and inventory items are both extracted into a shared
   Matching Core, on which deterministic constraint matching operates.

In conventional BIM and environmental data schemas, critical classification and
attribute information is distributed across semi-structured and highly variable
representations. ``compas_lca`` extracts and consolidates relevant attributes
into an overlapping normalized format, enabling deterministic building-element
to EPD matching and reproducible LCA report generation.


Table of Contents
=================

.. toctree::
   :maxdepth: 3
   :titlesonly:

   Introduction <self>
   installation
   tutorial
   api
   license


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
