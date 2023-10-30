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

"""A collection of numerical utilities.

This module contains a large collection of numerical utilities.
Many of them are related to processing arrays. Some are similar
to existing NumPy functions but offer some extended functionality.

Note
----
    While these functions were historically developed for pyFormex,
    this module only depends on numpy and can be used outside
    of pyFormex without changes.

"""
import numpy as np

# NOTE: this overrides the Python builtin function abs. This is no
# problem because np.abs works just like abs on a simple values and arrays.
# But do not be tempted to override Python's sum with np.sum, because
# these work very differently on multidimensional arrays and have other
# optional arguments.
from numpy import (pi, sin, cos, tan, arcsin, arccos, arctan,  # noqa: F401
                   arctan2, sqrt, abs, inf, nan)

def numpy_version():
    """Return the numpy version as a tuple of ints.

    This allow easy comparison with some required version.

    Returns
    -------
    tuple
        A tuple of three ints with the version of the loaded numpy module.

    Examples
    --------
    >>> numpy_version() > (1, 16, 0)
    True
    """
    return tuple(map(int, np.__version__.split('.')))


_attributes_ = ['Float', 'Int', 'DEG', 'RAD', 'golden_ratio']

# default float and int types
Float = np.float32
Int = np.int32

# Some constants
DEG = np.pi/180.
"""float: multiplier to transform degrees to radians = pi/180."""
RAD = 1.
"""float: multiplier to transform radians to radians"""

golden_ratio = 0.5 * (1.0 + sqrt(5.))
"""golden ratio is defined as  0.5 * (1.0 + sqrt(5.))"""

#
#  Exceptions
#
class InvalidShape(ValueError):
    pass
class InvalidKind(ValueError):
    pass

#
# Functions for checking types, values and array dimensions
###########################################################


where_1d = np.flatnonzero
where_nd = np.nonzero


def isInt(obj):
    """Test if an object is an integer number.

    Returns
    -------
    bool
        True if the object is a single integer number (a Python ``int``
        or a ``numpy.integer`` type), else False.

    Examples
    --------
    >>> isInt(1)
    True
    >>> isInt(np.arange(3)[1])
    True
    """
    return isinstance(obj, (int, np.integer))


def isFloat(obj):
    """Test if an object is a floating point number.

    Returns
    -------
    bool
        True if the object is a single floating point number (a Python
        ``float`` or a ``numpy.floating`` type), else False.

    Examples
    --------
    >>> isFloat(1.)
    True
    >>> isFloat(np.array([1,2],dtype=np.float32)[1])
    True
    """
    return isinstance(obj, (float, np.floating))


def isNum(obj):
    """Test if an object is an integer or a floating point number.

    Returns
    -------
    bool
        True if the object is a single integer or floating point
        number, else False. The type of the object can be either
        a Python ``int`` or ``float`` or a numpy ``integer`` or ``floating``.

    Examples
    --------
    >>> isNum(1)
    True
    >>> isNum(1.0)
    True
    >>> isNum(np.array([1,2],dtype=np.int32)[1])
    True
    >>> isNum(np.array([1,2],dtype=np.float32)[1])
    True
    """
    return isInt(obj) or isFloat(obj)


def checkInt(value, min=None, max=None):
    """Check that a value is an int in the range min..max.

    Parameters
    ----------
    value: int-like
        The value to check.
    min: int, optional
        If provided, minimal value to be accepted.
    max: int, optional
        If provided, maximal value to be accepted.

    Returns
    -------
    checked_int: int
        An integer not exceeding the provided boundaries.

    Raises
    ------
    ValueError:
        If the value is not convertible to an integer type or exceeds one
        of the specified boundaries.

    Examples
    --------
    >>> checkInt(1)
    1
    >>> checkInt(1,min=0,max=1)
    1
    >>> checkInt('2',min=0)
    2
    """
    try:
        a = int(value)
        if min is not None and a < min:
            raise ValueError
        if max is not None and a > max:
            raise ValueError
        return a
    except ValueError:
        raise ValueError(
            f"Expected an int in the range({min}, {max}), got: {value}")


def checkFloat(value, min=None, max=None):
    """Check that a value is a float in the range min..max.

    Parameters
    ----------
    value: float-like
        The value to check
    min: float-like, optional
        If provided, minimal value to be accepted.
    max: float-like, optional
        If provided, maximal value to be accepted.

    Returns
    -------
    checked_float: float
        A float not exceeding the provided boundaries.

    Raises
    ------
    ValueError:
        If the value is not convertible to a float type or exceeds one of the
        specified boundaries.

    Examples
    --------
    >>> checkFloat(1)
    1.0
    >>> checkFloat(1,min=0,max=1)
    1.0
    >>> checkFloat('2',min=0)
    2.0
    """
    try:
        a = float(value)
        if min is not None and a < min:
            raise ValueError
        if max is not None and a > max:
            raise ValueError
        return a
    except Exception:
        raise ValueError(
            f"Expected a float in the range({min}, {max}), got: {value}")


def checkBroadcast(shape1, shape2):
    """Check that two array shapes are broadcast compatible.

    In many numerical operations, NumPy will automatically broadcast
    arrays of different shapes to a single shape, if they have broadcast
    compatible shapes. Two array shapes are broadcast compatible if, in
    all the last dimensions that exist in both arrays, either the shape
    of both arrays has the same length, or one of the shapes has a length
    1.

    Parameters
    ----------
    shape1: tuple of ints
        Shape of first array
    shape2: tuple of ints
        Shape of second array

    Returns
    -------
    tuple of ints
        The broadcasted shape of the arrays.

    Raises
    ------
    ValueError: Shapes are not broadcast compatible
        If the two shapes can not be broadcast to a single one.

    Examples
    --------
    >>> checkBroadcast((8,1,6,1),(7,1,5))
    (8, 7, 6, 5)
    >>> checkBroadcast((5,4),(1,))
    (5, 4)
    >>> checkBroadcast((5,4),(4,))
    (5, 4)
    >>> checkBroadcast((15,3,5),(15,1,5))
    (15, 3, 5)
    >>> checkBroadcast((15,3,5),(3,5))
    (15, 3, 5)
    >>> checkBroadcast((15,3,5),(3,1))
    (15, 3, 5)
    >>> checkBroadcast((7,1,5),(8,1,6,1))
    (8, 7, 6, 5)

    """
    len1, len2 = len(shape1), len(shape2)
    if len1 < len2:
        shape1, shape2 = shape2, shape1
        len1, len2 = len2, len1
    shape = list(shape1[:len1-len2])
    for n1, n2 in zip(shape1[len1-len2:], shape2):
        if n1 == 1 or n2 == 1 or n1==n2:
            shape.append(max(n1, n2))
        else:
            raise ValueError("Shapes are not broadcast compatible")
    return tuple(shape)


def checkArray(a, shape=None, kind=None, allow=None, size=None, ndim=None,
               bcast=None, subok=False, addaxis=False):
    """Check that an array a has the correct shape, type and/or size.

    Parameters
    ----------
    a: :term:`array_like`
        An instance of a numpy.ndarray or a subclass thereof, or anything
        that can be converted into a numpy array.
    shape: tuple of ints, optional
        If provided, the shape of the array should match this value
        along each axis for which a nonzero value is specified. The
        length of the shape tuple should also match (unless addaxis=True
        is provided, see below).
    kind: dtype.kind character code, optional
        If provided, the array's dtype.kind should match this value,
        or one of the values in ``allow``, if provided.
    allow: string of dtype.kind character codes, optional
        If provided, and ``kind`` is also specified, any of the specified
        array types will also be accepted if it is convertible to the
        specified ``kind``. See also Notes below.
    size: int, optional
        If provided, the total array size should match this value.
    ndim: int, optional
        If provided the input array should have exactly ``ndim`` dimensions
        (unless addaxis=True is provided, see below).
    bcast: tuple of ints, optional
        If provided, the array's shape should be broadcast comaptible with
        the specified shape.
    subok: bool, optional
        If True, the returned array is of the same class as the input array
        ``a``, if possible. If False (default), the returned array is always
        of the base type numpy.ndarray.
    addaxis: bool, optional
        If False (default), and either ndim or shape are specified,
        the input array should have precisely the number of dimensions
        specified by ndim or the length of shape.
        If True, an input array with less dimensions will automatically
        be transformed by adding length 1 axes at the start of the shape
        tuple until the correct dimension is reached.

    Returns
    -------
    array
        The checked_array is equivalent to the input data. It has the same
        contents and shape. It also has the same type, unless ``kind`` is
        is provided, in which case the result is converted to this type.
        If ``subok=True`` was provided, the returned array will be of the
        same array subclass as the input ``a``, if possible.

    Raises
    ------
    InvalidShape:
        The shape of the input data is invalid.
    InvalidKind:
        The kind of the input data is invalid.
    ValueError:
        The input data are invalid for some other reason.

    Notes
    -----
    Currently, the only allowed conversion from an ``allow`` type to ``kind``
    type, is to 'f'. Thus specifiying ``kind='f', allow='i'`` will accept
    integer input but return float32 output.

    See Also
    --------
    :func:`checkArray1D`

    Examples
    --------
    >>> checkArray([1,2])
    array([1, 2])
    >>> checkArray([1,2],shape=(2,))
    array([1, 2])
    >>> checkArray([[1,2],[3,4]],shape=(2,-1))
    array([[1, 2], [3, 4]])
    >>> checkArray([1,2],kind='i')
    array([1, 2])
    >>> checkArray([1,2],kind='f',allow='i')
    array([1., 2.])
    >>> checkArray([1,2],size=2)
    array([1, 2])
    >>> checkArray([1,2],ndim=1)
    array([1, 2])
    >>> checkArray([[1,2],[3,4]],bcast=(3,1,2))
    array([[1, 2], [3, 4]])
    >>> checkArray([[1,2],[3,4]],ndim=3,addaxis=True)
    array([[[1, 2],
            [3, 4]]])
    >>> checkArray([[1,2],[3,4]],shape=(-1,-1,2),addaxis=True)
    array([[[1, 2],
            [3, 4]]])

    """
    a = np.asanyarray(a) if subok else np.asarray(a)
    if ndim is None and shape is not None:
        ndim = len(shape)
    if ndim is not None:
        if a.ndim != ndim:
            if addaxis and a.ndim < ndim:
                while a.ndim < ndim:
                    a = np.expand_dims(a, axis=0)
            else:
                raise InvalidShape(
                    f"Nonmatching ndim: expected {ndim}, got {a.ndim}")
    if size is not None:
        if a.size != size:
            raise InvalidShape(
                f"Nonmatching size: expected {size}, got {a.size}")
    if shape is not None:
        shape = np.asarray(shape)
        w = where_1d(shape >= 0)
        if (np.asarray(a.shape)[w] != shape[w]).any():
            raise InvalidShape(
                f"Nonmatching shape: expected {shape}, got {a.shape}")
    if kind is not None:
        if a.dtype.kind != kind:
            if allow is not None and a.dtype.kind in allow:
                if kind == 'f':
                    a = a.astype(Float)
                elif kind == 'i':
                    a = a.astype(Int)
            else:
                raise InvalidKind(
                    f"Nonmatching kind: expected {kind}, got {a.dtype.kind}")
        if kind == 'f':
            # FORCE TO float32, otherwise we break some opengl function
            # e.g. setTriade
            # Leave this until we have a proper dtype==Float checking
            # everywhere
            a = a.astype(Float)
    if bcast is not None:
        checkBroadcast(a.shape, bcast)
    return a


def checkArray1D(a, kind=None, allow=None, size=None):
    """Check and force an array to be 1D.

    This is equivalent to calling :func:`checkArray` without the ``shape`` and
    ``ndim`` parameters, and then turning the result into a 1D array.

    Parameters
    ----------
    See :func:`checkArray`.

    Returns
    -------
    1D array
        The checked_array holds the same data as the input, but the shape
        is rveled to 1D. It also has the same type, unless ``kind`` is
        is provided, in which case the result is converted to this type.

    Examples
    --------
    >>> checkArray1D([[1,2],[3,4]],size=4)
    array([1, 2, 3, 4])

    """
    return checkArray(a, kind=kind, allow=allow, size=size).ravel()


def checkUniqueNumbers(nrs, nmin=0, nmax=None):
    """Check that an array contains a set of unique integers in a given range.

    This functions tests that all integer numbers in the array are within the
    range math:`nmin <= i < nmax`. Default range is [0,unlimited].

    Parameters
    ----------
    nrs: :term:`array_like`, int
        Input array with integers to check against provided limits.
    nmin: int or None, optional
        If not None, no value in ``a`` should be lower than this.
    nmax: int, optionallMinimum allowed value.
    - `nmax`: maximum allowed value + 1! If set to None, the test is skipped.
        If provided, no value in ``a`` should be higher than this.

    Returns
    -------
    1D int array
        Containing the sorted unique numbers from the input.

    Raises
    ------
    ValueError
        If the numbers are not unique or some input value surpasses one of
        the specified limits.

    Examples
    --------
    >>> checkUniqueNumbers([0,5,1,7,2])
    array([0, 1, 2, 5, 7])
    >>> checkUniqueNumbers([0,5,1,7,-2],nmin=None)
    array([-2, 0, 1, 5, 7])
    """
    nrs = np.asarray(nrs)
    uniq = np.unique(nrs)
    if (uniq.size != nrs.size
            or (nmin is not None and uniq.min() < nmin)
            or (nmax is not None and uniq.max() > nmax)):
        raise ValueError("Values not unique or not in range")
    return uniq

###########################################################################
##
##   Some generic array functions
##
#########################


def mapArray(f, a):
    """Map a function f over an array a.

    Examples
    --------
    >>> mapArray(lambda x:x*x, [1,2,3])
    array([1, 4, 9])
    >>> mapArray(lambda x:x*x, [[1,2],[3,4]])
    array([[ 1,  4],
           [ 9, 16]])
    >>> mapArray(lambda x: (x, 2*x, x*x), [1,2,3])
    array([[1, 2, 1],
           [2, 4, 4],
           [3, 6, 9]])
    """
    a = np.asarray(a)
    data = np.stack([f(ai) for ai in a.flat])
    shape = a.shape
    if data.size > a.size:
        shape += (-1,)
    return data.reshape(shape)


def addAxis(a, axis):
    """Add a new axis with length 1 to an array.

    Parameters
    ----------
    a: :term:`array_like`
        The array to which to add an axis.
    axi: int
        The position of the new axis.

    Returns
    -------
    array
        Same type and data as a, but with an added axis of length 1.

    Notes
    -----
    This is equivalent to ``np.expand_dims(a, axis)``, but easier to remember.
    """
    return np.expand_dims(a, axis)


def growAxis(a, add, axis=-1, fill=0):
    """Increase the length of an array axis.

    Parameters
    ----------
    a: :term:`array_like`
        The array in which to extend an axis.
    add: int
        The length over which the specified axis should grow.
        If add<=0, the array is returned unchanged.
    axis: int
        Position of the target axis in the array. Default is last (-1).
    fill: int | float | None
        Value to set the new elements along the grown axis to.
        If None, the value is undefined.

    Returns
    -------
    array
        Same type and data as `a`, but length of specified axis has been
        increased with a value `add` and the new elements are filled with
        the value `fill`.

    Raises
    ------
    ValueError:
        If the specified axis exceeds the array dimensions.

    See Also
    --------
    resizeAxis: resize an axis by repeating elements along that axis.

    Examples
    --------
    >>> growAxis([[1,2,3],[4,5,6]],2)
    array([[1, 2, 3, 0, 0],
           [4, 5, 6, 0, 0]])
    >>> growAxis([[1,2,3],[4,5,6]],1,axis=0,fill=-3)
    array([[ 1, 2, 3],
           [ 4, 5, 6],
           [-3, -3, -3]])
    >>> growAxis([[1,2,3],[4,5,6]],-1)
    array([[1, 2, 3],
           [4, 5, 6]])
    """
    a = np.asarray(a)
    if axis >= a.ndim or axis < -a.ndim:
        raise ValueError(f"Array with ndim {a.ndim} has no axis {axis}")
    if add <= 0:
        return a
    else:
        pad_width = [(0, 0)] * a.ndim
        pad_width[axis] = (0, add)
        if fill is None:
            res = np.pad(a, pad_width, method='empty')
        else:
            res = np.pad(a, pad_width, constant_values=fill)
        return res


def resizeAxis(a, length, axis=-1):
    """Change the length of an array axis by cutting or repeating elements.

    Parameters
    ----------
    a: :term:`array_like`
        The array in which to extend n axis.
    length: int
        The new length of the axis.
    axis: int
        Position of the target axis in the array. Default is last (-1).

    Returns
    -------
    array
        Same type and data as `a`, but with the spefied axis cut at the
        specified length or increased by repeating the elements along that
        axis.

    Raises
    ------
    ValueError:
        If the specified axis exceeds the array dimensions.

    See Also
    --------
    growAxis: increase an axis and fill with a constant value.
    resizeArray: resize multiple axes by repeating elements along axes

    Examples
    --------
    >>> resizeAxis([[1,2,3],[4,5,6]], 5)
    array([[1, 2, 3, 1, 2],
           [4, 5, 6, 4, 5]])
    >>> resizeAxis([[1,2,3],[4,5,6]], 3, axis=0)
    array([[1, 2, 3],
           [4, 5, 6],
           [1, 2, 3]])
    >>> resizeAxis([[1,2,3],[4,5,6]], 2)
    array([[1, 2],
           [4, 5]])
    """
    a = np.asarray(a)
    if axis >= a.ndim or axis < -a.ndim:
        raise ValueError(f"Array with ndim {a.ndim} has no axis {axis}")
    if a.shape[axis] != length:
        # always put the axis to change in front
        # np.resize only copies correctly along axis 0
        # and taking a slice is also easier
        if axis != 0:
            a = a.swapaxes(0, axis)
        if a.shape[0] < length:
            a = np.resize(a, (length,) + a.shape[1:])
        else:
            a = a[:length]
        if axis != 0:
            a = a.swapaxes(0, axis)
    return a


def resizeArray(a, shape):
    """Resize an array to the requested shape, repeating elements along axes.

    Repeatedly applies :func:`resizeAxis` to get the desired shape.

    Parameters
    ----------
    a: :term:`array_like`
        The array in which to extend n axis.
    shape: tuple
        The intended shape. The number of axes should be the same as that
        of the input array.

    Returns
    -------
    array
        Same type and data as `a`, but with the specified shape and with
        elements along the axes repeated where the length has increased.

    Raises
    ------
    ValueError:
        If the specified axis exceeds the array dimensions.

    Examples
    --------
    >>> resizeArray([[1,2,3],[4,5,6]], (3,5))
    array([[1, 2, 3, 1, 2],
           [4, 5, 6, 4, 5],
           [1, 2, 3, 1, 2]])
    >>> resizeArray([[1,2,3],[4,5,6]], (3,2))
    array([[1, 2],
           [4, 5],
           [1, 2]])
    >>> resizeArray([[1,2,3],[4,5,6]], (2,2))
    array([[1, 2],
           [4, 5]])
    """
    a = np.asarray(a)
    if len(shape) != len(a.shape):
        raise ValueError(f"shape {shape} should have same dimension as a {a.shape}")
    for i in range(a.ndim):
        if a.shape[i] != shape[i]:
            a = resizeAxis(a, shape[i], i)
    return a


