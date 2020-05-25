import sys
import os

sys.path = [os.path.dirname(os.path.realpath(__file__)) + "/../../src"] + sys.path

project = 'RiotKit Do'
copyright = '2019, RiotKit Collective'
author = 'RiotKit Collective'

version = ''
release = '1'

extensions = [
    'sphinx.ext.todo',
    'sphinx.ext.imgmath',
    'sphinx.ext.githubpages',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinxcontrib.jinja'
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
        'PKG_NAME': 'rkd.standardlib.shell',
        'PKG_CLASS_NAME': 'rkd.standardlib.shell.ShellCommandTask',
        'PKG_PIP': 'rkd'
    },
    'exec': {
        'PKG_NAME': 'rkd.standardlib.shell',
        'PKG_CLASS_NAME': 'rkd.standardlib.shell.ExecProcessCommand',
        'PKG_PIP': 'rkd'
    },
    'j2_render': {
        'PKG_NAME': 'rkd.standardlib.jinja',
        'PKG_CLASS_NAME': 'rkd.standardlib.jinja.FileRendererTask',
        'PKG_PIP': 'rkd'
    },
    'j2_directory_to_directory': {
        'PKG_NAME': 'rkd.standardlib.jinja',
        'PKG_CLASS_NAME': 'rkd.standardlib.jinja.RenderDirectoryTask',
        'PKG_PIP': 'rkd'
    },
    'docker_tag': {
        'PKG_NAME': 'rkd.standardlib.docker',
        'PKG_CLASS_NAME': 'rkd.standardlib.docker.TagImageTask',
        'PKG_PIP': 'rkd'
    },
    'docker_push': {
        'PKG_NAME': 'rkd.standardlib.docker',
        'PKG_CLASS_NAME': 'rkd.standardlib.docker.PushTask',
        'PKG_PIP': 'rkd'
    },
    'init': {
        'PKG_NAME': 'rkd.standardlib',
        'PKG_CLASS_NAME': 'rkd.standardlib.InitTask',
        'PKG_PIP': 'rkd'
    },
    'tasks': {
        'PKG_NAME': 'rkd.standardlib',
        'PKG_CLASS_NAME': 'rkd.standardlib.TasksListingTask',
        'PKG_PIP': 'rkd'
    },
    'callable_task': {
        'PKG_NAME': 'rkd.standardlib',
        'PKG_CLASS_NAME': 'rkd.standardlib.CallableTask',
        'PKG_PIP': 'rkd'
    },
    'rkd_create_structure': {
        'PKG_NAME': 'rkd.standardlib',
        'PKG_CLASS_NAME': 'rkd.standardlib.CreateStructureTask',
        'PKG_PIP': 'rkd'
    },
    'version': {
        'PKG_NAME': 'rkd.standardlib',
        'PKG_CLASS_NAME': 'rkd.standardlib.VersionTask',
        'PKG_PIP': 'rkd'
    }
}

jinja_base = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + '/../')

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
language = None
exclude_patterns = []
pygments_style = None

import sphinx_glpi_theme
html_theme = 'glpi'
html_theme_path = sphinx_glpi_theme.get_html_themes_path()

html_theme_options = {
    'body_max_width': None
}

html_css_files = [
    'css/riotkit.css',
]

html_static_path = ['_static']
htmlhelp_basename = 'RiotkitDoDoc'


latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'FileRepository.tex', 'RiotKit Do Documentation',
     'Wolnosciowiec Team', 'manual'),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'filerepository', 'RiotKit Do Documentation',
     [author], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'FileRepository', 'RiotKit Do Documentation',
     author, 'FileRepository', 'One line description of project.',
     'Miscellaneous'),
]


# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']


# -- Extension configuration -------------------------------------------------

# -- Options for todo extension ----------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True
