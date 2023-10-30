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

"""Automatic generation of documentation

This module provides the tools to automatically generate the documentation
for a pyFormex module. It is mainly intended for use by the
'pyformex --docmodule' command option.

This command automatically extracts class & function docstrings and argument
list from a module and ships out the information in a format that can be
used by the Sphinx document preprocessor.
"""
import sys
import inspect
import importlib

from pyformex.utils import underlineHeader

_debug = False


############# Output formatting ##########################


def add_indent(s, n):
    """Indent all lines of a multiline string with n blanks."""
    return '\n'.join([' ' * n + si for si in s.split('\n')])


def split_doc(docstring):
    try:
        s = docstring.split('\n')
        shortdoc = s[0]
        if len(s) > 2:
            longdoc = '\n'.join(s[2:])
        else:
            longdoc = ''
        return shortdoc.strip('"'), longdoc.strip('"')
    except Exception:
        return '', ''


def sanitize(s):
    """Sanitize a string for LaTeX."""
    for c in '#&%':
        s = s.replace('\\' + c, c)
        s = s.replace(c, '\\' + c)
    # for c in '{}':
    #     s = s.replace('\\'+c,c)
    #     s = s.replace(c,'\\'+c)
    return s


out = ''


def ship_start():
    global out
    out = ''


def ship(s):
    global out
    out += s
    out += '\n'


def debug(s):
    if _debug:
        ship('.. DEBUG:' + str(s))


def ship_module(name, docstring, members):
    shortdoc, longdoc = split_doc(docstring)
    auto = 'auto' #'' if name.endswith('_c') else 'auto'
    ship(f"""\
..  -*- rst -*-
.. pyformex reference manual --- {name}
.. CREATED WITH pyformex --docmodule: DO NOT EDIT

.. include:: <isonum.txt>
.. include:: ../defines.inc
.. include:: ../links.inc

.. _sec:ref-{name}:

:mod:`{name}` --- {shortdoc}
{'=' * (12 + len(name) + len(shortdoc))}

.. {auto}module:: {name}
   :synopsis: {shortdoc}""")
    if members:
        ship(f"   :members: {','.join(members)}")
    ship('')


def ship_end():
    ship("""

.. moduleauthor:: pyFormex project (http://pyformex.org)

.. End
"""
    )


def ship_functions(members=[]):
    if members:
        for f in members:
            ship(f".. autofunction:: {f}")


def ship_class(name, members=[], special=[], exclude=[]):
    ship(f"   .. autoclass:: {name}")
    if members:
        ship(f"      :members: {','.join(members)}")
    else:
        ship(f"      :members:")
    if special:
        ship(f"      :special-members: {','.join(special)}")
    if exclude:
        ship(f"      :exclude-members: {','.join(exclude)}")


def ship_attribute(name):
    ship(f"   .. autodata:: {name}")


def ship_section_init(secname, modname):
    indent = 3 # 0 if modname.endswith('_c') else 3
    ship(
        add_indent(
            '\n' + underlineHeader(
                f"{secname} defined in module {modname}", '~'
            ) + '\n', indent
        )
    )


############# Info selection ##########################


def filter_local(name, fullname):
    """Filter definitions to include in doc

    We only include names defined in the module itself.
    """
    return name.__module__ == fullname


def filter_names(info):
    return [i for i in info if not i[0].startswith('_')]


def filter_docstrings(info):
    return [
        i for i in info
        if not (i[1].__doc__ is None or i[1].__doc__.startswith('_'))
    ]


def filter_module(info, modname):
    return [i for i in info if i[1].__module__ == modname]


def function_key(i):
    obj = i[1]
    return obj.__code__.co_firstlineno


def property_key(i):
    obj = i[1]
    if hasattr(obj, 'fget'):
        val = obj.fget.__code__.co_firstlineno
    else:
        val = 0
    return val


_py2rst_order = []

def class_key(i):
    try:
        key = inspect.getsourcelines(i[1])[1]
    except Exception:
        key = 999999
    return key

def class_key_1(i):
    try:
        key = _py2rst_order.index(i[0])
    except ValueError:
        key = 99999
    return key

