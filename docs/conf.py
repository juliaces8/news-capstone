import os
import sys
import django

# 1. Path Setup
sys.path.insert(0, os.path.abspath('..'))

# 2. Django Setup
os.environ['DJANGO_SETTINGS_MODULE'] = 'news_project.settings'
django.setup()

# 3. Mock External Libraries
autodoc_mock_imports = ["tweepy"]

# -- Project information -----------------------------------------------------
project = 'News-Final'
copyright = '2026, Julia C.'
author = 'Julia C.'
release = '1.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'alabaster'
html_static_path = ['_static']
