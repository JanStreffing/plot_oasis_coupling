=====
Usage
=====
 
Command Line Options
===================
 
The script provides several command-line options to customize its behavior:
 
.. code-block:: text
 
    usage: plot_fluxes.py [-h] [--no-remap] [--sequential] [--resolution RESOLUTION]
                          [--max-files MAX_FILES] [--folder FOLDER] [--timestep TIMESTEP]
                          [--verbose] [--compare FOLDER1 FOLDER2]
                          [base_dir]
 
    positional arguments:
      base_dir              Base directory containing experiment folders (default: current directory)
 
    optional arguments:
      -h, --help            Show this help message and exit
      --no-remap            Skip remapping to regular grid
      --sequential          Process files sequentially (default: parallel)
      --resolution RESOLUTION
                            Target resolution in degrees (default: 0.5)
      --max-files MAX_FILES
                            Maximum number of files to process per folder (0 for all)
      --folder FOLDER       Process only this folder (default: all folders)
      --timestep TIMESTEP   Timestep to process (0-indexed, default: 1)
      --verbose             Enable verbose debug output
      --compare FOLDER1 FOLDER2
                            Specify two folders to compare in HTML report
 
Basic Usage
==========
 
To process all experiment folders with default settings:
 
.. code-block:: bash
 
    python plot_fluxes.py
 
To process a specific folder:
 
.. code-block:: bash
 
    python plot_fluxes.py --folder flux_33
 
HTML Report Generation
=====================
 
The script generates HTML reports with two different layouts depending on the number of folders being processed:
 
Single Folder Mode
-----------------
 
When processing a single folder, the script generates an HTML report with a clean single-column layout:
 
.. code-block:: bash
 
    python plot_fluxes.py --folder flux_33
 
This creates a single-column HTML report displaying all plots from the specified folder, organized by plot type (native grid and remapped).
 
Two-Folder Comparison Mode
-------------------------
 
When processing two folders, you can use the compare option to generate a side-by-side comparison HTML report:
 
.. code-block:: bash
 
    python plot_fluxes.py --compare flux_33 flux_34
 
This creates a side-by-side HTML report that directly compares plots from the specified folders. The comparison shows matching variables from both folders for easy visual comparison.
 
Alternatively, you can process multiple folders and let the script automatically compare the first two:
 
.. code-block:: bash
 
    # Process multiple folders - first two will be used for HTML comparison
    python plot_fluxes.py
 
Memory Management
================
 
The script provides options to manage memory usage, which is important when working with large datasets:
 
Resolution Control
-----------------
 
By default, the script uses half-degree (0.5°) remapping which provides a good balance between detail and memory efficiency:
 
.. code-block:: bash
 
    python plot_fluxes.py --resolution 0.5
 
For higher resolution (but increased memory usage):
 
.. code-block:: bash
 
    python plot_fluxes.py --resolution 0.25
 
.. note::
    Quarter-degree (0.25°) remapping consumes significantly more memory and may lead to memory issues with large datasets. For large datasets, it's recommended to stick with the default half-degree remapping.
 
Sequential Processing
--------------------
 
For very large datasets, you can disable parallel processing to reduce memory usage:
 
.. code-block:: bash
 
    python plot_fluxes.py --sequential
 
This processes files one at a time instead of in parallel, which is slower but more memory-efficient.
 
Limiting File Processing
-----------------------
 
During testing or for memory-constrained environments, you can limit the number of files processed:
 
.. code-block:: bash
 
    python plot_fluxes.py --max-files 5
 
This will only process the first 5 files from each experiment folder.
 
Testing and Debugging
====================
 
For debugging or to see detailed information about processing:
 
.. code-block:: bash
 
    python plot_fluxes.py --verbose
 
This shows memory usage, file processing details, and other diagnostic information.
 
Output Structure
===============
 
The script generates the following output:
 
1. **Image files**: Generated in the `output/images/` directory
2. **HTML report**: An overview.html file in the `output/` directory for side-by-side comparison
 
HTML Report
----------
 
The HTML report provides a side-by-side comparison of variables from different experiment folders (e.g., flux_33 and flux_34). It has two tabs:
 
1. **Native Grid**: Shows variables in their original model grids
2. **Remapped**: Shows variables remapped to a regular latitude-longitude grid
 
This makes it easy to visually compare the same variable across different experiments.
