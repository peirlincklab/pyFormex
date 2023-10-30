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
"""Basic pyFormex script functions

The :mod:`script` module provides the basic functions available
in all pyFormex scripts. These functions are available in GUI and NONGUI
applications, without the need to explicitely importing the :mod:`script`
module.
"""

import os
import sys
import time

import pyformex as pf
from pyformex import utils
from pyformex.path import Path
from pyformex.timer import Timer
from pyformex.geometry import Geometry


######################### Exceptions #########################################


class _Exit(Exception):
    """Exception raised to exit from a running script."""
    pass


_script_timer = Timer('_script_')

############################# Globals for scripts ############################


def Globals():
    """Return the globals that are passed to the scripts on execution.

    When running pyformex with the --nogui option, this contains all the
    globals defined in the module formex (which include those from
    coords, arraytools and numpy.

    When running with the GUI, this also includes the globals from gui.draw
    (including those from gui.color).

    Furthermore, the global variable __name__ will be set to either 'draw'
    or 'script' depending on whether the script was executed with the GUI
    or not.
    """
    # :DEV it is not a good idea to put the pf.PF in the globals(),
    # because pf.PF may contain keys that are not valid Python names
    g = {}
    g.update(globals())
    from pyformex import core
    g.update(core.__dict__)
    if pf.GUI:
        from pyformex.gui import draw
        g.update(draw.__dict__)
    # Set module correct
    if pf.GUI:
        modname = '__draw__'
    else:
        modname = '__script__'
    g['__name__'] = modname
    return g


def export(dic):
    """Export the variables in the given dictionary."""
    pf.PF.update(dic)


def export2(names, values):
    """Export a list of names and values."""
    export(list(zip(names, values)))


def forget(names):
    """Remove the global variables specified in list."""
    g = pf.PF
    for name in names:
        if name in g:
            del g[name]


def forgetAll():
    """Delete all the global variables."""
    pf.PF = {}


def rename(oldnames, newnames):
    """Rename the global variables in oldnames to newnames."""
    g = pf.PF
    for oldname, newname in zip(oldnames, newnames):
        if oldname in g:
            g[newname] = g[oldname]
            del g[oldname]


def listAll(clas=None, like=None, filtr=None, dic=None, sort=False):
    """Return a name list of objects that match the given criteria.

    Parameters
    ----------
    clas: class | list of classes
        If provided, only instances of these class(es) will be returned.
    like: str
        If provided, only object names starting with this string
        will be returned.
    filtr: func
        A function taking an object name as parameter and returning True
        or False. If specified, only object names returning True will be
        returned.
    dic: mapping
        A dictionary with strings as keys. Objects from this dict will
        be returned. The default is the pyFormex global dict: pf.PF.
    sort: bool
        If True, the returned list will be sorted.

    Returns
    -------
    list
        A list of keys from ``dic`` matching the criteria.

    Examples
    --------
    >>> from pyformex.core import Mesh, TriSurface
    >>> pf.PF.clear()
    >>> M = Mesh()
    >>> M1 = Mesh(eltype='tri3')
    >>> S = M1.toSurface()
    >>> F = S.toFormex()
    >>> export({'Mint':2, 'M':M, 'S':S, 'F':F, 'M1':M1})
    >>> listAll()
    ['Mint', 'M', 'S', 'F', 'M1']
    >>> listAll(clas=Mesh)
    ['M', 'S', 'M1']
    >>> listAll(clas=Mesh, filtr=lambda o: isinstance(pf.PF[o], TriSurface))
    ['S']
    >>> listAll(like='M')
    ['Mint', 'M', 'M1']
    """
    if dic is None:
        dic = pf.PF

    names = list(dic.keys())
    if clas is not None:
        names = [n for n in names if isinstance(dic[n], clas)]
    if like is not None:
        names = [n for n in names if n.startswith(like)]
    if filtr is not None:
        names = [n for n in names if filtr(n)]
    if sort:
        names = sorted(names)
    # TODO: can/should we return an iterator instead?
    return names


def named(name):
    """Returns the global object named name."""
    if name in pf.PF:
        dic = pf.PF
    else:
        raise NameError(f"Name {name} is not in pyformex.PF")
    return dic[name]


