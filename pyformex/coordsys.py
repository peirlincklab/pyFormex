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
"""Coordinate Systems.

"""

import numpy as np

from pyformex import arraytools as at
from pyformex import utils
from pyformex.coords import Coords

__all__ = ['CoordSys']

###########################################################################
##
##   class CoordSys
##
#########################
#

#
# TODO: This could be improved:
#   - generalized: cartesian, cylindrical, spherical
#

@utils.pzf_register
class CoordSys():
    """A Cartesian coordinate system in 3D space.

    The coordinate system is stored as a rotation matrix and a translation
    vector, which transform the global coordinate axes into the axes of the
    CoordSys.
    Clearly, the translation vector is the origin of the CoordSys, and the
    rows of the rotation matrix are the unit vectors along the three axes.

    The CoordSys can be initialized in different ways and has only optional
    parameters to achieve this. If none are specified at all, the global
    coordinate axis results.

    Parameters
    ----------
    oab: float :term:`array_like` (3,3), optional
        Three non-collinear points O, A and B, that define the CoordSys
        in the following way: O is the origin of the coordinate system,
        A is a point along the positive first axis and B is a point B in
        the plane of the first two axes.
    points: float :term:`array_like` (4,3), optional
        The CoordSys is specified by four points: the first three are
        points on the three coordinate axes, at distance +1 from the
        origin; the fourth point is the origin. The use of this parameter
        is deprecated. It can be replaced with `oab=points[3,0,1]`.
    rot: float :term:`array_like` (3,3), optional
        Rotation matrix that transforms the global global axes to be
        parallel to the constructed CoordSys. The user is responsible to
        make sure that `rot` is a proper orthonormal rotation matrix.
    trl: float :term:`array_like` (3,)
        Translation vector that moves the global origin to the origin of the
        CoordSys, in other words, this is the origin of the new CoordSys
        in global coordinates.

    Notes
    -----
    If `oab` is provided, it takes precedence and the other parameters
    are ignored. If not, and `points` is provided, this takes precedence
    and the remaining are ignored. If neither `oab` nor `points` are
    provided, `rot` and `trl` are used and have default values equal
    to the rotation matrix and translation vector of the global coordinatee
    axes.


    A Coords object has a number of attributes that provide quick acces
    to its internal data. Of these, `trl` and `rot` can be used to set
    the data of the CoordSys and thus change the CoordSys in-place.

    Examples
    --------
    Three points O,A,B in the xy-plane, first two parallel to x-axis,
    third at higher y-value. The resulting CoordSys is global axes
    translated to point O.

    >>> OAB = Coords([[2.,1.,0.],[5.,1.,0.],[0.,3.,0.]])
    >>> print(CoordSys(oab=OAB))
    CoordSys: trl=[2. 1. 0.]; rot=[[1. 0. 0.]
                                    [0. 1. 0.]
                                    [0. 0. 1.]]

    Now translate the points so that O is on the z-axis, and rotate the
    points 30 degrees around z-axis.

    >>> OAB = OAB.trl([-2.,-1.,5.]).rot(30)
    >>> print(OAB)
    [[ 0.      0.      5.    ]
     [ 2.5981  1.5     5.    ]
     [-2.7321  0.7321  5.    ]]
    >>> C = CoordSys(oab=OAB)
    >>> print(C)
    CoordSys: trl=[0. 0. 5.]; rot=[[ 0.866  0.5    0.   ]
                                   [-0.5    0.866  0.   ]
                                   [ 0.    -0.     1.   ]]

    Reverse axes x and y. The resulting CoordSys is still righthanded. This is
    equivalent to a rotation over 180 degrees around z-axis.

    >>> print(C.reverse(0,1))
    CoordSys: trl=[0. 0. 5.]; rot=[[-0.866 -0.5   -0.   ]
                                   [ 0.5   -0.866 -0.   ]
                                   [ 0.    -0.     1.   ]]

    Now rotate C over 150 degrees around z-axis to become parallel with
    the global axes.

    >>> print(C.rotate(150,2))
    CoordSys: trl=[0.  0.  5.]; rot=[[ 1.  0.  0.]
                                     [-0.  1.  0.]
                                     [ 0.  0.  1.]]

    >>> C = CoordSys(trl=[0., 0., 5.],
    ...     rot=[[-0.87,-0.5,-0.], [0.5,-0.87,-0.], [0., -0., 1.]])
    >>> print(C)
    CoordSys: trl=[0.  0.  5.]; rot=[[-0.87 -0.5  -0.  ]
                                     [ 0.5  -0.87 -0.  ]
                                     [ 0.   -0.    1.  ]]

    """
    # REMOVED from docstring

    # Attributes
    # ----------
    # trl: float array (3,)
    #     The origin of the CoordSys
    # rot: float array (3,3)
    #     The rotation matrix of the CoordSys
    # u: float array (3,)
    #     The unit vector along the first axis (0).
    # v: float array (3,)
    #     The unit vector along the second axis (1).
    # w: float array (3,)
    #     The unit vector along the third axis (2).
    # o: float array (3,)
    #     The origin of the CoordSys.


    def __init__(self, oab=None, points=None, rot=None, trl=None):
        """Initialize the CoordSys"""
        if oab is not None:
            oab = at.checkArray(oab, (3, 3), 'f')
            rot = at.rotmat(oab)
            trl = oab[0]
        elif points is not None:
            points = at.checkArray(points, (4, 3), 'f')
            rot = at.normalize(points[:3] - points[3])
            trl = points[3]
        else:
            if rot is None:
                rot = np.eye(3, 3)
            else:
                rot = at.checkArray(rot, (3, 3), 'f')
                # perform a check
                # I = np.dot(rot, rot.T)
                # print(I)
                # print(at.length(rot))
            if trl is None:
                trl = np.zeros((3,))
            else:
                trl = at.checkArray(trl, (3,), 'f')

        self.rot = rot
        self.trl = trl


    @property
    def trl(self):
        """Return the origin as a (3,) vector"""
        return self._trl

    @trl.setter
    def trl(self, value):
        """Set the origin to (3,) value"""
        self._trl = at.checkArray(value, shape=(3,), kind='f')

    @property
    def rot(self):
        """Return the (3,3) rotation matrix"""
        return self._rot

    @rot.setter
    def rot(self, value):
        """Set the rotation matrix to (3,3) value"""
        self._rot = at.checkArray(value, shape=(3, 3), kind='f')

    @property
    def u(self):
        """Return unit vector along axis 0 (x)"""
        return self.axis(0)

    @property
    def v(self):
        """Return unit vector along axis 1 (y)"""
        return self.axis(1)

    @property
    def w(self):
        """Return unit vector along axis 2 (z)"""
        return self.axis(2)

    @property
    def o(self):
        """Return the origin"""
        return Coords(self.trl)

    # Some aliases
    origin = o
    axes = rot


    def axis(self, i):
        """Return the unit vector along an axis.

        Parameters
        ----------
        i: int (0,1,2)
            The axis number.

        Returns
        -------
        float array (3,)
            A unit vector along axis `i`.

        Notes
        -----
        If the axis is known in advance, it is more appropriate
        to use one of the u, v or w attributes

        Examples
        --------
        >>> CoordSys().rotate(30).axis(1)
        array([-0.5  ,  0.866,  0.   ])
        """
        return self.rot[i]


    def points(self):
        """Return origin and endpoints of unit vectors along axes.

        Returns
        -------
        Coords (4,3)
            A Coords object with four points: the endpoints of the
            unit vectors along the three axes of the CoordSys, and
            the origin of the CoordSys.

        Examples
        --------
        >>> CoordSys().rotate(30).points()
        Coords([[ 0.866,  0.5  ,  0.   ],
                [-0.5  ,  0.866,  0.   ],
                [ 0.   ,  0.   ,  1.   ],
                [ 0.   ,  0.   ,  0.   ]])

        """
        return Coords.concatenate([self.axes+self.trl, self.trl])

    # Simple transformation methods
    # These methods modify the object inplace
    # They still return self, so that they can be concatenated

    def _translate(self, trl):
        """Translate the CoordSys.

        Note
        ----
        This changes the CoordSys in place!

        Parameters
        ----------
        trl: term:`array_like` (3,)
            A translation vector to transform the current CoordSys.

        Returns
        -------
            The rotated CoordSys.
        """
        trl = at.checkArray(trl, shape=(3,), kind='f', allow='i')
        self.trl += trl
        return self


    def _rotate(self, rot):
        """Rotate the CoordSys.

        Rotates the CoordSys axes, keeping its origin.

        Note
        ----
        This changes the CoordSys in place!

        Parameters
        ----------
        rot: :term:`array_like` (3,3)
            A rotation matrix to transform the current CoordSys.

        Returns
        -------
            The rotated CoordSys.
        """
        rot = at.checkArray(rot, shape=(3, 3), kind='f', allow='i')
        self.rot = np.dot(self.rot, rot)
        return self


    def translate(self, *args, **kargs):
        """Translate the CoordSys like a Coords object.

        Parameters are like :meth:`Coords.translate`.

        Returns
        -------
            A new CoordSys obtained by giving `self` a translation.

        Examples
        --------
        >>> print(CoordSys().translate([-2.,-1.,5.]))
        CoordSys: trl=[-2. -1.  5.]; rot=[[1.  0.  0.]
                                          [0.  1.  0.]
                                          [0.  0.  1.]]

        """
        return CoordSys(points=self.points().translate(*args, **kargs))


    def rotate(self, *args, **kargs):
        """Rotate the CoordSys like a Coords object.

        Parameters are like :meth:`Coords.rotate`.

        Returns
        -------
            A new CoordSys obtained by giving `self` a rotation.

        Examples
        --------
        >>> print(CoordSys().rotate(30))
        CoordSys: trl=[0. 0. 0.]; rot=[[ 0.866  0.5    0.   ]
                                       [-0.5    0.866  0.   ]
                                       [ 0.     0.     1.   ]]
        """
        return CoordSys(points=self.points().rotate(*args, **kargs))


    def reverse(self, *axes):
        """Reverse some axes of the CoordSys.

        Parameters
        ----------
        axes: int (0,1,2) or tuple of ints
            The axes to be reversed.

        Note
        ----
        The reversing a single axis (or all three axes) will change a
        right-hand-sided CoordSys into a left-hand-sided one. Therefore,
        this method is normally used only with two axes.

        Examples
        --------
        >>> print(CoordSys().reverse(0,1))
        CoordSys: trl=[0.  0.  0.]; rot=[[-1. -0. -0.]
                                         [-0. -1. -0.]
                                         [ 0.  0.  1.]]

        """
        for axis in axes:
            self.rot[axis] *= -1.0
        return self


    def __str__(self):
        """User friendly string representation"""
        return at.stringar(f"CoordSys: trl={self.trl}; rot=", self.rot)


    def pzf_dict(self):
        return {
            'rot': self.rot,
            'trl': self.trl
        }


### End
