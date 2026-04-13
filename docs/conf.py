# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ecp.egov66.ru-timetable'
author = 'Матвей Вялков'
copyright = f'2026, {author}'
release = '2026.4.12.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosummary',
    'sphinx_prompt',
]

try:
    import notfound.extension
    extensions.append('notfound.extension')

    notfound_urls_prefix = None
except ModuleNotFoundError:
    pass

try:
    import sphinx_sitemap
    extensions.append('sphinx_sitemap')

    sitemap_locales = [None]
    sitemap_url_scheme = '{link}'
    sitemap_excludes = [
        '404.html',
    ]
    sitemap_show_lastmod = True
except ModuleNotFoundError:
    pass

try:
    import sphinxcontrib.spelling
    extensions.append('sphinxcontrib.spelling')

    spelling_lang = 'ru_RU'
    tokenizer_lang = 'ru_RU'
    spelling_word_list_filename = 'spelling_wordlist.txt'
except ModuleNotFoundError:
    pass

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

language = 'ru'

autosummary_generate = False
autodoc_default_options = {
    'show-inheritance': True,
    'undoc-members': True,
    'member-order': 'bysource',
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_permalinks_icon = '#'
html_theme_options = {
    'description': 'Просмотр расписания колледжей и техникумов Свердловской области',
    'canonical_url': 'https://acme-corp.altlinux.team/ecp.egov66.ru-timetable/',
}
html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'searchbox.html',
    ]
}

html_static_path = ['_static']
html_title = f'{project} {release}'
html_baseurl = 'https://acme-corp.altlinux.team/ecp.egov66.ru-timetable/'

# -- Options for intersphinx extension ---------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'bs4': ('https://www.crummy.com/software/BeautifulSoup/bs4/doc/', None),
    'jinja2': ('https://jinja.palletsprojects.com/en/stable/', None),
    'pydantic': ('https://docs.pydantic.dev/latest/', None),
}
