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
"""Create 3D graphical representations.

The draw module provides the basic user interface to the OpenGL
rendering capabilities of pyFormex. The full contents of this module
is available to scripts running in the pyFormex GUI without the need
to import it.
"""
import sys
import textwrap

import numpy as np
from contextlib import contextmanager

import pyformex as pf
from pyformex import arraytools as at
from pyformex import process
from pyformex import utils
from pyformex import coords
from pyformex import Path
from pyformex import colors
from pyformex.attributes import Attributes
from pyformex.formex import Formex, connect
from pyformex.gui import dialogs
from pyformex.gui import widgets
from pyformex.gui import QtCore
from pyformex.gui import toolbar
from pyformex.gui import image
from pyformex.gui import drawlock
from pyformex.opengl import actors, decors, camera

# Extra things that we want in the scripting language
from pyformex import print_err
from pyformex.script import *
from pyformex.core import *
from pyformex.colors import *
from pyformex.gui.widgets import Dialog, _I, _C, _G, _T
from pyformex.gui.toolbar import timeout
from pyformex.gui import image
from pyformex.gui import views


#################### Interacting with the user ###############################


@contextmanager
def busyCursor():
    pf.app.setOverrideCursor(QtCore.Qt.WaitCursor)
    try:
        yield pf.app.overrideCursor()
    finally:
        pf.app.restoreOverrideCursor()
        pf.app.processEvents()


def exitGui(res=0):
    """Terminate the GUI with a given status.

    """
    print(f"Terminating the GUI with a value {res}")
    pf.app.closeAllWindows()
    pf.app.exit(res)


def closeGui():
    """Close the GUI.

    Calling this function from a script closes the GUI and terminates
    pyFormex.
    """
    pf.debug("Closing the GUI: currently, this will also terminate pyformex.", pf.DEBUG.GUI)
    pf.GUI.close()


def closeDialog(name):
    """Close the named dialog.

    Closes the Dialog with the given name. If multiple dialogs are
    open with the same name, all these dialogs are closed.

    This only works for dialogs owned by the pyFormex GUI.
    """
    pf.GUI.closeDialog(name)


def showMessage(text, actions=['OK'], level='info', modal=True, align='00', **kargs):
    """Show a short message widget and wait for user acknowledgement.

    There are three levels of messages: 'info', 'warning' and 'error'.
    They differ only in the icon that is shown next to the test.
    By default, the message widget has a single button with the text 'OK'.
    The dialog is closed if the user clicks a button.
    The return value is the button text.
    """
    w = widgets.MessageBox(text, level=level, actions=actions, **kargs)
    if align == '--':
        w.move(100, 100)
    if modal:
        return w.getResults()


def showInfo(text, actions=['OK'], modal=True, **kargs):
    """Show an informational message and wait for user acknowledgement."""
    return showMessage(text, actions, 'info', modal, **kargs)

def showWarning(text, actions=['OK'], **kargs):
    """Show a warning message and wait for user acknowledgement."""
    return showMessage(text, actions, 'warning', **kargs)

def showError(text, actions=['OK'], **kargs):
    """Show an error message and wait for user acknowledgement."""
    return showMessage(text, actions, 'error', **kargs)

#@utils.deprecated_by('draw.warning', 'draw.showWarning')
def warning(*args, **kargs):
    showWarning(*args, **kargs)

#@utils.deprecated_by('draw.error', 'draw.showError')
def error(*args, **kargs):
    showError(*args, **kargs)


def ask(question, choices=None, **kargs):
    """Ask a question and present possible answers.

    Return answer if accepted or default if rejected.
    The remaining arguments are passed to :func:`showMessage`.
    """
    return showMessage(question, choices, 'question', **kargs)


def ack(question, **kargs):
    """Show a Yes/No question and return True/False depending on answer."""
    return ask(question, ['Yes', 'No'], **kargs) == 'Yes'


def showText(text, itemtype='text', actions=[('OK',)], modal=True,
             mono=False):
    """Display a text in a dialog window.

    Creates a dialog window displaying some text. The dialog can be modal
    (blocking user input to the main window) or modeless.
    Scrollbars are added if the text is too large to display at once.
    By default, the dialog has a single button to close the dialog.

    Parameters
    ----------
    text: str
        A multiline text to be displayed. It can be plain text or html
        or reStructuredText (starting with '..').
    itemtype: str
        An :Class:`InputItem` type that can be used for text display.
        Currently this should be either 'text' of 'info'.
    actions: list
        A list of action button definitions.
    modal: bool
        If True, a modal dialog is constructed. Else, the dialog is modeless.
    mono: bool
        If True, a monospace font will be used. This is only useful for
        plain text, e.g. to show the output of an external command.

    Returns
    -------
    If modal is True, the result of the dialog after closing.
    This is a dictionary with a single key: 'text' having the
    displayed text as a value. If an itemtype 'text' was used, it may
    be a changed text.

    If modal is False, return the open dialog window.
    """
    if mono:
        font = "DejaVu Sans Mono"
    else:
        font = "DejaVu Sans"
    w = Dialog(size=(0.75, 0.75),
        items=[_I('text', text, itemtype=itemtype, text='', font=font, size=(-1, -1))],
        modal=modal,
        actions=actions,
        caption='pyFormex Text Display',
        )
    if modal:
        return w.getResults()
    else:
        w.show()
        return w


def showFile(filename, mono=None, **kargs):
    """Display a text file.

    Uses the :func:`showText()` function to display a text read
    from a file.
    By default this uses a monospaced font.
    Other arguments may also be passed to ShowText.
    """
    try:
        with open(filename, 'r') as fil:
            if mono is None:
                mono = not filename.endswith('.rst')
            showText(fil.read(), mono=mono, **kargs)
    except IOError:
        print(f"Could not read file '{filename}'")


def showURL(url):
    """Show an URL in the browser.

    Parameters
    ----------
    url: URL
        The URL to be shown in the browser. The URL is checked with
        :func:`utils.okURL`. If this returns True, it is passed
        as parameter to the command configured in pf.cfg['browser'],
        which is executed as an external command without
        waiting for its result. Else, nothing is done.

    Returns
    -------
    bool
        True if ``url`` was actually passed to the browser command,
        False if not.
    """
    ok = utils.okURL(url)
    if ok:
        cmd = pf.cfg['browser']
        utils.system([cmd, url], wait=False)
    return ok


utils.deprecated_by('showHTML', 'showHtml')  # release 3.1
def showHTML(fn=None):
    return showHtml(fn, server=False)


def showHtml(path=None, http=True):
    """Show a local html file in the browser.

    Parameters
    ----------
    path: :term:`path_like`
        The path of the file to be displayed. This is normally a
        file with suffix .html. If not provided, a dialog is popped up
        to ask the user for a filename.
    http: bool
        If True (default) a local web server is created to serve the file's
        directory over http: protocol to the browser.
        If False, the file is directly served to the browser using the
        file: protocol.

    Notes
    -----
    Modern browsers with stricter security settings do not allow to include
    files (especially scripts) in the document that are coming from another
    origin. And with the file: protocol any other file, even in the same
    directory is considered another origin. Therefore the use of a web server
    and the http protocal is recommended and set as the default.

    The browser command is configurable in the settings.
    """
    if path is None:
        path = askFilename(filter='html')
    if path:
        if http:
            from pyformex.plugins.http_server import showHtml
            showHtml(path)
        else:
            showURL(f"file:{path}")


def showDoc(obj=None, rst=True, modal=False):
    """Show the docstring of an object.

    Parameters
    ----------
    obj: object
        Any object (module, class, method, function) that has a
        __doc__ attribute. If not provided, the docstring of the current
        script/app is shown.
    rst: bool.
        If True (default) the docstring is treated as being
        reStructuredText and will be nicely formatted accordingly.
        If False, the docstring is shown as plain text.
    """
    text = None
    if obj is None:
        if not pf.GUI.canPlay:
            return
        obj = pf.prefcfg['curfile']
        if utils.is_script(obj):
            #print "obj is a script"
            from pyformex.utils import getDocString
            text = getDocString(obj)
            obj = None
        else:
            from pyformex import apps
            obj = apps.load(obj)

    if obj:
        text = obj.__doc__

    if text is None:
        raise ValueError("No documentation found for object %s" % obj)

    text = utils.forceReST(text, underline=True)
    if pf.GUI.doc_dialog is None:
        if modal:
            actions=[('OK', None)]
        else:
            actions = [('Close', pf.GUI.close_doc_dialog)]
        pf.GUI.doc_dialog = showText(text, actions=actions, modal=modal)
    else:
        #
        # TODO: check why needed: without sometimes fails
        # RuntimeError: wrapped C/C++ object of %S has been deleted
        # probably when runall?
        #
        try:
            pf.GUI.doc_dialog.updateData({'text': text})
            # pf.GUI.doc_dialog.show()
            pf.GUI.doc_dialog.raise_()
            pf.GUI.doc_dialog.update()
            pf.app.processEvents()
        except Exception:
            pass


def editFile(fn, exist=False):
    """Load a file into the editor.

    Parameters:

    - `fn`: filename. The corresponding file is loaded into the editor.
    - `exist`: bool. If True, only existing filenames will be accepted.

    Loading a file in the editor is done by executing an external command with
    the filename as argument. The command to be used can be set in the
    configuration. If none is set, pyFormex will try to lok at the `EDITOR`
    and `VISUAL` environment settings.

    The main author of pyFormex uses 'emacsclient' as editor command,
    to load the files in a running copy of Emacs.
    """
    print("Edit File: %s" % fn)
    if pf.cfg['editor']:
        fn = Path(fn)
        if exist and not fn.exists():
            return
        process.run([pf.cfg['editor'], fn], wait=False)
    else:
        warning('No known editor was found or configured')


# widget and result status of the widget in askItems() function
_dialog_widget = None
_dialog_result = None

def askItems(items, *, modal=True, timeout=None, timeoutfunc=None, **kargs):
    """Ask the value of some items to the user.

    Create an interactive widget to let the user set the value of some items.
    The items are specified as a list of dictionaries. Each dictionary
    contains the input arguments for a widgets.InputItem. It is often
    convenient to use one of the _I, _G, ot _T functions to create these
    dictionaries. These will respectively create the input for a
    simpleInputItem, a groupInputItem or a tabInputItem.

    For convenience, simple items can also be specified as a tuple.
    A tuple (key,value) will be transformed to a dict
    {'key':key, 'value':value}.

    See :class:`widgets.Dialog` and :`widgets.InputItem` for a more
    comprehensive description of the available arguments.

    A timeout (in seconds) can be specified to have the input dialog
    interrupted automatically and return the default values.

    Also a timeoutfunc can be provided: it will be executed when the
    dialog times out.

    The remaining arguments are keyword arguments that are passed to the
    widgets.Dialog.getResult method.

    Returns a dictionary with the results: for each input item there is a
    (key,value) pair. Returns an empty dictionary if the dialog was canceled.
    Sets the dialog timeout and accepted status in global variables.
    """
    global _dialog_widget, _dialog_result

    w = widgets.Dialog(items, **kargs)
    _dialog_widget = w
    _dialog_result = None
    res = w.getResults(modal=modal, timeout=timeout, timeoutfunc=timeoutfunc)
    _dialog_widget = None
    # The dialog result is currently not available
    #_dialog_result = w.closure
    return res


