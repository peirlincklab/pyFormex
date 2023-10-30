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
  
  
Instant Meshes
--------------

Instant Meshes is a program that can remesh a sruface into high
quality triangle and/or quad surfaces.

See https://github.com/wjakob/instant-meshes for more information.

It is however not (yet?) available as ready-made packages in common
Linux distributions. This directory provides a Makefile that helps
you to install it.

It comes down to the following, and you can also do it by hand, if the
procedure doesn't suit your needs:

- download the program from https://github.com/wjakob/instant-meshes.
  (comes as a zipped ready to run binary)
- unzip the downloaded file somewhere in an executable path, e.g.
  your ~/bin, if that is in your PATH environment
- rename or symlink the 'Instant Meshes' binary to 'instant-meshes'

In commands::

  $ wget https://instant-meshes.s3.eu-central-1.amazonaws.com/instant-meshes-linux.zip
  $ unzip instant-meshes-linux.zip
  $ mv 'Instant Meshes' ~/bin
  $ ln -s 'Instant Meshes' ~/bin/instant-meshes

Then run ``pyFormex --detect`` to see if pyFormex can find it.

# End




CalculiX is a free Finite Element program (http://http://www.calculix.de/)
pyFormex can write input files for CalculiX and postprocess some results.
The following commands will install the CalculiX processor::

  apt install libgfortran4
  make download
  sudo make install

.. End