def reorderAxis(a, order, axis=-1):
    """Reorder the planes of an array along the specified axis.

    Parameters
    ----------
    a: :term:`array_like`
        The array in which to reorder the elements.
    order: int :term:`array_like` | str
        Specifies how to reorder the elements. It can be an integer index
        which should be a permutation of `arange(a.shape[axis])`. Each value
        in the index specified the old index of the elements that should be
        placed at its position. This is equivalent to `a.take(order,axis)`.

        `order` can also be one of the following predefined sting values,
        resulting in the corresponding renumbering scheme being generated:

        - 'reverse': the elements along axis are placed in reverse order
        - 'random': the elements along axis are placed in random order

    axis: int
        The axis of the array along which the elements are to be reordered.
        Default is last (-1).

    Returns
    -------
    array
        Same type and data as `a`, but the element planes are along `axis`
        have been reordered.

    Examples
    --------
    >>> reorderAxis([[1,2,3],[4,5,6]], [2,0,1])
    array([[3, 1, 2],
           [6, 4, 5]])

    """
    a = np.asarray(a)
    n = a.shape[axis]
    if order == 'reverse':
        order = np.arange(n-1, -1, -1)
    elif order == 'random':
        order = np.random.permutation(n)
    else:
        order = np.asarray(order)
    return a.take(order, axis)


def reverseAxis(a, axis=-1):
    """Reverse the order of the elements along an axis.

    Parameters
    ----------
    a: :term:`array_like`
        The array in which to reorder the elements.
    axis: int
        The axis of the array along which the elements are to be reordered.
        Default is last (-1).

    Returns
    -------
    array
        Same type and data as `a`, but the elements along `axis` are now
        in reversed order.

    Note
    ----
    This function is especially useful if axis has a computed value.
    If the axis is known in advance, it is more efficient to use
    an indexing operation. Thus **reverseAxis(A,-1)** is equivalent to
    **A[...,::-1]**.

    Examples
    --------
    >>> A = np.array([[1,2,3],[4,5,6]])
    >>> reverseAxis(A)
    array([[3, 2, 1],
           [6, 5, 4]])
    >>> A[...,::-1]
    array([[3, 2, 1],
           [6, 5, 4]])

    """
    return reorderAxis(a, 'reverse', axis)


def interleave(*ars):
    """Interleave two or more arrays along their first axis.

    Parameters
    ----------
    ars: two or more :term:`array_like`
        The arrays to interleave. All arrays should have the same shape,
        except that the first array may have a first dimension that is
        one longer than the other arrays. The rows of the other arrays
        are interleaved between those of the first array.

    Returns
    -------
    array
        An array with interleaved rows from all arrays. The result has the
        datatype of the first array and its length along the first axis
        id the combined length of that of all arrays.

    Examples
    --------
    >>> interleave(np.arange(4), 10*np.arange(3))
    array([ 0, 0, 1, 10, 2, 20, 3])
    >>> a = np.arange(8).reshape(2,4)
    >>> print(interleave(a, 10+a, 20+a))
    [[ 0  1  2  3]
     [10 11 12 13]
     [20 21 22 23]
     [ 4  5  6  7]
     [14 15 16 17]
     [24 25 26 27]]

    """
    if len(ars) < 2:
        raise ValueError("Need at least 2 arrays to interleave")
    ars = [np.asarray(a) for a in ars]
    a = ars[0]
    for b in ars:
        if b.shape[0]-b.shape[0] not in (0, 1) or a.shape[1:] != b.shape[1:]:
            raise ValueError("Array sizes not compatible for interleave")
    ntot = sum([b.shape[0] for b in ars])
    n = len(ars)
    c = np.empty((ntot,) + a.shape[1:], dtype=a.dtype)
    c[0::n] = a
    for i in range(1, n):
        c[i::n] = ars[i]
    return c


def multiplex(a, n, axis, warn=True):
    """Multiplex an array over a length n in direction of a new axis.

    Inserts a new axis in the array at the specified position and repeats
    the data of the array `n` times in the direction of the new axis.

    Parameters
    ----------
    a: :term:`array_like`
        The input array.
    n: int
        Number of times to repeat the data in direction of `axis`.
    axis: int, optional
        Position of the new axis in the expanded array. Should be
        in the range -a.ndim..a.ndim.

    Returns
    -------
    array
        An array with n times the original data repeated in the direction
        of the specified axis.

    See Also
    --------
    repeatValues: Repeat values in a 1-dim array a number of times

    Examples
    --------
    >>> a = np.arange(6).reshape(2,3)
    >>> print(a)
    [[0 1 2]
     [3 4 5]]
    >>> print(multiplex(a,4,-1))
    [[[0 0 0 0]
      [1 1 1 1]
      [2 2 2 2]]
    <BLANKLINE>
     [[3 3 3 3]
      [4 4 4 4]
      [5 5 5 5]]]
    >>> print(multiplex(a,4,-2))
    [[[0 1 2]
      [0 1 2]
      [0 1 2]
      [0 1 2]]
    <BLANKLINE>
     [[3 4 5]
      [3 4 5]
      [3 4 5]
      [3 4 5]]]

    """
    return np.expand_dims(a, axis).repeat(n, axis=axis)


def repeatValues(a, n):
    """Repeat values in a 1-dim array a number of times.

    Parameters
    ----------
    a: :term:`array_like`, 1-dim
        The input array. Can be a list or a single element.
    n: int :term:`array_like`, 1-dim
        Number of times to repeat the corresponding value of ``a``.
        If ``n`` has less elements than ``a``, it is reused until
        the end of ``a`` is reached.

    Returns
    -------
    array
        An 1-dim array of the same dtype as ``a`` with the value ``a[i]``
        repeated ``n[i]`` times.

    See Also
    --------
    multiplex: Multiplex an array over a length n in direction of a new axis

    Examples
    --------
    >>> repeatValues(2,3)
    array([2, 2, 2])
    >>> repeatValues([2,3],2)
    array([2, 2, 3, 3])
    >>> repeatValues([2,3,4],[2,3])
    array([2, 2, 3, 3, 3, 4, 4])
    >>> repeatValues(1.6,[3,5])
    array([1.6, 1.6, 1.6])

    """
    a = checkArray1D(a)
    n = checkArray1D(n, kind='i')
    n = np.resize(n, a.shape)
    return np.concatenate([np.resize(ai, ni) for ai, ni in zip(a, n)])


def concat(al, axis=0):
    """Smart array concatenation ignoring empty arrays.

    Parameters
    ----------
    al: list of arrays
        All arrays should have same shape except for the length of
        the concatenation axis, or be empty arrays.
    axis: int
        The axis along which the arrays are concatenated.

    Returns
    -------
    :array
        The concatenation of all non-empty arrays in the list,
        or an empty array if all arrays in the list are empty.

    Note
    ----
    This is just like numpy.concatenate, but allows empty arrays
    in the list and silently ignores them.

    Examples
    --------
    >>> concat([np.array([0,1]),np.array([]),np.array([2,3])])
    array([0, 1, 2, 3])

    """
    al = [a for a in al if a.size > 0]
    if len(al) > 0:
        return np.concatenate(al, axis=axis)
    else:
        return np.array([])


def splitrange(n, nblk):
    """Split a range of integers 0..n in almost equal sized slices.

    Parameters
    ----------
    n: int
        Highest integer value in the range.
    nblk: int
        Number of blocks to split into. Should be <= n to allow splitting.

    Returns
    -------
    : 1-dim int array
        If nblk <= n, returns the boundaries that divide the integers
        in the range 0..n in nblk almost equal slices.
        The outer boundaries 0 and n are included, so the length of the
        array is nblk+1.
        If nblk >= n, returns range(n+1), thus all slices have length 1.


    Examples
    --------
    >>> splitrange(7,3)
    array([0, 2, 5, 7])
    """
    if n > nblk:
        ndata = (np.arange(nblk+1) * n * 1.0 / nblk).round().astype(int)
    else:
        ndata = np.arange(n+1)
    return ndata


def splitar(a, nblk, axis=0, close=False):
    """Split an array in nblk subarrays along a given axis.

    Parameters
    ----------
    a: :term:`array_like`
        Array to be divided in subarrays.
    nblk: int
        Number of subarrays to obtain. The subarrays will be
        of almost the same size.
    axis: int:
        Axis along which to split the array (default 0)
    close: bool
        If True, the last item of each block will be repeated
        as the first item of the next block.

    Returns
    -------
    : list of arrays
        A list of subarrays obtained by splitting a along the specified axis.
        All arrays have almost the same shape. The number of arrays is equal
        to nblk, unless nblk is larger than a.shape[axis], in which case a
        a list with only the original array is returned.

    Examples
    --------
    >>> splitar(np.arange(7),3)
    [array([0, 1]), array([2, 3, 4]), array([5, 6])]
    >>> splitar(np.arange(7),3,close=True)
    [array([0, 1, 2]), array([2, 3, 4]), array([4, 5, 6])]
    >>> X = np.array([[0.,1.,2.],[3.,4.,5.]])
    >>> splitar(X,2)
    [array([[0., 1., 2.]]), array([[3., 4., 5.]])]
    >>> splitar(X,2,axis=-1)
    [array([[0., 1.],
            [3., 4.]]), array([[2.],
            [5.]])]
    >>> splitar(X,3)
    [array([[0., 1., 2.],
           [3., 4., 5.]])]
    """
    a = np.asanyarray(a).swapaxes(axis, 0)
    na = a.shape[0]
    if close:
        na -= 1
    if nblk > na:
        return [a]

    ndata = splitrange(na, nblk)
    k = 1 if close else 0
    return [a[i:j+k].swapaxes(0, axis) for i, j in zip(ndata[:-1], ndata[1:])]


def minmax(a, axis=-1):
    """Compute the minimum and maximum along an axis.

    Parameters
    ----------
    a: :term:`array_like`
        The data array for which to compute the minimum and maximum.
    axis: int
        The array axis along which to compute the minimum and maximum.

    Returns
    -------
    : array
        The array has the same dtype as `a`. It also has the same shape,
        except for the specified axis, which will have a length of 2.
        The first value along this axis holds the minimum value of the input,
        the second holds the maximum value.

    Examples
    --------
    >>> a = np.array([[[1.,0.,0.], [0.,1.,0.] ],
    ...            [[2.,0.,0.], [0.,2.,0.] ] ])
    >>> print(minmax(a,axis=1))
    [[[0. 0. 0.]
      [1. 1. 0.]]
    <BLANKLINE>
     [[0. 0. 0.]
      [2. 2. 0.]]]
    """
    return np.stack([a.min(axis=axis), a.max(axis=axis)], axis=axis)


def stretch(a, min=None, max=None, axis=None):
    """Scale the values of an array to fill a given range.

    Parameters
    ----------
    a: :term:`array_like`, int or float
        Input data.
    min: int or float, optional
        The targeted minimum value in the array. Same type as `a`.
        If not provided, the minimum of a is used.
    max: int or float, optional
        The targeted maximum value in the array. Same type as `a`.
        If not provided, the maximum of a is used.
    axis: int, optional
        If provided, each slice along the specified axis is
        independently scaled.

    Returns
    -------
    : array
        Array of the same type and size as the input array, but in which
        the values have been linearly scaled to fill the specified range.

    Examples
    --------
    >>> stretch([1.,2.,3.],min=0,max=1)
    array([0. , 0.5, 1. ])
    >>> A = np.arange(6).reshape(2,3)
    >>> stretch(A,min=20,max=30)
    array([[20, 22, 24],
           [26, 28, 30]])
    >>> stretch(A,min=20,max=30,axis=1)
    array([[20, 25, 30],
           [20, 25, 30]])
    >>> stretch(A,max=30)
    array([[ 0, 6, 12],
           [18, 24, 30]])
    >>> stretch(A,min=2,axis=1)
    array([[2, 4, 5],
           [2, 4, 5]])
    >>> stretch(A.astype(Float),min=2,axis=1)
    array([[2. , 3.5, 5. ],
           [2. , 3.5, 5. ]])
    """
    a = np.asarray(a)
    atype = a.dtype
    if min is None:
        min = a.min()
    if max is None:
        max = a.max()
    if not min < max:
        raise ValueError('max must be larger than min in `rng` parameter.')

    amin = a.min(axis=axis)
    amax = a.max(axis=axis)
    if axis is not None:
        amin = np.expand_dims(amin, axis)
        amax = np.expand_dims(amax, axis)
    sc = amax-amin
    if atype.kind == 'i':
        sc = sc.astype(Float)
    b = (a-amin) / sc * (max-min) + min
    if atype.kind == 'i':
        b = b.round()
    return b.astype(atype)


def stringar(s, a):
    """Nicely format a string followed by an array.

    Parameters
    ----------
    s: str
        String to appear before the formatted array
    a: array
        Array to be formatted after the string, with proper vertical
        alignment

    Returns
    -------
    : str
       A multiline string where the first line consists of the
       string s and the first line of the formatted array, and the next lines
       hold the remainder of the array lines, properly indented to align with
       the first line of the array.

    Examples
    --------
    >>> print(stringar("Indented array: ",np.arange(4).reshape(2,2)))
    Indented array: [[0 1]
                     [2 3]]

    """
    s = str(s)
    n = len(s)
    repl = ' '*n
    return s + str(a).replace('\n', '\n'+repl)


def array2str(a):
    """String representation of an array.

    This creates a string representation of an array. It is visually
    equivalent with numpy.ndarray.__repr__ without the dtype, except
    for 'uint.' types.

    Note
    ----
    This function can be used to set the default string representation
    of numpy arrays, using the following::

        import numpy as np
        np.set_string_function(array2str)

    To reset it to the default, do::

        np.set_string_function(None)

    Because this reference manual was created with the default numpy
    routine replaced with ours, you will never see the dtype, except
    for uint types. See also the examples below.

    Parameters
    ----------
    a: array
        Any :class:`numpy.ndarray` object.

    Returns
    -------
        The string representation of the array as created by its
        ``__repr__`` method, except that the ``dtype`` is left away.

    Examples
    --------
    >>> np.set_string_function(array2str)
    >>> a = np.arange(5).astype(np.int8)
    >>> print(array2str(a))
    array([0, 1, 2, 3, 4])
    >>> a
    array([0, 1, 2, 3, 4])

    Reset the numpy string function to its default.
    >>> np.set_string_function(None)
    >>> a
    array([0, 1, 2, 3, 4], dtype=int8)

    Change back to ours.
    >>> np.set_string_function(array2str)
    >>> a
    array([0, 1, 2, 3, 4])

    """
    import re
    return re.sub(r", dtype=[^u]\w*", "", np.array_repr(a))


def printar(s, a):
    """Print a string followed by a vertically aligned array.

    Parameters
    ----------
    s: str
        String to appear before the formatted array
    a: array
        Array to be formatted after the string, with proper vertical
        alignment

    Note
    ----
    This is a shorthand for ``print(stringar(s,a))``.

    Examples
    --------
    >>> printar("Indented array: ",np.arange(4).reshape(2,2))
    Indented array: [[0 1]
                     [2 3]]

    """
    print(stringar(s, a))


def writeArray(fil, array, sep=' '):
    """Write an array to an open file.

    This uses :func:`numpy.tofile` to write an array to an open file.

    Parameters
    ----------
    fil: file or str
        Open file object or filename.
    array: :term:`array_like`
        The array to write to the file.
    sep: str
        If empty, the array is written in binary mode.
        If not empty, the array is written in text mode, with this
        string as separator between the elements.

    See also
    --------
    readArray

    """
    array.tofile(fil, sep=sep)


def readArray(fil, dtype, shape, sep=' '):
    """Read data for an array with known size and type from an open file.

    This uses :func:`numpy.fromfile` to read an array with known shape and
    data type from an open file.

    Parameters
    ----------
    fil: file or str
        Open file object or filename.
    dtype: data-type
        Data type of the array to be read.
    shape: tuple of ints
        The shape of the array to be read.
    sep: str
        If not empty, the array is read in text mode, with this
        string as separator between the elements.
        If empty, the array is read in binary mode and an extra '\\n'
        after the data will be stripped off

    See Also
    --------
    writeArray
    """
    shape = np.asarray(shape)
    size = shape.prod()
    data = np.fromfile(fil, dtype=dtype, count=size, sep=sep).reshape(shape)
    if sep == '':
        pos = fil.tell()
        byte = fil.read(1)
        if not ord(byte) == 10:
            # not a newline: push back
            fil.seek(pos)
    return data


def powers(x, n):
    """Compute all the powers of x from zero up to n.

    Parameters
    ----------
    x: int, float or array (int,float)
        The number or numbers to be raised to the specified powers.
    n: int
        Maximal power to raise the numbers to.

    Returns
    -------
    powers: list
        A list of numbers or arrays of the same shape and type as the input.
        The list contains ``N+1`` items, being the input raised to the powers
        in ``range(n+1)``.

    Examples
    --------
    >>> powers(2,5)
    [1, 2, 4, 8, 16, 32]
    >>> powers(np.array([1.0,2.0]),5)
    [array([1., 1.]), array([1., 2.]), array([1., 4.]), \
    array([1., 8.]), array([ 1., 16.]), array([ 1., 32.])]
    """
    return [x ** i for i in range(n+1)]


###########################################################################
##
##   some math functions
##
#########################

# Convenience functions: trigonometric functions with argument in degrees

def sind(arg, angle_spec=DEG):
    """Return the sine of an angle in degrees.

    Parameters
    ----------
    arg: float number or array
        Angle(s) for which the sine is to be returned.
        By default, angles are specified in degrees (see ``angle_spec``).
    angle_spec: :py:attr:`DEG`, :py:attr:`RAD` or float
        Multiplier to apply to ``arg`` before taking the sine.
        The default multiplier DEG makes the argument
        being intrepreted as an angle in degrees. Use RAD when angles
        are specified in radians.

    Returns
    -------
    :float number or array
        The sine of the input angle(s)

    See also
    --------
    cosd
    tand
    arcsind
    arccosd
    arctand
    arctand2

    Examples
    --------
    >>> print(f"{sind(30):.4f}, {sind(pi/6,RAD):.4f}")
    0.5000, 0.5000
    >>> sind(np.array([0.,30.,45.,60.,90.]))
    array([0.    , 0.5   , 0.7071, 0.866 , 1.    ])
    """
    return np.sin(arg*angle_spec)


def cosd(arg, angle_spec=DEG):
    """Return the cosine of an angle in degrees.

    Parameters
    ----------
    arg: float number or array
        Angle(s) for which the cosine is to be returned.
        By default, angles are specified in degrees (see ``angle_spec``).
    angle_spec: :py:attr:`DEG`, :py:attr:`RAD` or float
        Multiplier to apply to ``arg`` before taking the sine.
        The default multiplier DEG makes the argument
        being intrepreted as an angle in degrees. Use RAD when angles
        are specified in radians.

    Returns
    -------
    :float number or array
        The cosine of the input angle(s)

    See also
    --------
    sind
    tand
    arcsind
    arccosd
    arctand
    arctand2

    Examples
    --------
    >>> print(f"{cosd(60):.4f}, {cosd(pi/3,RAD):.4f}")
    0.5000, 0.5000
    """
    return np.cos(arg*angle_spec)


def tand(arg, angle_spec=DEG):
    """Return the tangens of an angle in degrees.

    Parameters
    ----------
    arg: float number or array
        Angle(s) for which the tangens is to be returned.
        By default, angles are specified in degrees (see ``angle_spec``).
    angle_spec: :py:attr:`DEG`, :py:attr:`RAD` or float
        Multiplier to apply to ``arg`` before taking the sine.
        The default multiplier DEG makes the argument
        being intrepreted as an angle in degrees. Use RAD when angles
        are specified in radians.

    Returns
    -------
    :float number or array
        The tangens of the input angle(s)

    See also
    --------
    sind
    cosd
    arcsind
    arccosd
    arctand
    arctand2

    Examples
    --------
    >>> print(f"{tand(45):.4f}, {tand(pi/4,RAD):.4f}")
    1.0000, 1.0000
    """
    return np.tan(arg*angle_spec)


