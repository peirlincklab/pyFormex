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
"""Saving OpenGL renderings to image files.

This module defines some functions that can be used to save the
OpenGL rendering and the pyFormex GUI to image files. There are even
functions for automatically saving multiple renderings to a series of
files, for creating a movie from these images and for recording the GUI
directly to a video file.

The most important functions in this module are

- :func:`saveImage`: save (parts of) the GUI to an image file
- :func:`recordSession`: record (parts of) the GUI to a video file
"""

from PIL import Image

import pyformex as pf
from pyformex import utils
from pyformex import Path
from pyformex.gui import QtGui
from pyformex.gui import qtutils

# global parameters for multisave mode
multisave = None

# imported module
gl2ps = None

# The image formats recognized by pyFormex
image_formats = {
    'qt': None,
    'pil': None,
    'magick': None,
    'gl2ps': None,
}


def get_image_formats_qt():
    """List the image formats supported by :class:`~Qt.QtGui.QImage`

    Returns
    -------
    formats_r: list of str
        List of image formats that can be read by QImage
    formats_w: list of str
        List of image formats that can be written by QImage
    """
    formats_r = [f.toStr() for f in QtGui.QImageReader.supportedImageFormats()]
    formats_w = [f.toStr() for f in QtGui.QImageWriter.supportedImageFormats()]
    return formats_r, formats_w


def get_image_formats_pil():
    """List the image formats supported by PIL

    Returns
    -------
    formats_r: list of str
        List of image formats that can be read by PIL
    formats_w: list of str
        List of image formats that can be written by PIL
    """
    Image.init()
    formats_r = [f.strip('.') for f in Image.EXTENSION]
    formats_w = formats_r
    return formats_r, formats_w


def get_image_formats_magick():
    """List the image formats supported by ImageMagick

    Returns
    -------
    formats_r: list of str
        List of image formats that can be read by ImageMagick
    formats_w: list of str
        List of image formats that can be written by ImageMagick
    """
    if not utils.External.has('imagemagick'):
        # ImageMagick not installed/detected
        return [], []
    # Detection with external ImageMagick command
    P = utils.system("identify -list format")
    if P.returncode != 0:
        return [], []
    formats_r = []
    formats_w = []
    ok = False
    for line in P.stdout.split('\n'):
        if line[:8] == '-'*8:
            ok = True
            continue
        s = line.split()
        if len(s) > 3:
            fmt, mod, sup = s[:3]
            if fmt == '*':
                break
            if len(sup) != 3:
                continue
            fmt = fmt.strip('*').lower()
            if sup[0] == 'r':
                formats_r.append(fmt)
            if sup[1] == 'w':
                formats_w.append(fmt)
    return formats_r, formats_w


def get_image_formats_gl2ps():
    """List the image formats supported by gl2ps

    Returns
    -------
    formats_r: list of str
        An empty list, since gl2ps is write only.
    formats_w: list of str
        List of image formats that can be written by gl2ps
    """
    global gl2ps, _producer, _gl2ps_types
    if utils.Module.has('gl2ps'):
        import gl2ps
        # set some globals
        _producer = f"{pf.Version()} ({pf.cfg['help/website']})"
        _gl2ps_types = {
            'ps': gl2ps.GL2PS_PS,
            'eps': gl2ps.GL2PS_EPS,
            'tex': gl2ps.GL2PS_TEX,
            'pdf': gl2ps.GL2PS_PDF,
            }
        if utils.Module.check('gl2ps', '>=1.03'):
            _gl2ps_types.update({
                'svg': gl2ps.GL2PS_SVG,
                'pgf': gl2ps.GL2PS_PGF,
                })
        return [], [fmt for fmt in _gl2ps_types]
    else:
        return [], []


def get_image_formats(tool):
    """Return the image formats supported by a specific tool.

    Detects and stores the formats or returns the already detected
    and stored formats.

    Parameters
    ----------
    tool: str
        The key corresponding with the tool to be used to read/write
        the image file.
        It should be one of 'qt', 'pil', 'magick', 'gl2ps'.

    Returns
    -------
    formats_r: list of str
        List of the supported formats in read operations.
    formats_w: list of str
        List of the supported formats in write operations.

    Notes
    -----
    The returned formats are lower case strings corresponding with the
    conventional filename extension without the leading dot.
    Examples: 'png', 'gif'.
    """
    if image_formats[tool] is None:
        detect = globals()['get_image_formats_' + str(tool)]
        image_formats[tool] = detect()
        pf.debug(f"Detected image formats for {tool}:"
                 f" {image_formats[tool]}", pf.DEBUG.IMAGE)
    return image_formats[tool]


