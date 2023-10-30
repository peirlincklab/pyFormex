#
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

"""Try to read all .pyf files in some directory (and its subdirs)

The script will ask to select a directory name, lookup all '*.pyf'
file below that path, and then try to read each of this project files.

This script is intended to test whether your files can still be opened
and read in newer pyFormex versions.

In case of failures, set the PROJECT debug flag to get more info.

"""


dirname = pf.pyformexdir / 'pyformex' / 'data'
dirname = askDirname(dirname)
files = dirname.listTree(includefile='.*\.pyf')


def test_open_project(f):
    try:
        P = Project(f)
        print(P.keys())
        print("OK")
        return P
    except Exception as e:
        print(e)
        print("FAIL")

for f in sorted(files):
    print("="*72)
    print("Filename: %s" % f)
    P = test_open_project(f)


# End
