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
"""Specialized dialogs for the pyFormex GUI.

This module provides some dialogs that collect specific input for some
pyFormex GUI function. Most of these dialogs are normally accessed from
the GUI menus. But the user can also use these in his scripts.
"""
import pyformex as pf
from pyformex import utils
from pyformex.path import Path
from pyformex.script import chdir
from pyformex.gui.widgets import Dialog, _I, _C, _G, _T, InputBool
from pyformex.gui import image
from pyformex.gui import qtutils


def addToSidebar(path):
    key = 'gui/sidebardirs'
    if key not in pf.prefcfg.keys():   # keys() required here!
        pf.prefcfg[key] = pf.refcfg[key].copy()
    path = Path(path).expanduser().absolute()
    if not path.is_dir():
        path = path.parent
    pf.prefcfg[key].append(path)


class FileDialog(Dialog):
    """A customizable file selection Dialog.

    This is a specialized Dialog for the input of one or more file or
    directory paths. It includes a customized QFileDialog and being
    subclassed from Dialog, it can be easily further customized to add
    more input fields.

    Parameters
    ----------
    path: :term:`path_like`
        The initial path displayed in the file selector widget.
    filter: list of str
        The filters for the files selectable in the file selector widget.
    mode: str
        Determines what can be selected. One of:

        - 'file': select a file (existing or not). This is the default.
        - 'exist': select an existing file
        - 'dir': select an existing directory (widget allows to create a new)
        - 'any': select a file (existing or not) or a directory
        - 'multi': select multiple existing paths from the same directory
    compr: bool
        If True, the specified filters will be expanded to also include
        compressed files of the specified patterns. Compression algorithms
        include 'gz' and 'bz2'. For example, a filter 'Python files (\\*.py)'
        would be changed to 'Python files (\\*.py \\*.py.gz \\*.py.bz2)'.
    auto_suffix: bool
        If True (default), new file names will automatically be changed
        to have an extension matching the current filter.
        If False, any name is accepted as a new file name.
    sidebar: list
        A list of :term:`path_like` strings to add to the sidebar of the
        file selection widget. This is typically used to provide shortcuts
        to often used directories.
    extra: list
        A list of input items to be added to the FileDialog. No input item
        should be named 'filename'.
    kargs:
        Other keyword parameters to be passed to the :class:`Dialog` super
        class.

    Returns
    -------
    dict
        The results dict of the Dialog. If the selection was accepted,
        this will at least include a key 'filename' with the path of
        the selected file or files or directory. If extra items were
        specified, there will be keys corresponding to the item names.

    See Also
    --------
    GeometryFileDialog: A FileDialog to select a pyFormex Geometry File (PGF)
    ProjectDialog: A FileDialog to select a pyFormex Project File (PYF)
    ImageSaveDialog: A FileDialog for saving the rendering to an image file

    """
    message = {
        'file': 'Select a file, existing or new',
        'exist': 'Select an existing file',
        'dir': 'Select a directory',
        'any': 'Select a file or a directory',
        'multi': 'Select multiple existing paths from one directory',
        }

    def __init__(self, path='.', filter='*', *, mode='file',
                 compr=False, auto_suffix=True,
                 sidebar=[], add_to_sidebar=False, chdir=False,
                 extra=[], enablers=[],
                 caption="pyFormex File Dialog",
                 **kargs):
        """Create the dialog."""
        pf.verbose(3, f"FILEDIALOG mode {mode} kargs {kargs}")
        items=[
            _I('filename', path, itemtype='file', filter=filter, mode=mode,
               compr=compr, auto_suffix=auto_suffix, sidebar=sidebar, text=''),
            ] + extra
        # TODO: if we want to make the auto_suffix a dialog item,
        # we have to connect the changing of the auto_suffix value to an
        # auto_suffix setter on the filename item.

        super().__init__(items=items, enablers=enablers, modal=False,
                         caption=caption, parent=pf.GUI,
                         message=FileDialog.message[mode])

        layout = self['filename'].input.layout()
        if add_to_sidebar is not None:
            self.sidebar = InputBool(
                '_sidebar', add_to_sidebar, text='Add to sidebar')
            layout.addWidget(self.sidebar,2,2)
        if chdir is not None:
            self.chdir = InputBool(
                '_chdir', chdir, text='Change workdir')
            layout.addWidget(self.chdir,3,2)
            self.mode = mode


    def selectFile(self,fn):
        """Set the current selection on the file widget"""
        self['filename'].input.selectFile(fn)


    def close(self):
        """Perform additional actions on close"""
        if self.results:
            if hasattr(self,'sidebar') and self.sidebar.value():
                addToSidebar(self.results['filename'])
            if hasattr(self,'chdir') and self.chdir.value():
                dirname = self.results['filename']
                if self.mode == 'multi':
                    dirname = dirname[0]
                elif self.mode != 'dir':
                    dirname = dirname.parent
                chdir(dirname)
        return super().close()


