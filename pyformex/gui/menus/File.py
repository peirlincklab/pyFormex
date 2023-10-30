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
"""Functions from the File menu.

"""
import pyformex as pf
from pyformex import Path
from pyformex import utils
from pyformex import project

from .Settings import updateSettings
from .. import dialogs
from .. import draw
from .. import image
from ..widgets import _I, _G


##################### handle project files ##########################

def openProject(fn=None, exist=False, access=['wr', 'rw', 'w', 'r'],
                default=None):
    """Open a (new or old) Project file.

    A :class:`~gui.dialogs.ProjectDialog` is shown to ask the user for
    a Project file name and the access modalities. The parameters are used
    to set some sensible defaults and delimit the options.
    Depending on he results of the dialog, either a new project is created
    or an old one is opened, or nothing is done.

    Parameters
    ----------
    fn: :term:`path_like`
        If specified, the Project file dialog is shown with this file
        initially selected. If not specified, the dialog starts with an
        empty file name in the current directory.
    exist: bool
        If True, only existing Projects can be selected and the function
        will work like :func:`openExistingProject`. If False (default),
        the user can create new project files as well as open existing ones.
    access: list of str
        A list of :class:`Project` access modes to be presented to
        the user. The possible access modes are:

        - 'wr': open in write mode but read the project first if it exist,
        - 'rw': like 'wr', but the project must exist (and be read first),
        - 'w': overwrite the project if it exists,
        - 'r': open for read only."
    default: str
        The access mode that is initially selected in the dialog.
        If not provided, the first option of ``access`` will be used.

    Returns
    -------
    Project | None
        The opened Project, or None if the user canceled the dialog.
    """
    if isinstance(access, str):
        access = [access]
    cur = fn if fn else '.'
    res = dialogs.ProjectDialog(
        cur, ['pyf', 'all'], exist=exist, access=access,
        default=default, convert=True).getResults()
    if not res:
        return

    # OK, we have all data, now create/open the project
    print(f"Opening project {fn}")
    print(f"with params {res}")
    signature = pf.fullVersion()
    with draw.busyCursor():  # loading  may take a while
        proj = project.Project(signature=signature, **res)
    if proj.signature != signature:
        pf.warning("The project was written with %s, while you are now running %s. If the latter is the newer one, this should probably not cause any problems. Saving is always done in the current format of the running version. Save your project and this message will be avoided on the next reopening." % (proj.signature, signature))

    proj.hits = 0
    pf.debug("START COUNTING HITS", pf.DEBUG.PROJECT)
    return proj


def readProjectFile(fn):
    """Read a project from file fn.

    Parameters
    ----------
    fn: :term:`path_like`
        The name of the project file to read.

    Returns
    -------
    Project | None
        The loaded Project if the file was successfully read, else None.

    Notes
    -----
        Reading a Project file does not make that Project the current Project.
        See :func:`SetProject`.
    """
    if fn.exists():
        try:
            proj = project.Project(fn, access='wr')
            return proj
        except Exception:
            pass

    pf.warning("The project file '%s' could not be loaded" % fn)
    return None


