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
"""Menus for the pyFormex GUI.

This modules implements specialized classes and functions for building
the pyFormex GUI menu system.
"""
import os

import pyformex as pf
from pyformex import utils
from pyformex import script
from pyformex.path import Path
from pyformex.gui import QtGui, QtCore, QtWidgets, QPixmap

############################# Menu ##############################

class BaseMenu():
    """A generic hierarchical menu class.

    The BaseMenu is a mixin class for Qt menu widgets. It has the
    following advantages over using plain Qt:

    - all the menu data can be collected in an easy readable form and
      then inserted at once in a menu,
    - an action item can have data stored that is passed to the
      action's function,
    - an item can also be a list of items, and a submenu is created
      automatically,
    - an item can even be any type of data and it will be stored in the item.
    - the menu can have a global function triggered by all the items in
      the menu or its submenu, and then operate on the triggering action
      according to the data stored in the item.
    - items can be easily looked up in the menu through a normalized
      item text. This facilitates dynamical changes to the menu.

    This class is not intended for direct use, but through the subclasses
    :class:`Menu` and :class`MenuBar`, which pack the QtWidgets.QMenu and
    QtWidgets.QMenuBar. See Notes if you want to create a subclass yourself.

    Parameters
    ----------
    parent: QWidget
        The parent widget, which can be a BaseMenu itself. If provided,
        the menu will be added to that widget.
    before: str
        The name of an item in the parent menu. If parent was provided
        and is a BaseMenu having an item with that name, the menu will
        be inserted before that item instead of at the end.
    items: list
        A list of items to insert in the menu. See :meth:`insertItems`.
    func: callable
        A function that will be called whenever an item in the menu is
        clicked. The function is passed the triggering action as an
        argument.

    Notes
    -----
    Subclasses should implement at least the following methods:

    - addSeparator()
    - insertSeparator(before)
    - addAction(text,action)
    - insertAction(before,text,action)
    - addMenu(text,menu)
    - insertMenu(before,text,menu)
    - title(): returning the menu title

    """
    def __init__(self, parent=None, *, before=None, items=None, func=None):
        """Create a menu."""
        pf.debug(f"Creating menu {self.title()}", pf.DEBUG.MENU)
        self.parent = parent
        if items:
            self.insertItems(items)
        if parent and isinstance(parent, BaseMenu):
            before = parent.action(before)
            parent.insert_menu(self, before)
        if callable(func):
            self.func = func
            self.triggered.connect(self.func)

    def insertItems(self, items, *, before=None):
        """Insert a list of items in the menu.

        Parameters
        ----------
        items: list
            A list of menuitem tuples. Each item is a tuple of two
            or three elements: (text, action, options):

            - text: the string that will be displayed in the menu.
              It can contain a '&' before the character that will be
              used as a hot key for navigating the menu with the keyboard.
              In lookup operations the string is normalized by removing
              any '&' characters and converting the text to lower case.

            - action: what to do when the menu item is selected.
              It can be any of the following:

              - None: a separator is inserted the items and it can not be
                selected itself.
              - list: the list should again be a list of menu items.
                A :class:`Menu` is created from it and treated as below.
              - :class:`Menu`: the menu will popup when the item is selected.
              - a Python function or instance method: the function is
                executed when the item is clicked. If `options` has a key
                `data`, its value will be passed as the single argument.
                Else, no argument is passed.
              - anything else will be stored as data in the action. This is
                useful in combination with a menuwide function `func`.

            - options: optional dictionary with following recognized keys:

              - 'icon': the name of an icon to be displayed with the item text.
                It should be one of the icons in the pyFormex
                configured icon dirs.
              - 'shortcut': an optional key combination to select the item.
              - 'tooltip': a help text to popup when the mouse is over the item.
              - 'checkable': if True, a item will present a check box.
              - 'checked': if True and checkable, the item's checkbox will
                initially be checked.
              - 'disabled': if True, the item will initially be disabled.
        before: str | QAction, optional
            If provided, the items will be inserted before the specified item.
            It should be the text *or* the action of one of the items already
            in self before this insert operation is started.

        """
        pf.debug(f"Inserting {len(items)} items in menu {self.title()}",
                 pf.DEBUG.MENU)
        before = self.action(before)
        for item in items:
            txt, val = item[:2]
            #pf.debug(f"Inserting {txt}: {val}", pf.DEBUG.MENU)
            if len(item) > 2:
                options = item[2]
            else:
                options = {}
            if  val is None:
                # separator
                a = self.insert_sep(before)
                a.setData(txt)  # Separators should have no text
            elif isinstance(val, list):
                # submenu
                func = options.get('func', None)
                a = Menu(txt, parent=self, before=before, func=func)
                a.insertItems(val)
            elif isinstance(val, BaseMenu):
                # also submenu
                self.insert_menu(val, before=before)
            else:
                # action
                if callable(val):
                    a = Action(txt, parent=self, func=val,
                               data=options.pop('data', None))
                    # function is executed when triggering the item
                    # if 'data' in options:
                    #     a = DAction(txt, parent=self, data = options.pop('data'))
                    #     a.signal.connect(val)
                    #     # elif 'args' in options:
                    # else:
                    # else:
                    #     a = QtWidgets.QAction(txt, parent=self)
                    #     a.triggered.connect(val)
                else:
                    # don't know what to do: just store it
                    a = QtWidgets.QAction(txt, parent=self)
                    a.setData(val)
                self.insert_action(a, before)
                for k, v in options.items():
                    if k == 'icon':
                        a.setIcon(QtGui.QIcon(QPixmap(utils.findIcon(v))))
                    elif k == 'shortcut':
                        a.setShortcut(v)
                    elif k == 'tooltip':
                        a.setToolTip(v)
                    elif k == 'checkable':
                        a.setCheckable(v)
                    elif k == 'checked':
                        a.setCheckable(True)
                        a.setChecked(v)
                    elif k == 'disabled':
                        a.setDisabled(True)

    # The need for the following functions demonstrates how much more
    # powerful a dynamically typed language as Python is as compared to
    # the C++ language used by Qt
    def insert_sep(self, before=None):
        """Create and insert a separator"""
        if before:
            return self.insertSeparator(before)
        else:
            return self.addSeparator()

    def insert_menu(self, menu, before=None):
        """Insert an existing menu."""
        if before:
            return self.insertMenu(before, menu)
        else:
            return self.addMenu(menu)

    def insert_action(self, action, before=None):
        """Insert an action."""
        if before:
            return self.insertAction(before, action)
        else:
            return self.addAction(action)

    def itemNames(self):
        """Return the list of normalized names of all items"""
        return [utils.strNorm(a.text()) for a in self.actions()]

    def menuNames(self):
        """Return the list of normalized names of the submenus"""
        return [utils.strNorm(a.text()) for a in self.actions() if a.menu()]

    def separators(self):
        """Return the list of separators"""
        return [a for a in self.actions() if a.isSeparator()]

    def index(self, text):
        """Return the index of the named item.

        Parameters
        ----------
        text: str
            The text of one of the items in the menu. Case is ignored and
            &'s are removed.

        Returns
        -------
        int:
            The index of the item in the menu, or -1 if there is no item with
            that name.
        """
        try:
            return self.itemNames().index(utils.strNorm(text))
        except ValueError:
            return -1

    def action(self, text):
        """Return the action with the specified text.

        Parameters
        ----------
        text: str
            The text of one of the items in the menu. Case is ignored and
            &'s are removed. A string like '---i' returns the i-th separator.

        Returns
        -------
        QAction | QSeparator
            The QAction or QSeparator with the specified text, or None.
            Note that Daction and submenu items are also QAction instances.

        See also
        --------
        item: like action, but returns a Menu for submenu items.
        """
        if isinstance(text, str):
            if text.startswith('---'):
                try:
                    i = int(text[3:])
                    return self.separators()[i]
                except (ValueError, IndexError):
                    return None
            i = self.index(text)
            if i >= 0:
                return self.actions()[i]
        elif isinstance(text, QtWidgets.QAction):
            return text
        return None

    def getItem(self, text):
        """Return the item with specified text.

        This is like :meth:`action`, but returns the Menu for submenu items.
        The same is also obtained by simply indexing the menu: menu[text].
        """
        a = self.action(text)
        if a:
            m = a.menu()
            if m:
                return m
            else:
                return a
        return None

    __getitem__ = getItem  # allow indexing to get an item

    def nextItem(self, item):
        """Returns the next item in the menu.

        This can be used to replace the current item with another menu
        or to reload a menu.

        Parameters
        ----------
        item: QAction | text
            One of the items in the menu. To get an item from its text,
            use :meth:`action`, not :meth:`getItem`.

        Returns
        -------
        QAction
            The next item in the Menu, or None if item was not in self.actions().
        """
        if isinstance(item, str):
            item = self.action(item)
        i = self.actions().index(item)
        if i >= 0 and i < len(self.actions())-1:
            return self.actions()[i+1]
        else:
            return None

    def removeItem(self, item):
        """Remove an item from this menu."""
        action = self.action(item)
        if action:
            self.removeAction(action)
            if isinstance(action, QtWidgets.QMenu):
                action.close()
                del action

    def report(self, recursive=False, prefix=''):
        """Return a report of the menu with the items and submenus.

        If recursive, also add report of the submenus.
        Beware: this may get huge
        """
        fullname = f"{prefix}{self.title()}"
        s = f"""\
=== MENU: {fullname} ===
ACTIONS: {self.itemNames()}
SUBMENUS: {self.menuNames()}
"""
        if recursive:
            for a in self.actions():
                m = a.menu()
                if isinstance(m, BaseMenu):
                    s += m.report(recursive=recursive, prefix=fullname+'/')
        return s