def arcsind(arg, angle_spec=DEG):
    """Return the angle whose sine is equal to the argument.

    Parameters
    ----------
    arg: float number or array, in the range -1.0 to 1.0.
        Value(s) for which to return the arcsine.
    angle_spec: :py:attr:`DEG`, :py:attr:`RAD` or float, nonzero.
        Divisor applied to the resulting angles before returning.
        The default divisor DEG makes the angles be returned in
        degrees. Use RAD to get angles in radians.

    Returns
    -------
    :float number or array
        The angle(s) for which the input value(s) is/are the cosine.
        The default ``angle_spec=DEG`` returns values in the range
        -90 to +90.

    See also
    --------
    sind
    cosd
    tand
    arccosd
    arctand
    arctand2

    Examples
    --------
    >>> print(f"{arcsind(0.5):.1f} {arcsind(1.0,RAD):.4f}")
    30.0 1.5708
    >>> arcsind(-1)
    -90.0
    >>> arcsind(1)
    90.0
    """
    return np.arcsin(arg)/angle_spec


def arccosd(arg, angle_spec=DEG):
    """Return the angle whose cosine is equal to the argument.

    Parameters
    ----------
    arg: float number or array, in the range -1.0 to 1.0.
        Value(s) for which to return the arccos.
    angle_spec: :py:attr:`DEG`, :py:attr:`RAD` or float, nonzero.
        Divisor applied to the resulting angles before returning.
        The default divisor DEG makes the angles be
        returned in degrees. Use RAD to get angles in radians.

    Returns
    -------
    :float number or array
        The angle(s) for which the input value(s) is/are the cosine.
        The default ``angle_spec=DEG`` returns values in the range
        0 to 180.

    See also
    --------
    sind
    cosd
    tand
    arcsind
    arctand
    arctand2

    Examples
    --------
    >>> print(f"{arccosd(0.5):.1f} {arccosd(-1.0,RAD):.4f}")
    60.0 3.1416
    >>> arccosd(np.array([-1,0,1]))
    array([180.,  90.,   0.])
    """
    return np.arccos(arg)/angle_spec


def arctand(arg, angle_spec=DEG):
    """Return the angle whose tangens is equal to the argument.

    Parameters
    ----------
    arg: float number or array.
        Value(s) for which to return the arctan.
    angle_spec: :py:attr:`DEG`, :py:attr:`RAD` or float, nonzero.
        Divisor applied to the resulting angles before returning.
        The default divisor DEG makes the angles be
        returned in degrees. Use RAD to get angles in radians.

    Returns
    -------
    :float number or array
        The angle(s) for which the input value(s) is/are the tangens.
        The default ``angle_spec=DEG`` returns values in the range
        -90 to +90.

    See also
    --------
    sind
    cosd
    tand
    arcsind
    arccosd
    arctand2

    Examples
    --------

    >>> print(f"{arctand(1.0):.1f} {arctand(-1.0,RAD):.4f}")
    45.0 -0.7854
    >>> arctand(np.array([-np.inf,-1,0,1,np.inf]))
    array([-90., -45.,  0., 45., 90.])
    """
    return np.arctan(arg)/angle_spec


def arctand2(sin, cos, angle_spec=DEG):
    """Return the angle whose sine and cosine values are given.

    Parameters
    ----------
    sin: float number or array with same shape as ``cos``.
        Sine value(s) for which to return the corresponding angle.
    cos: float number or array with same shape as ``sin``
        Cosine value(s) for which to return the corresponding angle.
    angle_spec: :py:attr:`DEG`, :py:attr:`RAD` or float, nonzero.
        Divisor applied to the resulting angles before returning.
        The default divisor DEG makes the angles be returned in degrees.
        Use RAD to get angles in radians.

    Returns
    -------
    :float number or array with same shape as ``sin`` and ``cos``.
        The angle(s) for which the input value(s) are the sine and
        cosine.
        The default ``angle_spec=DEG`` returns values in the range
        [-180, 180].

    Note
    ----
    The input values ``sin`` and ``cos`` are not restricted to the [-1.,1.]
    range. The returned angle is that for which the tangens is given by
    ``sin/cos``, but with a sine and cosine that have the same sign as the
    ``sin`` and ``cos`` values.

    See also
    --------
    sind
    cosd
    tand
    arcsind
    arccosd
    arctand

    Examples
    --------
    >>> print(f"{arctand2(0.0,-1.0):.1f} "
    ...       f"{arctand2(-sqrt(0.5),-sqrt(0.5),RAD):.4f}")
    180.0 -2.3562
    >>> arctand2(np.array([0., 1., 0., -1.]), np.array([1., 0., -1., 0.]))
    array([  0.,  90., 180., -90.])
    >>> arctand2(2.,2.)
    45.0
    """
    return arctan2(sin, cos)/angle_spec


def niceLogSize(f):
    """Return an integer estimate of the magnitude of a float number.

    Parameters
    ----------
    f: float
        Value for which the integer magnitude has to be computed. The
        sign of the value is disregarded.

    Returns
    -------
    :int
        An integer magnitude estimator for the input.

    Note
    ----
    The returned value is the smallest integer ``e`` such that
    ``10**e > abs(f)``.
    If positive, it is equal to the number of digits
    before the decimal point; if negative, it is equal to the number of
    leading zeros after the decimal point.

    See also
    --------
    nicenumber

    Examples
    --------
    >>> print([niceLogSize(a) for a in [1.3, 35679.23, 0.4, 0.0004567, -1.3] ])
    [1, 5, 0, -3, 1]
    """
    return int(np.ceil(np.log10(abs(f))))


def niceNumber(f, round=np.ceil):
    """Return a nice number close to abs(f).

    A nice number is a number which only has only one significant digit
    (in the decimal system).

    Parameters
    ----------
    f: float
        A float number to approximate with a nice number. The sign of ``f``
        is disregarded.
    round: callable
        A function that rounds a float to the nearest integer. Useful
        functions are ``ceil``, ``floor`` and ``round`` from either
        NumPy or Python's math module. Default is ``numpy.ceil``.

    Returns
    -------
    :float
        A float value close to the input value, but having only
        a single decimal digit.

    Examples
    --------
    >>> numbers = [0.0837, 0.867, 8.5, 83.7, 93.7]
    >>> [str(niceNumber(f)) for f in numbers ]
    ['0.09', '0.9', '9.0', '90.0', '100.0']
    >>> [str(niceNumber(f,round=np.floor)) for f in numbers ]
    ['0.08', '0.8', '8.0', '80.0', '90.0']
    >>> [str(niceNumber(f,round=np.round)) for f in numbers ]
    ['0.08', '0.9', '8.0', '80.0', '90.0']
    """
    fa = abs(f)
    s = f"{fa:.1e}"
    m, n = s.split('e')
    m = int(round(float(m)))
    n = int(n)
    return m*10.**n


def isqrt(n):
    """Compute the square root of an integer number.

    Parameters
    ----------
    n: int
        An integer number that is a perfect square.

    Returns
    -------
    :int
        The square root from the input number

    Raises
    ------
    ValueError:
        If the input integer is not a perfect square.

    Examples
    --------
    >>> isqrt(36)
    6
    """
    i = int(np.sqrt(n) + 0.5)
    if i*i != n:
        raise ValueError(f"Input is not a perfect square: {n}")
    return i


###########################################################################
##
##   Vector operations
##
#########################

def dotpr(A, B, axis=-1):
    """Return the dot product of vectors of A and B in the direction of axis.

    Parameters
    ----------
    A: float :term:`array_like`
        Array containing vectors in the direction of axis.
    B: float :term:`array_like`
        Array containing vectors in the direction of axis. Same shape
        as A, or broadcast-compatible.
    axis: int
        Axis of A and B in which direction the vectors are layed out.
        Default is the last axis. A and B should have the same length
        along this axis.

    Returns
    -------
    float array, shape as A and B with axis direction removed.
        The elements contain the dot product of the vectors of A and B at
        that position.

    Note
    ----
    This multiplies the elements of the A and B and then sums them
    in the direction of the specified axis.

    Examples
    --------
    >>> A = np.array( [[1.0, 1.0], [1.0,-1.0], [0.0, 5.0]] )
    >>> B = np.array( [[5.0, 3.0], [2.0, 3.0], [1.33,2.0]] )
    >>> print(dotpr(A,B))
    [ 8. -1. 10.]
    >>> print(dotpr(A,B,0))
    [ 7. 10.]

    """
    A = np.asarray(A)
    B = np.asarray(B)
    return (A*B).sum(axis)


def length(A, axis=-1):
    """Returns the length of the vectors of A in the direction of axis.

    Parameters
    ----------
    A: float :term:`array_like`
        Array containing vectors in the direction of axis.
    axis: int
        Axis of A in which direction the vectors are layed out.
        Default is the last axis. A and B shoud have the same length
        along this axis.

    Returns
    -------
    : float array, shape of A with axis direction removed.
        The elements contain the length of the vector in A at that position.

    Note
    ----
    This is equivalent with ``sqrt(dotpr(A,A))``.

    Examples
    --------
    >>> A = np.array( [[1.0, 1.0], [1.0,-1.0], [0.0, 5.0]] )
    >>> print(length(A))
    [1.4142 1.4142 5.    ]
    >>> print(length(A,0))
    [1.4142 5.1962]

    """
    A = np.asarray(A)
    return sqrt((A*A).sum(axis))


def normalize(A, axis=-1, on_zeros='n', return_length=False, ignore_zeros=False):
    """Normalize the vectors of A in the direction of axis.

    Parameters
    ----------
    A: float :term:`array_like`
        Array containing vectors in the direction of axis.
    axis: int
        Axis of A in which direction the vectors are layed out.
    on_zeros: 'n', 'e' or 'i'
        Specifies how to treat occurrences of zero length vectors (having
        all components equal to zero):

        - 'n': return a vector of nan values
        - 'e': raise a ValueError
        - 'i': ignore zero vectors and return them as such.

    return_length: bool
        If True, also returns also the length of the original vectors.

    ignore_zeros: bool
         (Deprecated) Equivalent to specifying ``on_zeros='i'``.

    Returns
    -------
    norm: float array
        Array with same shape as A but where each vector along axis
        has been rescaled so that its length is 1.
    len: float array, optional
        Array with shape like A but with axis removed. The length of
        the original vectors in the direction of axis. Only returned
        if ``return_length=True`` provided.

    Raises
    ------
    ValueError: Can not normalize zero-length vector
        If any of the  vectors of B is a zero vector.

    Examples
    --------
    >>> A = np.array( [[3.0, 3.0], [4.0,-3.0], [0.0, 0.0]] )
    >>> print(normalize(A))
    [[ 0.7071  0.7071]
     [ 0.8    -0.6   ]
     [    nan     nan]]
    >>> print(normalize(A,on_zeros='i'))
    [[ 0.7071  0.7071]
     [ 0.8    -0.6   ]
     [ 0.      0.    ]]
    >>> print(normalize(A,0))
    [[ 0.6     0.7071]
     [ 0.8    -0.7071]
     [ 0.      0.    ]]
    >>> n,l = normalize(A,return_length=True)
    >>> print(n)
    [[ 0.7071  0.7071]
     [ 0.8    -0.6   ]
     [    nan     nan]]
    >>> print(l)
    [4.2426 5.     0.    ]

    """
    if ignore_zeros:
        on_zeros = 'i'
    A = np.asarray(A)
    Al = length(A, axis)
    if on_zeros != 'n':
        if (Al == 0.).any():
            if on_zeros=='i':
                Al[Al==0.] = 1.
            else:
                raise ValueError("Can not normalize zero-length vector.")
    with np.errstate(divide='ignore', invalid='ignore'):
        res = A / np.expand_dims(Al, axis)
    if return_length:
        return res, Al
    else:
        return res


def projection(A, B, axis=-1):
    """Return the (signed) length of the projection of vectors of A on B.

    Parameters
    ----------
    A: float :term:`array_like`
        Array containing vectors in the direction of axis.
    B: float :term:`array_like`
        Array containing vectors in the direction of axis. Same shape
        as A, or broadcast-compatible.
    axis: int
        Axis of A and B in which direction the vectors are layed out.
        Default is the last axis. A and B should have the same length
        along this axis.

    Returns
    -------
    : float array, shape as A and B with axis direction removed.
        The elements contain the length of the projections of vectors of A
        on the directions of the corresponding vectors of B.

    Raises
    ------
    ValueError: Can not normalize zero-length vector
        If any of the  vectors of B is a zero vector.

    Note
    ----
    This returns ``dotpr(A,normalize(B))``.

    Examples
    --------
    >>> A = [[2.,0.],[1.,1.],[0.,1.]]
    >>> projection(A,[1.,0.])
    array([2., 1., 0.])
    >>> projection(A,[1.,1.])
    array([1.4142, 1.4142, 0.7071])
    >>> projection(A,[[1.],[1.],[0.]],axis=0)
    array([2.1213, 0.7071])

    """
    return dotpr(A, normalize(B, axis=axis, on_zeros='e'), axis=axis)


def parallel(A, B, axis=-1):
    """Return the component of vector of A that is parallel to B.

    Parameters
    ----------
    A, B: float :term:`array_like`
        Broadcast compatible arrays containing vectors in the direction of
        axis.
    axis: int
        Axis of A and B in which direction the vectors are layed out.
        Default is the last axis. A and B should have the same dimension
        along this axis.

    Returns
    -------
    : float array, same shape as A and B.
        The vectors in the axis direction are the vectors of A projected
        on the direction of the corresponding vectors of B.

    See also
    --------
    orthog

    Examples
    --------
    >>> A = [[2.,0.],[1.,1.],[0.,1.]]
    >>> parallel(A,[1.,0.])
    array([[2., 0.],
           [1., 0.],
           [0., 0.]])
    >>> parallel(A,A)
    array([[2., 0.],
           [1., 1.],
           [0., 1.]])
    >>> parallel(A,[[1.],[1.],[0.]],axis=0)
    array([[1.5, 0.5],
           [1.5, 0.5],
           [0. , 0. ]])

    """
    Bn = normalize(B, axis=axis, on_zeros='e')
    p = dotpr(A, Bn, axis=axis)
    return np.expand_dims(p, axis) * Bn


def orthog(A, B, axis=-1):
    """Return the component of vector of A that is orthogonal to B.

    Parameters
    ----------
    A: float :term:`array_like`
        Array containing vectors in the direction of axis.
    B: float :term:`array_like`
        Array containing vectors in the direction of axis. Same shape
        as A, or broadcast-compatible.
    axis: int
        Axis of A and B in which direction the vectors are layed out.
        Default is the last axis. A and B should have the same length
        along this axis.

    Returns
    -------
    : float array, same shape as A and B.
        The vectors in the axis direction are the components of the vectors
        of A orthogonal to the direction of the corresponding vectors of B.

    See also
    --------
    parallel

    Examples
    --------
    >>> A = [[2.,0.],[1.,1.],[0.,1.]]
    >>> orthog(A,[1.,0.])
    array([[0., 0.],
           [0., 1.],
           [0., 1.]])
    >>> orthog(A,[[1.],[1.],[0.]],axis=0)
    array([[ 0.5, -0.5],
           [-0.5,  0.5],
           [ 0. ,  1. ]])

    """
    return A - parallel(A, B, axis=axis)


def inside(p, mi, ma):
    """Return true if point p is inside bbox defined by points mi and ma.

    Parameters
    ----------
    p: float :term:`array_like` with shape (ndim,)
        Point to test against the boundaries.
    mi: float :term:`array_like` with shape (ndim,)
        Minimum values for the components of p
    ma: float :term:`array_like` with shape (ndim,)
        Maximum values for the components of p

    Returns
    -------
    :bool
        True is all components are inside the specified limits, limits
        included. This means that the n-dimensional point p lies within
        the n-dimensional rectangular bounding box defined by the two
        n-dimensional points (mi,ma).

    Examples
    --------
    >>> inside([0.5,0.5],[0.,0.],[1.,1.])
    True
    >>> inside([0.,1.],[0.,0.],[1.,1.])
    True
    >>> inside([0.,1.1],[0.,0.],[1.,1.])
    False
    """
    p = np.asarray(p)
    return (p >= mi).all() and (p <= ma).all()


def unitVector(v):
    """Return a unit vector in the direction of v.

    Parameters
    ----------
    v: a single integer or a (3,) shaped float :term:`array_like`
        If an int, it specifies one of the global axes (0,1,2).
        Else, it is a vector in 3D space.

    Returns
    -------
    : (3,) shaped float array
        A unit vector along the specified direction.

    Examples
    --------
    >>> unitVector(1)
    array([0., 1., 0.])
    >>> unitVector([0.,3.,4.])
    array([0. , 0.6, 0.8])

    """
    if isInt(v):
        if v not in range(3):
            raise ValueError("v should be one of 0, 1 or 2")
        u = np.zeros((3), dtype=Float)
        u[v] = 1.0
    else:
        v = checkArray(v, shape=(3,), kind='f', allow='i')
        u = normalize(v, on_zeros='e')
    return u


def rotationMatrix(angle, axis=None, angle_spec=DEG):
    """Create a 2D or 3D rotation matrix over angle, optionally around axis.

    Parameters
    ----------
    angle: float
        Rotation angle, by default in degrees.
    axis: int or (3,) float :term:`array_like`, optional
        If not provided, a 2D rotation matrix is returned.
        If provided, it specifies the rotation axis in a 3D world. It is either
        one of 0,1,2, specifying a global axis, or a vector with 3 components
        specifying an axis through the origin. The returned matrix is 3D.
    angle_spec: float, DEG or RAD, optional
        The default (DEG) interpretes the angle in degrees. Use RAD to
        specify the angle in radians.

    Returns
    -------
    float array
        Rotation matrix which will rotate a vector over the specified angle.
        Shape is (3,3) if axis is specified, or (2,2) if not.

    See also
    --------
    rotationMatrix3: subsequent rotation around 3 axes
    rotmat: rotation matrix specified by three points in space
    trfmat: transformation matrix to transform 3 points
    rotMatrix: rotation matrix transforming global axis 0 into a given vector
    rotMatrix2: rotation matrix that transforms one vector into another

    Examples
    --------
    >>> rotationMatrix(30.,1)
    array([[ 0.866,  0.   , -0.5  ],
           [ 0.   ,  1.   ,  0.   ],
           [ 0.5  ,  0.   ,  0.866]])
    >>> rotationMatrix(45.,[1.,1.,0.])
    array([[ 0.8536,  0.1464, -0.5   ],
           [ 0.1464,  0.8536,  0.5   ],
           [ 0.5   , -0.5   ,  0.7071]])
    """
    a = angle*angle_spec
    c = cos(a)
    s = sin(a)
    if axis is None:
        f = [[c, s], [-s, c]]
    elif np.array(axis).size == 1:
        f = np.zeros((3, 3))
        axes = list(range(3))
        i, j, k = axes[axis:]+axes[:axis]
        f[i][i] = 1.0
        f[j][j] = c
        f[j][k] = s
        f[k][j] = -s
        f[k][k] = c
    else:
        X, Y, Z = unitVector(axis)
        t = 1.-c
        f = [[t*X*X + c, t*X*Y + s*Z, t*X*Z - s*Y],
             [t*Y*X - s*Z, t*Y*Y + c, t*Y*Z + s*X],
             [t*Z*X + s*Y, t*Z*Y - s*X, t*Z*Z + c]]

    return np.array(f)


