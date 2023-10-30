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
"""Menu with pyFormex apps.

"""
import random

import pyformex as pf
from pyformex import Path
from pyformex import apps
from pyformex import utils
from pyformex import olist
from pyformex import script
from pyformex.gui import menu
from pyformex.gui import draw
from pyformex.gui.menus import Settings


catname = 'apps.cat'


def sortSets(d):
    """Turn the set values in d into sorted lists.

    - `d`: a Python dictionary

    All the values in the dictionary are checked. Those that are of type
    `set` are converted to a sorted list.
    """
    for k in d:
        if isinstance(d[k], set):
            d[k] = sorted(d[k])


def classify(appdir, pkg, nmax=0):
    """Classify the files in submenus according to keywords.

    """
    class failed():
        """A class to allow failing examples in the catalog"""
        pass

    all_apps = sorted(apps.detect(appdir))
    kat = ['byname', 'level', 'topics', 'techniques']
    cat = dict([(k, set()) for k in kat])
    cat['level'] = ['beginner', 'normal', 'advanced']
    print(cat)
    col = {}

    if nmax > 9:  # Do not exagerate!
        # split the full collection in alphabetical groups of length nmax
        lbl, grp = splitAlpha(all_apps, nmax)
        cat['byname'] = lbl
        for l, g in zip(lbl, grp):
            col['byname/'+l] = g

    for i, appname in enumerate(all_apps):

        #col['all'].update([appname])
        try:
            fullname = str(pkg)+'.'+appname
            app = apps.load(fullname, strict=True)
            if app is None:
                raise RuntimeError("App '%s' has no run method" % fullname)
        except Exception:
            app = failed
            print("Failed to load app '%s'" % fullname)

        for k in kat:
            if hasattr(app, '_'+k):
                v = getattr(app, '_'+k)
                if isinstance(v, list):
                    v = [vi.lower() for vi in v]
                else:
                    v = v.lower()
                if k in ['level']:
                    v = [v]
                else:
                    cat[k].update(v)
                for i in v:
                    ki = '%s/%s' % (k, i)
                    if ki not in col:
                        col[ki] = set()
                    col[ki].update([appname])

    sortSets(cat)
    sortSets(col)

    return all_apps, kat, cat, col


def splitAlpha(strings, n, ignorecase=True):
    """Split a series of strings in alphabetic collections.

    The strings are split over a series of bins in alphabetical order.
    Each bin can contain strings starting with multiple successive
    characters, but not more than n items. Items starting with the same
    character are always in the same bin. If any starting character
    occurs more than n times, the maximum will be exceeded.

    - `files`: a list of strings start with an upper case letter ('A'-'Z')
    - `n`: the desired maximum number of items in a bin.

    Returns: a tuple of

    - `labels`: a list of strings specifying the range of start characters
      (or the single start character) for the bins
    - `groups`: a list with the contents of the bins. Each item is a list
      of sorted strings starting with one of the characters in the
      corresponding label
    """
    from pyformex.arraytools import multiplicity
    if ignorecase:
        key = key=str.upper
    else:
        key = str
    strings = sorted(strings, key=key)
    mult, bins = multiplicity([ord(key(f[0])) for f in strings])
    count = dict(zip(bins, mult))
    cat = []
    grp = []

    def accept(i, j, mtot, skip):
        if not skip:
            if i == j:
                cat.append(chr(i))
            else:
                cat.append('%c-%c' % (chr(i), chr(j)))
            grp.append(strings[:mtot])
        del strings[:mtot]

    def group(fromchar, tochar, skip=False):
        """Take the group from fromchar to tochar, inclusive

        fromchar and tochar are characters
        """
        j = i = ord(fromchar)
        mtot = count.get(i, 0)
        while j < ord(tochar):
            if mtot > n:
                accept(i, j, mtot, skip)
                j = i = i+1
                mtot = count.get(i, 0)
            else:
                mj = count.get(j+1, 0)
                if mtot+mj > n:
                    accept(i, j, mtot, skip)
                    j = i = j+1
                    mtot = mj
                else:
                    j += 1
                    mtot += mj
        if mtot > 0:
            accept(i, j, mtot, skip)

    # The grouping has to start from char(0) and loop over all values!
    group(chr(0), chr(31), skip=True)
    group(' ', '@')
    group('A', 'Z')
    if not ignorecase:
        # we should skip the group between
        group('a', 'z')

    return cat, grp


