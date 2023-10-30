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

"""tools_menu.py

Graphic Tools plugin menu for pyFormex.
"""
import pyformex as pf
from pyformex import utils
from pyformex.script import listAll, export, forgetAll
from pyformex.gui.draw import askItems, ack
from pyformex.plugins import objects

from pyformex.formex import Formex

def editFormex(F, name):
    """Edit a Formex"""
    items = [_I('coords', repr(F.coords), 'text')]
    if F.prop is not None:
        items.append(_I('prop', repr(F.prop), 'text'))
    items.append(_I('eltype', F.eltype))
    res = askItems(items)
    if res:
        x = eval(res['coords'])
        p = res.get('eltype', None)
        if isinstance(p, str):
            p = eval(p)
        e = res['eltype']
        print(x)
        print(p)
        print(e)
        F.__init__(x, F.prop, e)

Formex.edit = editFormex


##################### database tools ##########################

database = None
drawable = None

def _init_(all, draw):
    """_initialize the global variables of this module

    This can only be done after the database Ojects have been created
    in guimain.
    """
    global database, drawable
    database = all
    drawable = draw


def printall():
    """Print all global variable names."""
    print(listAll(sort=True))


def printval():
    """Print selected global variables."""
    database.ask()
    database.printval()


def printbbox():
    """Print selected global variables."""
    database.ask()
    database.printbbox()


def select():
    """Select and draw global variables."""
    database.ask()
    print(database.names)


def draw():
    """Draw selected variables."""
    drawable.ask()


def keep_():
    """Keep global variables."""
    database.ask()
    database.keep()


def forget_():
    """Forget global variables."""
    database.ask()
    database.forget()


def create():
    """Create a new global variable with default initial contents."""
    res = askItems([('name', '')])
    if res:
        name = res['name']
        if name in database:
            warning("The variable named '%s' already exists!")
        else:
            export({name: '__initial__'})


def edit():
    """Edit a global variable."""
    database.ask(single=True)
    F = database.check(single=True)
    if F is not None:
        name = database.names[0]
        if hasattr(F, 'edit'):
            # Call specialized editor
            F.edit(name)
        else:
            # Use general editor
            res = askItems([(name, repr(F), 'text')])
            if res:
                print(res)
                pf.PF.update(res)


def rename_():
    """Rename a global variable."""
    database.ask(single=True)
    F = database.check(single=True)
    if F is not None:
        oldname = database.names[0]
        res = askItems([('Name', oldname)], caption = 'Rename variable')
        if res:
            name = res['Name']
            export({name: F})
            database.forget()
            database.set(name)


def delete_all():
    printall()
    if ack("Are you sure you want to unrecoverably delete all global variables?"):
        forgetAll()


MenuData = ('Globals', [
    ('  List All', printall),
    ('  Select', select),
    ('  Print Value', printval),
    ('  Print BBox', printbbox),
    ('  Draw', draw),
    ('  Create', create),
    ('  Change Value', edit),
    ('  Rename', rename_),
    ('  Keep', keep_),
    ('  Delete', forget_),
    ('  Delete All', delete_all),
    ])


# End
