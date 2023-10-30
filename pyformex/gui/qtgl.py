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
"""Qt OpenGL format

"""

import pyformex as pf
from pyformex.gui import QtOpenGL

############### OpenGL Format #################################

_opengl_format = None

def getOpenGLFormat():
    if _opengl_format is None:
        raise RuntimeError(
            "The OpenGL format has not been initialized yet!"
            " You should call setOpenGLFormat first.")
    return _opengl_format


def setOpenGLFormat():
    """Set the correct OpenGL format.

    On a correctly installed system, the default should do well.
    The default OpenGL format can be changed by command line options::

       --dri   : use the Direct Rendering Infrastructure, if available
       --nodri : do not use the DRI
       --opengl : set the opengl version
       --(no)multisample
    """
    global _opengl_format
    fmt = QtOpenGL.QGLFormat.defaultFormat()
    if pf.DEBUG.OPENGL in pf.options.debuglevel:
        pf.debug(OpenGLVersions(fmt), pf.DEBUG.OPENGL)
        pf.debug("Initial " + OpenGLFormat(fmt), pf.DEBUG.OPENGL)
    if pf.options.dri is not None:
        fmt.setDirectRendering(pf.options.dri)
    try:
        major, minor = pf.cfg['opengl/version'].split('.')
        fmt.setVersion(int(major), int(minor))
    except Exception:
        print(f"Can not use OpenGL version {pf.cfg['opengl/version']}"
              "Will try to use whatever is available")

    if pf.options.multisample:
        fmt.setSampleBuffers(True)
    QtOpenGL.QGLFormat.setDefaultFormat(fmt)
    #QtOpenGL.QGLFormat.setOverlayFormat(fmt)
    #fmt.setDirectRendering(False)
    _opengl_format = fmt
    if pf.DEBUG.OPENGL in pf.options.debuglevel:
        pf.debug("Set " + OpenGLFormat(fmt), pf.DEBUG.OPENGL)
    return fmt


def OpenGLFormat(fmt=None):
    """Report information about the OpenGL format."""
    if fmt is None:
        fmt = _opengl_format
    flags = fmt.openGLVersionFlags()
    return f"""\
OpenGL Format
OpenGL: {fmt.hasOpenGL()}
OpenGl Version: {fmt.majorVersion()}.{fmt.minorVersion()} ({int(flags)})
OpenGLOverlays: {fmt.hasOpenGLOverlays()}
Double Buffer: {fmt.doubleBuffer()}
Depth Buffer: {fmt.depth()}
RGBA: {fmt.rgba()}
Alpha Channel: {fmt.alpha()}
Accumulation Buffer: {fmt.accum()}
Stencil Buffer: {fmt.stencil()}
Stereo: {fmt.stereo()}
Direct Rendering: {fmt.directRendering()}
Overlay: {fmt.hasOverlay()}
Plane: {fmt.plane()}
Multisample Buffers: {fmt.sampleBuffers()} ({fmt.samples()})
"""

def OpenGLSupportedVersions(flags):
    """Return the supported OpenGL version.

    flags is the return value of QGLFormat.OpenGLVersionFlag()

    Returns a list with tuple (k,v) where k is a string describing an Opengl
    version and v is True or False.
    """
    flag = QtOpenGL.QGLFormat.OpenGLVersionFlag
    keys = [k for k in dir(flag) if k.startswith('OpenGL') and not k.endswith('None')]
    return [(k, bool(int(flags) & int(getattr(flag, k)))) for k in keys]


def OpenGLVersions(fmt=None):
    """Report information about the supported OpenGL versions."""
    if fmt is None:
        fmt = _opengl_format
    flags = fmt.openGLVersionFlags()
    s = ["Supported OpenGL versions:"]
    for k, v in OpenGLSupportedVersions(flags):
        s.append("  %s: %s" % (k, v))
    return '\n'.join(s)


def printOpenGLContext(ctxt):
    if ctxt:
        print("context is valid: %d" % ctxt.isValid())
        print("context is sharing: %d" % ctxt.isSharing())
    else:
        print("No OpenGL context yet!")


def hasDRI():
    """Check whether the OpenGL canvas has DRI enabled."""
    return _opengl_format.directRendering()


# End
