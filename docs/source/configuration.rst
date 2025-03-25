=============
Configuration
=============

Default Settings
==============

The script comes with sensible defaults optimized for most use cases:

- **Resolution**: 0.5° remapping (balanced between detail and memory efficiency)
- **Processing Mode**: Parallel (faster but uses more memory)
- **Timestep**: 1 (second timestep, which is often the first "real" timestep after initialization)
- **Output HTML**: overview.html

These defaults work well for most datasets, but can be customized through command line arguments.

Customizing Processing
====================

Resolution
---------

The resolution parameter controls the grid cell size for remapping:

.. code-block:: bash

    # Half-degree grid (default, balanced approach)
    python plot_fluxes.py --resolution 0.5
    
    # Quarter-degree grid (higher detail but significantly more memory)
    python plot_fluxes.py --resolution 0.25

.. warning::
    Quarter-degree (0.25°) remapping requires substantially more memory. For large datasets with limited memory, stick with half-degree remapping.

Processing Mode
-------------

You can switch between parallel and sequential processing:

.. code-block:: bash

    # Sequential processing (reduces memory usage for large datasets)
    python plot_fluxes.py --sequential

Timestep Selection
----------------

By default, the script processes timestep 1 (second timestep). You can select a different timestep:

.. code-block:: bash

    # Process the first timestep (index 0)
    python plot_fluxes.py --timestep 0
    
    # Process the fifth timestep (index 4)
    python plot_fluxes.py --timestep 4

Limiting File Count
-----------------

For testing or to reduce processing time/memory usage:

.. code-block:: bash

    # Process only 5 files per experiment folder
    python plot_fluxes.py --max-files 5

Advanced Configuration
====================

For more advanced customization, you can modify the script directly:

Colormap Customization
--------------------

To change the colormaps used for different variables, modify the ``_create_plot`` method in the script:

.. code-block:: python

    # Example of customizing colormaps (in the _create_plot method)
    if 'temp' in var_name or 'sst' in var_name:
        cmap = 'coolwarm'  # blue-red for temperature
    elif 'prec' in var_name:
        cmap = 'Blues'     # blue scale for precipitation
    else:
        cmap = 'viridis'   # default colormap

Projection Customization
----------------------

To change the map projection, modify the ``_create_plot`` method:

.. code-block:: python

    # Example of changing the map projection
    plt.figure(figsize=(10, 6))
    ax = plt.axes(projection=ccrs.Robinson())  # Use Robinson projection instead of PlateCarree