# TODO: can we do this with a returnNone default_factory in pf.refcfg?
def getcfg(name, default=None):
    """Return a value from the configuration or None if nonexistent."""
    try:
        return pf.cfg[name]
    except KeyError:
        return default


#################### Interacting with the user ###############################

def ask(question, choices=None, default=''):
    """Ask a question and present possible answers.

    If no choices are presented, anything will be accepted.
    Else, the question is repeated until one of the choices is selected.
    If a default is given and the value entered is empty, the default is
    substituted.
    Case is not significant, but choices are presented unchanged.
    If no choices are presented, the string typed by the user is returned.
    Else the return value is the lowest matching index of the users answer
    in the choices list. Thus, ask('Do you agree',['Y','n']) will return
    0 on either 'y' or 'Y' and 1 on either 'n' or 'N'.
    """
    if choices:
        question += f" ({', '.join(choices)}) "
        choices = [c.lower() for c in choices]
    while True:
        res = input(question)
        if res == '' and default:
            res = default
        if not choices:
            return res
        try:
            return choices.index(res.lower())
        except ValueError:
            pass


def ack(question):
    """Show a Yes/No question and return True/False depending on answer."""
    return ask(question, ['Y', 'N']) == 0


def error(message):
    """Show an error message and wait for user acknowlegement."""
    print("pyFormex Error: "+message)
    if not ack("Do you want to continue?"):
        exit()


def warning(message):
    print("pyFormex Warning: "+message)
    if not ack("Do you want to continue?"):
        exit()


def showInfo(message):
    print("pyFormex Info: "+message)


########################### PLAYING SCRIPTS ##############################

exitrequested = False
scriptInit = None  # can be set to execute something before each script


def playScript(scr, name=None, filename=None, argv=[], encoding=None):
    """Run a pyFormex script specified as text.

    Parameters
    ----------
    scr: str
        A multiline string holding a valid Python program, ususally a
        pyFormex script. The program will be executed in an internal
        interpreter, with the :func:`Globals` as local definitions.
        There is a lock to prevent multiple scripts from being executed
        at the same time. This implies that pyFormex scripts can not
        start another script.
    name: str, optional
        If specified, this name is set in the global variable pf.scriptName
        to identify the currently running script.
    filename: :term:`path_like`, optional
        If specified, this filename is set into the global variable __file__
        in the script executing environment.
    argv: list, optional
        This value is set in the global variable _argv_.
        It is mostly used to pass an argument list to the script in --nogui
        mode.
    encoding: str, optional
        If specified, this is an encoding scheme for the script text provided
        in ``scr``. The text will be decoded by the specified scheme prior to
        execution. This is mostly intended to obfuscate the code for
        occasional viewer.
    """
    global exitrequested

    # Scripts are not reentrant, so we only allow one running at a time!
    if len(pf.scriptlock) > 0:
        print("!!Not executing because a script lock has been set: "
              f"{pf.scriptlock}")
        return 1

    scriptLock('__auto/script__')
    exitrequested = False

    if pf.GUI:
        pf.GUI.startRun()

    # Get the globals
    g = Globals()
    if filename:
        g.update({'__file__': filename})
    g.update({'_argv_': argv})

    if encoding=='egg':
        import base64
        scr = base64.b64decode(scr)

    if isinstance(scr, bytes):
        scr = scr.decode('utf-8')

    # Now we can execute the script using these collected globals
    pf.scriptName = name
    exitall = False

    if pf.DEBUG.MEM in pf.options.debuglevel:
        # use a test to avoid evaluation of memUsed
        memu = utils.memUsed()
        pf.debug(f"MemUsed = {memu}", pf.DEBUG.MEM)

    if filename is None:
        filename = '<string>'

    # Execute the code
    try:
        pf.interpreter.locals.update(g)
        pf.interpreter.runsource(scr, str(filename), 'exec')

    except SystemExit:
        print("EXIT FROM SCRIPT")

    finally:
        # honour the exit function
        if 'atExit' in g:
            atExit = g['atExit']
            try:
                atExit()
            except Exception:
                pf.debug('Error while calling script exit function',
                         pf.DEBUG.SCRIPT)

        if pf.cfg['autoglobals']:
            if pf.GUI and pf.GUI.console:
                g = pf.GUI.console.interpreter.locals
            autoExport(g)
        scriptRelease('__auto/script__')  # release the lock
        if pf.GUI:
            pf.GUI.stopRun()

    if pf.DEBUG.MEM in pf.options.debuglevel:
        # use a test to avoid evaluation of memUsed
        pf.debug(f"MemUsed = {utils.memUsed()}", pf.DEBUG.MEM)
        pf.debug(f"Diff MemUsed = {utils.memUsed()-memu}; ", pf.DEBUG.MEM)

    if exitall:
        pf.debug("Calling quit() from playScript", pf.DEBUG.SCRIPT)
        quit()

    return 0


