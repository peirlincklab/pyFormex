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
"""Interactive OpenGL Canvas embedded in a Qt widget.

This module implements user interaction with the OpenGL canvas defined in
module :mod:`canvas`.
`QtCanvas` is a single interactive OpenGL canvas, while `MultiCanvas`
implements a dynamic array of multiple canvases.
"""
import math
import numpy as np

import pyformex as pf
from pyformex import utils
from pyformex.formex import Formex
from pyformex.mesh import Mesh

from pyformex.opengl import canvas
from pyformex.opengl.gl import GL

from pyformex import arraytools as at
from pyformex.gui import QtCore, QtGui, QtOpenGL, QtWidgets
from pyformex.gui import qtutils
from pyformex.gui import qtgl
from pyformex.gui import image
from pyformex.plugins import imagearray


from pyformex.collection import Collection
from pyformex.config import Config
from pyformex.coords import Coords
from pyformex.arraytools import isInt, unitVector, stuur, checkInt
from pyformex.gui.signals import Signal

# Some 2D vector operations
# We could do this with the general functions of coords.py,
# but that would be overkill for this simple 2D vectors

def dotpr(v, w):
    """Return the dot product of vectors v and w"""
    return v[0]*w[0] + v[1]*w[1]

def length(v):
    """Return the length of the vector v"""
    return math.sqrt(dotpr(v, v))

def projection(v, w):
    """Return the (signed) length of the projection of vector v on vector w."""
    return dotpr(v, w)/length(w)


################# Constants for event handlers #########################

# keys
ESC = QtCore.Qt.Key_Escape
RETURN = QtCore.Qt.Key_Return    # Normal Enter
ENTER = QtCore.Qt.Key_Enter      # Num Keypad Enter

# mouse actions
PRESS = 0
MOVE = 1
RELEASE = 2

# mouse buttons
LEFT = QtCore.Qt.LeftButton
MIDDLE = QtCore.Qt.MidButton
RIGHT = QtCore.Qt.RightButton

# modifiers
NONE = QtCore.Qt.NoModifier
SHIFT = QtCore.Qt.ShiftModifier
CTRL = QtCore.Qt.ControlModifier
ALT = QtCore.Qt.AltModifier
META = QtCore.Qt.MetaModifier
ALLMODS = SHIFT | CTRL | ALT | META

_modifier = {
    'NONE': NONE,
    'SHIFT': SHIFT,
    'CTRL': CTRL,
    'ALT': ALT,
    'META': META,
}

# mouse modifiers used during picking actions
_PICK_MOVE = [_modifier[i] for i in pf.cfg['gui/mouse_mod_move']]
_PICK_SET = _modifier[pf.cfg['gui/mouse_mod_set']]
_PICK_ADD = _modifier[pf.cfg['gui/mouse_mod_add']]
_PICK_REMOVE = _modifier[pf.cfg['gui/mouse_mod_remove']]


################# Canvas Mouse Event Handler #########################

def custom_cursor(base):
    cbfile = pf.cfg['icondir'] / base + '-cb.xpm'
    cmfile = pf.cfg['icondir'] / base + '-cm.xpm'
    cb = QtGui.QPixmap(cbfile)
    cm = QtGui.QPixmap(cmfile)
    return QtGui.QCursor(cb, cm)


# class CursorShapeHandler():
#     """A class for handling the mouse cursor shape on the Canvas.

#     """
#     cursor_shape = {'default': QtCore.Qt.ArrowCursor,
#                     'pick': QtCore.Qt.CrossCursor,
#                     'busy': QtCore.Qt.BusyCursor,
#                     }
#     custom_cursors = ['mouse-pick']

#     def __init__(self, widget):
#         """Create a CursorHandler for the specified widget."""
#         self.widget = widget

#     def setCursorShape(self, shape):
#         """Set the cursor shape to shape"""
#         if shape in custom_cursors:
#             cursor = custom_cursor(shape),
#         else:
#             if shape not in QtCanvas.cursor_shape:
#                 shape = 'default'
#             cursor = QtCanvas.cursor_shape[shape]
#         self.setCursor(cursor)


#     def setCursorShapeFromFunc(self, func):
#         """Set the cursor shape to shape"""
#         if func in [self.mouse_rectangle]:
#             shape = 'mouse-pick'
#         else:
#             shape = 'default'
#         self.setCursorShape(shape)


class MouseHandler():
    """A class for handling the mouse events on the Canvas.

    mousefunc keeps track of the installed mouse functions.
    For each combination of mouse button and modifier key we keep a list
    of functions. Installing a function adds it at the start
    of the list. The first of the list is the active function.
    Reset pops the first off the list, making the next active.
    """
    buttons = [None, LEFT, MIDDLE, RIGHT]  # None is relevant for mouse tracking
    modifiers = [NONE, SHIFT, CTRL, ALT, META]
    cursor_shape = {'default': QtCore.Qt.ArrowCursor,
                    'cross': QtCore.Qt.CrossCursor,
                    'draw': QtCore.Qt.CrossCursor,
                    'busy': QtCore.Qt.BusyCursor,
                    }
    custom_cursor_shape = {'pick': 'mouse-pick'}

    def __init__(self, canvas):
        self.canvas = canvas
        self.mousefnc = {}
        for button in MouseHandler.buttons:
            self.mousefnc[button] = {}
            for mod in MouseHandler.modifiers:
                self.mousefnc[button][int(mod)] = []

    def set(self, button, mod, func):
        self.mousefnc[button][int(mod)].append(func)

    def reset(self, button, mod):
        try:
            self.mousefnc[button][int(mod)].pop()
        except IndexError:
            pass

    def get(self, button, mod):
        """Return the mouse function bound to button and mod"""
        try:
            return self.mousefnc[button][int(mod)][-1]
        except IndexError:
            return None

    def setCursorShape(self, shape):
        """Set the cursor shape to shape"""
        if shape in MouseHandler.custom_cursor_shape:
            cursor = custom_cursor(MouseHandler.custom_cursor_shape[shape])
        else:
            if shape not in MouseHandler.cursor_shape:
                shape = 'default'
            cursor = MouseHandler.cursor_shape[shape]
        self.canvas.setCursor(cursor)


################# Single Interactive OpenGL Canvas ###############


