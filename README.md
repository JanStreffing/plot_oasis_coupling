# OASIS Coupling Flux Visualization

[![Documentation Status](https://readthedocs.org/projects/plot-oasis-coupling/badge/?version=latest)](https://plot-oasis-coupling.readthedocs.io/en/latest/?badge=latest)

A tool for visualizing and comparing OASIS coupling fields between different model versions. This utility processes flux data from OASIS-coupled climate models and generates side-by-side comparisons.

## Features

- Process NetCDF flux data from OASIS-coupled models
- Create visualizations in both native grid and remapped formats
- Generate HTML reports with optimized layouts:
  - Single folder mode: Clean single-column layout for individual experiment visualization
  - Comparison mode: Side-by-side layout for direct visual comparison between two experiments
- Memory-optimized for large climate datasets (uses 0.5° remapping by default)
- Options for sequential processing to manage memory usage

## Documentation

Complete documentation is available at [plot-oasis-coupling.readthedocs.io](https://plot-oasis-coupling.readthedocs.io/).

## Installation

```bash
# Clone the repository
git clone https://github.com/JanStreffing/plot_oasis_coupling.git
cd plot_oasis_coupling

# Install required dependencies
pip install numpy matplotlib xarray cartopy dask scipy
```

## Quick Start

```bash
# Process all experiment folders with default settings
python plot_fluxes.py

# Use sequential processing for large datasets (reduces memory usage)
python plot_fluxes.py --sequential

# Process a specific folder (generates single-column HTML report)
python plot_fluxes.py --folder flux_33

# Process and compare specific folders (generates side-by-side HTML report)
python plot_fluxes.py --compare flux_33 rnffix

# Process multiple folders automatically (first two will be compared in HTML report)
python plot_fluxes.py
```

## Command Line Arguments

- `--folder`: Specify which folder to process. Displays that folder in a single-column layout HTML report.
- `--compare`: Specify two folders to compare in a side-by-side HTML report (e.g., `--compare flux_33 rnffix`).
- `--sequential`: Process files sequentially instead of in parallel (recommended for large datasets to avoid memory issues)
- `--no-remap`: Disable remapping to higher resolution grid
- `--resolution`: Target resolution in degrees (default: 0.5)
- `--max-files`: Maximum number of files to process per folder (0 for all)
- `--timestep`: Timestep to process (0-indexed, default: 1)
- `--verbose`: Enable verbose debug output

## License

This software is licensed under the MIT License.