def currentDialog():
    """Returns the current dialog widget.

    This returns the dialog widget created by the askItems() function,
    while the dialog is still active. If no askItems() has been called
    or if the user already closed the dialog, None is returned.
    """
    return _dialog_widget


def selectItems(choices, caption='Select from list', default=[], single=False,
                check=False, sort=False, **kargs):
     """Ask the user to select one or more items from a list.

     This is a convenience function presenting a dialog with a single
     input item: an InputList. It allows the user to select one or more items
     from a list.

     Returns
     -------
     list
         A list with the selected items
     """
     res = askItems([
         _I(name='input', value=default, itemtype='select', choices=choices,
            text='', single=single, check=check, sort=sort, **kargs),
     ], caption=caption)
     res = res['input'] if res else []
     if sort:
         res.sort()
     return res


def askFile(path=None, filter='all', *, mode='file', compr=False,
            timeout=None, caption=None, sidebar=None, extra=[], **kargs):
    """Ask for one or more files using a customized file dialog.

    Shows a modal :class:`FileDialog` and allows the user to select file(s)
    according to the parameters. See the :class:`FileDialog` for the meaning
    of the parameters. The timeout parameter is passed to
    :meth:`FileDialog.getresults`.

    Returns
    -------
    dict
        A dict with the results of the :class:`FileDialog`. If the user
        canceled the selection process, the dict is empty.
        If the user accepted the selection, the dict has at least a key
        'filename' with the selection: a single Path, except for 'multi'
        mode, which returns a list of Path.
        More keys are present if the dialog contains more input items,
        either specified in the extra argument, or forced by some specific
        filter.
    """
    if filter == 'pgf':
        _Dialog = dialogs.GeometryFileDialog
    else:
        _Dialog = dialogs.FileDialog
        kargs['extra'] = extra
    w = _Dialog(path, filter, mode=mode, compr=compr,
                caption=caption, sidebar=sidebar, **kargs)
    res = w.getResults(timeout=timeout)
    pf.GUI.update()
    pf.app.processEvents()
    return res


def askFilename(*args, **kargs):
    """Ask for a file name or multiple file names using a file dialog.

    Parameters
    ----------
    cur: :term:`path_like`
        Path of the starting point of the selection dialog. It can be a
        directory or a file. All the files in the provided directory (or the
        file's parent) that match the ``filter`` will be initially presented
        to the user. If ``cur`` is a file, it will be set as the initial
        selection.
    filter: str or list of str
        Specifies a (set of) filter(s) to be applied on the files in the
        selected directory. This allows to narrow down the selection
        possibilities. The ``filter`` argument is passed
        through the :func:`utils.fileDescription` function to create the
        actual filter set. If multiple filters are included, the user can
        switch between them in the dialog.
    mode: str
        Determines what can be selected. One of:

        - 'file': select a file (existing or not). This is the default.
        - 'exist': select an existing file
        - 'dir': select an existing directory (widget allows to create a new)
        - 'any': select a file (existing or not) or a directory
        - 'multi': select multiple existing paths from the same directory
    compr: bool
        If True, the specified filter pattern will be extended with
        the corresponding compressed file types. For example, a filter
        for '.pgf' files will also allow to pick '.pgf.gz' or '.pgf.bz2'
        files.
    change: bool
        If True (default), the current working directory will be changed to
        the parent directory of the selection.
    caption: str
        A string to be displayed as the dialog title instead of the
        default one.
    timeout: float
        If provided, the dialog will timeout after the specified number
        of seconds.
    sidebar: list of path_like.
        If provided, these will be added to the sidebar (in addition to
        the configured paths).
    kargs: keyword arguments
        More arguments to be passed to the FileDialog.

    Returns
    -------
    Path | list of Paths | None
        The selected file Path(s) if the user accepted the dialog, or None
        if the user canceled the dialog.
    """
    for key in ['exist', 'multi']:
        if key in kargs:
            utils.warn('depr_filemode')
            if kargs[key]:
                kargs['mode'] = key
            del kargs[key]
    res = askFile(*args, **kargs)
    if res:
        return res['filename']
    else:
        return None


def askNewFilename(cur=None, filter="All files (*.*)", compr=False,
                   timeout=None, caption=None, sidebar=None, **kargs):
    """Ask a single new filename.

    This is a convenience function for calling askFilename with the
    argument exist=False.
    """
    return askFilename(cur=cur, filter=filter, mode='file',
                       compr=compr, timeout=timeout, caption=caption,
                       sidebar=sidebar, **kargs)


def askDirname(path=None, change=True, byfile=False, **kargs):
    """Interactively select a directory and change the current workdir.

    The user is asked to select a directory through the standard file
    dialog. Initially, the dialog shows all the subdirectories in the
    specified path, or by default in the current working directory.

    The selected directory becomes the new working directory, unless the
    user canceled the operation, or the change parameter was set to False.
    """
    # if path is None:
    #     path = pf.cfg['workdir']
    # path = Path(path)
    # if not path.is_dir():
    #     path = path.parent
    mode = 'any' if byfile else 'dir'
    w = dialogs.FileDialog(
        path, filter='*', mode=mode, chdir=None, **kargs)
    res = w.getResults()
    if res:
        dirname = res['filename']
        if not dirname.is_dir():
            dirname = dirname.parent
        if change:
            chdir(dirname)
    else:
        dirname = None
    pf.GUI.update()
    pf.app.processEvents()
    return dirname


def askImageFile(fn=None, compr=False):
    if not fn:
        fn = pf.cfg['pyformexdir']
    return askFilename(fn, filter=['img', 'all'], mode='exist')


def checkWorkdir():
    """Ask the user to change the current workdir if it is not writable.

    Returns True if the current workdir is writable.
    """
    try:
        tmpfile = utils.TempFile(dir='.')
    except (FileNotFoundError, PermissionError):
        warning(
            f"Your current working directory {pf.cfg['workdir']} does not exist "
            f"or is not writable. Change your working directory to an "
            f"existing path where you have write permission.")
        askDirname()   # this also changes the current workdir
        try:
            tmpfile = utils.TempFile(dir='.')
        except (FileNotFoundError, PermissionError):
            return False
    return True


logfile = None     # the log file


def printc(*args, color=None, sep=' ', end='\n'):
    """Print in color to the console.

    Parameters
    ----------
    *args:
        The things to be printed. Every argument is converted to a string
        using :func:`str`. The strings are joined using the separator `sep`
        and the end separator `end` is appended. The resulting string is
        printed to the console with the specified `color`.
    color: int | color_like
        The color to use when displaying the string. It can be anything that
        is accepted by QColor or an int. If an int, it is used as index in the
        current palette: `pf.canvas.settings.colormap`.
    sep: str
        The separator between printed items in a single call.
    end: str
        The separator added at the end of each call.
    """
    if isinstance(color, int):
        colormap = pf.canvas.settings.colormap
        color = tuple(colormap[color % len(colormap)])
    pf.GUI.console.writecolor(sep.join(str(a) for a in args) + end, color=color)
    pf.GUI.update()
    pf.app.processEvents()

# compatibility
printMessage = printc


def delay(s=None):
    """Get/Set the draw delay time.

    Returns the current setting of the draw wait time (in seconds).
    This drawing delay is obeyed by drawing and viewing operations.

    A parameter may be given to set the delay time to a new value.
    It should be convertable to a float.
    The function still returns the old setting. This may be practical
    to save that value to restore it later.
    """
    saved = pf.GUI.drawwait
    if s is not None:
        pf.GUI.drawwait = float(s) if not pf.GUI.runallmode else 0.1
    return saved


def wait(relock=True):
    """Wait until the drawing lock is released.

    This uses the drawing lock mechanism to pause. The drawing lock
    ensures that subsequent draws are retarded to give the user the time
    to view. The use of this function is prefered over that of
    :func:`pause` or :func:`sleep`, because it allows your script to
    continue the numerical computations while waiting to draw the next
    screen.

    This function can be used to retard other functions than `draw` and `view`.
    """
    pf.GUI.drawlock.wait()
    if relock:
        pf.GUI.drawlock.lock()


# Functions corresponding with control buttons

def play(refresh=False):
    """Start the current script or if already running, continue it.

    """
    if len(pf.scriptlock) > 0:
        # An application is running
        if pf.GUI.drawlock.locked:
            pf.GUI.drawlock.release()

    else:
        # Start current application
        runAny(refresh=refresh)


def replay():
    """Replay the current app.

    This works pretty much like the play() function, but will
    reload the current application prior to running it.
    This function is especially interesting during development
    of an application.
    If the current application is a script, then it is equivalent with
    play().
    """
    appname = pf.cfg['curfile']
    play(refresh=utils.is_app(appname))



def fforward():
    """Releases the drawing lock mechanism indefinely.

    Releasing the drawing lock indefinely means that the lock will not
    be set again and your script will execute till the end.
    """
    pf.GUI.drawlock.free()


#
# IDEA: The pause() could display a progress bar showing how much time
# is left in the pause,
# maybe also with buttons to repeat, pause indefinitely, ...
#
def pause(timeout=None, msg=None):
    """Pause the execution until an external event occurs or timeout.

    When the pause statement is executed, execution of the pyformex script
    is suspended until some external event forces it to proceed again.
    Clicking the PLAY, STEP or CONTINUE button will produce such an event.

    - `timeout`: float: if specified, the pause will only last for this
      many seconds. It can still be interrupted by the STEP buttons.

    - `msg`: string: a message to write to the board to explain the user
      about the pause
    """
    def _continue_():
        return not pf.GUI.drawlock.locked

    if msg is None and timeout is None:
        msg = "Use the Play/Step/Continue button to proceed"

    pf.debug("Pause (%s): %s" % (timeout, msg), pf.DEBUG.SCRIPT)
    if msg:
        print(msg)

    pf.GUI.enableButtons(pf.GUI.actions, ['Step', 'Continue'], True)
    pf.GUI.drawlock.release()
    if pf.GUI.drawlock.allowed:
        pf.GUI.drawlock.locked = True
    if timeout is None:
        timeout = widgets.input_timeout
    R = drawlock.Repeater(_continue_, timeout, sleep=0.1)
    R.start()
    pf.GUI.drawlock.release()


def sleep(duration, granularity=0.01, func=None):
    """Hold execution for some duration

    This holds the execution of the thread where the function is
    called for the specified time (in seconds).

    See also
    --------
    `delay`

    Notes
    -----
    Because of the setup of the operation, in case of very small duration
    times the actual duration may be considerably longer than the specified
    value.
    If the sleep is intended to slow down drawing instructions, you may
    consider the use of :func:`delay`. Even if you do not have a draw function
    in the block you want to delay, a :func:`view` function could be added
    to apply the delay.
    Normally you should set granularity < duration.
    """
    if duration > 0:
        granularity = min(granularity,duration)
    R = drawlock.Repeater(func, duration=duration, sleep=granularity)
    R.start()