class QtCanvas(QtOpenGL.QGLWidget, canvas.Canvas):
    """A canvas for OpenGL rendering.

    This class provides interactive functionality for the OpenGL canvas
    provided by the :class:`canvas.Canvas` class.

    Interactivity is highly dependent on Qt. Putting the interactive
    functions in a separate class makes it esier to use the Canvas class
    in non-interactive situations or combining it with other GUI toolsets.

    The QtCanvas constructor may have positional and keyword arguments. The
    positional arguments are passed to the QtOpenGL.QGLWidget constructor,
    while the keyword arguments are passed to the canvas.Canvas constructor.
    """
    _exclude_members_ = ['Communicate']

    selection_filters = ['none', 'single', 'closest', 'conn0', 'conn1', 'conn2']

    # private signal class
    class Communicate(QtCore.QObject):
        RECTANGLE = Signal()
        CANCEL = Signal()
        DONE   = Signal()


    def __init__(self, *args, **kargs):
        """Initialize an empty canvas."""
        QtOpenGL.QGLWidget.__init__(self, *args)
        if pf.DEBUG.OPENGL in pf.options.debuglevel:
            fmt = qtgl.OpenGLFormat(self.format())
            pf.debug(f"QtCanvas.__init__:\n{fmt}", pf.DEBUG.OPENGL)
            # TODO: In case of multisample, report the number of samples here

        # Define our private signals
        self.signals = self.Communicate()
        self.setMinimumSize(32, 32)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                           QtWidgets.QSizePolicy.MinimumExpanding)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        canvas.Canvas.__init__(self, **kargs)
        self.mousehandler = MouseHandler(self)
        # Initial mouse funcs are dynamic handling
        # Also some modifier keys are bound to mouse movement operations
        # These can be used during picking operations
        for mod in set(_PICK_MOVE):
            self.mousehandler.set(LEFT, mod, self.dynarot)
            self.mousehandler.set(MIDDLE, mod, self.dynapan)
            self.mousehandler.set(RIGHT, mod, self.dynazoom)
        self.mousehandler.setCursorShape('default')
        self.button = None
        self.mod = NONE
        self.dynamouse = True  # dynamic mouse action works on mouse move
        self.dynamic = None    # what action on mouse move
        self.pick_modes = ['actor', 'element', 'face', 'edge', 'point']
        self.pick_tools = ['pix', 'any', 'all']
        self.pick_mode = None
        self.pick_tool = pf.cfg['draw/picktool']
        self.selection = Collection()
        self.trackfunc = None
        self.picked = None
        self.pickable = None
        self.drawmode = None
        self.drawing_mode = None
        self.drawing = None
        # Drawing options
        self.resetOptions()


    # def setCursorShape(self, shape):
    #     """Set the cursor shape to shape"""
    #     if shape in MouseHandler.custom_cursor_shape:
    #         cursor = custom_cursor(MouseHandler.custom_cursor_shape[shape])
    #     else:
    #         if shape not in MouseHandler.cursor_shape:
    #             shape = 'default'
    #         cursor = MouseHandler.cursor_shape[shape]
    #     self.canvas.setCursor(cursor)

    # def setCursorShapeFromFunc(self, func):
    #     """Set the cursor shape according to the specified function"""
    #     if func in [self.mouse_rectangle]:
    #         shape = 'pick' if self.canvas.pick_mode == 'point' else 'cross'
    #     elif func == self.mouse_draw:
    #         shape = 'draw'
    #     else:
    #         shape = 'default'
    #     self.mousehandler.setCursorShape(shape)


    def getSize(self):
        """Return the size of this canvas"""
        return qtutils.Size(self)


    def saneSize(self, width=-1, height=-1):
        """Return a cleverly resized canvas size.

        Computes a new size for the canvas, while trying to keep its
        current aspect ratio. Specified positive values are returned
        unchanged.

        Parameters
        ----------
        width: int
            Requested width of the canvas. If <=0, it is automatically
            computed from height and canvas aspect ratio, or set equal to
            canvas width.
        height: int
            Requested height of the canvas. If <=0, it is automatically
            computed from width and canvas aspect ratio, or set equal to
            canvas height.

        Returns
        -------
        width: int
            Adjusted canvas width.
        height: int
            Adjusted canvas height.

        """
        if width <= 0 or height <= 0:
            wc, hc = self.getSize()
            if height > 0:
                width = round(float(height)/hc*wc)
            elif width > 0:
                height = round(float(width)/wc*hc)
            else:
                width, height = wc, hc
        return width, height


    # TODO: negative sizes should probably resize all viewports
    # OR we need to implement frames
    def changeSize(self, width, height):
        """Resize the canvas to (width x height).

        If a negative value is given for either width or height,
        the corresponding size is set equal to the maximum visible size
        (the size of the central widget of the main window).

        Note that this may not have the expected result when multiple
        viewports are used.
        """
        if width < 0 or height < 0:
            w, h = pf.GUI.maxCanvasSize()
            if width < 0:
                width = w
            if height < 0:
                height = h
        self.resize(width, height)


    def image(self, *, resize=None, picking=None, remove_alpha=True):
        """Return the current OpenGL rendering in an image format.

        Parameters
        ----------
        resize: tuple of int, optional
            A tuple (width, height) with the requested image size. If either
            of these values is <= 0, it will be set from the other and the
            canvas aspect ratio. If not provided or both values are <= 0,
            the current canvas size will be used.
        remove_alpha: bool
            If True (default), the alpha channel is removed from the image.

        Returns
        -------
        qim: QImage
            The current OpenGL rendering as a QImage of the specified size.

        Notes
        -----
        The returned image can be written directly to an image file with
        ``qim.save(filename)``.

        See Also
        --------
        rgb: returns the canvas rendering as a numpy ndarray
        """
        self.makeCurrent()
        w, h = self.getSize()
        if resize:
            wc, hc = w, h
            w, h = self.saneSize(*resize)
        vcanvas = QtOpenGL.QGLFramebufferObject(
            w, h, QtOpenGL.QGLFramebufferObject.Depth)
        # With new FrameBufferObject
        # vcanvas = QtGui.QOpenGLFramebufferObject(
        #     w, h, QtGui.QOpenGLFramebufferObject.Depth)
        # print("IMAGE", vcanvas.attachment())
        vcanvas.bind()
        if resize:
            self.resize(w, h)
        if picking:
            self.renderpick(picking)
        else:
            self.display()
        self.glFinish()
        qim = vcanvas.toImage()
        vcanvas.release()
        if resize:
            self.resize(wc, hc)
            self.glFinish()
        del vcanvas
        if picking:
            # restore non-picking mode
            self.picking = False
            self.display()
            self.update()
            imagearray.removeAlpha(qim).save('pick_original.png')

        if remove_alpha:
            qim = imagearray.removeAlpha(qim)
        return qim


    def rgb(self, resize=None, remove_alpha=True, picking=False):
        """Return the current OpenGL rendering in an array format.

        Parameters
        ----------
        resize: tuple of int, optional
            A tuple (width, height) with the requested image size. If either
            of these values is <= 0, it will be set from the other and the
            canvas aspect ratio. If not provided or both values are <= 0,
            the current canvas size will be used.
        remove_alpha: bool
            If True (default), the alpha channel is removed from the image.
        picking: bool
            This argument is for internal use only.

        Returns
        -------
        ar: array
            The current OpenGL rendering as a numpy array of type uint.
            Its shape is (w,h,3) if remove_alpha is True (default)
            or (w,h,4) if remove_alpha is False.

        See Also
        --------
        image: return the current rendering as an image
        """
        qim = self.image(resize=resize, remove_alpha=False, picking=picking)
        ar, cm = imagearray.qimage2numpy(qim)
        if remove_alpha:
            ar = ar[..., :3]
        return ar


    def split_pickids(self, ids, obj_type='element'):
        """Convert picked pixel ids to element Collection"""
        K = Collection(obj_type=obj_type)
        key = 0
        for start, end in zip(self.pick_nitems[:-1], self.pick_nitems[1:]):
            mine = (ids >= start) * (ids < end)
            if obj_type == 'actor' and ids[mine].any():
                K.add([key], -1)
            elif obj_type == 'element':
                K.add(ids[mine] - start, key)
            else:  # obj_type = 'point'
                oids = ids[mine] - start
                actor = self.actors[key]
                if isinstance(actor.object, Formex):
                    oids = actor._translate_mesh_points_formex(oids)
                K.add(oids, key)
            key += 1
        return K


    def insideRect(self, rect=None, obj_type='element'):
        """Find collection of elements inside a rectangle"""
        if rect is None:
            rect = self.getRectangle()
        x0, y0, x1, y1 = rect
        h = self.height()
        qim = self.image(picking=obj_type)
        if pf.debugon(pf.DEBUG.PICK):
            qimmy = qim.copy(x0+1,h-y1+1,x1-x0-1,y1-y0-1)  # qt has y downwards
            savefile = pf.preffile.parent / 'pick_debug.png'
            imagearray.removeAlpha(qimmy).save(savefile)
        crop = imagearray.qimage2numpy(qim, indexed=False)
        if (x0,y0) == (x1,y1):
            # No movement: pick pixel under mouse
            crop = crop[y0, x0]
        else:
            x1, y1 = max(x1, x0+2), max(y1, y0+2)
            crop = crop[y0+1:y1, x0+1:x1]
        crop = crop.reshape(-1,4)
        print
        uniq = at.uniqueRows(crop)
        crop = crop[uniq]
        ids = crop.view(np.uint32).reshape(-1)
        return self.split_pickids(ids, obj_type=obj_type)


    def outline(self, size=(0, 0), profile='luminance', level=0.5, bgcolor=None,
                nproc=None):
        """Return the outline of the current rendering

        Parameters
        ----------
        size: tuple
             A tuple of ints (w,h) specifying the size of the image to
             be used in outline detection. A non-positive value will be set
             automatically from the current canvas size or aspect ratio.
        profile: callable
            The function to be used to translate pixel colors into a single
            value. The default is to use the luminance of the pixel color.
        level: float
            The isolevel at which to construct the outline.
        bgcolor: color_like
            A color that is to be interpreted as background color
            and will get a pixel value -0.5. This is currently experimental.
        nproc: int
            The number of processors to be used in the image processing.
            Default is to use as many as available.

        Returns
        -------
        Formex:
            The outline as a Formex of plexitude 2.
        """
        from pyformex.plugins.isosurface import isoline
        from pyformex.formex import Formex
        from pyformex.colors import luminance, RGBcolor
        self.camera.lock()
        w, h = self.saneSize(*size)
        data = self.rgb((w,h))
        shape = data.shape[:2]

        if bgcolor:
            bgcolor = RGBcolor(bgcolor)
            print("bgcolor = %s" % (bgcolor,))
            bg = (data==bgcolor).all(axis=-1)
            print(bg)
            data = luminance(data.reshape(-1, 3)).reshape(shape) + 0.5
            data[bg] = -0.5

        else:
            data = luminance(data.reshape(-1, 3)).reshape(shape)

        rng = data.max() - data.min()
        bbox = self.bbox
        ctr = self.camera.project((bbox[0]+bbox[1])*.05)
        axis = unitVector(self.camera.eye-self.camera.focus)
        #
        # NOTE: the + [0.5,0.5] should be checked and then be
        #       moved inside the isoline function!
        #
        seg = isoline(data, data.min()+level*rng, nproc=nproc) + [0.5, 0.5]
        if size is not None:
            wc, hc = self.getSize()
            sx = float(wc)/w
            sy = float(hc)/h
            #print("Post scaling %s,%s" % (sx,sy))
            seg[..., 0] *= sx
            seg[..., 1] *= sy
        X = Coords(seg).trl([0., 0., ctr[0][2]])
        shape = X.shape
        X = self.camera.unproject(X.reshape(-1, 3)).reshape(shape)
        self.camera.unlock()
        F = Formex(X)
        F.attrib(axis=axis)
        return F


