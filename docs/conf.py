# Configuration file for the Sphinx documentation builder.
# Minimal settings so `sphinx-build` runs without error.

project = 'Astra Userbot'
copyright = '2026'
author = 'Aman Kumar Pandey'

extensions = []

# The master toctree document.
master_doc = 'index'

# Add any Sphinx paths here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = []

# use a more modern theme similar to Telethon docs
html_theme = 'sphinx_rtd_theme'

# remove Sphinx branding in footer
html_theme_options = {
    'logo_only': False,
    'display_version': True,
}

# disable "built with Sphinx" message
html_show_sphinx = False