class AppMenu(menu.Menu):
    """A menu of pyFormex applications in a directory or list.

    This class creates a menu of pyFormex applications or scripts
    collected from a directory or specified as a list of modules.
    It is used in the pyFormex GUI to create
    the examples menu, and for the apps history. The pyFormex apps
    can then be run from the menu or from the button toolbar.
    The user may use this class to add his own apps/scripts
    into the pyFormex GUI.

    Apps are simply Python modules that have a 'run' function.
    Only these modules will be added to the menu.
    Only files that are recognized by :func:`utils.is_pyFormex()` as being
    pyFormex scripts will be added to the menu.

    The constructor takes the following arguments:

    - `title`: the top level label for the menu
    - `dir`: an optional directory path. If specified, and no `files` argument
      is specified, all Python files in `dir` that do not start with either
      '.' or '_', will be considered for inclusion in the menu.
      If mode=='app', they will only be included if
      they can be loaded as a module. If mode=='script', they will only be
      included if they are considered a pyFormex script by utils.is_pyFormex.
      If `files` is specified, `dir` will just be prepended to each file in
      the list.
    - `files`: an explicit list of file names of pyFormex scripts.
      If no `dir` nor `ext` arguments are given, these should be the full path
      names to the script files. Otherwise, `dir` is prepended and `ext` is
      appended to each filename.
    - `ext`: an extension to be added to each filename. If `dir` was specified,
      the default extension is '.py'. If no `dir` was specified, the default
      extension is an empty string.
    - `recursive`: if True, a cascading menu of all pyFormex scripts in the
      directory and below will be constructed. If only `dir` and no `files`
      are specified, the default is True
    - `max`: if specified, the list of files will be truncated to this number
      of items. Adding more files to the menu will then be done at the top and
      the surplus number of files will be dropped from the bottom of the list.

    The defaults were thus chosen to be convenient for the three most frequent
    uses of this class::

      AppMenu('My Apps',dir="/path/to/my/appsdir")

    creates a menu with all pyFormex apps in the specified path and its
    subdirectories.

    ::

      ApptMenu('My Scripts',dir="/path/to/my/sciptsdir",mode='scripts')

    creates a menu with all pyFormex scripts in the specified path and its
    subdirectories.

    ::

      AppMenu('History',files=["/my/script1.py","/some/other/script.py"],\
          mode='script',recursive=False)

    is typically used to create a history menu of previously visited script
    files.

    With the resulting file list, a menu is created. Selecting a menu item
    will make the corresponding file the current script and unless the
    `autoplay` configuration variable was set to False, the script is executed.

    Furthermore, if the menu is a toplevel one, it will have the following
    extra options:

    - :menuselection:`Classify scripts`
    - :menuselection:`Remove catalog`
    - :menuselection:`Reload scripts`

    The first option uses the keyword specifications in the scripts docstring
    to make a classification of the scripts according to keywords.
    See the :func:`scriptKeywords()` function for more info. The second option
    removes the classification. Both options are especially useful for the
    pyFormex examples.

    The last option reloads a ScriptMenu. This can be used to update the menu
    when you created a new script file.
    """

    def __init__(self, title, dir=None, files=None, mode='app', ext=None,
                 recursive=None, max=0, autoplay=False, toplevel=True,
                 parent=None, before=None):
        """Create a menu with pyFormex apps/scripts to play."""
        pf.debug("New AppMenu %s: dir=%s; files=%s" % (title, dir, files),
                 pf.DEBUG.APPS)
        menu.Menu.__init__(self, title, parent=parent, before=before)
        if dir is None and files is None:
            raise ValueError("At least one of 'dir' or 'files' must be set.")
        if dir is not None:
            dir = Path(dir)
        self.dir = dir
        self.files = files
        self.my_actions = []
        self.mode = mode
        if ext is None and self.mode != 'app':
            if self.dir is None:
                ext = ''
            else:
                ext = '.py'
        self.ext = ext
        if recursive is None:
            recursive = True
        self.recursive = recursive and self.dir is not None
        self.toplevel = toplevel
        self.max = max
        self.autoplay = autoplay
        if self.dir and self.mode == 'app':
            self.pkg = self.dir.name
        else:
            self.pkg = None
        self.load()


    def loadCatalog(self):
        catfile = self.dir / catname
        if catfile.exists():
            utils.execFile(str(catfile), globals())
            for k in kat:
                if k == 'all_apps' and self.mode != 'app':
                    files = col[k]
                else:
                    files = []
                mk = AppMenu(k.capitalize(), dir=self.dir, files=files,
                             mode=self.mode, recursive=False, toplevel=False,
                             autoplay=self.autoplay, parent=self)
                for i in cat[k]:
                    if '-' in i:
                        # alpha label like A-B
                        lbl = i
                    else:
                        # string from catalog file
                        lbl = i.capitalize()
                    ki = '%s/%s' % (k, i)
                    mi = AppMenu(lbl, dir=self.dir, files=col.get(ki, []),
                                 mode=self.mode, recursive=False,
                                 toplevel=False, autoplay=self.autoplay,
                                 parent=mk)
            self.files = []
            return True
        return False


    def loadSubmenus(self, dirs=[]):
        if not dirs:
            dirs = self.dir.dirnames()
        for d in dirs:
            if d[0] not in '._':  # skip hidden and private dirs
                m = AppMenu(d, self.dir / d, mode=self.mode, ext=self.ext,
                            autoplay=self.autoplay, recursive=self.recursive,
                            parent=self)


    def getFiles(self):
        """Get a list of scripts in self.dir"""
        files = [f for f in self.dir.filenames() if f[0] not in '._']
        if self.ext:
            filtr = lambda s: s.endswith(self.ext)
            n = len(self.ext)
            files = [f[:-n] for f in files if filtr(f)]

        files = sorted(self.filterFiles(files))
        return files


    def filterFiles(self, files):
        """Filter a list of scripts"""
        filtr = lambda s: utils.is_pyFormex(self.fileName(s))
        files = [f for f in files if filtr(f)]

        if self.max > 0 and len(files) > self.max:
            files = files[:self.max]

        return files


    def loadFiles(self, files=None):
        """Load the app/script files in this menu"""
        if files is None:
            if self.mode == 'app':
                files = apps.detect(self.dir)
            else:
                files = self.getFiles()

        if self.mode != 'app':
            files = self.filterFiles(files)

        if self.max > 0 and len(files) > self.max:
            files = files[:self.max]

        self.files = files

        pf.debug("Found %ss in %s\n%s" % (self.mode.capitalize(), self.dir, self.files), pf.DEBUG.APPS)

        self.my_actions = [self.insert_action(str(f)) for f in self.files]
        self.triggered.connect(self.run)

        self.current = ""


    def load(self):
        if self.dir is None:
            self.loadFiles(self.files)

        else:
            if self.files is None:
                self.loadCatalog()

            if self.recursive:
                self.loadSubmenus()

            if self.files or self.files is None:
                self.loadFiles(self.files)

            if self.toplevel:
                self.insert_sep()
                self.addAction('Classify apps', self._classify)
                self.addAction('Remove catalog', self._unclassify)

                # Confined to 'app', crashes when applied on script
                if self.mode == 'app':
                    self.addAction('Reload apps', self.reload)


    def fileName(self, script):
        """Return the full pathname for a script."""
        fn = Path(script)
        if self.ext:
            fn = fn.with_suffix(self.ext)
        if self.dir:
            fn = self.dir / fn
        return fn


    def fullAppName(self, app):
        """Return the pkg.module name for an app."""
        if self.pkg:
            return "%s.%s" % (self.pkg, app)
        else:
            return app


    def listApps(self, recursive=True):
        """Returns the full AppNAme of all apps under this menu.

        The default recursive=True includes all apps under submenus as well.

        This is only for app mode menus!
        """
        files = [ self.fullAppName(f) for f in self.files]
        if recursive:
            for name in self.menuNames():
                files.extend(self[name].listApps(recursive=True))
        return files


    def run(self, action):
        """Run the selected app.

        This function is executed when the menu item is selected.
        """
        app = str(action.text())
        if app in self.files:
            self.runApp(app, play=self.autoplay)


    def runApp(self, app, play=True):
        """Set/Run the specified app.

        Set the specified app as the current app,
        and run it if play==True.
        """
        self.current = app
        #if self.mode != 'app':
        pf.GUI.setcurfile(app)
        if play:
            if self.mode == 'app':
                appname = self.fullAppName(app)
            else:
                appname = self.fileName(app)
            pf.debug("Running application %s" % appname, pf.DEBUG.APPS|pf.DEBUG.MENU)
            script.runAny(appname)


    def runAll(self, startfrom='A', stopat='[', count=-1, recursive=True,
               timeout=1.0, pause=1.0, random=False):
        """Run all apps with a name in the range [startfrom,stopat[.

        Runs the apps with a name >= `startfrom` and < `stopat`.
        The default will run all apps starting with a capital (like
        the examples). Specify None to disable the limit.
        If count is positive, at most count scripts are executed.
        If recursive is True, also the files in submenu are played.
        If random is True, the files in any submenu are shuffled before running.
        """
        from pyformex.gui.draw import layout, reset, sleep
        from pyformex.gui import widgets

        if self.mode != 'app':
            print("I can only do this in 'App' mode, not 'Script' mode")
            return

        print("%s, %s, %s" % (startfrom, stopat, count))

        pf.GUI.enableButtons(pf.GUI.actions, ['Stop'], True)

        files = self.files
        if startfrom is not None:
            files = [f for f in files if f >= startfrom]
        if stopat is not None:
            files = [f for f in files if f < stopat]
        if random:
            utils.shuffle(files)
        if count >= 0:
            files = files[:count]

        tcount = len(files)
        print("%s %s" % (tcount, files))

        if tcount > 0:
            # Run these files
            print("Running %s applications from '%s'" % (len(files), self.title()))
            print(files)
            pf.GUI.runallmode = True
            save = widgets.input_timeout
            pf.GUI.drawlock.free()
            widgets.input_timeout = timeout
            tcount = 0
            try:
                for f in files:
                    layout(1)
                    reset()
                    pf.PF.clear()
                    print("Running app '%s'" % f)
                    self.runApp(f)
                    script.breakpt(msg="Breakpoint from runall")
                    if script.exitrequested:
                        break
                    tcount += 1
                    sleep(pause)
            finally:
                widgets.input_timeout = save
                pf.GUI.drawlock.allow()
                pf.GUI.runallmode = False


        # if room for more, recurse into submenus
        if recursive and (count < 0 or tcount < count):
            for name in self.menuNames:
                n = self[name].runAll(startfrom, stopat, count=count-tcount,
                             recursive=recursive, random=random)
                tcount += n
                if count > 0 and tcount >= count:
                    print("Ran %s examples; getting out" % tcount)
                    break
                else:
                    print("Still want %s more examples" % (count-tcount))

        pf.GUI.enableButtons(pf.GUI.actions, ['Stop'], False)
        return tcount



    def reload(self):
        """Reload the scripts from dir.

        This is only available if a directory path was specified and
        no files.
        """
        pf.debug("Reloading this menu", pf.DEBUG.APPS)
        if self.dir:
            self.clear()
            self.files = None
            self.load()


    def add(self, name, strict=True, skipconfig=True):
        """Add a new filename to the front of the menu.

        This function is used to add app/scripts to the history menus.
        By default, only legal pyFormex apps or scripts can be added, and
        scripts from the user config will not be added.
        Setting strict and or skipconfig to False will skip the filter(s).
        """
        if strict:
            if self.mode == 'app':
                appname = self.fullAppName(name)
                app = apps.load(appname, strict=strict)
                if app is None:
                    print("%s is not a pyFormex app!" % appname)
                    return
            else:
                if not utils.is_pyFormex(name):
                    return
                if skipconfig:
                    # This is here to skip the startup script
                    if Path(name).resolve().parent == pf.cfg['userconfdir']:
                        return

        files = self.files
        olist.toFront(files, name)
        if self.max > 0 and len(files) > self.max:
            files = files[:self.max]
        while len(self.my_actions) < len(files):
            self.my_actions.append(self.addAction(str(name)))
        for a, f in zip(self.my_actions, self.files):
            a.setText(str(f))


    def _classify(self, nmax=20):
        """Classify, symlink and reload the scripts"""
        pf.debug("Classifying scripts", pf.DEBUG.APPS)
        if self.dir:
            fn = self.dir / catname
            all_apps, kat, cat, col = classify(self.dir, self.pkg, nmax)
            s = """# Do not edit this file! It was generated by %s.
#
all_apps = %r
#
kat = %r
#
cat = %r
#
col = %r
#
""" % (pf.fullVersion(), all_apps, kat, cat, col)
            with fn.open('w') as fil:
                fil.writelines(s)
            print("Created catalog %s" % fn)
            self.reload()


    def _unclassify(self):
        """Remove the catalog and reload the scripts unclassified"""
        if self.dir:
            fn = self.dir / catname
            if fn.exists():
                fn.unlink()
                self.reload()