def do_after(sec, func):
    """Call a function in another thread after a specified elapsed time.

    Parameters
    ----------
    sec: float
        Time in seconds to wait before starting the execution.
        As the function will be executed in a separate thread,
        the calling thread will immediately continue.
    func: callable
        The function (or bound method) to be called.
    """
    import threading
    t = threading.Timer(sec, func)
    t.start()
    pf.logger.info("Started timer for %s: %s" % (sec, func))


def monitor_qt(P, check=False):
    """Monitor a subprocess without blocking the GUI"""
    import subprocess
    poll_timer = QtCore.QThread
    with P:
        try:
            # Make sure qt app can continue
            while P.poll() is None:
                pf.app.processEvents()
                poll_timer.msleep(20)
            stdout, stderr = P.communicate()
        except subprocess.TimeoutExpired as e:
            if check:
                raise e
            P.kill()
            stdout, stderr = P.communicate()
            return process.DoneProcess(P.args, -1, stdout=stdout, stderr=stderr,
                                       timedout=True)
        except :
            # Unexpected error
            P.kill()
            raise
        retcode = P.poll()
        if retcode and check:
            raise subprocess.CalledProcessError(
                retcode, P.args, output=stdout, stderr=stderr)
    return process.DoneProcess(P.args, retcode, stdout=stdout, stderr=stderr)


def runLongTask(args, finished='info', **kargs):
    """Run a long lasting subprocess without blocking the GUI"""
    #print(f"Starting long task: {args}")
    kargs['wait'] = False
    #print(f"With options: {kargs}")
    P = utils.command(args, **kargs)
    if P:
        #print(P)
        P = monitor_qt(P)
        if finished == 'info':
            showText(f"""..

Background task has finished
----------------------------
Your background task has finished. The result of the process is::

{textwrap.indent(str(P), '  ')}

""")
    return P


########################## print information ################################


def printbbox():
    print(pf.canvas.bbox)

def printviewportsettings():
    pf.GUI.viewports.printSettings()

def reportCamera():
    print(pf.canvas.camera.report())


#################### camera ##################################

def zoom_factor(factor=None):
    if factor is None:
        factor = pf.cfg['gui/zoomfactor']
    return float(factor)

def pan_factor(factor=None):
    if factor is None:
        factor = pf.cfg['gui/panfactor']
    return float(factor)

def rot_factor(factor=None):
    if factor is None:
        factor = pf.cfg['gui/rotfactor']
    return float(factor)

def zoomIn(factor=None):
    pf.canvas.camera.zoomArea(1./zoom_factor(factor))
    pf.canvas.update()
def zoomOut(factor=None):
    pf.canvas.camera.zoomArea(zoom_factor(factor))
    pf.canvas.update()

def panRight(factor=None):
    pf.canvas.camera.transArea(-pan_factor(factor), 0.)
    pf.canvas.update()
def panLeft(factor=None):
    pf.canvas.camera.transArea(pan_factor(factor), 0.)
    pf.canvas.update()
def panUp(factor=None):
    pf.canvas.camera.transArea(0., -pan_factor(factor))
    pf.canvas.update()
def panDown(factor=None):
    pf.canvas.camera.transArea(0., pan_factor(factor))
    pf.canvas.update()

def rotRight(factor=None):
    pf.canvas.camera.rotate(rot_factor(factor), 0, 1, 0)
    pf.canvas.update()
def rotLeft(factor=None):
    pf.canvas.camera.rotate(-rot_factor(factor), 0, 1, 0)
    pf.canvas.update()
def rotUp(factor=None):
    pf.canvas.camera.rotate(-rot_factor(factor), 1, 0, 0)
    pf.canvas.update()
def rotDown(factor=None):
    pf.canvas.camera.rotate(rot_factor(factor), 1, 0, 0)
    pf.canvas.update()
def twistLeft(factor=None):
    pf.canvas.camera.rotate(rot_factor(factor), 0, 0, 1)
    pf.canvas.update()
def twistRight(factor=None):
    pf.canvas.camera.rotate(-rot_factor(factor), 0, 0, 1)
    pf.canvas.update()
def barrelRoll(n=36):
    d = 360./n
    t = 2./n
    for i in range(n):
        twistRight(d)
        sleep(t)
def transLeft(factor=None):
    val = pan_factor(factor) * pf.canvas.camera.dist
    pf.canvas.camera.translate(-val, 0, 0, pf.cfg['draw/localaxes'])
    pf.canvas.update()
def transRight(factor=None):
    val = pan_factor(factor) * pf.canvas.camera.dist
    pf.canvas.camera.translate(+val, 0, 0, pf.cfg['draw/localaxes'])
    pf.canvas.update()
def transDown(factor=None):
    val = pan_factor(factor) * pf.canvas.camera.dist
    pf.canvas.camera.translate(0, -val, 0, pf.cfg['draw/localaxes'])
    pf.canvas.update()
def transUp(factor=None):
    val = pan_factor(factor) * pf.canvas.camera.dist
    pf.canvas.camera.translate(0, +val, 0, pf.cfg['draw/localaxes'])
    pf.canvas.update()
def dollyIn(factor=None):
    pf.canvas.camera.dolly(1./zoom_factor(factor))
    pf.canvas.update()
def dollyOut(factor=None):
    pf.canvas.camera.dolly(zoom_factor(factor))
    pf.canvas.update()

def lockCamera():
    """Fully lock the current camera."""
    pf.canvas.camera.lock()
def lockView():
    """Lock the camera's viewing direction, but not zooming."""
    pf.canvas.camera.lock(view=True, lens=False)
def unlockCamera():
    """Fully unlock the camera."""
    pf.canvas.camera.lock(view=False, lens=False)

def saveCamera(fn=None):
    if fn is None:
        fn = askNewFilename(pf.cfg['workdir'], 'pzf')
    if fn:
        PzfFile(fn).save(_camera=True),
        print("Saved Camera Settings to '%s'" % fn)

def loadCamera(fn=None):
    if fn is None:
        fn = askFilename(pf.cfg['workdir'], ['pzf','all'])
    if fn:
        print("Loading Camera Settings from '%s'" % fn)
        if fn.endswith('.pzf'):
            res = PzfFile(fn).load()
            camera = res.get('_camera', None)
            if camera:
                pf.canvas.initCamera(camera)
                pf.canvas.update()
        else:
            pf.canvas.camera.load(fn)

def zoomRectangle():
    """Zoom a rectangle selected by the user."""
    pf.canvas.zoom_rectangle()
    pf.canvas.update()

def zoomBbox(bb):
    """Zoom thus that the specified bbox becomes visible."""
    pf.canvas.setCamera(bbox=bb)
    pf.canvas.update()

def zoomObj(object):
    """Zoom thus that the specified object becomes visible.

    object can be anything having a bbox() method or a list thereof.
    """
    zoomBbox(coords.bbox(object))

def zoomAll():
    """Zoom thus that all actors become visible."""
    zoomBbox(pf.canvas.sceneBbox())


# Can this be replaced with zoomIn/Out?
def zoom(f):
    """Zoom with a factor f

    A factor > 1.0 zooms out, a factor < 1.0 zooms in.
    """
    pf.canvas.zoom(f)
    pf.canvas.update()


def focus(point):
    """Move the camera focus to the specified point.

    Parameters:

    - `point`: float(3,) or alike

    The camera focus is set to the specified point, while keeping
    a parallel camera direction and same zoom factor.
    The specified point becomes the center of the screen and
    the center of camera rotations.
    """
    pf.canvas.camera.focus = point
    pf.canvas.camera.setArea(0., 0., 1., 1., True, center=True)
    pf.canvas.update()


def flyAlong(path, upvector=[0., 1., 0.], sleeptime=None):
    """Fly through the current scene along the specified path.

    - `path`: a plex-2 or plex-3 Formex (or convertibel to such Formex)
      specifying the paths of camera eye and center (and upvector).
    - `upvector`: the direction of the vertical axis of the camera, in case
      of a 2-plex camera path.
    - `sleeptime`: a delay between subsequent images, to slow down
      the camera movement.

    This function moves the camera through the subsequent elements of the
    Formex. For each element the first point is used as the center of the
    camera and the second point as the eye (the center of the scene looked at).
    For a 3-plex Formex, the third point is used to define the upvector
    (i.e. the vertical axis of the image) of the camera. For a 2-plex
    Formex, the upvector is constant as specified in the arguments.
    """
    try:
        if not isinstance(path, Formex):
            path = path.toFormex()
        if not path.nplex() in (2, 3):
            raise ValueError
    except Exception:
        raise ValueError("The camera path should be (convertible to) a plex-2 or plex-3 Formex!")

    nplex = path.nplex()
    if sleeptime is None:
        sleeptime = pf.cfg['draw/flywait']
    saved = delay(sleeptime)
    saved1 = pf.GUI.actions['Continue'].isEnabled()
    pf.GUI.enableButtons(pf.GUI.actions, ['Continue'], True)

    for elem in path:
        eye, center = elem[:2]
        if nplex == 3:
            upv = elem[2] - center
        else:
            upv = upvector
        pf.canvas.camera.lookAt(center, eye, upv)
        wait()
        pf.canvas.display()
        pf.canvas.update()
        if image.autoSaveOn():
            image.saveNext()

    delay(saved)
    pf.GUI.enableButtons(pf.GUI.actions, ['Continue'], saved1)
    pf.canvas.camera.focus = center
    pf.canvas.camera.dist = at.length(center-eye)
    pf.canvas.update()


#################### viewports ##################################

### BEWARE FOR EFFECTS OF SPLITTING pf.canvas and pf.GI.viewports.current
### if these are called from interactive functions!


def viewport(n=None):
    """Select the current viewport.

    n is an integer number in the range of the number of viewports,
    or is one of the viewport objects in pyformex.GUI.viewports

    if n is None, selects the current GUI viewport for drawing
    """
    if n is not None:
        pf.canvas.update()
        pf.GUI.viewports.setCurrent(n)
    pf.canvas = pf.GUI.viewports.current


def nViewports():
    """Return the number of viewports."""
    return len(pf.GUI.viewports.all)

def layout(nvps=None, ncols=None, nrows=None, pos=None,
           rstretch=None, cstretch=None, reset=False):
    """Set the viewports layout.

    See :meth:`MultiCanvas.changeLayout`.
    """
    pf.GUI.viewports.changeLayout(nvps, ncols, nrows, pos,
                                  rstretch, cstretch, reset)
    viewport()

def addViewport():
    """Add a new viewport."""
    pf.GUI.viewports.addView()
    viewport()

def removeViewport():
    """Remove the last viewport."""
    if nViewports() > 1:
        pf.GUI.viewports.removeView()
    viewport()

def linkViewport(vp, tovp):
    """Link viewport vp to viewport tovp.

    Both vp and tovp should be numbers of viewports.
    """
    pf.GUI.viewports.link(vp, tovp)
    viewport()

####################

def updateGUI():
    """Update the GUI."""
    pf.GUI.update()
    pf.canvas.update()
    pf.app.processEvents()


######### Highlighting ###############
#
def highlightActor(actor):
    """Highlight an actor in the scene."""
    actor.setHighlight()
    pf.canvas.update()