def imageFormats(tool=None, mode=None):
    """Detect and return the list of supported image formats.

    pyFormex supports reading and writing image files through different
    underlying tools: 'qt', 'PIL', 'ImageMagick', 'gl2ps'.
    Each tool has its own supported set of image formats, often different
    for reading and writing.
    In pyFormex, image formats are lowercase strings corresponding with the
    conventional filename extension without the leading dot. Examples are
    'png', 'gif', 'ppm', 'eps', 'jpg', 'jpeg'.

    Parameters
    ----------
    tool: str, optional
        If specified, it is a key corresponding with the underlying tool
        to be used to read/write the image file. It should be one of
        'qt', 'pil', 'magick', 'gl2ps'. If not specified, returns
        a dict with results for all tools.
    mode: 'r' | 'w', optional
        The purpose of the format: read or write. If not specified, returns
        results for both. This parameter can only be used if tool is specified
        as well.

    Returns
    -------
    list, tuple or dict
        If both tool and mode are specified, returns a list with the
        supported formats by that tool for the specified mode. The list
        contains lower case strings corresponding with the conventional
        filename extension without the leading dot. Examples are
        'png', 'gif', 'ppm', 'eps', 'jpg', 'jpeg'.

        If mode is not specified, returns a tuple (formats_r, formats_w)
        where formats_r is the list of supported formats for reading, and
        formats_w for writing.

        Without parameters, returns a dict where the keys are the valid
        tool names and the values are the corresponding (formats_r, formats_w)
        tuples.

    """
    if tool is None:
        for tool in image_formats:
            get_image_formats(tool)
        return image_formats

    get_image_formats(tool)
    formats = image_formats[tool]
    if mode == 'r':
        return formats[0]
    elif mode == 'w':
        return formats[1]
    else:
        return formats


def checkImageFormat(tool, mode, fmt, verbose=True):
    """Check that an image format is supported by tool and mode.

    Parameters
    ----------
    tool: str
        The key corresponding with the tool to be used to read/write
        the image file.
        It should be one of 'qt', 'pil', 'magick', 'gl2ps'.
    mode: 'r' | 'w'
        The purpose of the format: read or write.
    fmt: str
        The image format to check.
    verbose: bool
        If True, a warning message will be displayed to the user
        if the format is not supported.

    Returns
    -------
    str | None
        The image format if it is supported by the specified
        tool and mode, or else None.
    """
    pf.debug(f"Format requested: {tool}, {mode}, {fmt}", pf.DEBUG.IMAGE)
    if fmt in imageFormats(tool, mode):
        if fmt == 'tex' and verbose:
            pf.warning("This will only write a LaTeX fragment to include"
                       " the 'eps' image\nYou have to create the .eps"
                       " image file separately.\n")
        return fmt
    else:
        if verbose:
            from pyformex.gui import draw
            draw.showError(f"Sorry, can not save in {fmt} format!\n"
                       "I suggest you use 'png' format ;)")
        return None


# TODO: should we keep this undocumented old functionality?
def convertEPS(epsfile, tofile, fmt):
    epsfile = Path(epsfile)
    if epsfile.exists():
        cmd = f"pstopnm -portrait -stdout {epsfile}"
        if fmt != 'ppm':
            cmd += f" | pnmto{fmt} > {tofile}"
        utils.command(cmd, shell=True)


######## LOW LEVEL FUNCTIONS ###############

