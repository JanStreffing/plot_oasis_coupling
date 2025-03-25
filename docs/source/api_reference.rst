=============
API Reference
=============

FluxPlotter Class
================

.. code-block:: python

    class FluxPlotter:
        def __init__(self, base_dir: str, timestep: int = 0, 
                    remap_higher_res: bool = False, resolution: float = 0.5, 
                    parallel: bool = True, verbose: bool = False)

The main class that handles processing of flux files, generating plots, and creating HTML reports.

Parameters
---------

- **base_dir** (*str*): Base directory containing experiment folders
- **timestep** (*int*): Timestep to process (0-indexed, default: 0)
- **remap_higher_res** (*bool*): Whether to remap to a higher resolution grid
- **resolution** (*float*): Target resolution in degrees (default: 0.5)
- **parallel** (*bool*): Whether to process files in parallel (True) or sequentially (False)
- **verbose** (*bool*): Whether to print verbose debug information

Main Methods
===========

process_folder
-------------

.. code-block:: python

    def process_folder(self, folder_name: str, max_files: int = 0)

Processes all NetCDF files in a specified experiment folder.

Parameters:
- **folder_name** (*str*): Name of the experiment folder to process
- **max_files** (*int*): Maximum number of files to process (0 for all)

generate_html
------------

.. code-block:: python

    def generate_html(self)

Generates an HTML report comparing plots from different experiment folders.

process_file
-----------

.. code-block:: python

    def process_file(self, file_path: str, experiment_name: str)

Processes a single NetCDF file and generates plots.

Parameters:
- **file_path** (*str*): Path to the NetCDF file
- **experiment_name** (*str*): Name of the experiment (folder)

Utility Methods
=============

print_memory_usage
----------------

.. code-block:: python

    def print_memory_usage(self, msg: str = "")

Prints current memory usage information.

Parameters:
- **msg** (*str*): Optional message to print with memory information

reshape_1d_to_2d
--------------

.. code-block:: python

    def reshape_1d_to_2d(self, data: np.ndarray, target_shape: tuple) -> np.ndarray

Reshapes 1D data to 2D based on target shape.

Parameters:
- **data** (*numpy.ndarray*): 1D input data
- **target_shape** (*tuple*): Target 2D shape

Returns:
- 2D numpy array with the reshaped data

remap_to_regular_grid
-------------------

.. code-block:: python

    def remap_to_regular_grid(self, data: np.ndarray, lats: np.ndarray, lons: np.ndarray, 
                             target_resolution: float) -> np.ndarray

Remaps data from a source grid to a regular lat-lon grid.

Parameters:
- **data** (*numpy.ndarray*): Source data
- **lats** (*numpy.ndarray*): Latitude coordinates
- **lons** (*numpy.ndarray*): Longitude coordinates
- **target_resolution** (*float*): Target resolution in degrees

Returns:
- Remapped data on a regular lat-lon grid