def removeHighlight():
    """Remove the highlights from the current viewport"""
    pf.canvas.removeHighlight()
    pf.canvas.update()

def removeAnnotations():
    """Remove all annotations"""
    pf.canvas.scene.removeAny(pf.canvas.scene.annotations)


# for comaptibility
from pyformex.gui.toolbar import pick

# These are undocumented, and deprecated: use pick() instead
# @utils.deprecated_by('pickActors', 'pick')
# def pickActors(filter=None, oneshot=False, func=None):
#     return pick('actor', filter, oneshot, func)

# @utils.deprecated_by('pickElements', 'pick')
# def pickElements(filter=None, oneshot=False, func=None):
#     return pick('element', filter, oneshot, func)

# @utils.deprecated_by('pickPoints', 'pick')
# def pickPoints(filter=None, oneshot=False, func=None):
#     return pick('point', filter, oneshot, func)

# @utils.deprecated_by('pickEdges', 'pick')
# def pickEdges(filter=None, oneshot=False, func=None):
#     return pick('edge', filter, oneshot, func)


# This could probably be moved into the canvas picking functions
def pickProps(filter=None, oneshot=False, func=None, pickable=None, prompt=None):
    """Pick property numbers

    This is like pick('element'), but returns the (unique) property numbers
    of the picked elements of the actors instead.
    """
    C = pick('element', filter, oneshot, func)
    for a in C.keys():
        actor = pf.canvas.actors[a]
        object = actor.object
        elems = C[a]
        if hasattr(object, 'prop') and object.prop is not None:
            # Replace elem ids with unique props
            C[a] = np.unique(object.prop[elems])
        else:
            # Actor with no props: delete it
            del C.d[a]
    C.obj_type = 'prop'
    return C


def pickFocus():
    """Enter interactive focus setting.

    This enters interactive point picking mode and
    sets the focus to the center of the picked points.
    """
    K = pick('point', oneshot=True)
    removeHighlight()
    if K:
        X = []
        for k in K:
            a = pf.canvas.actors[k]
            o = a.object
            x = o.points()[K[k]]
            X.append(x.center())
        X = Coords(X).center()
        focus(X)


LineDrawing = None
edit_modes = ['undo', 'clear', 'close']

def drawLinesInter(mode ='line', single=False, func=None):
    """Enter interactive drawing mode and return the line drawing.

    See viewport.py for more details.
    This function differs in that it provides default displaying
    during the drawing operation and a button to stop the drawing operation.

    The drawing can be edited using the methods 'undo', 'clear' and 'close',
    which are presented in a combobox.
    """
    def _set_edit_mode(item):
        """Set the drawing edit mode."""
        s = item.value()
        if s in edit_modes:
            pf.canvas.edit_drawing(s)
        if pf.canvas.drawing_mode is not None:
            warning("You need to finish the previous drawing operation first!")

    if pf.canvas.drawing_mode is not None:
        warning("You need to finish the previous drawing operation first!")
        return
    if func is None:
        func = showLineDrawing
    drawing_buttons = widgets.ButtonBox('Drawing:', [
        ('Cancel', pf.canvas.cancel_drawing),
        ('OK', pf.canvas.accept_drawing)])
    pf.GUI.statusbar.addWidget(drawing_buttons)
    edit_combo = widgets.InputCombo(
        'Edit:', None, choices=edit_modes, func=_set_edit_mode)
    pf.GUI.statusbar.addWidget(edit_combo)
    lines = pf.canvas.drawLinesInter(mode, single, func)
    pf.GUI.statusbar.removeWidget(drawing_buttons)
    pf.GUI.statusbar.removeWidget(edit_combo)
    return lines


def showLineDrawing(L):
    """Show a line drawing.

    L is usually the return value of an interactive draw operation, but
    might also be set by the user.
    """
    global LineDrawing
    if LineDrawing:
        undecorate(LineDrawing)
        LineDrawing = None
    if L.size != 0:
        LineDrawing = decors.Lines(L, color='yellow', linewidth=3)
        decorate(LineDrawing)


def exportWebGL(fn, createdby=50, **kargs):
    """Export the current scene to WebGL.

    Parameters:

    - `fn` : string: the (relative or absolute) filename of the .html, .js
      and .pgf files comprising the WebGL model. It can contain a directory
      path and any extension. The latter is dropped and not used.
    - `createdby`: int: width in pixels of the 'Created by pyFormex' logo
      appearing on the page. If < 0, the logo is displayed at its natural
      width. If 0, the logo is suppressed.
    - `**kargs`: any other keyword parameteris passed to the
      :class:`WebGL` initialization. The `name` can not be specified: it
      is derived from the `fn` parameter.

    Returns the absolute pathname of the generated .html file.
    """
    from pyformex.plugins.webgl import WebGL
    fn = Path(fn)
    print("Exporting current scene to %s" % fn)
    curdir = Path.cwd()
    with busyCursor():
        chdir(fn.parent, create=True)
        try:
            name = fn.stem
            W = WebGL(name=name, **kargs)
            W.addScene(name)
            fn = W.export(createdby=createdby)
        finally:
            chdir(curdir)
    return fn


the_multiWebGL = None

def multiWebGL(name=None, fn=None, title=None, description=None, keywords=None, author=None, createdby=50):
    """Export the current scene to WebGL.

    fn is the (relative or absolute) pathname of the .html and .js files to be
    created.

    When the export is finished, returns the absolute pathname of the
    generated .html file. Else, returns None.
    """
    global the_multiWebGL

    from pyformex.plugins.webgl import WebGL
    ret = None
    if fn is not None:
        fn = Path(fn)
        with busyCursor():
            if the_multiWebGL is not None:
                the_multiWebGL.export()
                the_multiWebGL = None

            print("OK", the_multiWebGL)

            if fn.is_absolute():
                chdir(fn.parent)
            proj = fn.stem
            print("PROJECT %s" % proj)
            the_multiWebGL = WebGL(proj, title=title, description=description, keywords=keywords, author=author)

        if the_multiWebGL is not None:
            if name is not None:
                print("Exporting current scene to %s" % the_multiWebGL.name)
                the_multiWebGL.addScene(name)

            elif fn is None:  # No name, and not just starting
                print("Finishing export of %s" % the_multiWebGL.name)
                ret = the_multiWebGL.export(createdby=createdby)
                the_multiWebGL = None

    return ret


################################

def setLocalAxes(mode=True):
    pf.cfg['draw/localaxes'] = mode
def setGlobalAxes(mode=True):
    setLocalAxes(not mode)


def resetGUI():
    """Reset the GUI to its default operating mode.

    When an exception is raised during the execution of a script, the GUI
    may be left in a non-consistent state.
    This function may be called to reset most of the GUI components
    to their default operating mode.
    """
    ## resetPick()
    pf.GUI.resetCursor()
    pf.GUI.enableButtons(pf.GUI.actions, ['Play', 'Step'], True)
    pf.GUI.enableButtons(pf.GUI.actions, ['Continue', 'Stop'], False)
    pf.GUI.setViewButtons(pf.cfg['gui/frontview'])


############################## drawing functions ########################

class TempPalette:
    """Context manager to set a temporary colormap for the canvas.

    This can be used as follows::

        M = Mesh(eltype='quad4').subdivide(3,2).setProp('range')
        with TempPalette([red,blue]):
            draw(M)   # draws with only red and blue
            sleep(2)
        clear()
        draw(M)       # draws with default colormap

    If no colormap is specified (default), the context manager does
    nothing. This is convenient to use it as an optional colormap
    switcher.
    """
    def __init__(self, colormap=None):
        from pyformex.opengl.sanitize import saneColor
        if colormap is not None:
            colormap = saneColor(colormap)
        self.colormap = colormap
        self.saved_colormap = None

    def __enter__(self):
        if self.colormap is not None:
            self.saved_colormap = pf.canvas.settings.colormap
            pf.canvas.settings.colormap = self.colormap
        return self

    def __exit__(self, *exc):
        if self.saved_colormap is not None:
            pf.canvas.settings.colormap = self.saved_colormap
        return False  # we did not handle exceptions


def flatten(objects, recurse=True):
    """Flatten a list of objects.

    Each item in the list should be either:

    - a drawable object,
    - a string with the name of such an object,
    - a list of any of these three.

    This function will flatten the lists and replace the string items with
    the object they point to. The result is a single list of drawable
    objects. This function does not enforce the objects to be drawable.
    That should be done by the caller.
    """
    r = []
    for i in objects:
        if isinstance(i, str):
            i = named(i)
        if isinstance(i, list):
            if recurse:
                r.extend(flatten(i, True))
            else:
                r.extend(i)
        else:
            r.append(i)
    return r


def drawn_as(object):
    """Check how an object can be drawn.

    An object can be drawn (using :func:`draw`) if it has a method
    'actor', 'toFormex' or 'toMesh'. In the first case, it has a native
    :class:`Actor`, else, it is first transformed to :class:`Formex`
    or :class:`Mesh`.

    Parameters
    ----------
    object: any object, though usually a :class:`Geometry` instance
        An object to check for a drawing method.

    Returns
    -------
    object: drawabable object or None
        If the object is drawable (directly or after conversion), returns
        a directly drawable object, else None.

    """
    d = dir(object)
    if 'actor' in d:
        a = object
    elif 'toFormex' in d:
        a = object.toFormex()
        if 'attrib' in d:
            a.attrib(**object.attrib)
    elif 'toMesh' in d:
        a = object.toMesh()
        if 'attrib' in d:
            a.attrib(**object.attrib)
    else:
        a = None
    return a


def drawable(objects):
    """Filters the drawable objects from a list of objects.

    Parameters
    ----------
    objects: list or sequence of objects.
        The list of objects to filter for drawable objects.

    Returns
    -------
    list of objects
        The list of objects that can be drawn.
    """
    r = [drawn_as(o) for o in objects]
    return [i for i in r if i is not None]


# Accepted keyword parameters for draw
## color='prop',colormap=None,alpha=None,
## bkcolor=None,bkcolormap=None,bkalpha=None,
## mode=None,linewidth=None,linestipple=None,
## marksize=None,nolight=False,ontop=False,

