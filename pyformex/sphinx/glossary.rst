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



.. _glossary:

########
Glossary
########

.. topic:: Abstract

   This glossary contains the description of terms used throughout the
   pyFormex documentation and that might not be immediately clear to
   first time users. Since it is expected that users will have at least
   a basic knowledge of Python, typical Python terms will not be explained
   here. Some NumPy terms are included.


.. glossary::

    array_like
        Any sequence that can be interpreted as an ndarray. This includes
        nested lists, tuples, scalars and existing arrays.

    color_like
        Any object that is acceptable as input to the :func:`colors.GLcolor`
	function. This includes  GLcolor

    coords_like
        Either a Coords or data that can be used to initialize a Coords.

    eltype_like
        Either an ElementType instance or the name of such an instance.

    file_like
        An object supporting the write(bytes) method, like a file opened
        in binary write mode.

    file_type
        A string that is the key of one of the defined :class:`FileType`
        instances. It often is the file name suffix in lower case and
	without leading dot, though it can also be an alias for multiple
        file types.

    file_types
        A :term:`file_type` string or a tuple or list of such strings.

    index
        An object that can be used as an index in a numpy ndarray.
        This includes Python style slicing and numpy advanced indexing.

    level
        The dimensionality of a basic geometric entity. The highest level (3)
        are volumetric entities (cells). Surfaces (and faces of cells) are
        level 2. Lines (including face edges) are level 1. Finally, points
        are level 0.

    line_like
        An object that can be used to initialize a :class:`Lines` instance.
        This includes a (...,2,3) shaped array containing two points on the
        lines, or a tuple of (...,3) shaped arrays containing one point and
        a direction vector.

    mapping
        A container object that supports arbitrary key lookups. Examples
	include Python's dict, defaultdict, OrderedDict and pyFormex's
	:class:`Dict` and :class:`CDict`.

    mesh
        A geometric model where entities are represented by a combination
	of a table of coordinates of all points (nodes) and a connectivity
	table holding for each element the indices of the included nodes.

    node
        A point in a :term:`mesh` type geometric model.

    path_like
        An object that holds the path name of a file or directory.
	It can be a pure `str` or a :class:`Path`.

    plexitude
        The number of points used to describe a basic geometric entity.
        For example, a straight line segment has plexitude 2, a triangle
        has plexitude 3, a quadrilateral and a tetrahedron have plexitude 4.
	And a point obviously hjas plexitude 1.

    qimage_like
        A QImage, or data that can be converted to a QImage, e.g. the name of
        a raster image file.

    re
        A Python regular expression.

    seed
        Data that can be used as argument in the :func:`~arraytools.smartSeed`
	function. This means either a single int, a tuple containing an int
        ant optionally one or two end attractors, or a sorted list of float
        values in the range 0.0 to 1.0.

    varray_like
        Any data that are acceptable as input for the :class:`~varray.Varray`
	constructor.

    vector_like
        A tuple, list or array of three float values (x,y,z).

.. End
