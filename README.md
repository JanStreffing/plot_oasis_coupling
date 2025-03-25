# OASIS Coupling Flux Visualization

[![Documentation Status](https://readthedocs.org/projects/plot-oasis-coupling/badge/?version=latest)](https://plot-oasis-coupling.readthedocs.io/en/latest/?badge=latest)

A tool for visualizing and comparing OASIS coupling fields between different model versions. This utility processes flux data from OASIS-coupled climate models and generates side-by-side comparisons.

## Features

- Process NetCDF flux data from OASIS-coupled models
- Create visualizations in both native grid and remapped formats
- Generate HTML comparison reports for flux_33 and flux_34 directories
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

# Process specific folder
python plot_fluxes.py --folder flux_33
