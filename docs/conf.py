# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from datetime import datetime

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath(".."))
import consul  # noqa: E402

# -- Project information -----------------------------------------------------

project = "py-consul"
copyright = f"{datetime.now().year}, Criteo"
author = "Criteo"

# The full version, including alpha/beta/rc tags
version = consul.__version__
release = consul.__version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",  # For Google/NumPy style docstrings
    "myst_parser",          # For Markdown support
    "sphinx_rtd_theme",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# -- Extension configuration -------------------------------------------------
# myst_parser configuration
myst_enable_extensions = [
    "colon_fence",
]

# autodoc configuration
autodoc_member_order = "bysource"
autoclass_content = "both"

def clean_check_signature(app, what, name, obj, options, signature, return_annotation):
    if name.startswith("consul.Check") and signature:
        # Remove the first argument (klass) from the signature if present
        # This is a legacy fix from the old conf.py, might still be needed depending on how Check methods are defined
        if signature.startswith("(klass, "):
             return ("(" + signature[len("(klass, ") :], return_annotation)
    return (signature, return_annotation)


def setup(app):
    app.connect("autodoc-process-signature", clean_check_signature)