####################### MOUSE RECTANGLE ############################

    def clip_coords(self, x, y):
        w, h = self.width(), self.height()
        x = 0 if x < 0 else w if x > w else x
        y = 0 if y < 0 else h if y > h else y
        return x, y

    def draw_state_line(self, x, y):
        """Store the pos and draw a rectangle to it."""
        self.state = self.clip_coords(x, y)
        canvas.drawLine(self.statex, self.statey, *self.state)

    def draw_state_rect(self, x, y):
        """Store the pos and draw a line to it."""
        self.state = self.clip_coords(x, y)
        canvas.drawRect(self.statex, self.statey, *self.state)

    def wait_interaction(self):
        """Wait for the user to finish some interaction."""
        timer = QtCore.QThread
        self.interaction_busy = True
        while self.interaction_busy:
            # This allows us to push mouse rectangle picking events
            if self.events:
               self.emit_events(self.events.pop(0))
            timer.msleep(20)
            pf.app.processEvents()

    def start_rectangle(self, func=None):
        self.rectangle = None
        self.rectangle_func = func
        self.mousehandler.set(LEFT, NONE, self.mouse_rectangle)
        self.mousehandler.setCursorShape('cross')
        if func is None:
            func = self.finish_rectangle
        self.signals.RECTANGLE.connect(func)

    def finish_rectangle(self):
        self.mousehandler.reset(LEFT, NONE)
        self.mousehandler.setCursorShape('default')
        self.update()

    def mouse_rectangle(self, x, y, action):
        """Draw a rectangle during mouse move.

        On PRESS, record the mouse position.
        On MOVE, show a rectangle.
        On RELEASE, store the picked rectangle and possibly execute a function
        """
        if action == PRESS:
            self.makeCurrent()
            self.update()
            if self.trackfunc:
                self.camera.setTracking(True)
                x, y, z = self.camera.focus
                self.zplane = self.project(x, y, z, True)[2]
                self.trackfunc(x, y, self.zplane)
            self.begin_2D_drawing()
            GL.glEnable(GL.GL_COLOR_LOGIC_OP)
            GL.glLogicOp(GL.GL_INVERT)   # An alternative is GL_XOR #
            self.draw_state_rect(x, y)   # Draw rectangle
            self.swapBuffers()

        elif action == MOVE:
            if self.trackfunc:
               self.trackfunc(x, y, self.zplane)
            self.draw_state_rect(*self.state)  # Remove old rectangle
            self.draw_state_rect(x, y)     # Draw new rectangle
            self.swapBuffers()

        elif action == RELEASE:
            self.draw_state_rect(*self.state)  # Remove old rectangle
            GL.glDisable(GL.GL_COLOR_LOGIC_OP)
            self.swapBuffers()
            self.end_2D_drawing()
            x0 = max(min(self.statex, x), 0)
            y0 = max(min(self.statey, y), 0)
            x1 = min(max(self.statex, x), self.width())
            y1 = min(max(self.statey, y), self.height())
            self.rectangle = x0, y0, x1, y1
            self.interaction_busy = False

    def mouse_line(self, x, y, action):
        """Draw a line during mouse move.

        On PRESS, record the mouse position.
        On MOVE, create a rectangular zoom window.
        On RELEASE, store the picked rectangle and possibly execute a function

        (self.statex, self.statey) is the start point
        self.state is the current end point
        """
        if action == PRESS:
            self.makeCurrent()
            self.update()
            if self.trackfunc:
                self.camera.setTracking(True)
                x, y, z = self.camera.focus
                self.zplane = self.project(x, y, z, True)[2]
                self.trackfunc(x, y, self.zplane)
            self.begin_2D_drawing()
            GL.glEnable(GL.GL_COLOR_LOGIC_OP)
            GL.glLogicOp(GL.GL_INVERT)   # An alternative is GL_XOR #
            self.draw_state_line(x, y)   # Draw line
            self.swapBuffers()

        elif action == MOVE:
            if self.trackfunc:
               self.trackfunc(x, y, self.zplane)
            self.draw_state_line(*self.state)  # Remove oldline
            self.draw_state_line(x, y)     # Draw new line
            self.swapBuffers()

        elif action == RELEASE:
            self.draw_state_line(*self.state)  # Remove line
            GL.glDisable(GL.GL_COLOR_LOGIC_OP)
            self.swapBuffers()
            self.end_2D_drawing()
            self.drawn = self.unproject(x, y, self.zplane)
            self.interaction_busy = False

    def mouse_draw(self, x, y, action):
        """Process mouse events during interactive drawing.

        On PRESS, do nothing.
        On MOVE, do nothing.
        On RELEASE, compute the unprojected point
        """
        if action == PRESS:
            self.makeCurrent()
            self.update()
            if self.trackfunc:
                print("ENABLE TRACKING")
                self.camera.setTracking(True)

        elif action == MOVE:
            if pf.app.hasPendingEvents():
                return
            if self.trackfunc:
                self.trackfunc(x, y, self.zplane)
            if self.previewfunc:
                self.swapBuffers()
                self.drawn = self.unproject(x, y, self.zplane)
                self.previewfunc(self)
                self.swapBuffers()

        elif action == RELEASE:
            self.drawn = self.unproject(x, y, self.zplane)
            self.interaction_busy = False


    def getRectangle(self, yup=True):
        """Let the user pick a rectangle.

        Returns: x0, y0, x1, y1 where x0<x1, y0<y1
        If yup is False, y values are downwards
        """
        self.start_rectangle()
        self.wait_interaction()
        self.finish_rectangle()
        if yup:
            return self.rectangle
        else:
            h = self.height()
            x0, y0, x1, y1 = self.rectangle
            return x0, h-y1, x1, h-y0

    def zoom_rectangle(self):
        self.zoomRectangle(*self.getRectangle())