def save_qt(filename, format, quality=-1, canvas=None, size=None,
            crop=None, alpha=False):
    """Save an OpenGL canvas rendering as an image file.

    Saves a :class:`~gui.viewport.QtCanvas` rendering using the Qt library
    functions. This provides the 'qt' tool functionality of :func:`saveImage`,
    which is the prefered user level function for saving pyFormex renderings
    to image files.

    Parameters
    ----------
    filename: :term:`path_like`
        The file path to which to save the image.
    format: str
        One of the supported image formats. Any format supported by QImage
        for writing. The list can be got from ``imageFormats('qt', 'w')``.
    quality: int, optional
        The image quality for compressed formats.
    canvas: :class:`~gui.viewport.QtCanvas`, optional
        The canvas to be saved. If not specified, the current active canvas
        is used.
    size: int tuple, optional
        A tuple (width, height) specifying the size of the output image.
        The default is to use the canvas size.
    crop: int 4-tuple, optional
        A tuple (x, y, w, h) defining a rectangular area to crop from the
        image. (x,y) is the top left corner and (w,h) are the width and
        height in pixels. The stored image will thus have size (w,h).
        Note that combining this parmeter with a canvas resizing using the
        `size` parameter will make it difficult to predict what exactly will
        end up in the cropped image. Therefore this parameter is commonly only
        used with the original canvas size.

    See Also
    --------
    saveImage: the recommended high level versatile image saving function
    save_window: save the pyFormex window as image file
    save_gl2ps: save the OpenGL rendering in a vector format
    """
    pf.debug(f"save_qt", pf.DEBUG.IMAGE)
    # make sure we have the current content displayed (on top)
    canvas.makeCurrent()
    canvas.raise_()
    canvas.display()
    pf.app.processEvents()

    sta = 1  # Flag failure
    filename = Path(filename)
    if format is None:
        format = filename.lsuffix.strip('.')
    if format in imageFormats('qt', 'w'):
        pf.debug("Image format can be saved by Qt", pf.DEBUG.IMAGE)
        if size is None or size == canvas.getSize():
            #
            # Use direct grabbing from current buffer
            # TODO: We could grab from the OpenGL buffers here!!
            #
            canvas.glFinish()
            pf.debug(f"Saving image from opengl buffer with"
                     f"size {canvas.getSize()}", pf.DEBUG.IMAGE)
            qim = canvas.grabFrameBuffer(withAlpha=alpha)
        else:
            # Render in an off-screen buffer and grab from there
            # TODO: the offscreen buffer should be properly initialized
            # according to the current canvas
            #
            wc, hc = canvas.getSize()
            try:
                w, h = size
            except Exception:
                w, h = wc, hc
            pf.debug(f"Saving image from virtual buffer with size {w}x{h}",
                     pf.DEBUG.IMAGE)
            qim = canvas.image(resize=(w, h), remove_alpha=not alpha)

        pf.debug(f"Image has alpha channel: {qim.hasAlphaChannel()}",
                 pf.DEBUG.IMAGE)
        if crop:
            qim = qim.copy(*crop)
        pf.debug(f"Saving canvas to {filename} in format {format}"
                 f" with size ({crop[2:4]}) and quality {quality}",
                 pf.DEBUG.IMAGE)
        if qim.save(filename, format, quality):
            sta = 0

    return sta


# if we have gl2ps, or when building docs
if gl2ps or pf.sphinx :

    def save_gl2ps(filename, format=None, canvas=None, title='', producer='',
               # viewport=None
    ):
        """ Export the OpenGL rendering to PostScript/PDF/TeX format.

        Exporting OpenGL renderings to PostScript is based on the PS2GL
        library by Christophe Geuzaine (http://geuz.org/gl2ps/), linked
        to Python by Toby Whites's wrapper
        (http://www.esc.cam.ac.uk/~twhi03/software/python-gl2ps-1.1.2.tar.gz)

        This function is only defined if the gl2ps module is found.
        It provides the 'gl2ps' tool functionality of :func:`saveImage`,
        which is the prefered user level function for saving pyFormex
        renderings to image files.

        Parameters
        ----------
        filename: :term:`path_like`
            The file path to which to save the image.
        format: str
            One of the supported image formats. Any format supported by gl2ps.
            The list can be got from ``imageFormats('gl2ps', 'w')``,
            but at least includes 'ps', 'eps', 'pdf' and 'tex'.
            In the case of 'tex', two files are actually written: one with
            the .tex extension, and one with .eps extension.
            If format is not specified, it is derived from the filename
            extension.
        canvas: :class:`~gui.viewport.QtCanvas`, optional
            The canvas to be saved. If not specified, the current active canvas
            is used.
        title: str, optional
            An optional title to be written into the image file.
        producer: str, optional
            A producer string to be written in the image file. Default
            is a pyFormex identification.

        See Also
        --------
        saveImage: the recommended high level versatile image saving function
        save_qt: save the OpenGL rendering as a raster image
        save_window: save the pyFormex window as image file
        """
        from pyformex.opengl.gl import GL

        pf.debug(f"save_window_gl2ps", pf.DEBUG.IMAGE)
        # make sure we have the current content displayed (on top)
        canvas.makeCurrent()
        canvas.raise_()
        canvas.display()
        pf.app.processEvents()

        filename = Path(filename)
        if format is None:
            format = filename.lsuffix.strip('.')
        if format in imageFormats('gl2ps', 'w'):
            pf.debug("Image format can be saved by gl2ps", pf.DEBUG.IMAGE)
            filetype = _gl2ps_types[filetype]

        fp = open(filename, "wb")
        if not title:
            title = filename
        if not producer:
            producer = pf.fullVersion()
        # if not viewport:
        #     viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
        bufsize = 0
        state = gl2ps.GL2PS_OVERFLOW
        opts = ( gl2ps.GL2PS_SILENT |
                 gl2ps.GL2PS_SIMPLE_LINE_OFFSET |
                 gl2ps.GL2PS_USE_CURRENT_VIEWPORT
                 )
        ##| gl2ps.GL2PS_NO_BLENDING | gl2ps.GL2PS_OCCLUSION_CULL | gl2ps.GL2PS_BEST_ROOT
        ##color = GL[[0.,0.,0.,0.]]
        #print(f"VIEWPORT {viewport}")
        #print(fp)
        viewport=None
        while state == gl2ps.GL2PS_OVERFLOW:
            bufsize += 1024*1024
            gl2ps.gl2psBeginPage(title, _producer, viewport, filetype,
                                 gl2ps.GL2PS_BSP_SORT, opts, GL.GL_RGBA,
                                 0, None, 0, 0, 0, bufsize, fp, '')
            canvas.display()
            canvas.glFinish()
            state = gl2ps.gl2psEndPage()
        fp.close()
        return 0


