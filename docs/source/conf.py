# Configuration file for the Sphinx documentation builder.
import sys
from unittest.mock import MagicMock

# -- Mock modules that are difficult to install on ReadTheDocs ------------------
class Mock(MagicMock):
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()

# List of modules to mock for ReadTheDocs
MOCK_MODULES = ['numpy', 'matplotlib', 'matplotlib.pyplot', 'xarray', 'cartopy', 
                'cartopy.crs', 'dask', 'scipy', 'scipy.interpolate', 'netCDF4']
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)

# -- Project information -----------------------------------------------------
project = 'OASIS Coupling Flux Visualization'
copyright = '2025, Jan Streffing'
author = 'Jan Streffing'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx_rtd_theme',
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- Extension configurations ------------------------------------------------
autodoc_member_order = 'bysource'

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'matplotlib': ('https://matplotlib.org/stable/', None),
}