def draw(F, clear=None, **kargs):
    """Draw geometrical object(s) with specified drawing options and settings.

    This is the generic drawing function in pyFormex.
    The function requires a single positional parameter specifying the
    geometry to be drawn. There are also a whole lot of optional keyword
    parameters, divided in two groups.

    The first are the drawing options, which modify the way the draw
    function operates. If not specified, or a value None is specified,
    they are filled in from the current viewport drawing options, which
    can be changed using the :func:`~gui.draw.setDrawOptions` function.
    The initial defaults are: clear=False, view='last', bbox='auto',
    shrink=False, shrinkfactor=0.8, wait=True, silent=True, single=False.

    The second group are rendering attributes that define the way the
    geometrical objects should be rendered. These have default values in
    :attr:`canvas.Canvas.settings`, and can be overridden per object by
    the object's attrib() settings. These options are listed below under
    Notes.

    Parameters
    ----------
    F: object or list of objects
        The object(s) to be drawn. It can be a single item or a
        (possibly nested) list of items. The list will be flattened.
        Strings are looked up in the pyFormex global project dictionary
        and replaced with their value. Nondrawable objects are filtered
        out from the list (see also option ``silent``).
        The resulting list of drawable objects is processed with the same
        drawing options and default rendering atributes.
    clear: bool, optional
        If True, the scene is cleared before drawing. The default is to add
        to the existing scene.
    view: str
        Either the name of a defined view or 'last'.
        This defines the orientation of the camera looking at the drawn
        objects. Predefined views are 'front', 'back', 'top', 'bottom',
        'left', 'right', 'iso' and a whole list of other ones.
        * TODO: we should expand this *
        On creation of a viewport, the initial default view is 'front'
        (looking in the -z direction).
        With view='last', the camera angles will be set
        to the same camera angles as in the last draw operation,
        undoing any interactive changes.
        With view=None the camera settings remain unchanged (but still may
        be changed interactively through the user interface). This may make
        the drawn object out of view. See also ``bbox``.
    bbox: :term:`array_like` or str
        Specifies the 3D volume at which the camera will be aimed (using
        the angles set by ``view``). The camera position will
        be set thus that the volume comes in view using the current lens
        (default 45 degrees).  ``bbox`` is a list of two points or
        compatible (array with shape (2,3)).  Setting the bbox to a
        volume not enclosing the object may make the object invisible
        on the canvas.  The special value bbox='auto' will use the
        bounding box of the objects getting drawn (object.bbox()),
        thus ensuring that the camera will focus on these objects.
        This is the default when creating a new viewport.
        A value bbox=None will use the bounding box of the
        previous drawing operation, thus ensuring that the camera's
        target volume is unchanged.
    shrink: bool
        If specified, each object will be transformed by the
        :meth:`Coords.shrink` transformation (with the default
        or specified shrink_factor as a parameter), thus showing
        all the elements of the object separately (sometimes called
        an 'exploded' view).
    shrink_factor: float
        Overrides the default shrink_factor for the current draw operation.
        If provided, it forces ``shrink=True``.
    wait: bool
        If True (initial default), the draw action activates
        a locking mechanism for the next draw action, which will only be
        allowed after `drawdelay` seconds have elapsed. This makes it easier
        to see subsequent renderings and is far more efficient than adding
        an explicit sleep() operation, because the script processing can
        continue up to the next drawing instruction. The value of drawdelay
        can be changed in the user settings or using the :func:`delay` function.
        Setting this value to 0 will disable the waiting mechanism for all
        subsequent draw statements (until set > 0 again). But often the user
        wants to specifically disable the waiting lock for some draw
        operation(s). This can be done without changing the `drawdelay`
        setting, by specifying `wait=False`. This means that the *next* draw
        operation does not have to wait.
    silent: bool
        If True (initial default), non-drawable objects are
        silently ignored. If set False, an error is raised if ``F`` contains
        an object that is not drawable.
    single: bool, optional
        If True, the return value will be a single Actor, corresponding
        with the first drawable object in the flattened list of ``F``.
        The remainder of the drawable objects in ``F`` are then set as
        children of the main return value.
        The default is to return a single Actor if F is a single drawable
        object, or a list of Actors if F is a list.
    kargs: keyword parameters
        The remaining keyword parameters are the default rendering
        attributes to be used for all the objects in ``F``.
        They will apply unless overridden by attributes set in
        the object itself (see :meth:`geometry.Geometry.attrib`).
        There is a long list of possible settings. The important ones
        are listed below (see Notes).

    Returns
    -------
    :class:`Actor` or list of Actors
        If F is a single object or ``single==True`` was provided, returns a
        single Actor instance. If F is a list and ``single==True`` was not
        set, a list a Actors is returned.

    Notes
    -----
    * This section is incomplete and needs an update *

    Here is an (incomplete) list of rendering attributes that can be provided
    to the draw function and will be used as defaults for drawing the objects
    that do not have the needed values set as attributes on the object itself.
    While the list is long, in most cases only a few are used, and the
    remainder are taken from the canvas rendering defaults.

    These arguments will be passed to the corresponding Actor for the object.
    The Actor is the graphical representation of the geometry. Not all Actors
    use all of the settings that can be specified here. But they all accept
    specifying any setting even if unused. The settings hereafter are thus a
    superset of the settings used by the different Actors.
    Settings have a default value per viewport, and if unspecified, most
    Actors will use the viewport default for that value.

    - `color`, `colormap`: specify the color of the object (see below)
    - `alpha`: float (0.0..1.0): alpha value to use in transparent mode. 0.0
      means fully transparent (invisible), while 1.0 means opaque.
    - `bkcolor`, `bkcolormap`: color for the backside of surface type geometry,
      if it is to be different from the front side. Specifications are as for
      front color and colormap.
    - `bkalpha`: float (0.0..1.0): transparency alphe value for the back side.
    - `linewidth`: float, thickness of line drawing
    - `linestipple`: stipple pattern for line drawing
    - `marksize`: float: point size for dot drawing
    - `nolight`: bool: render object as unlighted in modes with lights on
    - `ontop`: bool: render object as if it is on top.
      This will make the object fully visible, even when it is hidden by
      other objects. If more than one objects is drawn with `ontop=True`
      the visibility of the object will depend on the order of drawing.

    Specifying color:
    Color specification can take many different forms. Some Actors recognize
    up to six different color modes and the draw function adds even another
    mode (property color)

    - no color: `color=None`. The object will be drawn in the current
      viewport foreground color.
    - single color: the whole object is drawn with the specified color.
    - element color: each element of the object has its own color. The
      specified color will normally contain precisely `nelems` colors,
      but will be resized to the required size if not.
    - vertex color: each vertex of each element of the object has its color.
      In smooth shading modes intermediate points will get an interpolated
      color.
    - element index color: like element color, but the color values are not
      specified directly, but as indices in a color table (the `colormap`
      argument).
    - vertex index color: like vertex color, but the colors are indices in a
      color table (the `colormap` argument).
    - property color: as an extra mode in the draw function, if `color='prop'`
      is specified, and the object has an attribute 'prop', that attribute
      will be used as a color index and the object will be drawn in
      element index color mode. If the object has no such attribute, the
      object is drawn in no color mode.

    Hey! What about nodal color? When drawing a :class:`Mesh`, it is possible
    to draw with colors that are specified on the nodes instead of on
    the elements. To do that, just expand the colors to the element nodes
    as follows. ``M`` is a :class:`Mesh`, ncolors is an array containing
    ``M.ncoords()`` colors or color indices::

      draw(M, color=ncolors[M.elems])

    Element and vertex color modes are usually only used with a single object
    in the `F` parameter, because they require a matching set of colors.
    Though the color set will be automatically resized if not matching, the
    result will seldomly be what the user expects.
    If single colors are specified as a tuple of three float values
    (see below), the correct size of a color array for an object with
    `nelems` elements of plexitude `nplex` would be: (nelems,3) in element
    color mode, and (nelems,nplex,3) in vertex color mode. In the index modes,
    color would then be an integer array with shape respectively (nelems,) and
    (nelems,nplex). Their values are indices in the colormap array, which
    could then have shape (ncolors,3), where ncolors would be larger than the
    highest used value in the index. If the colormap is insufficiently large,
    it will again be wrapped around. If no colormap is specified, the current
    viewport colormap is used. The default contains eight colors: black=0,
    red=1, green=2, blue=3, cyan=4, magenta=5, yellow=6, white=7.

    A color value can be specified in multiple ways, but should be convertible
    to a normalized OpenGL color using the :func:`colors.GLcolor` function.
    The normalized color value is a tuple of three values in the range 0.0..1.0.
    The values are the contributions of the red, green and blue components.
    """
    _camera = None

    if clear is not None:
        kargs['clear_'] = clear

    draw_options = ['view', 'bbox', 'clear_', 'shrink', 'shrink_factor',
                     'wait', 'silent', 'single', ]

    # handle the shrink special case: bool or float
    if 'shrink' in kargs:
        if at.isFloat(kargs['shrink']):
            kargs['shrink_factor'] = kargs['shrink']
            kargs['shrink'] = True

    # Get default drawing options and overwrite with specified values
    opts = Attributes(pf.canvas.drawoptions)
    opts.update(utils.selectDict(kargs, draw_options, remove=True))

    # First try as a single drawable object
    FL = drawn_as(F)
    if FL is not None:
        # For simplicity of the code, put the object always in a list
        FL = [FL]
        single = True
    else:
        if isinstance(F, dict):
            # TODO: set the keys as name attrib
            FL = list(F.values())
        else:
            # First flatten the input
            FL = flatten(list(F))
        single = opts.single
        # Record the (last) camera, if any
        for item in FL:
            if isinstance(item, camera.Camera):
                _camera = item

    ntot = len(FL)

    # Transform to list of drawable objects
    FL = drawable(FL)
    nres = len(FL)

    if nres < ntot and not opts.silent:
        raise ValueError("Data contains undrawable objects (%s/%s)" % (ntot-nres, ntot))

    # Shrink the objects if requested
    if opts.shrink:
        FL = [_shrink(Fi, opts.shrink_factor) for Fi in FL]

    ## # Execute the drawlock wait before doing first canvas change
    pf.GUI.drawlock.wait()

    if opts.clear_:
        clear_canvas()

    if opts.view not in [None, 'last', 'cur']:
        pf.debug("SETTING VIEW to %s" % opts.view, pf.DEBUG.DRAW)
        setView(opts.view)

    with busyCursor():
        pf.app.processEvents()

        actors = []

        # loop over the objects
        for Fi in FL:

            # Create the actor
            actor = Fi.actor(**kargs)
            if single and len(actors) > 0:
                # append the new actor to the children of the first
                actors[0].children.append(actor)
            else:
                # append the actor to the list of actors
                actors.append(actor)

            if actor is not None and not single:
                # Immediately show the new actor
                pf.canvas.addActor(actor)

        if single:
            # Return a single actor
            actors = actors[0] if len(actors) > 0 else None
            if actors is not None:
                # Draw all actors in a single shot
                pf.canvas.addActor(actors)

        view = opts.view
        bbox = opts.bbox
        pf.debug(pf.canvas.drawoptions, pf.DEBUG.OPENGL)
        pf.debug(opts, pf.DEBUG.OPENGL)
        pf.debug(view, pf.DEBUG.OPENGL)
        pf.debug(bbox, pf.DEBUG.OPENGL)

        # Adjust the camera
        # use the view and bbox args
        if view not in [None, 'cur'] or bbox not in [None, 'last']:
            if view == 'last':
                view = pf.canvas.drawoptions['view']
            # bbox can be an ndarray, for which '==' would fail
            if isinstance(bbox, str):
                if bbox == 'auto':
                    bbox = pf.canvas.scene.bbox
                elif bbox == 'last':
                    bbox = None
            pf.canvas.setCamera(bbox, view)
        if _camera is not None:
            pf.canvas.initCamera(_camera)

        # Update the rendering
        pf.canvas.update()
        pf.app.processEvents()

        # Save the rendering if autosave on
        pf.debug("AUTOSAVE %s" % image.autoSaveOn())
        if image.autoSaveOn():
            image.saveNext()

        # Make sure next drawing operation is retarded
        if opts.wait:
            pf.GUI.drawlock.lock()

    # Return the created Actor(s)
    return actors