def rotationMatrix3(rx, ry, rz, angle_spec=DEG):
    """Create a rotation matrix defined by three angles.

    This applies successive rotations about the 0, 1 and 2 axes, over
    the angles rx, ry and rz, respectively. These angles are also known
    as the cardan angles.

    Parameters
    ----------
    rx: float
        Rotation angle around the 0 axis.
    ry: float
        Rotation angle around the 1 axis.
    rz: float
        Rotation angle around the 2 axis.
    angle_spec: float, DEG or RAD, optional
        The default (DEG) interpretes the angles in degrees. Use RAD to
        specify the angle in radians.

    Returns
    -------
    : float array (3,3)
        Rotation matrix that performs the combined rotation equivalent
        to subsequent rotations around the three global axes.

    See Also
    --------
    rotationMatrix: rotation matrix specified by an axis and angle
    cardanAngles: find cardan angles that produce a given rotation matrix

    Examples
    --------
    >>> rotationMatrix3(60,45,30)
    array([[ 0.6124,  0.3536, -0.7071],
           [ 0.2803,  0.7392,  0.6124],
           [ 0.7392, -0.5732,  0.3536]])
    """
    Rx = rotationMatrix(rx, 0, angle_spec=angle_spec)
    Ry = rotationMatrix(ry, 1, angle_spec=angle_spec)
    Rz = rotationMatrix(rz, 2, angle_spec=angle_spec)
    return np.dot(Rx, np.dot(Ry, Rz))


def cardanAngles(R, angle_spec=DEG):
    """Compute cardan angles from rotation matrix

    Computes the angles over which to rotate subsequently around
    the 0-axis, the 1-axis and the 2-axis to obtain the rotation
    corresponding to the given rotation matrix.

    Parameters
    ----------
    R: (3,3) float :term:`array_like`
        Rotation matrix for post multiplication (see Notes)
    angle_spec: :py:attr:`DEG`, :py:attr:`RAD` or float, nonzero.
        Divisor applied to the resulting angles before returning.
        The default divisor DEG makes the angles be returned in
        degrees. Use RAD to get angles in radians.

    Returns
    -------
    (rx,ry,rz): tuple of floats
        The three rotation angles around that when applied subsequently
        around the global 0, 1 and 2 axes, yield the same rotation
        as the input. The default angle_spec=DEG returns the angles
        in degrees.

    Notes
    -----
    The returned angles are but one of many ways to obtain a given
    rotation by three subsequent rotations around frame axes. Look
    on the web for 'Euler angles' to get comprehensive information.
    Different sets of angles can be obtained depending on the sequence
    of rotation axes used, and whether fixed axes (extrinsic) or
    rotated axes (intrinsic) are used in subsequent rotations.
    The here obtained 'cardan' angles are commonly denoted as a zy'x''
    system with intrinsic angles or xyz with extrinsic angles. It is the
    latter angles that are returned.

    Because pyFormex stores rotation matrices as post-multiplication
    matrices (to be applied on row-vectors), the combined rotation
    around first the 0-axis, then the 1-axis and finally the 2-axis,
    is found as the matrix product Rx.Ry.Rz. (Traditionally,
    vectors were often written as column matrices, and rotation
    matrices were pre-multiplication matrices, so the subsequent
    rotation matrices would have to be multiplied in reverse order.)

    Even if one chooses a single frame system for the subsequent
    rotations, the resulting angles are not unique. There are infinitely
    many sets of angles that will result in the same rotation matrix.
    The implementation here results in angles rx and rz in the range
    [-pi,pi], while the angle ry will be in [-pi/2,pi/2]. Even then,
    there remain infinite solutions in the case where the elements
    R[0,2] == R[2,0] equal +1 or -1 (ry = +pi/2 or -pi/2). The result
    will then be the solution with rx==0.

    Examples
    --------
    >>> print("%8.2f  "*3 % cardanAngles(rotationMatrix3(60,45,30)))
       60.00     45.00     30.00
    >>> print("%8.2f  "*3 % cardanAngles(rotationMatrix3(0,90,77)))
        0.00     90.00     77.00
    >>> print("%8.2f  "*3 % cardanAngles(rotationMatrix3(0,-90,30)))
        0.00    -90.00     30.00

    But:

    >>> print("%8.2f  "*3 % cardanAngles(rotationMatrix3(20,-90,30)))
        0.00    -90.00     50.00

    """
    if abs(R[0, 2]) < 1.:
        theta = -arcsin(R[0, 2])
        if theta < -pi/2:
            theta = pi - theta
        c = cos(theta)
        psi = arctan2(R[1, 2]/c, R[2, 2]/c)
        phi = arctan2(R[0, 1]/c, R[0, 0]/c)

    else:
        psi = 0.
        if R[0, 2] < 0.:
            theta = pi/2
            phi = psi - arctan2(R[1, 0], R[2, 0])
        else:
            theta = -pi/2
            phi = psi + arctan2(-R[1, 0], -R[2, 0])

    return psi/DEG, theta/DEG, phi/DEG


def rotmat(x):
    """Create a rotation matrix defined by 3 points in space.

    Parameters
    ----------
    x: :term:`array_like` (3,3)
        The rows contain the coordinates in 3D space of three non-colinear
        points x0, x1, x2.

    Returns
    -------
    rotmat: matrix(3,3)
        Rotation matrix which transforms the global axes
        into a new (orthonormal) coordinate system with the
        following properties:

        - the origin is at point x0,
        - the 0 axis is along the direction x1-x0
        - the 1 axis is in the plane (x0,x1,x2) with x2 lying
          at the positive side.

    Notes
    -----
    The rows of the rotation matrix represent the unit vectors
    of the resulting coordinate system.
    The coodinates in the rotated axes of any point are
    obtained by the reverse transformation, i.e. multiplying the
    point with the transpose of the rotation matrix.

    See also
    --------
    rotationMatrix: rotation matrix specified by angle and axis
    trfmat: transformation matrices defined by 2 sets of 3 points
    rotMatrix: rotation matrix transforming global axis 0 into a given vector
    rotMatrix2: rotation matrix that transforms one vector into another

    Examples
    --------
    >>> rotmat([[0,0,0],[1,0,0],[0,1,0]])
    array([[1., 0., 0.],
           [0., 1., 0.],
           [0., 0., 1.]])
    >>> rotmat(np.eye(3,3))
    array([[-0.7071,  0.7071,  0.    ],
           [-0.4082, -0.4082,  0.8165],
           [ 0.5774,  0.5774,  0.5774]])
    >>> s,c = sind(30),cosd(30)
    >>> R = rotmat([[0,0,0],[c,s,0],[0,1,0]])
    >>> print(R)
    [[ 0.866  0.5    0.   ]
     [-0.5    0.866  0.   ]
     [ 0.    -0.     1.   ]]
    >>> B = np.array([[2.,0.,0.],[3*s,3*c,3]])
    >>> D = np.dot(B,R)    # Rotate some vectors with the matrix R
    >>> print(D)
    [[ 1.7321  1.      0.    ]
     [-0.      3.      3.    ]]
    """
    x = checkArray(x, shape=(3, 3), kind='f', allow='i')
    u = normalize(x[1]-x[0])
    v = normalize(x[2]-x[0])
    v = normalize(orthog(v, u))
    w = np.cross(u, v)  # is orthog and normalized
    m = np.row_stack([u, v, w])
    return m


def trfmat(x, y):
    """Find the transformation matrices from 3 points x into y.

    Constructs the rotation matrix and translation vector that will
    transform the points x thus that:

    - point x0 coincides with point y0,
    - line x0,x1 coincides with line y0,y1
    - plane x0,x1,x2 coincides with plane y0,y1,y2

    Parameters
    ----------
    x: float :term:`array_like` (3,3)
        Original coordinates of three  non-colinear points.
    y: float :term:`array_like` (3,3)
        Final coordinates of the three points.

    Returns
    -------
    rot: float array (3,3)
        The rotation matrix for the transformation x to y.
    trf:
         float array(3,)
        The translation vector for the transformation x to y, Obviously,
        this is equal to y0-x0.


    The rotation is to be applied first and should be around the first
    point x0. The full transformation of a Coords object is thus obtained
    by ``(coords-x0)*rot+trl+x0 = coords*rot+(trl+x0-x0*rot)``.

    Examples
    --------
    >>> R,T = trfmat(np.eye(3,3), [[0,0,0],[1,0,0],[0,1,0]])
    >>> print(R)
    [[-0.7071 -0.4082  0.5774]
     [ 0.7071 -0.4082  0.5774]
     [ 0.      0.8165  0.5774]]
    >>> print(T)
    [ 0.7071  0.4082 -0.5774]
    """
    # rotation matrices for both systems
    r1 = rotmat(x)
    r2 = rotmat(y)
    # combined rotation matrix
    r = np.dot(r1.transpose(), r2)
    # translation vector (in a rotate first operation
    t = y[0] - np.dot(x[0], r)
    return r, t


def any_perp(u):
    """Return any vector perpendicular to u

    The vector doesn't have to be normalized.

    Examples
    --------
    >>> any_perp([1., 1., 1.])
    array([ 0.,  1., -1.])
    >>> any_perp([1., 1.e-6, -1.e-6])
    array([0., 0., 1.])
    >>> any_perp([6., 4., 5.])
    array([-5.,  0.,  6.])
    """
    i = np.argmin(np.abs(u))
    v = np.roll(u, 2-i)
    v[0], v[1] = v[1], -v[0]
    v[2] = 0
    v = np.roll(v, i-2)
    return v


def rotMatrix(u, w=[0., 0., 1.]):
    # TODO: we could allow here a None value for w, like in rotMatrix2
    """Create a rotation matrix that rotates global axis 0 to a given vector.

    Parameters
    ----------
    u: (3,) :term:`array_like`
        Vector specifying the direction to which the global axis 0 should
        be rotated by the returned rotation matrix.
    w: (3,) :term:`array_like`
        Vector that is not parallel to u. This vector is used to uniquely
        define the resulting rotation. It will be equivalent to rotating
        first around ``w``, until the target ``u`` lies in the plane
        of the rotated axis 0 and ``w``, then rotated in that plane until
        the rotated axis 0 coincides with ``u``. See also Note.
        If a parallel w is provided, it will be replaced with a non-parallel
        one.

    Returns
    -------
    : float array (3,3)
        Rotation matrix that transforms a vector [1.,0.,0.] into ``u``.
        The returned matrix should be used in postmultiplication to the
        coordinates.

    See Also
    --------
    rotMatrix2: rotation matrix that transforms one vector into another
    rotationMatrix: rotation matrix specified by an axis and angle
    rotmat: rotation matrix specified by three points in space
    trfmat: rotation and translation matrix that transform three points

    Examples
    --------
    >>> rotMatrix([1,0,0])
    array([[1., 0., 0.],
           [0., 1., 0.],
           [0., 0., 1.]])
    >>> rotMatrix([0,1,0])
    array([[ 0.,  1.,  0.],
           [-1.,  0.,  0.],
           [ 0., -0.,  1.]])
    >>> rotMatrix([0,0,1])
    array([[ 0.,  0.,  1.],
           [ 1., -0.,  0.],
           [ 0.,  1., -0.]])
    >>> rotMatrix([0,1,1])
    array([[ 0.    ,  0.7071,  0.7071],
           [-1.    ,  0.    ,  0.    ],
           [ 0.    , -0.7071,  0.7071]])
    >>> rotMatrix([1,0,1])
    array([[ 0.7071,  0.    ,  0.7071],
           [ 0.    ,  1.    ,  0.    ],
           [-0.7071,  0.    ,  0.7071]])
    >>> rotMatrix([1,1,0])
    array([[ 0.7071,  0.7071,  0.    ],
           [-0.7071,  0.7071,  0.    ],
           [ 0.    , -0.    ,  1.    ]])
    >>> rotMatrix([1,1,1])
    array([[ 0.5774,  0.5774,  0.5774],
           [-0.7071,  0.7071,  0.    ],
           [-0.4082, -0.4082,  0.8165]])

    >>> np.dot([1,0,0], rotMatrix([1,1,1]))
    array([0.5774, 0.5774, 0.5774])
    """
    u = unitVector(u)
    w = unitVector(w)
    v = np.cross(w, u)
    if length(v) == 0:
        # u and w are parallel
        w = any_perp(u)
        v = np.cross(w, u)
    v = unitVector(v)
    w = unitVector(np.cross(u, v))
    m = np.row_stack([u, v, w])
    return m


def rotMatrix2(vec1, vec2, upvec=None):
    """Create a rotation matrix that rotates a vector vec1 to vec2.

    Parameters
    ----------
    vec1: (3,) :term:`array_like`
        Original vector.
    vec2: (3,) :term:`array_like`
        Direction of ``vec1`` after rotation.
    upvec: (3,) :term:`array_like`, optional
        If provided, the rotation matrix will be such that the plane of
        vec2 and the rotated upvec will be parallel to the original upvec.
        If not provided, the rotation matrix will perform a rotation
        around the normal to the plane on the two vectors.

    Returns
    -------
    : float array (3,3)
        Rotation matrix that transforms a vector ``vec1`` into ``vec2``.
        The returned matrix should be used in postmultiplication to the
        coordinates.

    See Also
    --------
    rotMatrix: rotation matrix transforming global axis 0 into a given vector
    rotationMatrix: rotation matrix specified by an axis and angle
    rotmat: rotation matrix specified by three points in space
    trfmat: rotation and translation matrix that transform three points

    Examples
    --------
    >>> rotMatrix2([1,0,0],[1,0,0])
    array([[1., 0., 0.],
           [0., 1., 0.],
           [0., 0., 1.]])
    >>> rotMatrix2([1,0,0],[-1,0,0])
    array([[-1., -0., -0.],
           [-0., -1., -0.],
           [-0., -0., -1.]])
    >>> rotMatrix2([1,0,0],[0,1,0])
    array([[ 0., 1., 0.],
           [-1., 0., 0.],
           [ 0., 0., 1.]])
    >>> rotMatrix2([1,0,0],[0,0,1])
    array([[ 0., 0., 1.],
           [ 0., 1., 0.],
           [-1., 0., 0.]])
    >>> rotMatrix2([1,0,0],[0,1,1])
    array([[ 0.    ,  0.7071,  0.7071],
           [-0.7071,  0.5   , -0.5   ],
           [-0.7071, -0.5   ,  0.5   ]])
    >>> rotMatrix2([1,0,0],[1,0,1])
    array([[ 0.7071,  0.    ,  0.7071],
           [ 0.    ,  1.    ,  0.    ],
           [-0.7071,  0.    ,  0.7071]])
    >>> rotMatrix2([1,0,0],[1,1,0])
    array([[ 0.7071,  0.7071,  0.    ],
           [-0.7071,  0.7071,  0.    ],
           [ 0.    ,  0.    ,  1.    ]])
    >>> rotMatrix2([1,0,0],[1,1,1])
    array([[ 0.5774,  0.5774,  0.5774],
           [-0.5774,  0.7887, -0.2113],
           [-0.5774, -0.2113,  0.7887]])
    >>> rotMatrix2([1,0,0],[1,0,0],[0,0,1])
    array([[1., 0., 0.],
           [0., 1., 0.],
           [0., 0., 1.]])
    >>> rotMatrix2([1,0,0],[0,1,0],[0,0,1])
    array([[ 0., 1., 0.],
           [-1., 0., 0.],
           [ 0., 0., 1.]])
    >>> rotMatrix2([1,0,0],[0,0,1],[0,0,1])
    array([[0., 0., 1.],
           [1., 0., 0.],
           [0., 1., 0.]])
    >>> rotMatrix2([1,0,0],[0,1,1],[0,0,1])
    array([[ 0.    ,  0.7071,  0.7071],
           [-1.    ,  0.    ,  0.    ],
           [ 0.    , -0.7071,  0.7071]])
    >>> rotMatrix2([1,0,0],[1,0,1],[0,0,1])
    array([[ 0.7071,  0.    ,  0.7071],
           [ 0.    ,  1.    ,  0.    ],
           [-0.7071,  0.    ,  0.7071]])
    >>> rotMatrix2([1,0,0],[1,1,0],[0,0,1])
    array([[ 0.7071,  0.7071,  0.    ],
           [-0.7071,  0.7071,  0.    ],
           [ 0.    ,  0.    ,  1.    ]])
    >>> rotMatrix2([1,0,0],[1,1,1],[0,0,1])
    array([[ 0.5774,  0.5774,  0.5774],
           [-0.7071,  0.7071,  0.    ],
           [-0.4082, -0.4082,  0.8165]])
    """
    vec1 = checkArray(vec1, shape=(3,), kind='f', allow='i')
    vec2 = checkArray(vec2, shape=(3,), kind='f', allow='i')
    if upvec is None:
        upvec = np.cross(vec1, vec2)
        if length(upvec) == 0.:  # vec1 and vec2 are parallel
            mat = np.eye(3, 3, dtype=Float)
            if vec1 @ vec2 < 0.:
                mat = -mat
            return mat
    mat1 = rotMatrix(vec1, upvec)
    mat2 = rotMatrix(vec2, upvec)
    mat = np.dot(mat1.T, mat2)
    return mat


def abat(a, b):
    """Compute the matrix product a * b * at.

    Parameters
    ----------
    a: :term:`array_like`, 2-dim
        Array with shape (m,n).
    b: :term:`array_like`, 2-dim
        Array with square shape (n,n).

    Returns
    -------
    :array
        Array with shape (m,m) holding the matrix product a * b * at.

    See Also
    --------
    atba

    Examples
    --------
    >>> abat([[1],[2]],[[3]])
    array([[ 3,  6],
           [ 6, 12]])
    >>> abat([[1,2]],[[0,1],[2,3]])
    array([[18]])
    """
    a = checkArray(a, ndim=2)
    b = checkArray(b, shape=(a.shape[1], a.shape[1]))
    return np.dot(np.dot(a, b), a.T)


def atba(a, b):
    """Compute the matrix product at * b * a

    Parameters
    ----------
    a: :term:`array_like`, 2-dim
        Array with shape (n,m).
    b: :term:`array_like`, 2-dim
        Array with square shape (n,n).

    Returns
    -------
    :array
        Array with shape (m,m) holding the matrix product at * b * a.

    Note
    ----
    This multiplication typically occurs when rotating a symmetric tensor b
    to axes defined by the rotation matrix a.

    See Also
    --------
    abat

    Examples
    --------
    >>> atba([[1,2]],[[3]])
    array([[ 3,  6],
           [ 6, 12]])
    >>> atba([[1],[2]],[[0,1],[2,3]])
    array([[18]])
    """
    a = checkArray(a, ndim=2)
    b = checkArray(b, shape=(a.shape[0], a.shape[0]))
    return np.dot(np.dot(a.T, b), a)


def horner(a, u):
    """Compute the value of a polynom using Horner's rule.

    Parameters
    ----------
    a: float :term:`array_like` (n+1,nd)
        ``nd``-dimensional coefficients of a polynom of degree ``n``
        in a scalar variable ``u``. The coefficients are in order of
        increasing degree.
    u: float :term:`array_like` (nu)
        Parametric values where the polynom is to be evaluated.

    Returns
    -------
    :float array(nu,nd)
        The nd-dimensional values of the polynom at the specified `nu`
        parameter values.

    Examples
    --------
    >>> print(horner([[1.,1.,1.],[1.,2.,3.]],[0.5,1.0]))
    [[1.5 2.  2.5]
     [2.  3.  4. ]]

    """
    a = checkArray(a, ndim=2, kind='f', allow='i')
    u = checkArray(u, ndim=1, kind='f', allow='i').reshape(-1, 1)
    c = a[-1]
    for i in range(-2, -1-len(a), -1):
        c = c * u + a[i]
    return c


