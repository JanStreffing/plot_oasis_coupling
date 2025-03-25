================================
OASIS Coupling Flux Visualization
================================

A Python-based visualization tool for OASIS coupling fluxes from climate models.

.. image:: https://img.shields.io/badge/Python-3.6+-blue.svg
   :target: https://www.python.org/downloads/

Overview
========

This tool enables visualization and comparison of OASIS coupling fluxes from climate model experiments. 
It processes netCDF files containing flux data, creates plots for both native grid and remapped 
versions, and generates an HTML report for easy visual comparison between different experiments.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   usage
   configuration
   file_structure
   api_reference
   performance

Features
========

* Process NetCDF files from multiple experiment folders
* Generate visualizations of native grid data
* Remap data to regular lat-lon grids for better visualization
* Create side-by-side HTML comparisons between experiments
* Memory-efficient processing for large datasets
* Support for parallel processing of files

Quick Start
===========

Install the required dependencies:

.. code-block:: bash

   pip install -r requirements.txt

Run the script with default settings:

.. code-block:: bash

   python plot_fluxes.py

To specify a specific experiment folder:

.. code-block:: bash

   python plot_fluxes.py --folder flux_33

For more options, see the :doc:`usage` page.

License
=======

This project is licensed under the MIT License - see the LICENSE file for details.

Indices and tables
=================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