def _setFocus(object, bbox, view):
    """Set focus after a draw operation"""
    if view is not None or bbox not in [None, 'last']:
        if view == 'last':
            view = pf.canvas.drawoptions['view']
        if bbox == 'auto':
            bbox = coords.bbox(object)
        pf.canvas.setCamera(bbox, view)
    pf.canvas.update()


def setDrawOptions(kargs0={}, **kargs):
    """Set default values for the draw options.

    Draw options are a set of options that hold default values for the
    draw() function arguments and for some canvas settings.
    The draw options can be specified either as a dictionary, or as
    keyword arguments.
    """
    d = {}
    d.update(kargs0)
    d.update(kargs)
    pf.canvas.setOptions(d)


def showDrawOptions():
    print("Current Drawing Options: %s" % pf.canvas.drawoptions)
    print("Current Viewport Settings: %s" % pf.canvas.settings)


def reset():
    """reset the canvas"""
    frontview(pf.cfg['gui/frontview'])
    pf.canvas.resetDefaults()
    pf.canvas.resetOptions()
    pf.GUI.drawwait = pf.cfg['draw/wait']
    try:
        if len(pf.GUI.viewports.all) == 1:
            size = (-1, -1)
            canvasSize(*size)
    except Exception:
        print("Warning: Resetting canvas before initialization?")
    clear(sticky=True)
    pf.canvas.camera.unlock()
    view('front')


def resetAll():
    reset()
    renderMode(pf.cfg['draw/rendermode'])


def frontview(front):
    """Set the frontview configuration"""
    if front in ['xy', 'xz']:
        pf.GUI.setViewButtons(front)
    else:
        raise ValueError("front should be one of 'xy' or 'xz'")


def setShrink(shrink=None):
    """Set shrink mode on or off, and optionally the shrink factor.

    In shrink mode, all elements are drawn shrinked around their
    centroid. This results in an exploded view showing individual
    elements and permitting look through the inter-element gaps to
    what is behind.

    Parameters
    ----------
    shrink: float | bool | None
        If a float, switches shrink mode on and sets the shrink factor to the
        provided value. If True, switches on shrink mode with the current
        shrink factor (see notes).
        If False, switches off shrink mode.

    Notes
    -----
    Useful values for the shrink factor are in the range 0.0 to 1.0.
    The initial value is 0.8.
    The current shrink status and factor are stored in
    ``pf.canvas.drawoptions['shrink_factor']``.
    """
    if at.isFloat(shrink):
        d = {
            'shrink': True,
            'shrink_factor': shrink,
            }
    else:
        if shrink is None:
            shrink = not pf.canvas.drawoptions['shrink']
        d = {'shrink': bool(shrink)}
    setDrawOptions(d)


def _shrink(F, factor):
    """Return a shrinked object.

    A shrinked object is one where each element is shrinked with a factor
    around its own center.
    """
    try:
        if not isinstance(F, Formex):
            F = F.toFormex()
        return F.shrink(factor)
    except AttributeError:
        return F


def drawVectors(P, v, size=None, nolight=True, **drawOptions):
    """Draw a set of vectors.

    If size is None, draws the vectors v at the points P.
    If size is specified, draws the vectors size*normalize(v)
    P, v and size are single points
    or sets of points. If sets, they should be of the same size.

    Other drawoptions can be specified and will be passed to the draw function.
    """
    if size is None:
        Q = P + v
    else:
        Q = P + size*at.normalize(v)
    return draw(connect([P, Q]), nolight=nolight, **drawOptions)


def drawPlane(P, N, size=(1.0,1.0), **drawOptions):
    from pyformex.plugins.tools import Plane
    p = Plane(P, N, size)
    return draw(p, bbox='last', **drawOptions)


