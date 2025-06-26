#!/usr/bin/env python3

import os
import gc
import numpy as np
import xarray as xr
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from pathlib import Path
import dask
from scipy.interpolate import griddata
from typing import Dict, List, Tuple
from dask.diagnostics import ProgressBar
import argparse
import psutil
import sys

class FluxPlotter:
    def __init__(self, base_dir: str, timestep: int = 0, remap_higher_res: bool = False, resolution: float = 0.5, parallel: bool = True, verbose: bool = False):
        """Initialize the FluxPlotter.
        
        Args:
            base_dir: Base directory containing data folders
            timestep: Timestep to process (0-indexed, default 0)
            remap_higher_res: Whether to remap to higher resolution
            resolution: Target resolution in degrees (0.5 for half-degree, 0.25 for quarter-degree)
            parallel: Whether to process files in parallel (True) or sequentially (False)
            verbose: Whether to print verbose debug information (default: False)
        """
        self.base_dir = Path(base_dir)
        self.output_dir = self.base_dir / 'output'
        self.output_dir.mkdir(exist_ok=True)
        self.image_dir = self.output_dir / 'images'
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.timestep = timestep
        self.remap_higher_res = remap_higher_res
        self.resolution = resolution
        self.parallel = parallel
        self.verbose = verbose
        self.skipped_files = []
        self.plotted_files = []
        
        # Pre-initialize the remapping grid for higher resolution plotting
        if self.remap_higher_res:
            self.print_memory_usage("Before initializing target grid")
            # Creating target grid for higher resolution plotting (0.5 by default)
            # Use -180 to 180 longitude range for better visualization
            self.target_lon = np.arange(-180, 180, self.resolution)
            self.target_lat = np.arange(-90, 90, self.resolution)
            self.target_lon_mesh, self.target_lat_mesh = np.meshgrid(self.target_lon, self.target_lat)
            self.print_memory_usage("After initializing target grid")
        
    def remap_to_higher_res(self, lon, lat, data):
        """Remap irregular grid data to a higher resolution regular grid.
        
        Args:
            lon: Longitude coordinates
            lat: Latitude coordinates
            data: Data values
            
        Returns:
            Remapped data array
        """
        # Flatten input arrays if needed
        if lon.ndim > 1:
            lon = lon.flatten()
        if lat.ndim > 1:
            lat = lat.flatten()
        if data.ndim > 1:
            data = data.flatten()
            
        # Make sure all arrays have the same length
        min_len = min(len(lon), len(lat), len(data))
        lon = lon[:min_len]
        lat = lat[:min_len]
        data = data[:min_len]
        
        # Convert longitudes to the range [-180, 180] if they're in [0, 360]
        if np.any(lon > 180):
            lon = np.where(lon > 180, lon - 360, lon)
            
        # Create points array for interpolation
        points = np.vstack((lon, lat)).T
        
        # Filter out any NaN values
        valid_mask = ~np.isnan(data)
        if not np.any(valid_mask):
            if self.verbose:
                print("Warning: No valid data points for interpolation")
            return np.zeros((len(self.target_lat), len(self.target_lon)))
            
        points = points[valid_mask]
        values = data[valid_mask]
        
        self.print_memory_usage("After filtering invalid points")
        
        # Use linear interpolation for the remapping
        remapped_data = griddata(
            points, 
            values, 
            (self.target_lon_mesh, self.target_lat_mesh),
            method='linear',
            fill_value=0
        )
        
        self.print_memory_usage("After griddata interpolation")
        
        return remapped_data
    
    def generate_html(self, comparison_folders=None):
        """Generate an HTML page of plotted files.
        
        This is a dispatcher function that calls the appropriate HTML generation
        function based on the number of folders.
        """
        # Get all image files
        all_images = list(self.image_dir.glob('*.png'))
        
        # Determine if we're in single folder mode or comparison mode
        if comparison_folders:
            if len(comparison_folders) == 1:
                self.generate_html_single(all_images, comparison_folders[0])
            else:
                self.generate_html_comparison(all_images, comparison_folders)
        else:
            # Auto-detect mode based on available folders
            experiment_names = sorted(list(self._extract_experiment_names_from_images(all_images)))
            
            if len(experiment_names) == 1:
                self.generate_html_single(all_images, experiment_names[0])
            else:
                self.generate_html_comparison(all_images, experiment_names[:2] if len(experiment_names) >= 2 else None)
        
        if self.verbose:
            print(f"Comparison HTML generated at: {self.output_dir / 'comparison.html'}")
    
    def generate_html_single(self, all_images, folder_name):
        """Generate an HTML page for a single folder of images."""
        if self.verbose:
            print(f"Single folder mode: {folder_name}")
            
        html_content = f'''<!DOCTYPE html>
<html>
<head>
<title>{folder_name} Flux Visualization</title>
<style>
    /* Styles for the single folder HTML */
    body {{
        font-family: Arial, sans-serif;
        background-color: #f5f5f5;
        margin: 0;
        padding: 20px;
    }}
    h1, h2 {{
        color: #333;
    }}
    h1 {{
        border-bottom: 1px solid #ccc;
        padding-bottom: 10px;
    }}
    .single-view {{
        display: flex;
        flex-direction: column;
        gap: 20px;
        align-items: center;
    }}
    .plot-item {{
        background: white;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        width: 80%;
        max-width: 900px;
        text-align: center;
    }}
    img {{
        max-width: 100%;
        height: auto;
        border: 1px solid #ddd;
    }}
    .stats {{
        background: white;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-top: 20px;
    }}
    .toggle {{
        cursor: pointer;
        color: #06c;
        text-decoration: underline;
    }}
    .skipped-list {{
        display: none;
        margin-top: 10px;
        padding: 10px;
        background: #fff;
        border: 1px solid #ddd;
    }}
    /* Tab styles */
    .tab {{
        overflow: hidden;
        border: 1px solid #ccc;
        background-color: #f1f1f1;
        margin-bottom: 20px;
    }}
    .tab button {{
        background-color: inherit;
        float: left;
        border: none;
        outline: none;
        cursor: pointer;
        padding: 14px 16px;
        transition: 0.3s;
        font-size: 16px;
    }}
    .tab button:hover {{
        background-color: #ddd;
    }}
    .tab button.active {{
        background-color: #ccc;
    }}
    .tabcontent {{
        display: none;
        padding: 6px 12px;
        border: 1px solid #ccc;
        border-top: none;
    }}
</style>
</head>
<body>
<h1>{folder_name} Flux Visualization</h1>

<div class="tab">
    <button class="tablinks active" onclick="openPlotType(event, 'NativeGridPlots')">Native Grid</button>
    <button class="tablinks" onclick="openPlotType(event, 'RemappedPlots')">Remapped</button>
</div>

<div id="NativeGridPlots" class="tabcontent" style="display: block;">
    <h1>Native Grid Plots</h1>
    <div class="single-view">
'''
        
        # Create dictionaries to store files by prefix and variable
        native_grid_files = {}
        remapped_files = {}
        
        # Debug: List all files
        if self.verbose:
            print(f"Found {len(all_images)} images in directory: {self.image_dir}")
            
        # Categorize files
        for img_file in all_images:
            file_name = img_file.name
            if self.verbose:
                print(f"Processing image file: {file_name}")
            
            # Determine if it's remapped or native grid
            is_remapped = f"_{self.resolution}deg" in file_name
            
            # Extract experiment name and variable name
            if file_name.startswith(f"{folder_name}_"):
                if is_remapped:
                    # Extract variable name without resolution suffix
                    var_name = file_name[len(f"{folder_name}_"):].rsplit(f"_{self.resolution}deg", 1)[0]
                    remapped_files[var_name] = img_file
                else:
                    # Extract variable name
                    var_name = file_name[len(f"{folder_name}_"):-4]  # Remove .png extension
                    native_grid_files[var_name] = img_file
        
        # Add native grid plots
        if self.verbose:
            print(f"Native grid {folder_name} files: {list(native_grid_files.keys())}")
        
        for var_name, img_file in sorted(native_grid_files.items()):
            if self.verbose:
                print(f"Adding native grid plot for {var_name}")
                
            html_content += f'''
        <div class="plot-item">
            <h2>{var_name}</h2>
            <img src="images/{img_file.name}" alt="{folder_name} {var_name}">
        </div>
'''
        
        # Add remapped content section
        html_content += '''
    </div>
</div>

<div id="RemappedPlots" class="tabcontent">
    <h1>Remapped Plots</h1>
    <div class="single-view">
'''
        
        # Add remapped plots
        if self.verbose:
            print(f"Remapped {folder_name} files: {list(remapped_files.keys())}")
            
        for var_name, img_file in sorted(remapped_files.items()):
            if self.verbose:
                print(f"Adding remapped plot for {var_name}")
                
            html_content += f'''
        <div class="plot-item">
            <h2>{var_name} ({self.resolution}° grid)</h2>
            <img src="images/{img_file.name}" alt="{folder_name} {var_name} {self.resolution} degree">
        </div>
'''
        
        # Build the skipped files list
        skipped_files_html = ""
        for file in sorted(self.skipped_files):
            skipped_files_html += f"<li>{file}</li>\n"
            
        # Add stats and skipped files section with proper escaping for JavaScript
        html_content += f'''
    </div>
</div>

<div class="stats">
    <p>Files plotted: {len(self.plotted_files)}, Files skipped: {len(self.skipped_files)}</p>
    <span class="toggle" onclick="toggleSkippedList()">Show/hide skipped files</span>
    <div id="skippedList" class="skipped-list">
        <ul>
            {skipped_files_html}
        </ul>
    </div>
</div>

<script>
function openPlotType(evt, plotType) {{
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {{
        tabcontent[i].style.display = "none";
    }}
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {{
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }}
    document.getElementById(plotType).style.display = "block";
    evt.currentTarget.className += " active";
}}

function toggleSkippedList() {{
    var list = document.getElementById("skippedList");
    if (list.style.display === "block") {{
        list.style.display = "none";
    }} else {{
        list.style.display = "block";
    }}
}}
</script>
</body>
</html>'''

        # Write the HTML file
        with open(self.output_dir / 'comparison.html', 'w') as f:
            f.write(html_content)
            
    def generate_html_comparison(self, all_images, comparison_folders=None):
        """Generate an HTML comparison page for two folders."""
        html_content = '''<!DOCTYPE html>
<html>
<head>
<title>Flux Comparison</title>
<style>
    /* Styles for the comparison HTML */
    body {
        font-family: Arial, sans-serif;
        background-color: #f5f5f5;
        margin: 0;
        padding: 20px;
    }
    h1 {
        color: #333;
        border-bottom: 1px solid #ccc;
        padding-bottom: 10px;
    }
    h2 {
        color: #444;
        margin-top: 5px;
    }
    .comparison {
        display: flex;
        flex-direction: column;
        gap: 20px;
    }
    .pair {
        display: flex;
        gap: 20px;
        background: white;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .pair > div {
        flex: 1;
    }
    img {
        width: 100%;
        height: auto;
        border: 1px solid #ddd;
    }
    .stats {
        background: white;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-top: 20px;
    }
    .toggle {
        cursor: pointer;
        color: #06c;
        text-decoration: underline;
    }
    .skipped-list {
        display: none;
        margin-top: 10px;
        padding: 10px;
        background: #fff;
        border: 1px solid #ddd;
    }
    /* Tab styles */
    .tab {
        overflow: hidden;
        border: 1px solid #ccc;
        background-color: #f1f1f1;
        margin-bottom: 20px;
    }
    .tab button {
        background-color: inherit;
        float: left;
        border: none;
        outline: none;
        cursor: pointer;
        padding: 14px 16px;
        transition: 0.3s;
        font-size: 16px;
    }
    .tab button:hover {
        background-color: #ddd;
    }
    .tab button.active {
        background-color: #ccc;
    }
    .tabcontent {
        display: none;
        padding: 6px 12px;
        border: 1px solid #ccc;
        border-top: none;
    }
</style>
</head>
<body>
<div class="tab">
    <button class="tablinks active" onclick="openPlotType(event, 'NativeGridPlots')">Native Grid</button>
    <button class="tablinks" onclick="openPlotType(event, 'RemappedPlots')">Remapped</button>
</div>

<div id="NativeGridPlots" class="tabcontent" style="display: block;">
    <h1>Native Grid Flux Comparison</h1>
    <div class="comparison">
'''
        
        # If comparison folders are specified, use them directly
        if comparison_folders and len(comparison_folders) >= 2:
            exp1_name = comparison_folders[0]
            exp2_name = comparison_folders[1]
            
            if self.verbose:
                print(f"Using specified folders for comparison: {exp1_name} and {exp2_name}")
        else:
            # Extract experiment names from image filenames
            experiment_names = sorted(list(self._extract_experiment_names_from_images(all_images)))
            
            if len(experiment_names) < 2:
                if self.verbose:
                    print(f"Warning: Found fewer than 2 experiment folders: {experiment_names}")
                if len(experiment_names) == 0:
                    experiment_names = ["exp1", "exp2"]  # Fallback if no valid experiments found
                elif len(experiment_names) == 1:
                    experiment_names.append("exp2")  # Add a dummy second experiment
            
            # For backward compatibility with existing code, use the first two experiment names
            exp1_name = experiment_names[0]
            exp2_name = experiment_names[1] if len(experiment_names) > 1 else "exp2"
        
        if self.verbose:
            print(f"Using experiment names for comparison: {exp1_name} and {exp2_name}")
        
        # Create dictionaries to store files by prefix and variable
        exp1_native_grid_files = {}
        exp2_native_grid_files = {}
        exp1_remapped_files = {}
        exp2_remapped_files = {}
        
        # Debug: List all files
        if self.verbose:
            print(f"Found {len(all_images)} images in directory: {self.image_dir}")
            
        # Categorize files
        for img_file in all_images:
            file_name = img_file.name
            if self.verbose:
                print(f"Processing image file: {file_name}")
            
            # Determine if it's remapped or native grid
            is_remapped = f"_{self.resolution}deg" in file_name
            
            # Extract experiment name and variable name
            if file_name.startswith(f"{exp1_name}_"):
                if is_remapped:
                    # Extract variable name without resolution suffix
                    var_name = file_name[len(f"{exp1_name}_"):].rsplit(f"_{self.resolution}deg", 1)[0]
                    exp1_remapped_files[var_name] = img_file
                else:
                    # Extract variable name
                    var_name = file_name[len(f"{exp1_name}_"):-4]  # Remove .png extension
                    exp1_native_grid_files[var_name] = img_file
            elif file_name.startswith(f"{exp2_name}_"):
                if is_remapped:
                    var_name = file_name[len(f"{exp2_name}_"):].rsplit(f"_{self.resolution}deg", 1)[0]
                    exp2_remapped_files[var_name] = img_file
                else:
                    var_name = file_name[len(f"{exp2_name}_"):-4]  # Remove .png extension
                    exp2_native_grid_files[var_name] = img_file
                    
        if self.verbose:
            print(f"Native grid {exp1_name} files: {list(exp1_native_grid_files.keys())}")
            print(f"Native grid {exp2_name} files: {list(exp2_native_grid_files.keys())}")
            print(f"Remapped {exp1_name} files: {list(exp1_remapped_files.keys())}")
            print(f"Remapped {exp2_name} files: {list(exp2_remapped_files.keys())}")
            
        # Find common variable names for native grid
        common_vars_native_grid = sorted(set(exp1_native_grid_files.keys()) & set(exp2_native_grid_files.keys()))
        
        if self.verbose:
            print(f"Common native grid variables: {common_vars_native_grid}")
        
        # Add native grid plots
        native_grid_plots_added = 0
        for var_name in common_vars_native_grid:
            exp1_file = exp1_native_grid_files[var_name]
            exp2_file = exp2_native_grid_files[var_name]
            
            if self.verbose:
                print(f"Adding native grid plot pair for {var_name}")
                
            html_content += f'''
        <div class="pair">
            <div>
                <h2>{exp1_name} - {var_name}</h2>
                <img src="images/{exp1_file.name}" alt="{exp1_name} {var_name}">
            </div>
            <div>
                <h2>{exp2_name} - {var_name}</h2>
                <img src="images/{exp2_file.name}" alt="{exp2_name} {var_name}">
            </div>
        </div>
'''
            native_grid_plots_added += 1
        
        # If no native grid plots were added, provide a message
        if native_grid_plots_added == 0:
            html_content += '''
        <div class="pair">
            <div>
                <h2>No native grid plots available</h2>
            </div>
        </div>
'''
        
        html_content += '''
    </div>
</div>

<div id="RemappedPlots" class="tabcontent">
    <h1>Remapped Flux Comparison</h1>
    <div class="comparison">
'''
        # Find common variable names for remapped files
        common_vars_remapped = sorted(set(exp1_remapped_files.keys()) & set(exp2_remapped_files.keys()))
        
        if self.verbose:
            print(f"Common remapped variables: {common_vars_remapped}")
        
        # Add higher resolution plots
        higher_res_plots_added = 0
        for var_name in common_vars_remapped:
            exp1_file = exp1_remapped_files[var_name]
            exp2_file = exp2_remapped_files[var_name]
            
            if self.verbose:
                print(f"Adding remapped plot pair for {var_name}")
                
            html_content += f'''
        <div class="pair">
            <div>
                <h2>{exp1_name} - {var_name} ({self.resolution}° grid)</h2>
                <img src="images/{exp1_file.name}" alt="{exp1_name} {var_name}">
            </div>
            <div>
                <h2>{exp2_name} - {var_name} ({self.resolution}° grid)</h2>
                <img src="images/{exp2_file.name}" alt="{exp2_name} {var_name}">
            </div>
        </div>
'''
            higher_res_plots_added += 1
        
        # If no higher resolution plots were added, provide a message
        if higher_res_plots_added == 0:
            html_content += '''
        <div class="pair">
            <div>
                <h2>No remapped plots available</h2>
            </div>
        </div>
'''

        # Build the skipped files list
        skipped_files_html = ""
        for file in sorted(self.skipped_files):
            skipped_files_html += f"<li>{file}</li>\n"
        
        # Add stats and skipped files section with proper escaping for JavaScript
        html_content += f'''
    </div>
</div>

<div class="stats">
    <p>Files plotted: {len(self.plotted_files)}, Files skipped: {len(self.skipped_files)}</p>
    <span class="toggle" onclick="toggleSkippedList()">Show/hide skipped files</span>
    <div id="skippedList" class="skipped-list">
        <ul>
            {skipped_files_html}
        </ul>
    </div>
</div>

<script>
function openPlotType(evt, plotType) {{
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {{
        tabcontent[i].style.display = "none";
    }}
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {{
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }}
    document.getElementById(plotType).style.display = "block";
    evt.currentTarget.className += " active";
}}

function toggleSkippedList() {{
    var list = document.getElementById("skippedList");
    if (list.style.display === "block") {{
        list.style.display = "none";
    }} else {{
        list.style.display = "block";
    }}
}}
</script>
</body>
</html>'''

        # Write the HTML file
        with open(self.output_dir / 'comparison.html', 'w') as f:
            f.write(html_content)
            
    def reshape_1d_to_2d(self, data: np.ndarray, target_shape: tuple) -> np.ndarray:
        """Reshape 1D data to 2D based on target shape."""
        if len(data.shape) == 1:
            if data.shape[0] == target_shape[0] * target_shape[1]:
                return data.reshape(target_shape)
        return data
        
    def get_coordinates(self, folder: str, grid_ds: xr.Dataset, coord_type: str) -> Tuple[np.ndarray, np.ndarray]:
        """Get coordinates for a specific type from the grids dataset."""
        if coord_type == 'A':
            # Dynamically find atmospheric grid variables based on available data
            # Look for variables starting with 'A' and ending with '.lon' and '.lat'
            a_vars = [var for var in grid_ds.variables if var.startswith('A') and (var.endswith('.lon') or var.endswith('.lat'))]
            
            # Find the specific A-grid prefix (e.g., A096 or A128) from the available variables
            a_prefixes = set(var.split('.')[0] for var in a_vars)
            
            if not a_prefixes:
                raise ValueError(f"No atmospheric grid variables found in dataset for folder {folder}. Available variables: {list(grid_ds.variables)}")
                
            # Use the first available A-grid prefix
            a_prefix = sorted(list(a_prefixes))[0]
            
            if self.verbose:
                print(f"Using atmospheric grid prefix: {a_prefix} for folder {folder}")
                
            lon = grid_ds[f'{a_prefix}.lon'].values.reshape(1, -1)[0]
            lat = grid_ds[f'{a_prefix}.lat'].values.reshape(1, -1)[0]
            return lon, lat
            
        elif coord_type == 'feom':
            lon = grid_ds['feom.lon'].values.reshape(1, -1)[0]
            lat = grid_ds['feom.lat'].values.reshape(1, -1)[0]
            return lon, lat
        else:  # RnfA
            return grid_ds['RnfA.lon'].values, grid_ds['RnfA.lat'].values
    
    def print_memory_usage(self, label: str = ""):
        """Print the current memory usage."""
        if self.verbose:
            process = psutil.Process()
            memory_info = process.memory_info()
            print(f"Memory usage {label}: {memory_info.rss / 1024 / 1024:.2f} MB")
        
    @dask.delayed
    def process_file(self, nc_file: Path, grid_ds: xr.Dataset):
        """Process a single netCDF file and create its plot."""
        # Skip grids file and mesh diagnostic file
        if nc_file.name == 'grids.nc' or nc_file.name == 'fesom.mesh.diag.nc':
            return

        if self.verbose:
            print(f"Processing {nc_file.name} (parallel)")
        # Determine coordinate type based on filename prefix
        if nc_file.name.startswith('A_'):
            coord_type = 'A'
        elif nc_file.name.startswith('R_'):
            coord_type = 'RnfA'
        else:
            coord_type = 'feom'
        
        try:
            # Open the file
            with xr.open_dataset(nc_file) as ds:
                var_keys = [key for key in ds.variables if key != 'time' and key not in ds.dims]
                if not var_keys:
                    self.skipped_files.append(nc_file.name)
                    return
                
                var_name = var_keys[0]  # Use the first variable that isn't time or a dimension
                
                # Check data dimensions and extract timestep
                if self.verbose:
                    print(f"Variable {var_name} shape: {ds[var_name].shape}")
                
                # If the variable has multiple timesteps, extract only the one we want
                if 'time' in ds[var_name].dims:
                    # Load only the specified timestep
                    if self.timestep < ds[var_name].shape[0]:
                        if self.verbose:
                            print(f"Loading only timestep {self.timestep} out of {ds[var_name].shape[0]}")
                        var_data = ds[var_name].isel(time=self.timestep).values
                    else:
                        if self.verbose:
                            print(f"Timestep {self.timestep} out of range, using timestep 0")
                        var_data = ds[var_name].isel(time=0).values
                else:
                    var_data = ds[var_name].values
                    
                # Check if there are more dimensions to reduce
                if var_data.ndim > 2:
                    if self.verbose:
                        print(f"Variable has {var_data.ndim} dimensions, shape {var_data.shape}")
                    # If 3D, but first dimension is not time (already handled above)
                    if var_data.shape[0] in [1, 2]:
                        if self.verbose:
                            print(f"Taking first slice of dimension 0")
                        var_data = var_data[0, ...]
        except Exception as e:
            if self.verbose:
                print(f"Error processing {nc_file}: {e}")
            self.skipped_files.append(nc_file.name)
            return
            
        # Determine the appropriate coordinate type based on the file name
        # This handles different grid types by looking at filename patterns
        file_coord_type = coord_type
        if '_ico_' in nc_file.name or '_oce_' in nc_file.name or 'fesom' in nc_file.name:
            file_coord_type = 'feom'  # Ocean grid
        elif '_OpenIFS_' in nc_file.name or '_ice_' in nc_file.name:
            file_coord_type = 'A'     # Atmosphere grid
        elif 'RnfA' in nc_file.name:
            file_coord_type = 'RnfA'   # Runoff grid
        
        if self.verbose:
            print(f"Using coordinate type '{file_coord_type}' for file {nc_file.name}")
            
        # Get coordinates for the specific grid type of this file
        lon, lat = self.get_coordinates(nc_file.parent.name, grid_ds, file_coord_type)
        
        # Check that coordinates and data array sizes match
        if lon.size != var_data.size and lat.size != var_data.size:
            if self.verbose:
                print(f"Warning: Coordinate size ({lon.size}) doesn't match data size ({var_data.size}) for {nc_file.name}")
            
            # If data is 1D but different size, we might have the wrong grid - skip this file
            if var_data.ndim == 1:
                if self.verbose:
                    print(f"Incompatible grid sizes - skipping {nc_file.name}")
                self.skipped_files.append(nc_file.name)
                return
        
        # Replace NaNs with zeros
        var_data = np.nan_to_num(var_data, nan=0.0)
        
        # Generate standard resolution plot
        self._create_plot(nc_file, var_name, lon, lat, var_data, False)
        
        # Generate higher resolution plot if requested
        if self.remap_higher_res:
            remapped_data = self.remap_to_higher_res(lon, lat, var_data)
            self._create_plot(nc_file, var_name, self.target_lon_mesh, self.target_lat_mesh, remapped_data, True)
        
        self.plotted_files.append(nc_file.name)
        return nc_file.name  # Return the filename for tracking
    
    def process_file_sequential(self, nc_file: Path, grid_ds: xr.Dataset):
        """Process a single netCDF file sequentially (non-dask version)."""
        # Skip grids file and mesh diagnostic file
        if nc_file.name == 'grids.nc' or nc_file.name == 'fesom.mesh.diag.nc':
            return

        self.print_memory_usage(f"Before processing {nc_file.name}")

        # Determine coordinate type based on filename prefix
        if nc_file.name.startswith('A_'):
            coord_type = 'A'
        elif nc_file.name.startswith('R_'):
            coord_type = 'RnfA'
        else:
            coord_type = 'feom'
        
        try:
            # Open the file
            self.print_memory_usage(f"Before opening {nc_file.name}")
            with xr.open_dataset(nc_file) as ds:
                self.print_memory_usage(f"After opening {nc_file.name}")
                var_keys = [key for key in ds.variables if key != 'time' and key not in ds.dims]
                if not var_keys:
                    self.skipped_files.append(nc_file.name)
                    return
                
                var_name = var_keys[0]  # Use the first variable that isn't time or a dimension
                
                # Check data dimensions and extract timestep
                if self.verbose:
                    print(f"Variable {var_name} shape: {ds[var_name].shape}")
                
                # If the variable has multiple timesteps, extract only the one we want
                if 'time' in ds[var_name].dims:
                    # Load only the specified timestep
                    if self.timestep < ds[var_name].shape[0]:
                        if self.verbose:
                            print(f"Loading only timestep {self.timestep} out of {ds[var_name].shape[0]}")
                        var_data = ds[var_name].isel(time=self.timestep).values
                    else:
                        if self.verbose:
                            print(f"Timestep {self.timestep} out of range, using timestep 0")
                        var_data = ds[var_name].isel(time=0).values
                else:
                    var_data = ds[var_name].values
                    
                # Check if there are more dimensions to reduce
                if var_data.ndim > 2:
                    if self.verbose:
                        print(f"Variable has {var_data.ndim} dimensions, shape {var_data.shape}")
                    # If 3D, but first dimension is not time (already handled above)
                    if var_data.shape[0] in [1, 2]:
                        if self.verbose:
                            print(f"Taking first slice of dimension 0")
                        var_data = var_data[0, ...]
                    # If there are more dimensions, we might need to handle them differently
                    
                self.print_memory_usage(f"After reading {var_name} from {nc_file.name}")
        except Exception as e:
            if self.verbose:
                print(f"Error processing {nc_file}: {e}")
            self.skipped_files.append(nc_file.name)
            return
        
        self.print_memory_usage(f"Before getting coordinates for {nc_file.name}")
        # Get coordinates
        lon, lat = self.get_coordinates(nc_file.parent.name, grid_ds, coord_type)
        self.print_memory_usage(f"After getting coordinates for {nc_file.name}")
        
        # Replace NaNs with zeros
        var_data = np.nan_to_num(var_data, nan=0.0)
        
        # Generate standard resolution plot
        self.print_memory_usage(f"Before creating standard plot for {nc_file.name}")
        self._create_plot(nc_file, var_name, lon, lat, var_data, False)
        self.print_memory_usage(f"After creating standard plot for {nc_file.name}")
        
        # Generate higher resolution plot if requested
        if self.remap_higher_res:
            self.print_memory_usage(f"Before remapping {nc_file.name}")
            remapped_data = self.remap_to_higher_res(lon, lat, var_data)
            self.print_memory_usage(f"After remapping {nc_file.name}")
            self._create_plot(nc_file, var_name, self.target_lon_mesh, self.target_lat_mesh, remapped_data, True)
            self.print_memory_usage(f"After creating remapped plot for {nc_file.name}")
        
        self.plotted_files.append(nc_file.name)
        
        # Explicitly delete variables to free memory
        del var_data
        if self.remap_higher_res and 'remapped_data' in locals():
            del remapped_data
        gc.collect()
        self.print_memory_usage(f"After cleanup for {nc_file.name}")
    
    def process_folder(self, folder: str, max_files: int = 0):
        """Process all files in a folder with parallel or sequential processing."""
        folder_path = self.base_dir / 'data' / folder
        
        # Load grids once for the folder
        chunks = {'x_A096': 4032, 'x_feom': 12685}
        with xr.open_dataset(folder_path / 'grids.nc', chunks=chunks) as grid_ds:
            # Get all .nc files
            nc_files = list(folder_path.glob('*.nc'))
            if max_files > 0:
                nc_files = nc_files[:max_files]
                
            if self.parallel:
                # Parallel processing with dask
                if self.verbose:
                    print(f"Processing folder {folder} in parallel mode")
                # Create list of delayed tasks
                tasks = [self.process_file(nc_file, grid_ds) for nc_file in nc_files]
                
                # Execute tasks in parallel with progress bar
                with ProgressBar():
                    processed_files = dask.compute(*tasks)
                    if self.verbose:
                        print(f"Processed {len([f for f in processed_files if f is not None])} files")
            else:
                # Sequential processing
                if self.verbose:
                    print(f"Processing folder {folder} in sequential mode")
                for nc_file in nc_files:
                    if self.verbose:
                        print(f"Processing {nc_file.name}")
                    # Process file directly without dask.delayed
                    self.process_file_sequential(nc_file, grid_ds)
                    # Force garbage collection after each file
                    gc.collect()

    def _create_plot(self, nc_file, var_name, lon, lat, var_data, is_remapped):
        """
        Create a plot for the given variable data.
        
        Parameters:
        -----------
        nc_file : Path
            Path to the source netCDF file
        var_name : str
            Name of the variable to plot
        lon : np.ndarray
            Longitude values
        lat : np.ndarray
            Latitude values
        var_data : np.ndarray
            Variable data to plot
        is_remapped : bool
            Whether this is remapped data (True) or native grid data (False)
        """
        self.print_memory_usage(f"Start of _create_plot for {nc_file.name}")
        
        # Determine whether to use reduced or full coastline detail based on file size
        # For smaller files, we can afford more detail
        resolution = '110m' if is_remapped else '110m'
        
        # Make sure the plotting directory exists
        self.image_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare data for plotting
        plot_lon, plot_lat, var_data = lon, lat, var_data
        
        # For remapped data, ensure dimensions are correct
        if is_remapped and var_data.ndim == 2:
            if self.verbose:
                print(f"Final array shapes: lon={plot_lon.shape}, lat={plot_lat.shape}, var_data={var_data.shape}")
        else:
            # For unstructured data, ensure we have 1D arrays
            if var_data.ndim > 1:
                if self.verbose:
                    print(f"Flattening data from shape {var_data.shape}")
                var_data = var_data.flatten()
                if self.verbose:
                    print(f"New data shape: {var_data.shape}")
            
            if self.verbose:
                print(f"Final array shapes: lon={plot_lon.shape}, lat={plot_lat.shape}, var_data={var_data.shape}")
        
        # Create output filename
        folder_name = nc_file.parent.name
        if is_remapped:
            output_filename = self.image_dir / f"{folder_name}_{var_name}_{self.resolution}deg.png"
        else:
            output_filename = self.image_dir / f"{folder_name}_{var_name}.png"
        
        # Create a new figure and axis for each plot
        fig = plt.figure(figsize=(10, 6), dpi=300)
        
        # Use PlateCarree projection for both cases to avoid coordinate transformation issues
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        
        # Reduce the amount of coastline detail
        ax.coastlines(resolution=resolution, linewidth=0.5)
        
        # Simplify gridlines
        gl = ax.gridlines(draw_labels=True, linewidth=0.2, color='gray', alpha=0.5, linestyle=':')
        gl.top_labels = False
        gl.right_labels = False
        
        # Set global extent
        ax.set_global()
        
        # Plot data based on structure
        if is_remapped:
            # For remapped data (regular grid), use pcolormesh but with special handling to avoid geometry errors
            try:
                # Make sure we're using 1D arrays for lon and lat in the grid
                if plot_lon.ndim > 1:
                    plot_lon = plot_lon[0, :]  # Extract first row for longitude
                if plot_lat.ndim > 1:
                    plot_lat = plot_lat[:, 0]  # Extract first column for latitude
                
                # Create a 2D meshgrid for pcolormesh if needed
                # This avoids cartopy geometry transformation issues
                if plot_lon.ndim == 1 and plot_lat.ndim == 1:
                    # Create the 2D meshgrid required for pcolormesh
                    mesh_lon, mesh_lat = np.meshgrid(plot_lon, plot_lat)
                    
                    # Use imshow instead of pcolormesh to avoid geometry transformation issues
                    # This displays the data in the image coordinates directly
                    extent = [
                        np.min(plot_lon), np.max(plot_lon),
                        np.min(plot_lat), np.max(plot_lat)
                    ]
                    cs = ax.imshow(
                        var_data, 
                        origin='lower', 
                        extent=extent,
                        transform=ccrs.PlateCarree(),
                        aspect='auto',
                        cmap='viridis'
                    )
                else:
                    # Fallback to pcolormesh with explicit coordinates
                    cs = ax.pcolormesh(
                        plot_lon, 
                        plot_lat, 
                        var_data, 
                        transform=ccrs.PlateCarree(), 
                        cmap='viridis'
                    )
            except Exception as e:
                if self.verbose:
                    print(f"Error in pcolormesh: {e}. Falling back to imshow.")
                
                # Fallback to imshow when pcolormesh fails
                extent = [-180, 180, -90, 90]  # Default global extent
                cs = ax.imshow(
                    var_data, 
                    origin='lower', 
                    extent=extent,
                    transform=ccrs.PlateCarree(),
                    aspect='auto',
                    cmap='viridis'
                )
        else:
            # For unstructured grid data, try to plot with scatter or fallback to other methods
            try:
                # First, check if arrays are compatible
                if var_data.ndim > 1:
                    # If data is multi-dimensional and doesn't match coordinates, reshape or skip
                    if self.verbose:
                        print(f"Multi-dimensional data with shape {var_data.shape}, attempting to flatten")
                    var_data = var_data.flatten()
                
                # Ensure all arrays have the same length before plotting
                if len(plot_lon) != len(plot_lat) or len(plot_lon) != len(var_data) or len(plot_lat) != len(var_data):
                    if self.verbose:
                        print(f"Array length mismatch: lon: {len(plot_lon)}, lat: {len(plot_lat)}, data: {len(var_data)}")
                    
                    # If arrays can't be made compatible, switch to a different plotting method
                    if (var_data.ndim == 2 and var_data.shape[0] == var_data.shape[1]) or \
                       (len(plot_lon) != len(var_data) and len(plot_lat) != len(var_data)):
                        # If data is a 2D grid or arrays can't be matched, use imshow instead
                        if self.verbose:
                            print("Falling back to imshow instead of scatter due to incompatible array shapes")
                            
                        extent = [-180, 180, -90, 90]  # Default global extent
                        cs = ax.imshow(
                            var_data.reshape(-1, 1) if var_data.ndim == 1 else var_data, 
                            origin='lower', 
                            extent=extent,
                            transform=ccrs.PlateCarree(),
                            aspect='auto',
                            cmap='viridis'
                        )
                    else:
                        # Try to make arrays compatible by truncating to the minimum length
                        min_length = min(len(plot_lon), len(plot_lat), len(var_data))
                        if self.verbose:
                            print(f"Resizing all arrays to minimum length: {min_length}")
                        plot_lon = plot_lon[:min_length]
                        plot_lat = plot_lat[:min_length]
                        var_data = var_data[:min_length]
                        
                        # Check for NaN or invalid values in var_data
                        valid_mask = np.isfinite(var_data)
                        if not np.all(valid_mask):
                            invalid_count = np.sum(~valid_mask)
                            if self.verbose:
                                print(f"Found {invalid_count} invalid values in data. Replacing with zeros.")
                            var_data = np.where(valid_mask, var_data, 0.0)
                        
                        cs = ax.scatter(
                            plot_lon, 
                            plot_lat, 
                            c=var_data, 
                            transform=ccrs.PlateCarree(),
                            cmap='viridis', 
                            s=1.0,  # Small point size to avoid overlapping
                            alpha=0.7
                        )
                else:
                    # Arrays are already compatible
                    # Check for NaN or invalid values in var_data
                    valid_mask = np.isfinite(var_data)
                    if not np.all(valid_mask):
                        invalid_count = np.sum(~valid_mask)
                        if self.verbose:
                            print(f"Found {invalid_count} invalid values in data. Replacing with zeros.")
                        var_data = np.where(valid_mask, var_data, 0.0)
                    
                    cs = ax.scatter(
                        plot_lon, 
                        plot_lat, 
                        c=var_data, 
                        transform=ccrs.PlateCarree(),
                        cmap='viridis', 
                        s=1.0,  # Small point size to avoid overlapping
                        alpha=0.7
                    )
                    
                if self.verbose:
                    print("Using scatter plot for original point cloud data")
                    
            except Exception as e:
                if self.verbose:
                    print(f"Error in scatter plot: {str(e)}. Falling back to imshow.")
                    
                # Last resort fallback to imshow
                extent = [-180, 180, -90, 90]  # Default global extent
                var_data_display = var_data.copy()
                
                # Reshape data if needed
                if var_data_display.ndim == 1:
                    size = int(np.sqrt(len(var_data_display)))
                    var_data_display = var_data_display[:size*size].reshape(size, size)
                    
                cs = ax.imshow(
                    var_data_display, 
                    origin='lower', 
                    extent=extent,
                    transform=ccrs.PlateCarree(),
                    aspect='auto',
                    cmap='viridis'
                )
        
        # Calculate min/max values for colorbar outside of NaN values
        valid_data = var_data[~np.isnan(var_data)]
        if len(valid_data) > 0:
            v_min, v_max = np.min(valid_data), np.max(valid_data)
            if self.verbose:
                print(f"Data range: min={v_min}, max={v_max}")
            
            # Add colorbar - using the specific figure rather than the global plt state
            fig.colorbar(cs, ax=ax, orientation='horizontal', pad=0.05, label=var_name)
        
        # Add title
        ax.set_title(f"{folder_name}: {var_name}{' (remapped)' if is_remapped else ''}")
        
        # Save the figure with consistent DPI and close it explicitly
        fig.savefig(output_filename, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        self.print_memory_usage(f"End of _create_plot for {nc_file.name}")
        
        return output_filename
    
    def _extract_experiment_names_from_images(self, all_images):
        """Extract experiment names from image filenames."""
        experiment_names = set()
        for img_file in all_images:
            file_name = img_file.name
            # Extract experiment name from the file name prefix (before the variable name)
            if '_' in file_name:
                # Find the position of the first underscore followed by a common flux variable name
                common_var_patterns = ['sst_', 'prec_', 'A_']
                exp_name = file_name
                for pattern in common_var_patterns:
                    if pattern in file_name:
                        exp_name = file_name.split(pattern, 1)[0]
                        if exp_name.endswith('_'):
                            exp_name = exp_name[:-1]  # Remove trailing underscore
                        break
                experiment_names.add(exp_name)
        return experiment_names

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process and visualize flux data')
    parser.add_argument('--no-remap', action='store_true', help='Disable remapping to higher resolution')
    parser.add_argument('--sequential', action='store_true', help='Process files sequentially (default: parallel)')
    parser.add_argument('--resolution', type=float, default=0.5, help='Target resolution in degrees (default: 0.5)')
    parser.add_argument('--max-files', type=int, default=0, help='Maximum number of files to process per folder (0 for all)')
    parser.add_argument('--folder', type=str, default='', help='Process only this folder (default: all folders)')
    parser.add_argument('--timestep', type=int, default=1, help='Timestep to process (0-indexed, default: 1)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose debug output')
    parser.add_argument('--compare', type=str, nargs=2, help='Specify two folders to compare in HTML report (e.g., --compare flux_33 rnffix)')
    args = parser.parse_args()
    
    plotter = FluxPlotter(
        base_dir="/Users/jstreffi/software/plot_oasis_coupling", 
        timestep=args.timestep, 
        remap_higher_res=not args.no_remap, 
        resolution=args.resolution, 
        parallel=not args.sequential,
        verbose=args.verbose
    )
    
    # Keep track of processed folders for HTML comparison
    processed_folders = []
    
    if args.folder:
        if args.verbose:
            print(f"Processing folder: {args.folder}")
        plotter.process_folder(args.folder, max_files=args.max_files)
        processed_folders.append(args.folder)
    else:
        # Dynamically detect available folders in the data directory
        data_dir = Path(plotter.base_dir) / 'data'
        
        # If comparison folders are specified, only process those
        if args.compare:
            experiment_folders = args.compare
        else:
            experiment_folders = [folder.name for folder in data_dir.iterdir() if folder.is_dir()]
        
        if args.verbose:
            print(f"Found experiment folders: {experiment_folders}")
            
        for folder in experiment_folders:
            if args.verbose:
                print(f"Processing folder: {folder}")
            plotter.process_folder(folder, max_files=args.max_files)
            processed_folders.append(folder)
    
    # Generate HTML comparison with specified folders
    if args.compare:
        plotter.generate_html(comparison_folders=args.compare)
    else:
        # Use the processed folders for comparison
        if len(processed_folders) >= 2:
            plotter.generate_html(comparison_folders=processed_folders[:2])
        elif len(processed_folders) == 1:
            # For a single folder, pass just that folder
            plotter.generate_html(comparison_folders=[processed_folders[0]])
        else:
            plotter.generate_html()
    if args.verbose:
        print(f"Comparison HTML generated at: {plotter.output_dir / 'comparison.html'}")
