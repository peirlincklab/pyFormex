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
"""Convert bitmap images into numpy arrays.

This module contains functions to convert bitmap images into numpy
arrays and vice versa. There are functions to read image from file
into arrays, and to save image arrays to files. There is even a class
that reads a full stack of Dicom images into a 3D numpy array.

Some of this code was based on ideas found on the PyQwt mailing list.
"""

import numpy as np
import PIL.Image

import pyformex as pf
from pyformex import utils
from pyformex import arraytools as at
from pyformex.gui import QtGui, QImage

QColor = QtGui.QColor

####################################################################
# Import/export images using PIL


def image2array(filename, mode=None, flip=True):
    """
    Read an image file into a numpy array.

    Parameters
    ----------
    filename: :term:`path_like`
        The name of the file containing the image.
    mode: str, optional
        If provided, the image will be converted to the specified mode.
        The mode is a string defining the color channels to be returned.
        Typical values are '1' (black/white), 'L' (grayscale),
        'LA' (gray with alpha), 'RGB' (three colors),
        'RGBA' (three colors plus alpha).
        Default is to return the image as it is stored.
    flip: bool
        If True, the vertical axis will be inverted. This is the default,
        because image scanlines are stored from top to bottom, while opengl
        uses a vertical axis running from bottom to top. Set this to False
        when using images as fonts in :class:`FontTexture`, because the
        FontTexture engine itself takes account of the top-down image
        storage.

    Examples
    --------
    >>> im = image2array(pf.cfg['datadir'] / 'butterfly.png')
    >>> im.shape
    (419, 420, 3)
    """
    im = PIL.Image.open(filename)
    if mode and im.mode != mode:
        im = im.convert(mode)
    im = np.array(im)
    if flip:
        im = np.flipud(im)
    return im


def array2image(ar, filename):
    """
    Save an image stored in a numpy array to file.

    Parameters
    ----------
    ar: array
        Array holding the pixel data. This is typically an Int8 type
        array with shape (height, width, 3) where the last axis holds
        the RGB color data.
    filename: :term:`path_like`
        The name of the file where the image is to be saved.
    """
    im = PIL.Image.fromarray(ar)
    im.save(filename)


def image2string(filename):
    # defer import for startup efficiency
    im = PIL.Image.open(filename)
    nx, ny = im.size[0], im.size[1]
    try:
        data = im.tostring("raw", "RGBA", 0, -1)
    except SystemError:
        data = im.tostring("raw", "RGBX", 0, -1)
    return nx, ny, data


####################################################################
# Handle images using QImage

def resizeImage(image, w=0, h=0):
    """
    Load and optionally resize a QImage.

    Parameters
    ----------
    image: :term:`qimage_like`
        QImage, or data that can be converted to a QImage, e.g. the name of
        a raster image file.
    w: int, optional
        If provided and >0, the image will be resized to this width.
    h: int, optional
        If provided and >0, the image will be resized to this height.

    Returns
    -------
    QImage
        A QImage with the requested size (if provided).
    """
    if not isinstance(image, QImage):
        image = QImage(image)

    W, H = image.width(), image.height()
    if w <= 0:
        w = W
    if h <= 0:
        h = H
    if w != W or h != H:
        image = image.scaled(w, h)

    return image


