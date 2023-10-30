..  -*- rst -*-
  
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
  
  
What is pyFormex?
=================
pyFormex is a tool for generating, manipulating and transforming large
geometrical models of 3D structures by sequences of mathematical
transformations. Thanks to a powerful (Python3 based) scripting language,
pyFormex is very well suited for the automated design of spatial frame
structures. It provides a wide range of operations on surface meshes,
like STL type triangulated surfaces. There are provisions to import medical
scan images. pyFormex can also be used as a pre- and post-processor for
Finite Element analysis programs. Finally, it might be used just for
creating some nice graphics.

Using pyFormex, the topology of the elements and the final geometrical form
can be decoupled. Often, topology is created first and then mapped onto the
geometry. Through the scripting language, the user can define any sequence
of transformations, built from provided or user defined functions.
This way, building parametric models becomes a natural thing.

The pyFormex core functionality and scripting language have become fairly
stable. Its OpenGL GUI environment for displaying and manipulating the
generated structures provides a wide range of features and is easily
expandable.

The project page for pyFormex development, support and bug reports is at
http://savannah.nongnu.org/projects/pyformex/.


Installation
============

Quick installation from official .tar.gz release or from git clone:

1. Install dependencies. On recent Debian/Ubuntu you can just run::

     sudo ./apt_install_deps

2. Install pyFormex. This can be done either in user space, or system-wide
   (as root)::

     ./install.sh all

   or ::

     sudo ./install.sh all

   In the first case, the executable is installed under $HOME/.local/bin.
   For the system-wide installation, the executable is in /usr/local/bin.

   As of version 2.7 of pyFormex, the default installation allows for
   multiple versions being installed in parallel, and the executable is
   named pyformex-VERSION, where VERSION is the version designator.

   Add a '-d' to the install.sh options to make the installed version
   the default by linking this executable under the generic name 'pyformex'.

For more information see the installation manual at
http://www.nongnu.org/pyformex/doc-2.0/index.html
or if you have the pyFormex source tree, read the file
``sphinx/install.rst``.


Documentation
=============

The documentation is included with the pyFormex distribution. Execute the command
pyformex --whereami to find out where the pyformex files are
installed. The pyformex path contains a directory doc/html with the
full html ocumentation.
When working with the pyFormex GUI, you can load this local documentation in
your browser using the help menu, or view the online documentation at
http://pyformex.org/doc.

To use pyFormex, you create a script that builds a structure layout and
geometry. Look at the examples to get the feeling of how it is working.
Use the File->Play menu selection to display the structure.

The examples and the Python source are fairly well documented.


Help and Feedback
=================

For any questions or feedback, please go to the pyFormex support tracker at
http://savannah.nongnu.org/support/?group=pyformex

If you find any bugs or malfunctions in pyFormex, please submit them to
the pyFormex Bug tracker http://savannah.nongnu.org/bugs/?group=pyformex

.. _`GIT repository`: http://savannah.nongnu.org/git/?group=pyformex

.. target-notes::

Copyright
=========

pyFormex is distributed under the GNU GPL version 3 or later.

.. End
