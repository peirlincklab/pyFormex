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
"""pyFormex plugins initialisation.

This module contains the functions to detect and load the pyFormex
plugin menus.
"""
import sys
from types import ModuleType
import importlib

import pyformex as pf


class PluginMenu():
    """A registered reloadable plugin menu.

    A plugin menu is a Python module living in an accessible package.
    The default package is pyformex.plugins. The module should define
    a function ``create_menu(before='help')``. This function should create
    and return a :class:`Menu` created as follows::

        menu.Menu(name, menu_items, parent=pf.GUI.menu, before=before)

    Here ``name`` is the displayed menu name and menu_items is the list
    of items in the menu. The menu should be a child of the main pyFormex
    menu, and be inserted before the Help menu (or a preceding menu).

    The plugin module can also define a function ``on_reload()``. If so,
    this function will be called when the plugin is reloaded.

    The plugin menu should then be registered by creating a PluginMenu
    instance.

    Parameters
    ----------
    name: str
        The name of the menu. This is the name as appearing in the menu bar.
        This is normally a single short capitalized word. It should be
        different from all other plugin menus (unless you want to override
        another plugin with the same name).
    modname: str, optional
        The name of the module that contains the plugin menu.
        The default value is the name converted to lower case and with
        '_menu' appended.
    package: str, optional
        The dotted name of the package containing the plugin module.
        The default is 'pyformex.plugins'.
    """

    # The register is kept in order of registering
    _register_ = {}

    def __init__(self, name, modname=None, package='pyformex.plugins'):
        self.name = name
        self.modname = modname if modname else self.name.lower() + '_menu'
        self.pkg = package
        self.module = None  # not loaded
        self.__class__._register_[self.name] = self

    @property
    def fullname(self):
        return f"{self.pkg}.{self.modname}"

    @property
    def nicename(self):
        return self.name + ' Menu'

    def load(self):
        """Load the plugin menu"""
        importlib.import_module(self.fullname)
        module = self.module = sys.modules.get(self.fullname, None)
        if isinstance(module, ModuleType) and hasattr(module, 'create_menu'):
            self.show()

    def refresh(self):
        """Reload the plugin module"""
        importlib.import_module(self.fullname)
        module = self.module
        if isinstance(module, ModuleType) and hasattr(module, 'create_menu'):
            importlib.reload(module)
        else:
            pf.error("No such module: %s" % self.fullname)

    def show(self, before='help'):
        """Show the menu."""
        if self.module and not pf.GUI.menu[self.name]:
            self.menu = self.module.create_menu(before=before)
            self.menu.insertItems([
                ("Reload Menu", self.reload),
                ("Close Menu", self.close),
                ])

    def close(self):
        """Close the menu."""
        pf.GUI.menu.removeItem(self.name)

    def reload(self):
        """Reload the menu."""
        action = pf.GUI.menu.action(self.name)
        before = pf.GUI.menu.nextItem(action)
        self.close()
        self.refresh()
        try:
            self.module.on_reload()
        except:
            pass
        self.show(before=before)

    @classmethod
    def list(clas):
        """Return a list of registered plugin menus.

        Returns
        -------
        list of tuple
            A list of tuples (name, nicename), where name is the
            module name of the plugin and Nice Name is the beautified
            displayed name for user readability. Thus 'geometry_menu'
            can be displayed as 'Geometry Menu').
        """
        return [(m.name, m.nicename) for m in clas._register_.values()]

    # TODO: TEMPORARY
    @classmethod
    def get(clas, name):
        return clas._register_.get(name, None)

# Register the pyFormex plugin menus
PluginMenu('Geometry')
PluginMenu('Mesh')
PluginMenu('Surface')
PluginMenu('Tools')
PluginMenu('Draw2d')
PluginMenu('Nurbs')
PluginMenu('Dxf')
PluginMenu('Bifmesh')
PluginMenu('Jobs')
PluginMenu('Postproc')


def loadConfiguredPlugins(ok_plugins=None):
    """Load or unload plugin menus.

    Loads the specified plugins and unloads all others. If None
    specified, load the user configured plugins.
    """
    if ok_plugins is None:
        ok_plugins = pf.cfg['gui/pluginmenus']
        pf.debug("Configured plugins: %s" % ok_plugins, pf.DEBUG.PLUGIN)
    for p in PluginMenu._register_.values():
        pf.debug(f"Plugin menu: {p.name}", pf.DEBUG.PLUGIN)
        if p.name in ok_plugins:
            pf.debug("  Loading plugin menu: %s" % p, pf.DEBUG.PLUGIN)
            p.load()
        else:
            pf.debug("  Closing plugin menu: %s" % p, pf.DEBUG.PLUGIN)
            p.close()


# End