def runScript(fn, argv=[]):
    """Run a pyFormex script stored on a file.

    Parameters
    ----------
    fn: :term:`path_like`
        The name of a file holding a pyFormex script.
    argv: list, optional
        A list of arguments to be passed to the script. This argument list
        becomes available in the script as the global variable _argv_.

    Notes
    -----
    This calls :func:`playScript` to execute the code read from the script file.

    See Also
    --------
    runApp: run a pyFormex application
    runAny: run a pyFormex script or app
    """
    fn = Path(fn)
    msg = f"Running script ({fn})"
    if pf.GUI:
        pf.GUI.scripthistory.add(str(fn))
        pf.GUI.console.write(msg+'\n', color='red')
    else:
        print(msg)
    pf.debug(f"  Executing with arguments: {argv}", pf.DEBUG.SCRIPT)
    encoding = None

    with _script_timer:
        res = playScript(fn.read_text(), fn, fn, argv, encoding)
    msg = f"Finished script {fn} in {_script_timer.mem:.6f} seconds"
    if pf.GUI:
        pf.GUI.console.write(msg+'\n', color='red')
    else:
        print(msg)
    pf.debug(f"  Arguments left after execution: {argv}", pf.DEBUG.SCRIPT)
    return res


def runApp(appname, argv=[], refresh=False, lock=True, check=True, wait=False):
    """Run a pyFormex application.

    A pyFormex application is a Python module that can be loaded in
    pyFormex and at least contains a function 'run()'. Running the
    application means execute this function.

    Parameters
    ----------
    appname: str
        The name of the module in Python dot notation. The module should
        live in a path included in the 'appsdirs' configuration variable.
    argv: list, optional
        A list of arguments to be passed to the app. This argument list
        becomes available in the app as the global variable _argv_.
    refresh: bool
        If True, the app module will be reloaded before running it.
    lock: bool
        If True (default), the running of the app will be recorded so that
        other apps can be locked out while this one has not finished.
    check: bool
        If True (default), check that no other app is running at this time.
        If another app is running, either wait or return without executing.
    wait: bool
        If True, and check is True and another app is busy, wait until that
        one has finished and then start execution.

    Returns
    -------
    int
        The return value of the run function. A zero value is supposed
        to mean a normal exit.

    See Also
    --------
    runScript: run a pyFormex script
    runAny: run a pyFormex script or app
    """
    pf.debug(f"runApp '{appname}'", pf.DEBUG.APPS)
    global exitrequested
    if check:
        while len(pf.scriptlock) > 0:
            if wait:
                print(f"!!Waiting for lock {pf.scriptlock} to be released")
                time.sleep(5)
            else:
                print("!!Not executing because a script lock has been set: "
                      f"{pf.scriptlock}")
                return

    from pyformex import apps
    print(f"Loading application {appname} with refresh={refresh}")
    app = apps.load(appname, refresh=refresh)
    if app is None:
        errmsg = f"An error occurred while loading application {appname}"
        if apps._traceback and pf.cfg['showapploaderrors']:
            print(apps._traceback)
        if pf.GUI:
            from pyformex.gui import draw
            fn = apps.findAppSource(appname)
            if fn.exists():
                errmsg += ("\n\nYou may try executing the application "
                           "as a script,\n  or you can load the source "
                           "file in the editor.")
                res = draw.ask(errmsg, choices=[
                    'Run as script', 'Load in editor', "Don't bother"])
                if res[0] in 'RL':
                    if res[0] == 'L':
                        draw.editFile(fn)
                    elif res[0] == 'R':
                        pf.GUI.setcurfile(fn)
                        runScript(fn)
            else:
                errmsg += "and I can not find the application source file."
                draw.showError(errmsg)
        else:
            error(errmsg)

        return

    if hasattr(app, '_status') and app._status == 'unchecked':
        pf.warning(
            "This looks like an Example script that has been automatically "
            "converted to the pyFormex Application model, but has not been "
            "checked yet as to whether it is working correctly in App mode.\n"
            "You can help here by running and rerunning the example, checking "
            "that it works correctly, and where needed fixing it (or reporting "
            "the failure to us). If the example runs well, you can change its "
            "status to 'checked'")

    if lock:
        scriptLock('__auto/app__')
    msg = f"Running application '{appname}' from {app.__file__}"
    pf.scriptName = appname
    if pf.GUI:
        pf.GUI.startRun()
        pf.GUI.apphistory.add(appname)
        pf.GUI.console.write(msg+'\n', color='green')
    else:
        print(msg)
    pf.debug(f"  Passing arguments: {argv}", pf.DEBUG.SCRIPT)
    app._argv_ = argv
    try:
        try:
            with _script_timer:
                res = app.run()
        except SystemExit:
            print("EXIT FROM APP")
            # TODO: this can be removed?
            pass
        except Exception:  # TODO: this can be removed?
            raise
    finally:
        if hasattr(app, 'atExit'):
            app.atExit()
        if pf.cfg['autoglobals']:
            g = app.__dict__
            autoExport(g)
        if lock:
            scriptRelease('__auto/app__')  # release the lock
        if pf.GUI:
            pf.GUI.stopRun()
    pf.debug(f"  Arguments left after execution: {argv}", pf.DEBUG.SCRIPT)
    msg = f"Finished {appname} in {_script_timer.mem:.6f} seconds"
    if pf.GUI:
        pf.GUI.console.write(msg+'\n', color='green')
    else:
        print(msg)
    return res


