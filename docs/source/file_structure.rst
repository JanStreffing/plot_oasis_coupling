=============
File Structure
=============

Input Files
==========

The script processes NetCDF files from OASIS coupling experiments. These files should be organized in a specific directory structure:

.. code-block:: text

    base_directory/
    ├── flux_33/           # First experiment folder
    │   ├── A_Qns_oce_oifs_01.nc
    │   ├── prec_oce_fesom_02.nc
    │   └── ...
    └── flux_34/           # Second experiment folder
        ├── A_Evap_OpenIFS_02.nc
        ├── sst_feom_fesom_07.nc
        └── ...

File Naming Convention
---------------------

The NetCDF filenames follow a specific convention:

.. code-block:: text

    [variable_name]_[component]_[numerical_suffix].nc

For example:
- ``A_Qns_oce_oifs_01.nc``
- ``prec_oce_fesom_02.nc``

.. note::
    The numerical suffixes (e.g., ``_01``, ``_02``) represent OASIS coupling order, not timesteps.

Output Structure
==============

The script generates output in the following directory structure:

.. code-block:: text

    base_directory/
    └── output/
        ├── images/          # Generated plot images
        │   ├── flux_33_A_Qns_oce.png
        │   ├── flux_33_A_Qns_oce_0.5deg.png
        │   ├── flux_34_A_Evap.png
        │   ├── flux_34_A_Evap_0.5deg.png
        │   └── ...
        └── overview.html    # HTML comparison report

Image Naming Convention
----------------------

The generated image files follow this naming convention:

- Native grid plots: ``[experiment]_[variable_name].png``
- Remapped plots: ``[experiment]_[variable_name]_[resolution]deg.png``

For example:
- ``flux_33_A_Qns_oce.png`` - Native grid plot
- ``flux_33_A_Qns_oce_0.5deg.png`` - Remapped to 0.5° grid

HTML Report
----------

The HTML report (``overview.html``) provides:

1. Side-by-side comparisons of the same variables from different experiment folders
2. Tabs for switching between native grid plots and remapped plots

This structure makes it easy to visually compare variables between different experiments while maintaining a clear organization.
