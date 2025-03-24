#!/usr/bin/env python3

import os
import matplotlib
matplotlib.use('Agg')  # Use Agg backend for non-interactive plotting
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import cartopy.crs as ccrs
from pathlib import Path
from typing import Dict, List, Tuple
import gc
from tqdm import tqdm
import dask
from dask.diagnostics import ProgressBar
from scipy.interpolate import griddata

class FluxPlotter:
    def __init__(self, base_dir: str, timestep: int = 0, remap_quarter_degree: bool = False):
        self.base_dir = Path(base_dir)
        self.timestep = timestep
        self.remap_quarter_degree = remap_quarter_degree
        self.output_dir = self.base_dir / 'output'
        self.output_dir.mkdir(exist_ok=True)
        self.image_dir = self.output_dir / 'images'
        self.image_dir.mkdir(exist_ok=True)
        self.skipped_files = []
        self.plotted_files = []
        
        # Create quarter degree lat-lon grid if remapping is enabled
        if self.remap_quarter_degree:
            self.target_lon = np.arange(-180, 180.25, 0.25)
            self.target_lat = np.arange(-90, 90.25, 0.25)
            self.target_lon_mesh, self.target_lat_mesh = np.meshgrid(self.target_lon, self.target_lat)
    
    def remap_to_quarter_degree(self, lon: np.ndarray, lat: np.ndarray, data: np.ndarray) -> np.ndarray:
        """Remap data to quarter degree lat-lon grid."""
        print(f"Input shapes: lon={lon.shape}, lat={lat.shape}, data={data.shape}")
        print(f"Input dtypes: lon={lon.dtype}, lat={lat.dtype}, data={data.dtype}")
        
        # Ensure data is 1D for scattered points
        if len(lon.shape) == 1 and len(lat.shape) == 1:
            print("Processing scattered points")
            valid = ~np.isnan(data[0])  # Take first dimension
            print(f"Valid points: {np.sum(valid)}")
            remapped_data = griddata(
                (lon[valid], lat[valid]), 
                data[0][valid],  # Take first dimension
                (self.target_lon_mesh, self.target_lat_mesh),
                method='linear'
            )
        else:  # For gridded data
            print("Processing gridded data")
            valid = ~np.isnan(data)
            points = np.column_stack((lon.ravel(), lat.ravel()))
            remapped_data = griddata(
                points,
                data.ravel(),
                (self.target_lon_mesh, self.target_lat_mesh),
                method='linear'
            )
        
        return remapped_data
    
    def generate_html(self):
        """Generate HTML file comparing plots from both folders."""
        html_content = f'''<html>
<head>
<title>Flux Comparison</title>
<style>
    body {{
        font-family: Arial, sans-serif;
        margin: 0;
        padding: 0;
    }}
    .tab {{
        overflow: hidden;
        border: 1px solid #ccc;
        background-color: #f1f1f1;
        position: sticky;
        top: 0;
        z-index: 100;
    }}
    .tab button {{
        background-color: inherit;
        float: left;
        border: none;
        outline: none;
        cursor: pointer;
        padding: 14px 16px;
        transition: 0.3s;
        font-size: 17px;
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
        animation: fadeEffect 1s;
    }}
    @keyframes fadeEffect {{
        from {{opacity: 0;}}
        to {{opacity: 1;}}
    }}
    .comparison {{
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        margin: 20px;
    }}
    .pair {{
        display: flex;
        gap: 20px;
        margin-bottom: 40px;
    }}
    img {{
        max-width: 800px;
        height: auto;
        border: 1px solid #ddd;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }}
    h2 {{
        margin: 20px 0 10px;
        color: #333;
    }}
    .stats {{
        margin: 20px;
        padding: 20px;
        background: #f5f5f5;
        border-radius: 5px;
    }}
    .skipped {{
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
</style>
</head>
<body>
<div class="tab">
    <button class="tablinks active" onclick="openPlotType(event, 'StandardPlots')">Standard Resolution</button>
    <button class="tablinks" onclick="openPlotType(event, 'QuarterDegreePlots')">Quarter Degree Resolution</button>
</div>

<div id="StandardPlots" class="tabcontent" style="display: block;">
    <h1>Standard Resolution Flux Comparison</h1>
    <div class="comparison">
'''

        # Get unique variable names from plot files
        var_names = set()
        plot_files = list(self.image_dir.glob('*.png'))
        for file in plot_files:
            if '_025deg' not in file.name:
                parts = file.stem.split('_')
                # Skip the folder prefix and get the variable name
                var_name = '_'.join(parts[1:])
                var_names.add(var_name)
        
        # Add standard resolution plots first
        for var_name in sorted(var_names):
            flux33_file = self.image_dir / f"flux_33_{var_name}.png"
            flux34_file = self.image_dir / f"flux_34_{var_name}.png"
            
            if flux33_file.exists() and flux34_file.exists():
                html_content += f'''
        <div class="pair">
            <div>
                <h2>flux_33 - {var_name}</h2>
                <img src="images/{flux33_file.name}" alt="flux_33 {var_name}">
            </div>
            <div>
                <h2>flux_34 - {var_name}</h2>
                <img src="images/{flux34_file.name}" alt="flux_34 {var_name}">
            </div>
        </div>
'''
        
        html_content += '''
    </div>
</div>

<div id="QuarterDegreePlots" class="tabcontent">
    <h1>Quarter Degree Resolution Flux Comparison</h1>
    <div class="comparison">
'''

        # Add quarter degree plots
        for var_name in sorted(var_names):
            flux33_file = self.image_dir / f"flux_33_{var_name}_025deg.png"
            flux34_file = self.image_dir / f"flux_34_{var_name}_025deg.png"
            
            if flux33_file.exists() and flux34_file.exists():
                html_content += f'''
        <div class="pair">
            <div>
                <h2>flux_33 - {var_name} (0.25° grid)</h2>
                <img src="images/{flux33_file.name}" alt="flux_33 {var_name} 0.25 degree">
            </div>
            <div>
                <h2>flux_34 - {var_name} (0.25° grid)</h2>
                <img src="images/{flux34_file.name}" alt="flux_34 {var_name} 0.25 degree">
            </div>
        </div>
'''

        # Add stats and skipped files
        html_content += f'''
    </div>
</div>

<div class="stats">
    <h2>Processing Statistics</h2>
    <p>Total files processed: {len(self.plotted_files)}</p>
    <div class="skipped">
        <p><span class="toggle" onclick="toggleSkippedList()">Show/hide skipped files</span> (Total: {len(self.skipped_files)})</p>
        <div id="skippedList" class="skipped-list">
            <ul>
                {''.join(f"<li>{file}</li>" for file in sorted(self.skipped_files))}
            </ul>
        </div>
    </div>
</div>

<script>
function toggleSkippedList() {{
    var list = document.getElementById("skippedList");
    if (list.style.display === "block") {{
        list.style.display = "none";
    }} else {{
        list.style.display = "block";
    }}
}}

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
            lon = grid_ds['A096.lon'].values.reshape(1, -1)[0]
            lat = grid_ds['A096.lat'].values.reshape(1, -1)[0]
            return lon, lat
        elif coord_type == 'feom':
            lon = grid_ds['feom.lon'].values.reshape(1, -1)[0]
            lat = grid_ds['feom.lat'].values.reshape(1, -1)[0]
            return lon, lat
        else:  # RnfA
            return grid_ds['RnfA.lon'].values, grid_ds['RnfA.lat'].values
    
    def _create_plot(self, nc_file, var_name, lon, lat, var_data, is_remapped):
        """Create a plot for the given data."""
        # Create output path
        output_path = self.image_dir / f"{nc_file.parent.name}_{var_name}{'_025deg' if is_remapped else ''}.png"
        
        # Create new figure
        fig = plt.figure(figsize=(20, 12))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.coastlines()
        ax.gridlines()
        
        # Plot data with fixed color range
        vmin, vmax = -1, 1  # Default range for zero data
        if not np.all(var_data == 0):
            valid_data = var_data[~np.isnan(var_data) & (var_data != 0)]
            if valid_data.size > 0:
                vmin, vmax = valid_data.min(), valid_data.max()
        
        mesh = ax.pcolormesh(lon, lat, var_data, transform=ccrs.PlateCarree(), vmin=vmin, vmax=vmax)
        cbar = fig.colorbar(mesh, ax=ax, fraction=0.02, pad=0.04)
        
        cbar.set_label(var_name, rotation=270, labelpad=15)
        plt.title(f"{nc_file.parent.name} - {nc_file.stem}" + (" (0.25° grid)" if is_remapped else ""))
        
        # Save plot with higher DPI
        fig.canvas.draw()  # Force draw before saving
        fig.savefig(str(output_path), dpi=300, bbox_inches='tight', pad_inches=0.1)
        
        # Clean up
        plt.close(fig)
        plt.close('all')
        gc.collect()
    
    @dask.delayed
    def process_file(self, nc_file: Path, grid_ds: xr.Dataset):
        """Process a single netCDF file and create its plot."""
        # Skip grids file
        if nc_file.name == 'grids.nc':
            return

        # Skip files that aren't for the configured timestep
        if f"t={self.timestep}" not in nc_file.name:
            self.skipped_files.append(nc_file.name)
            return
        
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
                var_data = ds[var_name].values
                
                # For 3D variables with time, extract the timestep
                if var_data.ndim > 2 and var_data.shape[0] in [1, 2]:
                    var_data = var_data[0, ...]
        except Exception as e:
            print(f"Error processing {nc_file}: {e}")
            self.skipped_files.append(nc_file.name)
            return
            
        # Replace NaNs with zeros
        var_data = np.nan_to_num(var_data, nan=0.0)
        
        # Get coordinates
        lon, lat = self.get_coordinates(nc_file.parent.name, grid_ds, coord_type)
        
        # Generate standard resolution plot
        self._create_plot(nc_file, var_name, lon, lat, var_data, False)
        
        # Generate quarter degree resolution plot
        if self.remap_quarter_degree:
            remapped_data = self.remap_to_quarter_degree(lon, lat, var_data)
            self._create_plot(nc_file, var_name, self.target_lon_mesh, self.target_lat_mesh, remapped_data, True)
        
        self.plotted_files.append(nc_file.name)
    
    def process_folder(self, folder: str):
        """Process all files in a folder with parallel processing."""
        folder_path = self.base_dir / 'data' / folder
        
        # Load grids once for the folder
        chunks = {'x_A096': 4032, 'x_feom': 12685}
        with xr.open_dataset(folder_path / 'grids.nc', chunks=chunks) as grid_ds:
            # Create list of delayed tasks
            tasks = [self.process_file(nc_file, grid_ds) for nc_file in folder_path.glob('*.nc')]
            
            # Execute tasks in parallel with progress bar
            with ProgressBar():
                dask.compute(*tasks)

if __name__ == "__main__":
    plotter = FluxPlotter(base_dir="/Users/jstreffi/software/plot_fluxes", timestep=1, remap_quarter_degree=True)
    
    for folder in ['flux_33', 'flux_34']:
        print(f"Processing folder: {folder}")
        plotter.process_folder(folder)
    
    # Generate HTML comparison
    plotter.generate_html()
    print(f"Comparison HTML generated at: {plotter.output_dir / 'comparison.html'}")
