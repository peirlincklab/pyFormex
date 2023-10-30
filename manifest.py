#!/usr/bin/env python3
##
##  SPDX-FileCopyrightText: © 2007-2023 Benedict Verhegghe <bverheg@gmail.com>
##  SPDX-License-Identifier: GPL-3.0-or-later
##
##  This file is part of pyFormex 3.3  (Sun Mar 26 20:16:15 CEST 2023)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: https://pyformex.org
##  Project page: https://savannah.nongnu.org/projects/pyformex/
##  Development: https://gitlab.com/bverheg/pyformex
##  Distributed under the GNU General Public License version 3 or later.
##
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see http://www.gnu.org/licenses/.
##
#
"""manifest.py

This script creates the list of files to be included in
the pyFormex source distribution.
"""
from importlib.machinery import SourceFileLoader
path = SourceFileLoader("path","pyformex/path.py").load_module()
from path import Path
def listTree(path, *args, **kargs):
    return Path(path).listTree(*args, **kargs)

# pyFormex documentation files
DOC_FILES = listTree(
    'pyformex/doc', maxdepth=0, ftypes='f',
    includefile=[
        'README.rst',
        'Description',
        'LICENSE',
        'ReleaseNotes',
    ],
) + listTree(
    'pyformex/doc/html', ftypes='f',
)

# pyFormex data files (installed in the pyformex tree)
DATA_FILES = listTree(
    'pyformex/data',
    excludedir=['benchmark','ply'],
    excludefile=['.*\.pyc','.*~$','PTAPE.*'],
    includefile=[
        'README',
        'benedict_6\.jpg',
        'bifurcation\.off.gz',
        'blippo\.pgf',
        'blippok\.ttf',
        'butterfly\.png',
        'fewgl\.js',
        'hesperia-nieve\.prop',
        'horse\.off',
        'horse\.pgf',
        'image_not_loaded\.png',
        'man\.off',
        'man\.pgf',
        'mark_cross\.png',
        'materials\.json',
        'sections\.json',
        'splines\.pgf',
        'supershape\.txt',
        'teapot1\.off',
        'template.py',
        'world\.jpg',
        'xtk_xdat\.gui\.js',
        ],
) + listTree('pyformex/scripts',
) + listTree('pyformex/glsl', ftypes='f', includefile=['.*\.c',],
) + listTree('pyformex/fonts', includefile=['.*\.png',],
)

# scripts to install extra programs
EXTRA_FILES = listTree(
    'pyformex/extra',
    includedir=[
        'calpy',
        'dxfparser',
        'gts',
        'instant',
        'postabq',
        'pygl2ps',
        ],
    excludefile=['.*~$'],
    includefile=[
        'README',
        'Makefile',
        '.*\.sh$',
        '.*\.rst$',
        '.*\.patch$',
        '.*\.c$',
        '.*\.cc$',
        '.*\.h$',
        '.*\.i$',
        '.*\.py$',
        '.*\.1$',
        '.*\.pc$',
        ],
    )

# Data files to be installed outside the pyformex tree
# These are tuples (installdir,filelist)
OTHER_DATA = [
    ('share/pixmaps', [
        'pyformex/icons/pyformex-64x64.png',
        'pyformex/icons/pyformex.xpm',
        ]),
    ('share/applications', ['pyformex.desktop']),
    ('share/man/man1', [
        'pyformex/doc/pyformex.1',
        ]),
    # the full html documentation
    ## ('share/doc/pyformex/html',DOC_FILES),
    ]

DIST_FILES = [
    'README.rst',
    'LICENSE',
    'Description',
    'install.sh',
    'apt_install_deps',
    'ReleaseNotes',
    'manifest.py',
    'setup.py',
    'setup.cfg',
    ] + \
    listTree('pyformex',
             includedir=['gui','menus','plugins','opengl',
                          'fe','appsdir'],   # DO NOT ADD scripts HERE
             includefile=['.*\.py$','pyformex(rc)?$','pyformex.conf$'],
             excludefile=[],
             ) + \
    listTree('pyformex/freetype',
             includedir=['ft_enums'],
             includefile=['.*\.py$'],
             ) + \
    listTree('pyformex/icons', ftypes='f',
             includefile=['README','.*\.xpm$','.*\.png$','.*\.gif$']
             ) + \
    listTree('pyformex/lib',
             includefile=['.*\.c$','.*\.py$','.*\.pyx$']
             ) + \
    listTree('pyformex/bin',
             excludefile=['.*~$'],
             ) + \
    listTree('pyformex/examples',
             excludedir=['Demos'],
             excludefile=['.*\.pyc','.*~$',
                           ],
             includefile=['[_A-Z].*\.py$','apps.cat','README']
             ) + \
    DATA_FILES + \
    DOC_FILES + \
    EXTRA_FILES


for i in OTHER_DATA:
    DIST_FILES += i[1]


if __name__ == '__main__':
    import sys

    todo = sys.argv[1:]
    if not todo:
        todo = ['usage']

    for a in todo:
        if a == 'doc':
            print("=========DOC_FILES=========")
            print('\n'.join(DOC_FILES))
        elif a == 'data':
            print("=========DATA_FILES========")
            print('\n'.join(DATA_FILES))
        elif a == 'other':
            print("=========OTHER_DATA========")
            for i in OTHER_DATA:
                print('\n'.join(i[1]))
        elif a == 'dist':
            print("=========DIST_FILES========")
            print('\n'.join(DIST_FILES))
        elif a == 'manifest':
            with open('MANIFEST', 'wt') as fil:
                fil.write('\n'.join(DIST_FILES))
                fil.write('\n')
            print("Created new MANIFEST")
        else:
            print("""\
Usage: manifest.py CMD [...]
where CMD is one of:
doc data other dist manifest
""")



# End