####################### INTERACTIVE PICKING ############################


    def start_selection(self, mode, tool, filter, pickable=None):
        """Start an interactive picking mode.

        If selection mode was already started, mode is disregarded and
        this can be used to change the tool or filter.
        """
        if pf.debugon(pf.DEBUG.PICK):
            print(f"PICK: Start selection {mode=}, {tool=}, {filter=}")
        if self.pick_mode is None:
            self.pick_mode = mode
            self.mousehandler.set(LEFT, NONE, self.mouse_rectangle)
            self.mousehandler.set(LEFT, SHIFT, self.mouse_rectangle)
            self.mousehandler.set(LEFT, CTRL, self.mouse_rectangle)
            self.mousehandler.set(RIGHT, NONE, self.emit_done)
            self.mousehandler.set(RIGHT, SHIFT, self.emit_cancel)
            self.mousehandler.setCursorShape(
                'pick' if self.pick_mode == 'point' else 'cross')
            self.signals.DONE.connect(self.accept_selection)
            self.signals.CANCEL.connect(self.cancel_selection)
            self.pickable = pickable
            self.selection_front = None
        self.pick_tool = tool
        if filter == 'none':
            filter = None
        self.selection_filter = filter
        if filter is None:
            self.selection_front = None
        self.selection.clear()
        self.selection.obj_type = self.pick_mode
        if pf.debugon(pf.DEBUG.PICK):
            print(f"PICK started: {self.pick_mode=}, {self.selection}")
        self.removeHighlight()


    def finish_selection(self):
        """End an interactive picking mode."""
        if pf.debugon(pf.DEBUG.PICK):
            print("Finish selection")
        self.mousehandler.reset(LEFT, NONE)
        self.mousehandler.reset(LEFT, SHIFT)
        self.mousehandler.reset(LEFT, CTRL)
        self.mousehandler.reset(RIGHT, NONE)
        self.mousehandler.reset(RIGHT, SHIFT)
        self.mousehandler.setCursorShape('default')
        self.signals.DONE.disconnect(self.accept_selection)
        self.signals.CANCEL.disconnect(self.cancel_selection)
        self.pick_mode = None
        self.pickable = None


    def accept_selection(self, clear=False):
        """Accept or cancel an interactive picking mode.

        If clear == True, the current selection is cleared.
        """
        if pf.debugon(pf.DEBUG.PICK):
            print("Accept selection")
        self.selection_accepted = True
        if clear:
            self.selection.clear()
            self.selection_accepted = False
        self.selection_canceled = True
        self.interaction_busy = False


    def cancel_selection(self):
        """Cancel an interactive picking mode and clear the selection."""
        self.accept_selection(clear=True)


    def emit_events(self, events):
        #pf.logger.debug("sending events %s" % events)
        for event in events:
            pf.app.sendEvent(self, event)


    def pick_pixels(self):
        """Set the list of actor parts inside the pick_window.

        This implements the 'pix' picking tool.
        The picked object numbers are stored in self.picked.
        """
        if pf.debugon(pf.DEBUG.PICK):
            print(f"PICK_PIXELS {self.pick_mode}")
        # Allow a different pickable list than the pickable actors.
        # This is used in the draw2d plugin.
        if self.pickable is None:
            pickable = [a for a in self.actors if a.pickable]
        else:
            pickable = self.pickable
        self.picked = self.insideRect(self.rectangle, self.pick_mode)
        if pf.debugon(pf.DEBUG.PICK):
            print(f"self.picked={self.picked}")


    def pick_parts(self):
        """Set the list of actor parts inside the pick_window.

        This implements the 'any' and 'all' picking tool.
        The picked object numbers are stored in self.picked.
        """
        if pf.debugon(pf.DEBUG.PICK):
            print(f"PICK_PARTS {self.pick_mode=} "
                  f"{self.pick_tool=} {store_closest=}")
        # Allow a different pickable list than the pickable actors.
        # This is used in the draw2d plugin.
        if self.pickable is None:
            pickable = [a for a in self.actors if a.pickable]
        else:
            pickable = self.pickable
        self.picked = Collection(self.pick_mode)
        x0, y0, x1, y1 = self.rectangle
        x, y = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
        w, h = x1 - x0, y1 - y0
        if w <= 1 or h <= 1:
            w, h = pf.cfg['draw/picksize']
        vp = GL.glGetIntegerv(GL.GL_VIEWPORT)
        self.pick_window = (x, y, w, h, vp)
        if pf.debugon(pf.DEBUG.PICK):
            print(f"{self.pick_window=}")
        # Make sure we always return Actor index from self.actors
        for i, a in enumerate(self.actors):
            if a in pickable:
                picked = a.inside(
                    self.camera, rect=self.pick_window[:4], mode=self.pick_mode,
                    sel=self.pick_tool, return_depth=False)
                if self.pick_mode == 'actor':
                    if picked:
                        self.picked.add([i], key=-1)
                else:
                    self.picked.add(picked, key=i)


    def filter_closest(self, picked):
        """Narrow a Collection to its single item closest to the camera plane"""
        if not picked:
            return picked
        imin = -1
        jmin = None
        dmin = None
        if picked.obj_type == 'actor':
            for i in picked[-1]:
                o = self.actors[i].object
                # we use normal towards objects to have positive distances
                d = o.points().distanceFromPlane(
                    self.camera.eye, -self.camera.axis)
                d = d.min()
                if imin < 0 or d < dmin:
                    imin, dmin = i, d
            picked.clear()
            picked.add([imin], key=-1)
            picked.depth = dmin
        elif picked.obj_type == 'point':
            for i in picked:
                v = picked[i]
                o = self.actors[i].object
                d = o.points()[v].distanceFromPlane(
                    self.camera.eye, -self.camera.axis)
                j = d.argmin()
                if imin < 0 or d[j] < dmin:
                    imin, jmin, dmin = i, v[j], d[j]
            picked.clear()
            picked.add([jmin], key=imin)
            picked.depth = dmin
        elif picked.obj_type == 'element':
            for i in picked:
                v = picked[i]
                o = self.actors[i].object
                if isinstance(o, Formex):
                    X = o.coords[v]
                elif isinstance(o, Mesh):
                    X = o.coords[o.elems[v]]
                d = X.distanceFromPlane(self.camera.eye, -self.camera.axis)
                j = d.argmin() // X.shape[1]
                if imin < 0 or d[j] < dmin:
                    imin, jmin, dmin = i, v[j], d[j]
            picked.clear()
            picked.add([jmin], key=imin)
            picked.depth = dmin


    def filter_connected(self, picked, level=1):
        """Narrow a Collection to the items connected or self.selection"""
        if not picked:
            return
        if not self.selection:
            # set to closest picked item
            self.selection = picked.copy()
            self.filter_closest(self.selection)
        imin = -1
        jmin = None
        dmin = None
        if picked.obj_type == 'element':
            for i in self.selection:
                if i in picked:
                    o = self.actors[i].object
                    if not isinstance(o, Mesh):
                        del picked[i]
                    else:
                        start = self.selection[i]
                        new = self.picked[i]
                        test = np.union1d(start, new)
                        ok = o.connectedElements(start, test, level)
                        self.picked[i] = np.intersect1d(ok, new)


    def modify_selection(self):
        """Modify the current selection.

        This method is intended for use in the `func` of the :meth:`pick`
        method, to update the selection after each atomic pick.
        It modifies the selection depending on the used filters and on the
        modifier key pressed when doing the pick. Default is:

        - None: add to the selection
        - SHIFT: set as the selection (forgetting previous picks)
        - CTRL: remove from the selection

        Without filter, all the items in the last pick are involved.
        With a filter only a subset may be involved.
        """
        if self.mod == _PICK_SET:
            self.selection.set(self.picked)
        elif self.mod == _PICK_ADD:
            self.selection.add(self.picked)
        elif self.mod == _PICK_REMOVE:
            self.selection.remove(self.picked)
        if self.selection_filter == 'single':
            self.filter_closest(self.selection)


    def modify_and_highlight(self):
        """Modify selection and highlight updated selection.

        This method is the default `func` used in the pick method
        after each atomic pick. It modifies the selection according to
        the modifiers and filters, and highlights the resulting selection.
        """
        self.modify_selection()
        self.highlightSelection(self.selection)


    def pick(self, mode, tool='pix', oneshot=False, func=None,
             filter=None, pickable=None, _rect=None, minobj=0):
        """Interactively pick objects from the canvas.

        Parameters
        ----------
        mode: str
            Defines what to pick: one of ``actor``, ``element``, ``point``.
        oneshot: bool
            If True, the function returns as soon as the user ends
            an atomic picking operation (left mouse press and release).
            If False (default) the user can modify his selection until
            he explicitely accepts (right mouse button press or ENTER)
            or cancels (ESC) the pick operation.
        func: callable
            If provided, this function is called after each atomic pick
            operation (from mouse button press to mouse button release).
            The canvas self is passed as an argument. The last atomic pick
            is then available as `self.picked` and the previously collected
            selection (if collection is done) is in self.selection. This is
            commonly used to highlight the picked items, collect picked items,
            report picked items, compute and display features of picked
            items. If not provided, the default function
            :meth:`modify_and_highlight` is used. See there for details.
        filter: str
            Defines a filter to retain only some of the picked items in
            the selection. If not provided, all the picked items are retained.
            Available filters:

            - single: keeps only a single item
            - closest: keeps only the item closest to the user.
            - conn?: keeps only the items connected to the already selected
              items or to the closest picked item if nothing has been selected
              yet. The ? can be one of 0, 1 or 2 to define the level of
              the connectors (point, edge, face). The default is 1 (edge).
              The conn? filters only work when picking mode is 'element' and
              for objects of type Mesh.
        _rect: tuple
            A tuple (x0, y0, x1, y1) speciying the rectangular part on the
            canvas that will be picked. Allows simulated picking.

        Returns
        -------
        Collection:
            A (possibly empty) Collection with the picked items.
            After return, the value of the selection_accepted
            attribute can be tested to find how the picking operation was
            exited:

            - True: the selection was accepted (right mouse click, ENTER key,
              or OK button),
            - False: the selection was canceled (ESC key, or Cancel button).
              In the latter case, the returned Collection is always empty.
              It is also possible to test on the length of the selection.
        """
        self.setFocus()
        self.selection_canceled = False
        self.start_selection(mode, tool, filter, pickable)
        if not callable(func):
            func = QtCanvas.modify_and_highlight
        self.events = []
        if _rect:
            #create events for programmed pick
            self.events.extend(self.mouse_rect_pick_events(_rect))
        try:
            while not self.selection_canceled:
                self.wait_interaction()  # wait for user to pick a rectangle
                if not self.selection_canceled:
                    # if pf.debugon(pf.DEBUG.PICK):
                    #     print(f"{self.pick_tool=}, {self.rectangle=}")
                    if self.pick_tool == 'pix':
                        self.pick_pixels()  # pick by pixels
                    else:
                        self.pick_parts()  # pick by points
                    if self.selection_filter in ['single', 'closest']:
                        self.filter_closest(self.picked)
                    elif str(self.selection_filter)[:4] == 'conn':
                        try:
                            connlevel = int(self.selection_filter[5])
                        except:
                            connlevel = 1
                        self.filter_connected(self.picked, connlevel)
                    func(self)
                    self.update()
                    if (oneshot or
                        minobj > 0 and self.selection.total() >= minobj):
                        self.accept_selection()
        finally:
            self.finish_selection()
        return self.selection


    def mouse_rect_pick_events(self, rect=None):
        """Create the events for a mouse rectangle pick.

        Parameters
        ----------
        rect: tuple of ints, optional
            A tuple (x0,y0,x1,y1) specifying the top left corner and the
            bottom right corner of the rectangular are to be picked. Values
            are in pixels relative to the canvas widget.
            If not provided, the whole canvas area will be picked.

        Returns
        -------
        list
            A nested list of events. The list contains two sublists. The first
            holds the events to make the rectangle pick:

            - Press the left button mouse at (x0,y0).
            - Move the mouse while holding the left button pressed to (x1,y1).
            - Release the left mouse button at (x1,y1).

            The second sublist holds the events to accept the picked area:

            - Press the right mouse button at (x1,y1).
            - Release the right mouse button at (x1,y1).

        """
        if rect is None:
            x0, y0 = 0, 0
            x1, y1 = self.getSize()
        else:
            x0, y0, x1, y1 = rect
        event1 = QtGui.QMouseEvent(QtCore.QEvent.MouseButtonPress, QtCore.QPoint(x0, y0), QtCore.Qt.LeftButton, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier)
        event2 = QtGui.QMouseEvent(QtCore.QEvent.MouseMove, QtCore.QPoint(x1, y1), QtCore.Qt.NoButton, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier)
        event3 = QtGui.QMouseEvent(QtCore.QEvent.MouseButtonRelease, QtCore.QPoint(x1, y1), QtCore.Qt.LeftButton, QtCore.Qt.NoButton, QtCore.Qt.NoModifier)
        event4 = QtGui.QMouseEvent(QtCore.QEvent.MouseButtonPress, QtCore.QPoint(x1, y1), QtCore.Qt.RightButton, QtCore.Qt.RightButton, QtCore.Qt.NoModifier)
        event5 = QtGui.QMouseEvent(QtCore.QEvent.MouseButtonRelease, QtCore.QPoint(x1, y1), QtCore.Qt.RightButton, QtCore.Qt.NoButton, QtCore.Qt.NoModifier)
        return [[event1, event2, event3], [event4, event5]]