def save_window(filename, format, quality=-1, windowname=None, crop=None):
    """Save (part of) a window as an image file.

    Saves any window or part of it to an image file. This uses the 'import'
    command from ImageMagick and can save in any format supported by it.
    It provides the 'magick' tool functionality of :func:`saveImage`,
    which is the prefered user level function for saving the pyFormex window
    to image files.

    Parameters
    ----------
    filename: :term:`path_like`
        The filename on which to save the image.
    format: str
        One of the supported image formats. See ImageMagick. The format needs
        to be specified. It is currently not derived from the file name.
    quality: int, optional
        See :func:`save_window_rect`
    windowname: str, optional
        The name of the window to be saved. The windowid or name of the window
        you want to save. To find the id/name of an open window, you can run
        the command xwininfo and click on the window. If not specified, the
        pyFormex main window is used. A value 'root' will save the full
        desktop window.
    crop: tuple|str, optional
        Define a subregion of the window to be saved. A subregion can
        be specified as a tuple (x,y,w,h) defining the rectangle to be saved:
        (x,y) is the position of the upper left corner with respect to the
        window origin; (w,h) are the width and height of the rectangle.
        Some subregions can also be conveniently specified by a string:
        'all' will save all viewports of the central widget, 'vp' will save
        only the current viewport. The default None will
        save the whole window (without border decorations).

    Notes
    -----
    While this function can be used to save any window, it is primarily provided
    to save pyFormex windows. Therefore, in all cases, the pyFormex GUI and
    current canvas are raised and updated before saving.

    See Also
    --------
    saveImage: the recommended high level versatile image saving function
    save_qt: save the OpenGL rendering as a raster image
    save_gl2ps: save the OpenGL rendering in a vector format
    """
    pf.debug(f"save_window", pf.DEBUG.IMAGE)
    pf.GUI.raise_()
    pf.GUI.repaint()
    pf.GUI.toolbar.repaint()
    pf.GUI.update()
    pf.canvas.makeCurrent()
    pf.canvas.raise_()
    pf.canvas.update()
    pf.app.processEvents()
    # Deprecated value 'canvas'
    if crop == 'canvas':
        utils.warn("crop='canvas' is deprecated. Use crop='all' instead")
        crop = 'all'
    if crop in ['all', 'vp']:
        windowname = pf.GUI.windowTitle()
        widget = pf.GUI.central if crop=='all' else pf.canvas
        x, y = qtutils.relPos(widget)
        w, h = qtutils.Size(widget)
        crop = (x, y, w, h)
    if windowname is None:
        windowname = pf.GUI.windowTitle()
    return save_window_rect(filename, format, quality, windowname, crop)


def save_window_rect(filename, format, quality=-1, window='root', crop=None):
    """Save a rectangular part of the screen to a an image file.

    This uses the external program 'import' from Imagemagick to save a
    rectangle from any window on the screen.

    Parameters
    ----------
    filename: :term:`path_like`
        The name of the file on which to save the image.
    format: str
        The format of the image file. The available formats can be
        obtained from `imageFormats('magick', 'w')`.
    quality: int
        For compressed images, this defines the quality in percent.
        For PNG images, this is a value 0..9, where 0 is uncompressed
        and 9 is maximal compression. For JPEG, this is a value 1..100
        where 100 is maximum quality.
        A value -1 selects the default quality, which is 0 for PNG and
        90 for JPEG.
    crop: tuple of int, optional
        A tuple (x,y,w,h) specifying the rectangle to be saved from
        the window. (x,y,) is the top left corner relative to the
        window. (w,h) is the size of the rectangle. The default is
        to save the whole window.

    See Also
    --------
    saveImage: the recommended high level versatile image saving function
    save_window: save the pyFormex window to an image file
    record_rect: record a screen rectangle to a video file
    """
    pf.debug(f"save_window_rect({filename!r}, {format!r},"
             f" quality={quality}, window={window!r}, crop={crop})",
             pf.DEBUG.IMAGE)
    utils.External.require('imagemagick')
    format = format.lower()
    cmd = ['import', '-window', window]
    if crop:
        x, y, w, h = crop
        cmd += ['-crop', f"{w}x{h}+{x}+{y}"]
    if quality == -1:
        if format == 'png':
            quality = 0
        elif format in ['jpg', 'jpeg']:
            quality = 90
        cmd += ['-quality', f"{quality}"]
    cmd += [f"{format}:{filename}"]
    P = utils.system(cmd)
    return P.returncode