def runAny(appname=None, argv=[], remember=True, refresh=False, wait=False):
    """Run a pyFormex application or script file.

    Parameters
    ----------
    appname: str
        Either the name of a pyFormex application (app) or the name of a file
        containing a pyFormex script. An app name is specified in Python
        fotted module format (pkg.module) and the path to the package
        should be in the configuration variable 'appsdirs'.
        If no appname is provided, the current app/script set in the GUI
        will be run, if it is set.
    argv: list, optional
        A list of arguments to be passed to the app. This argument list
        becomes available in the script or app as the global variable _argv_.
    remember: bool
        If True (default), the app is set as the current app in the GUI, so
        that the play button can be used to run it again.
    refresh, wait: bool
        Parameters passed to :func:`runApp`.

    See Also
    --------
    runScript: run a pyFormex script
    runApp: run a pyFormex application
    """
    if appname is None:
        appname = pf.cfg['curfile']
    if not appname:
        return

    if callable(scriptInit):
        scriptInit()

    if pf.GUI and remember:
        pf.GUI.setcurfile(appname)

    if utils.is_script(appname):
        return runScript(appname, argv)
    else:
        return runApp(appname, argv, refresh=refresh, wait=wait)


def autoExport(g):
    """Autoexport globals from script/app globals.

    Parameters
    ----------
    g: dict
        A dictionary holding definitions topossibly autoexport.
        Normally this is the globals dict from a script/app run enviroment.

    Notes
    -----
    This exports some objects from the script/app runtime globals
    to the pf.PF session globals directory.
    The default is to export all instances of :class:`Geometry`.

    This can be customized in the script/app by setting the global
    variables ``autoglobals`` and ``autoclasses``.
    If ``autoglobals`` evaluates to False, no autoexport will be done.
    If set to True, the default autoexport will be done: all instances
    of :class:`Geometry`. If set to a list of names, only the specified
    names will be exported.
    The global variable ``autoclasses`` may be set to a list of class
    names and all global instances of the specified classes
    will be exported.

    Remember that the variables need to be globals in your script/app
    in order to be autoexported, and that the autoglobals feature
    should not be disabled in your configuration (it is enabled by default).
    """
    ag = g.get('autoglobals', True)
    if ag:
        if ag is True:
            # default autoglobals: all Geometry instances
            ag = [Geometry]
        an = []
        for a in ag:
            if isinstance(a, str) and a in g:
                an.append(a)
            elif isinstance(a, type):
                try:
                    an.extend(listAll(clas=a, dic=g))
                except Exception:
                    pass
        if an:
            an = sorted(list(set(an)))
            print(f"Autoglobals: {', '.join(an)}")
            pf.PF.update([(k, g[k]) for k in an])