#################### Interactive drawing ####################################


    def add_point(self):
        from pyformex.gui import draw as gs
        self.drawing = Coords.concatenate([self.drawing, self.drawn])
        self.removeHighlight()
        gs.draw(self.drawing, highlight=True, color=0, marksize=10,
                ontop=True)


    def idraw(self, mode='point', npoints=-1, zplane=0.,
              func=None, coords=None, preview=False, mouseline=False):
        """Interactively draw on the canvas.

        This function allows the user to interactively create points in 2.5D
        space and collects the subsequent points in a Coords object. The
        interpretation of these points is left to the caller.
        The drawing operation is finished when the number of requested points
        has been reached, or when the user clicks the right mouse button or
        hits 'ENTER' or presses the ESC-button.

        Parameters
        ----------
        mode: str
            One of the drawing modes, specifying the kind of objects you
            want to draw. This is passed to the specified `func`.
        npoints: int
            Specifies how many points can be created before returning.
            If < 0, the continuous drawing mode has to be ended explicitely
            with an accept or cancel.
        zplane: float
            The depth of the z-plane on which the 2D drawing is done.
        func: callable
            A function that is called after each atomic drawing operation.
            It is typically used to accumulate the drawn points in a single
            set of points and draw a preview of the drawing. If not provided,
            the default will just do that.
            The function is passed the canvas as a parameter, from which the
            following data are available:

                - canvas.drawn: the newly drawn point,
                - canvas.drawing: the accumulated set of points
                - canvas.drawmode: the current drawing mode

        coords: Coords
            An initial set of coordinates to which the newly created
            points should be added. THis can be used to continue a previous
            idraw operation. If provided, `npoints` also counts these
            initial points.
        preview: bool
            If True, the func will also be called during mouse movement with
            a depressed button, allowing to preview the result before a point
            is actually created.

        Returns
        -------
        Coords (npts, 3)
            The Coordinates of the created points. On return
            canvas.draw_accepted will be True if the function returned
            because the number of points was reached or the result was
            accepted with a right mouse click or ENTER key;
            it will be False if the ESC button was hit.
        """
        self.setFocus()
        self.draw_canceled = False
        self.start_draw(mode, zplane, coords, mouseline)
        if not callable(func):
            func = QtCanvas.add_point
        self.previewfunc = func if preview else None
        self.events = []
        try:
            while not self.draw_canceled:
                self.wait_interaction()
                if not self.draw_canceled:
                    func(self)
                    self.update()
                if npoints > 0 and len(self.drawing) >= npoints:
                    self.accept_draw()
        finally:
            self.finish_draw()
        return self.drawing


    def start_draw(self, mode, zplane, coords, mouseline):
        """Start an interactive drawing mode."""
        #self.perspective(False)
        self.camera.lock()
        if mouseline:
            self.mousehandler.set(LEFT, NONE, self.mouse_line)
            self.mousehandler.set(None, NONE, self.mouse_line)
            self.mousehandler.setCursorShape('default')
        else:
            self.mousehandler.set(LEFT, NONE, self.mouse_draw)
            self.mousehandler.setCursorShape('draw')
        self.mousehandler.set(RIGHT, NONE, self.emit_done)
        self.mousehandler.set(RIGHT, SHIFT, self.emit_cancel)
        self.signals.DONE.connect(self.accept_draw)
        self.signals.CANCEL.connect(self.cancel_draw)
        self.drawmode = mode
        self.zplane = float(zplane)
        #print(f"START_DRAW {zplane=}")
        self.drawing = Coords(coords)

    def finish_draw(self):
        """End an interactive drawing mode."""
        self.mousehandler.reset(None, NONE)
        self.mousehandler.reset(LEFT, NONE)
        self.mousehandler.reset(RIGHT, NONE)
        self.mousehandler.reset(RIGHT, SHIFT)
        self.mousehandler.setCursorShape('default')
        self.signals.DONE.disconnect(self.accept_draw)
        self.signals.CANCEL.disconnect(self.cancel_draw)
        self.drawmode = None
        # self.perspective(original_perspective)
        # self.camera.unlock() # should unlock only if it wasn't lock

    def accept_draw(self, clear=False):
        """Cancel an interactive drawing mode.

        If clear == True, the current drawing is cleared.
        """
        self.draw_accepted = True
        if clear:
            self.drawing = Coords()
            self.draw_accepted = False
        self.draw_canceled = True
        self.interaction_busy = False

    def cancel_draw(self):
        """Cancel an interactive drawing mode and clear the drawing."""
        self.accept_draw(clear=True)


    def mouse_draw(self, x, y, action):
        """Process mouse events during interactive drawing.

        On PRESS, do nothing.
        On MOVE, do nothing.
        On RELEASE, compute the unprojected point
        """
        if action == PRESS:
            self.makeCurrent()
            self.update()
            if self.trackfunc:
                print("ENABLE TRACKING")
                self.camera.setTracking(True)

        elif action == MOVE:
            if pf.app.hasPendingEvents():
                return
            if self.trackfunc:
                self.trackfunc(x, y, self.zplane)
            if self.previewfunc:
                self.swapBuffers()
                self.drawn = self.unproject(x, y, self.zplane)
                self.previewfunc(self)
                self.swapBuffers()

        elif action == RELEASE:
            self.drawn = self.unproject(x, y, self.zplane)
            self.interaction_busy = False


