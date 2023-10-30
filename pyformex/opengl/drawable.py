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
"""OpenGL rendering objects for the new OpenGL2 engine.

"""
import numpy as np
from numpy import int32, float32
from .gl import GL
from OpenGL.arrays.vbo import VBO

import pyformex as pf
from pyformex import utils
from pyformex import colors
from pyformex import geomtools as gt
from pyformex import arraytools as at
from pyformex.formex import Formex
from pyformex.mesh import Mesh
from pyformex.polygons import Polygons
from pyformex.attributes import Attributes
from pyformex.elements import ElementType
from .sanitize import saneFloat, saneLineStipple, saneColor, saneColorSet
from .texture import Texture


### Drawable Objects ###############################################

def size_report(s, a):
    print(f"{s}: size {a.size}; shape {a.shape}; type {a.dtype}")


def glObjType(nplex):
    if nplex <= 3:
        return [GL.GL_POINTS, GL.GL_LINES, GL.GL_TRIANGLES][nplex-1]
    else:
        # everything higher is a polygon, and it better be convex ;)
        return GL.GL_TRIANGLE_FAN

def _show_buffers(d):
    """Return a dict where the buffers are shown"""
    for key in ['vbo', 'nbo', 'ibo', 'tbo']:
        if key in d:
            d[key] = d[key].data


