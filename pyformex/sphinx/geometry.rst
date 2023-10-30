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
  
  
.. include:: defines.inc
.. include:: links.inc

.. _cha:geometry:

*******************************
Modeling Geometry with pyFormex
*******************************

.. warning:: This document is under construction!

.. topic:: Abstract

  This chapter explains the different geometrical models in pyFormex,
  how and when to use them, how to convert between them, how to import
  and export them in various formats.

.. _sec:geom_intro:

Introduction
============

  *Everything is geometry*

In everyday life, geometry is ubiquitous. Just look around you: all the things you see, whether objects or living organisms or natural phenomena like clouds, they all have a shape or geometry. This holds for all concrete things, even if they are ungraspable, like a rainbow, or have no defined or fixed shape, like water. The latter evidently takes the shape of its container. Only abstract concepts do not have a geometry. Any material thing has though [#quantum]_, hence our claim: everything is geometry.

Since geometry is such an important aspect of everybody's life, one would expect that it would take an important place in education (base as well as higher). Yet we see that in the educational system of many developed countries, attention for geometry has vaned during the last decades.
Important for craftsmen, technician, engineer, designer, artist

We will give some general ideas about geometry, but do not pretend to be a full
geometry course. Only concepts needed for or related to modleing with pyFormex.

We could define the geometry of an object as the space it occupies. In our three-dimensional world, any object is also 3D. Some objects however have very small dimensions in one or more directions (e.g. a thin wire or a sheet of paper). It may be convenient then to model these only in one or two dimensions. [#4d]_


Concrete things also have a material. THIngs going wrong is mostly mechanical: geometry/materail

.. [#quantum] We obviously look here at matter in the way we observe it with our senses (visual, tactile) and not in a quantum-mechanics way.
.. [#4d] Mathematically we can also define geometry with higher dimensionality than 3, but this is of little practical use.


.. _sec:formex_model:

The **Formex** model
====================

.. _sec:mesh_model:

The **Mesh** model
==================

.. _sec:trisurface_model:

The **TriSurface** model
========================

.. _sec:curve_model:

The **Curve** model
===================

.. _sec:subclassing_geometry:

Subclassing Geometry
====================

The __init__ method of the derived class should at least call
Geometry.__init__(self) and then assign a :class:`~coords.Coords`
to self.coords. Furthermore, the class should override the
:meth:`nelems` method. Then a newly created instance of the subclass
will at least have these attributes:

Derived classes can (and in most cases should) declare a method
`_set_coords(coords)` returning an object that is identical to the
original, except for its coords being replaced by new ones with the
same array shape.

The Geometry class provides two possible default implementations:

- `_set_coords_inplace` sets the coords attribute to the provided new
  coords, thus changing the object itself, and returns itself,
- `_set_coords_copy` creates a deep copy of the object before setting
  the coords attribute. The original object is unchanged, the returned
  one is the changed copy.

When using the first method, a statement like ``B = A.scale(0.5)``
will result in both `A` and `B` pointing to the same scaled object,
while with the second method, `A` would still be the untransformed
object. Since the latter is in line with the design philosophy of
pyFormex, it is set as the default `_set_coords` method.
Many derived classes that are part of pyFormex override this
default and implement a more efficient copy method.

Derviced classes should immplement the _select method

 def _select(self,selected,**kargs):
        """Return a Formex only holding the selected elements.

The kargs can hold optional arguments:
compact = True/False

if the Coords modell can hold unused points that can be removed by
compacyion (the case with Mesh)


.. _sec:analytical_models:

Analytical models
=================



.. End