def solveMany(A, B):
    """Solve many systems of linear equations.

    Parameters
    ----------
    A: float :term:`array_like` (nsys,ndof,ndof)
        Coefficient matrices for nsys systems of ndof linear equations
        in ndof unknowns.
    B: float :term:`array_like` (nsys,ndof,nrhs)
        Right hand sides for the nsys systems of linear equations in ndof
        unkn owns.
        Each of the nsys systems is solved simultaneously for nrhs right
        hand sides.

    Returns
    -------
    X: float array (nsys,ndof,nrhs)
        The set of values X(nsys,ndof,nrhs) that solve the systems of linear
        equations A @ X = B, where @ is the Python matrix multiplication
        operator. Thus for each set of submatrices A[i], B[i], X[i], the
        normal matrix multiplication holds: A[i] . X[i] = B[i].


    Notes
    -----
    For values of ndof >= 4, a general linear system soultion method is used.
    For values 1, 2 or 3 however, a direct solution method is used which is
    much faster.

    Examples
    --------
    This example creates random systems of linear equations and random values
    for the unknown variables, then computes the right hand sides, and solves
    the equations. Finally the found solution is compared with the original
    values of the unknowns.
    In rare cases however, one of the randomly generated systems may be
    (nearly) singular, and the solution will not match the preset values.
    In that case we repeat the process, and the change of having a failure
    again is extermely small.

    >>> def solveRandom(nsys, ndof, nrhs):
    ...     A = np.random.rand(nsys, ndof, ndof)
    ...     for i in range(nsys):
    ...         if abs(np.linalg.det(A[i])) < 1.e-4:
    ...             A[i] = np.random.rand(ndof, ndof)
    ...     X = np.random.rand(nsys, ndof, nrhs)
    ...     B = np.stack([np.dot(a,x) for a,x in zip(A,X)])
    ...     Y = solveMany(A,B)
    ...     return np.allclose(X,Y,atol=1.e-2)
    >>> nsys, nrhs = 10, 5
    >>> ok =[solveRandom(nsys,ndof,nrhs) for ndof in [1,2,3,4]]
    >>> print(ok)
    [True, True, True, True]
    """
    B = checkArray(B, ndim=3, kind='f', allow='i')
    nsys, ndof, nrhs = B.shape
    A = checkArray(A, shape=(nsys, ndof, ndof), kind='f', allow='i')

    if ndof < 4:
        if ndof == 1:
            X = B / A

        else:
            AA = np.expand_dims(A, 3)
            BB = np.expand_dims(B, 2)
            if ndof == 2:
                N = np.cross(AA[:, :, 0], AA[:, :, 1], axis=1)
                AS = np.roll(AA, -1, axis=2)
                AS[:, :, 1] *= -1.
                X = np.cross(BB, AS, axis=1) / N[:, np.newaxis]

            elif ndof == 3:
                C = np.cross(np.roll(AA, -1, axis=2),
                             np.roll(AA, -2, axis=2), axis=1)
                N = dotpr(AA[:, :, 0], C[:, :, 0], axis=1)
                X = dotpr(BB, C, axis=1) / N[:, np.newaxis]

    else:
        X = np.stack([np.linalg.solve(A[i], B[i]) for i in range(nsys)])

    return X


def quadraticEquation(a, b, c):
    """Return roots of quadratic equation

    Parameters
    ----------
    a: float
        Coefficient of the second degree term.
    b: float
        Coefficient of the first degree term.
    c: float
        Constant in the third degree polynom.

    Returns
    -------
    r1: float
        First real root or real part of the complex conjugate roots.
    r2: float
        Second real root or imaginary part of the complex conjugate roots.
    kind: int
        A value specifying the nature and ordering of the roots:

        ======   ============================================================
         kind      roots
        ======   ============================================================
          0       two real roots r1 < r2
          1       two real roots r1 = r2
          2       two complex conjugate roots with real part r1 and
                  imaginary part r2; the complex roots are thus:
                  r1-i*r2 en r1+i*r2, where i=sqrt(-1).
        ======   ============================================================

    Examples
    --------
    >>> quadraticEquation(1,-3,2)
    (1.0, 2.0, 0)
    >>> quadraticEquation(1,3,2)
    (-2.0, -1.0, 0)
    >>> quadraticEquation(4,-4,1)
    (0.5, 0.5, 1)
    >>> quadraticEquation(1, -4, 13)
    (2.0, 3.0, 2)
    """
    if a == 0.0:
        raise ValueError("Coefficient a of quadratic equation should not be 0")

    b = b/a
    c = c/a
    b /= 2
    d = b*b - c
    if d > 0:
        kind = 0
        d = np.sqrt(d)
        if b >= 0:   # this ensures higher accuracy by avoiding subtraction
            bd = -(b + d)
            r1, r2 = bd, c / bd
        else:
            bd = -b + d
            r1, r2 = c / bd, bd
    elif d == 0:
        kind = 1
        r1 = r2 = -b
    else:
        kind = 2
        r1, r2 = -b, np.sqrt(-d)
    return r1, r2, kind


def cubicEquation(a, b, c, d):
    """Solve a cubic equation using a direct method.

    Given a polynomial equation of the third degree with real coefficients::

      a*x**3 + b*x**2 + c*x + d = 0

    Such an equation (with a non-zero) always has exactly three roots, with
    some possibly being complex, or identical.
    This function computes all three roots of the equation and returns full
    information about their nature, multiplicity and sorting order.
    It uses scaling of the variables to enhance the accuracy.

    Parameters
    ----------
    a: float
        Coefficient of the third degree term.
    b: float
        Coefficient of the second degree term.
    c: float
        Coefficient of the first degree term.
    d: float
        Constant in the third degree polynom.

    Returns
    -------
    r1: float
        First real root of the cubic equation
    r2: float
        Second real root of the cubic equation or real part of the
        complex conjugate second and third root.
    r3: float
        Third real root of the cubic equation or imaginary part of the
        complex conjugate second and third root.
    kind: int
        A value specifying the nature and ordering of the roots:

        ======   ============================================================
         kind      roots
        ======   ============================================================
          0       three real roots r1 < r2 < r3
          1       three real roots r1 < r2 = r3
          2       three real roots r1 = r2 < r3
          3       three real roots r1 = r2 = r3
          4       one real root r1 and two complex conjugate roots with real
                  part r2 and imaginary part r3; the complex roots are thus:
                  r2+i*r3 en r2-i*r3, where i=sqrt(-1).
        ======   ============================================================

    Raises
    ------
    ValueError:
        If the coefficient a==0 and the equation reduces to a second degree.

    Examples
    --------
    >>> cubicEquation(1.,-6.,11.,-6.)
    (array([1., 2., 3.]), 0)
    >>> cubicEquation(1.,-2.,1.,0.)
    (array([-0., 1., 1.]), 1)
    >>> cubicEquation(1.,-5.,8.,-4.)
    (array([1., 2., 2.]), 1)
    >>> cubicEquation(1.,-4.,5.,-2.)
    (array([1., 1., 2.]), 2)
    >>> cubicEquation(1.,-3.,3.,-1.)
    (array([1., 1., 1.]), 3)
    >>> cubicEquation(1.,-1.,1.,-1.)
    (array([1., 0., 1.]), 4)
    >>> cubicEquation(1.,-3.,4.,-2.)
    (array([1., 1., 1.]), 4)

    """
    if a == 0.0:
        raise ValueError("Coefficient a of cubic equation should not be 0")

    e3 = 1./3.
    pie = np.pi*2.*e3
    r = b/a
    s = c/a
    t = d/a

    # scale variable
    sc = max(abs(r), sqrt(abs(s)), abs(t)**e3)
    sc = 10**(int(np.log10(sc)))
    r = r/sc
    s = s/sc/sc
    t = t/sc/sc/sc
    gc = max(abs(r), abs(s), abs(t)) * 1.e-8

    rx = r*e3
    p3 = (s-r*rx)*e3
    q2 = rx**3-rx*s/2.+t/2.

    q2s = q2*q2
    p3c = p3**3
    som = q2s+p3c

    if abs(som) < gc:
        # two equal real roots
        ic = 1
        u = -q2
        r1 = np.sign(u) * abs(u)**e3
        r2 = -r1-rx
        r3 = r2
        r1 = r1+r1-rx
        if abs(r1-r2) < gc:
            ic = 3
        if r1 > r2:
            ic = 2
            r3, r1 = r1, r2
        roots = np.array([r1, r2, r3])

    elif som < 0.0:
        # 3 different roots
        ic = 0
        rt = sqrt(-p3c)
        roots = np.array([-rx] * 3)
        if abs(rt) > gc:
            phi = arccos(-q2/rt)*e3
            rt = 2.*sqrt(-p3)
            roots += rt*cos(phi + np.array([0., +pie, -pie]))

        # sort the 3 roots

        roots.sort()
        if roots[1] == roots[2]:
            ic += 1
        if roots[1] == roots[0]:
            ic += 2

    else:  # som > 0.0
        #  1 real and 2 complex conjugate roots
        ic = 4
        som = sqrt(som)
        u = -q2+som
        u = np.sign(u) * abs(u)**e3
        v = -q2-som
        v = np.sign(v) * abs(v)**e3
        r1 = u+v
        r2 = -r1/2-rx
        r3 = (u-v)*sqrt(3.)/2.
        r1 = r1-rx
        roots = np.array([r1, r2, r3])

    # scale and return values
    roots *= sc
    return roots, ic


###########################################################################
##
##   Operations on integer arrays
##
#########################


def renumberIndex(index, order='val'):
    """Renumber an index sequentially.

    Given a one-dimensional integer array with only non-negative values,
    and `nval` being the number of different values in it, and you want to
    replace its elements with values in the range `0..nval`, such that
    identical numbers are always replaced with the same number and the
    new values at their first occurrence form an increasing sequence `0..nval`.
    This function will give you the old numbers corresponding with each
    position `0..nval`.

    Parameters
    ----------
    index: 1-dim int :term:`array_like`
        Array with non-negative integer values.
    order: 'val' | 'pos'
        Determines

    Returns
    -------
    : int array
        A 1-dim int array with length equal to `nval`, where `nval`
        is the number of different values in `index`. The elements are
        the original values corresponding to the new values `0..nval`.

    See Also
    --------
    inverseUniqueIndex: get the inverse mapping.

    Examples
    --------
    >>> ind = [0,5,2,2,6,0]
    >>> old = renumberIndex(ind)
    >>> old
    array([0, 2, 5, 6])
    >>> new = inverseUniqueIndex(old)
    >>> new
    array([ 0, -1,  1, -1, -1,  2,  3])
    >>> new[ind]
    array([0, 2, 1, 1, 3, 0])
    >>> old = renumberIndex(ind, 'pos')
    >>> old
    array([0, 5, 2, 6])
    >>> new = inverseUniqueIndex(old)
    >>> new
    array([ 0, -1,  2, -1, -1,  1,  3])
    >>> new[ind]
    array([0, 1, 2, 2, 3, 0])
    """
    un, pos = np.unique(index, True)
    if order == 'pos':
        un = un[pos.argsort()]
    return un


def inverseUniqueIndex(index):
    """Inverse an index.

    Given a 1-D integer array with *unique* non-negative values, and
    `max` being the highest value in it, this function returns the position
    in the array of the values `0..max`. Values not occurring in input index
    get a value -1 in the inverse index.

    Parameters
    ----------
    index: 1-dim int :term:`array_like`
        Array with non-negative values, which all have to be unique.
        It's highest value is `max = index.max()`.

    Returns
    -------
    1-dim int array
        Array with length `max+1`, with the position in `index` of each
        of the values `0..max`, or -1 if the value does not occur in
        `index`.

    Note
    ----
    This is a low level function that does not check whether the input
    has indeed all unique values.

    The inverse index translates the unique index numbers in a
    sequential index, so that
    ``inverseUniqueIndex(index)[index] == np.arange(1+index.max())``.

    Examples
    --------
    >>> inverseUniqueIndex([0,5,2,6])
    array([ 0, -1, 2, -1, -1, 1, 3])
    >>> inverseUniqueIndex([0,5,2,6])[[0,5,2,6]]
    array([0, 1, 2, 3])

    """
    index = checkArray(index, ndim=1, kind='i')
    if np.unique(index).size != index.size:
        raise ValueError("The array does not contain unique values")
    inv = -np.ones(index.max()+1, dtype=index.dtype)
    inv[index] = np.arange(index.size, dtype=index.dtype)
    return inv


def renumberClusters(index, order='val'):
    """Renumber clusters of int values.

    This is like renumberIndex but returns the fully renumbered set
    of values.

    Examples
    --------
    >>> renumberClusters([2,6,3,2,6,0,3])
    array([1, 3, 2, 1, 3, 0, 2])
    """
    return inverseUniqueIndex(renumberIndex(index, order=order))[index]


def cumsum0(a):
    """Cumulative sum of a list of numbers preprended with a 0.

    Parameters
    ----------
    a: :term:`array_like`, int
        List of integers to compute the cumulative sum for.

    Returns
    -------
    : array, int
         Array with ``len(a)+1`` integers holding the cumulative sum of the
         integers from ``a`` with a 0 prepended.

    Examples
    --------
    >>> cumsum0([2,4,3])
    array([0, 2, 6, 9])
    >>> cumsum0(np.array([2,4,3]))
    array([0, 2, 6, 9])

    A common use case is when concatenating some blocks of different length.
    If the list `a` holds the length of each block, the cumsum0(a) holds
    the start and end of each block in the concatenation.

    >>> L = [[0,1], [2,3,4,5], [6], [7,8,9] ]
    >>> n = cumsum0([len(i) for i in L])
    >>> print(n)
    [ 0  2  6  7 10]
    >>> C = np.concatenate(L)
    >>> print(C)
    [0 1 2 3 4 5 6 7 8 9]
    >>> for i,j in zip(n[:-1],n[1:]):
    ...     print(f"{i}:{j} = {C[i:j]}")
    ...
    0:2 = [0 1]
    2:6 = [2 3 4 5]
    6:7 = [6]
    7:10 = [7 8 9]
    """
    return np.concatenate([[0], np.cumsum(a)])


def multiplicity(a):
    """Return the multiplicity of the numbers in an array.

    Parameters
    ----------
    a: :term:`array_like`, 1-dim
        The data array, will be flattened if it is not 1-dim.

    Returns
    -------
    mult: 1-dim int array
        The multiplicity of the unique values in a
    uniq: 1-dim array
        Array of same type as a, with the sorted list of unique values in a.

    Examples
    --------
    >>> multiplicity([0,1,4,3,1,4,3,4,3,3])
    (array([1, 2, 4, 3]), array([0, 1, 3, 4]))
    >>> multiplicity([[1.0, 0.0, 0.5],[0.2,0.5,1.0]])
    (array([1, 1, 2, 2]), array([0. , 0.2, 0.5, 1. ]))
    """
    a = checkArray1D(a)
    bins = np.unique(a)
    if bins.size > 0:
        mult, b = np.histogram(a, bins=np.concatenate([bins, [max(a)+1]]))
    else:
        mult = bins
    return mult, bins


def binsum(val, vbin, nbins=None):
    """Sum values in separate bins

    Parameters
    ----------
    val: 1-dim array_like (nval)
        The values to sum over the bins
    vbin: 1-dim int array_like (nval)
        The bin number to which each of the values has to be added.
        Bin numbers should not be negative.
    nbins: int, optional
        The number of bins. If not specified, it is set to vbin.max()+1.

    Returns
    -------
    array (nbins)
        The sums of the values dropped in the respective bins. The data
        type is the same as the input values.

    Examples
    --------
    >>> val = [1,2,3,4,5,6,7,8,9]
    >>> binsum(val, [0,1,2,3,4,3,2,1,0])
    array([10, 10, 10, 10, 5])
    >>> binsum(val, [0,1,0,3,4,3,0,1,0], nbins=6)
    array([20, 10, 0, 10, 5, 0])
    >>> binsum(np.arange(6)/3.,[0,0,0,1,1,1])
    array([1., 4.])
    """
    val = checkArray(val, ndim=1)
    vbin = checkArray(vbin, ndim=1, size=val.size)
    if nbins is None:
        nbins = vbin.max()+1
    return np.array([val[vbin == i].sum() for i in range(nbins)])


def complement(index, n=-1):
    """Return the complement of an index in a range(0,n).

    The complement is the list of numbers from the range(0,n) that are
    not included in the index.

    Parameters
    ----------
    index: 1-dim int or bool :term:`array_like`
        If integer, the array contains non-negative numbers in the range(0,n)
        and the return value will be the numbers in range(0,n) not included
        in index.
        If boolean, False value flag elements to be included (having a value
        True) in the output.
    n: int
        Upper limit for the range of numbers. If `index` is of
        type integer and `n` is not specified or is negative, it will be set
        equal to the largest number in `index` plus 1. If `index` is of type
        boolean and `n` is larger than the length of `index`, `index` will be
        padded with `False` values until length `n`.

    Returns
    -------
    : 1-dim array, type int or bool.
        The output array has the same dtype as the input.
        If `index` is integer: it is an array with the numbers from
        range(0,n) that are not included in `index`. If `index` is boolean,
        it is the negated input, padded to or cut at length `n`.

    Examples
    --------
    >>> print(complement([0,5,2,6]))
    [1 3 4]
    >>> print(complement([0,5,2,6],10))
    [1 3 4 7 8 9]
    >>> print(complement([False,True,True,True],6))
    [ True False False False  True  True]
    """
    index = np.asarray(index)
    if index.dtype == bool:
        m = index.shape[0]
        if n > m:
            comp = np.ones(n, dtype=bool)
            comp[:m] = ~index
        else:
            comp = ~index[:n]
    else:
        if n < 0:
            n = max(n, 1+index.max())
        comp = np.delete(np.arange(n), index)
    return comp


def sortByColumns(a):
    """Sort an array on all its columns, from left to right.

    The rows of a 2-dimensional array are sorted, first on the first
    column, then on the second to resolve ties, etc..

    Parameters
    ----------
    a: :term:`array_like`, 2-dim
        The array to be sorted

    Returns
    -------
    : int array, 1-dim
        Index specifying the order in which the rows have to
        be taken to obtain an array sorted by columns.

    Examples
    --------
    >>> sortByColumns([[1,2],[2,3],[3,2],[1,3],[2,3]])
    array([0, 3, 1, 4, 2])

    """
    a = checkArray(a, ndim=2)
    keys = [a[:, i] for i in range(a.shape[1]-1, -1, -1)]
    return np.lexsort(keys)


def minroll(a):
    """Roll a 1-D array to get the lowest values in front

    If the lowest value occurs more than once, the one with the
    lowest next value is choosen, etcetera.

    Parameters
    ----------
    a: array, 1-dim
        The array to roll

    Returns
    -------
    m: int
        The index of the element that should be put in front. This
        means that the ``np.roll(a,-m)`` gives the rolled array with
        the lowest elements in front.

    Examples
    --------
    >>> minroll([1,3,5,1,2,6])
    3
    >>> minroll([0,0,2,0,0,1])
    3
    >>> minroll([0,0,0,0,0,0])
    0
    """
    a = checkArray(a, ndim=1)
    m = np.argmin(a)
    w = where_1d(a==a[m])
    m = w[0]
    for k in w[1:]:
        d = np.roll(a, -m) - np.roll(a, -k)
        u = where_1d(d!=0)
        if len(u) > 0 and d[u[0]] > 0:
            m = k
    return m