class GeometryFileDialog(FileDialog):
    """A file selection dialog specialized for opening .pgf files.

    """
    def __init__(self, path=None, filter='pgf', *,
                 fmode='binary', compression=4,
                 intend=None, convert=True,
                 **kargs):
        """Create the dialog."""
        print(f"KARGS1 {kargs}")
        kargs.setdefault('caption', "pyFormex Geometry File Dialog")
        # TODO: should set mode based on access and exist
        kargs['mode'] = 'file'
        exist = kargs.setdefault('exist', False)
        if intend == 'r':
            access = ['r']
        elif intend == 'w':
            access = ['wr', 'rw', 'w']
        else:
            access = ['wr', 'rw', 'w', 'r']
        extra = [
            _I('access', itemtype='radio', text="Access Mode", choices=access,
               spacer='r',
               tooltip="wr=read if exist; rw=must exist; w=overwrite; r=readonly"
            )]
        if 'w' in access:
            extra.extend([
                _I('mode', fmode, itemtype='radio', text="Write mode",
                   choices=['binary', 'ascii', 'short lines ascii'],
                   tooltip="'binary' produces smaller files, "
                   "'short lines ascii' is easier to edit, "
                   "'ascii' types may be compressed to produce smaller files",
                ),
                _I('compression', compression, itemtype='slider',
                   min=0, max=9, ticks=1,
                   text="Compression level (0-9)",
                   tooltip="Higher compression levels result in smaller "
                   "files, but higher load and save times."
                )
            ])
        print(f"KARGS2 {kargs}")
        super().__init__(path, filter='pgf', extra=extra, **kargs)


class ProjectDialog(FileDialog):
    """A file selection dialog specialized for opening projects."""
    def __init__(self, path=None, filter='pyf', *,
                 compression=4, protocol=None, access=None,
                 default=None, convert=True,
                 **kargs):
        """Create the dialog."""
        from pyformex import project
        import pickle

        kargs.setdefault('caption', "pyFormex Project File Dialog")
        exist = kargs.get('exist', False)
        if access is None:
            access = ['rw', 'r'] if exist else ['wr', 'rw', 'w', 'r']
        extra = [
            _I('access', itemtype='radio', text="Access Mode", choices=access,
               spacer='r',
               tooltip="wr=read if exist; rw=must exist; w=overwrite; r=readonly"
            ),
        ]
        if exist:
            extra.append(
                _I('convert', convert,
                   text="Automatically convert file to latest format",
                   tooltip="It is recommended to automatically convert your "
                   "project files to the latest format, to avoid future "
                   "compatibility problems. The only reason to not convert "
                   "is if you still need to read your files with older "
                   "versions of pyFormex. The conversion will not be "
                   "performed if pyFormex can not correctly read your file.",
                ))
        if not exist:
            if protocol is None:
                protocol = project.default_protocol
            extra.extend([
                _I('protocol', protocol, itemtype='int',
                   text="Protocol",
                   min=0, max=pickle.HIGHEST_PROTOCOL, ticks=1,
                   tooltip = "Use at most protocol 2 if you need to read "
                   "back the project from Python2 version"
                ),
                _I('compression', compression, itemtype='slider',
                   min=0, max=9, ticks=1,
                   text="Compression level (0-9)",
                   tooltip="Higher compression levels result in smaller "
                   "files, but higher load and save times."
                )
            ])
        super().__init__(path, filter='pyf', extra=extra, **kargs)