def setProject(proj):
    """Make the specified project the current project.

    Parameters
    ----------
    proj: Project
        An open Project, such as returned by :func:`readProjectFile`.

    .. note: The remainder is obsolete

    The user is asked for a Project file name and the access modalities.
    Depending on the results of the dialog:

    - either an new project is create or an old is opened,
    - the old data may be discarded, added to the current pyFormex globals,
      or replace them
    - the opened Project may become the current Project, or its data are
      just imported in the current Project.


    The default will let the user create new project files as well as open
    existing ones.
    Use create=False or the convenience function openProject to only accept
    existing project files.

    If a compression level (1..9) is given, the contents will be compressed,
    resulting in much smaller project files at the cost of

    Only one pyFormex project can be open at any time. The open project
    owns all the global data created and exported by any script.

    If makeDefault is True, an already open project will be closed and
    the opened project becomes the current project.
    If makeDefault is False, the project data are imported into pf.PF
    and the current project does not change. This means that if a project was
    open, the imported data will be added to it.

    If addGlobals is None, the user is asked whether the current globals
    should be added to the project. Set True or False to force or reject
    the adding without asking.
    """
    print("Setting current project to %s" % proj.filename)
    print("Project contents: %s" % proj.contents())
    keep = {}
    if pf.PF:
        print("Current pyFormex globals: %s" % pf.PF.contents())
        _delete = "Delete"
        _add = "Keep non existing"
        _overwrite = "Keep all (overwrite project)"
        res = draw.ask("What shall I do with the current pyFormex globals?", [_delete, _add, _overwrite])
        if res == _add:
            keep = utils.removeDict(pf.PF, proj)
        elif res == _overwrite:
            keep = pf.PF
    pf.PF = proj
    if keep:
        pf.PF.update(keep)
    if pf.PF.filename:
        updateSettings({
            'curproj': pf.PF.filename,
            'workdir': Path(pf.PF.filename).parent,
            }, save=True)
    pf.GUI.setcurproj(pf.PF.filename)

    if hasattr(proj, '_autoscript_'):
        _ignore = "Ignore it!"
        _show = "Show it"
        _edit = "Load it in the editor"
        _exec = "Execute it"
        res = draw.ask("There is an autoscript stored inside the project.\nIf you received this project file from an untrusted source, you should probably not execute it.", [_ignore, _show, _edit, _exec])
        if res == _show:
            res = draw.showText(proj._autoscript_)  # ,actions=[_ignore,_edit,_show])
            return
        if res == _exec:
            draw.playScript(proj._autoscript_)
        elif res == _edit:
            fn = "_autoscript_.py"
            draw.checkWorkdir()
            f = open(fn, 'w')
            f.write(proj._autoscript_)
            f.close()
            openScript(fn)
            editApp(fn)

    if hasattr(proj, 'autofile') and draw.ack("The project has an autofile attribute: %s\nShall I execute this script?" % proj.autofile):
        draw.processArgs([proj.autofile])

    listProject()


def createProject():
    """Open an new project.

    Ask the user to select an existing project file, and then open it.
    """
    closeProject()
    proj = openProject(pf.PF.filename, exist=False)
    if proj is not None:  # a project was selected
        setProject(proj)


def openExistingProject():
    """Open an existing project.

    Ask the user to select an existing project file, and then open it.
    """
    closeProject()
    proj = openProject(pf.PF.filename, exist=True)
    if proj is not None:  # a project was selected
        setProject(proj)


def importProject():
    """Import an existing project.

    Ask the user to select an existing project file, and then import
    all or selected data from it into the current project.
    """
    proj = openProject(exist=True, access='r')
    if proj:  # only if non-empty
        keys = proj.contents()
        res = draw.askItems(
            [_I('mode', choices=['All', 'Defined', 'Undefined', 'Selected', 'None'], itemtype='radio'),
                _I('selected', choices=keys, itemtype='select'),
                ],
            caption='Select variables to import',
            )
        if res:
            mode = res['mode'][0]
            if mode == 'A':
                pass
            elif mode == 'D':
                proj = utils.selectDict(proj, pf.PF)
            elif mode == 'U':
                proj = utils.removeDict(proj, pf.PF)
            elif mode == 'S':
                proj = utils.selectDict(proj, res['selected'])
            elif mode == 'N':
                return
            print("Importing symbols: %s" % proj.contents())
            pf.PF.update(proj)
            listProject()


def setAutoScript():
    """Set the current script as autoScript in the project"""
    if pf.cfg['curfile'] and pf.GUI.canPlay:
        pf.PF._autoscript_ = open(pf.cfg['curfile']).read()