def repeat_items(l, c):
    return l * (c // len(l)) + l[:(c % len(l))]


def drawMarks(X, M, *, colors=None, prefix='', ontop=True, fuse=False,
              color='black', **kargs):
    """Draw a list of marks at points X.

    Parameters
    ----------
    X: Coords
        The 3D coordinates of the points where to insert the marks.
    M: list of str
        List of text marks to draw at points X. If the list is shorter than
        the array X, the list is cycled. If the list is longer, it is cut
        at the length of X. The string representation of the
    colors: list of :term:`color_like`
        List of colors to be used for the subsequent marks. If not long
        enough, the list will be cycled.
        If not provided, all marks are drawn with the same color, specified
        with the ``color`` argument, which defaults to the current foreground
        color.
        If ``colors`` is provided, it overrides any specified ``color`` value
        and sets the ``texmode`` argument to 5.
    prefix: str, optional
        If specified, this string is prepended to all drawn strings.
    ontop: bool, optional
        If True (default), the marks are drawn on top, meaning they will
        all be visible, even those drawn at points hidden by the geometry.
        If False, marks at hidden points can be hidden by the drawn geometry.
    fuse: bool, optional
        If True, the drawing positions X will be fused, and marks
        for the fused points will be collected in a single string separated
        by commas. If False (default), labels at the same position are
        drawn on top of each other, likely making them unreadable.
        Note that using ``fuse=True`` together with a ``colors`` list may
        garble up the order of the colors.
    **kargs:
        Other parameters that will be passed to the :class:`actors.TextArray`
        class.

    Returns
    -------
    TextArray
        The drawn actor.

    """
    from pyformex.gui.draw import ack
    _large_ = 20000
    lenX, lenM = len(X), len(M)
    if lenX == 0 or lenM == 0:
        return None
    if lenM < lenX:
        M *= (lenX - 1) // lenM + 1
    if lenM > lenX:
        M = M[:lenX]
    if lenM > _large_:
        if not ack(
                f"You are trying to draw marks at {lenM} points. This may "
                "take a long time, and the results will most likely not be "
                "readable. If you still insist on drawing these marks, "
                "answer YES."):
            return None
    if colors is not None:
        kargs.setdefault('texmode', 5)
    else:
        kargs['color'] = color
    if fuse:
        # TODO: if multiple colors are used, we should also pick the
        # corrrect colors.
        X, ind = X.fuse()
        ind = Varray(ind.reshape(-1,1)).inverse()
        M = [','.join([str(M[i]) for i in row]) for row in ind]
    #print(colors, kargs)
    A = actors.TextArray(val=M, pos=X, colors=colors, prefix=prefix, **kargs)
    drawActor(A)
    return A


def drawNumbers(G, numbers=None, *, offset=0, trl=None, ontop=True, **kargs):
    """Draw numbers on all elements of a Geometry G.

    Parameters
    ----------
    G: Coords | Geometry
        A Coords or Geometry (or any class having a 'centroids' method that
        returns a Coords. Specifies the coordinates of the points where the
        numbers are drawn.
    numbers: int :term:`array_like`, optional
        The numbers to be drawn at the points of G
        An int array of length G.nelems(). If not provided, the range from
        0 to G.nelems()-1 is used.
    offset: int, optional
        If provided, this constant value is added to the numbers.
        This can e.g. be used to create an image for comparison with
        systems using base 1 numbering.
    trl: :term:`vector_like`, optional
        If provided, the drawing positions are the centroids of G translated
        over this vector.
    ontop: bool, optional
        If True, the marks are drawn on top, meaning they will all be visible,
        even those drawn at points hidden by the geometry.
        If False, marks at hidden points can be hidden by the drawn geometry.
        If None, the value of the configuration variable
        draw/numbersontop is used.
    kargs: optional
        Other keywork parameters are passed to the :func:`drawMarks` function
        for doing the real work.
    """
    if ontop is None:
        ontop = getcfg('draw/numbersontop')
    try:
        X = G.centroids()
    except Exception:
        return None
    if trl is not None:
        X = X.trl(trl)
    X = X.reshape(-1, 3)
    if numbers is None:
        numbers = np.arange(X.shape[0])
    if offset:
        numbers = numbers + offset
    # TODO: do not make fuse the default, because it mixes up the order
    # of points when fuse is not even needed or wanted. This is important
    # if we use different colors. This should be fixed upstream.
    # if 'fuse' not in kargs:
    #     kargs['fuse'] = True
    return drawMarks(X, numbers, ontop=ontop, **kargs)


def drawPropNumbers(F, **kargs):
    """Draw property numbers on all elements of F.

    This calls drawNumbers to draw the property numbers on the elements.
    All arguments of drawNumbers except `numbers` may be passed.
    If the object F thus not have property numbers, -1 values are drawn.
    """
    if F.prop is None:
        nrs = -np.ones(F.nelems(), dtype=np.Int)
    else:
        nrs = F.prop
    drawNumbers(F, nrs, **kargs)


def drawVertexNumbers(F, color='black', trl=None, ontop=False):
    """Draw (local) numbers on all vertices of F.

    Normally, the numbers are drawn at the location of the vertices.
    A translation may be given to put the numbers out of the location,
    e.g. to put them in front of the objects to make them visible,
    or to allow to view a mark at the vertices.
    """
    FC = F.coords.reshape((-1, 3))
    if trl is not None:
        FC = FC.trl(trl)
    return drawMarks(FC, np.resize(np.arange(F.coords.shape[-2]), (FC.shape[0])), color=color, ontop=ontop)


def drawBbox(F, *, actor=None, color='black', **kargs):
    """Draw the bounding box of the Geometry object F.

    Parameters
    ----------
    F: Geometry
        Any object that has a 'bbox' method to compute its bounding box.
    actor: 'bbox' | 'grid'
        The type of actor to be used to represent the bounding box.
        'bbox' is simple cuboid drawn in line mode. 'grid' is a more
        complex actor that can show a series of planes and or lines.
        The default can be configured in the user settings.

    Returns
    -------
    The drawn Annotation(s).
    """
    bb = F.bbox()
    if actor is None:
        actor = pf.cfg['geometry_menu/bbox']
    if actor == 'bbox':
        A = actors.BboxActor(F.bbox(), color=color, **kargs)
        drawActor(A)
    else:
        nx = np.array([4, 4, 4])
        A = actors.Grid(nx=nx, ox=bb[0], dx=(bb[1]-bb[0])/nx, planes='f')
        # Beware! Grid is a Geometry, not an Actor
        A = draw(A)
    return A


def drawBboxGrid():
    """Draw a grid in the bbox of the Geometry object F.

    F is any object that has a `bbox` method.
    Returns the drawn Annotation.
    """
    bb = F.bbox()
    nx = np.array([4, 4, 4])
    G = actors.Grid(nx=nx, ox=bb[0], dx=(bb[1]-bb[0])/nx, planes='f')


def drawText(text, pos, **kargs):
    """Show a text at position pos.

    Draws a text at a given position. The position can be either a 2D
    canvas position, specified in pixel coordinates (int), or a 3D position,
    specified in global world coordinates (float). In the latter case the
    text will be displayed on the canvas at the projected world point, and
    will move with that projection, while keeping the text unscaled and
    oriented to the viewer. The 3D mode is especially useful to annotate
    parts of the geometry with a label.

    Parameters:

    - `text`: string to be displayed.
    - `pos`: (2,) int or (3,) float: canvas or world position.
    - any other parameters are passed to :class:`opengl.textext.Text`.

    """
    A = actors.Text(text, pos, **kargs)
    drawActor(A)
    return A


# This function should be completed
def drawViewportAxes3D(pos, color=None):
    """Draw two viewport axes at a 3D position."""
    A = actors.Mark((0, 200, 0), image, size=40, color='red')
    drawActor(A)
    return A


def drawAxes(cs=None, **kargs):
    """Draw the axes of a coordinate system.

    Parameters:

    - `cs`: a :class:`coordsys.CoordSys`
      If not specified, the global coordinate system is used.

    Other arguments can be added just like in the :class:`candy.Axes` class.

    By default this draws the positive parts of the axes in the colors R,G,B
    and the negative parts in C,M,Y.
    """
    from pyformex.candy import Axes
    from pyformex.coordsys import CoordSys
    if cs is None:
        cs = CoordSys()

    A = draw(Axes(cs, **kargs))
    return A


def drawPrincipal(F, weight=None, **kargs):
    """Draw the principal axes of the geometric object F.

    F is Coords or Geometry.
    If weight is specified, it is an array of weights attributed to the points
    of F. It should have the same length as `F.coords`.
    Other parameter are drawing attributes passed to :func:`drawAxes`.
    """
    return drawAxes(F.principalCS(weight), **kargs)


def drawImage3D(image, nx=0, ny=0, pixel='dot'):
    """Draw an image as a colored Formex

    Draws a raster image as a colored Formex. While there are other and
    better ways to display an image in pyFormex (such as using the imageView
    widget), this function allows for interactive handling the image using
    the OpenGL infrastructure.

    Parameters:

    - `image`: a QImage or any data that can be converted to a QImage,
      e.g. the name of a raster image file.
    - `nx`,`ny`: width and height (in cells) of the Formex grid.
      If the supplied image has a different size, it will be rescaled.
      Values <= 0 will be replaced with the corresponding actual size of
      the image.
    - `pixel`: the Formex representing a single pixel. It should be either
      a single element Formex, or one of the strings 'dot' or 'quad'. If 'dot'
      a single point will be used, if 'quad' a unit square. The difference
      will be important when zooming in. The default is 'dot'.

    Returns the drawn Actor.

    See also :func:`drawImage`.
    """
    from pyformex.plugins.imagearray import qimage2glcolor, resizeImage
    from pyformex import colors

    with busyCursor():
        # Create the colors
        #print("TYPE %s" % type(image))
        if isinstance(image, np.ndarray):
            # undocumented feature: allow direct draw of 2d array
            color = image
            if color.dtype.kind == 'i':
                color = color / 255
            nx, ny = color.shape[:2]
            colortable = None
            #print(color)
        else:
            image = resizeImage(image, nx, ny)
            nx, ny = image.width(), image.height()
            color, colortable = qimage2glcolor(image, order='RGBA')

        # Create a 2D grid of nx*ny elements
        # !! THIS CAN PROBABLY BE DONE FASTER
        if isinstance(pixel, Formex) and pixel.nelems()==1:
            F = pixel
        elif pixel == 'quad':
            F = Formex('4:0123')
        else:
            F = Formex('1:0')
        F = F.replicm((nx, ny)).centered()
        F.attrib(color=color, colormap=colortable, nolight=True,
                 imageshape=(nx,ny))
        # Draw the grid using the image colors
        FA = draw(F)
    return FA


def drawFreeEdges(M, color='black'):
    """Draw the feature edges of a Mesh"""
    B = M.getFreeEdgesMesh()
    return draw(B, color=color, nolight=True)


def drawImage(image, w=0, h=0, x=-1, y=-1, color='white', ontop=False):
    """Draws an image as a viewport decoration.

    Parameters:

    - `image`: a QImage or any data that can be converted to a QImage,
      e.g. the name of a raster image file. See also the :func:`loadImage`
      function.
    - `w`,`h`: width and height (in pixels) of the displayed image.
      If the supplied image has a different size, it will be rescaled.
      A value <= 0 will be replaced with the corresponding actual size of
      the image.
    - `x`,`y`: position of the lower left corner of the image. If negative,
      the image will be centered on the current viewport.
    - `color`: the color to mix in (AND) with the image. The default (white)
      will make all pixels appear as in the image.
    - `ontop`: determines whether the image will appear as a background
      (default) or at the front of the 3D scene (as on the camera glass).

    Returns the Decoration drawn.

    Note that the Decoration has a fixed size (and position) on the canvas
    and will not scale when the viewport size is changed.
    The :func:`bgcolor` function can be used to draw an image that completely
    fills the background.
    """
    utils.warn("warn_drawImage_changed")
    from pyformex.plugins.imagearray import qimage2numpy
    from pyformex.opengl.decors import Rectangle

    image = qimage2numpy(image, resize=(w, h), indexed=False)
    w, h = image.shape[:2]
    if x < 0:
        x = (pf.canvas.width() - w) // 2
    if y < 0:
        y = (pf.canvas.height() - h) // 2
    R = Rectangle(x, y, x+w, y+h, color=color, texture=image, ontop=ontop)
    decorate(R)
    return R


def drawField(fld, comp=0, scale='RAINBOW', symmetric_scale=False,
              cvalues=None, clageom=None, **kargs):
    """Draw intensity of a scalar field over a Mesh.

    Parameters
    ----------
    fld: :class:`Field`
        A Field, specifying some value over a Geometry.
    comp: int, optional
        Required if `fld` is a vectorial Field: specifies the component
        that is to be drawn.
    scale: str
        One of the color palettes defined in :mod:`colorscale`.
        If an empty string is specified, the scale is not drawn.
    symmetric_scale: bool
        If `True` the mid value of the color scale will be set to the value
        corresponding to the middle value of the `fld` data range.
        If `False` the mid value of the color scale will be set to 0.0
        if the range extends over negative and positive values.
    cvalues: list, optional
        Specifies the min, max and mid values between which to span the
        color palette. It can be a list of 2 values (min, max) or
        3 values (min, mid, max).
        If not provided, the values are taken from the field data.
    clageom: list of int, optional
        If provided, it is a list of four integers (x, y, w, h) specifying
        the position and size (in pixels) of the colorscale. The default
        size is a height of 200 (adjusted down if the canvas is not high
        enough) and positioned near the lower left corner of the canvas.
    **kargs:
        Other keyword arguments are passed to the draw function to draw
        the Geometry.

    Draws the Field's Geometry with the Field data converted to colors.
    A color legend is added to convert colors to values.
    NAN data are converted to numerical values using numpy.nan_to_num.

    """
    from pyformex.gui.colorscale import ColorScale
    from pyformex.opengl.decors import ColorLegend

    # Get the data
    data = np.nan_to_num(fld.comp(comp))

    # create a colorscale and draw the colorlegend
    vmid = None
    if cvalues is None:
        vmin, vmax = data.min(), data.max()
    else:
        vmin, vmax = cvalues[0], cvalues[-1]
        if len(cvalues) == 3:
            vmid = cvalues[1]
    if vmid is None:
        if vmin*vmax < 0.0 and not symmetric_scale:
            vmid = 0.0
        else:
            vmid = 0.5*(vmin+vmax)

    scalev = [vmin, vmid, vmax]
    if max(scalev) > 0.0:
        logv = [abs(a) for a in scalev if a != 0.0]
        logs = np.log10(logv)
        logma = int(logs.max())
    else:
        # All data = 0.0
        logma = 0

    if logma < 0:
        multiplier = 3 * ((2 - logma) // 3)
    else:
        multiplier = 0

    CS = ColorScale(scale, vmin, vmax, vmid, 1., 1.)
    cval = np.array([CS.color(v) for v in data.flat])
    cval = cval.reshape(data.shape+(3,))
    if clageom:
        CLAx, CLAy, CLAw, CLAh = clageom
    else:
        CLAh = min(200, pf.canvas.height()-30)
        CLAx = CLAy = CLAw = CLAh // 10
    CLA = ColorLegend(CS, 256, CLAx, CLAy, CLAw, CLAh, scale=multiplier)
    drawActor(CLA)
    decorate(drawText(f"{fld.fldname} (1.e{-multiplier})",
                      (10, 260), size=18, color='black'))
    if fld.fldtype == 'node':
        draw(fld.geometry, color=cval[fld.geometry.elems], **kargs)
    else:
        draw(fld.geometry, color=cval, **kargs)


def drawActor(A):
    """Draw an actor and update the screen."""
    pf.canvas.addActor(A)
    pf.canvas.update()


def drawAny(A):
    """Draw an Actor/Annotation/Decoration and update the screen."""
    pf.canvas.addAny(A)
    pf.canvas.update()


def undraw(items):
    """Remove an item or a number of items from the canvas.

    Use the return value from one of the draw... functions to remove
    the item that was drawn from the canvas.
    A single item or a list of items may be specified.
    """
    pf.canvas.removeAny(items)
    pf.canvas.update()
#    pf.app.processEvents()


#############################################################
## views ##


# TODO: merge with view??
def viewAngles(long=0., lat=0., twist=0.):
    pf.GUI.drawlock.wait()
    orient = views.getOrientation()
    pf.canvas.setCamera(None, angles=(long, lat, twist), orient=orient)
    pf.canvas.update()
    if wait:
        pf.GUI.drawlock.lock()


def view(v, wait=True):
    """Show a named view, either a builtin or a user defined.

    This shows the current scene from another viewing angle.
    Switching views of a scene is much faster than redrawing a scene.
    Therefore this function is prefered over :func:`draw` when the actors
    in the scene remain unchanged and only the camera viewpoint changes.

    Just like :func:`draw`, this function obeys the drawing lock mechanism,
    and by default it will restart the lock to retard the next draing operation.
    """
    pf.GUI.drawlock.wait()
    if v != 'last':
        angles, orient = views.getAngles(v)
        if not angles:
            utils.warn("A view named '%s' has not been created yet" % v)
            return
        pf.canvas.setCamera(None, angles, orient)
    setView(v)
    pf.canvas.update()
    if wait:
        pf.GUI.drawlock.lock()


def createView(name, angles, addtogui=False):
    """Create a new named view (or redefine an old).

    The angles are (longitude, latitude, twist).
    The named view is global to all viewports.
    If addtogui is True, a view button to set this view is added to the GUI.
    """
    views.setAngles(name, angles)
    if addtogui:
        pf.GUI.createView(name, angles)


def setView(name, angles=None):
    """Set the default view for future drawing operations.

    If no angles are specified, the name should be an existing view, or
    the predefined value 'last'.
    If angles are specified, this is equivalent to createView(name,angles)
    followed by setView(name).
    """
    if name != 'last' and angles:
        createView(name, angles)
    setDrawOptions({'view': name})


def saveView(name, addtogui=False):
    pf.GUI.saveView(name)


def frontView():
    view("front")
def backView():
    view("back")
def leftView():
    view("left")
def rightView():
    view("right")
def topView():
    view("top");
def bottomView():
    view("bottom")
def isoView():
    view("iso")


#########################################################################
## decorations ##

def setTriade(on=None, pos='lb', siz=50, triade=None):
    """Toggle the display of the global axes on or off.

    This is a convenient feature to display the global axes
    directions with rotating actor at fixed viewport size and
    position.

    Parameters:

    - `on`: boolean. If True, the global axes triade is displayed. If
      False, it is removed. The default (None) toggles between on and off.
      The remaining parameters are only used on enabling the triade.
    - `pos`: string of two characters. The characters define the horizontal
      (one of 'l', 'c', or 'r') and vertical (one of 't', 'c', 'b') position
      on the camera's viewport. Default is left-bottom.
    - `siz`: size (in pixels) of the triade.
    - `triade`: None, Geometry or str: defines the Geometry to be used for
      representing the global axes.

      If None: use the previously set triade, or set a default if no
      previous.

      If Geometry: use this to represent the axes. To be useful and properly
      displayed, the Geometry's bbox should be around [(-1,-1,-1),(1,1,1)].
      Drawing attributes may be set on the Geometry to influence
      the appearance. This allows to fully customize the Triade.

      If str: use one of the predefined Triade Geometries. Currently, the
      following are available:

      - 'axes': axes and coordinate planes as in :class:`candy.Axes`
      - 'man': a model of a man as in data file 'man.pgf'

    """
    if on is None:
        on = not pf.canvas.hasTriade()
    if on:
        if triade is None and pf.canvas.triade is None:
            triade = 'axes'
        if triade == 'axes':
            from pyformex import candy
            triade = candy.Axes(reverse=False)
        elif triade == 'man':
            triade = Formex.read(pf.cfg['datadir'] / 'man.pgf')
        pf.canvas.setTriade(pos, siz, triade)
    else:
        pf.canvas.removeTriade()
    pf.canvas.update()
    pf.app.processEvents()


def setGrid(on=None, d=None, s=None, **kargs):
    """Toggle the display of the canvas grid on or off.

    Parameters
    ----------
    on: bool.
        If True, the grid is displayed. If False, it is removed.
        The default (None) toggles between on and off.
    d: None, int or (int,int), optional
        Only used when ``on==True``.
        Distance in pixels between the grid lines. A tuple of two values
        specifies the distance in x,y direction. If not specified, the
        previous grid is used, or a default grid with d=100
        is created.
    s: None, int or (int,int), optional
        Only used when ``on==True``.
        The grid size in pixels. A tuple of two values specifies size in
        x,y direction. If not specified the size is set equal to the
        desktop screen size. This allows resizing the window while still
        seeing the grid on the full canvas.
    kargs: optional
        Extra drawing parameters that influence the appearance of the
        grid. Example::

            setGrid(d=200,linewidth=3,color=red,ontop=True)

    Notes
    -----
    This is a convenient function to display a grid on the canvas. The grid
    may someday become an integral part of the Canvas.

    """
    if on is None:
        # toggle
        on = not pf.canvas.hasGrid()
    if on:
        # show grid
        w, h = pf.canvas.width(), pf.canvas.height()
        # anchor point is at the center
        x, y = w//2, h//2
        if s is None:
            # Use full desktop size, and anchor at the lower left
            g = pf.app.desktop().screenGeometry()
            w, h = g.width(), g.height()
            x, y = w//2, h//2
            s = (w, h)
        if d is None:
            # reuse or default
            if pf.canvas.grid is None:
                # create default
                d = 100
            else:
                # reuse previous
                grid = None
        if d is not None:
            # create grid
            if at.isInt(d):
                dx, dy = d, d
            else:
                dx, dy = d
            if at.isInt(s):
                sx, sy = s, s
            else:
                sx, sy = s
            nx, ny = int(np.ceil(float(sx)/dx/2)), int(np.ceil(float(sy)/dy/2))
            x0, y0 = x-nx*dx, y-ny*dy
            x1, y1 = x+nx*dx, y+ny*dy
            print(x0, y0, x1, y1)
            grid = decors.Grid2D(x0, y0, x1, y1, 2*nx, 2*ny, rendertype=2, **kargs)
        pf.canvas.setGrid(grid)
    else:
        # hide grid
        pf.canvas.removeGrid()
    pf.canvas.update()
    pf.app.processEvents()


def annotate(annot):
    """Draw an annotation."""
    pf.canvas.addAnnotation(annot)
    pf.canvas.update()

def unannotate(annot):
    pf.canvas.removeAnnotation(annot)
    pf.canvas.update()

def decorate(decor):
    """Draw a decoration."""
    pf.canvas.addDecoration(decor)
    pf.canvas.update()

def undecorate(decor):
    pf.canvas.removeDecoration(decor)
    pf.canvas.update()

def bgcolor(color=None, image=None):
    """Change the background color and image.

    Parameters:

    - `color`: a single color or a list of 4 colors. A single color sets a
      solid background color. A list of four colors specifies a gradient.
      These 4 colors are those of the Bottom Left, Bottom Right, Top Right
      and Top Left corners respectively.
    - `image`: the name of an image file. If specified, the image will be
      overlayed on the background colors. Specify a solid white background
      color to sea the image unaltered.
    """
    pf.canvas.setBackground(color=color, image=image)
    pf.canvas.display()
    pf.canvas.update()


def fgcolor(color):
    """Set the default foreground color."""
    pf.canvas.setFgColor(color)

def hicolor(color):
    """Set the highlight color."""
    pf.canvas.setSlColor(color)


def colormap(color=None):
    """Gets/Sets the current canvas color map"""
    return pf.canvas.settings.colormap


def colorindex(color):
    """Return the index of a color in the current colormap"""
    cmap = pf.canvas.settings.colormap
    color = np.array(color)
    i = np.where((cmap==color).all(axis=1))[0]
    if len(i) > 0:
        return i[0]
    else:
        i = len(cmap)
        print("Add color %s = %s to viewport colormap" % (i, color))
        color = color.reshape(1, 3)
        pf.canvas.settings.colormap = np.concatenate([cmap, color], axis=0)
    return i


def renderModes():
    """Return a list of predefined render profiles."""
    from pyformex.opengl.canvas import CanvasSettings
    return list(CanvasSettings.RenderProfiles.keys())


def renderMode(mode, light=None):
    """Change the rendering profile to a predefined mode.

    Currently the following modes are defined:

    - wireframe
    - smooth
    - smoothwire
    - flat
    - flatwire
    - smooth_avg
    """
    # ERROR The following redraws twice !!!
    pf.canvas.setRenderMode(mode, light)
    pf.canvas.update()
    toolbar.updateViewportButtons(pf.canvas)
    toolbar.updateNormalsButton()
    toolbar.updateTransparencyButton()
    toolbar.updateLightButton()
    pf.app.processEvents()


def wireMode(mode):
    """Change the wire rendering mode.

    Currently the following modes are defined: 'none', 'border',
    'feature','all'
    """
    modes = ['all', 'border', 'feature']
    if mode in modes:
        state = True
        mode = 1 + modes.index(mode)
    elif mode == 'none':
        state = False
        mode = None
    else:
        return
    pf.canvas.setWireMode(state, mode)
    pf.canvas.update()
    pf.app.processEvents()


def wireframe():
    renderMode("wireframe")

def smooth():
    renderMode("smooth")

def smoothwire():
    renderMode("smoothwire")

def flat():
    renderMode("flat")

def flatwire():
    renderMode("flatwire")

def smooth_avg():
    renderMode("smooth_avg")

## def opacity(alpha):
##     """Set the viewports transparency."""
##     pf.canvas.alpha = float(alpha)

def lights(state=True):
    """Set the lights on or off"""
    pf.canvas.setToggle('lighting', state)
    pf.canvas.update()
    toolbar.updateLightButton()
    pf.app.processEvents()


def transparent(state=True):
    """Set the transparency mode on or off."""
    pf.canvas.setToggle('alphablend', state)
    pf.canvas.update()
    toolbar.updateTransparencyButton()
    pf.app.processEvents()


def perspective(state=True):
    pf.canvas.setToggle('perspective', state)
    pf.canvas.update()
    toolbar.updatePerspectiveButton()
    pf.app.processEvents()


def set_material_value(typ, val):
    """Set the value of one of the material lighting parameters

    typ is one of 'ambient','specular','emission','shininess'
    val is a value between 0.0 and 1.0
    """
    setattr(pf.canvas, typ, val)
    pf.canvas.setToggle('lighting', True)
    pf.canvas.update()
    pf.app.processEvents()

def set_light(light, **args):
    light = int(light)
    pf.canvas.lights.set(light, **args)
    pf.canvas.setToggle('lighting', True)
    pf.canvas.update()
    pf.app.processEvents()

def set_light_value(light, key, val):
    light = int(light)
    pf.canvas.lights.set_value(light, key, val)
    pf.canvas.setToggle('lighting', True)
    pf.canvas.update()
    pf.app.processEvents()


def linewidth(wid):
    """Set the linewidth to be used in line drawings."""
    pf.canvas.setLineWidth(wid)

def linestipple(factor, pattern):
    """Set the linewidth to be used in line drawings."""
    pf.canvas.setLineStipple(factor, pattern)

def pointsize(siz):
    """Set the size to be used in point drawings."""
    pf.canvas.setPointSize(siz)


def canvasSize(width, height):
    """Resize the canvas to (width x height).

    If a negative value is given for either width or height,
    the corresponding size is set equal to the maximum visible size
    (the size of the central widget of the main window).

    Note that changing the canvas size when multiple viewports are
    active is not approved.
    """
    pf.canvas.changeSize(width, height)


# This is not intended for the user
def clear_canvas(sticky=False):
    pf.canvas.removeAll(sticky)
    pf.canvas.triade = None
    pf.canvas.grid = None
    pf.canvas.clearCanvas()


def clear(sticky=False):
    """Clear the canvas.

    Removes everything from the current scene and displays an empty
    background.

    This function waits for the drawing lock to be released, but will
    not reset it.
    """
    pf.GUI.drawlock.wait()
    clear_canvas(sticky)
    pf.canvas.update()


def redraw():
    pf.canvas.redrawAll()
    pf.canvas.update()


def saveCanvas(fn=None):
    if fn is None:
        fn = askNewFilename(pf.cfg['workdir'], 'all')
    if fn:
        PzfFile(fn).save(_canvas=True)
        print("Saved Canvas Settings to '%s'" % fn)


def loadCanvas(fn=None):
    if fn is None:
        fn = askFilename(pf.cfg['workdir'], ['pzf', 'all'])
    if fn:
        print("Loading Canvas Settings from '%s'" % fn)
        if fn.endswith('.pzf'):
            res = PzfFile(fn).load()
            canvas = res.get('_canvas', None)
            if canvas:
                pf.GUI.viewports.loadConfig(canvas)
        else:
            pf.GUI.viewports.load(fn)


def select(*args):
    """Select exported symbols in geometry_menu"""
    pf.GUI.selection['geometry'].set(args)


###########################################################################
# Make _I, _G, _C, _T be included when doing 'from gui.draw import *'
#

__all__ = [n for n in list(globals().keys()) if not n.startswith('_')] + ['_I', '_G', '_C', '_T']


#######################################################
## deprecated ##

@utils.deprecated_by("drawText3D", "drawText")
def drawText3D(*args, **kargs):
    return drawText(*args, **kargs)


## End
