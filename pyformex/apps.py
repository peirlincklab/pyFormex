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
"""pyFormex application loading.

This module contains the functions used to detect and load the pyFormex
applications. pyFormex applications ('apps') are loaded as a Python
module. They contain a dedicated function 'run' that is executed when
the application is started. The application stays in memory, unless it
is explicitely unloaded.

This module contains functions to find, handle, list and (un)load
applications and manage application directories.
"""

import os
import sys
import importlib

import pyformex as pf
from pyformex import utils
from pyformex import Path


# global variable used for tracing application load errors
_traceback = ''


# def import_app(app):

# +if os.environ.get('PYFORMEX_IMPORTS', '') == 'T':
# +    import builtins
# +    orig_import = builtins.__import__
# +
# +    def my_import(arg0, *args, **kargs):
# +        if arg0.startswith('pyformex'):
# +            print(f"Importing {arg0}")
# +        return orig_import(arg0, *args, **kargs)
# +
# +    builtins.__import__ = my_import
# +


def guessDir(n, s):
    """ Guess the appdir from the name

    n: app name
    s: app path

    This works for dirs having a matching cfg['NAMEdir'] entry
    """
    return Path(s) if s else pf.cfg[f"{n.lower()}dir"]


class AppDir():
    """Application directory

    An AppDir is a directory containing pyFormex applications.
    When creating an AppDir, its path is added to sys.path
    """

    def __init__(self, path, name=None, create=True):
        path = guessDir(name, path)
        self.path = checkAppdir(path)
        if self.path is None:
            raise ValueError(f"Invalid application path {self.path}")

        # Add the parent path to sys.path if it is not there
        parent = self.path.parent
        self.added = parent not in sys.path
        if self.added:
            sys.path.insert(1, str(parent))

        self.pkg = self.path.name
        if name is None:
            self.name = self.pkg.capitalize()
        else:
            self.name = name
        pf.debug(f"Created {self}", pf.DEBUG.APPS)

    def __repr__(self):
        return f"AppDir {self.name} at {self.path} ({self.pkg})"


def setAppDirs():
    """Set the configured application directories"""
    # If this is a reset, first remove sys.path components
    if hasattr(pf, 'appdirs'):
        for p in pf.appdirs:
            if p.added:
                parent = str(p.path.parent)
                if parent in sys.path:
                    sys.path.remove(parent)
        print('SYSPATH IS NOW:', sys.path)

    pf.appdirs = []
    for p in pf.cfg['appdirs']:
        try:
            pf.appdirs.append(AppDir(p[1], p[0]))
        except Exception:
            # Silently skip invalid paths
            pf.debug(f"Invalid appdir path: {p}", pf.DEBUG.CONFIG)
    for p in pf.appdirs:
        pf.debug(str(p), pf.DEBUG.CONFIG)


def checkAppdir(d):
    """Check that a directory d can be used as a pyFormex application path.

    If the path does not exist, it is created.
    If no __init__.py exists, it is created.
    If __init__.py exists, it is not checked.

    If successful, returns the path, else None
    """
    d = Path(d)
    if not d.exists():
        try:
            os.makedirs(str(d))
        except Exception:
            pass

    initfile = d / '__init__.py'
    if not initfile.exists():
        try:
            with initfile.open('w') as f:
                f.write("""#
\"\"\"pyFormex application directory.

Do not remove this file. It is used by pyFormex to flag the parent
directory as a pyFormex application path.
\"\"\"
# End
""")
        except Exception:
            pass
    if initfile.exists():
        return d
    else:
        print(f"Invalid appdir {d}")
        return None


def findAppDir(path):
    """Return the AppDir for a given path"""
    for p in pf.appdirs:
        if p.path == path:
            return p


def load(appname, refresh=False, strict=False):
    """Load the named app

    If refresh is True, the module will be reloaded if it was already loaded
    before.
    On succes, returns the loaded module, else returns None.
    In the latter case, if the config variable apptraceback is True, the
    traceback is store in a module variable _traceback.
    """
    global _traceback
    if not appname:
        raise RuntimeError("No appname specified!")
    pf.debug(f"Loading {appname} with refresh={refresh}", pf.DEBUG.APPS)
    pf.logger.info(f"Loading application {appname}")
    try:
        _traceback = ''
        importlib.import_module(appname)
        app = sys.modules[appname]
        if refresh:
            importlib.reload(app)
        if strict:
            if not hasattr(app, 'run') or not callable(app.run):
                return None
        return app
    except Exception:
        import traceback
        _traceback = traceback.format_exc()
        return None


def findAppSource(app):
    """Find the source file of an application.

    app is either an imported application module (like: pkg.mod)
    or the corresponding application module name(like: 'pkg.mod').
    In the first case the name is extracted from the loaded module.
    In the second case an attempt is made to find the path that the module
    would be loaded from, without actually loading the module. This can
    be used to load the source file when the application can not be loaded.
    """
    from types import ModuleType
    if isinstance(app, (str, ModuleType)):
        path = utils.findModuleSource(app)
        if path:
            return Path(path)
        else:
            return None
    else:
        raise ValueError("app should be a module or a module name")


def unload(appname):
    """Try to unload an application"""
    name = 'apps.'+appname
    if name in sys.modules:
        app = sys.modules[name]
        refcnt = sys.getrefcount(app)
        if refcnt == 4:
            pf.debug(f"Unloading {name}", pf.DEBUG.APPS)
            del globals()[appname]
            del sys.modules[name]
            del app
        else:
            print(f"Can not unload {name}")
    else:
        print(f"Module {name} is not loaded")


def listLoaded(appsdir='appsdir'):
    """List the currently loaded apps

    Parameters
    ----------
    appsdir: str
        The base name of a directory registered as an application
        directory.

    Returns
    -------
    list of str
        A list with the currently loaded applications from the specified
        application directory.

    """
    return sorted([m for m in sys.modules if m.startswith(f"{appsdir}.")])


def detect(appdir):
    """Detect the apps present in the specified appdir.

    Parameters
    ----------
    appdir: :term:`path_like`
        Path to an appdir (i.e. a directory containing a file '__init__.py').

    Returns
    -------
    list of str
        A list with all the pyFormex apps in the specified appdir.
        If a file '.apps.dir' exists in the appdir, the returned list is the
        contents of that file. Otherwise the list contains all '.py' files
        in the directory, without the '.py' extension and sorted.

    Examples
    --------
    >>> 'RunAll' in detect(pf.cfg.appsdir)
    True
    """
    pf.debug(f"Detect apps in {appdir}", pf.DEBUG.APPS)
    # Detect, but do not load!!!!
    # because we are using this on import (before some applications can load)
    appdir = Path(appdir)
    appsdirfile = appdir / '.apps.dir'
    if appsdirfile.exists():
        pf.debug(f"Detect apps: read {appsdirfile}", pf.DEBUG.APPS)
        with appsdirfile.open('r') as fil:
            apps = fil.readlines()
            return [a.strip('\n').strip() for a in apps]
    else:
        pf.debug(f"Detect apps: scan {appdir}", pf.DEBUG.APPS)

        files = appdir.listTree(
            maxdepth=0, includefile=[r'.*[.]py$'])
        apps = [f.stem for f in files if f.stem[0] not in '._']
        apps = sorted(apps)
        pf.debug(f"{apps}", pf.DEBUG.APPS)
        return apps


# End