def qimage2numpy(image, resize=(0, 0), order='RGBA', flip=True, indexed=None):
    """
    Transform a QImage to a :class:`numpy.ndarray`.

    Parameters
    ----------
    image: :term:`qimage_like`
        A QImage or any data that can be converted to a QImage,
        e.g. the name of an image file, in any of the formats supported by Qt.
        The image can be a full color image or an indexed type. Only 32bit
        and 8bit images are currently supported.
    resize: tuple of ints
        A tuple of two integers (width,height). Positive value will
        force the image to be resized to this value.
    order: str
        String with a permutation/subset of the characters 'RGBA', defining
        the order in which the colors are returned. Default is RGBA, so that
        result[...,0] gives the red component. Note however that QImage stores
        in ARGB order. You may also specify a subset of the 'RGBA' characters,
        in which case you will only get some of the color components. An often
        used value is 'RGB' to get the colors without the alpha value.
    flip: bool
        If True, the image scanlines are flipped upside down.
        This is practical because image files are usually stored in top down
        order, while OpenGL uses an upwards positive direction, requiring a
        flip to show the image upright.
    indexed: bool or None.
        If True, the result will be an indexed image where each pixel color
        is an index into a color table. Non-indexed image data will be
        converted.

        If False, the result will be a full color array specifying the color
        of each pixel. Indexed images will be expanded to a full color array.

        If None (default), no conversion is done and the resulting data are
        dependent on the image format. In all cases both a color and a
        colortable will be returned, but the latter will be None for
        non-indexed images.

    Returns
    -------
    colors: array
        An int8 array with shape (height,width,ncomp), holding
        the components of the color of each pixel. Order and number
        of components is as specified by the ``order`` argument. The default
        is 4 components in order 'RGBA'.

        This value is only returned if the image was not an indexed type
        or if ``indexed=False`` was specified, in which case indexed images
        will be converted to full color.
    colorindex: array
        An int array with shape (height,width) holding color indices into
        ``colortable``, which stores the actual color values.

        This value is only returned if the image was an indexed type
        or if ``indexed=True`` was specified, in which case nonindexed images
        will be converted to using color index and table.
    colortable: array or None.
        An int8 array with shape (ncolors,ncomp). This array stores all the
        colors used in the image, in the order specified by ``order``

        This value is only returned if ``indexed`` is not False.
        Its value will be None if ``indexed`` is None (default) and
        the image was not indexed.

    Notes
    -----
    This table summarizes the return values for each of the possible values
    of the ``indexed`` argument combined with indexed or nonindexed image data:

    ===============   ======================   ======================
    arg               non-indexed image        indexed image
    ===============   ======================   ======================
    indexed=None      colors, None             colorindex, colortable
    indexed=False     colors                   colors
    indexed=True      colorindex, colortable   colorindex, colortable
    ===============   ======================   ======================

    """
    image = resizeImage(image, *resize)

    pf.debug("IMAGE FORMAT %s" % image.format(), pf.DEBUG.IMAGE)

    if indexed:
        image = image.convertToFormat(QImage.Format_Indexed8)

    h, w = image.height(), image.width()

    if image.format() in (QImage.Format_ARGB32_Premultiplied,
                          QImage.Format_ARGB32,
                          QImage.Format_RGB32):
        buf = image.bits()
        # TODO: is this needed??
        if pf.gui.bindings == 'pyqt5':
            buf = buf.asstring(image.byteCount())
        ar = np.frombuffer(buf, dtype='ubyte',
                           count=image.byteCount()).reshape(h, w, 4)
        idx = ['BGRA'.index(c) for c in order]
        ar = ar[..., idx]
        ct = None

    elif image.format() == QImage.Format_Indexed8:
        ct = np.array(image.colorTable(), dtype=np.uint32)
        ct = ct.view(np.uint8).reshape(-1, 4)
        idx = ['BGRA'.index(c) for c in order]
        ct = ct[..., idx]
        buf = image.bits()
        # TODO: is this needed??
        if pf.gui.bindings == 'pyqt5':
            buf = buf.asstring(image.byteCount())
        ar = np.frombuffer(buf, dtype=np.uint8)
        if ar.size % h == 0:
            ar = ar.reshape(h, -1)
            if ar.shape[1] > w:
                # The QImage buffer always has a size corresponding
                # with a width that is a multiple of 8. Here we strip
                # off the padding pixels of the QImage buffer to the
                # reported width.
                ar = ar[:, :w]

        if ar.size != w*h:
            # This should no longer happen, since we have now adjusted
            # the numpy buffer width to the correct image width.
            pf.warning(f"Size of image data ({ar.size}) does not match "
                       f"the reported dimensions: {w} x {h} = {w*h}")

    else:
        raise ValueError("qimage2numpy only supports 32bit and 8bit images. "
                         f"Your qimage format is {image.format()}")

    # Put upright as expected
    if flip:
        ar = np.flipud(ar)

    # Convert indexed to nonindexed if requested
    if indexed is False and ct is not None:
        ar = ct[ar]
        ct = None

    # Return only full colors if requested
    if indexed is False:
        return ar
    else:
        return ar, ct


# TODO: make flip=True the default ?
def numpy2qimage(array, flip=False):
    """
    Convert a 2D or 3D integer numpy array into a QImage

    Parameters
    ----------
    array: 2D or 3D int array
        If the input array is 2D, the array is converted into a gray image.
        If the input array is 3D, the last axis should have length 3 or 4
        and represents the color channels in order RGB or RGBA.
    flip: bool
        If True, the image scanlines are flipped upside down.
        This is practical because image files are usually stored in top down
        order, while OpenGL uses an upwards positive direction, requiring a
        flip to show the image upright.

    Notes
    -----
    This is equivalent to calling :func:`gray2qimage` for a 2D array
    and :func:`rgb2qimage` for a 3D array.

    """
    if flip:
        array = np.flipud(array)
    if np.ndim(array) == 2:
        return gray2qimage(array)
    elif np.ndim(array) == 3:
        return rgb2qimage(array)
    raise ValueError("can only convert 2D or 3D arrays")