class Drawable(Attributes):
    """Base class for objects that can be rendered by the OpenGL engine.

    This is the basic drawable object in the pyFormex OpenGL rendering
    engine. It collects all the data that are needed to properly described
    any object to be rendered by the OpenGL shader programs.
    It has a multitude of optional attributes allowing it to describe
    many very different objects and rendering situations.

    This class is however not intended to be directly used to construct an
    object for rendering. The :class:`Actor` class and its multiple
    subclasses should be used for that purpose. The Actor classes provide
    an easier and more logical interface, and more powerful at the same time,
    since they can be compound: one Actor can hold multiple Drawables.

    The elementary objects that can be directly drawn by the shader programs
    are more simple, yet very diverse. The Drawable class collects all
    the data that are needed by the OpenGL engine to do a proper
    rendering of the object. It this represents a single, versatile
    interface of the Actor classes with the GPU shader programs.

    The versatility comes from the :class:`Attributes` base class, with
    an unlimited set of attributes. Any undefined attribute just returns
    None. Some of the most important attributes are described hereafter:

    - `rendertype`: int: the type of rendering process that will be applied
      by the rendering engine to the Drawable:

      0: A full 3D Actor. The Drawable will be rendered in full 3D with
         all active capabilities, such as camera rotation, projection,
         rendermode, lighting. The full object undergoes the camera
         transformations, and thus will appear as a 3D object in space.
         The object's vertices are defined in 3D world coordinates.
         Used in: :class:`Actor`.

      1: A 2D object (often a text or an image) inserted at a 3D position.
         The 2D object always keeps its orientation towards the camera.
         When the camera changes, the object can change its position on
         the viewport, but the oject itself looks the same.
         This can be used to add annotations to (parts of) a 3D object.
         The object is defined in viewport coordinates, the insertion
         points are in 3D world coordinates.
         Used in: :class:`textext.Text`.

      2: A 2D object inserted at a 2D position. Both object and position
         are defined in viewport coordinates. The object will take a fixed
         position on the viewport. This can be use to add decorations to
         the viewport (like color legends and background images).
         Used in: :class:`decors.ColorLegend`.

      3: Like 2, but with special purpose. These Drawables are not part of
         the user scene, but used for system purposes (like setting the
         background color, or adding an elastic rectangle during mouse picking).
         Used in: :meth:`Canvas.createBackground`.

      -1: Like 1, but with different insertion points for the multiple items
          in the object. Used to place a list of marks at a list of points.
          Used in: :class:`textext.Text`.

      -2: A 3D object inserted at a 2D position. The 3D object will rotate
          when the camera changes directions, but it will always be located
          on the same position of the viewport. This is normally used to
          display a helper object showing the global axis directions.
          Used in: :class:`decors.Triade`.


    The initialization of a Drawable takes a single parameter: `parent`,
    which is the Actor that created the Drawable. All other parameters
    should be keyword arguments, and are stored as attributes in the
    Drawable.

    Methods:

    - `prepare...`: creates sanitized and derived attributes/data. Its action
      depends on current canvas settings: mode, transparent, avgnormals

    - `render`: push values to shader and render the object:
      depends on canvas and renderer.

    - `pick`: fake render to be used during pick operations

    - `str`: format the full data set of the Drawable

    """

    # A list of acceptable attributes in the drawable
    # These are the parent attributes that can be overridden
    attributes = [
        'cullface', 'indices', 'color', 'name', 'highlight', 'opak',
        'linewidth', 'pointsize', 'lighting', 'offset', 'vbo', 'nbo', 'ibo',
        'alpha', 'drawface', 'objectColor', 'useObjectColor', 'rgbamode',
        'texture', 'texcoords', 'counts', 'indexptr',
        ]

    def __init__(self, parent, **kargs):
        """Create a new drawable."""
        super().__init__(parent, **kargs)

        # Default lighting parameter:
        # rendertype 0 (3D) follows canvas lighting
        # other rendertypes set lighting=False by default
        if self.rendertype != 0 and self.lighting is None:
            self.lighting = False

        self.prepareColor()
        #self.prepareNormals()  # The normals are currently always vertex
        self.prepareIndex()
        if self.texture is not None:
            self.prepareTexture()


    def prepareColor(self):
        """Prepare the colors for the shader."""
        #
        # TODO: This should be moved to Actor
        # OR NOT?
        # - color, colormap, bkcolor, bkcolormap are Actor attributes
        # - useObjectColor, object*Color, vertexColor are Drawable attributes
        # - the shader has objectCOlor and objectBkColor; alpha and bkalpha
        #   but only vertexColor, no vertexBkColor. If we add the latter
        #   we could always just draw 1 plane, not back and front
        self.useObjectColor = None
        self.objectColor = None
        self.vertexColor = None
        # print(f"DRAWABLE PREPARECOLOR {self.name} IN:"
        #       f"{self.color=}, {self.useObjectColor=}")
        if self.highlight:
            # we set single highlight color in shader
            # Currently do everything in Formex model
            # And we always need this one
            ###self.avbo = VBO(self.fcoords)
            self.useObjectColor = 1
            self.objectColor = np.array(colors.red)

        elif self.color is not None:
            if self.color.ndim == 1:
                # here we only accept a single color for front and back
                # different colors should have been handled before
                self.useObjectColor = 1
                self.vertexColor = None
                self.objectColor = self.color
            elif self.color.ndim == 3:
                self.useObjectColor = 0
                self.vertexColor = self.color
            else:
                raise ValueError(
                    "color should be an array with 1 or 3 dimensions")

            if self.vertexColor is not None:
                if self.alpha is None:
                    self.alpha = 0.5
                if self.vertexColor.shape[-1] == 3:
                    # Expand to 4 !!!
                    self.vertexColor = at.growAxis(self.vertexColor, 1,
                                                   fill=self.alpha)
                self.cbo = VBO(self.vertexColor.astype(float32))
                #size_report("Created cbo VBO", self.cbo)

                # print(f"{self.name=}, {self.useObjectColor=}, {self.objectColor=}")
                # print(f"{self.vertexColor=}")

        self.rgbamode = self.vertexColor is not None and self.vertexColor.shape[-1] == 4

        #  !!!!!!!!!!!!   Fix a bug with AMD cards   !!!!!!!!!!!!!!!
        #
        #  it turns out that some? AMD? cards do not like an unbound cbo
        #  even if that attribute is not used in the shader.
        #  Creating a dummy color buffer seems to solve that problem
        #
        if pf.options.fixcbo:
            if self.cbo is None:
                self.cbo = VBO(np.array(colors.red))


    # TODO: replace with changeColor?
    def changeVertexColor(self, color):
        """Change the vertex color buffer of the object.

        This is experimental!!!
        Just make sure that the passed data have the correct shape!
        """
        if self.useObjectColor:
            return
        self.vertexColor = self.color
        self.cbo = VBO(color.astype(float32))
        size_report('cbo', self.cbo)


    def prepareTexture(self):
        """Prepare texture and texture coords"""
        if self.useTexture == 1:
            if self.texcoords.ndim == 2:
                #curshape = self.texcoords.shape
                self.texcoords = at.multiplex(self.texcoords, self.object.nelems(), axis=-3, warn=False)
                #print("Multiplexing texture coords: %s -> %s " % (curshape, self.texcoords.shape))
        self.tbo = VBO(self.texcoords.astype(float32))
        self.texture.activate()


    def prepareIndex(self):
        """Create an index buffer to draw subelements

        This is always used for nplex > 3, but also to draw the edges
        for nplex=3.
        """
        if self.ibo is None and self.indices is not None:
            self.ibo = VBO(self.indices.astype(int32),
                           target=GL.GL_ELEMENT_ARRAY_BUFFER)


    def render(self, renderer):
        """Render the geometry of this object"""
        if self.offset:
            pf.debug("POLYGON OFFSET", pf.DEBUG.DRAW)
            GL.glPolygonOffset(1.0, 1.0)

        if self.linewidth:
            GL.glLineWidth(self.linewidth)

        renderer.shader.loadUniforms(self)

        if self.offset3d is not None:
            offset = renderer.camera.toNDC(self.offset3d)
            offset[..., 2] = 0.
            offset += (1., 1., 0.)
            if offset.shape == (3,):
                renderer.shader.uniformVec3('offset3', offset)
            elif offset.ndim > 1:
                self.obo = VBO(offset.astype(float32))
                self.obo.bind()
                i = renderer.shader.attribute['vertexOffset']
                GL.glEnableVertexAttribArray(i)
                GL.glVertexAttribPointer(i, 3, GL.GL_FLOAT, False, 0, self.obo)


        if self.rendertype == -2:
            # This is currently a special code for the Triade
            # It needs an object with coords in pixel values,
            # centered around the origin
            # and must have attributes x,y, set to the viewport
            # position of the (0,0,0) point after rotation.
            #
            rot = renderer.camera.modelview.rot
            x = np.dot(self.fcoords.reshape(-1, 3), rot).reshape(self.fcoords.shape)
            x[:, :, 0] += self.x
            x[:, :, 1] += self.y
            x[:, :, 2] = 0
            self.vbo = VBO(x)

        self.vbo.bind()
        i = renderer.shader.attribute['vertexCoords']
        GL.glEnableVertexAttribArray(i)
        GL.glVertexAttribPointer(i, 3, GL.GL_FLOAT, False, 0, self.vbo)

        if self.ibo:
            self.ibo.bind()

        if self.nbo:
            self.nbo.bind()
            i = renderer.shader.attribute['vertexNormal']
            GL.glEnableVertexAttribArray(i)
            GL.glVertexAttribPointer(i, 3, GL.GL_FLOAT, False, 0, self.nbo)

        if self.cbo:
            self.cbo.bind()
            i = renderer.shader.attribute['vertexColor']
            GL.glEnableVertexAttribArray(i)
            GL.glVertexAttribPointer(
                i, self.cbo.shape[-1], GL.GL_FLOAT, False, 0, self.cbo)

        if self.tbo:
            self.tbo.bind()
            i = renderer.shader.attribute['vertexTexturePos']
            GL.glEnableVertexAttribArray(i)
            GL.glVertexAttribPointer(i, 2, GL.GL_FLOAT, False, 0, self.tbo)

        if self.cullface == 'front':
            # Draw back faces
            GL.glEnable(GL.GL_CULL_FACE)
            GL.glCullFace(GL.GL_FRONT)
        elif self.cullface == 'back':
            # Draw front faces
            GL.glEnable(GL.GL_CULL_FACE)
            GL.glCullFace(GL.GL_BACK)
        else:
            GL.glDisable(GL.GL_CULL_FACE)

        # Specifiy the depth comparison function
        if self.ontop:
            GL.glDepthFunc(GL.GL_ALWAYS)

        # Bind the texture
        if self.texture:
            self.texture.bind()

        ### RENDER ###
        # Render the geometry
        if self.ibo is None:
            GL.glDrawArrays(
                self.glmode, 0, np.asarray(self.vbo.shape[:-1]).prod())
        else:
            if self.counts is not None and self.indexptr is not None:
               GL.glMultiDrawElements(
                    self.glmode, self.counts, GL.GL_UNSIGNED_INT,
                    self.indexptr, self.counts.shape[0])
            else:
                #GL.glDrawElementsui(self.glmode, self.ibo)
                # This is more general
                GL.glDrawElements(
                    self.glmode, self.ibo.data.size,  # not self.ibo.size !
                    # We do not pass the ibo because we already bind it.
                    GL.GL_UNSIGNED_INT, None) #self.ibo)

        # Cleanup
        if self.ibo:
            self.ibo.unbind()
        if self.obo:
            self.obo.unbind()
            GL.glDisableVertexAttribArray(renderer.shader.attribute['vertexOffset'])
        if self.cbo:
            self.cbo.unbind()
            GL.glDisableVertexAttribArray(renderer.shader.attribute['vertexColor'])
        if self.tbo:
            self.tbo.unbind()
            GL.glDisableVertexAttribArray(renderer.shader.attribute['vertexTexturePos'])
        if self.nbo:
            self.nbo.unbind()
            GL.glDisableVertexAttribArray(renderer.shader.attribute['vertexNormal'])
        self.vbo.unbind()
        GL.glDisableVertexAttribArray(renderer.shader.attribute['vertexCoords'])
        if self.offset:
            GL.glPolygonOffset(0.0, 0.0)


    def renderpick(self, renderer):
        """Render for picking"""
        renderer.shader.loadUniforms(self)

        self.vbo.bind()
        i = renderer.shader.attribute['vertexCoords']
        GL.glEnableVertexAttribArray(i)
        GL.glVertexAttribPointer(i, 3, GL.GL_FLOAT, False, 0, self.vbo)

        if self.ibo:
            self.ibo.bind()

        if self.pbo:   # we may also add drawables without pick buffers
            self.pbo.bind()
            i = renderer.shader.attribute['pickColor']
            i = GL.glGetAttribLocation(renderer.shader.shader, 'pickColor')
            GL.glEnableVertexAttribArray(i)
            if self.pbo.data.dtype == np.float32:
                GL.glVertexAttribPointer(
                    i, 4, GL.GL_FLOAT, False, 0, self.pbo)
            else:
                GL.glVertexAttribPointer(
                    i, 4, GL.GL_UNSIGNED_BYTE, False, 0, self.pbo)

        if self.cullface == 'front':
            # Draw back faces
            GL.glEnable(GL.GL_CULL_FACE)
            GL.glCullFace(GL.GL_FRONT)
        elif self.cullface == 'back':
            # Draw front faces
            GL.glEnable(GL.GL_CULL_FACE)
            GL.glCullFace(GL.GL_BACK)
        else:
            GL.glDisable(GL.GL_CULL_FACE)

        # Specifiy the depth comparison function
        if self.ontop:
            GL.glDepthFunc(GL.GL_ALWAYS)

        # Simulate rendering
        if self.ibo is None:
            GL.glDrawArrays(
                self.glmode, 0, np.asarray(self.vbo.shape[:-1]).prod())
        else:
            if self.counts is not None and self.indexptr is not None:
                GL.glMultiDrawElements(
                    self.glmode, self.counts, GL.GL_UNSIGNED_INT,
                    self.indexptr, self.counts.shape[0])
            else:
                GL.glDrawElements(
                    self.glmode, self.ibo.data.size,  # not self.ibo.size !
                    # We do not pass the ibo because we already bind it.
                    GL.GL_UNSIGNED_INT, None) #self.ibo)

        # Cleanup
        if self.ibo:
            self.ibo.unbind()
        if self.pbo:
            self.pbo.unbind()
        GL.glDisableVertexAttribArray(renderer.shader.attribute['pickColor'])
        self.vbo.unbind()
        GL.glDisableVertexAttribArray(renderer.shader.attribute['vertexCoords'])


    def report(self):
        keys = sorted(set(self.keys()) - set(('_default_dict_',)))
        d = utils.selectDict(self, keys)
        _show_buffers(d)
        return utils.formatDict(d)