################################ Menu ##################################

class Menu(QtWidgets.QMenu, BaseMenu):
    """A popup/pulldown menu.

    Parameters
    ----------
    title: str
        The name of the menu.
    parent: QWidget, optional
        If parent is a QMenu, the Menu will automatically
        be inserted in the parent. If parent is pf.GUI, the menu is
        inserted in the main window's menu bar. If not provided,
        the menu is a standalone popup menu.
    before, items, func: see :class:`BaseMenu`
    tearoff: bool
        If True, the Menu can be teared of from its parent and used as
        a standalone popup menu.
    """

    def __init__(self, title='Menu', parent=None, before=None,
                 items=None, func=None, tearoff=False):
        """Initialize the Menu."""
        super().__init__(title, parent)
        BaseMenu.__init__(self, parent, before=before, items=items, func=func)
        if parent is None:
            self.setWindowFlags(QtCore.Qt.Dialog)
            self.setWindowTitle(title)
        else:
            if tearoff:
                print("TEAR OFF menus are experimental")
            self.setTearOffEnabled(tearoff)
        self.done = False

    def remove(self):
        """Close a Menu and remove it from its parent"""
        self.close()
        if self.parent:
            self.parent.removeItem(self.title())


    def toolbar(self, name):
        """Create a new toolbar corresponding to the menu."""
        # TODO: Fix this error!
        tb = QtWidgets.QToolBar(name)
        print(f"NEW TOOLBAR {nb}")
        for n in self.actions:
            print(f"ADDED ACTION {n}")
            self.toolbar.addAction(self.actions[a])
        return tb