def setAutoFile():
    """Set the current script/app as autofile in the project"""
    if pf.cfg['curfile'] and pf.GUI.canPlay:
        pf.PF.autofile = pf.cfg['curfile']


def removeAutoScript():
    delattr(pf.PF, '_autoscript_')


def removeAutoFile():
    delattr(pf.PF, 'autofile')


def saveProject():
    """Save the current project.

    If the current project is a named one, its contents are written to file.
    This function does nothing if the current project is a temporary one.
    """
    if pf.PF.filename is not None:
        print("Saving Project contents: %s" % pf.PF.contents())
        # Always put the current version is projects saved from file menu!
        pf.PF.signature = pf.fullVersion()
        with draw.busyCursor():
            pf.PF.save()


def saveAsProject():
    """Save the current project under a new name.

    A new project file is created, with the contents of the current project.
    The new project file becomes the current one.
    """
    proj = openProject(pf.PF.filename, exist=False, access=['w'], default='w')
    #
    #
    # TODO: can we do proj.update(pf.PF) and pf.PF = proj instead ?
    #
    if proj is not None:  # even if empty
        pf.PF.filename = proj.filename
        pf.PF.gzip = proj.gzip
        pf.PF.access = proj.access
        pf.PF.signature = proj.signature
        pf.PF.mode = proj.mode
        pf.PF.protocol = proj.protocol
        saveProject()
    if pf.PF.filename is not None:
        updateSettings({
            'curproj': pf.PF.filename,
            'workdir': Path(pf.PF.filename).parent,
            }, save=True)
        pf.GUI.setcurproj(pf.PF.filename)


def listProject():
    """Print all global variable names."""
    print("pyFormex globals: %s" % pf.PF.contents())

def clearProject():
    """Clear the contents of the current project."""
    pf.PF.clear()

def closeProject(save=None, clear=None):
    """Close the current project, saving it or not.

    Parameters:

    - `save`: None, True or False. Determines whether the project should be
      saved prior to closing it. If None, it will be asked from the user.
      Note that this parameter is only used for named Projects. Temporary
      Projects are never saved implicitely.
    - `clear`: None, True or False.
    """
    if pf.PF.filename is not None:
        if save is None:
            save = draw.ack("Save the current project before closing it?")
        print("Closing project %s (save=%s)" % (pf.PF.filename, save))
        if save:
            saveProject()
            if pf.PF:
                listProject()
                if clear is None:
                    clear = draw.ask("What shall I do with the existing globals?", ["Delete", "Keep"]) == "Delete"

    if clear:
        pf.PF.clear()

    pf.PF.filename = None
    pf.GUI.setcurproj('None')
    updateSettings({
        'curproj': pf.PF.filename,
        }, save=True)


def closeProjectWithoutSaving():
    """Close the current project without saving it."""
    closeProject(False)


def convertProjectFile():
    proj = openProject(pf.PF.filename, access=['c'], default='c', exist=True)
    if proj is not None:
        pf.debug("Converting project file %s" % proj.filename, pf.DEBUG.PROJECT|pf.DEBUG.INFO)
        proj.convert(proj.filename.replace('.pyf', '_converted.pyf'))


def uncompressProjectFile():
    proj = openProject(pf.PF.filename, access=['u'], default='u', exist=True)
    if proj is not None:
        proj.uncompress(proj.filename.replace('.pyf', '_uncompressed.pyf'))


##################### handle script files ##########################

