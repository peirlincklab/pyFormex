..   -*- rst -*-

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


.. pyFormex documentation reference manual master file

.. include:: defines.inc
.. include:: links.inc


.. _cha:reference:

#########################
pyFormex reference manual
#########################

.. topic:: Abstract

   This is the reference manual for pyFormex |release|.
   It describes most of the classes and functions
   defined in the pyFormex modules. It was built automatically from
   the pyFormex sources and is therefore the ultimate reference
   document if you want to look up the precise arguments (and their meaning)
   of any class constructor or function in pyFormex. The :ref:`genindex`
   and :ref:`modindex` may be helpful in navigating through this
   document.

This reference manual describes the classes in functions defined in
most of the pyFormex modules. It was built automatically from the docstrings in
the pyFormex sources. The pyFormex modules are placed in three paths:

- ``pyformex`` contains the core functionality, with most of the
  geometrical transformations, the pyFormex scripting language and utilities,
- ``pyformex/gui`` contains all the modules that form the interactive
  graphical user interface,
- ``pyformex/plugins`` contains extensions that are not considered to
  be essential parts of pyFormex. They usually provide additional
  functionality for specific applications.

Some of the modules are loaded automatically when pyFormex is
started. Currently this is the case with the modules
:mod:`coords`, :mod:`formex`, :mod:`arraytools`, :mod:`script` and, if the GUI is used, :mod:`draw` and :mod:`colors`.
All the public definitions in these modules are available to pyFormex
scripts without explicitly importing them. Also available is the complete
:mod:`numpy` namespace, because it is imported by :mod:`arraytools`.

The definitions in the other modules can only be accessed using the
normal Python ``import`` statements.

.. _sec:autoloaded-modules:

Autoloaded modules
==================

The definitions in these modules are always available to your scripts, without
the need to explicitely import them.

.. mytoctree::
   :maxdepth: 1
   :numbered:
   :numberedfrom: -1

   ref/coords
   ref/formex
   ref/mesh
   ref/arraytools
   ref/script
   ref/gui.draw
   ref/colors


.. _sec:core-modules:

Other pyFormex core modules
===========================

Together with the autoloaded modules, the following modules located under the
main pyformex path are considered to belong to the pyformex core functionality.

.. mytoctree::
   :maxdepth: 1
   :numbered:
   :numberedfrom: -1

   ref/adjacency
   ref/apps
   ref/attributes
   ref/candy
   ref/cmdtools
   ref/collection
   ref/config
   ref/connectivity
   ref/coordsys
   ref/curve
   ref/database
   ref/elements
   ref/field
   ref/fileread
   ref/filetools
   ref/filewrite
   ref/flatkeydb
   ref/geometry
   ref/geomfile
   ref/geomtools
   ref/globalformat
   ref/inertia
   ref/main
   ref/multi
   ref/mydict
   ref/olist
   ref/options
   ref/path
   ref/polygons
   ref/process
   ref/project
   ref/pzffile
   ref/simple
   ref/software
   ref/timer
   ref/track
   ref/trisurface
   ref/utils
   ref/varray


..   ref/sendmail  currently fails to be imported

.. ref/track    errors on py2rst


.. _sec:gui-modules:

pyFormex GUI modules
====================

These modules create the components of the pyFormex GUI. They are located under pyformex/gui. They depend on the Qt4 framework.

.. mytoctree::
   :maxdepth: 1
   :numbered:
   :numberedfrom: -1

   ref/gui.appMenu
   ref/gui.colorscale
   ref/gui.dialogs
   ref/gui.drawlock
   ref/gui.guifunc
   ref/gui.guimain
   ref/gui.image
   ref/gui.menu
   ref/gui.pyconsole
   ref/gui.qtcanvas
   ref/gui.qtgl
   ref/gui.qtutils
   ref/gui.signals
   ref/gui.toolbar
   ref/gui.viewport
   ref/gui.views
   ref/gui.widgets


.. _sec:plugins-modules:

pyFormex plugins
================

Plugin modules extend the basic pyFormex functions to a variety of
specific applications. Apart from being located under the pyformex/plugins
path, these modules are in no way different from other pyFormex modules.

