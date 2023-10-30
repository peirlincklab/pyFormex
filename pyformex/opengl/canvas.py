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
"""This implements an OpenGL drawing widget for painting 3D scenes.

"""
import numpy as np

import pyformex as pf

from . import gl
from .gl import GL, GLU

from pyformex import utils
from pyformex import arraytools as at
from pyformex import colors
from pyformex.coords import Coords, bbox
from pyformex.mydict import Dict
from pyformex.collection import Collection
from pyformex.simple import cuboid2d
from pyformex.gui import views
from .sanitize import saneColor
from .canvas_settings import CanvasSettings, Light, LightProfile
from .scene import Scene, ItemList
from .renderer import Renderer
from .actors import Actor
from .camera import Camera
from .decors import Grid2D

### Some (OLD) drawing functions ############################################

# But still kept because used!

def drawDot(x, y):
    """Draw a dot at canvas coordinates (x,y)."""
    GL.glBegin(GL.GL_POINTS)
    GL.glVertex2f(x, y)
    GL.glEnd()


def drawLine(x1, y1, x2, y2):
    """Draw a straight line from (x1,y1) to (x2,y2) in canvas coordinates."""
    GL.glBegin(GL.GL_LINES)
    GL.glVertex2f(x1, y1)
    GL.glVertex2f(x2, y2)
    GL.glEnd()


def drawRect(x1, y1, x2, y2):
    """Draw the circumference of a rectangle."""
    GL.glBegin(GL.GL_LINE_LOOP)
    GL.glVertex2f(x1, y1)
    GL.glVertex2f(x1, y2)
    GL.glVertex2f(x2, y2)
    GL.glVertex2f(x2, y1)
    GL.glEnd()


def drawGrid(x1, y1, x2, y2, nx, ny):
    """Draw a rectangular grid of lines

    The rectangle has (x1,y1) and and (x2,y2) as opposite corners.
    There are (nx,ny) subdivisions along the (x,y)-axis. So the grid
    has (nx+1) * (ny+1) lines. nx=ny=1 draws a rectangle.
    nx=0 draws 1 vertical line (at x1). nx=-1 draws no vertical lines.
    ny=0 draws 1 horizontal line (at y1). ny=-1 draws no horizontal lines.
    """
    GL.glBegin(GL.GL_LINES)
    ix = range(nx+1)
    if nx==0:
        jx = [1]
        nx = 1
    else:
        jx = ix[::-1]
    for i, j in zip(ix, jx):
        x = (i*x2+j*x1)/nx
        GL.glVertex2f(x, y1)
        GL.glVertex2f(x, y2)

    iy = range(ny+1)
    if ny==0:
        jy = [1]
        ny = 1
    else:
        jy = iy[::-1]
    for i, j in zip(iy, jy):
        y = (i*y2+j*y1)/ny
        GL.glVertex2f(x1, y)
        GL.glVertex2f(x2, y)
    GL.glEnd()


#############################################################################
#############################################################################
#
#  The Canvas
#
#############################################################################
#############################################################################


def print_camera(self):
    print(self.report())


def print_lighting(s):
    try:
        settings = pf.GUI.viewports.current.settings
        print("%s: LIGTHING %s (%s)" %(s, settings.lighting, id(settings)))
    except Exception:
        print("No settings yet")


