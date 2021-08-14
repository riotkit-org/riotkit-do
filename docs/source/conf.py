import os
from distutils.version import LooseVersion
import sphinx_material

project = "Riotkit-Do: Universal automation (DevOps) tool for elastic, shareable tasks and pipelines"
html_title = "Riotkit-Do: Universal automation (DevOps) tool for elastic, shareable tasks and pipelines"

copyright = "2021, Riotkit"
author = "Riotkit"

# The full version, including alpha/beta/rc tags
release = LooseVersion(sphinx_material.__version__).vstring

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx_tabs.tabs",
    "sphinxcontrib.jinja"
]

jinja_contexts = {
    'py_publish': {
        'PKG_NAME': 'rkd_python',
        'PKG_CLASS_NAME': 'rkd_python.PublishTask',
        'PKG_PIP': 'rkd_python'
    },
    'py_build': {
        'PKG_NAME': 'rkd_python',
        'PKG_CLASS_NAME': 'rkd_python.BuildTask',
        'PKG_PIP': 'rkd_python'
    },
    'py_install': {
        'PKG_NAME': 'rkd_python',
        'PKG_CLASS_NAME': 'rkd_python.InstallTask',
        'PKG_PIP': 'rkd_python'
    },
    'py_clean': {
        'PKG_NAME': 'rkd_python',
        'PKG_CLASS_NAME': 'rkd_python.CleanTask',
        'PKG_PIP': 'rkd_python'
    },
    'py_unittest': {
        'PKG_NAME': 'rkd_python',
        'PKG_CLASS_NAME': 'rkd_python.UnitTestTask',
        'PKG_PIP': 'rkd_python'
    },
    'shell': {
        'PKG_NAME': 'rkd.core.standardlib.shell',
        'PKG_CLASS_NAME': 'rkd.core.standardlib.shell.ShellCommandTask',
        'PKG_PIP': 'rkd'
    },
    'exec': {
        'PKG_NAME': 'rkd.core.standardlib.shell',
        'PKG_CLASS_NAME': 'rkd.core.standardlib.shell.ExecProcessCommand',
        'PKG_PIP': 'rkd'
    },
    'j2_render': {
        'PKG_NAME': 'rkd.core.standardlib.jinja',
        'PKG_CLASS_NAME': 'rkd.core.standardlib.jinja.FileRendererTask',
        'PKG_PIP': 'rkd'
    },
    'j2_directory_to_directory': {
        'PKG_NAME': 'rkd.core.standardlib.jinja',
        'PKG_CLASS_NAME': 'rkd.core.standardlib.jinja.RenderDirectoryTask',
        'PKG_PIP': 'rkd'
    },
    'init': {
        'PKG_NAME': 'rkd.core.standardlib',
        'PKG_CLASS_NAME': 'rkd.core.standardlib.InitTask',
        'PKG_PIP': 'rkd'
    },
    'tasks': {
        'PKG_NAME': 'rkd.core.standardlib',
        'PKG_CLASS_NAME': 'rkd.core.standardlib.TasksListingTask',
        'PKG_PIP': 'rkd'
    },
    'callable_task': {
        'PKG_NAME': 'rkd.core.standardlib',
        'PKG_CLASS_NAME': 'rkd.core.standardlib.CallableTask',
        'PKG_PIP': 'rkd'
    },
    'rkd_create_structure': {
        'PKG_NAME': 'rkd.core.standardlib',
        'PKG_CLASS_NAME': 'rkd.core.standardlib.CreateStructureTask',
        'PKG_PIP': 'rkd'
    },
    'version': {
        'PKG_NAME': 'rkd.core.standardlib',
        'PKG_CLASS_NAME': 'rkd.core.standardlib.VersionTask',
        'PKG_PIP': 'rkd'
    },
    'env_get': {
        'PKG_NAME': 'rkd.core.standardlib.env',
        'PKG_CLASS_NAME': 'rkd.core.standardlib.env.SetEnvTask',
        'PKG_PIP': 'rkd'
    },
    'env_set': {
        'PKG_NAME': 'rkd.core.standardlib.env',
        'PKG_CLASS_NAME': 'rkd.core.standardlib.env.GetEnvTask',
        'PKG_PIP': 'rkd'
    },
    'line_in_file': {
        'PKG_NAME': 'rkd.core.standardlib',
        'PKG_CLASS_NAME': 'rkd.core.standardlib.LineInFileTask',
        'PKG_PIP': 'rkd'
    },
    'ArchivePackagingBaseTask': {
        'PKG_NAME': 'rkd.core.standardlib.io',
        'PKG_CLASS_NAME': 'rkd.core.standardlib.io.ArchivePackagingBaseTask',
        'PKG_PIP': 'rkd'
    },
    'PhpScriptTask': {
        'PKG_NAME': 'rkd.php.script',
        'PKG_CLASS_NAME': 'rkd.php.script.PhpScriptTask',
        'PKG_PIP': 'rkd.php'
    },
    'RunInContainerBaseTask': {
        'PKG_NAME': 'rkd.core.standardlib.docker',
        'PKG_CLASS_NAME': 'rkd.core.standardlib.docker.RunInContainerBaseTask',
        'PKG_PIP': 'rkd'
    }
}

jinja_base = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + '/../')

autosummary_generate = True
autoclass_content = "class"

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

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named 'default.css' will overwrite the builtin 'default.css'.
html_static_path = ["_static"]

# -- HTML theme settings ------------------------------------------------

html_show_sourcelink = True
html_sidebars = {
    "**": ["logo-text.html", "globaltoc.html", "localtoc.html", "searchbox.html"]
}

extensions.append("sphinx_material")
html_theme_path = sphinx_material.html_theme_path()
html_context = sphinx_material.get_html_context()
html_theme = "sphinx_material"

html_css_files = [
    'css/riotkit.css',
]

# material theme options (see theme.conf for more information)
html_theme_options = {
    "base_url": "https://riotkit-do.readthedocs.io/",
    "repo_url": "https://github.com/riotkit-org/riotkit-do/",
    "repo_name": "Riotkit-Do",
    "html_minify": False,
    "html_prettify": True,
    "css_minify": True,
    "logo_icon": "&#xe869",
    "repo_type": "github",
    "globaltoc_depth": 2,
    "color_primary": "blue",
    "color_accent": "cyan",
    "touch_icon": "images/apple-icon-152x152.png",
    "theme_color": "#2196f3",
    "master_doc": False,
    "nav_links": [
        {
            "href": "https://github.com/riotkit-org",
            "internal": False,
            "title": "Riotkit organization",
        },
        {
            "href": "https://github.com/riotkit-org/riotkit-harbor",
            "internal": False,
            "title": "Riotkit Harbor",
        },
    ],
    "heroes": {
    },
    "version_dropdown": False,
    # "version_json": "_static/versions.json",
    # "version_info": {
    #     "Release": "https://bashtage.github.io/sphinx-material/",
    #     "Development": "https://bashtage.github.io/sphinx-material/devel/",
    #     "Release (rel)": "/sphinx-material/",
    #     "Development (rel)": "/sphinx-material/devel/",
    # },
    "table_classes": ["plain"],
}

language = "en"
html_last_updated_fmt = ""

todo_include_todos = True
html_favicon = "images/favicon.ico"

html_use_index = True
html_domain_indices = True

nbsphinx_execute = "always"
nbsphinx_kernel_name = "python3"