######## saveImage ######################

# For each saving tool, record the possible extents
_image_tools = {
    'qt': ['canvas', 'rectangle', 'allvps']  # always available
}
_image_tools_detected = False

def add_tool_options(tool, extents):
    """Add extra tool if detected"""
    if tool not in _image_tools:
        _image_tools[tool] = []
    for extent in extents:
        if extent not in _image_tools[tool]:
            _image_tools[tool].append(extent)


def extent_options(tool):
    """Return possible extents for a tool"""
    return _image_tools[tool]


def tool_options(extent):
    """Return possible tools for an extent"""
    return [t for t in _image_tools if extent in _image_tools[t]]


def detect_tools():
    """Detect optional image saving tools"""
    global _image_tools_detected
    if utils.External.has('imagemagick'):
        add_tool_options(
            'magick', ['canvas', 'central', 'window', 'border', 'screen'])
    if utils.Module.has('gl2ps'):
        add_tool_options('gl2ps', ['canvas'])
    _image_tools_detected = True


def image_tools():
    """Return a list with all image tools"""
    if not _image_tools_detected:
        detect_tools()
    return list(_image_tools)


def image_extents():
    """Return a list with all image extents"""
    if not _image_tools_detected:
        detect_tools()
    extents = []
    for t in _image_tools:
        extents.extend([e for e in _image_tools[t] if e not in extents])
    return extents