def isroll(a, b):
    """Check that two 1-dim arrays can be rolled into eachother

    Parameters
    ----------
    a: array, 1-dim
        The first array
    b: array, 1-dim
        The second array, same length and dtype as a to be non-trivial.

    Returns
    -------
    m: int
        The number of positions (non-negative) that b has to be rolled
        to be equal to a, or -2 if the two arrays have a different length,
        or -1 if their elements are not the same or not in the same order.

    Examples
    --------
    >>> isroll(np.array([1,2,3,4]), np.array([2,3,4,1]))
    1
    >>> isroll(np.array([1,2,3,4]), np.array([2,3,1,4]))
    -1
    >>> isroll(np.array([1,2,3,4]), np.array([3,2,1,4]))
    -1
    >>> isroll(np.array([1,2,3,4]), np.array([1,2,3]))
    -2

    """
    a = np.asarray(a)
    b = np.asarray(b)
    if a.size != b.size:
        return -2

    for i in range(len(b)):
        if (a==np.roll(b, i)).all():
            return i

    return -1


def findEqualRows(a, permutations='', return_perm=False):
    """Find equal rows in a 2-dim array.

    Parameters
    ----------
    a: :term:`array_like`, 2-dim
        The array in which to find the equal rows.
    permutations: str
        Defines which permutations of the row data are allowed while still
        considering the rows equal. Possible values are:

        - 'roll': rolling is allowed. Rows that can be transformed into
          each other by rolling are considered equal;
        - 'all': any permutation of the same data will be considered an
          equal row.

        Any other value will not allow permutations: rows must match
        exactly, with the same data at the same positions. This is the default.
    return_perm: also returns an index identifying the permutation that
        was performed for each row.

    Returns
    -------
    ind: 1-dim int array
        A row index sorting the rows in such order that equal rows are grouped
        together.
    ok: 1-dim bool array
        An array flagging the rows in the order of ``index`` with True if
        it is the first row of a group of equal rows, or with False if the
        row is equal to the previous.
    perm: None, 1-dim or 2-dim int array
        The permutations that were done on the rows to obtain equal rows.
        For permutations='all', this is a 2-dim array with for every row
        the original positions of the elements of the sorted rows. For
        permutations='roll' it is the number of positions the array was
        rolled to be identical to the sorted row. If no permutations are
        allowed, a None is returned.

    Notes
    -----
    This function provides the functionality for detecting equal rows,
    but is seldomly used directly. There are wrapper functions providing more
    practical return values. See below.

    See Also
    --------
    equalRows: return the indices of the grouped equal rows
    uniqueRows: return the indices of the unique rows
    uniqueRowsIndex: like uniqueRows, but also returns index for all rows

    Examples
    --------
    >>> print(*findEqualRows([[1,2],[2,3],[3,2],[1,3],[2,3]]))
    [0 3 1 4 2] [ True  True  True False  True]
    >>> print(*findEqualRows([[1,2],[2,3],[3,2],[1,3],[2,3]],permutations='all'))
    [0 3 1 2 4] [ True  True  True False False]
    >>> print(*findEqualRows([[1,2,3],[3,2,1],[2,3,1],[1,2,3]]))
    [0 3 2 1] [ True False  True  True]
    >>> print(*findEqualRows([[1,2,3],[3,2,1],[2,3,1],[1,2,3]],permutations='all'))
    [0 1 2 3] [ True False False False]
    >>> print(*findEqualRows([[1,2,3],[3,2,1],[2,3,1],[1,2,3]],permutations='roll'))
    [0 2 3 1] [ True False False  True]
    """
    a = checkArray(a, ndim=2)
    if permutations == 'all':
        # Sort the rows
        perm = np.argsort(a, axis=1)
        a = np.take_along_axis(a, perm, 1)
    elif permutations == 'roll':
        # Roll the rows until smallest is in front
        perm = np.array([minroll(ai) for ai in a])
        a = a.copy()
        for i in range(a.shape[0]):
            a[i] = np.roll(a[i], -perm[i])
    else:
        perm = None
    ind = sortByColumns(a)  # groups the equal rows together
    a = a.take(ind, axis=0)
    ok = (a != np.roll(a, 1, axis=0)).any(axis=1)
    ok[0] = True
    if return_perm:
        return ind, ok, perm
    else:
        return ind, ok


def argNearestValue(values, target):
    """Return the index of the item nearest to target.

    Find in a list of floats the position of the value nearest to
    the target value.

    Parameters
    ----------
    values: list
        List of float values.
    target: float
        Target value to look up in list.

    Returns
    -------
    :int
        The index in `values` of the float value that is closest
        to `target`.

    See Also
    --------
    nearestValue

    Examples
    --------
    >>> argNearestValue([0.1,0.5,0.9],0.7)
    1
    """
    v = np.array(values).ravel()
    c = v - target
    return np.argmin(c*c)


def nearestValue(values, target):
    """Return the float nearest to target.

    Find in a list of floats the value that is closest to
    the target value.

    Parameters
    ----------
    values: list
        List of float values.
    target: float
        Target value to look up in list.

    Returns
    -------
    :float
        The value from the list that is closest to `target`.

    See Also
    --------
    argNearestValue

    Examples
    --------
    >>> nearestValue([0.1,0.5,0.9],0.7)
    0.5
    """
    return values[argNearestValue(values, target)]


def subsets(a):
    """Split an array of integers into subsets.

    The subsets of an integer array are sets of elements
    with the same value.

    Parameters
    ----------
    a: int :term:`array_like`, 1-dim
        Array with integer values to be split in subsets

    Returns
    -------
    val: array of ints
        The unique values in ``a``, sorted in increasing order.
    ind: :class:`varray.Varray`
        The Varray has the same number of rows as the number of values in
        ``ind``. Each row contains the indices in a of the elements with
        the corresponding value in ``val``.

    Examples
    --------
    >>> A = [0,1,4,3,1,4,3,4,3,3]
    >>> val,ind = subsets(A)
    >>> print(val)
    [0 1 3 4]
    >>> print(ind)
    Varray (nrows=4, width=1..4)
      [0]
      [1 4]
      [3 6 8 9]
      [2 5 7]
    <BLANKLINE>

    The inverse of ``ind`` can be used to restore A from val.

    >>> inv = ind.inverse().data
    >>> print(inv)
    [0 1 3 2 1 3 2 3 2 2]
    >>> (val[inv] == A).all()
    True
    """
    from .varray import Varray
    a = checkArray(a, ndim=1, kind='i')
    val = np.unique(a)
    ind = Varray([where_1d(a==v) for v in val])
    return val, ind


def sortSubsets(a, w=None):
    """Sort subsets of an integer array a.

    Subsets of an array are the sets of elements with equal values.
    By default the subsets are sorted according to decreasing number
    of elements in the set, or if a weight for each element is provided,
    according to decreasing sum of weights in the set.

    Parameters
    ----------
    a: 1-dim int :term:`array_like`
        Input array containing non-negative integer sets to be sorted.
    w: 1-dim int or float :term:`array_like`, optional
        If provided, it should have the same length as a. Each element of a
        will be attributed the corresponding weight.
        Specifying no weigth is equivalent to giving all elements the same
        weight.

    Returns
    -------
    : int array
        Array with same size as a, specifying for each element of a
        the index of its subset in the sorted list of subsets.

    Examples
    --------
    >>> sortSubsets([0,1,3,2,1,3,2,3,2,2])
    array([3, 2, 1, 0, 2, 1, 0, 1, 0, 0])
    >>> sortSubsets([0,1,4,3,1,4,3,4,3,3])
    array([3, 2, 1, 0, 2, 1, 0, 1, 0, 0])
    >>> sortSubsets([0,1,4,3,1,4,3,4,3,3],w=[9,8,7,6,5,4,3,2,1,0])
    array([3, 1, 0, 2, 1, 0, 2, 0, 2, 2])

    """
    a = checkArray(a, ndim=1, kind='i')
    # Make sure we have unique numbers
    a = inverseUniqueIndex(renumberIndex(a))[a]
    if w is None:
        h, u = multiplicity(a)
    else:
        w = checkArray(w, shape=a.shape, kind='f', allow='i')
        u = np.unique(a)
        h = [w[a==j].sum() for j in u]
    srt = np.argsort(h)[::-1]
    inv = inverseUniqueIndex(srt)
    return inv[a]


def collectOnLength(items, return_index=False):
    """Separate items in a list according to their length.

    The length of all items in the list are determined and
    the items are put in separate lists according to their length.

    Parameters
    ----------
    items: list
         A list of any items that can be accepted
         as parameter of the len() function.
    return_index: bool
         If True, also return an index with the positions of the equal
         length items in the original iterable.

    Returns
    -------
    col: dict
        A dict whose keys are the item lengths and values are lists of
        items with this length.
    ind: dict, optional
        A dict with the same keys as ``col``, and the values being a
        list of indices in the list where the corresponding item
        of ``col`` appeared.

    Examples
    --------
    >>> collectOnLength(['a','bc','defg','hi','j','kl'])
    {1: ['a', 'j'], 2: ['bc', 'hi', 'kl'], 4: ['defg']}
    >>> collectOnLength(['a','bc','defg','hi','j','kl'],return_index=True)[1]
    {1: [0, 4], 2: [1, 3, 5], 4: [2]}
    """
    val, ind = subsets([len(e) for e in items])
    col = {}
    index = {}
    for v, i in zip(val, ind):
        col[v] = [items[j] for j in i]
        if return_index:
            index[v] = i.tolist()
    if return_index:
        return col, index
    else:
        return col


def equalRows(a, permutations='none'):
    """Return equal rows in a 2-dim array.

    Parameters: see :meth:`findEqualRows`

    Returns
    -------
    V: :class:`varray.Varray`
        A Varray where each row contains a list of the row numbers
        from a that are considered equal. The entries in each row are
        sorted, but the order of the rows is indetermined.

    Notes
    -----
    The return Varray holds a lot of information:

    - ``V.col(0)`` gives the indices of the unique rows.
    - ``complement(V.col(0),len(a))`` gives the indices of duplicate rows.
    - ``V.col(0)[V.lengths==1]`` gives the indices of rows without duplicate.
    - ``Va.inverse().data`` gives an index into the unique
      rows for each of the rows of ``a``.

    See Also
    --------
    findEqualRows: sorts and detects equal rows
    uniqueRows: return the indices of the unique rows
    uniqueRowsIndex: like uniqueRows, but also returns index for all rows

    Examples
    --------
    >>> equalRows([[1,2],[2,3],[3,2],[1,3],[2,3]])
    Varray([[0], [3], [1, 4], [2]])
    >>> equalRows([[1,2],[2,3],[3,2],[1,3],[2,3]],permutations='all')
    Varray([[0], [3], [1, 2, 4]])
    >>> equalRows([[1,2,3],[3,2,1],[2,3,1],[1,2,3]])
    Varray([[0, 3], [2], [1]])
    >>> equalRows([[1,2,3],[3,2,1],[2,3,1],[1,2,3]],permutations='all')
    Varray([[0, 1, 2, 3]])
    >>> equalRows([[1,2,3],[3,2,1],[2,3,1],[1,2,3]],permutations='roll')
    Varray([[0, 2, 3], [1]])
    """
    from .varray import Varray
    ind, ok = findEqualRows(a, permutations=permutations)
    return Varray(ind, where_1d(ok))


def uniqueRows(a, permutations='none'):
    """Find the unique rows of a 2-D array.

    Parameters: see :meth:`findEqualRows`

    Returns
    -------
    uniq: 1-dim int array
        Contains the indices of the unique rows in `a`.

    See Also
    --------
    equalRows: return the indices of the grouped equal rows
    uniqueRowsIndex: like uniqueRows, but also returns index for all rows

    Examples
    --------
    >>> uniqueRows([[1,2],[2,3],[3,2],[1,3],[2,3]])
    array([0, 1, 2, 3])
    >>> uniqueRows([[1,2],[2,3],[3,2],[1,3],[2,3]],permutations='all')
    array([0, 1, 3])
    >>> uniqueRows([[1,2,3],[3,2,1],[2,3,1],[1,2,3]])
    array([0, 1, 2])
    >>> uniqueRows([[1,2,3],[3,2,1],[2,3,1],[1,2,3]],permutations='all')
    array([0])
    >>> uniqueRows([[1,2,3],[3,2,1],[2,3,1],[1,2,3]],permutations='roll')
    array([0, 1])
    >>> uniqueRows([[1,2,3],[3,2,1],[2,3,1],[1,2,3]])
    array([0, 1, 2])

    """
    ind, ok = findEqualRows(a, permutations=permutations)
    return np.sort(ind[ok])


def uniqueRowsIndex(a, permutations='none'):
    """Return the unique rows of a 2-D array and an index for all rows.

    Parameters
    ----------
    a: :term:`array_like`, 2-dim
        Array from which to find the unique rows.
    permutations: bool
         If True, rows which are permutations of the same data are considered
        equal. The default is to consider permutations as different.
    roll: bool
        If True, rows which can be rolled into the same contents are
        considered equal.

    Returns
    -------
    uniq: 1-dim int array
        Contains the indices of the unique rows in `a`.
        The order of the elements in `uniq` is determined by the sorting
        procedure: in the current implementation this is :func:`sortByColumns`.
        If `permutations==True`, `a` is sorted along its last axis -1 before
        calling this sorting function. If `roll=True`, the rows of ``a``
        are rolled to put the lowest values at the front.
    ind: 1-dim int array
        For each row of `a`, holds the index in `uniq` where the row with
        the same data is found.

    See Also
    --------
    equalRows: return the indices of the grouped equal rows
    uniqueRows: return the indices of the unique rows

    Examples
    --------
    >>> print(*uniqueRowsIndex([[1,2],[2,3],[3,2],[1,3],[2,3]]))
    [0 3 1 2] [0 2 3 1 2]

    >>> print(*uniqueRowsIndex([[1,2],[2,3],[3,2],[1,3],[2,3]],permutations='all'))
    [0 3 1] [0 2 2 1 2]
    >>> print(*uniqueRowsIndex([[1,2,3],[3,2,1],[2,3,1],[1,2,3]]))
    [0 2 1] [0 2 1 0]
    >>> print(*uniqueRowsIndex([[1,2,3],[3,2,1],[2,3,1],[1,2,3]],permutations='all'))
    [0] [0 0 0 0]
    >>> print(*uniqueRowsIndex([[1,2,3],[3,2,1],[2,3,1],[1,2,3]],permutations='roll'))
    [0 1] [0 1 0 0]

    """
    Va = equalRows(a, permutations=permutations)
    return Va.col(0), Va.inverse().data


def inverseIndex(a, sort=True):
    """Create the inverse of a 2D-index array.

    A 2D-index array is a 2D integer array where only the nonnegative values.
    are relevant. Negative values are flagging a non-existent element. This
    allows for rows with different number of entries.
    While in most practical cases all (non-negative) values in a row are
    unique, this is not a requirement.

    Parameters
    ----------
    a: :term:`varray_like`.
        The input index table. This can be anything that is acceptable as
        data for the Varray constructor.
    sort: bool.
        If True, the values on each row of the returned index are sorted.
        The default (False) will leave the values in the order obtained
        by the algorithm, which depends on Python/numpy sorting.

    Returns
    -------
    inv: :class:`numpy.ndarray`
        The inverse index as an array. Each row ``i`` of the inverse index
        contains the numbers of the rows of the input in which a value ``i``
        appeared, and padded with -1 values to make all rows equal length.
        With ``sort=True``, the values on each row are guaranteed to be sorted.

    See also
    --------
    Varray.inverse   Return the inverse as a Varray

    Note
    ----
    If the same value occurs multiple times on the same row of the input,
    the inverse index will also contain repeated row numbers for that value.

    Examples
    --------
    >>> A = np.array([[0,1],[0,2],[1,2],[0,3]])
    >>> print(A)
    [[0 1]
     [0 2]
     [1 2]
     [0 3]]
    >>> inv = inverseIndex(A)
    >>> print(inv)
    [[ 0  1  3]
     [-1  0  2]
     [-1  1  2]
     [-1 -1  3]]

    The inverse of the inverse returns the original:

    >>> (inverseIndex(inv) == A).all()
    True
    """
    from .varray import Varray
    return Varray(a).inverse(sort=sort).toArray()


def findFirst(target, values):
    """Find first position of values in target.

    Find the first position in the array `target` of all the elements
    in the array `values`.

    Parameters
    ----------
    target: 1-dim int array
        Integer array with all non-negative values. If not 1-dim, it
        will be flattened.
    values: 1-dim int array
        Array with values to look up in target. If not 1-dim, it
        will be flattened.

    Returns
    -------
    : int array
        Array with same size as `values`. For each element in `values`,
        the return array contains the position of that value
        in the flattened `target`, or -1 if that number does not occur
        in `target`.
        If an element from `values` occurs more than once in `target`, it is
        currently undefined which of those positions is returned.

    Note
    ----
    After ``m = findIndex(target,values)`` the equality
    ``target[m] == values`` holds for all the non-negative positions of `m`.

    Examples
    --------
    >>> A = np.array([1,3,4,5,7,3,8,9])
    >>> B = np.array([0,7,-1,1,3])
    >>> ind = findFirst(A,B)
    >>> print(ind)
    [-1  4 -1  0  1]
    >>> (A[ind[ind>=0]] == B[ind>=0]).all()
    True
    """
    from .varray import Varray
    target = checkArray1D(target, kind='i', allow='u').reshape(-1, 1)
    values = checkArray1D(values, kind='i', allow='u')
    inv = Varray(target).inverse(sort=True)
    return np.array([inv[i][0]
                     if i >= 0 and i < inv.nrows and len(inv[i]) > 0 else -1
                     for i in values])


def matchLine2(edges, edges1):
    """Match Line elems in a given Connectivity.

    Find the rows in edges that have the same nodes as the rows of edges1.

    Parameters
    ----------
    edges: int :term:`array_like`
        An int array (nedges,2), e.g. a Line2 :class:`Connectivity`.
    edges1: int :term:`array_like`
        An int array (nedges1,2), e.g. a Line2 :class:`Connectivity`.

    Returns
    -------
    int array
        An int array (nedges1,) specifying for each row of edges1 which row
        of edges contains the same two nodes (in any order). Rows that do
        not occur in edges get a value -1. If multiple rows are matching,
        the first one is returned.
    """
    e = np.sort(edges, axis=-1)
    e1 = np.sort(edges1, axis=-1)
    maxv = max(e.max(), e1.max()) + 1
    e = maxv*e[:, 0] + e[:, 1]
    e1 = maxv*e1[:, 0] + e1[:, 1]
    return findFirst(e, e1)


def findAll(target, values):
    """Find all locations of values in target.

    Find the position in the array `target` of all occurrences of
    the elements in the array `values`.

    Parameters
    ----------
    target: 1-dim int array
        Integer array with all non-negative values. If not 1-dim, it
        will be flattened.
    values: 1-dim int array
        Array with values to look up in target. If not 1-dim, it
        will be flattened.

    Returns
    -------
    : list of int arrays.
        For each element in values, an array is returned with the indices
        in target of the elements with the same value.

    See Also
    --------
    findFirst

    Examples
    --------
    >>> gid = np.array([2, 1, 1, 6, 6, 1 ])
    >>> values = np.array([1, 2, 6 ])
    >>> print(findAll(gid,values))
    [array([1, 2, 5]), array([0]), array([3, 4])]
    """
    return [where_1d(target==i) for i in values]