class SaveImageDialog(FileDialog):
    """A dialog for saving an image to a file.

    This is a specialized Dialog for the input of all data required to
    save the current pyFormex rendering to an image file. It is a
    convenient interactive frontend for the :func:`image.saveImage`
    function. The Dialog ask for the target file name and all the
    other parameters accepted by that function.

    Parameters
    ----------
    path: :term:`path_like`
        The initial path displayed in the file selector widget.
        See FileDialog.
    filer: list of str
        The filters for the files selectable in the file selecter widget.
        See FileDialog.
    multi: bool
        If True, the dialog will show the multisave option initially
        checked.

    """
    default_size = None

    def __init__(self, path=None, filter=['img', 'icon', 'all'], *, multi=False):
        """Create the dialog."""
        if SaveImageDialog.default_size is None:
            # Late initialization because pf.canvas needed
            SaveImageDialog.default_size = pf.canvas.getSize()

        kargs = {}
        kargs['caption'] = "pyFormex Save Image Dialog"
        kargs['exist'] = False
        extra=[
            _C('',[
                _I('extent', choices=image.image_extents(),
                   text="Extent:",
                   func=self.change_extent,
                   tooltip="The part(s) of the pyFormex window to be saved"),
                _I('tool', choices=image.image_tools(),
                   text="Tool:",
                   # func=self.change_tool,  # can not do both !!
                   tooltip="The tool to be used for saving the image."
                   " The possible extents and formats depend on it."),
               _I('set_size', choices=['No', 'Width', 'Height', 'Both'],
                   text='Set Size:',
                   tooltip="Adjust one or both image dimensions. Beware, "
                   " this may give incorrect results if transparency is used."),
                _I('size', itemtype='ivector',
                   value=SaveImageDialog.default_size,
                   fields=['W', 'H'],
                   text="Size:",
                   tooltip="The size of the save image."),
            ], newline=True),
            _C('',[
                _I('format', choices=['From Extension'],
                   text="Format:",
                   tooltip="The image format to be used. Normally derived from"
                   "extension"),
                _I('quality', -1, min=-1, max=100,
                   text="Quality:",
                   tooltip="For compressed image formats (like JPG), specifies"
                   " the compression level (PNG:0..9; JPEG: 1..100"),
                _I('alpha', False, text="Keep Alpha",
                   tooltip="Keep the alpha channel in the result (Experimental!)"),
            ], spacer='l'),
            _C('',[
                _I('multi', False,
                   text="Multisave mode",
                   tooltip="In multisave mode you can save sequences of images,"
                   " by pressing a hotkey and/or automatically on drawing"),
                _I('hotkey', True,
                   text="Activate hotkey",
                   tooltip=f"A new image will be saved every time you hit the hotkey"
                   f" ({pf.cfg['keys/save']}) while the focus is on the canvas"),
                _I('autosave', False,
                   text="Activate ausave mode",
                   tooltip="In autosave mode, a new image will be saved"
                   " at each draw operation"),
            ], spacer='l'),
        ]
        enablers=[
            ('multi', True, 'hotkey', 'autosave'),
            ('set_size', 'Width', 'size'),
            ('set_size', 'Height', 'size'),
            ('set_size', 'Both', 'size'),
        ]

        super().__init__(path, filter, extra=extra, enablers=enablers, **kargs)
        self.change_extent(self['extent'])

    # !! only one of change_tool or change_extent can be activated
    def change_tool(self, item):
        tool = item.value()
        self['extent'].setChoices(image.extent_options(tool))
        formats = ['From Extension'] + image.imageFormats(tool, 'w')
        self['format'].setChoices(formats)


    def change_extent(self, item):
        extent = item.value()
        tools = image.tool_options(extent)
        self['tool'].setChoices(tools)
        self['tool'].setValue(tools[0])
        formats = ['From Extension'] + image.imageFormats(tools[0], 'w')
        self['format'].setChoices(formats)


    def validate(self):
        if super().validate():
            res = self.results
            w, h = SaveImageDialog.default_size = res['size']
            resize = res['set_size'][0]
            if resize == 'W':
                h = -1
            elif resize == 'H':
                w = -1
            elif resize == 'N':
                w = h = -1    # This would use unscaled offline rendering
            res['size'] = (w, h)
            if resize == 'N':
                res['size'] = None  # Instead grab from screen buffer
            if res['format'] == 'From Extension':
                res['format'] = None
        return self.valid


class RecordSessionDialog(FileDialog):
    """A dialog for recording the GUI to a video file.

    This is a specialized Dialog for the input of all data required to
    save the current pyFormex rendering to an image file. It is a
    convenient interactive frontend for the :func:`image.saveImage`
    function. The Dialog ask for the target file name and all the
    other parameters accepted by that function.

    Parameters
    ----------
    path: :term:`path_like`
        The initial path displayed in the file selector widget.
        See FileDialog.
    filer: list of str
        The filters for the files selectable in the file selecter widget.
        See FileDialog.

    """
    def __init__(self, path=None, filter=['video', 'all']):
        """Create the dialog."""
        extra = [
            _C('',[
                _I('extent', choices=image.record_extents,
                   text="Extent:",
                   tooltip="The part(s) of the pyFormex window to be saved"),
            ]),
            _C('',[
                _I('framerate', 25,
                   text="framerate:",
                   tooltip="The number of frames saved per second."),
            ], spacer='l'),
        ]

        super().__init__(path, filter, extra=extra,
                       caption="pyFormex Record Session Dialog")