########################################################################

class BaseActor(Attributes):
    """Base class for all drawn objects (Actors) in pyFormex.

    This defines the interface for all drawn objects, but does not
    implement any drawn objects.
    Drawable objects should be instantiated from the derived classes.
    Currently, we have the following derived classes:

    Actor: a 3-D object positioned and oriented in the 3D scene. Defined
           in actors.py.
    Mark: an object positioned in 3D scene but not undergoing the camera
          axis rotations and translations. It will always appear the same
          to the viewer, but will move over the screen according to its
          3D position. Defined in marks.py.
    Decor: an object drawn in 2D viewport coordinates. It will unchangeably
           stick on the viewport until removed. Defined in decors.py.

    The BaseActor class is just an Attributes dict storing all the rendering
    parameters, and providing defaults from the current canvas drawoptions
    for the essential parameters that are not specified.

    Additional parameters can be set at init time or later using the
    update method. The specified parameters are sanitized before being
    stored.

    Arguments processed by the base class:

    - `marksize`: force to float and also copied as `pointsize`

    """

    def __init__(self, **kargs):
        """Initialize the BaseActor class."""
        # TODO: Check if we can make pf.canvas.drawoptions a Dict
        # (and thus a default_factory)
        Attributes.__init__(self, pf.canvas.drawoptions if pf.canvas else {})
        if kargs:
            self.update(**kargs)
            self.setLineWidth(self.linewidth)
            self.setLineStipple(self.linestipple)
            self.setColor(self.color, self.colormap)
            self.setTexture(self.texture)

    __repr__ = object.__repr__

    def __eq__(self, x):
        """Compare BaseActor class instances

        Because the BaseActor is dict which may contain very
        different and large objects, comparison on all attributes
        being equal would be very demanding (and possibly failing
        in case of numpy arrays.)
        Also, these objects should be unique representing objects
        of OpenGL drawables. They are cosntructed once, stored,
        and deleted, but not processed otherwise.
        The reason for comparison is merely to be able to test
        if they are in a given list of actors.
        Therefore we compare BaseActors purely on them being
        exactly the object, by id, without a need of comparing
        the contents.
        """
        return self is x


    def setLineWidth(self, linewidth):
        """Set the linewidth of the Drawable."""
        self.linewidth = saneFloat(linewidth)

    def setLineStipple(self, linestipple):
        """Set the linewidth of the Drawable."""
        self.linestipple = saneLineStipple(linestipple)

    def setColor(self, color=None, colormap=None, ncolors=1):
        """Set the (single) color of the BaseActor."""
        self.color, self.colormap = saneColorSet(color, colormap, shape=(ncolors,))

    def setTexture(self, texture):
        """Set the texture data of the Drawable."""
        if texture is not None:
            if not isinstance(texture, Texture):
                try:
                    texture = Texture(texture)
                except Exception:
                    texture = None
        self.texture = texture


