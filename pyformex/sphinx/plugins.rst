.. % pyformex manual --- plugins
  
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
  
  
..
  This file is part of pyFormex 1.0.5  (Thu Jun 21 13:57:46 CEST 2018)
  pyFormex is a tool for generating, manipulating and transforming 3D
  geometrical models by sequences of mathematical operations.
  Home page: http://pyformex.org
  Project page:  http://savannah.nongnu.org/projects/pyformex/
  Copyright 2004-2018 (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
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
  
  
.. _cha:plugins:

****************
pyFormex plugins
****************


.. topic:: Abstract

   This chapter describes how to create plugins for and documents some of the
   standard plugins that come with the pyFormex distribution.


.. _sec:plugins-def:

What are plugins?
=================

From its inception was intended to be easily expandable. Its open  architecture
allows educated users to change the behavior of and to extend its functionality
in any way they want. There are no fixed rules to obey and there is no registrar
to accept and/or validate the provided plugins. In , any  set of functions that
are not an essential part of can be called a 'plugin', if its functionality can
usefully be called from elsewhere and if the source can be placed inside the
distribution.

Thus, we distinct plugins from the vital parts of which comprehense the basic
data types (Formex), the scripting facilities, the (OpenGL) drawing
functionality and the graphical user interface. We also distinct plugins from
normal (example and user) scripts because the latter will usually be intended to
execute some specific task, while the former will often only provide some
functionality without themselves performing some actions.

To clarify this distinction, plugins are located in a separate subdirectory
``plugins`` of the tree. This directory should not be used for anything else.

The extensions provided by the plugins usually fall within one of the following
categories:

Functional
   Extending the functionality by providing new data types and functions.

External
   Providing access to external programs, either by dedicated interfaces or through
   the command shell and file system.

GUI
   Extending the graphical user interface of .

The next section of this chapter gives some recommendations on how to structure
the plugins so that they work well with . The remainder of the chapter discusses
some of the most important plugins included with .


.. _sec:plugins-create:

How to create a plugin.
=======================

.. End