class Canvas():
    """A canvas for OpenGL rendering.

    The Canvas is a class holding all global data of an OpenGL scene rendering.
    It always contains a Scene with the actors and decorations that are drawn
    on the canvas. The canvas has a Camera holding the viewing parameters
    needed to project the scene on the canvas.
    Settings like colors, line types, rendering mode and the lighting
    information are gathered in a CanvasSettings object.
    There are attributes for some special purpose decorations (Triade, Grid)
    that can not be handled by the standard drawing and Scene changing
    functions.

    The Canvas class does not however contain the viewport size and position.
    The class is intended as a mixin to be used by some OpenGL widget class
    that will hold this information (such as the QtCanvas class).

    Important note: the Camera object is not initalized by the class
    initialization. The derived class initialization should therefore
    explicitely call the `initCamera` method before trying to draw anything
    to the canvas. This is because initializing the camera requires a working
    OpenGL format, which is only established by the derived OpenGL widget.
    """

    def __init__(self, settings={}):
        """Initialize an empty canvas with default settings."""
        from pyformex.gui import views
        #loadLibGL()
        self.scene = Scene(self)
        self.renderer = None
        self.highlights = ItemList(self)
        self.camera = None
        self.triade = None
        self.grid = None
        self.settings = CanvasSettings(**settings)
        self.mode2D = False
        self.setRenderMode(pf.cfg['draw/rendermode'])
        self.picking = False
        self.resetLighting()
        self._focus = None
        self.focus = False
        self.state = (0,0)
        pf.debug("Canvas Setting:\n%s"% self.settings, pf.DEBUG.DRAW)
        self.makeCurrent()  # we need correct OpenGL context

    @property
    def rendermode(self):
        return self.settings.rendermode

    @rendermode.setter
    def rendermode(self, mode):
        if mode not in CanvasSettings.RenderProfiles:
            raise ValueError("Invalid render mode %s" % mode)
        self.settings.rendermode = mode

    @property
    def focus(self):
        return self._focus is not None

    @focus.setter
    def focus(self, onoff):
        if onoff:
            self.add_focus_rectangle()
        else:
            self.remove_focus_rectangle()
        self.updateGL()


    @property
    def actors(self):
        return self.scene.actors

    @property
    def bbox(self):
        return self.scene.bbox

    def sceneBbox(self):
        """Return the bbox of all actors in the scene"""
        return bbox(self.scene.actors)


    ## def enable_lighting(self, state):
    ##     """Toggle OpenGL lighting on/off."""
    ##     glLighting(state)


    def resetDefaults(self, dict={}):
        """Return all the settings to their default values."""
        self.settings.reset(dict)
        self.resetLighting()
        ## self.resetLights()

    def setAmbient(self, ambient):
        """Set the global ambient lighting for the canvas"""
        self.lightprof.ambient = float(ambient)

    def setMaterial(self, matname):
        """Set the default material light properties for the canvas"""
        self.material = pf.GUI.materials[matname]


    def resetLighting(self):
        """Change the light parameters"""
        self.lightmodel = pf.cfg['render/lightmodel']
        self.setMaterial(pf.cfg['render/material'])
        self.lightset = pf.cfg['render/lights']
        lights = [Light(**pf.cfg['light/%s' % light]) for light in self.lightset]
        self.lightprof = LightProfile(pf.cfg['render/ambient'], lights)


    def resetOptions(self):
        """Reset the Drawing options to default values"""
        self.drawoptions = dict(
            view = None,        # Keep the current camera angles
            bbox = 'auto',      # Automatically zoom on the drawed object
            clear_ = False,     # Clear on each drawing action
            shrink = False,
            shrink_factor = 0.8,
            wait = True,
            silent = True,
            single = False,
            )

    def setOptions(self, d):
        """Set the Drawing options to some values"""

        ## # BEWARE
        ## # We rename the 'clear' to 'clear_', because we use a Dict
        ## # to store these (in __init__.draw) and Dict does not allow
        ## # a 'clear' key.

        if 'clear' in d and isinstance(d['clear'], bool):
            d['clear_'] = d['clear']
            del d['clear']
        self.drawoptions.update(d)


    def setRenderMode(self, mode, lighting=None):
        """Set the rendering mode.

        This sets or changes the rendermode and lighting attributes.
        If lighting is not specified, it is set depending on the rendermode.

        If the canvas has not been initialized, this merely sets the
        attributes self.rendermode and self.settings.lighting.
        If the canvas was already initialized (it has a camera), and one of
        the specified settings is different from the existing, the new mode
        is set, the canvas is re-initialized according to the newly set mode,
        and everything is redrawn with the new mode.
        """
        if mode not in CanvasSettings.RenderProfiles:
            raise ValueError("Invalid render mode %s" % mode)

        self.settings.update(CanvasSettings.RenderProfiles[mode])
        if lighting is None:
            lighting = self.settings.lighting

        if self.camera:
            if mode != self.rendermode or lighting != self.settings.lighting:
                self.rendermode = mode
                self.scene.changeMode(self, mode)

            self.settings.lighting = lighting
            self.reset()

        else:
            pf.debug("NO camera, but setting rendermode anyways", pf.DEBUG.OPENGL)
            self.rendermode = mode


    def setWireMode(self, state=None, mode=None):
        """Set the wire mode.

        This toggles the drawing of edges on top of 2D and 3D geometry.
        State is either True or False, mode is 1, 2 or 3 to switch:

        1: all edges
        2: feature edges
        3: border edges

        If no mode is specified, the current wiremode is used. A negative
        value inverses the state.
        """
        oldstate = self.settings.wiremode
        if state is None and mode is None:
            # just toggle
            state = -oldstate
        else:
            if mode is None:
                mode = abs(oldstate)
            if state is False:
                state = -mode
            else:
                state = mode
        self.settings.wiremode = state
        self.do_wiremode(state, oldstate)


    def getToggle(self, attr):
        """Get the value of a toggle attribute"""
        if attr == 'perspective':
            return self.camera.perspective
        else:
            return self.settings[attr]


    def setToggle(self, attr, state):
        """Set or toggle a boolean settings attribute

        Furthermore, if a Canvas method do_ATTR is defined, it will be called
        with the old and new toggle state as a parameter.
        """
        oldstate = self.getToggle(attr)
        if state not in [True, False]:
            state = not oldstate
        if attr == 'perspective':
            self.camera.perspective = state
        else:
            self.settings[attr] = state
        try:
            func = getattr(self, 'do_'+attr)
            func(state, oldstate)
        except Exception:
            pass


    def do_wiremode(self, state, oldstate):
        """Change the wiremode"""
        #print("CANVAS.do_wiremode: %s -> %s"%(oldstate, state))
        if state != oldstate and (state>0 or oldstate>0):
            # switching between two <= modes does not change anything
            #print("Changemode %s" % self.settings.wiremode)
            self.scene.changeMode(self)
            self.display()


    def do_alphablend(self, state, oldstate):
        """Toggle alphablend on/off."""
        #print("CANVAS.do_alphablend: %s -> %s"%(state,oldstate))
        if state != oldstate:
            #self.renderer.changeMode(self)
            self.scene.changeMode(self)
            self.display()


    def do_lighting(self, state, oldstate):
        """Toggle lights on/off."""
        #print("CANVAS.do_lighting: %s -> %s"%(state,oldstate))
        if state != oldstate:
            self.enable_lighting(state)
            self.scene.changeMode(self)
            self.display()


    def do_avgnormals(self, state, oldstate):
        #print("CANVAS.do_avgnormals: %s -> %s" % (state, oldstate))
        if state!=oldstate and self.settings.lighting:
            self.scene.changeMode(self)
            self.display()


    def setLineWidth(self, lw):
        """Set the linewidth for line rendering."""
        self.settings.linewidth = float(lw)


    def setLineStipple(self, repeat, pattern):
        """Set the linestipple for line rendering."""
        self.settings.update({'linestipple': (repeat, pattern)})


    def setPointSize(self, sz):
        """Set the size for point drawing."""
        self.settings.pointsize = float(sz)


    def setBackground(self, color=None, image=None):
        """Set the color(s) and image.

        Change the background settings according to the specified parameters
        and set the canvas background accordingly. Only (and all) the specified
        parameters get a new value.

        Parameters:

        - `color`: either a single color, a list of two colors or a list of
          four colors.
        - `image`: an image to be set.
        """
        self.scene.backgrounds.clear()
        if color is not None:
            self.settings.update(dict(bgcolor=color))
        if image is not None:
            self.settings.update(dict(bgimage=image))
        color = self.settings.bgcolor
        if color.ndim == 1 and not self.settings.bgimage:
            pf.debug("Clearing fancy background", pf.DEBUG.DRAW)
        else:
            self.createBackground()


    def createBackground(self):
        """Create the background object."""
        F = cuboid2d(xmin=[-1., -1.], xmax=[1., 1.])
        # TODO: Currently need a Mesh for texture
        F = F.toMesh()
        image = None
        if self.settings.bgimage:
            from pyformex.plugins.imagearray import qimage2numpy
            try:
                image = qimage2numpy(self.settings.bgimage, indexed=False)
            except Exception:
                pass
        actor = Actor(F, name='background', rendermode='smooth',
                      color=[self.settings.bgcolor], texture=image,
                      rendertype=3, opak=True, lighting=False, view='front',
                      sticky=True)
        self.scene.addAny(actor)
        self.update()



    def setFgColor(self, color):
        """Set the default foreground color."""
        self.settings.fgcolor = colors.GLcolor(color)


    def setSlColor(self, color):
        """Set the highlight color."""
        self.settings.slcolor = colors.GLcolor(color)


    def setTriade(self, pos='lb', siz=100, triade=None):
        """Set the Triade for this canvas.

        Display the Triade on the current viewport.
        The Triade is a reserved Actor displaying the orientation of
        the global axes. It has special methods to show/hide it.
        See also: :meth:`removeTriade`, :meth:`hasTriade`

        Parameters:

        - `pos`: string of two characters. The characters define the horizontal
          (one of 'l', 'c', or 'r') and vertical (one of 't', 'c', 'b') position
          on the camera's viewport. Default is left-bottom.
        - `siz`: float: intended size (in pixels) of the triade.
        - `triade`: None or Geometry: defines the Geometry to be used for
          representing the global axes.

          If None, use the previously set triade, or set a default if no
          previous.

          If Geometry, use this to represent the axes. To be useful and properly
          displayed, the Geometry's bbox should be around [(-1,-1,-1),(1,1,1)].
          Drawing attributes may be set on the Geometry to influence
          the appearance. This allows to fully customize the Triade.

        """
        if self.triade:
            self.removeTriade()
        if triade:
            from pyformex.gui.draw import draw
            self.triade = None
            x, y, w, h = GL.glGetIntegerv(GL.GL_VIEWPORT)
            if pos[0] == 'l':
                x0 = x + siz
            elif pos[0] =='r':
                x0 = x + w - siz
            else:
                x0 = x + w // 2
            if pos[1] == 'b':
                y0 = y + siz
            elif pos[1] == 't':
                y0 = y + h - siz
            else:
                y0 = y + h // 2
            A = draw(triade.scale(siz), rendertype=-2, single=True, size=siz, x=x0, y=y0)
            self.triade = A
        elif self.triade:
            self.addAny(self.triade)


    def removeTriade(self):
        """Remove the Triade from the canvas.

        Remove the Triade from the current viewport.
        The Triade is a reserved Actor displaying the orientation of
        the global axes. It has special methods to draw/undraw it.
        See also: :meth:`setTriade`, :meth:`hasTriade`

        """
        if self.hasTriade():
            self.removeAny(self.triade)


    def hasTriade(self):
        """Check if the canvas has a Triade displayed.

        Return True if the Triade is currently displayed.
        The Triade is a reserved Actor displaying the orientation of
        the global axes.
        See also: :meth:`setTriade`, :meth:`removeTriade`

        """
        return self.triade is not None and self.triade in self.scene.decorations


    def setGrid(self, grid=None):
        """Set the canvas Grid for this canvas.

        Display the Grid on the current viewport.
        The Grid is a 2D grid fixed to the canvas.
        See also: :meth:`removeGrid`, :meth:`hasGrid`

        Parameters:

        - `grid`: None or Actor: The Actor to be displayed as grid. This will
          normall be a Grid2D Actor.
        """
        if self.grid:
            self.removeGrid()
        if grid:
            self.grid = grid
        if self.grid:
            self.addAny(self.grid)


    def removeGrid(self):
        """Remove the Grid from the canvas.

        Remove the Grid from the current viewport.
        The Grid is a 2D grid fixed to the canvas.
        See also: :meth:`setGrid`, :meth:`hasGrid`

        """
        if self.hasGrid():
            self.removeAny(self.grid)


    def hasGrid(self):
        """Check if the canvas has a Grid displayed.

        Return True if the Grid is currently displayed.
        The Grid is a 2D grid fixed to the canvas.
        See also: :meth:`setGrid`, :meth:`removeGrid`

        """
        return self.grid is not None and self.grid in self.scene.decorations


    def initCamera(self, camera=None):
        """Initialize the current canvas camera

        If a camera is provided, that camera is set. Else a new
        default camera is constructed.
        """
        self.makeCurrent()  # we need correct OpenGL context for camera
        if not isinstance(camera, Camera):
            camera = Camera()
        self.camera = camera
        if self.renderer is None:
            self.renderer = Renderer(self)
        self.renderer.camera = self.camera


    def clearCanvas(self):
        """Clear the canvas to the background color."""
        color = self.settings.bgcolor
        if color.ndim > 1:
            color = color[0]
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glClearColor(*colors.RGBA(color))
        self.setDefaults()


    def setSize(self, w, h):
        if h == 0:  # prevent divide by zero
            h = 1
        GL.glViewport(0, 0, w, h)
        self.aspect = float(w)/h
        self.camera.setLens(aspect=self.aspect)
        ## if self.scene.background:
        ##     # recreate the background to match the current size
        ##     self.createBackground()
        self.display()


    def drawit(self, a):
        """_Perform the drawing of a single item"""
        self.setDefaults()
        a.draw(self)


    def setDefaults(self):
        """Activate the canvas settings in the GL machine."""
        self.settings.activate()
        #self.enable_lighting(self.settings.lighting)
        GL.glDepthFunc(GL.GL_LESS)


    def overrideMode(self, mode):
        """Override some settings"""
        settings = CanvasSettings.RenderProfiles[mode]
        CanvasSettings.glOverride(settings, self.settings)


    def reset(self):
        """Reset the rendering engine.

        The rendering machine is initialized according to self.settings:
        - self.rendermode: one of
        - self.lighting
        """
        self.setDefaults()
        self.setBackground(self.settings.bgcolor, self.settings.bgimage)
        self.clearCanvas()
        GL.glClearDepth(1.0)	       # Enables Clearing Of The Depth Buffer
        GL.glEnable(GL.GL_DEPTH_TEST)	       # Enables Depth Testing
        GL.glEnable(GL.GL_CULL_FACE)
        if self.rendermode == 'wireframe':
            gl.gl_polygonoffset(0.0)
        else:
            gl.gl_polygonoffset(1.0)


    def glinit(self):
        """Initialize the rendering engine.

        """
        self.reset()


    def glFinish(self):
        """Flush all OpenGL commands, making sure the display is updated."""
        GL.glFinish()


    # TODO: this is here for compatibility reasons
    # should be removed after complete transition to shaders
    def draw_sorted_objects(self, objects, alphablend):
        """Draw a list of sorted objects through the fixed pipeline.

        If alphablend is True, objects are separated in opaque
        and transparent ones, and the opaque are drawn first.
        Inside each group, ordering is preserved.
        Else, the objects are drawn in the order submitted.
        """
        if alphablend:
            opaque = [a for a in objects if a.opak]
            transp = [a for a in objects if not a.opak]
            for obj in opaque:
                self.setDefaults()
                obj.draw(canvas=self)
            GL.glEnable(GL.GL_BLEND)
            GL.glDepthMask(GL.GL_FALSE)
            if pf.cfg['draw/disable_depth_test']:
                GL.glDisable(GL.GL_DEPTH_TEST)
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
            for obj in transp:
                self.setDefaults()
                obj.draw(canvas=self)
            GL.glEnable(GL.GL_DEPTH_TEST)
            GL.glDepthMask(GL.GL_TRUE)
            GL.glDisable(GL.GL_BLEND)
        else:
            for obj in objects:
                self.setDefaults()
                obj.draw(canvas=self)


    def display(self):
        """(Re)display all the actors in the scene.

        This should e.g. be used when actors are added to the scene,
        or after changing  camera position/orientation or lens.
        """
        self.makeCurrent()
        if self.picking:
            #self.settings.lighting = False
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
            GL.glClearColor(0.0,0.0,0.0,0.0)
            gl.gl_flat()
            GL.glDisable(GL.GL_BLEND)
        else:
            self.clearCanvas()
            gl.gl_smooth()
        gl.gl_fill()
        self.renderer.render(self.scene, self.picking)
        self.glFinish()


    def create_pickitems(self, obj_type):
        start = 1  # 0 is used to identify background pixels
        self.pick_nitems = [start]
        for a in self.actors:
            if pf.debugon(pf.DEBUG.PICK):
                print(f"Actor {a.name}, pickable: {a.pickable}")
            if a.pickable:
                start = a._add_pick(start, obj_type)
            self.pick_nitems.append(start)


    def renderpick(self, obj_type):
        """Show rendering for picking"""
        # Create pickitems
        self.create_pickitems(obj_type)
        self.picking = True
        self.display()


    def zoom_2D(self, zoom=None):
        if zoom is None:
            zoom = (0, self.width(), 0, self.height())
        GLU.gluOrtho2D(*zoom)


    def begin_2D_drawing(self):
        """Set up the canvas for 2D drawing on top of 3D canvas.

        The 2D drawing operation should be ended by calling end_2D_drawing.
        It is assumed that you will not try to change/refresh the normal
        3D drawing cycle during this operation.
        """
        #pf.debug("Start 2D drawing",pf.DEBUG.DRAW)
        if self.mode2D:
            #pf.debug("WARNING: ALREADY IN 2D MODE",pf.DEBUG.DRAW)
            return
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        self.zoom_2D()
        GL.glDisable(GL.GL_DEPTH_TEST)
        #self.enable_lighting(False)
        self.mode2D = True


    def end_2D_drawing(self):
        """Cancel the 2D drawing mode initiated by begin_2D_drawing."""
        #pf.debug("End 2D drawing",pf.DEBUG.DRAW)
        if self.mode2D:
            GL.glEnable(GL.GL_DEPTH_TEST)
            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glPopMatrix()
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glPopMatrix()
            #self.enable_lighting(self.settings.lighting)
            self.mode2D = False


    def addHighlight(self, itemlist):
        """Add a highlight or a list thereof to the 3D scene"""
        self.highlights.add(itemlist)

    def removeHighlight(self,itemlist=None):
        """Remove a highlight or a list thereof from the 3D scene.

        Without argument, removes all highlights from the scene.
        """
        if itemlist is None:
            itemlist = self.highlights[:]
        self.highlights.delete(itemlist)


    def addAny(self, itemlist):
        self.scene.addAny(itemlist)


    addActor = addAnnotation = addDecoration = addAny

    def removeAny(self, itemlist):
        self.scene.removeAny(itemlist)

    removeActor = removeAnnotation = removeDecoration = removeAny


    def removeAll(self, sticky=False):
        self.scene.clear(sticky)
        self.highlights.clear()


    def dummy(self):
        pass

    redrawAll = dummy


    def setBbox(self, bbox):
        #print("SETBBOX %s" % bbox)
        self.scene.bbox = bbox


    def setCamera(self, bbox=None, angles=None, orient='xy'):
        """Sets the camera looking under angles at bbox.

        This function sets the camera parameters to view the specified
        bbox volume from the specified viewing direction.

        Parameters:

        - `bbox`: the bbox of the volume looked at
        - `angles`: the camera angles specifying the viewing direction.
          It can also be a string, the key of one of the predefined
          camera directions

        If no angles are specified, the viewing direction remains constant.
        The scene center (camera focus point), camera distance, fovy and
        clipping planes are adjusted to make the whole bbox viewed from the
        specified direction fit into the screen.

        If no bbox is specified, the following remain constant:
        the center of the scene, the camera distance, the lens opening
        and aspect ratio, the clipping planes. In other words the camera
        is moving on a spherical surface and keeps focusing on the same
        point.

        If both are specified, then first the scene center is set,
        then the camera angles, and finally the camera distance.

        In the current implementation, the lens fovy and aspect are not
        changed by this function. Zoom adjusting is performed solely by
        changing the camera distance.
        """
        #
        # TODO: we should add the rectangle (digital) zooming to
        #       the docstring

        self.makeCurrent()

        # set scene center
        if bbox is not None:
            pf.debug("SETTING BBOX: %s" % bbox, pf.DEBUG.DRAW)
            self.setBbox(bbox)

            X0, X1 = self.scene.bbox
            self.camera.focus = 0.5*(X0+X1)

        # set camera angles
        if isinstance(angles, str):
            #print("canvas0: %s (%s)" % (angles, orient))
            angles, orient = views.getAngles(angles)
            #print("canvas1: %s (%s)" % (angles, orient))
        if angles is not None:
            #print("canvas2: %s (%s)" % (angles, orient))
            try:
                axes = views.getAngleAxes(orient)
                #print("canvas3: %s" % str(axes))
                if orient == 'xz':
                    angles = angles + (-90.,)
                    axes = axes + ((1., 0., 0.),)
                    #print("canvas4: %s (%s)" % (angles, axes))
                self.camera.setAngles(angles, axes)
            except Exception:
                raise ValueError("Invalid view angles specified: %s %s" % (angles, orient))

        # set camera distance and clipping planes
        if bbox is not None:
            #print("SET CAMERA %s" % bbox)
            # Currently, we keep the default fovy/aspect
            # and change the camera distance to focus
            fovy = self.camera.fovy
            #pf.debug("FOVY: %s" % fovy,pf.DEBUG.DRAW)
            self.camera.setLens(fovy, self.aspect)
            # Default correction is sqrt(3)
            correction = float(pf.cfg['gui/autozoomfactor'])
            tf = at.tand(fovy/2.)

            from pyformex import simple
            bbix = simple.regularGrid(X0, X1, [1, 1, 1], swapaxes=True)
            bbix = np.dot(bbix, self.camera.rot[:3, :3])
            bbox = Coords(bbix).bbox()
            dx, dy, dz = bbox[1] - bbox[0]
            vsize = max(dx/self.aspect, dy)
            dsize = bbox.dsize()
            offset = dz
            dist = (vsize/tf + offset) / correction

            if dist == np.nan or dist == np.inf:
                pf.debug("DIST: %s" % dist, pf.DEBUG.DRAW)
                return
            if dist <= 0.0:
                dist = 1.0
            self.camera.dist = dist

            ## print "vsize,dist = %s, %s" % (vsize,dist)
            ## near,far = 0.01*dist,100.*dist
            ## print "near,far = %s, %s" % (near,far)
            #near,far = dist-1.2*offset/correction,dist+1.2*offset/correction
            near, far = dist-2.0*dsize, dist+2.0*dsize
            # print "near,far = %s, %s" % (near,far)
            #print (0.0001*vsize,0.01*dist,near)
            # We set this very extreme, because near and far are not changed
            # in the zoom functions. TODO: fix this.
            near = max(near, 0.001*vsize, 0.001*dist)
            far = min(far, 10000.*vsize, 1000.*dist)
            # make sure near is positive far > near
            #print(f"NEAR = {near}; FAR = {far}")
            # Very small near gives rounding problems
            near = max(near, 0.1)
            #if near < 0.:
            #    near = np.finfo(at.Float).eps
            if far <= near:
                far = 2*near
            # print(f"DIST={dist}; DSIZE={dsize}; NEAR={near}; FAR={far}")
            self.camera.setClip(near, far)
            self.camera.resetArea()


    def project(self, x, y, z):
        """Map the object coordinates (x,y,z) to window coordinates."""
        return self.camera.project((x, y, z))[0]


    def unproject(self, x, y, z):
        """Map the window coordinates (x,y,z) to object coordinates."""
        return self.camera.unproject((x, y, z))[0]


    def zoom(self, f, dolly=True):
        """Dolly zooming.

        Zooms in with a factor `f` by moving the camera closer
        to the scene. This does not change the camera's FOV setting.
        It will change the perspective view though.
        """
        if dolly:
            self.camera.dolly(f)


    def zoomRectangle(self, x0, y0, x1, y1):
        """Rectangle zooming.

        Zooms in/out by changing the area and position of the visible
        part of the lens.
        Unlike zoom(), this does not change the perspective view.

        `x0,y0,x1,y1` are pixel coordinates of the lower left and upper right
        corners of the area of the lens that will be mapped on the
        canvas viewport.
        Specifying values that lead to smaller width/height will zoom in.
        """
        w, h = float(self.width()), float(self.height())
        self.camera.setArea(x0/w, y0/h, x1/w, y1/h)


    def zoomCentered(self, w, h, x=None, y=None):
        """Rectangle zooming with specified center.

        This is like zoomRectangle, but the zoom rectangle is specified
        by its center and size, which may be more appropriate when using
        off-center zooming.
        """
        self.zoomRectangle(x-w/2, y-h/2, x+w/2, y+w/2)


    def zoomAll(self):
        """Zoom to make full scene visible."""
        self.setCamera(bbox=self.sceneBbox())


    def saveBuffer(self):
        """Save the current OpenGL buffer"""
        self.save_buffer = GL.glGetIntegerv(GL.GL_DRAW_BUFFER)

    def showBuffer(self):
        """Show the saved buffer"""
        pass


    def add_focus_rectangle(self, color=colors.pyformex_pink):
        """Draw the focus rectangle."""
        if self._focus is None:
            self._focus = Grid2D(-1., -1., 1., 1., color=color, linewidth=2, rendertype=3)
            self._focus.sticky = True
        if self._focus not in self.scene.backgrounds:
            self.addAny(self._focus)
            self.update()


    def remove_focus_rectangle(self):
        if self._focus:
            self.removeAny(self._focus)
            self._focus = None


    def highlightSelection(self, K):
        """Highlight a selection of items on the canvas.

        K is Collection of actors/items as returned by the pick() method.
        """
        self.scene.removeHighlight()
        if K.obj_type == 'actor':
            for i in K.get(-1, []):
                self.scene.actors[i].setHighlight()
        else:
            for i in K.keys():
                if i >= 0:
                    if K.obj_type == 'element':
                        self.actors[i].addHighlightElements(K[i])
                    elif K.obj_type == 'point':
                        self.actors[i].addHighlightPoints(K[i])


    def removeHighlight(self):
        """Remove a highlight or a list thereof from the 3D scene.

        Without argument, removes all highlights from the scene.
        """
        self.scene.removeHighlight()
        for actor in self.scene.actors:
            actor.removeHighlight()


### End
