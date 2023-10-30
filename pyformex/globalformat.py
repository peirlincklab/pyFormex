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

# This file includes parts from https://pypi.org/project/forbiddenfruit/
# Copyright (c) 2013-2020  Lincoln de Sousa <lincoln@clarete.li>

"""Set global ouput format for built-in types.

One of the major shortcomings of Python is the lack of global print options
allowing to set the output format for built-in type globally for your
application. Especially the default formatting of float values is
annoyingly large.

>>> sqrt2 = 2 ** 0.5
>>> print(sqrt2)
1.4142135623730951

To get a shorter output with less decimals one can round the value, or
use a format specifier:

>>> print(round(sqrt2, 4))
1.4142
>>> print(f"{sqrt2:.4f}")
1.4142

But this is only convenient when you have to output a single float,
but doesn't work for floats embedded in a container.

>>> cont = (1/2, 1/3, 1/16)
>>> print(cont)
(0.5, 0.3333333333333333, 0.0625)

Luckily, for most numerical work we can (and should) use NumPy, which allows
to set global print options for its classes:

>>> import numpy as np
>>> np.set_printoptions(precision=4, floatmode='fixed')
>>> ar = np.array(cont)
>>> print(ar)
[0.5000 0.3333 0.0625]

But even then one falls back to the Python default for a single array element:

>>> print(ar[0], ar[1])
0.5 0.3333333333333333

The solution would be to override float.__repr__, but Python won't let you:

>>> float.__repr__ = lambda f: f"{f:.4f}"
Traceback (most recent call last):
...
TypeError: cannot set '__repr__' attribute of immutable type 'float'

But since this is Python, there must be some way to overcome this hurdle.
And I finally found one: the forbiddenfruit module
(https://pypi.org/project/forbiddenfruit/)
by Lincoln de Sousa <lincoln@clarete.li> allows to do all kinds of
monkeypatching on builtin types. Since we only need a small part of
it, we copied the relevant things in this module, thus avoiding that
our users need to install that module. Now we can set our own float.__repr__
method, which can take account of a global precision setting.

>>> setfloatformat('.4f')        # set fixed format for all floats
>>> print(cont)
(0.5000, 0.3333, 0.0625)
>>> setfloatformat('')           # reset Python's default
>>> print(cont)
(0.5, 0.3333333333333333, 0.0625)

Or you can use the floatformat context manager to temporarily change
the format:

>>> with floatformat('.4f'):
...    print('.4f', cont)
...    with floatformat('10.2e'):
...        print('10.2e', cont)
...    print('back to .4f', cont)
.4f (0.5000, 0.3333, 0.0625)
10.2e (  5.00e-01,   3.33e-01,   6.25e-02)
back to .4f (0.5000, 0.3333, 0.0625)
>>> print('back to default', cont)
back to default (0.5, 0.3333333333333333, 0.0625)

"""
# Start (c) Lincoln de Sousa
import ctypes
from functools import wraps

__all__ = ('override_dunder', 'revert_dunder', 'setfloatformat', 'floatformat',
           'setintformat', 'intformat')


Py_ssize_t = ctypes.c_int64 if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_int32

# dictionary holding references to the allocated function resolution
# arrays to type objects
tp_as_dict = {}
# container to cfunc callbacks
tp_func_dict = {}


class PyObject(ctypes.Structure):
    def incref(self):
        self.ob_refcnt += 1

    def decref(self):
        self.ob_refcnt -= 1


class PyFile(ctypes.Structure):
    pass

PyObject_p = ctypes.py_object
Inquiry_p = ctypes.CFUNCTYPE(ctypes.c_int, PyObject_p)
# return type is void* to allow ctypes to convert python integers to
# plain PyObject*
UnaryFunc_p = ctypes.CFUNCTYPE(ctypes.py_object, PyObject_p)
BinaryFunc_p = ctypes.CFUNCTYPE(ctypes.py_object, PyObject_p, PyObject_p)
TernaryFunc_p = ctypes.CFUNCTYPE(ctypes.py_object, PyObject_p, PyObject_p, PyObject_p)
LenFunc_p = ctypes.CFUNCTYPE(Py_ssize_t, PyObject_p)
SSizeArgFunc_p = ctypes.CFUNCTYPE(ctypes.py_object, PyObject_p, Py_ssize_t)
SSizeObjArgProc_p = ctypes.CFUNCTYPE(ctypes.c_int, PyObject_p, Py_ssize_t, PyObject_p)
ObjObjProc_p = ctypes.CFUNCTYPE(ctypes.c_int, PyObject_p, PyObject_p)

FILE_p = ctypes.POINTER(PyFile)


def get_not_implemented():
    namespace = {}
    name = "_Py_NotImplmented"
    not_implemented = ctypes.cast(
        ctypes.pythonapi._Py_NotImplementedStruct, ctypes.py_object)

    ctypes.pythonapi.PyDict_SetItem(
        ctypes.py_object(namespace),
        ctypes.py_object(name),
        not_implemented
    )
    return namespace[name]


