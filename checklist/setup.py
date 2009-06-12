#!/usr/bin/env python
from distutils.core import setup
import py2exe
import os


setup(
name='weddingchecklist',
version='0.1',

windows=[{
    'script': 'wedding_checklist',
    'icon_resources': [(1, 'logo.png')]
    }],

data_files=[
("ui.glade", "wedding-banner.png", "checklist.sqlite")],

options = {
'py2exe' : {
  'packages': 'encodings',
    'includes': 'cairo, pango, pangocairo, atk, gobject',
  'excludes' : ['_ssl', 'inspect', 'pdb', 'difflib', 'doctest', 'locale', 'calendar']
},
#'sdist': {
#  'formats': 'zip',
#}

}
)