########################################################################

class Actor(BaseActor):
    """Proposal for drawn objects

    __init__:  store all static values: attributes, geometry, vbo's
    prepare: creates sanitized and derived attributes/data
    render: push values to shader and render the object

    __init__ is only dependent on input attributes and geometry

    prepare may depend on current canvas settings:
      mode, transparent, avgnormals

    render depends on canvas and renderer

    If the actor does not have a name, it will be given a
    default one.

    The actor has the following attributes, initialized or computed on demand

    """
    # default names for the actors
    defaultname = utils.NameSequence('object_0')

    def __init__(self, obj, **kargs):

        BaseActor.__init__(self)

        self._memory = {}

        # Check it is something we can draw
        if not isinstance(obj, (Mesh, Formex, Polygons)):
            raise ValueError(
                f"Object is of type {type(obj)}. Can only render Mesh, Formex,"
                " Polygons and objects that can be converted to Formex")
        self.object = obj

        if isinstance(obj, Mesh):
            coords = obj.coords.astype(float32)
            elems = obj.elems.astype(int32)
            eltype = obj.eltype

        elif isinstance(obj, Polygons):
            coords = obj.coords.astype(float32)
            elems = obj.elems.data.astype(int32)
            eltype = 'polygon'

        elif isinstance(obj, Formex):
            coords = obj.coords.astype(float32)
            elems = None
            eltype = obj.eltype
            if eltype is None:
                # We need an eltype for drawing
                if obj.nplex() <= 4:
                    # Set default eltype
                    eltype = ElementType.default[obj.nplex()]
                else:
                    # Consider it a polygon
                    eltype = ElementType.polygon(obj.nplex())

        try:
            self.eltype = ElementType.get(eltype)
        except:
            self.eltype = eltype

        # Store minimal data and remember available data
        if elems is None:
            self.fcoords = coords
        else:
            self.fcoords = coords[elems]
            self._memory['coords'] = coords.reshape(-1, 3)
            self._memory['elems'] = elems

        self.drawable = []
        self._pickitems = None
        self.children = []

        # By default, Actors are pickable
        self.pickable = True

        # Acknowledge all object attributes and passed parameters
        self.update(obj.attrib)
        self.update(kargs)
        if self.rendertype is None:
            self.rendertype = 0

        # copy marksize as pointsize for gl2 shader
        if 'marksize' in self:
            self['pointsize'] = self['marksize']

        if self.name is None:
            self.name = next(Actor.defaultname)

        # Currently do everything in Formex model
        # And we always need this one
        self.vbo = VBO(self.fcoords)
        #print(f"vbo shape is {self.vbo.shape}")


    def getType(self):
        return self.object.__class__


    def _fcoords_fuse(self):
        coords, elems = self.fcoords.fuse()
        if elems.ndim != 2:
            elems = elems[:, np.newaxis]
        self._memory['coords'] = coords
        self._memory['elems'] = elems
        return coords, elems


    @property
    @utils.memoize
    def coords(self):
        """Return the fused coordinates of the object"""
        return self._fcoords_fuse()[0]


    @property
    @utils.memoize
    def elems(self):
        """Return the original elems of the object"""
        return self._fcoords_fuse()[1]


    def bbox(self):
        try:
            return self.object.bbox()
        except Exception as e:
            raise e
            return np.zeros(6).reshape(2, 3)


    @property
    def ndim(self):
        """Return the dimensionality of the object."""
        return self.object.level()


    @property
    def b_normals(self):
        """Return individual normals at all vertices of all elements"""
        if self.object.eltype == 'polygon':
            return self.object.vnormals
        if self._normals is None:
            self._normals = gt.polygonNormals(self.fcoords.astype(float32))
            #print(f"COMPUTED NORMALS for {self.name}: {self._normals.shape}")
            #print(self._normals)
        return self._normals


    @property
    def b_avgnormals(self):
        """Return averaged normals at the vertices"""
        if self.object.eltype == 'polygon':
            return self.object.fanormals
        if self._avgnormals is None:
            tol = pf.cfg['render/avgnormaltreshold']
            self._avgnormals = gt.polygonAvgNormals(
                self.coords, self.elems,
                atnodes=False, treshold=tol).astype(float32)
            #print(f"COMPUTED AVGNORMALS for {self.name}: {self._avgnormals.shape}")
            #print(self._avgnormals)
        return self._avgnormals


    def changeColor(self, color=None, colormap=None, bkcolor=None, bkcolormap=None):
        """Change the colors of an actor.

        Changes the specified non-None values and repaints the actor accordingly.
        Note: you can not set a value to None using this method. Set the
        attribute directly and then call changeColor. For example, to remove
        the back color, do::

            actor.bkcolor = None
            actor.changeColor()

        To repaint an actor with the current objects's prop values, do::

            actor.changeColor(color='prop')
        """
        self.prepareColor()
        for d in self.drawable:
             d.prepareColor()
        pf.canvas.update()


    def prepareColor(self):
        # Implement the default color='prop' if no color is set and
        # the object has props
        if self.color is None and hasattr(self.object, 'prop'):
            self.color = 'prop'
        if self.color is not None:
            self.color = self.okColor(self.color, self.colormap)
        #     print(f"OK COLOR SHAPE: {self.color.shape}")
        # print(f"OK COLOR: {self.color.shape}, {self.colormap}")
        if self.bkcolor is not None:
            self.bkcolor = self.okColor(self.bkcolor, self.bkcolormap)
        ##print("ok bkcolor", self.bkcolor)
        self.useObjectColor = None
        if self.color is not None:
            if self.color.ndim == 1:
                self.useObjectColor = 1
                self.objectColor = self.color
                self.color = None
                if self.bkcolor is not None and self.bkcolor.ndim == 1:
                    self.useObjectColor = 2
                    self.objectBkColor = self.bkcolor
                    self.bkcolor = None
        # print(f"PREPARED COLOR {self.useObjectColor=}")
        # if hasattr(self.color, 'shape'):
        #     print(f"{self.color.shape=}")
        # else:
        #     print(f"{self.color=}")

    def prepare(self, canvas):
        """Prepare the attributes for the renderer.

        This sanitizes and completes the attributes for the renderer.
        Since the attributes may be dependent on the rendering mode,
        this method is called on each mode change.
        """
        #print(f"PREPARE {self.name}")
        self.prepareColor()
        self.setAlpha(self.alpha, self.bkalpha)
        self.setTexture(self.texture, self.texcoords, self.texmode)
        self.setLineWidth(self.linewidth)
        self.setLineStipple(self.linestipple)

        #### CHILDREN ####
        for child in self.children:
            child.prepare(canvas)


    def changeMode(self, canvas):
        """Modify the actor according to the specified mode"""
        #print("CHANGEMODE")
        #pf.debug("GEOMACTOR.changeMode", pf.DEBUG.DRAW)
        self.drawable = []
        #print(f"NDIM {self.ndim}")
        if self.ndim >= 2:
            self._prepareNormals(canvas)
            if self.mode:
                rendermode = self.mode
            else:
                rendermode = canvas.rendermode
            if rendermode == 'wireframe':
                # Draw the colored edges
                if self.edges is not None:
                    self._addLinesPoints(self.edges)
            else:
                # Draw the colored faces
                self._addFaces()
                # Overlay the black edges (or not)
                if rendermode.endswith('wire'):
                    #print("ADDWIRES")
                    self._addWires(self.edges)
        else:
            # Lines or points
            #print("FACES", self.faces)
            self._addLinesPoints(self.faces)

        #### CHILDREN ####
        for child in self.children:
            child.changeMode(canvas)

        pf.debug("GEOMACTOR.changeMode create %s drawables" % len(self.drawable), pf.DEBUG.DRAW)


    def _prepareNormals(self, canvas):
        """Prepare the normals buffer object for the actor.

        The normals buffer object depends on the renderer settings:
        lighting, avgnormals
        """
        #if renderer.canvas.settings.lighting:
        if True:
            if canvas.settings.avgnormals:
                normals = self.b_avgnormals
            else:
                normals = self.b_normals
            # Normals are always full fcoords size
            #print("SIZE OF NORMALS: %s; COORDS: %s" % (normals.size,self.fcoords.size))
            self.nbo = VBO(normals)


    def fullElems(self):
        """Return an elems index for the full coords set"""
        nelems, nplex = self.fcoords.shape[:2]
        return np.arange(nelems*nplex, dtype=int32).reshape(nelems, nplex)


    def subElems(self, nsel=None, esel=None):
        """Create indices for the drawable subelems

        This indices always refers to the full coords (fcoords).

        The esel selects the elements to be used (default all).

        The nsel selects (possibly multiple) parts from each element.
        The selector is 2D (nsubelems, nsubplex). It is applied on all
        selected elements

        If both esel and esel are None, returns None
        """
        if (nsel is None or len(nsel)==0) and (esel is None or len(esel)==0):
            return None
        else:
            # The elems index defining the original elements
            # based on the full fcoords
            elems = self.fullElems()
            if esel is not None:
                elems = elems[esel]
            if nsel is not None:
                elems = elems[:, nsel].reshape(-1, nsel.shape[-1])
            return elems


    @property
    @utils.memoize
    def faces(self):
        """Return the faces of the object as they will be drawn

        Returns a dict with parameters for the Drawable
        """
        if isinstance(self.eltype, ElementType):
            elems = self.subElems(nsel=self.eltype.getDrawFaces())
            if elems is None:
                # draw without index buffer (points, lines, triangles in order)
                nplex = self.eltype.nplex
                res = { 'glmode': glObjType(nplex) }
            else:
                nelems, nplex = elems.shape
                if nplex <= 3:
                    # draw triangles, lines, points with index
                    res = {
                        'indices': elems,
                        'glmode': glObjType(nplex),
                    }
                else:
                    # draw polygon Mesh
                    res = {
                        'indices': elems,
                        'glmode': GL.GL_TRIANGLE_FAN,
                        'counts': np.full((nelems,), nplex, dtype=np.int32),
                        'indexptr': np.arange(0, 4*nelems*nplex, 4*nplex,
                                              dtype=np.int32),
                        }
        elif self.eltype == 'polygon':
            # draw Polygons
            obj = self.object
            res = {
                'indices': np.arange(obj.elems.size, dtype=np.int32),
                'glmode': GL.GL_TRIANGLE_FAN,
                'counts': obj.elems.lengths.astype(int32),
                'indexptr': (4 * obj.elems.ind[:-1]).astype(int32),
                }
        else:
            raise pf.ImplementationError("This shouldn't happen")
        #print(f"FACES MULTIPLEX {self.multiplex}")
        return res


    def selectedFaces(self, esel):
        """Return selected faces of the object as they will be drawn

        This is like faces but only containing some elements.
        """
        if isinstance(self.eltype, ElementType):
            elems = self.subElems(nsel=self.eltype.getDrawFaces(), esel=esel)
            if elems is None:
                # draw without index buffer (points, lines, triangles in order)
                nplex = self.eltype.nplex
                res = { 'glmode': glObjType(nplex) }
            else:
                nelems, nplex = elems.shape
                if nplex <= 3:
                    # draw triangles, lines, points with index
                    res = {
                        'indices': elems,
                        'glmode': glObjType(nplex),
                    }
                else:
                    # draw polygon Mesh
                    res = {
                        'indices': elems,
                        'glmode': GL.GL_TRIANGLE_FAN,
                        'counts': np.full((nelems,), nplex, dtype=np.int32),
                        'indexptr': np.arange(0, 4*nelems*nplex, 4*nplex,
                                              dtype=np.int32),
                        }
        elif self.eltype == 'polygon':
            # draw Polygons
            obj = self.object
            res = {
                'indices': np.arange(obj.elems.size, dtype=np.int32),
                'glmode': GL.GL_TRIANGLE_FAN,
                'counts': obj.elems.lengths.astype(int32),
                'indexptr': (4 * obj.elems.ind[:-1]).astype(int32),
                }
        else:
            raise pf.ImplementationError("This shouldn't happen")
        #print(f"FACES COMPUTED RESULT {res}")
        return res


    @property
    @utils.memoize
    def edges(self):
        """Return the edges of the object as they will be drawn

        This returns a 2D index in a single element. All elements
        should have compatible node numberings.
        """
        if isinstance(self.eltype, ElementType):
            elems = self.subElems(nsel=self.eltype.getDrawEdges())
        elif self.eltype == 'polygon':
            face_ind = self.object.elems.__class__(self.faces['indices'],
                              ind=self.object.elems.ind)
            #print("FACE_IND", face_ind)
            edge_sel = [self.object.__class__.edgeSelector(l)
                for l in self.object.elems.lengths]
            #print("EDGE_SEL", edge_sel)
            elems = np.row_stack([f[i] for f, i in zip(face_ind, edge_sel)])
            #print("EDGES", elems)
        else:
            raise pf.ImplementationError("This shouldn't happen")
        #print(f"EDGES SHAPE: {elems.shape}")
        return {
            'indices': elems.astype(np.int32),
            'glmode': GL.GL_LINES if elems.shape[-1] == 2 else GL.GL_POINTS,
            }


    def _translate_mesh_points_formex(self, ids):
        """Convert Mesh node numbers back to Formex point numbers

        During pixel point picking, we draw the fused Formex points.
        Afterwards, this function is called to translate the picked
        point numbers back to Formex point numbers.
        """
        nitems = self.coords.shape[0]
        trl = np.zeros(nitems, dtype=at.Int)
        trl[ids] = 1
        out = trl[self.elems]
        w = at.where_nd(out)
        nplex = self.elems.shape[1]
        ids = w[0] * nplex + w[1]
        return ids


    def _add_pick(self, start, mode):
        """Add drawables for picking

        Picking (parts of) an actor is done by rendering the parts of the actor
        offscreen with a unique color in a flat opak mode, and identifying the
        parts by their pixel color. All parts of all objects thus need a unique
        integer identifier in order to be recognized.

        Parameters
        ----------
        start: int
            First id value usable for this actor. This means that no higher
            value is used yet by other actors.
        mode: str
            Identifies which parts of the actor should be pickable.

            - 'point': add pickable points and opak elements (hiding points)
            - 'point0': add pickable points only
            - anything else: add pickable elements

            TODO: pickable edges, pickable faces

        Returns
        -------
        next_start: int
            The next available identifier. This means that all ids used
            by this actor are in ``range(start, next_start)``.
        """
        if mode in ['point', 'point0']:
            points = self.coords
            nitems = points.shape[0]
            next_start = start + nitems
            color = np.arange(start, next_start, dtype=np.uint32)
            color8 = color.view(np.uint8).reshape(-1, 4)
            if pf.debugon(pf.DEBUG.PICK):
                print("PICKCOLORS\n", color8)
            color8f = (color8 / 255).astype(np.float32)
            D0 = Drawable(
                self, vbo=VBO(self.coords), name=self.name+"_pick", picking=True,
                indices=np.arange(nitems).reshape(-1, 1), glmode=GL.GL_POINTS,
                lighting=False, opak=True, pointsize=10, pbo=VBO(color8f),
                color=None)
            self._pickitems = D0
            if mode == 'point':
                D1 = Drawable(   # make faces opak
                    self, name=self.name+"_pick0", picking=True, lighting=False,
                    color=np.array(colors.black), alpha=1.0,
                    opak=True, cullface='', drawface=0, **self.faces)
                self._pickitems = [D0, D1]
        else:
            faces = self.faces
            nelems = self.fcoords.shape[0]
            next_start = start + nelems
            color = np.arange(start, next_start, dtype=np.uint32)
            if self.eltype == 'polygon':
                shape = (self.object.nelems(), 1)
            else:
                shape = self.fcoords.shape[:2]
            color8 = color.view(np.uint8).reshape(-1, 4)
            if pf.debugon(pf.DEBUG.PICK):
                print("PICKCOLORS\n", color8)
            color8 = at.multiplex(color8, shape[1], 1).reshape(-1, 4)
            color8f = (color8 / 255).astype(np.float32)
            self._pickitems = Drawable(
                self, name=self.name+"_pick", picking=True, lighting=False,
                pbo = VBO(color8f), color=None,
                cullface='', drawface=0, **faces)
        return next_start


    def _addFaces(self):
        """Draw the elems which are triangles or polygons"""
        faces = self.faces

        if self.rendertype > 1 or self.drawface == 0:
            # Draw front and back at once, without culling
            # Beware: this does not work with different front/back color
            # as our Drawable currently has only one color
            D = Drawable(self, name=self.name,
                         cullface='', drawface=0, **faces)
            self.drawable.append(D)
        else:
            # Draw both back and front sides, with culling
            # First the front sides (they hide anything behind)
            D = Drawable(self, name=self.name+"_front",
                         cullface='back', drawface=1, **faces)
            self.drawable.append(D)
            # Then the front sides, using same ibo and indexptr
            D = Drawable(self, name=self.name+"_back",
                         cullface='front', drawface=-1, **faces,
                         ibo = D.ibo, # Add in same ibo to avoid copy
                         )
            self.drawable.append(D)


    def _addLinesPoints(self, elems):
        """Draw lines or points"""
        #print("ADDLINESPOINTS",elems)
        # if elems is None:
        #     nplex = self.object.nplex()
        # else:
        #     nplex = elems.shape[1]
        # glmode = glObjType(nplex)
        if elems is not None:
            D = Drawable(self, name=self.name+"_faces",
                         **elems,
                         lighting=False)
            self.drawable.append(D)


    def _addWires(self, elems):
        """Add or remove the edges depending on rendering mode"""
        wiremode = pf.canvas.settings.wiremode
        if wiremode > 0 and self.edges is not None:
            if wiremode == 1:
                # all edges:
                #print("ADDWIRES %s" % elems)
                pass
            elif wiremode == 2:
                # border edges
                inv = at.inverseIndex(self.elems.reshape(-1, 1))[:, -1]
                M = Mesh(self.coords, self.elems)
                elems = M.getFreeEntities(level=1)
                elems = inv[elems]
            elif wiremode == 3:
                # feature edges
                print("FEATURE EDGES NOT YET IMPLEMENTED")
                elems = None

        if elems is not None and elems['indices'].size > 0:
            #print("ADDWIRES SIZE %s" % (elems['indices'].shape,))
            #print(f"ELEMS {elems}")
            #print(f"EDGES {self.edges}")
            D = Drawable(self, name=self.name+"_wires",
                         **self.edges,
                         lighting=False, color=saneColor(colors.black),
                         opak=True)
            # Put at the front to make visible
            # ontop will not help, because we only sort actors
            self.drawable.insert(0, D)


    def highlighted(self):
        """Return True if the Actor is highlighted.

        The highlight can be full (self.highlight=1) or partial
        (self._highlight is not None).
        """
        return self.highlight == 1 or self._highlight is not None


    def removeHighlight(self):
        """Remove the highlight for the current actor.

        Remove the highlight (whether full or partial) from the actor.
        """
        self.highlight = 0  # Full highlight
        if self._highlight:   # Partial highlight
            if self._highlight in self.drawable:
                self.drawable.remove(self._highlight)
            self._highlight = None


    def setHighlight(self):
        """Add full highlighting of the actor.

        This makes the whole actor being drawn in the highlight color.
        """
        self.highlight = 1


    def addHighlightElements(self, sel=None):
        """Add a highlight for the selected elements. Default is all."""
        self.removeHighlight()
        faces = self.selectedFaces(sel)
        self._highlight = Drawable(
            self, name=self.name+"_highlight", **faces,
            linewidth=10, lighting=False, highlight=True, opak=True)
        # Put at the front to make visible
        self.drawable.insert(0, self._highlight)


    def addHighlightPoints(self, sel=None):
        """Add a highlight for the selected points. Default is all."""
        self.removeHighlight()
        vbo = VBO(self.object.points())
        self._highlight = Drawable(
            self, name=self.name+"_highlight",
            vbo=vbo, indices=sel.reshape(-1, 1), glmode=GL.GL_POINTS,
            lighting=False, highlight=True, opak=True,
            pointsize=10, offset=0.05*self.object.points().dsize())
        # Put at the front to make visible
        self.drawable.insert(0, self._highlight)


    def okColor(self, color, colormap=None):
        """Compute a color usable by the shader.

        The shader (currently) only supports 3*float type of colors:

        - None
        - single color (separate for front and back faces)
        - vertex colors
        """
        if isinstance(color, str):
            if color == 'prop' and hasattr(self.object, 'prop'):
                color = self.object.prop
            elif color == 'random':
                # create random colors
                color = np.random.rand(self.object.nelems(), 3)
            elif color.startswith('fld:'):
                # get colors from a named field
                fld = self.object.getField(color[4:])
                if fld:
                    color = fld.convert('elemn').data
                    colormap = None
                else:
                    pf.warning("Could not set color from field %s" % color)

        if self.eltype == 'polygon':
            shape = (self.object.nelems(), 1)
            #print(color, shape)
        else:
            shape = self.fcoords.shape[:2]
        #print(f"FCOORDS SHAPE {self.fcoords.shape}")
        #print(f"BEFORE SANITIZING {np.asarray(color).shape}, {shape}")
        color, colormap = saneColorSet(color, colormap, shape=shape)
        #print(f"AFTER SANITIZING: {color.shape}")
        if color is not None:
            if self.eltype == 'polygon':
                #print(f"color is {color}")
                if color.ndim > 1:
                    #print(f"MULTIPLEXING POLYGONS COLOR FROM {color.shape}")
                    color = np.repeat(color, self.object.elems.lengths, axis=0)
                    #print(f"MULTIPLEXED COLOR TO {color.shape}")
                    #print(color)
            if color.dtype.kind == 'i':
                # We have a color index
                if colormap is None:
                    colormap = np.array(colors.palette)
                color = colormap[color]

        ##print("final color", color)
        return color


    def setAlpha(self, alpha, bkalpha=None):
        """Set the Actors alpha value."""
        try:
            self.alpha = self.bkalpha = float(alpha)
        except Exception:
            del self.alpha
            del self.bkalpha
        try:
            self.bkalpha = float(bkalpha)
        except Exception:
            pass
        if self.opak is None:
            self.opak = (self.alpha == 1.0) and (self.bkalpha == 1.0)


    def setTexture(self, texture, texcoords=None, texmode=None):
        """Set the texture data of the Drawable."""
        self.useTexture = 0
        if texture is not None:
            if not isinstance(texture, Texture):
                try:
                    texture = Texture(texture)
                except Exception:
                    print("Error while creating Texture from %s" % type(texture))
                    raise
                    texture = None
            if texture is not None:
                if texcoords is None:
                    if isinstance(self.eltype, ElementType) and (
                            self.eltype.ndim == 2):
                        texcoords = np.array(self.eltype.vertices[..., :2])
                    else:
                        print("Texture not allowed for eltype %s" % self.eltype)
                        self.texture = self.texcoords = None
                        return
                if not isinstance(self.eltype, ElementType):
                    raise ValueError(
                        f"Can not yet use texture with eltype {self.eltype}")
                if texcoords.shape[-2:] != (self.eltype.nplex, 2):
                    print(self.eltype.nplex)
                    print("Shape of texcoords does not match: %s" % str(texcoords.shape))
                    texcoords = texture = None
            if texmode is None:
                texmode = 1

        if texture is not None:
            # everything ok, store the texture params
            self.useTexture = 1
            self.texture = texture
            self.texcoords = texcoords
            self.texmode = texmode


    ## def setLineWidth(self, linewidth):
    ##     """Set the linewidth of the Drawable."""
    ##     self.linewidth = saneLineWidth(linewidth)


    ## def setLineStipple(self, linestipple):
    ##     """Set the linewidth of the Drawable."""
    ##     self.linestipple = saneLineStipple(linestipple)


    def render(self, renderer):
        """Render the geometry of this object"""

        ## if self.modified:
        ##     print("LOAD GEOMACTOR uniforms")
        ##     renderer.shader.loadUniforms(self)
        ##     self.modified = False

        if self.invisible:
            return
        for obj in self.drawable:
            renderer.setDefaults()
            renderer.shader.loadUniforms(self)
            obj.render(renderer)
        for obj in self.children:
            renderer.setDefaults()
            obj.render(renderer)


    def renderpick(self, renderer):
        """Render the geometry of this object"""
        if self.invisible:
            return
        if self._pickitems:
            if isinstance(self._pickitems, list):
                for picki in self._pickitems:
                    picki.renderpick(renderer)
            else:
                self._pickitems.renderpick(renderer)
        for obj in self.children:
            obj.renderpick(renderer)


    def inside(self, camera, rect=None, mode='actor', sel='any',
               return_depth=False):
        """Test whether the actor is rendered inside rect of camera.

        Parameters
        ----------
        camera: Camera
            A properly initialized Camera. Usually it will be the current
            canvas camera (``pf.canvas.camera``).
        rect: tuple[int], optional
            A tuple (x,y,w,h) specifying a rectangular subregion of the
            camera's viewport. (x,y) is the lower left angle, (w,h) are
            the width and height, all in pixels. If not provided
            the full camera viewport is used.
        mode: str
            The testing mode. Currently one of:

            - 'actor' (default): test if the actor is (partly) inside
            - 'element': test which elements of the actor are inside
            - 'point': test which vertices of the actor are inside

        sel: str
            One of 'all' or 'any'. This is not used with 'point' mode.
            For the other modes it specifies whether all or any of the
            points of the actor or element should be inside the rectangle
            in order to be flagged as a positive.
        return_depth: bool
            If True, also returns the z-depth of the objects that are found
            inside the rectangle. The z-depth is the closest distance of the
            object to the camera.

        Returns
        -------
        inside: bool | int array
            In 'actor' mode, returns True if the Actor is inside the rectangle,
            or False otherwise. If 'element' and 'point' mode, returns
            an array  with the indices of the actor's elements or points that
            are inside the rectangle.
        depth: float array
            The z-depth of the objects inside the rectangle. Only returned
            if `return_depth` is True.
        """
        ins = camera.inside(self.object.points(), rect, return_depth)
        if return_depth:
            ins, depth = ins

        if mode == 'point':
            ok = np.where(ins)[0]
            if return_depth:
                depth = depth[ok]

        else:
            if mode in ['element', 'actor']:
                if isinstance(self.object, Mesh):
                    elems = self.elems
                elif isinstance(self.object, Formex):
                    elems = self.fullElems()
                else:
                    raise ValueError(
                        f"Element picking on objects of type {type(self.object)}"
                        f"is not implemented")

            elif mode == 'edge':
                # TODO: add edges selector
                #elems =
                raise ValueError("Edge picking is not implemented yet")

            ins = ins[elems]
            if sel == 'all':
                ok = ins.all(axis=-1)
            elif sel == 'any':
                ok = ins.any(axis=-1)
            else:
                # Useful?
                ok = ins[:, sel].all(axis=-1)

            if mode == 'actor':
                ok = ok.any()
                if return_depth:
                    depth =  depth[np.unique(elems)].min()

            else:
                ok = np.where(ok)[0]
                elems = elems[ok]
                if return_depth:
                    depth = depth[elems].min(axis=-1)

        if return_depth:
            return ok, depth
        else:
            return ok


    def report(self):
        keys = sorted(set(self.keys()) - set(('drawable',)))
        d = utils.selectDict(self, keys)
        _show_buffers(d)
        s = utils.formatDict(d)
        for i, d in enumerate(self.drawable):
            s += "\n** Drawable %s **\n" % i
            s += d.report()
        return s


########################################################################

# TODO: these should be moved to polysurface

def polygonFaceIndex(n):
    """Return a selector to get triangle fan elements from polygon

    Examples
    --------
    >>> polygonFaceIndex(5)
    array([[0, 1, 2],
           [0, 2, 3],
           [0, 3, 4]])
    """
    i0 = np.zeros(n-2, dtype=at.Int)
    i1 = np.arange(1, n-1, dtype=at.Int)
    i2 = i1+1
    return np.column_stack([i0, i1, i2])


def polygonEdgeIndex(n):
    """Return a selector to get edge elements from polygon

    Examples
    --------
    >>> polygonEdgeIndex(5)
    array([[0, 1],
           [1, 2],
           [2, 3],
           [3, 4],
           [4, 0]])
    """
    i0 = np.arange(n)
    i1 = np.roll(i0, -1)
    return np.column_stack([i0, i1])


### End