################################ MenuBar ##################################

class MenuBar(QtWidgets.QMenuBar, BaseMenu):
    """A menu bar allowing easy menu creation.

    This can be set as the main window menubar using
    :meth:`QMainWindow.setMenuBar`.
    """

    def __init__(self, title='MenuBar', parent=None, before=None,
                 items=None, func=None):
        """Create the menubar."""
        super().__init__()
        self._title = title  # QMEnuBar does not have title
        BaseMenu.__init__(self, parent, before=before, items=items, func=func)

    def title(self):
        return self._title


###################### Action List #########################################


class Action(QtWidgets.QAction):
    """An Action is an executable menu item.

    The Action class provides some extra functionality over the default QAction.
    It can store an executable function and directly call it instead of using a
    signal. It can store any data and pass these data to the executed function.
    If the Action is inserted in a Menu that has its own executable function,
    that function can detect if the item has its own function and ignore it,
    or it can detect the stored data and act according to these data.
    An Action can be inserted in a Menu or in a Toolbar.

    Parameters
    ----------
    name: str
        The name of the item. In a Menu, this is the text displayed on the item.
        In a Toolbar the name may or may not be displayed. The name can be used
        to get the item from the Menu or Toolbar.
    parent: Menu
        The menu in which to insert the action. Inserting an item in a Menu
        makes sure the item is kept alive and selecting it will trigger the
        menu's function if it has one. The Action can be accessed as menu[name].
    icon: QICon | :term:`path_like`
        An icon for display in a Toolbar. It can be a QICon instance, or
        (more approperiately) the path to a file storing an image.
    func: callable
        If provided, the function is recorded in the Action and will be executed
        when the Action is triggered. The stored `data` will be passed as
        arguments. If an Action with a func is inserted in a Menu that has
        it's own executable function, it is often unwanted that both functions
        are executed. The menu function is passed the action as an argument
        and can detect that the action itself has a triggered executable from
        looking at ``action.func``.
    data:
        Anything passed as data will be stored in the Action. These data are
        passed as arguments to `func` when executed. Without a `func`, data
        are also often used together with a Menu function. The Menu function
        gets the action as an argument and has access to the action's data as
        ``action.data()``.

    Notes
    -----
    The user can identify an Action by its name or its icon. It is customary
    to display the name in menus, and show the icon in toolbars. This is the
    default in pyFormex. It is however possible to also add the icons in a menu
    or show the names in a toolbar, but it has to be explicitely set or
    configured.
    """
    def __init__(self, name, parent=None, icon=None, func=None, data=None):
        """Initialize the Action"""
        super().__init__(name, parent=parent)
        if icon:
            if not isinstance(icon, QtGui.QIcon):
                icon = Path(icon)
                if not icon.exists():
                    raise ValueError(f"Icon {icon} not found")
                icon = QtGui.QIcon(QPixmap(icon))
            self.setIcon(icon)
        if callable(func):
            self.func = func
            self.triggered.connect(self.execute)
        else:
            self.func = None
        if data:
            self.setData(data)

    def execute(self):
        """Execute the connected function"""
        args = self.data()
        if args is None:
            #print("EXECUTE FUNC WITHOUT ARGS")
            self.func()
        elif isinstance(args, tuple):
            #print(f"EXECUTE FUNC WITH ARGS {args}")
            self.func(*args)
        else:
            #print(f"EXECUTE FUNC WITH SINGLE ARG {args}")
            self.func(args)