# address of the _Py_NotImplementedStruct singleton
NotImplementedRet = get_not_implemented()

class PyTypeObject(ctypes.Structure):
    pass

class PyAsyncMethods(ctypes.Structure):
    pass


PyObject._fields_ = [
    ('ob_refcnt', Py_ssize_t),
    ('ob_type', ctypes.POINTER(PyTypeObject)),
]

PyTypeObject._fields_ = [
    # varhead
    ('ob_base', PyObject),
    ('ob_size', Py_ssize_t),
    # declaration
    ('tp_name', ctypes.c_char_p),
    ('tp_basicsize', Py_ssize_t),
    ('tp_itemsize', Py_ssize_t),
    ('tp_dealloc', ctypes.CFUNCTYPE(None, PyObject_p)),
    ('printfunc', ctypes.CFUNCTYPE(ctypes.c_int, PyObject_p, FILE_p, ctypes.c_int)),
    ('getattrfunc', ctypes.CFUNCTYPE(PyObject_p, PyObject_p, ctypes.c_char_p)),
    ('setattrfunc', ctypes.CFUNCTYPE(ctypes.c_int, PyObject_p, ctypes.c_char_p, PyObject_p)),
    ('tp_as_async', ctypes.CFUNCTYPE(PyAsyncMethods)),
    ('tp_repr', ctypes.CFUNCTYPE(PyObject_p, PyObject_p)),  # added by BV
    ('tp_str', ctypes.CFUNCTYPE(PyObject_p, PyObject_p)),
    # ...
]


override_dict = {
    '__str__': ('tp_str', "tp_str"),
    '__repr__': ('tp_repr', "tp_repr"),  # added by BV
    }


def override_dunder(klass, attr, func):
    assert callable(func)

    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        This wrapper returns the address of the resulting object as a
        python integer which is then converted to a pointer by ctypes
        """
        try:
            return func(*args, **kwargs)
        except NotImplementedError:
            return NotImplementedRet

    tp_as_name, impl_method = override_dict[attr]

    # get the pointer to the correct tp_as_* structure
    # or create it if it doesn't exist
    tyobj = PyTypeObject.from_address(id(klass))
    # find the C function type
    for fname, ftype in PyTypeObject._fields_:
        if fname == impl_method:
            cfunc_t = ftype

    if not (klass, attr) in tp_as_dict:
        tp_as_dict[(klass, attr)] = ctypes.cast(getattr(tyobj, impl_method), cfunc_t)

    # override function call
    cfunc = cfunc_t(wrapper)
    tp_func_dict[(klass, attr)] = cfunc
    setattr(tyobj, impl_method, cfunc)

def revert_dunder(klass, attr):
    tp_as_name, impl_method = override_dict[attr]
    tyobj = PyTypeObject.from_address(id(klass))
    tp_as_ptr = getattr(tyobj, tp_as_name)
    if tp_as_ptr:
        if not (klass, attr) in tp_as_dict:
            # we didn't save this pointer
            # most likely never cursed
            return

        cfunc = tp_as_dict[(klass, attr)]
        setattr(tyobj, impl_method, cfunc)

# End (c) Lincoln de Sousa

_float_format = ''

def float_repr(f):
    return f"{f:{_float_format}}"

def setfloatformat(fmt):
    """Set global default format for float

    Parameters
    ----------
    fmt: str
        A format string to format a single float number. For example: '.4f'
        will format the float with 4 decimals. An empty string resets
        the format to Python's default. An invalid format string raises an
        Exception.
    """
    global _float_format
    if fmt:
        f"{1.5:{fmt}}"   #  force an exception on invalid format
        _float_format = fmt
        override_dunder(float, '__repr__', float_repr)
    else:
        _float_format = ''
        revert_dunder(float, '__repr__')

class floatformat:
    """Context manager to temporarily change the global float format.

    Parameters
    ----------
    fmt: str
        A format string like in :func:`setfloatformat`.

    Notes
    -----
    On exit, the global float format is reset to what is was before entering.
    """
    def __init__(self, fmt):
        self.fmt = fmt
        self.prev = _float_format

    def __enter__(self):
        setfloatformat(self.fmt)
        return self

    def __exit__(self, *exc):
        setfloatformat(self.prev)

_int_format = ''

def int_repr(value):
    return f"{value:{_int_format}}"

def setintformat(fmt):
    global _int_format
    if fmt:
        f"{1:{fmt}}"
        _int_format = fmt
        override_dunder(int, '__repr__', int_repr)
    else:
        _int_format = ''
        revert_dunder(int, '__repr__')

class intformat:
    def __init__(self, fmt):
        self.fmt = fmt
        self.prev = _int_format

    def __enter__(self):
        setintformat(self.fmt)
        return self

    def __exit__(self, *exc):
        setintformat(self.prev)

# End
