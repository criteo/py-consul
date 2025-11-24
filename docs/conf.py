# Configuration file for the Sphinx documentation builder.
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'py-consul'
copyright = '2025, Criteo'
author = 'Criteo'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",  # Link to other project docs (e.g., Python stdlib)
    "sphinx.ext.viewcode",      # Add links to source code
    "myst_parser",
]

# Autodoc settings
autoclass_content = 'both'
autodoc_member_order = 'bysource'  # Keep source order instead of alphabetical
autodoc_typehints = 'description'  # Show type hints in description, not signature
# Intersphinx - link to external docs
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'

# Furo theme options
html_theme_options = {
    "source_repository": "https://github.com/criteo/py-consul/",
    "source_branch": "master",
    "source_directory": "docs/",
    "navigation_with_keys": True,
    "top_of_page_button": "edit",
}

# Show "Edit on GitHub" links
html_context = {
    "display_github": True,
    "github_user": "criteo",
    "github_repo": "py-consul",
    "github_version": "master",
    "conf_py_path": "/docs/",
}

# Show deeper TOC levels in sidebar for better subpage navigation
html_sidebars = {
    "**": [
        "sidebar/scroll-start.html",
        "sidebar/brand.html",
        "sidebar/search.html",
        "sidebar/navigation.html",
        "sidebar/ethical-ads.html",
        "sidebar/scroll-end.html",
    ]
}