def check_declared_members(obj):
    """Check if obj has declared members

    Currently 3 members declarations are acknowledged:
    _members_
    _special_members_
    _exclude_members_
    """
    try:
        members = getattr(obj, '_members_')
    except Exception:
        members = []
    try:
        special = getattr(obj, '_special_members_')
    except Exception:
        special = []
    try:
        exclude = getattr(obj, '_exclude_members_')
    except Exception:
        exclude = []
    return members, special, exclude


def do_class(name, obj):
    members, special, exclude = check_declared_members(obj)
    ship_class(name, members=members, special=special, exclude=exclude)
    return

    # # get class attributes
    # try:
    #     attrnames = getattr(obj,'_attributes_')
    # except Exception:
    #     attrnames = []

    # # get class properties#
    # # props = inspect.getmembers(obj,inspect.isdatadescriptor)
    # # props = [ p for p in props if isinstance(p[1],property) ]
    # # props = filter_names(props)
    # # props = filter_docstrings(props)
    # # props = sorted(props,key=property_key)
    # props = []
    # # get class methods #
    # methods = inspect.getmembers(obj,inspect.ismethod)
    # methods = filter_names(methods)
    # methods = filter_docstrings(methods)
    # methods = sorted(methods,key=function_key)
    # names = [ f[0] for f in props+methods ]
    # ship_class(name,attrnames+names)


def do_list(module):
    members = inspect.getmembers(module)
    visible = [m for m in members if not m[0].startswith('_')]

    attributes = [
        m for m in visible
        if not inspect.isclass(m[1]) and not inspect.isfunction(m[1])
    ]
    for m in attributes:
        print(m)

    for name, obj in visible:
        print(f"{name} docstring: {inspect.getdoc(obj)}")


def get_py_members(module, fullname):
    """Select the attributes, classes and functions from module"""
    global _py2rst_order
    _py2rst_order = getattr(module, '_py2rst_order_', [])

    # Attributes #
    attrnames = getattr(module, '_attributes_', [])

    # Classes #
    classes = [
        c for c in inspect.getmembers(module, inspect.isclass)
        if filter_local(c[1], fullname)
    ]
    classes = filter_names(classes)
    classes = filter_docstrings(classes)
    keyfunc = class_key_1 if _py2rst_order else class_key
    classes = sorted(classes, key=keyfunc)

    # Functions #
    functions = [
        c for c in inspect.getmembers(module, inspect.isfunction)
        if filter_local(c[1], fullname)
    ]
    functions = filter_names(functions)
    functions = filter_docstrings(functions)
    functions = sorted(functions, key=function_key)
    funcnames = [f[0] for f in functions]

    return attrnames, classes, funcnames


def get_c_members(members):
    """Select the attributes, classes and functions from module"""
    attrnames = [] # 'accelerated' ]
    functions = [m for m in members if callable(m[1])]
    functions = filter_names(functions)
    functions = filter_docstrings(functions)
    # sigs = [inspect.signature(m[1]) for m in functions]
    # print(sigs)
    funcnames = [f[0] for f in functions]
    return attrnames, [], funcnames


def do_module(modname, outfile=None):
    """Process a module.

    Prints the documentation of the module in .rst format.
    The output has to be processes by sphinx using autodoc to generate
    the full documentation. This is done with the ``make html`` command
    in the top directory of the pyFormex source.

    Parameters
    ----------
    modname: str
        Name of the module in Python dotted style. The ``pyformex.`` part
        may be omitted.
    """
    if modname.startswith('pyformex.'):
        fullname = modname
    else:
        fullname = 'pyformex.' + modname
    module = importlib.import_module(fullname)

    members = inspect.getmembers(module)
    visible = [m for m in members if not m[0].startswith('_')]  # noqa: F841

    if modname.endswith('_c'):
        attrnames, classes, funcnames = get_c_members(members)
    else:
        attrnames, classes, funcnames = get_py_members(module, fullname)

    # Shipout

    ship_start()
    ship_module(modname, module.__doc__, funcnames)
    if attrnames:
        ship_section_init('Variables', modname)
        for n in attrnames:
            ship_attribute(n)
    if classes:
        # If the module only contains 1 single class and nothing else,
        # omit the classes header
        if len(classes) > 1 or attrnames or funcnames:
            ship_section_init('Classes', modname)
        for c in classes:
            do_class(*c)
    if funcnames:
        ship_section_init('Functions', modname)
    # if funcnames and modname.endswith('_c'):
    #     ship_functions(funcnames)
    ship_end()

    return out

# End
