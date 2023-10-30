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
"""opengl/matrix.py

Python OpenGL framework for pyFormex
"""

import numpy as np
import pyformex.arraytools as at


DTYPE = at.Float

class Matrix4(np.ndarray):
    """A 4x4 transformation matrix for homogeneous coordinates.

    The matrix is to be used with post-multiplication on
    row vectors (i.e. OpenGL convention).

    Parameters
    ----------
    data: array_like (4,4), optional
        If specified, should be a (4,4) float array or compatible. Else
        a 4x4 identity matrix is created.

    Examples
    --------
    >>> I = Matrix4()
    >>> print(I)
    [[1.  0.  0.  0.]
     [0.  1.  0.  0.]
     [0.  0.  1.  0.]
     [0.  0.  0.  1.]]

    We can first scale and then rotate, or first rotate and then scale:

    >>> a = Matrix4().scale([4.,4.,4.]).rotate(45.,[0.,0.,1.])
    >>> a
    Matrix4([[ 2.8284,  2.8284,  0.    ,  0.    ],
             [-2.8284,  2.8284,  0.    ,  0.    ],
             [ 0.    ,  0.    ,  4.    ,  0.    ],
             [ 0.    ,  0.    ,  0.    ,  1.    ]])
    >>> b = Matrix4().rotate(45.,[0.,0.,1.]).scale([4.,4.,4.])
    >>> np.allclose(a,b)
    True
    """

    def __new__(clas, data=None):
        """Create a new Matrix instance"""
        if data is None:
            data = np.eye(4, 4, dtype=DTYPE)
        else:
            data = at.checkArray(data, (4, 4), 'f').astype(DTYPE)
        ar = data.view(clas)
        ar._gl = None
        return ar


    def __array_finalize__(self, obj):
        """Finalize the new Matrix object.

        When a class is derived from numpy.ndarray and the constructor (the
        :meth:`__new__` method) defines new attributes, these atttributes
        need to be reset in this method.
        """
        if obj is None:
            return
        self._gl = getattr(obj, '_gl', None)


    def __array_wrap__(self, out_arr, context=None):
        res = super().__array_wrap__(out_arr, context)
        if type(res) == Matrix4 and (
                res.dtype != DTYPE or res.shape != (4,4) ):
            res = res.view(np.ndarray)
        return res


    def gl(self):
        """Get the transformation matrix as a 'ready-to-use'-gl version.

        Returns the (4,4) Matrix as a rowwise flattened array of type float32.

        Example:

        >>> Matrix4().gl()
        Matrix4([1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0.,
            0., 0., 1.], dtype=float32)
        """
        if self._gl is None:
            self._gl = self.flatten().astype(np.float32)
        return self._gl


    @property
    def rot(self):
        """Return the (3,3) rotation matrix"""
        return self[:3, :3]


    @rot.setter
    def rot(self, value):
        """Set the rotation matrix to (3,3) value"""
        self[:3, :3] = value
        self._gl = None


    @property
    def trl(self):
        """Return the (3,) translation vector"""
        return self[3, :3]


    @trl.setter
    def trl(self, value):
        """Set the translation vector to (3,) value"""
        self[3, :3] = value
        self._gl = None


    def identity(self):
        """Reset the matrix to a 4x4 identity matrix."""
        self = np.eye(4, 4)
        self._gl = None


    def translate(self, vector):
        """Translate a 4x4 matrix by a (3,) vector.

        - `vector`: (3,) float array: the translation vector

        Changes the Matrix in place and also returns the result

        Example:

        >>> Matrix4().translate([1.,2.,3.])
        Matrix4([[1., 0., 0., 0.],
                 [0., 1., 0., 0.],
                 [0., 0., 1., 0.],
                 [1., 2., 3., 1.]])
        """
        vector = at.checkArray(vector, (3,), 'f')
        self.trl += np.dot(vector, self.rot)
        return self


    def rotate(self, angle, axis=None):
        """Rotate a Matrix4.

        The rotation can be specified by

        - an angle and axis,
        - a 3x3 rotation matrix,
        - a 4x4 trtransformation matrix (Matrix4).

        Parameters:

        - `angle`: float: the rotation angle. A 3x3 or 4x4 matrix may be
           give instead, to directly specify the roation matrix.
        - `axis`: int or (3,) float: the axis to rotate around

        Changes the Matrix in place and also returns the result.

        Example:

        >>> Matrix4().rotate(90.,[0.,1.,0.])
        Matrix4([[ 0., 0., -1., 0.],
                 [ 0., 1.,  0., 0.],
                 [ 1., 0.,  0., 0.],
                 [ 0., 0.,  0., 1.]])

        """
        ## !! TRANSPOSE!!
        ## x^2(1-c)+c     xy(1-c)-zs     xz(1-c)+ys     0
        ##  yx(1-c)+zs     y^2(1-c)+c     yz(1-c)-xs     0
        ##  xz(1-c)-ys     yz(1-c)+xs     z^2(1-c)+c     0
        ##       0              0               0        1

        try:
            rot = at.checkArray(angle, (4, 4), 'f')[:3, :3]
        except Exception:
            try:
                rot = at.checkArray(angle, (3, 3), 'f')
            except Exception:
                angle = at.checkFloat(angle)
                rot = at.rotationMatrix(angle, axis)
        self.rot = rot @ self.rot
        return self


    def scale(self, vector):
        """Scale a 4x4 matrix by a (3,) vector.

        - `vector`: (3,) float array: the scaling vector

        Changes the Matrix in place and also returns the result

        Example:

        >>> Matrix4().scale([1.,2.,3.])
        Matrix4([[1., 0., 0., 0.],
                 [0., 2., 0., 0.],
                 [0., 0., 3., 0.],
                 [0., 0., 0., 1.]])
        """
        vector = at.checkArray(vector, (3,), 'f')
        scale3 = np.diagflat(vector)
        self[:3, :3] = self[:3, :3] @ scale3
        self._gl = None
        return self


    # Do we need these?
    def swapRows(self, row1, row2):
        """Swap two rows.

        - `row1`, `row2`: index of the rows to swap
        """
        temp = np.copy(self[row1])
        self[row1] = self[row2]
        self[row2] = temp
        self._gl = None


    def swapCols(self, col1, col2):
        """Swap two columns.

        - `col1`, `col2`: index of the columns to swap
        """
        temp = np.copy(self[:, col1])
        self[:, col1] = self[:, col2]
        self[:, col2] = temp
        self._gl = None


    def inverse(self):
        """Return the inverse matrix"""
        return np.linalg.inv(self)


    def transform(self, x):
        """Transform a vertex using this matrix.

        - `x`: a (3,) or (4,) vector.

        If the vector has length 4, it holds homogeneous coordinates, and
        the result is the dot product of the vector with the Matrix:  x * M.
        If the vector has length 3, the 4th homogeneous coordinate is
        assumed to be 1, and the product is computed in an optimized way.
        """
        try:
            x = at.checkArray(x, (3,), 'f')
            return np.dot(x, self[:3, :3]) + self[3, :3]
        except Exception:
            x = at.checkArray(x, (4,), 'f')
            return np.dot(x, self)


    def invtransform(self, x):
        """Transform a vertex with the inverse of this matrix.

        - `x`: a (3,) or (4,) vector.

        """
        return np.dot(Vector4(x), self.inverse())


    def transinv(self):
        """Return the transpose of the inverse."""
        return self.inverse().transpose()


# End
