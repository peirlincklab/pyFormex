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

"""Selection of objects from the global dictionary.

This is a support module for other pyFormex plugins.
"""

from copy import deepcopy

import pyformex as pf
from pyformex import geomfile
from pyformex.coords import bbox
from pyformex.gui import draw as gs
from pyformex.gui.draw import _I, _G, _C, _T


class Objects():
    """A selection of objects from the pyFormex Globals().

    The class provides facilities to filter the global objects by their type
    and select one or more objects by their name(s). The values of these
    objects can be changed and the changes can be undone.

    Examples
    --------
    >>> from pyformex.core import Mesh, TriSurface
    >>> pf.PF.clear()
    >>> M = Mesh()
    >>> M1 = Mesh(eltype='tri3')
    >>> S = M1.toSurface()
    >>> F = S.toFormex()
    >>> gs.export({'a':2, 'M':M, 'S':S, 'F':F, 'M1':M1})
    >>> Objects(clas=Mesh).listAll()
    ['M', 'S', 'M1']
    >>> Objects(clas=Mesh,
    ...     filter=lambda o: isinstance(pf.PF[o], TriSurface)).listAll()
    ['S']
    """

    def __init__(self, clas=None, like=None, filter=None, namelist=[]):
        """Create a new selection of objects.

        If a filter is given, only objects passing it will be accepted.
        The filter will be applied dynamically on the dict.

        If a list of names is given, the current selection will be set to
        those names (provided they are in the dictionary).
        """
        self.clas = clas
        self.like = like
        self.filter = filter
        self.names = []
        self._values = []
        self.clear()
        if namelist:
            self.set(namelist)


    @property
    def object_type(self):
        """Return the type of objects in this selection."""
        return self.clas.__name__ if self.clas else 'Any'


    def set(self, names):
        """Set the selection to a list of names.

        namelist can be a single object name or a list of names.
        This will also store the current values of the variables.
        """
        if isinstance(names, str):
            names = [names]
        self.names = [s for s in names if isinstance(s, str)]
        self._values = [gs.named(s) for s in self.names]


    def append(self, name, value=None):
        """Add a name,value to a selection.

        If no value is given, its current value is used.
        If a value is given, it is exported.
        """
        self.names.append(name)
        if value is None:
            value = gs.named(name)
        else:
            gs.export({name: value})
        self._values.append(value)


    def clear(self):
        """Clear the selection."""
        self.set([])


    def narrow(self, allowed=()):
        """Narrow the current selection to objects of the specified classes

        Parameters
        ----------
        allowed: type | tuple of type
            The allowed instance types. All objects in the current selection
            that are not instances of any of the allowed types, are removed.
            The default (empty tuple) clears the selection. A value None leaves
            the selection untouched.
        """
        if allowed is None:
            return
        if isinstance(allowed, type):
            allowed = (allowed,)
        oknames = [n for n in self.names if isinstance(gs.named(n), allowed)]
        if len(oknames) < len(self.names):
            print(f"Current selection is narrowed to: {oknames}")
        self.set(oknames)


    def __getitem__(self, i):
        """Return selection item i"""
        return self.names[i]


    def listAll(self, allowed=None):
        """Return a list with all selectable objects.

        This lists all the global names in pyformex.PF that match
        the class and/or filter (if specified).
        """
        if allowed is None:
            allowed = self.clas
        return gs.listAll(clas=allowed, like=self.like, filtr=self.filter)


    def selectAll(self):
        self.set(self.listAll())


    def remember(self, copy=False):
        """Remember the current values of the variables in selection.

        If copy==True, the values are copied, so that the variables' current
        values can be changed inplace without affecting the remembered values.
        """
        self._values = [gs.named(n) for n in self.names]
        if copy:
            self._values = [deepcopy(n) for n in self._values]


    def changeValues(self, newvalues):
        """Replace the current values of selection by new ones.

        The old values are stored locally, to enable undo operations.

        This is only needed to change the values of objects that can not
        be changed inplace!
        """
        self.remember()
        gs.export2(self.names, newvalues)


    def undoChanges(self):
        """Undo the last changes of the values."""
        gs.export2(self.names, self._values)


    def check(self, *, allowed=None, single=False, warn=True):
        """Check and return the current selection.

        Checks that a current selection exists and conforms to the
        provided requirements.

        Parameters
        ----------
        allowed: type or tuple of type, optional
            One or more object types. If provided, the current selection
            will be narrowed down to objects of this type.
        single: bool, optional
            If True, only a single object should be selected. The default
            allows a multiple objects selection.
        warn: bool, optional
            If True (default), a warning is displayed if the selection
            is empty or there is more than one selected object when
            ``single=True`` was specified. Setting to False suppresses
            the warning, which may be useful in batch processing.

        Returns
        -------
        object | list of objects | None
            With ``single=True``, a single selected object, else a list
            of objects. These objects constitute the current selection.
            If there is no current selection, or more than one in case
            of ``single=True``, None is returned.
        """
        self.names = [n for n in self.names if n in pf.PF]
        if allowed is not None:
            self.narrow(allowed)
        if len(self.names) == 0:
            if warn:
                pf.warning(f"No {self.object_type} objects were selected")
            return None
        if single and len(self.names) > 1:
            if warn:
                pf.warning(f"You should select exactly one {self.object_type}")
            return None
        ret = self.values()
        if single:
            return ret[0]
        else:
            return ret


    # TODO: this could/should become an option of check
    def checkOrAsk(self, *, allowed=None, single=False, warn=True):
        """Check, ask and return the current selection.

        This is like :meth:`check`, but if the selection does not
        conform, lets the user change it.
        """
        sel = self.check(allowed=allowed, single=single, warn=False)
        print(f"AFTER CHECK: {sel}")
        if sel is None:
            res = self.ask(single=single, allowed=allowed)
            if res is not None:
                sel = self.check(allowed=allowed, single=single, warn=False)
        return sel


    def keys(self):
        """Return the names of the currently selected objects."""
        return self.names


    def values(self):
        """Return the values of the currently selected objects."""
        return [gs.named(n) for n in self.names]


    def odict(self):
        """Return the currently selected items as a dictionary.

        Returns a dict with the currently selected objects in the order
        of the selection.names.
        """
        return dict(zip(self.names, self.values()))


    def ask(self, single=False, allowed=None):
        """Show the names of known objects and let the user select one or more.

        Parameters
        ----------
        single: bool
            If True, only one item can be selected.

        Returns
        -------
        list | None
            A list with the selected name(s), possibly empty (if nothing
            was selected by the user), or None if there is nothing to choose
            from.

        Notes
        -----
        This also sets the current selection to the selected names, unless
        the return value is None, in which case the selection remains unchanged.
        """
        if allowed is None:
            allowed = self.clas
        choices = self.listAll(allowed)
        if not choices:
            pf.warning(f"There are no objects of class {allowed.__name__}")
            return None
        res = gs.selectItems(caption=f"Known objects of type {self.object_type}",
                          choices=choices,
                          default=[n for n in self.names if n in choices],
                          single=single,
                          sort=True)
        if res is None:
            res = []
        self.set(res)
        return res


    def ask1(self):
        """Select a single object from the list.

        This is like :func:`ask` with the ``single=True`` parameter,
        but returns the object instead of its name.
        """
        if self.ask(single=True):
            return gs.named(self.names[0])
        else:
            return None


    def forget(self):
        """Remove the selection from the globals."""
        gs.forget(self.names)
        self.clear()


    def keep(self):
        """Remove everything except the selection from the globals."""
        gs.forget([n for n in self.listAll() if not n in self.names])


    def writeToFile(self, filename):
        """Write objects to a geometry file."""
        objects = self.odict()
        if objects:
            filewrite.writePGF(filename, objects)


    def readFromFile(self, filename):
        """Read objects from a geometry file."""
        res = fileread.readPGF(filename)
        gs.export(res)
        self.set(res.keys())