############### The pyFormex App menu ############################

def unloadCurrentApp():
    appname = pf.cfg['curfile']
    from pyformex import apps
    apps.unload(appname)


def createAppMenu(mode='app', parent=None, before=None):
    """Create the menu(s) with pyFormex apps

    This creates a menu with all examples distributed with pyFormex.
    By default, this menu is put in the top menu bar with menu label 'Examples'.

    The user can add his own app directories through the configuration
    settings. In that case the 'Examples' menu and menus for all the
    configured app paths will be gathered in a top level popup menu labeled
    'Apps'.

    The menu will be placed in the top menu bar before the specified item.
    If a menu item named 'Examples' or 'Apps' already exists, it is
    replaced.
    """
    Mode = mode.capitalize()
    appmenu = menu.Menu('&%s'%Mode, parent=parent, before=before)
    appmenu.mode = mode
    if mode == 'app':
        appdirs = [(d.name, d.path) for d in pf.appdirs]
    else:
        appdirs = pf.cfg['scriptdirs']


    history = AppMenu('History', files=pf.cfg['gui/%shistory'%mode], max=pf.cfg['gui/history_max'], mode=mode, parent=appmenu)

    # Fill in missing default locations : this enables the user
    # to keep the pyFormex installed examples in his config
    appdirs = [(d[0], apps.guessDir(*d)) for d in appdirs]
    appdirs = [d for d in appdirs if d[1].exists() and d[1].is_dir()]
    for name, path in appdirs:
        pf.debug("Loading menu %s from %s" % (name, path), pf.DEBUG.MENU)
        m = AppMenu(name, path, mode=mode, autoplay=True, parent=appmenu)

    setattr(pf.GUI, f"{mode}history", history)

    appmenu.insertItems([
        ('---', None),
        (f'Show {Mode} Info', draw.showDoc),
        (f'Configure {Mode} Paths', Settings.setDirs, {'data': f'{mode}dirs'}),
        (f'Reload {Mode} Menu', reloadMenu, {'data': mode}),
        ])
    if mode == 'app':
        appmenu.insertItems([
            ('List loaded Apps', script.printLoadedApps),
            ('Unload Current App', unloadCurrentApp),
            ])
    if mode == 'script':
        appmenu.insertItems([
            ('Force Finish Script', script.force_finish),
        ])

    return appmenu


def reloadMenu(mode='app'):
    """Reload the named menu."""
    print(f"Reloading {mode}s")
    name = mode  # +'s'
    item = pf.GUI.menu.action(name)
    if item is not None:
        before = pf.GUI.menu.nextItem(item)
        print("ITEM BEFORE ",before)
        pf.GUI.menu.removeItem(item)
        if mode == 'app':
            # reset pf.appdirs, we may have configuration changes
            from pyformex import apps
            apps.setAppDirs()
        createAppMenu(mode, pf.GUI.menu, before)



# End
