============
Installation
============

Prerequisites
============

To use the OASIS Coupling Flux Visualization tool, you need:

* Python 3.6 or later
* The following Python packages:
    * numpy
    * matplotlib
    * xarray
    * dask
    * cartopy
    * scipy

Environment Setup
================

It's recommended to use a conda environment to manage dependencies:

.. code-block:: bash

    # Create a new conda environment
    conda create -n plot_fluxes python=3.8
    
    # Activate the environment
    conda activate plot_fluxes
    
    # Install required packages
    conda install -c conda-forge numpy matplotlib xarray dask cartopy scipy

Alternatively, you can install the dependencies via pip:

.. code-block:: bash

    pip install numpy matplotlib xarray dask cartopy scipy

Getting the Code
===============

Clone the repository:

.. code-block:: bash

    git clone https://github.com/yourusername/plot_oasis_coupling.git
    cd plot_oasis_coupling

Directory Structure
==================

Set up your directory structure as follows:

.. code-block:: text

    plot_oasis_coupling/
    ├── plot_fluxes.py       # Main script
    ├── README.md            # Project readme
    ├── requirements.txt     # Dependencies
    └── data/
        ├── flux_33/         # Experiment 1 data
        │   └── *.nc         # NetCDF files
        └── flux_34/         # Experiment 2 data
            └── *.nc         # NetCDF files

Note that the data files should be kept separate from the code, in a structured directory as shown above.