def openScript(fn=None, exist=False, create=False):
    """Open a pyFormex script and set it as the current script.

    If no filename is specified, a file selection dialog is started to select
    an existing script, or allow to create a new file if exist is False.

    If the file exists and is a pyFormex script, it is set ready to execute.

    If the file is empty or create is True, a default pyFormex script
    template will be written to the file, overwriting the contents if the
    file existed. Then, the script is loaded into the editor.
    """
    if fn is not None:
        fn = Path(fn)
    else:
        mode='exist' if exist else 'file'
        fn = draw.askFilename(pf.cfg['curfile'], 'pyformex', mode=mode)
    if fn:
        if create and fn.exists() and fn.size > 0:
            if not draw.ack(f"The file {fn} exists and is not empty.\n "
                            f"Are you sure you want to overwrite it?"):
                return None
        create = create or not fn.exists() or fn.size == 0
        if create:
            template = pf.cfg['scripttemplate']
            if template.exists():
                template.copy(fn)
        updateSettings({'workdir': fn.parent}, save=True)
        draw.chdir(fn)
        pf.GUI.setcurfile(fn)
        pf.GUI.scripthistory.add(fn)
        if create:
            draw.editFile(fn)
    return fn


def editApp(appname=None):
    """Edit an application source file.

    If no appname is specified, the current application is used.

    This loads the application module, gets its file name, and if
    it is a source file or the the corresponding source file exists,
    that file is loaded into the editor.
    """
    if appname is None:
        appname = pf.cfg['curfile']

    if utils.is_script(appname):
        # this is a script, not an app
        fn = Path(appname)

    else:
        from pyformex import apps
        app = apps.load(appname)
        if app is None:
            fn = apps.findAppSource(appname)
        else:
            fn = apps.findAppSource(app)
        if not fn.exists():
            draw.showWarning("The file '%s' does not exist" % fn)
            return

    draw.editFile(fn)


##################### other functions ##########################


def saveImage(multi=False):
    """Save an image to file.

    Show the Save Image dialog, with the multisave mode checked if
    multi = True. Then, depending on the user's selection, either:

     - save the current Canvas/Window to file
     - start the multisave/autosave mode
     - do nothing
    """
    dia = dialogs.SaveImageDialog(multi=multi)
    res = dia.getResults()

    if res:
        pf.verbose(3, res)
        del res['set_size']
        pf.debug(res, pf.DEBUG.IMAGE)
        # updateSettings({'workdir': Path(opt.fn).parent}, save=True)
        image.saveImage(**res)


def startMultiSave():
    """Start/change multisave mode."""
    saveImage(True)


def stopMultiSave():
    """Stop multisave mode."""
    image.saveImage()


def saveIcon():
    """Save an image as icon.

    This will show the Save Image dialog, with the multisave mode off and
    asking for an icon file name. Then save the current rendering to that file.
    """
    ## We should create a specialized input dialog, asking also for the size
    fn = draw.askNewFilename(filter='icon')
    if fn:
        image.saveIcon(fn, size=32)

viewer = None
def showImage():
    """Display an image file."""
    from pyformex.gui.imageViewer import ImageViewer
    global viewer
    fn = draw.askFilename(filter='img')
    if fn:
        viewer = ImageViewer(pf.app, fn)
        viewer.show()


def listAll():
    print(pf.PF)



def createMovieInteractive():
    """Create a movie from a saved sequence of images.

    """
    if not image.multisave:
        pf.warning('You need to start multisave mode first!')
        return

    names = image.multisave['filename']
    glob = names.glob()

    res = draw.askItems(
        [_I('files', glob),
          _I('encoder', choices=['mencoder', 'convert', 'ffmpeg']),
          _G('Mencoder', [
              _I('fps', 10),
              _I('vbirate', 800),
              ]),
          _G('Convert', [
              _I('delay', 1),
              _I('colors', 256),
              ]),
          ],
        enablers = [
            ('encoder', 'mencoder', 'Mencoder'),
            ('encoder', 'convert', 'Convert'),
          ])
    if not res:
        return

    with draw.busyCursor():
        image.createMovie(**res)



#
# TODO: this no longer works with the new webgl; should redo
#
# def exportPGF():
#     """Export the current scene to PGF"""
#     from pyformex.plugins.webgl import WebGL
#     fn = draw.askNewFilename(pf.cfg['workdir'], ['pgf', 'all'])
#     if fn:
#         with draw.busyCursor():
#             print("Exporting current scene to %s" % fn)
#             fn = fn.with_suffix('.pgf')
#             W = WebGL(fn.stem)
#             W.addScene()
#             res = W.exportPGF(fn, sep='')
#             print("Contents: %s" % res)