def groupArgmin(val, gid):
    """Compute the group minimum.

    Computes the minimum value per group of a set of values tagged with
    a group number.

    Parameters
    ----------
    val: 1-dim array
        Data values
    gid: 1-dim int :term:`array_like`
        Array with same length as val, containing the group identifiers.

    Returns
    -------
    ugid: 1-dim int array
        (ngrp,) shaped array with unique group identifiers.
    minpos: 1-dim int array
        (ngrp,) shaped array giving the position in `val` of the minimum
        of all values with the corresponding group identifier in `ugid`.
        The minimum values corresponding to the groups in `ugid` can be
        obtained with ``val[minpos]``.

    Examples
    --------
    >>> val = np.array([0.0, 1.0, 2.0, 3.0, 4.0, -5.0 ])
    >>> gid = np.array([2, 1, 1, 6, 6, 1 ])
    >>> print(groupArgmin(val,gid))
    (array([1, 2, 6]), array([5, 0, 3]))
    """
    ugid = np.unique(gid)
    pos = findAll(gid, ugid)
    minid = np.hstack([val[ind].argmin() for ind in pos])
    minpos = np.hstack([ind[k] for ind, k in zip(pos, minid)])
    return ugid, minpos


def collectRowsByColumnValue(a, col):
    """Collects rows of a 2D array by common value in a specified column.

    Parameters
    ----------
    a: 2-dim :term:`array_like`
        Any 2-dim array.
    col: int
        Column number on which values to collect the rows.

    Returns
    -------
    dict
        A dict where the keys are the unique values of the specified
        column of the array `a`. The values are int arrays with the
        indices of the rows that have the key value in their `col`
        column.

    Examples
    --------
    >>> a = np.array([[0,0], [1,1], [1,0], [0,1], [4,0]])
    >>> print(a)
    [[0 0]
     [1 1]
     [1 0]
     [0 1]
     [4 0]]
    >>> d = collectRowsByColumnValue(a,0)
    >>> print(d)
    {0: array([0, 3]), 1: array([1, 2]), 4: array([4])}
    >>> d = collectRowsByColumnValue(a,1)
    >>> print(d)
    {0: array([0, 2, 4]), 1: array([1, 3])}
    """
    edgset = np.unique(a[:, col])
    d = {}
    for e in edgset:
        d[e] = where_1d(a[:, col]==e)
    return d


###########################################################
# Working with sets of vectors
###########################

def vectorPairAreaNormals(vec1, vec2):
    """Compute area of and normals on parallellograms formed by vec1 and vec2.

    Parameters
    ----------
    vec1: (3,) or (n,3) shaped float :term:`array_like`
        Array with 1 or n vectors in 3D space.
    vec2: (3,) or (n,3) shaped float :term:`array_like`
        Array with 1 or n vectors in 3D space.

    Returns
    -------
    area: (n,) shaped float array
        The area of the parallellograms formed by the vectors vec1 and vec2.
    normal: (n,3) shaped float array
        The unit length vectors normal to each vector pair (vec1,vec2).

    Note
    ----
    This first computes the cross product of vec1 and vec2, which is a normal
    vector with length equal to the area. Then :func:`normalize` produces
    the required results.

    Note that where two vectors are parallel, an area zero results and
    an axis with components NaN.

    See Also
    --------
    vectorPairNormals: only returns the normal vectors
    vectorPairArea: only returns the area

    Examples
    --------
    >>> a = np.array([[3.,4,0],[1,0,0],[1,-2,1]])
    >>> b = np.array([[1.,3.,0],[1,0,1],[-2,4,-2]])
    >>> l,v = vectorPairAreaNormals(a,b)
    >>> print(l)
    [5. 1. 0.]
    >>> print(v)
    [[ 0.  0.  1.]
     [ 0. -1.  0.]
     [nan nan nan]]
    """
    vec1 = checkArray(vec1, kind='f', allow='i')
    vec2 = checkArray(vec2, kind='f', allow='i')
    normal = np.cross(vec1.reshape(-1, 3), vec2.reshape(-1, 3))
    return normalize(normal, return_length=True)[::-1]


def vectorPairNormals(vec1, vec2):
    """Create unit vectors normal to vec1 and vec2.

    Parameters
    ----------
    vec1: (3,) or (n,3) shaped float :term:`array_like`
        Array with 1 or n vectors in 3D space.
    vec2: (3,) or (n,3) shaped float :term:`array_like`
        Array with 1 or n vectors in 3D space.

    Returns
    -------
    normal: (n,3) shaped float array
        The unit length vectors normal to each vector pair (vec1,vec2).

    See Also
    --------
    vectorPairAreaNormals: returns the normals and the area between vectors
    vectorPairArea: only returns the area between vectors

    Examples
    --------
    >>> a = np.array([[3.,4,0],[1,0,0],[1,-2,1]])
    >>> b = np.array([[1.,3.,0],[1,0,1],[-2,4,-2]])
    >>> v = vectorPairNormals(a,b)
    >>> print(v)
    [[ 0.  0.  1.]
     [ 0. -1.  0.]
     [nan nan nan]]
    """
    return vectorPairAreaNormals(vec1, vec2)[1]


def vectorPairArea(vec1, vec2):
    """Compute area of the parallellogram formed by a vector pair vec1,vec2.

    Parameters
    ----------
    vec1: (3,) or (n,3) shaped float :term:`array_like`
        Array with 1 or n vectors in 3D space.
    vec2: (3,) or (n,3) shaped float :term:`array_like`
        Array with 1 or n vectors in 3D space.

    Returns
    -------
    area: (n,) shaped float array
        The area of the parallellograms formed by the vectors vec1 and vec2.

    See Also
    --------
    vectorPairAreaNormals: returns the normals and the area between vectors
    vectorPairNormals: only returns the normal vectors

    Examples
    --------
    >>> a = np.array([[3.,4,0],[1,0,0],[1,-2,1]])
    >>> b = np.array([[1.,3.,0],[1,0,1],[-2,4,-2]])
    >>> l = vectorPairArea(a,b)
    >>> print(l)
    [5. 1. 0.]
    """
    vec1 = checkArray(vec1, kind='f', allow='i')
    vec2 = checkArray(vec2, kind='f', allow='i')
    normal = np.cross(vec1.reshape(-1, 3), vec2.reshape(-1, 3))
    return length(normal)


def vectorPairCosAngle(vec1, vec2):
    """Return the cosinus of the angle between the vectors v1 and v2.

    Parameters
    ----------
    vec1: (3,) or (n,3) shaped float :term:`array_like`
        Array with 1 or n vectors in 3D space.
    vec2: (3,) or (n,3) shaped float :term:`array_like`
        Array with 1 or n vectors in 3D space.

    Returns
    -------
    cosa: (n,) shaped float array
        The cosinus of the angles formed by the vectors vec1 and vec2

    See Also
    --------
    vectorPairAngle: returns the angle between the vectors
    """
    vec1 = np.asarray(vec1)
    vec2 = np.asarray(vec2)
    cos = dotpr(vec1, vec2) / sqrt(dotpr(vec1, vec1)*dotpr(vec2, vec2))
    # clip to [-1.,1.] in case of rounding errors
    return cos.clip(min=-1., max=1.)


def vectorPairAngle(vec1, vec2, angle_spec=DEG):
    """Return the angle (in radians) between the vectors vec1 and vec2.

    Parameters
    ----------
    vec1: (3,) or (n,3) shaped float :term:`array_like`
        Array with 1 or n vectors in 3D space.
    vec2: (3,) or (n,3) shaped float :term:`array_like`
        Array with 1 or n vectors in 3D space.
    angle_spec: :py:attr:`DEG`, :py:attr:`RAD` or float, nonzero.
        Divisor applied to the resulting angles before returning.
        The default divisor DEG makes the angles be returned in
        degrees. Use RAD to get angles in radians.

    Returns
    -------
    angle: (n,) shaped float array
        The angles formed by the vectors vec1 and vec2, by default in degrees.

    See Also
    --------
    vectorPairCosAngle: returns the cosinus of angle between the vectors

    Examples
    --------
    >>> vectorPairAngle([1,0,0],[0,1,0])
    90.0
    >>> vectorPairAngle([[1,0,0],[0,1,0]],[[1,1,0],[1,1,1]])
    array([45.    , 54.7356])
    """
    return np.arccos(vectorPairCosAngle(vec1, vec2)) / angle_spec


def vectorTripleProduct(vec1, vec2, vec3):
    """Compute triple product vec1 . (vec2 x vec3).

    Parameters
    ----------
    (vec1, vec2, vec3): three (3,) or (n,3) shaped float :term:`array_like`
        Three arrays with same shape holding 1 or n vectors in 3D space.

    Returns
    -------
    : (n,) shaped float array
        The triple product of each set of corresponding vectors from
        vec1, vec2, vec3.

    Note
    ----
    The triple product is the dot product of the first vector(s) and
    the normal(s) on the second and third vector(s).
    This is also twice the volume of the parallellepid formed by
    the 3 vectors.

    If vec1 has a unit length, the result is also the area of the parallellogram
    (vec2,vec3) projected in the direction vec1.

    This is functionally equivalent with `dotpr(vec1, np.cross(vec2, vec3))`
    but is implemented in a more efficient way, using the determinant formula.

    Examples
    --------
    >>> vectorTripleProduct([[1.,0.,0.],[2.,0.,0.]],
    ...                     [[1.,1.,0.],[2.,2.,0.]],
    ...                     [[1.,1.,1.],[2.,2.,2.]])
    array([1., 8.])
    """
    vec1 = np.asarray(vec1)
    vec2 = np.asarray(vec2)
    vec3 = np.asarray(vec3)
    a11 = vec1[..., 0]
    a12 = vec1[..., 1]
    a13 = vec1[..., 2]
    a21 = vec2[..., 0]
    a22 = vec2[..., 1]
    a23 = vec2[..., 2]
    a31 = vec3[..., 0]
    a32 = vec3[..., 1]
    a33 = vec3[..., 2]
    return a11*(a22*a33-a32*a23) + a12*(a23*a31-a33*a21) + a13*(a21*a32-a22*a31)


def det2(a):
    """Compute the determinant of 2x2 matrices.

    Parameters
    ----------
    a: int or float :term:`array_like` (...,2,2)
        Array containing one or more (2,2) square matrices.

    Returns
    -------
    : int or float number or array(...)
         The determinant(s) of the matrices. The result has the same type
         as the input array.

    Note
    ----
    This method is faster than the generic numpy.linalg.det.

    See Also
    --------
    det3: determinant of (3,3) matrices
    det4: determinant of (4,4) matrices
    numpy.linalg.det: determinant of any size matrix

    Examples
    --------
    >>> det2([[1,2],[2,1]])
    -3
    >>> det2([[[1,2],[2,1]],[[4,2],[1,3]]])
    array([-3, 10])

    """
    a = np.asarray(a)
    a11 = a[..., 0, 0]
    a12 = a[..., 0, 1]
    a21 = a[..., 1, 0]
    a22 = a[..., 1, 1]
    return a11*a22 - a12*a21


def det3(a):
    """Compute the determinant of 3x3 matrices.

    Parameters
    ----------
    a: int or float :term:`array_like` (...,3,3)
        Array containing one or more (3,3) square matrices.

    Returns
    -------
    : int or float number or array(...)
         The determinant(s) of the matrices. The result has the same type
         as the input array.

    Note
    ----
    This method is faster than the generic numpy.linalg.det.

    See Also
    --------
    det2: determinant of (2,2) matrices
    det4: determinant of (4,4) matrices
    numpy.linalg.det: determinant of any size matrix

    Examples
    --------
    >>> det3([[1,2,3],[2,2,2],[3,2,1]])
    0
    >>> det3([[[1.,0.,0.],[1.,1.,0.],[1.,1.,1.]],
    ...       [[2.,0.,0.],[2.,2.,0.],[2.,2.,2.]]])
    array([1., 8.])
    """
    a = np.asarray(a)
    return vectorTripleProduct(a[..., 0, :], a[..., 1, :], a[..., 2, :])


def det4(a):
    """Compute the determinant of 4x4 matrices.

    Parameters
    ----------
    a: int or float :term:`array_like` (...,4,4)
        Array containing one or more (4,4) square matrices.

    Returns
    -------
    : int or float number or array(...)
         The determinant(s) of the matrices. The result has the same type
         as the input array.

    Note
    ----
    This method is faster than the generic numpy.linalg.det.

    See Also
    --------
    det2: determinant of (2,2) matrices
    det3: determinant of (3,3) matrices
    numpy.linalg.det: determinant of any size matrix

    Examples
    --------
    >>> det4([[[1.,0.,0.,0.],[1.,1.,0.,0.],[1.,1.,1.,0.],[1.,1.,1.,1.]],
    ...       [[2.,0.,0.,0.],[2.,2.,0.,0.],[2.,2.,2.,0.],[2.,2.,2.,2.]]])
    array([ 1., 16.])
    """
    a = np.asarray(a)
    a00 = a[..., 0, 0]
    a01 = a[..., 0, 1]
    a02 = a[..., 0, 2]
    a03 = a[..., 0, 3]
    m00 = det3(a[..., 1:, [1, 2, 3]])
    m01 = det3(a[..., 1:, [0, 2, 3]])
    m02 = det3(a[..., 1:, [0, 1, 3]])
    m03 = det3(a[..., 1:, [0, 1, 2]])
    return a00*m00 - a01*m01 + a02*m02 - a03*m03


def percentile(values, perc=[25., 50., 75.], wts=None):
    """Return percentiles of a set of values.

    A percentiles is the value such that at least a given percent of the
    values is lower or equal than the value.

    Parameters
    ----------
    values: 1-dim int or float :term:`array_like`
        The set of values for which to compute the percentiles.
    perc: 1-dim int or float :term:`array_like`
        One or multiple percentile values to compute. All values should be
        in the range [0,100]. By default, the quartiles are computed.
    wts: 1-dim array
        Array with same shape as values and all positive values. These are
        weights to be assigned to the values.

    Returns
    -------
    : 1-dim float array
        Array with the percentile value(s) that is/are greater or equal than
        `perc` percent of `values`. If the result lies between two items of
        `values`, it is obtained by interpolation.

    Examples
    --------
    >>> percentile(np.arange(100),[10,50,90])
    array([ 9., 49., 89.])
    >>> percentile([1,1,1,1,1,2,2,2,3,5])
    array([1., 1., 2.])

    """
    values = checkArray1D(values)
    perc = checkArray1D(perc)
    if perc.min() < 0. or perc.max() > 100.:
        raise ValueError(f"Percentiles should be between 0 and 100, got {perc}")
    if wts is not None and wts.min() <= 0.:
        raise ValueError(f"Weights should be positive, got {wts.min()}")
    ind = values.argsort()
    values = values[ind]
    if wts is None:
        wts = np.resize(1., values.shape)
    else:
        wts = wts[ind]
    wts = wts.cumsum()
    w = perc /100. * (wts[-1])
    ind = wts.searchsorted(w)
    val = np.where(ind>0,
                   values[ind-1] + (w-wts[ind-1]) / (wts[ind]-wts[ind-1])
                   * (values[ind]-values[ind-1]),
                   values[0])
    return val


# TODO: this should probably be removed or replaced
# with np.bin and np.bincount
# maybe keeping the right limit extension
def histogram2(a, bins, range=None):
    """Compute the histogram of a set of data.

    This is similar to the numpy histogram function, but also returns
    the bin index for each individual entry in the data set.

    Parameters
    ----------
    a: :term:`array_like`
        Input data. The histogram is computed over the flattened array.
    bins: int or sequence of scalars.
        If `bins` is an int, it defines the number of equal-width bins
        in the given range (nbins).
        If `bins` is a sequence, it defines the bin edges, including the
        rightmost edge, allowing for non-uniform bin widths. The number of
        bins (nbins) is then equal to `len(bins) - 1`.
        A value `v` will be sorted in bin `i` if
        `bins[i] <= v < bins[i+1]`, except for the last bin, which will also
        contain the values equal to the right bin edge.
    range`: (float, float), optional.
        The lower and upper range of the bins.
        If not provided, range is simply (a.min(), a.max()). Values outside the
        range are ignored. This parameter is ignored if bins is a sequence.

    Returns
    -------
    hist: int array
        The number of elements from `a` sorted in each of the bins.
    ind: list of ``nbins`` int arrays
        Each array holds the indices the elements sorted in the
        corresponding bin.
    bin_edges: float array
        The array contains the ``len(hist)+1`` bin edges.

    Example
    -------
    >>> hist, ind, bins = histogram2([1,2,3,4,3,2,3,1],[1,2,3,4,5])
    >>> print(hist)
    [2 2 3 1]
    >>> print(ind)
    Varray (nrows=4, width=1..3)
      [0 7]
      [1 5]
      [2 4 6]
      [3]
    >>> print(bins)
    [1 2 3 4 5]
    >>> hist, bins = np.histogram([[1,2,3,4],[3,2,3,1]],5)
    >>> print(hist)
    [2 2 0 3 1]
    >>> print(bins)
    [1.  1.6 2.2 2.8 3.4 4. ]
    >>> hist, ind, bins = histogram2([1,2,3,4,3,2,3,1],5)
    >>> print(hist)
    [2 2 0 3 1]
    >>> print(bins)
    [1.  1.6 2.2 2.8 3.4 4. ]
    >>> print(ind)
    Varray (nrows=5, width=0..3)
      [0 7]
      [1 5]
      []
      [2 4 6]
      [3]
    """
    from .varray import Varray
    a = np.asarray(a)
    bins = np.histogram_bin_edges(a, bins, range)
    bins[-1] = np.nextafter(bins[-1], bins[-1]+0.5)
    d = np.digitize(a, bins)
    ind = Varray([where_1d(d==i) for i in np.arange(1, len(bins))])
    hist = ind.lengths
    return hist, ind, bins


def movingView(a, size):
    """Create a moving view along the first axis of an array.

    A moving view of an array is a view stacking a sequence of subarrays
    with fixed size along the 0 axis of the array, where each next subarray
    shifts one position down along the 0 axis.

    Parameters
    ----------
    a: :term:`array_like`
        Array for which to create a moving view.
    size : int
        Size of the moving view: this is the number of rows to include
        in the subarray.

    Returns
    -------
    : view of the array ``a``
        The view of the original array has an extra first axis with length
        ``1 + a.shape[0] - size``, a second axis with length ``size``, and
        the remaining axes have the same length as those in ``a``.

    Note
    ----
    While this function limits the moving view to the direction of the 0 axis,
    using swapaxes(0,axis) allows to create moving views over any axis.

    See Also
    --------
    movingAverage: compute moving average values along axis 0

    Examples
    --------
    >>> x=np.arange(10).reshape((5,2))
    >>> print(x)
    [[0 1]
     [2 3]
     [4 5]
     [6 7]
     [8 9]]
    >>> print(movingView(x, 3))
    [[[0 1]
      [2 3]
      [4 5]]
    <BLANKLINE>
     [[2 3]
      [4 5]
      [6 7]]
    <BLANKLINE>
     [[4 5]
      [6 7]
      [8 9]]]

    Calculate rolling sum of first axis:

    >>> print(movingView(x, 3).sum(axis=0))
    [[ 6  9]
     [12 15]
     [18 21]]

    """
    if size < 1:
        raise ValueError("`size` must be at least 1.")
    if size > a.shape[0]:
        raise ValueError("`size` is too long.")
    shape = (size, a.shape[0] - size + 1) + a.shape[1:]
    strides = (a.strides[0],) + a.strides
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)