##########################################################################
 # line drawing mode #

    def drawLinesInter(self, mode='line', oneshot=False, func=None):
        """Interactively draw lines on the canvas.

        - oneshot: if True, the function returns as soon as the user ends
          a drawing operation. The default is to let the user
          draw multiple lines and only to return after an explicit
          cancel (ESC or right mouse button).
        - func: if specified, this function will be called after each
          atomic drawing operation. The current drawing is passed as
          an argument. This can e.g. be used to show the drawing.

        When the drawing operation is finished, the drawing is returned.
        The return value is a (n,2,2) shaped array.
        """
        self.setFocus()
        self.drawing_canceled = False
        self.start_drawing(mode)
        while not self.drawing_canceled:
            self.wait_drawing()
            if not self.drawing_canceled:
                if self.edit_mode:  # an edit mode from the edit combo was clicked
                    if self.edit_mode == 'undo' and self.drawing.size != 0:
                        self.drawing = delete(self.drawing, -1, 0)
                    elif self.edit_mode == 'clear':
                        self.drawing = empty((0, 2, 2), dtype=int)
                    elif self.edit_mode == 'close' and self.drawing.size != 0:
                        line = asarray([self.drawing[-1, -1], self.drawing[0, 0]])
                        self.drawing = append(self.drawing, line.reshape(-1, 2, 2), 0)
                    self.edit_mode = None
                else:  # a line was drawn interactively
                    self.drawing = append(self.drawing, self.drawn.reshape(-1, 2, 2), 0)
                if func:
                    func(self.drawing)
            if oneshot:
                self.accept_drawing()
        if func and not self.drawing_accepted:
            func(self.drawing)
        self.finish_drawing()
        return self.drawing

    def start_drawing(self, mode):
        """Start an interactive line drawing mode."""
        pf.debug("START DRAWING MODE", pf.DEBUG.GUI)
        self.mousehandler.set(LEFT, NONE, self.mouse_draw_line)
        self.mousehandler.set(RIGHT, NONE, self.emit_done)
        self.mousehandler.set(RIGHT, SHIFT, self.emit_cancel)
        self.mousehandler.setCursorShape('default')
        self.signals.DONE.connect(self.accept_drawing)
        self.signals.CANCEL.connect(self.cancel_drawing)
        self.drawing_mode = mode
        self.edit_mode = None
        self.drawing = empty((0, 2, 2), dtype=int)

    def wait_drawing(self):
        """Wait for the user to interactively draw a line."""
        self.drawing_timer = QtCore.QThread
        self.drawing_busy = True
        while self.drawing_busy:
            self.drawing_timer.msleep(20)
            pf.app.processEvents()

    def finish_drawing(self):
        """End an interactive drawing mode."""
        pf.debug("END DRAWING MODE", pf.DEBUG.GUI)
        self.mousehandler.reset(LEFT, NONE)
        self.mousehandler.reset(RIGHT, NONE)
        self.mousehandler.reset(RIGHT, SHIFT)
        self.mousehandler.setCursorShape('default')
        self.signals.DONE.disconnect(self.accept_drawing)
        self.signals.CANCEL.disconnect(self.cancel_drawing)
        self.drawing_mode = None

    def accept_drawing(self, clear=False):
        """Cancel an interactive drawing mode.

        If clear == True, the current drawing is cleared.
        """
        pf.debug("CANCEL DRAWING MODE", pf.DEBUG.GUI)
        self.drawing_accepted = True
        if clear:
            self.drawing = empty((0, 2, 2), dtype=int)
            self.drawing_accepted = False
        self.drawing_canceled = True
        self.drawing_busy = False

    def cancel_drawing(self):
        """Cancel an interactive drawing mode and clear the drawing."""
        self.accept_drawing(clear=True)

    def edit_drawing(self, mode):
        """Edit an interactive drawing."""
        self.edit_mode = mode
        self.drawing_busy = False