def saveImage(filename=None,
              extent='canvas', tool='qt',
              format=None, quality=-1, size=None, alpha=True,
              multi=False, hotkey=True, autosave=False,
              verbose=False):
    """Save the pyFormex rendering or window to an image file.

    This is the recommended high level function for saving a pyFormex
    canvas rendering or even the whole pyFormex GUI window to an
    image file in one of the many supported formats.

    This function can also be used to start/stop multisave mode, which can
    save a series of images.

    Parameters
    ----------
    filename: :term:`path_like` or :class:`~utils.NameSequence`
        The path where the image is to be saved. If it is a NameSequence,
        the actual filename will be ``next(filename)``.
        If no filename is specified, nothing is saved and multisave mode
        is turned off if it was on (see also ``multi``).
    extent: str
        Identifies which part of the GUI is to be saved. It should be
        one of the following

        - 'canvas': the current OpenGL viewport
        - 'rectangle': let the user pick a rectangle from the canvas
        - 'allvps': all the OpenGL viewports, each in their own file.
          If there is more than one viewport, actual file names are derived
          from the specified filename by adding '_vp#' (where # is the
          viewport number) before the file extension
        - 'central': the central widget of the GUI, including all the OpenGL
          viewports, in a single image
        - 'window': the pyFormex GUI main window, without the border
        - 'border': the pyFormex GUI main window including border decorations
        - 'screen': saves the full primary X11 screen

        Depending on the installed tools on your system, some options may
        not be available. The actually available options are given by
        :func:`image_extents`.
    tool: 'qt' | 'magick' | 'gl2ps'
        The tool to be used to save the image. 'qt' is always available.
        The others depend on your installation. The actually available
        tools are given by :func:`image_tools`. The tool defines the possible
        values of ``extent``:

        - qt: 'canvas', 'rectangle, 'allvps'
        - magick: 'canvas', 'central', 'window', 'border', 'screen'
        - gl2ps: 'canvas'

    format: str
        One of the supported image formats. The list of supported
        image formats depends on ``tool`` and can be found from
        ``imageFormats('qt', 'w')``.
        If not specified, it is derived from the filename extension,
        converted to lower case and without the leading dot.
    quality: int, optional
        See :func:`save_window_rect`.
    size: tuple (w,h), optional
        A tuple of width and height specifying the requested image size.
        The default is to use the size of the current onscreen rendering
        as this ensures the best quality.
        If the output size is not equal to the actual rendering size,
        the image is rendered offscreen and some OpenGL features might
        not be shown correctly.
    alpha: bool, optional
        This is an experimental feature not ready for use.
    multi: bool, optional
        If True and a filename was specified, multisave mode is switched on.
        In multisave mode, images will repeatedly be saved on demand or
        automatically. The filename is turned into a
        :class:`~utils.NameSequence`
        to generate consecutive file names for the images. The images are saved
        with the same format, quality and size. In multisave mode, each call
        to :func:`saveNext` will save an image to the next generated file name.
        The starting of multisave mode in itself does not save any image.
        See also the ``hotkey`` and ``autosave`` options.
        Multisave mode can be turned off from the GUI File menu or by calling
        saveImage without a filename. Starting a new multisave mode
        will also quietly stop a previous multisave.
    hotkey: bool, optional
        If True (default) when multisave mode is activated, a new image can
        be saved by hitting a hotkey (configurable in the settings).
    autosave: bool, optional
        If True, a new image will be saved on each execution of the
        :func:`~gui.draw` function.
    verbose: True, optional
        If True, additional error or warning messages may be displayed.

    See Also
    --------
    save_window: save the pyFormex window to an image file
    save_qt: save the OpenGL rendering as a raster image
    save_gl2ps: save the OpenGL rendering in a vector format

    """
    global multisave

    # Leave multisave mode if no filename or starting new multisave mode
    if multisave and (filename is None or multi):
        print("Leave multisave mode")
        if multisave['hotkey']:
            pf.GUI.signals.SAVE.disconnect(saveNext)
        multisave = None

    if filename is None:
        return

    if isinstance(filename, utils.NameSequence) and not multi:
        fileseq = filename
        filename = next(fileseq)
    else:
        fileseq = None
    filename = Path(filename)
    # Check tool/extent
    if tool not in image_tools() or extent not in extent_options(tool):
        pf.warning("Invalid combination of tool/extent parameters")
        return

    # Get/Check format
    if format is None:
        format = filename.lsuffix.strip('.')
    format = checkImageFormat('qt', 'w', format)
    if not format:
        pf.warning(f"Can not save image in format {format}")
        return

    crop = None
    if extent == 'rectangle':
        # Set crop from rectangle picked by user
        x0, y0, x1, y1 = pf.canvas.getRectangle(yup=False)
        crop = (x0 + 1, y0 + 1, x1 - x0 - 1, y1 - y0 - 1)

    if multi:  # Start multisave mode
        fileseq = utils.NameSequence(filename)
        while Path(fileseq.peek()).exists():
            next(fileseq)
        print(f"Start multisave mode to files: {fileseq.template} ({format})")
        if hotkey:
             pf.GUI.signals.SAVE.connect(saveNext)
             if verbose:
                 pf.warning(
                     f"Each time you hit the {pf.cfg['keys/save']} key,"
                     f" the image will be saved to the next numbered file.")
        multisave = {'filename': fileseq, 'tool': tool, 'extent': extent,
                     'format': format, 'quality': quality, 'size': size,
                     'crop': crop, 'alpha': alpha,
                     'hotkey': hotkey, 'autosave': autosave}
        # verbosity 2
        if pf.verbosity(2):
            print(f"Multisave params: {multisave}")
        return multisave is None

    else:
        # Save the image
        sta = -1
        if tool == 'magick':
            # Grab from X server buffers (needs external ImageMagick)
            utils.External.require('imagemagick')
            windowname = None  # use pyFormex window
            if extent == 'canvas':
                crop = 'vp'
            elif extent == 'central':
                crop = 'all'
            elif extent == 'window':
                crop = None  # use whole window
            elif extent == 'border':
                windowname = 'root'
                crop = pf.GUI.frameGeometry().getRect()
            elif extent == 'screen':
                windowname = 'root'
                crop = pf.app.primaryScreen().geometry().getRect()
            sta = save_window(filename, format, quality, windowname=windowname,
                              crop=crop)
        elif tool == 'qt':
            if extent in ['canvas', 'rectangle']:
                sta = save_qt(filename, format, quality, canvas=pf.canvas,
                              size=size, crop=crop, alpha=alpha)
            elif extent == 'allvps':
                suffix = filename.lsuffix
                fileseq = utils.NameSequence(
                    filename.with_suffix('_vp0'), suffix)
                sta = 0
                for vp in pf.GUI.viewports.all:
                    filename = next(fileseq)
                    sta += save_qt(filename, format, quality, canvas=vp,
                                   size=size, alpha=alpha)
                    if sta == 0:
                        print(f"Image file {filename} written")
                    else:
                        break


        elif tool == 'ps2gl':
            sta = save_ps(pf.canvas, filename, filetype=format)

        if sta == 0 and extent != 'allvps':
            print(f"Image file {filename} written")
        else:
            pf.debug("Error while saving image {filename}", pf.DEBUG.IMAGE)


# REMOVED 2023-01
# @utils.deprecated_by('image.save', 'image.saveImage')
# def save(filename=None,
#          grab=False, window=False, border=False,
#          format=None, quality=-1, size=None, alpha=True,
#          multi=False, hotkey=True, autosave=False,
#          verbose=False):
#     """Save the pyFormex rendering to an image file.

#     This is a wrapper around :func:`saveImage`, using a slightly
#     different (but deprecated) interface with reduced functionality.
#     We describe here only the parameters that are different.
#     The ``extent`` and ``tool`` parameters are missing and are
#     replaced with ``window``, ``border`` and ``grab``.