class ActionList():
    """Menu and toolbar with named actions.

    An action list is a list of strings, each connected to some action.
    The actions can be presented in a menu and/or a toolbar.
    On activating one of the menu or toolbar buttons, a given signal is
    emitted with the button string as parameter. A fixed function can be
    connected to this signal to act dependent on the string value.
    """

    def __init__(self, actions=[], function=None, menu=None, toolbar=None,
                 icons=None, text=None):
        """Create an new action list, empty by default.

        A list of strings can be passed to initialize the actions.
        If a menu and/or toolbar are passed, a button is added to them
        for each string in the action list.
        If a function is passed, it will be called with the string as
        parameter when the item is triggered.

        If no icon names are specified, they are taken equal to the
        action names. Icons will be taken from the installed icon directory.
        If you want to specify other icons, use the add() method.
        """
        self.actions = {}
        self.function = function
        self.menu = menu
        self.toolbar = toolbar
        if icons is None:
            icons = actions
        icons = [utils.findIcon(i) for i in icons]
        if text is None:
            text = actions
        for name, icon, txt in zip(actions, icons, text):
            self.add(name, icon, txt)


    def add(self, name, icon=None, text=None):
        """Add a new name to the actions list and create a matching DAction.

        If the actions list has an associated menu or toolbar,
        a matching button will be inserted in each of these.
        If an icon is specified, it will be used on the menu and toolbar.
        The icon is either a filename or a QIcon object.
        If text is specified, it is displayed instead of the action's name.
        """
        if text is None:
            text = name
        a = Action(text, parent=self.menu, icon=icon, func=self.function, data=name)
        self.actions[name] = a
        if self.menu:
            self.menu.addAction(a)
        if self.toolbar:
            self.toolbar.addAction(a)


    def remove(self, name):
        """Remove an action by name"""
        if name in self.actions:
            action = self.actions[name]
            if self.menu:
                self.menu.removeAction(action)
            if self.toolbar:
                 self.toolbar.removeAction(action)
            del self.actions[name]


    def removeAll(self):
        """Remove all actions from self"""
        for name in self.names():
            self.remove(name)


    def names(self):
        """Return an ordered list of names of the action items."""
        return list(self.actions.keys())


    def toolbar(self, name):
        """Create a new toolbar corresponding to the menu."""
        # TODO: Fix this error!
        tb = QtWidgets.QToolBar(name)
        print(f"NEW TOOLBAR {nb}")
        for n in self.actions:
            print(f"ADDED ACTION {n}")
            self.toolbar.addAction(self.actions[a])
        return tb


# End
