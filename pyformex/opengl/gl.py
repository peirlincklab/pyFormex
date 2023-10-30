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

"""OpenGL access functions

All calls to opengl functions are collected here, so we can easily
select different gl engines.
"""
import pyformex as pf
from pyformex.software import SaneVersion

if not pf.sphinx and pf.options.gl3:
    from pyformex.opengl3.GL import GL, GLU
else:
    from OpenGL import GL, GLU
    from OpenGL.GL import shaders

######## For Camera class #######

def gl_projection():
    """Get the OpenGL projection matrix"""
    return GL.glGetDoublev(GL.GL_PROJECTION_MATRIX)
def gl_modelview():
    """Get the OpenGL modelview matrix"""
    return GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX)
def gl_viewport():
    """Get the OpenGL viewport"""
    return GL.glGetIntegerv(GL.GL_VIEWPORT)
def gl_loadmodelview(m):
    """Load the OpenGL modelview matrix"""
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadMatrixf(m)
def gl_loadprojection(m):
    """Load the OpenGL projection matrix"""
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadMatrixf(m)
    # we reset OpenGL engine to default MODELVIEW
    GL.glMatrixMode(GL.GL_MODELVIEW)
def gl_depth(x, y):
    """Read the depth value of the pixel at (x,y)"""
    return GL.glReadPixels(x, y, 1, 1, GL.GL_DEPTH_COMPONENT, GL.GL_FLOAT)

# Canvas
def gl_version(mode='all'):
    return {
        'vendor': str(GL.glGetString(GL.GL_VENDOR)),
        'renderer': str(GL.glGetString(GL.GL_RENDERER)),
        'version': str(GL.glGetString(GL.GL_VERSION)),
        # Does not always exist, and is unneeded as of 3.3
        # 'glsl_version': str(GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION)),
        }

# Used in CanvasSettings.glOverride !
gl_linewidth = GL.glLineWidth
gl_pointsize = GL.glPointSize

fill_modes = [GL.GL_FRONT_AND_BACK, GL.GL_FRONT, GL.GL_BACK]
fill_mode = GL.GL_FRONT_AND_BACK

def gl_fillmode(mode):
    global fill_mode
    if mode in fill_modes:
        fill_mode = mode
def gl_frontfill():
    glFillMode(GL.GL_FRONT)
def gl_backfill():
    glFillMode(GL.GL_BACK)
def gl_bothfill():
    glFillMode(GL.GL_FRONT_AND_BACK)

def gl_fill(fill=True):
    if fill:
        GL.glPolygonMode(fill_mode, GL.GL_FILL)
    else:
        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)

def gl_linesmooth(onoff):
    if onoff is True:
        GL.glEnable(GL.GL_LINE_SMOOTH)
        GL.glHint(GL.GL_LINE_SMOOTH_HINT, GL.GL_NICEST)
    elif onoff is False:
        GL.glDisable(GL.GL_LINE_SMOOTH)


def gl_linestipple(factor, pattern):
    """Set the line stipple pattern.

    When drawing lines, OpenGl can use a stipple pattern. The stipple
    is defined by two values: a pattern (on/off) of maximum 16 bits,
    used on the pixel level, and a multiplier factor for each bit.

    If factor <= 0, the stippling is disabled.
    """
    print("Line stipple is currently not supported with gl2 engine")
    ## if factor > 0:
    ##     GL.glLineStipple(factor, pattern)
    ##     GL.glEnable(GL.GL_LINE_STIPPLE)
    ## else:
    ##     GL.glDisable(GL.GL_LINE_STIPPLE)


def gl_smooth(smooth=True):
    """Enable smooth shading"""
    if smooth:
        GL.glShadeModel(GL.GL_SMOOTH)
    else:
        GL.glShadeModel(GL.GL_FLAT)

def gl_flat():
    """Disable smooth shading"""
    gl_smooth(False)


def onOff(onoff):
    """Convert On/Off strings to a boolean"""
    if isinstance(onoff, str):
        return (onoff.lower() == 'on')
    else:
        if onoff:
            return True
        else:
            return False


def gl_enable(facility, onoff):
    """Enable/Disable an OpenGL facility, depending on onoff value

    facility is an OpenGL facility.
    onoff can be True or False to enable, resp. disable the facility, or
    None to leave it unchanged.
    """
    #pf.debug("%s: %s" % (facility,onoff),pf.DEBUG.DRAW)
    if onOff(onoff):
        #pf.debug("ENABLE",pf.DEBUG.DRAW)
        GL.glEnable(facility)
    else:
        #pf.debug("DISABLE",pf.DEBUG.DRAW)
        GL.glDisable(facility)


def gl_culling(onoff=True):
    gl_enable(GL.GL_CULL_FACE, onoff)
def gl_noculling():
    gl_culling(False)


def gl_polygonfillmode(mode):
    if isinstance(mode, str):
        mode = mode.lower()
        if mode == 'Front and Back':
            gl_bothFill()
        elif mode == 'Front':
            gl_frontFill()
        elif mode == 'Back':
            gl_backFill()


def gl_polygonmode(mode):
    if isinstance(mode, str):
        mode = mode.lower()
        gl_fill(mode == 'fill')


def gl_shademodel(model):
    if isinstance(model, str):
        model = model.lower()
        if model == 'smooth':
            gl_smooth()
        elif model == 'flat':
            gl_flat()


def gl_polygonoffset(value):
    if value <= 0.0:
        GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)
    else:
        GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)
        GL.glPolygonOffset(value, value)


def gl_viewport():
    """Return the current OpenGL Viewport

    Returns a tuple x,y,w,h spcifying the position and size of the
    current OpenGL viewport (in pixels).
    """
    return GL.glGetIntegerv(GL.GL_VIEWPORT)


### OLD: to be rmoved (still used in viewport menu)
def gl_settings(settings):
    pf.debug("GL SETTINGS: %s" % settings, pf.DEBUG.DRAW)
    gl_shadeModel(settings.get('Shading', None))
    gl_culling(settings.get('Culling', None))
    #glLighting(settings.get('Lighting', None))
    gl_linesmooth(onOff(settings.get('Line Smoothing', None)))
    gl_polygonfillmode(settings.get('Polygon Fill', None))
    gl_polygonmode(settings.get('Polygon Mode', None))
    pf.canvas.update()

# End