def scriptLock(id):
    global _run_mode
    if id == '__auto/script__':
        pf.scriptMode = 'script'
    elif id == '__auto/app__':
        pf.scriptMode = 'app'

    pf.debug(f"Setting script lock {id}", pf.DEBUG.SCRIPT)
    pf.scriptlock |= {id}


def scriptRelease(id):
    pf.debug(f"Releasing script lock {id}", pf.DEBUG.SCRIPT)
    pf.scriptlock -= {id}
    pf.scriptMode = None


def force_finish():
    pf.scriptlock = set()  # release all script locks (in case of an error)


def breakpt(msg=None):
    """Set a breakpoint where the script can be halted on a signal.

    If an argument is specified, it will be written to the message board.

    The exitrequested signal is usually emitted by pressing a button in the GUI.
    """
    global exitrequested
    if exitrequested:
        if msg is not None:
            print(msg)
        exitrequested = False  # reset for next time
        raise SystemExit


def raiseExit():
    pf.debug("RAISING SystemExit", pf.DEBUG.SCRIPT)
    if pf.GUI:
        pf.GUI.drawlock.release()
    raise _Exit("EXIT REQUESTED FROM SCRIPT")


def enableBreak(mode=True):
    if pf.GUI:
        pf.GUI.enableButtons(pf.GUI.actions, ['Stop'], mode)


def stopatbreakpt():
    """Set the exitrequested flag."""
    global exitrequested
    exitrequested = True


def exit(all=False):
    """Exit from the current script or from pyformex if no script running."""
    if len(pf.scriptlock) > 0:
        if all:
            utils.warn("warn_exit_all")
            pass
        else:
            # This is the only exception we can use in script mode
            # to stop the execution
            raise SystemExit


def quit():
    """Quit the pyFormex program

    This is a hard exit from pyFormex. It is normally not called
    directly, but results from an exit(True) call.
    """
    if pf.app and pf.app_started:  # quit the QT app
        pf.debug("draw.exit called while no script running", pf.DEBUG.SCRIPT)
        pf.app.quit()  # closes the GUI and exits pyformex
    else:  # the QT app didn't even start
        sys.exit(0)  # use Python to exit pyformex


def processArgs(args):
    """Run pyFormex scripts/apps in batch mode.

    Arguments are interpreted as names of script files, possibly interspersed
    with arguments for the scripts.
    Each running script should pop the required arguments from the list.
    """
    res = 0
    while len(args) > 0:
        pf.debug(f"Remaining args: {args}", pf.DEBUG.SCRIPT)
        fn = args.pop(0)
        if fn == '-c':
            # next arg is a script
            txt = args.pop(0)
        if '++' in args:
            # this is experimental and not documented
            i = args.index('++')
            argv = args[:i]
            args = args[i+1:]
        else:
            argv = args
        if fn == '-c':
            res = playScript(txt, name='__inline__', argv=argv)
        else:
            res = runAny(fn, argv=argv, remember=False)
        if res:
            print(f"Error during execution of script/app {fn}")
    return res


def setPrefs(res, save=False):
    """Update the current settings (store) with the values in res.

    res is a dictionary with configuration values.
    The current settings will be update with the values in res.

    If save is True, the changes will be stored to the user's
    configuration file.
    """
    pf.debug(f"Accepted settings:\n{res}", pf.DEBUG.CONFIG)
    for k in res:
        pf.cfg[k] = res[k]
        if save and pf.prefcfg[k] != pf.cfg[k]:
            pf.prefcfg[k] = pf.cfg[k]

    pf.debug(f"New settings:\n{pf.cfg}", pf.DEBUG.CONFIG)
    if save:
        pf.debug(f"New preferences:\n{pf.prefcfg}", pf.DEBUG.CONFIG)