def movingAverage(a, n, m0=None, m1=None):
    """Compute the moving average along the first axis of an array.

    Parameters
    ----------
    a: :term:`array_like`
        The array to be averaged.
    n: int
        Sample length along axis 0 over which to compute the average.
    m0: int, optional
        If provided, the first data row of ``a`` will be prepended to ``a``
        this number of times.
    m1 : int, optional
        If provided, the last data row of ``a`` will  be appended to ``a``
        this number of times.

    Returns
    -------
    : float array
        Array containing the moving average over data sets of length ``n``
        along the first axis of ``a``.
        The array has a shape like ``a`` except for its first axis,
        which may have a different length.
        If neither m0 nor m1 are set, the first axis will have a length of
        1 + a.shape[0] - n.
        If both m0 and m1 are given, the first axis will have a length of
        1 + a.shape[0] - n + m0 + m1.
        If either m0 or m1 are set and the other not, the missing value m0
        or m1 will be computed thus that the return array has a first axis
        with length a.shape[0].

    Examples
    --------
    >>> x=np.arange(10).reshape((5,2))
    >>> print(x)
    [[0 1]
     [2 3]
     [4 5]
     [6 7]
     [8 9]]
    >>> print(movingAverage(x,3))
    [[2. 3.]
     [4. 5.]
     [6. 7.]]
    >>> print(movingAverage(x,3,2))
    [[0.     1.    ]
     [0.6667 1.6667]
     [2.     3.    ]
     [4.     5.    ]
     [6.     7.    ]]
    """
    if m0 is None and m1 is None:
        ae = a
    else:
        if m0 is None:
            m0 = n-1 - m1
        elif m1 is None:
            m1 = n-1 - m0
        if m0 < 0 or m1 < 0:
            raise ValueError("Invalid value a m0 or m1")
        ae = [a[:1]] * m0 + [a] + [a[-1:]] * m1
        ae = np.concatenate(ae, axis=0)
    return movingView(ae, n).mean(axis=0)


def randomNoise(shape, min=0.0, max=1.0):
    """Create an array with random float values between min and max

    Parameters
    ----------
    shape: tuple of ints
        Shape of the array to create.
    min: float
        Minimum value of the random numbers.
    max: float
        Maximum value of the random numbers.

    Returns
    -------
    : float array
        An array of the requested shape filled with random numbers
        in the specified range.

    Examples
    --------
    >>> x = randomNoise((3,4))
    >>> x.shape == (3,4)
    True
    >>> (x >= 0.0).all()
    True
    >>> (x <= 1.0).all()
    True
    """
    return np.random.random(shape) * (max-min) + min


def stuur(x, xval, yval, exp=2.5):
    """Returns a (non)linear response on the input x.

    xval and yval should be lists of 3 values:
    ``[xmin,x0,xmax], [ymin,y0,ymax]``.
    Together with the exponent exp, they define the response curve
    as function of x. With an exponent > 0, the variation will be
    slow in the neighbourhood of (x0,y0).
    For values x < xmin or x > xmax, the limit value ymin or ymax
    is returned.

    Examples
    --------
    >>> x = unitDivisor(4)
    >>> x
    array([0.  , 0.25, 0.5 , 0.75, 1.  ])
    >>> np.array([stuur(xi, (0.,0.5,1.0), (0.,0.5,1.0) ) for xi in x])
    array([0.    , 0.4116, 0.5   , 0.5884, 1.    ])
    """
    xmin, x0, xmax = xval
    ymin, y0, ymax = yval
    if x < xmin:
        return ymin
    elif x < x0:
        xr = float(x-x0) / (xmin-x0)
        return y0 + (ymin-y0) * xr**exp
    elif x < xmax:
        xr = float(x-x0) / (xmax-x0)
        return y0 + (ymax-y0) * xr**exp
    else:
        return ymax


def unitDivisor(div):
    """Divide a unit interval in equal parts.

    This function is intended to be used by interpolation functions
    that accept an input as either an int or a list of floats.

    Parameters
    ----------
    div: int, or list of floats in the range [0.0, 1.0].
        If it is an integer, it specifies the number of equal sized parts
        in which the interval [0.0, 1.0] is to be divided.
        If a list of floats, its values should be monotonically increasing
        from 0.0 to 1.0. The values are returned unchanged.

    Returns
    -------
    : 1-dim float array
        The float values that border the parts of the interval.
        If `div` is a an integer, returns the floating point values
    dividing the unit interval in div equal parts. If `div` is a list,
    just returns `div` as a 1D array.

    Examples
    --------
    >>> unitDivisor(4)
    array([0.  , 0.25, 0.5 , 0.75, 1.  ])
    >>> unitDivisor([0., 0.3, 0.7, 1.0])
    array([0. , 0.3, 0.7, 1. ])
    """
    if isInt(div):
        div = np.linspace(0., 1., div+1, dtype=Float)
    else:
        div = checkArray1D(div, kind='f', allow='i')
    return div


def uniformParamValues(n, umin=0.0, umax=1.0):
    """Create a set of uniformly distributed parameter values in a range.

    Parameters
    ----------
    n: int
        Number of intervals in which the range should be divided.
        The number of values returned is ``n+1``.
    umin: float
        Starting value of the interval.
    umax: float
        Ending value of the interval.

    Returns
    -------
    : 1-dim float array
        The array contains n+1 equidistant values in the range [umin, umax].
        For n > 0, both of the endpoints are included. For n=0, a single
        value at the center of the interval will be returned. For n<0, an
        empty array is returned.

    Examples
    --------
    >>> uniformParamValues(4).tolist()
    [0.0, 0.25, 0.5, 0.75, 1.0]
    >>> uniformParamValues(0).tolist()
    [0.5]
    >>> uniformParamValues(-1).tolist()
    []
    >>> uniformParamValues(2,1.5,2.5).tolist()
    [1.5, 2.0, 2.5]
    """
    if n == 0:
        return np.array([0.5*(umax+umin)])
    else:
        return umin + np.arange(n+1) * (umax-umin) / float(n)


def unitAttractor(x, e0=0., e1=0.):
    """Moves values in the range 0..1 closer to or away from the limits.

    Parameters
    ----------
    x: float :term:`array_like`
        Values in the range 0.0 to 1.0, to be pulled to/pushed from ends.
    e0: float
        Attractor force to the start of the interval (0.0). A negative
        value will push the values away from this point.
    e1: float
        Attractor force to the end of the interval (1.0). A negative
        value will push the values away from this point.

    Note
    ----
    This function is usually called from the :func:`seed` function,
    passing an initially uniformly distributed set of points.

    Examples
    --------
    >>> print(unitAttractor([0.,0.25,0.5,0.75,1.0], 2.))
    [0.     0.0039 0.0625 0.3164 1.    ]
    >>> unitAttractor([0.,0.25,0.5,0.75,1.0])
    array([0.  , 0.25, 0.5 , 0.75, 1.  ])
    """
    x = np.asarray(x)
    e0 = 2**e0
    e1 = 2**e1
    at0 = lambda x, e: x**e  # noqa: E731
    at1 = lambda x, e: 1.-(1.-x)**e  # noqa: E731
    return 0.5 * (at1(at0(x, e0), e1) + at0(at1(x, e1), e0))


def seed(n, e0=0., e1=0.):
    # TODO: this function could be merged into smartSeed
    """Create a list of seed values.

    A seed list is a list of float values in the range 0.0 to 1.0.
    It can be used to subdivide a line segment or to seed nodes
    along lines for meshing purposes.

    This function divides the unit interval in `n` parts, resulting
    in `n+1` seed values. While the intervals are by default of equal
    length, the `e0` and `e1` can be used to create unevenly spaced
    seed values.

    Parameters
    ----------
    n: int
        Positive integer: the number of elements (yielding `n+1`
        parameter values).
    e0: float
        Attractor force at the start of the interval. A value larger
        than zero will attract the points closer to 0.0, while
        a negative value will repulse them.
    e1: float
        Attractor force at the end of the interval. A value larger
        than zero will attract the points closer to 1.0, while
        a negative value will repulse them.

    Returns
    -------
    float arraya list of `n+1` float values in the range 0.0 to 1.0.
    The values are in ascending order, starting with 0.0 and ending with 1.0.

    See Also
    --------
    seed1: attractor at one end and equidistant points at the other.
    smartSeed: similar function accepting a variety of input.

    Examples
    --------
    >>> print(seed(5,2.,2.))
    [0.     0.0639 0.3362 0.6638 0.9361 1.    ]
    >>> with np.printoptions(precision=2):
    ...     for e0 in [0., 0.1, 0.2, 0.5, 1.0]:
    ...         print(seed(5,e0))
    [0.    0.2   0.4   0.6   0.8   1. ]
    [0.    0.18  0.37  0.58  0.79  1.  ]
    [0.    0.16  0.35  0.56  0.77  1.  ]
    [0.    0.1   0.27  0.49  0.73  1.  ]
    [0.    0.04  0.16  0.36  0.64  1.  ]
    """
    x = np.arange(n+1) * 1. / n
    if e0 != 0. or e1 != 0.:
        x = unitAttractor(x, e0, e1)
    return x


def seed1(n, nuni=0, e0=0.):
    """Create a list of seed values.

    A seed list is a list of float values in the range 0.0 to 1.0.
    It can be used to subdivide a line segment or to seed nodes
    along lines for meshing purposes.

    This function divides the unit interval in `n` parts, resulting
    in `n+1` seed values. While the intervals are by default of equal
    length, the `nuni` and `e0` can be used to create unevenly spaced
    seed values.

    Parameters
    ----------
    n: int
        The number of intervals in which to divide the range. This will
        yield `n+1` parameter values.
    nuni: 0..n-1
        The number of intervals at the end of the range that
        will have equal length. If n < 2, this function is equivalent
        with `seed(n,e0,0.0)`.
    e0: float
        Attractor for the start of the range.
        A value larger than zero will attract the points closer to the
        startpoint, while a negative value will repulse them.

    Returns
    -------
    float array
        A list of `n+1` float values in the range 0.0 to 1.0.
        The values are in ascending order, starting with 0.0 and ending with 1.0.

    See Also
    --------
    `seed`: an analogue function with attractors at both ends of the range.

    Examples
    --------
    >>> S = seed1(5,0,1.)
    >>> print(S)
    [0.   0.04 0.16 0.36 0.64 1.  ]
    >>> print(S[1:]-S[:-1])
    [0.04 0.12 0.2  0.28 0.36]
    >>> S = seed1(5,2,1.)
    >>> print(S)
    [0.     0.0435 0.1739 0.3913 0.6957 1.    ]
    >>> print(S[1:]-S[:-1])
    [0.0435 0.1304 0.2174 0.3043 0.3043]
    """
    if nuni < 2:
        seeds = seed(n, e0, 0.)
    else:
        n0 = n-nuni+1
        seeds = seed(n0, e0, 0.)
        length = seeds[-1] - seeds[-2]
        seeds2 = seeds[-1] + np.arange(1, nuni) * length
        seeds = np.concatenate([seeds, seeds2])
    seeds /= float(seeds[-1])
    return seeds


def smartSeed(n):
    """Create a list of seed values.

    Like the :func:`seed` function, this function creates a list of float
    values in the range 0.0 to 1.0. It accepts however a variety of inputs,
    making it the prefered choice when it is not known in advance how the
    user wants to control the seeds: automatically created or self specified.

    Parameters
    ----------
    n: int, tuple or float :term:`seed`
        Action depends on the argument:

        - if an int, returns ``seed(n)``,
        - if a tuple (n,), (n,e0) or (n,e0,e1): returns ``seed(*n)``,
        - if a float array-like, it is normally a sorted list of float
          values in the range 0.0 to 1.0: the values are returned
          unchanged in an array.

    Returns
    -------
    float array
        The values created depending on the input argument.

    Examples
    --------
    >>> print(smartSeed(5))
    [0.  0.2 0.4 0.6 0.8 1. ]
    >>> print(smartSeed((5,2.,1.)))
    [0.     0.01   0.1092 0.3701 0.7504 1.    ]
    >>> print(smartSeed([0.0,0.2,0.3,0.4,0.8,1.0]))
    [0.  0.2  0.3  0.4  0.8  1. ]

    """
    if isInt(n):
        return seed(n)
    elif isinstance(n, tuple):
        return seed(*n)
    elif isinstance(n, (list, np.ndarray)):
        return np.asarray(n)
    else:
        raise ValueError(f"Expected an integer, tuple or list; "
                         f"got {type(n)} = {n}")


def gridpoints(seed0, seed1=None, seed2=None):
    """Create weights for 1D, 2D or 3D element coordinates.

    Parameters
    ----------
    seed0: int or list of floats
        Subdivisions along the first parametric direction
    seed1: int or list of floats
        Subdivisions along the second parametric direction
    seed2: int or list of floats
        Subdivisions along the third parametric direction

    If these parameters are integer values the divisions will be equally
    spaced between 0 and 1.

    Examples
    --------
    >>> gridpoints(4)
    array([0.  , 0.25, 0.5 , 0.75, 1.  ])
    >>> gridpoints(4,2)
    array([[1.   , 0.   , 0.   , 0.   ],
           [0.75 , 0.25 , 0.   , 0.   ],
           [0.5  , 0.5  , 0.   , 0.   ],
           [0.25 , 0.75 , 0.   , 0.   ],
           [0.   , 1.   , 0.   , 0.   ],
           [0.5  , 0.   , 0.   , 0.5  ],
           [0.375, 0.125, 0.125, 0.375],
           [0.25 , 0.25 , 0.25 , 0.25 ],
           [0.125, 0.375, 0.375, 0.125],
           [0.   , 0.5  , 0.5  , 0.   ],
           [0.   , 0.   , 0.   , 1.   ],
           [0.   , 0.   , 0.25 , 0.75 ],
           [0.   , 0.   , 0.5  , 0.5  ],
           [0.   , 0.   , 0.75 , 0.25 ],
           [0.   , 0.   , 1.   , 0.   ]])
    """
    if seed0 is not None:
        if isInt(seed0):
            seed0 = seed(seed0)
        sh = 1
        pts = np.asarray(seed0)
    if seed1 is not None:
        if isInt(seed1):
            seed1 = seed(seed1)
        sh = 4
        x1 = np.asarray(seed0)
        y1 = np.asarray(seed1)
        x0 = 1.-x1
        y0 = 1.-y1
        pts = np.dstack([np.outer(y0, x0), np.outer(y0, x1),
                         np.outer(y1, x1), np.outer(y1, x0)])
    if seed2 is not None:
        if isInt(seed2):
            seed2 = seed(seed2)
        sh = 8
        z1 = np.asarray(seed2)
        z0 = 1.-z1
        pts = np.dstack([np.dstack([np.outer(pts[:, :, ipts], zz)
                                    for ipts in range(pts.shape[2])])
                         for zz in [z0, z1]])
    return pts.reshape(-1, sh).squeeze()




def nodalSum(val, elems, nnod=-1):
    """Compute the nodal sum of values defined on element nodes.

    Parameters
    ----------
    val: float array (nelems,nplex,nval)
        Array with ``nval`` values at ``nplex`` nodes of ``nelems`` elements.
        As a convenience, if nval=1, the last dimension may be absent.
        Also, if the values at all the nodes of an element are
        the same, an array with shape (nelems, 1, nval) may be provided.
    elems: int array (nelems,nplex)
        The node indices of the elements.
    nnod: int, optional
        If provided, the length of the output arrays will be set to
        this value. It should be higher than the highest node number
        appering in elems. The default will set it automatically to
        ``elems.max() + 1``.

    Returns
    -------
    sum: float array (nnod, nval)
        The sum of all the values at the same node.
    cnt: int array (nnod)
        The number of values summed at each node.

    See Also
    --------
    nodalAvg: compute the nodal average of values defined on element nodes

    Examples
    --------
    >>> elems = np.array([[0,1,4], [1,2,4], [2,3,4], [3,0,4]])
    >>> val = np. array([[1.], [2.], [3.], [4.]])
    >>> sum, cnt = nodalSum(val, elems)
    >>> print(sum)
    [[ 5.]
     [ 3.]
     [ 5.]
     [ 7.]
     [10.]]
    >>> print(cnt)
    [2 2 2 2 4]

    """
    try:
        from pyformex.lib.misc import nodalsum
    except ImportError:
        # Could not import nodalsum form pyformex.lib
        # So we define a replacement here
        def nodalsum(val, elems, nnod):
            """Python emulation of nodalsum from pyformex.lib.misc_c."""
            if nnod < 0:
                nnod = elems.max() + 1

            # create return arrays
            nval = val.shape[2]
            sum = np.zeros((nnod, nval), dtype=np.float32)
            cnt = np.zeros((nnod,), dtype=np.int32)

            for i, elem in enumerate(elems):
                for j, node in enumerate(elem):
                    sum[node] += val[i, j].reshape(nval)
                    cnt[node] += 1

            return sum, cnt

    if val.ndim != 3:
        val = val.reshape(val.shape+(1,))
    if val.shape[1] == 1:
        val = multiplex(val, elems.shape[1], 1)
    if elems.shape != val.shape[:2]:
        raise RuntimeError(f"shapes of elems ({elems.shape}) and val"
                           f"({val.shape[:2]}) do not match")
    val = val.astype(Float)
    elems = elems.astype(Int)
    return nodalsum(val, elems, nnod)


def nodalAvg(val, elems, nnod=-1):
    """Compute the nodal average of values defined on element nodes.

    Parameters
    ----------
    val: float array (nelems,nplex,nval)
        Array with ``nval`` values at ``nplex`` nodes of ``nelems`` elements.
    elems: int array (nelems,nplex)
        The node indices of the elements.
    nnod: int, optional
        If provided, the length of the output arrays will be set to
        this value. It should be higher than the highest node number
        appering in elems. The default will set it automatically to
        ``elems.max() + 1``.

    Returns
    -------
    avg: float array (nnod, nval)
        The average of all the values at the same node.

    See Also
    --------
    nodalSum: compute the nodal sum of values defined on element nodes
    """
    sum, cnt = nodalSum(val, elems, nnod)
    return sum/cnt[:, np.newaxis]


def fmtData1d(data, npl=8, sep=', ', linesep='\n', fmt=str):
    """Format data in lines with maximum npl items.

    Formats a list or array of data items in groups containing
    a maximum number of items. The data items are converted to
    strings using the `fmt` function, concatenated
    in groups of `npl` items using `sep` as a separator between them.
    Finally, the groups are concatenated with a `linesep` separator.

    Parameters
    ----------
    data: list or array.
        List or array with data. If an array, if will be flattened.
    npl: int
        Maximum number of items per group. Items will be concatenated
        groups of this number of items. The last group
        may contain less items.
    sep: str
        Separator to add between individual items in a group.
    linesep: str
        Separator to add between groups. The default (newline) will
        put each group of `npl` items on a separate line.
    fmt: callable
        Used to convert a single item to a string. Default
        is the Python built-in string converter.

    Returns
    -------
    : str
        Multiline string with the formatted data.

    Examples
    --------
    >>> print(fmtData1d(np.arange(10)))
    0, 1, 2, 3, 4, 5, 6, 7
    8, 9
    >>> print(fmtData1d([1.25, 3, 'no', 2.50, 4, 'yes'],npl=3))
    1.25, 3, no
    2.5, 4, yes

    >>> myformat = lambda x: f"{str(x):>10s}"
    >>> print(fmtData1d([1.25, 3, 'no', 2.50, 4, 'yes'],npl=3,fmt=myformat))
          1.25,         3,        no
           2.5,         4,       yes

    """
    if isinstance(data, np.ndarray):
        data = data.flat
    return linesep.join([sep.join(map(fmt, data[i:i+npl]))
                         for i in range(0, len(data), npl)])


# selftest
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    import doctest
    np.set_printoptions(precision=4, suppress=True)
    failures, tests = doctest.testmod(
        optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)
    print(f"{__file__}: Tests: {tests}; Failures: {failures}")

# End
