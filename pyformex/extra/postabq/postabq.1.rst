..
  
..
  SPDX-FileCopyrightText: © 2007-2023 Benedict Verhegghe <bverheg@gmail.com>
  SPDX-License-Identifier: GPL-3.0-or-later
  
  This file is part of pyFormex 3.3  (Sun Mar 26 20:16:15 CEST 2023)
  pyFormex is a tool for generating, manipulating and transforming 3D
  geometrical models by sequences of mathematical operations.
  Home page: https://pyformex.org
  Project page: https://savannah.nongnu.org/projects/pyformex/
  Development: https://gitlab.com/bverheg/pyformex
  Distributed under the GNU General Public License version 3 or later.
  
  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.
  
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
  
  You should have received a copy of the GNU General Public License
  along with this program.  If not, see http://www.gnu.org/licenses/.
  
  
=======
postabq
=======

------------------------------------------------
Postprocess results from an Abaqus(C) simulation
------------------------------------------------

:Author: postabq was written by Benedict Verhegghe <benedict.verhegghe@ugent.be> for the pyFormex project. This manual page was written for the Debian project (and may be used by others).
:Date:   2012-08-08
:Copyright: GPL v3 or higher
:Version: 0.1
:Manual section: 1
:Manual group: text and X11 processing

SYNOPSIS
========

postabq [OPTIONS] FILE

DESCRIPTION
===========

postabq scans an Abaqus output file (.fil format) and converts the data
into a Python script that can be interpreted by the pyFormex fe_post plugin.
The Python script is written to stdout.

The postabq command is usually installed under the name 'pyformex-postabq'.

OPTIONS
=======

-v  Be verbose (mostly for debugging)
-e  Force EXPLICIT from the start (default is to autodetect)
-n  Dry run: run through the file but do not produce conversion
-h  Print this help text
-V  Print version and exit

SEE ALSO
========

The pyFormex project <https://savannah.nongnu.org/projects/pyformex/>.