last_exported_webgl = None

def exportWebGL():
    """Export the current scene to WebGL

    The user is asked for a file name to store the exported model,
    and after export, whether to load the model in the browser.
    """
    global last_exported_webgl
    last_exported_webgl = None
    fn = draw.askNewFilename(pf.cfg['workdir'], 'html')
    if fn:
        last_exported_webgl = draw.exportWebGL(fn)


def multiWebGL():
    """Export the current scene as a model in a multiscene WebGL

    The user is asked for a file name to store the exported model,
    and after export, whether to load the model in the browser.
    """
    global last_exported_webgl
    last_exported_webgl = None
    if draw.the_multiWebGL is None:
        print("NO CURRENT EXPORT")
    else:
        print("CURRENTLY EXPORTED: %s" % draw.the_multiWebGL.scenes)

    if draw.the_multiWebGL is None:
        fn = draw.askNewFilename(pf.cfg['workdir'], 'html')
        if fn:
            print("Exporting multiscene WebGL to %s" % fn)
            draw.multiWebGL(fn=fn)
            print(draw.the_multiWebGL)

    if draw.the_multiWebGL is not None:
        res = draw.askItems([
            _I('name', draw.the_multiWebGL.name, text='Name of the scene', tooltip='An empty name will skip the export of the current scene'),
            _I('finish', False, text='Finish the export'),
            ])
        if res['name']:
            draw.multiWebGL(res['name'])
        if res['finish']:
            last_exported_webgl = draw.multiWebGL()


def showWebGL():
    """Show the last WebGL model.

    """
    if last_exported_webgl and last_exported_webgl.exists():
        draw.showHtml(last_exported_webgl)


def recordSession():
    """Record the current pyFormex session."""
    pf.debug("RECORDING with dri=%s" % pf.options.dri, pf.DEBUG.IMAGE)
    utils.External.require('ffmpeg')
    dia =  dialogs.RecordSessionDialog(pf.cfg['workdir'])
    res = dia.getResults()
    if res:
        image.recordSession(**res)


MenuData = ('File', [
    ('Exit', draw.closeGui),
    ('---', None),
    ('Start new project', createProject),
    ('Open new/existing project', openExistingProject),
    ('Import a project', importProject),
    ('Set current script as AutoScript', setAutoScript),
    ('Remove the AutoScript', removeAutoScript),
    ('Set current script as AutoFile', setAutoFile),
    ('Remove the AutoFile', removeAutoFile),
    ('List project contents', listAll),
    ('Save project', saveProject),
    ('Save project As', saveAsProject),
    ('Clear project', clearProject),
    ('Close project', closeProject),
    # ('---', None),
    ('Convert Project File', convertProjectFile),
    ('Uncompress Project File', uncompressProjectFile),
    ('---', None),
    ('Change workdir', draw.askDirname),
    ('Open pyFormex script', openScript),
    ('Edit current script/app', editApp),
    ('Run current script/app', draw.play),
    ('Reload and run current app', draw.replay),
    ('---', None),
    ('Save Image', saveImage),
    ('Start MultiSave', startMultiSave),
    ('Save Next Image', image.saveNext),
    ('Create Movie', createMovieInteractive),
    ('Stop MultiSave', stopMultiSave),
    ('Save as Icon', saveIcon),
    ('Show Image', showImage),
    ## ('Export as PGF', exportPGF),
    ('Export as WebGL', exportWebGL),
    ('Export as multiscene WebGL', multiWebGL),
    ('Show exported WebGL', showWebGL),
    ('Show HTML', draw.showHtml),
    ('Record Session', recordSession),
    ])

# End