#     Parameters
#     ----------
#     window: bool
#         If True, the full pyFormex window is saved. The default (False)
#         only saves the central widget with the OpenGL rendering. If there
#         are multiple viewports, only the current viewport is saved.
#     border: bool
#         If True, and also ``window`` is True, the image will also contain
#         the window border decorations.
#     grab: bool
#         If True, the external 'import' program is used to grab the
#         window from the screen buffers. This mode is also forced by
#         the ``window=True`` option. The default (False) saves the
#         image directly using the Qt GUI libraries.

#     """
#     if grab:
#         tool = 'magick'
#         if window:
#             if border:
#                 extent = 'bordered'
#             else:
#                 extent = 'window'
#         else:
#             extent = 'current viewport'
#     else:
#         tool = 'qt'
#         extent = 'current viewport'
#     saveImage(filename=filename, extent=extent, tool=tool,
#               format=format, quality=quality, size=size, alpha=alpha,
#               multi=multi, hotkey=hotkey, autosave=autosave,
#               verbose=verbose)


def saveNext():
    """In multisave mode, save the next image.

    This is a quiet function that does nothing if multisave was not activated.
    It can thus safely be called on regular places in scripts where one would
    like to have a saved image. In interactive use, the user then has to be
    asked only once whether to activate the multisave mode or not.
    """
    if multisave:
        saveImage(multi=False, verbose=False, **multisave)


def autoSaveOn():
    """Returns True if autosave multisave mode is currently on.

    Use this function instead of directly accessing the multisave variable.
    """
    return multisave and multisave['autosave']


def createMovie(files, encoder='convert', outfn='output', **kargs):
    """Create a movie from a saved sequence of images.

    Parameters
    ----------
    files: list of str
        A list of filenames, or a string with one or more filenames
        separated by whitespace. The filenames can also contain wildcards
        interpreted by the shell.
    encoder: str
        The external program to be used to create the movie.
        This will also define the type of output file, and the extra parameters
        that can be passed. The external program has to be installed on the
        computer. The default is 'convert', which will create animated gif.
        Other possible values are 'mencoder' and 'ffmeg', creating meg4
        encode movies from jpeg input files.
    outfn: str
        output file name (not including the extension).
        Default is 'output'.
    **kargs:
        Other parameters may be passed and may be needed, depending on the
       converter program used. Thus, for the default 'convert' program,
       each extra keyword parameter will be translated to an option
       ``-keyword value`` for the command. Example::

           createMovie('images*.png',delay=1,colors=256)

       will create an animated gif 'output.gif'.
    """
    outfn = path(outfn)
    if pf.verbosity(2):
        print(f"Encoding {files}")
    if isinstance(files, list):
        files = ' '.join(files)

    if encoder == 'convert':
        outfile = outfn.with_suffix('.gif')
        cmd= "convert " + " ".join(
            [f"-{k} {kargs[k]}" for k in kargs]) + f" {files} {outfile}"
    elif encoder == 'mencoder':
        outfile = outfn.with_suffix('.avi')
        cmd = (f"mencoder \"mf://{files}\" -o {outfile} -mf fps={kargs['fps']} "
               f"-ovc lavc -lavcopts vcodec=msmpeg4v2:vbitrate={kargs['vbirate']}")
    else:
        outfile = outfn.with_suffix('.mp4')
        cmd = f"ffmpeg -qscale 1 -r 1 -i {files} output.mp4"
        pf.debug(cmd, pf.DEBUG.IMAGE)
    P = utils.command(cmd)
    if pf.verbosity(1):
        print(f"Created video file {outfile.resolve()}")
    return P.returncode


def changeBackgroundColorXPM(fn, color):
    """Change the background color of an .xpm image.

    Parameters
    ----------
    fn: :term:`path_like`
        The file name of an .xpm image file.
    color: str
        The color to be set as background color. It is an X11 color name or
        a web format hexadecimal color ('#FFF' or '#FFFFFF' is white).
        A special value 'None' may be used to set a transparent background.

    Notes
    -----
    The current background color is selected from the lower left pixel.
    All pixels having that color will be changed.

    This function is mainly intended for use by :func:`saveIcon`.
    """
    with open(fn,'r') as fil:
        t = fil.readlines()
    c = ''
    for l in t[::-1]:
        if l.startswith('"'):
            c = l[1]
            if pf.verbosity(2):
                print(f"Found '{c}' as background character")
            break
    if not c and pf.verbosity(1):
        print(f"Can not change background color of '{fn}'")
        return
    for i, l in enumerate(t):
        if l.startswith(f'"{c} c '):
            t[i] = f'"{c} c None",\n'
            break
    with open(fn, 'w') as fil:
        fil.writelines(t)