########################## print information ################################


def printConfig():
    print("Reference Configuration: " + str(pf.refcfg))
    print("Preference Configuration: " + str(pf.prefcfg))
    print("User Configuration: " + str(pf.cfg))


def printLoadedApps():
    from pyformex import apps, sys
    loaded = apps.listLoaded()
    refcnt = [sys.getrefcount(sys.modules[k]) for k in loaded]
    print(', '.join([f"{k} ({r})" for k, r in zip(loaded, refcnt)]))


### Utilities


def chdir(path, create=False):
    """Change the current working directory.

    If path exists and it is a directory name, make it the current directory.
    If path exists and it is a file name, make the containing directory the
    current directory.
    If path does not exist and create is True, create the path and make it the
    current directory. If create is False, raise an Error.

    Parameters
    ----------
    path: :term:`path_like`
        The name of a directory or file. If it is a file, the name of
        the directory containing the file is used. If the path exists, it is
        made the current directory. The path can be an absolute
        or a relative pathname. A '~' character at the start of the pathname will
        be expanded to the user's home directory.
    create: bool.
        If True and the specified path does not exist, it will be created and
        made the current directory. The default (False) will do nothing if the
        specified path does not exist.

    Notes
    -----
    The new current directory is stored in the user's preferences file
    for persistence between pyFormex invocations.
    """
    path = Path(path).expanduser()
    if path.exists():
        if not path.is_dir():
            path = path.resolve().parent
    else:
        if create:
            mkdir(path)
        else:
            raise ValueError(f"The path {path} does not exist")
    try:
        os.chdir(str(path))
        setPrefs({'workdir': path}, save=True)
    except Exception:
        pass
    pwdir()
    if pf.GUI:
        pf.GUI.setcurdir()


def pwdir():
    """Print the current working directory.

    """
    print(f"Current workdir is {Path.cwd()}")


def mkdir(path, clear=False, new=False):
    """Create a directory.

    Create a directory, including any needed parent directories.
    Any part of the path may already exist.

    Parameters
    ----------
    path: :term:`path_like`
        The pathname of the directory to create, either an absolute
        or relative path. A '~' character at the start of the pathname will
        be expanded to the user's home directory.
    clear: bool.
        If True, and the directory already exists, its contents
        will be deleted.
    new: bool.
        If True, requires the directory to be a new one. An error
        will be raised if the path already exists.

    The following table gives an overview of the actions for different
    combinations of the parameters:

    ======  ====  ===================  =============
    clear   new   path does not exist  path exists
    ======  ====  ===================  =============
    F       F     newly created        kept as is
    T       F     newly created        emptied
    T/F     T     newly created        raise OSError
    ======  ====  ===================  =============

    Returns
    -------
    Path
        The tilde-expanded path of the directory, if the operation was
        successful.

    Raises
    ------
    OSError:
        in the following cases:

        - the directory could not be created,
        - ``clear=True``, and the existing directory could not be cleared,
        - ``new=False, clear=False``, and the existing path is not a directory,
        - ``new=True``, and the path exists.
    """
    path = Path(path).expanduser()
    if new and path.exists():
        raise OSError(f"Path already exists: {path}")
    if clear and path.exists():
        path.removeTree(top=not new)
    os.makedirs(path, exist_ok=not new)
    return path


def runtime():
    """Return the time elapsed since start of execution of the script."""
    return _script_timer.value()


def startGui():
    """Start the gui

    This can be used to start the gui when pyFormex was loaded from
    a Python shell.
    """
    if pf.GUI is None:
        pf.debug("Starting the pyFormex GUI", pf.DEBUG.GUI)
        from pyformex.gui import guimain
        guimain.createGUI()
    if pf.GUI:
        pf.GUI.run()
    del pf.GUI
    del pf.app
    pf.GUI = pf.app = None


#### End