def gray2qimage(gray):
    """
    Convert a 2D numpy array to gray QImage.

    Parameters
    ----------
    gray: uint8 array (height,width)
        Array with the grey values of an image with size (height,width).

    Returns
    -------
    QImage
        A QImage with the corresponding gray image. The image format
        will be indexed.
    """
    if len(gray.shape) != 2:
        raise ValueError("gray2QImage can only convert 2D arrays")

    gray = np.require(gray, np.uint8, 'C')
    h, w = gray.shape
    result = QImage(gray.data, w, h, QImage.Format_Indexed8)
    result.ndarray = gray
    for i in range(256):
        result.setColor(i, QColor(i, i, i).rgb())
    return result


def rgb2qimage(rgb):
    """
    Convert a 3D numpy array into a 32-bit QImage.

    Parameters
    ----------
    rgb: int array (height,width,ncomp)
        Int array with the pixel values of the image. The data can have
        3 (RGB) or 4 (RGBA) components.

    Returns
    -------
    QImage
        A QImage with size (height,width) in the format
        RGB32 (3 components) or ARGB32 (4 components).
    """
    if len(rgb.shape) != 3:
        raise ValueError(
            "rgb2QImage expects the first (or last) dimension "
            "to contain exactly three (R,G,B) channels")
    if rgb.shape[2] != 3:
        raise ValueError("rgb2QImage can only convert 3D arrays")

    h, w, channels = rgb.shape

    # Qt expects 32bit BGRA data for color images:
    bgra = np.empty((h, w, 4), np.uint8, 'C')
    bgra[..., 0] = rgb[..., 2]
    bgra[..., 1] = rgb[..., 1]
    bgra[..., 2] = rgb[..., 0]

    if channels == 4:
        bgra[..., 3] = rgb[..., 3]
        fmt = QImage.Format_ARGB32
    else:
        fmt = QImage.Format_RGB32

    result = QImage(bgra.data, w, h, fmt)
    result.ndarray = bgra
    return result


def qimage2glcolor(image, resize=(0, 0), order='RGB'):
    """
    Convert a bitmap image to corresponding OpenGL colors.

    Parameters
    ----------
    image: :term:`qimage_like`
        A QImage or any data that can be converted to a QImage,
        e.g. the name of an image file, in any of the formats supported by Qt.
        The image can be a full color image or an indexed type. Only 32bit
        and 8bit images are currently supported.
    resize: tuple of ints
        A tuple of two integers (width,height). Positive value will
        force the image to be resized to this value.

    Returns
    -------
    float array (w,h,3)
        Array of float values in the range 0.0 to 1.0,
        containing the OpenGL colors corresponding to the image RGB colors.
        By default the image is flipped upside-down because the vertical
        OpenGL axis points upwards, while bitmap images are stored downwards.
    """
    c = qimage2numpy(image, resize=resize, order=order, flip=True, indexed=False)
    c = c.reshape(-1, len(order))
    c = c / 255.
    return c, None


def removeAlpha(qim):
    """
    Remove the alpha component from a QImage.

    Directly saving a QImage grabbed from the OpenGL buffers always
    results in an image with transparency.
    See https://savannah.nongnu.org/bugs/?36995 .

    This function will remove the alpha component from the QImage, so
    that it can be saved with opaque objects.

    Note: we did not find a way to do this directly on the QImage,
    so we go through a conversion to a numpy array and back.
    """
    ar, cm = qimage2numpy(qim, flip=False)
    return rgb2qimage(ar[..., :3])


def saveGreyImage(a, f, flip=True):
    """
    Save a 2D int array as a grey image.

    Parameters
    ----------
    a: int array
        Int array (height,width) with values in the range 0..255. These are
        the grey values of the pixels.
    f: str
        Name of the file to write the image to.
    flip: bool
        If True (default), the vertical axis is flipped, so that images are
        stored starting at the top. If your data already have the vertical axis
        downwards, use flip=False.

    Note
    ----
    This stores the image as an RGB image with equal values for all
    three color components.
    """
    a = at.checkArray(a, ndim=2, kind='u', allow='i').astype(np.uint8)
    c = np.flipud(a)
    c = np.dstack([c, c, c])
    im = numpy2qimage(c)
    im.save(f)


if utils.Module.has('pydicom') or pf.sphinx:
    from .dicomstack import DicomStack, dicom2numpy   # noqa: F401

# End