def saveIcon(fn, size=32, transparent=True):
    """Save the current rendering as an icon.

    Saves the current rendering as an .xpm image file.

    Parameters
    ----------
    fn: :term:`path_like`
        File name of the target image file. If it does not end with '.xpm',
        this extension will be appended.
    size: int
        Pixel size of the output image.
    transparent: bool
        If True (default), the background will be set to transparent.

    Notes
    -----
    This function is primarily intended for creating icons for the
    pyFormex GUI.
    """

    if not fn.endswith('.xpm'):
        fn += '.xpm'
    save_qt(fn, format='xpm', canvas=pf.canvas, size=(size, size))
    if pf.verbosity(1):
        print(f"Saved icon to file {fn} in {Path.cwd()}")
    if transparent:
        changeBackgroundColorXPM(fn, 'None')


_recording_P = None
_recording_button = None
record_extents = ['canvas', 'central', 'window', 'border', 'screen']

def recordSession(filename, extent='window', framerate=25):
    """Create a video from the pyFormex window or another zone on the screen.

    This uses ffmpeg to record a rectangular area of the screen to a video file.

    Parameters
    ----------
    filename: :term:`path_like`
        The path to the file to save. The filename should have an extension
        .mp4 for the 'ffmpeg' tool, and '.ogv' for the 'recordmydesktop'
        tool.
    extent: str
        The part
    """
    global _recording_P, _recording_button
    if _recording_P:
        pf.warning("Another recorder is already running!")
        return _recording_P
    print(f"Recording your session to file {filename}")
    pf.GUI.raise_()
    pf.GUI.repaint()
    pf.GUI.toolbar.repaint()
    pf.GUI.update()
    pf.canvas.makeCurrent()
    pf.canvas.raise_()
    pf.canvas.update()
    pf.app.processEvents()
    # we need screen offsets, so get the main window geometry first
    if extent == 'canvas':
        geom = qtutils.absRect(pf.canvas)
    elif extent == 'central':
        geom = qtutils.absRect(pf.GUI.central)
    elif extent == 'window':
        geom = pf.GUI.geometry().getRect()
    elif extent == 'border':
        geom = pf.GUI.frameGeometry().getRect()
    elif extent == 'screen':
        geom = pf.app.primaryScreen().geometry().getRect()
    print(f"Geometry: geom")
    x, y, w, h = geom
    cmd = (f"ffmpeg -video_size {w}x{h} -framerate {framerate} -f x11grab"
           f" -i :0.0+{x},{y} -y {filename}")
    pf.debug(cmd, pf.DEBUG.IMAGE)
    _recording_P = utils.command(cmd, wait=False)
    if _recording_P:
        pf.GUI.onExit(stopRecording)
        _recording_button = pf.GUI.addStatusbarButtons(
            ':movie:recording', actions=[('REC', stopRecording)], spacing=0)
    return _recording_P


def stopRecording():
    global _recording_P, _recording_button
    if _recording_P:
        # Was recording: finish it
        _recording_P.terminate()
        returncode = _recording_P.wait()
        pf.debug(f"Recording stopped with code {returncode}")
        _recording_P = None
    if _recording_button:
        pf.GUI.statusbar.removeWidget(_recording_button)
        _recording_button = None
    return returncode


def record_rect(filename, size, pos, framerate=25):
    """Record a rectangular part of the screen to a a video file.

    This uses the external program 'ffmpeg' to record a
    rectangle from any window on the screen.

    Parameters
    ----------
    filename: :term:`path_like`
        The name of the file on which to save the image. This should by
        preference be a .mp4 file. If you want another format, one can
        always convert afterwards.
    size: tuple of int
        A tuple (w,h) specifying the width and height of the rectangle to grab.
        It is also the size of the output video. If you need another output
        size, convert the video afterwards.
    pos: tuple of int
        A tuple (x,y) with the position of the top left corner of the rectangle
        to grab. The values are relative to the primary screen origin.
    framerate: int, optional
        The number of frames to capture per second.

    See Also
    --------
    recordSession: the recommended high level video recording function
    save_window_rect: save a screen rectangle to an image file
    """
    pf.debug(f"record_rect size={size} pos={pos} framerate={framerate}",
             pf.DEBUG.IMAGE)
    x, y, w, h = geom
    cmd = (f"ffmpeg -video_size {w}x{h} -framerate {framerate} -f x11grab"
           f" -i :0.0+{x},{y} -y {filename}")
    cmd = f"import -window '{window}' {options} {format}:{filename}"
    # We need to use shell=True because window name might contain spaces
    # thus we need to add quotes, but these are not stripped off when
    # splitting the command line.
    # TODO: utils should probably be changed to strip quotes after splitting
    P = utils.command(cmd, shell=True)
    return P.returncode

### End