###################### Drawable Objects #############################

class DrawableObjects(Objects):
    """A selection of drawable objects from the globals().

    This is a subclass of Objects. The constructor has the same arguments
    as the Objects class. THe difference is that when a selection is made
    in the DrawableObjects class, the selection is drawn automatically.
    This is therefore well suited to do interactive modeling.
    Furthermore it has provisions to add annotations to the rendering, like
    node and element numbers, or surface normals.
    """
    # Registered annotations
    Annotations = {}

    def __init__(self, **kargs):
        super().__init__(**kargs)
        self.autodraw = False
        self.annotations = set()  # Active annotations (function names)
        self._annotations = {}  # Drawn annotations (Drawables/Actors)
        self._actors = []  # Drawn objects (Actors)


    def ask(self, **kargs):
        """Interactively sets the current selection."""
        new = super().ask(**kargs)
        if new is not None:
            self.draw()
        return new


    def draw(self, **kargs):
        gs.clear()
        pf.debug(f"Drawing SELECTION: {self.names}", pf.DEBUG.DRAW)
        with gs.busyCursor():
            self._actors = gs.draw(self.names, clear=False, wait=False, **kargs)
            for f in self.annotations:
                pf.debug(f"Drawing ANNOTATION: {f}", pf.DEBUG.DRAW)
                self.drawAnnotation(f)


    def drawChanges(self):
        """Draws old and new version of a Formex with different colors.

        old and new can be a either Formex instances or names or lists thereof.
        old are drawn in yellow, new in the current color.
        """
        self.draw()
        gs.draw(self._values, color='yellow', bbox=None, clear=False, wait=False)


    def undoChanges(self):
        """Undo the last changes of the values."""
        super().undoChanges()
        self.draw()


    def registerAnnotation(self, **kargs):
        """Register annotation function.

        An annotation function is a function that takes the name of an
        object as parameter and draws something related to that object.
        The annotations drawn by these functions can be toggled on and off.
        Annotion functions should silently ignore objects for which they
        can not draw the annptation
        The Geometry menu has many examples of annotation functions.

        Parameters
        ----------
        kargs:
            A dict where each key ia an annotation name and the value
            is an annotation function.
        """

        DrawableObjects.Annotations.update(kargs)


    def registeredAnnotations(self):
        return DrawableObjects.Annotations


    def hasAnnotation(self, f):
        """Return the status of annotation f"""
        if isinstance(f, str):
            f = DrawableObjects.Annotations.get(f, None)
        return f in self.annotations


    def toggleAnnotation(self, f, onoff=None):
        """Toggle the display of an annotation On or Off.

        If given, onoff is True or False.
        If no onoff is given, this works as a toggle.
        """
        print(f"toggleAnnotation {self} {f} {onoff}")
        if isinstance(f, str):
            f = DrawableObjects.Annotations.get(f, None)
        if f is None:
            return
        if onoff is None:
            # toggle
            active = f not in self.annotations
        else:
            active = onoff
        if active:
            self.annotations.add(f)
            self.drawAnnotation(f)
        else:
            self.annotations.discard(f)
            self.removeAnnotation(f)


    def drawAnnotation(self, f):
        """Draw some annotation for the current selection."""
        print(f"drawAnnotation {f}")
        self._annotations[f] = [f(n) for n in self.names]


    def removeAnnotation(self, f):
        """Remove the annotation f."""
        if f in self._annotations:
            # pf.canvas.removeAnnotation(self._annotations[f])
            # Use removeAny, because some annotations are not canvas
            # annotations but actors!
            pf.canvas.removeAny(self._annotations[f])
            pf.canvas.update()
            del self._annotations[f]


    def editAnnotations(self, ontop=None):
        """Edit the annotation properties

        Currently only changes the ontop attribute for all drawn
        annotations. Values: True, False or '' (toggle).
        Other values have no effect.

        """
        for f in self._annotations.values():
            if ontop in [True, False, '']:
                if not isinstance(f, list):
                   f = [f]
                for a in f:
                    if ontop == '':
                        ontop = not a.ontop
                    print(a, ontop)
                    a.ontop = ontop


    def setProp(self, prop=None):
        """Set the property of the current selection.

        prop should be a single integer value or None.
        If None is given, a value will be asked from the user.
        If a negative value is given, the property is removed.
        If a selected object does not have a setProp method, it is ignored.
        """
        objects = self.check()
        if objects:
            if prop is None:
                res = gs.askItems(caption = 'Set Property Value', items=[
                    _I('method', choices=['single', 'list', 'object',
                                          'element', 'none']),
                    _I('value', 0,
                       tooltip='A single value given to all elements'),
                    _I('list', [0, 1],
                       tooltip='A list of values, repeated if needed'),
                ], enablers=[
                    ('method', 'single', 'value'),
                    ('method', 'object', 'value'),
                    ('method', 'list', 'list'),
                ])
                if res:
                    if res['method'] == 'single':
                        prop = res['value']
                    elif res['method'] == 'list':
                        prop = res['list']
                    elif res['method'] == 'object':
                        prop = res['value']
                    elif res['method'] == 'element':
                        prop = 'range'
                    else:
                        prop = None
                    for o in objects:
                        if hasattr(o, 'setProp'):
                            o.setProp(prop)
                        if res['method'] == 'object':
                            prop += 1
                    self.draw()


    def delProp(self):
        """Delete the property of the current selection.

        Resets the `prop` attribute of all selected objects to None.
        """
        objects = self.check()
        if objects:
            for o in objects:
                if hasattr(o, 'prop'):
                    o.prop=None
            self.draw()


# End