.. mytoctree::
   :maxdepth: 1
   :numbered:
   :numberedfrom: -1

   ref/plugins.bifmesh
   ref/plugins.cameratools
   ref/plugins.ccxdat
   ref/plugins.ccxinp
   ref/plugins.datareader
   ref/plugins.dicomstack
   ref/plugins.dxf
   ref/plugins.fe
   ref/plugins.fe_abq
   ref/plugins.fe_post
   ref/plugins.flavia
   ref/plugins.gts_itf
   ref/plugins.http_server
   ref/plugins.imagearray
   ref/plugins.isopar
   ref/plugins.isosurface
   ref/plugins.lima
   ref/plugins.mesh_io
   ref/plugins.neu_exp
   ref/plugins.nurbs
   ref/plugins.objects
   ref/plugins.partition
   ref/plugins.plot2d
   ref/plugins.polygon
   ref/plugins.polynomial
   ref/plugins.postproc
   ref/plugins.properties
   ref/plugins.section2d
   ref/plugins.sectionize
   ref/plugins.tetgen
   ref/plugins.tools
   ref/plugins.turtle
   ref/plugins.units
   ref/plugins.web
   ref/plugins.webgl

..   ref/plugins.calpy_itf
..   ref/plugins.centerline  still relevant?
..   ref/plugins.draw2d   gives errors on py2rst
..   ref/plugins.fe_ast  needs work
..   ref/plugins.f2flu  still relevant?
..   ref/plugins.formian
..   ref/plugins.plyfile
..   ref/plugins.surface_abq  still relevant?
..   ref/plugins.wrl    gives errors on py2rst

.. _sec:opengl-modules:

pyFormex OpenGL modules
=======================

These modules are responsible for rendering the 3D models and depend on OpenGL.
These modules are located under pyformex/opengl.

.. mytoctree::
   :maxdepth: 1
   :numbered:
   :numberedfrom: -1

   ref/opengl.actors
   ref/opengl.camera
   ref/opengl.canvas
   ref/opengl.canvas_settings
   ref/opengl.decors
   ref/opengl.drawable
   ref/opengl.matrix
   ref/opengl.objectdialog
   ref/opengl.renderer
   ref/opengl.sanitize
   ref/opengl.scene
   ref/opengl.shader
   ref/opengl.textext
   ref/opengl.texture

.. _sec:menu-modules:

pyFormex plugin menus
=====================

Plugin menus are optionally loadable menus for the pyFormex GUI, providing
specialized interactive functionality. Because these are still under heavy
development, they are currently not documented. Look to the source code or
try them out in the GUI. They can be loaded from the File menu option and
switched on permanently from the Settings menu.

Currently avaliable:

- geometry_menu
- formex_menu
- surface_menu
- tools_menu
- draw2d_menu
- nurbs_menu
- dxf_tools
- postproc_menu
- bifmesh_menu

.. - fe_menu     used?

.. _sec:lib-modules:

pyFormex acceleration library
=============================

The acceleration library contains some compiled C-versions of critical (parts of)
algorithms that are known to take long computing times that are unacceptable
for large data sets. Most of the functions in our C-libraries also
exist in a Python version. Those versions are intended for studying the
algorithm and as a last resort in case the C versions do not compile
on your system.
By default, pyFormex will try to compile and use the accelerated versions. You
can force the use of the slower Python versions by adding the ``--nouselib``
option to the pyformex command.

Normally the user should not have to call any of the library functions directly.
They can be accessed from Python wrapper functions
in the appropriate places. Be aware that, especially in the case of the
accelerated versions, one should pass the precise C-type objects.
The accelerated C-extensions have a name ending in _, the Python
versions end in _e. To import the modules, just use the name with underscore::

  from pyformex.lib import misc
  from pyformex.lib import nurbs
  from pyformex.lib import clust

The initialization code will have loaded the appropriate version already.

.. mytoctree::
   :maxdepth: 1
   :numbered:
   :numberedfrom: -1

   ref/lib.misc_c
   ref/lib.misc_e
   ref/lib.nurbs_c
   ref/lib.nurbs_e
   ref/lib.clust_c
   ref/lib.clust

.. End
