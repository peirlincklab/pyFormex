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
#
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see http://www.gnu.org/licenses/.
##

"""Field data defined over a geometry.

This module defines the Field class, which can be used to describe
scalar and vectorial field data over a geometrical domain.
"""

import numpy as np

from pyformex import utils
import pyformex.arraytools as at

##############################################################


class Field():

    """Scalar or vectorial field data defined over a geometric domain.

    A scalar data field is a quantity having exactly one value in each
    point of some geometric domain. A vectorial field is a quantity having
    exactly `nval` values at each point, where `nval >= 1`.
    A vectorial field can also be considered as a collection of `nval`
    scalar fields: as far as the Field class is concerned, there is no
    relation between the `nval` components of a vectorial field.

    The definition of a field is always tied to some geometric domain.
    Currently pyFormex allows fields to be defined on Formex and Mesh
    type geometries.

    Fields should only be defined on geometries whose topology does not
    change anymore. This means that for Formex type, the shape of the
    `coords` attribute should not be changed, and for Mesh type, the
    shape of `coords` and the full contents of `elems` should not be
    changed. It is therefore best ot only add field data to geometry
    objects that will not be changed in place.
    Nearly all methods in pyFormex return a copy of the object, and the
    copy currently looses all the fields defined on the parent.
    In future however, selected transformations may inherit fields from
    the parent.

    While Field class instances are usually created automatically by the
    :func:`Geometry.addField` method of some Geometry,
    it is possible to create Field
    instances yourself and manage the objects like you want. The Fields
    stored inside Geometry objects have some special features though,
    like being exported to a PGF file together with the geometry.

    Parameters
    ----------
    geometry: :class:`Formex` | :class:`Mesh`
        Describes the geometrical domain over which the field is defined.
        Currently this has to be an instance of :class:`Formex` or
        :class:`Mesh` (or a subclass thereof).
    fldtype: str
        The field type, one of the following predefined strings:

        - 'node': the field data are specified at the nodes of the geometry;
        - 'elemc': the field data are constant per element;
        - 'elemn': the field data vary over the element and are specified at
          the nodes of the elements;
        - 'elemg': the field data are specified at a number of points of
          the elements, from which they can be inter- or extrapolated;

        The actually available field types depend on the type of the
        `geometry` object. :class:`Formex` type has only 'elemc' and 'elemn'.
        `Mesh` currently has 'node', 'elemc' and 'elemn'.
    data`: :term:`array_like`
        An array with the field values defined at the specified
        points. The required shape of the array depends on `fldtype`:

        - 'node':  ( nnodes, ) or ( nnodes, nval )
        - 'elemc': ( nelems, ) or ( nelems, nval )
        - 'elemn': ( nelems, nplex ) or  (nelems, nplex, nval )
        - 'elemg': ( nelems, ngp ) or  (nelems, ngp, nval )
    fldname: str, optional
        The name used to identify the field. Fields stored in a Geometry
        object can be retrieved using this name. See :func:`Geometry.getField`.
        If no name is specified, an automatic name is generated.

    Examples
    --------
    >>> from pyformex.formex import Formex
    >>> M = Formex('4:0123').replic(2).toMesh()
    >>> print(M.coords)
    [[0. 0. 0.]
     [0. 1. 0.]
     [1. 0. 0.]
     [1. 1. 0.]
     [2. 0. 0.]
     [2. 1. 0.]]
    >>> print(M.elems)
    [[0 2 3 1]
     [2 4 5 3]]
    >>> d = M.coords.distanceFromPlane([0.,0.,0.],[1.,0.,0.])
    >>> f1 = Field(M,'node',d)
    >>> print(f1)
    Field 'field-0', type 'node', shape (6,), nnodes=6, nelems=2, nplex=4
    [0. 0. 1. 1. 2. 2.]
    >>> f2 = f1.convert('elemn')
    >>> print(f2)
    Field 'field-1', type 'elemn', shape (2, 4), nnodes=6, nelems=2, nplex=4
    [[0. 1. 1. 0.]
     [1. 2. 2. 1.]]
    >>> f3 = f2.convert('elemc')
    >>> print(f3)
    Field 'field-2', type 'elemc', shape (2,), nnodes=6, nelems=2, nplex=4
    [0.5 1.5]
    >>> d1 = M.coords.distanceFromPlane([0.,0.,0.],[0.,1.,0.])
    >>> f4 = Field(M,'node',np.column_stack([d,d1]))
    >>> print(f4)
    Field 'field-3', type 'node', shape (6, 2), nnodes=6, nelems=2, nplex=4
    [[0. 0.]
     [0. 1.]
     [1. 0.]
     [1. 1.]
     [2. 0.]
     [2. 1.]]
    >>> f5 = f4.convert('elemn')
    >>> print(f5)
    Field 'field-4', type 'elemn', shape (2, 4, 2), nnodes=6, nelems=2, nplex=4
    [[[0. 0.]
      [1. 0.]
      [1. 1.]
      [0. 1.]]
    <BLANKLINE>
     [[1. 0.]
      [2. 0.]
      [2. 1.]
      [1. 1.]]]
    >>> f6 = f5.convert('elemc')
    >>> print(f6)
    Field 'field-5', type 'elemc', shape (2, 2), nnodes=6, nelems=2, nplex=4
    [[0.5 0.5]
     [1.5 0.5]]
    >>> print(f3.convert('elemn'))
    Field 'field-6', type 'elemn', shape (2, 4), nnodes=6, nelems=2, nplex=4
    [[0.5 0.5 0.5 0.5]
     [1.5 1.5 1.5 1.5]]
    >>> print(f3.convert('node'))
    Field 'field-8', type 'node', shape (6, 1), nnodes=6, nelems=2, nplex=4
    [[0.5]
     [0.5]
     [1. ]
     [1. ]
     [1.5]
     [1.5]]
    >>> print(f6.convert('elemn'))
    Field 'field-9', type 'elemn', shape (2, 4, 2), nnodes=6, nelems=2, nplex=4
    [[[0.5 0.5]
      [0.5 0.5]
      [0.5 0.5]
      [0.5 0.5]]
    <BLANKLINE>
     [[1.5 0.5]
      [1.5 0.5]
      [1.5 0.5]
      [1.5 0.5]]]
    >>> print(f6.convert('node'))
    Field 'field-11', type 'node', shape (6, 2), nnodes=6, nelems=2, nplex=4
    [[0.5 0.5]
     [0.5 0.5]
     [1.  0.5]
     [1.  0.5]
     [1.5 0.5]
     [1.5 0.5]]
    """

    _autoname = utils.autoName('Field')

    def __init__(self, geometry, fldtype, data, fldname=None):
        """Initialize a Field."""
        if not hasattr(geometry, 'fieldtypes') or\
           fldtype not in geometry.fieldtypes:
            raise ValueError(f"Can not add field of type '{fldtype}' "
                             f"to a {geometry.__class__.__name__}")

        if fldtype == 'node':
            datashape = (geometry.nnodes(), -1)
        elif fldtype == 'elemc':
            datashape = (geometry.nelems(), -1)
        elif fldtype == 'elemn':
            datashape = (geometry.nelems(), geometry.nplex(), -1)
        elif fldtype == 'elemg':
            datashape = (geometry.nelems(), -1, -1)

        scalar = len(data.shape) < len(datashape)
        if scalar:
            datashape = datashape[:-1]
        data = at.checkArray(data, shape=datashape)

        if fldname is None:
            fldname = next(Field._autoname)

        # All data seem OK, store them
        self.geometry = geometry
        self.fldname = fldname
        self.fldtype = fldtype
        self.data = data
        self.scalar = scalar


    def comp(self, i):
        """Return the data component i of a vectorial Field.

        Parameters
        ----------
        i: int:
            Component index of a vectorial Field. If the Field is a
            scalar one, any value will return the full scalar data.

        Returns
        -------
        array
            An array with scalar data over the Geometry.
        """
        if self.scalar:
            return self.data
        else:
            return self.data[:, i]


    def convert(self, totype, toname=None):
        """Convert a Field to another type.

        Parameters
        ----------
        totype: str
            The target field type. Can be any of the available
            field types. See :class:`Field` class. If the target type is equal
            to the source type, a copy of the original Field will result.
            This may or may not be a shallow copy.

        toname: str
            The name of the target field. If not specified,
            a autoname is generated.

        Returns
        -------
        Field
            A Field of type `totype` with data converted from the input Field.

        """
        data = None
        if totype == self.fldtype:
            data = self.data
        elif totype in self.geometry.fieldtypes:
            if self.fldtype == 'node':
                if totype == 'elemn':
                    data = self.data[self.geometry.elems]
                elif totype == 'elemc':
                    return self.convert('elemn').convert('elemc', toname)
            elif self.fldtype == 'elemn':
                if totype == 'elemc':
                    data = self.data.mean(axis=1)
                elif totype == 'node':
                    data = at.nodalAvg(
                        self.data, self.geometry.elems, self.geometry.nnodes()
                    )
            elif self.fldtype == 'elemc':
                if totype == 'elemn':
                    data = at.multiplex(
                        self.data, self.geometry.nplex(), axis=1
                    )
                elif totype == 'node':
                    return self.convert('elemn').convert('node', toname)

        if data is None:
            raise ValueError(
                f"Can not convert {self.geometry.__class__.__name__} "
                f"field data from '{self.fldtype}' to '{totype}'")

        return Field(self.geometry, totype, data, toname)

    def __str__(self):
        s = ", ".join([
            f"Field '{self.fldname}'",
            f"type '{self.fldtype}'",
            f"shape {self.data.shape}",
            f"nnodes={self.geometry.nnodes()}",
            f"nelems={self.geometry.nelems()}",
            f"nplex={self.geometry.nplex()}\n"])
        return s + str(self.data)


# End