######## QtOpenGL interface ##############################

    def initializeGL(self):
        self.glinit()
        self.initCamera()
        self.resizeGL(self.width(), self.height())
        self.makeCurrent()
        #self.setCamera()

    def	resizeGL(self, w, h):
        self.setSize(w, h)

    def	paintGL(self):
        if not self.mode2D:
            self.display()

####### MOUSE EVENT HANDLERS ############################

    # Mouse functions can be bound to any of the mouse buttons
    # LEFT, MIDDLE or RIGHT.
    # Each mouse function should accept three possible actions:
    # PRESS, MOVE, RELEASE.
    # On a mouse button PRESS, the mouse screen position and the pressed
    # button are always saved in self.statex,self.statey,self.button.
    # The mouse function does not need to save these and can directly use
    # their values.
    # On a mouse button RELEASE, self.button is cleared, to avoid further
    # move actions.
    # ATTENTION! The y argument is positive upwards, as in normal OpenGL
    # operations!


    def dynarot(self, x, y, action):
        """Perform dynamic rotation operation.

        This function processes mouse button events controlling a dynamic
        rotation operation. The action is one of PRESS, MOVE or RELEASE.
        """
        if action == PRESS:
            w, h = self.getSize()
            self.state = [self.statex-w/2, self.statey-h/2]
            self.stated = length(self.state) < 0.35 * length([w, h])

        elif action == MOVE:
            w, h = self.getSize()
            # set all three rotations from mouse movement
            # tangential movement sets twist,
            # but only if initial vector is big enough
            x0 = self.state        # initial vector
            d = length(x0)
            x1 = [x-w/2, y-h/2]     # new vector
            if d > h/8:
                a0 = math.atan2(x0[0], x0[1])
                a1 = math.atan2(x1[0], x1[1])
                an = (a1-a0) / math.pi * 180
                ds = stuur(d, [-h/4, h/8, h/4], [-1, 0, 1], 2)
                twist = - an*ds
                self.camera.rotate(twist, 0., 0., 1.)
            self.state = x1
            # radial movement rotates around vector in lens plane
            x0 = [self.statex-w/2, self.statey-h/2]    # initial vector
            if x0 == [0., 0.]:
                x0 = [1., 0.]
            dx = [x-self.statex, y-self.statey]        # movement
            b = projection(dx, x0)
            if abs(b) > 5:  # only process when the movement is large enough
                if self.stated:  # mouse action did not start in the corners
                    val = stuur(b, [-2*h, 0, 2*h], [-180, 0, +180], 1)
                    rot =  [abs(val), -dx[1], dx[0], 0]
                    self.camera.rotate(*rot)
                self.statex, self.statey = (x, y)
            self.update()

        elif action == RELEASE:
            self.update()


    def dynapan(self, x, y, action):
        """Perform dynamic pan operation.

        This function processes mouse button events controlling a dynamic
        pan operation. The action is one of PRESS, MOVE or RELEASE.
        """
        if action == PRESS:
            pass

        elif action == MOVE:
            w, h = self.getSize()
            dx, dy = float(self.statex-x)/w, float(self.statey-y)/h
            self.camera.transArea(dx, dy)
            self.statex, self.statey = (x, y)
            self.update()

        elif action == RELEASE:
            self.update()


    def dynazoom(self, x, y, action):
        """Perform dynamic zoom operation.

        This function processes mouse button events controlling a dynamic
        zoom operation. The action is one of PRESS, MOVE or RELEASE.
        """
        if action == PRESS:
            self.state = [self.camera.dist, self.camera.area.tolist(), pf.cfg['gui/dynazoom']]

        elif action == MOVE:
            w, h = self.getSize()
            dx, dy = float(self.statex-x)/w, float(self.statey-y)/h
            for method, state, value, size in zip(self.state[2], [self.statex, self.statey], [x, y], [w, h]):
                if method == 'area':
                    d = float(state-value)/size
                    f = math.exp(4*d)
                    self.camera.zoomArea(f, area=np.asarray(self.state[1]).reshape(2, 2))
                elif method == 'dolly':
                    d = stuur(value, [0, state, size], [5, 1, 0.2], 1.2)
                    self.camera.dist = d*self.state[0]

            self.update()

        elif action == RELEASE:
            self.update()

    def wheel_zoom(self, delta):
        """Zoom by rotating a wheel over an angle delta"""
        f = 2**(delta/120.*pf.cfg['gui/wheelzoomfactor'])
        if pf.cfg['gui/wheelzoom'] == 'area':
            self.camera.zoomArea(f)
        elif pf.cfg['gui/wheelzoom'] == 'lens':
            self.camera.zoom(f)
        else:
            self.camera.dolly(f)
        self.update()

    def emit_done(self, x, y, action):
        """Emit a DONE event by clicking the mouse.

        This is equivalent to pressing the ENTER button."""
        if action == RELEASE:
            self.signals.DONE.emit()

    def emit_cancel(self, x, y, action):
        """Emit a CANCEL event by clicking the mouse.

        This is equivalent to pressing the ESC button."""
        if action == RELEASE:
            self.signals.CANCEL.emit()


    @classmethod
    def has_modifier(clas, e, mod):
        return (e.modifiers() & mod) == mod

    def mousePressEvent(self, e):
        """Process a mouse press event."""
        # Make the clicked viewport the current one
        pf.GUI.viewports.setCurrent(self)
        # on PRESS, always remember mouse position and button
        self.statex, self.statey = e.x(), self.height()-e.y()
        self.button = e.button()
        self.mod = e.modifiers() & ALLMODS
        func = self.mousehandler.get(self.button, self.mod)
        if func:
            func(self.statex, self.statey, PRESS)
        e.accept()

    def mouseMoveEvent(self, e):
        """Process a mouse move event."""
        # the MOVE event does not identify a button, use the saved one
        func = self.mousehandler.get(self.button, self.mod)
        if func:
            #print(f"{func=}")
            func(e.x(), self.height()-e.y(), MOVE)
        e.accept()

    def mouseReleaseEvent(self, e):
        """Process a mouse release event."""
        func = self.mousehandler.get(self.button, self.mod)
        self.button = None        # clear the stored button
        if func:
            func(e.x(), self.height()-e.y(), RELEASE)
        e.accept()


    def wheelEvent(self, e):
        """Process a wheel event."""
        func = self.wheel_zoom
        if func:
            func(e.delta())
        e.accept()


    # Any keypress with focus in the canvas generates a GUI WAKEUP signal.
    # This is used to break out of a wait status.
    # Events not handled here could also be handled by the toplevel
    # event handler.
    def keyPressEvent(self, e):
        # Make the clicked viewport the current one
        pf.GUI.signals.WAKEUP.emit()
        if e.key() == ESC:
            self.signals.CANCEL.emit()
            e.accept()
        elif e.key() == ENTER or e.key() == RETURN:
            self.signals.DONE.emit()
            e.accept()
        else:
            e.ignore()


# End
