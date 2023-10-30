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
"""opengl/renderer.py

Python OpenGL framework for pyFormex

This OpenGL framework is intended to replace (in due time)
the current OpenGL framework in pyFormex.

(C) 2013 Benedict Verhegghe and the pyFormex project.

"""
import numpy as np

import pyformex as pf
from pyformex.attributes import Attributes
from .matrix import Matrix4
from .camera import orthogonal_matrix
from .gl import GL

if not pf.sphinx and pf.options.gl3:
    from opengl3.shader import Shader
else:
    from .shader import Shader


class Renderer():

    def __init__(self, canvas, shader=None):
        self.canvas = canvas
        if shader is None:
            shader = Shader(self.canvas)
        self.shader = shader
        self.camera = self.canvas.camera


    def loadLightProfile(self):
        lightprof = self.canvas.lightprof
        mat = self.canvas.material
        lights = [light for light in lightprof.lights if light.enabled]
        nlights = len(lights)
        ambient = lightprof.ambient * np.ones(3)  # global ambient
        for light in lights:
            ambient += light.ambient
        ambient = np.clip(ambient, 0., 1.)  # clip, OpenGL does anyways
        diffuse = np.array([light.diffuse for light in lights]).ravel()
        specular = np.array([light.specular for light in lights]).ravel()
        position = np.array([light.position[:3] for light in lights]).ravel()
        settings = Attributes({
            'nlights': nlights,
            'ambicolor': ambient,
            'diffcolor': diffuse,
            'speccolor': specular,
            'lightdir': position,
            'ambient': mat.ambient,
            'diffuse': mat.diffuse,
            'specular': mat.specular,
            'shininess': mat.shininess,
            'alphablend': self.canvas.settings.alphablend,
            'alpha': self.canvas.settings.transparency,
            'bkalpha': self.canvas.settings.transparency,
            })
        #if pf.options.gl3:
            #print("LIGHT PROFILE to shader: %s" % settings)
        self.shader.loadUniforms(settings)


    def setDefaults(self):
        """Set the GL context and the shader uniforms to default values."""
        GL.glLineWidth(self.canvas.settings.linewidth)
        # Enable setting pointsize in the shader
        # Maybe we should do pointsize with gl context?
        GL.glEnable(GL.GL_VERTEX_PROGRAM_POINT_SIZE)
        # NEXT, the shader uniforms
        # When all attribute names are correct, this could be done with a
        # single statement like
        #   self.shader.loadUniforms(self.canvas.settings)
        #
        self.shader.uniformInt('highlight', False)
        self.shader.uniformFloat('lighting', self.canvas.settings.lighting)
        self.shader.uniformInt('useObjectColor', 1)
        self.shader.uniformInt('rgbamode', False)
        self.shader.uniformVec3('objectColor', self.canvas.settings.fgcolor)
        self.shader.uniformVec3('objectBkColor', self.canvas.settings.fgcolor)
        self.shader.uniformVec3('highlightColor', self.canvas.settings.slcolor)
        self.shader.uniformFloat('pointsize', self.canvas.settings.pointsize)
        self.loadLightProfile()


    def renderObjects(self, objects):
        """Render a list of objects"""
        for obj in objects:
            GL.glDepthFunc(GL.GL_LESS)
            self.setDefaults()
            if obj.trl or obj.rot or obj.trl0:
                self.loadMatrices(rot=self.rot, trl=self.trl, trl0=self.trl0)
            obj.render(self)
            if obj.trl or obj.rot or obj.trl0:
                self.loadMatrices()


    def pickObjects(self, objects):
        """Render a list of objects for picking"""
        for obj in objects:
            GL.glDepthFunc(GL.GL_LESS)
            #self.setDefaults()
            if obj.trl or obj.rot or obj.trl0:
                self.loadMatrices(rot=self.rot, trl=self.trl, trl0=self.trl0)
            obj.renderpick(self)
            if obj.trl or obj.rot or obj.trl0:
                self.loadMatrices()

    def loadMatrices(self, rot=None, trl=None, trl0=None):
        """Load the rendering matrices.

        rot, trl, trl0 are additional rotation, translation and
        pre-translation for the object.
        """
        # Get the current modelview*projection matrix
        modelview = self.camera.modelview
        if trl0:
            modelview.translate(trl0)
        if rot:
            modelview.rotate(rot)
        if trl:
            modelview.translate(trl)
        projection = self.camera.projection
        transinv = self.camera.modelview.transinv().rot

        # Propagate the matrices to the uniforms of the shader
        self.shader.uniformMat4('modelview', modelview.gl())
        self.shader.uniformMat4('projection', projection.gl())
        self.shader.uniformMat3('normalstransform', transinv.flatten().astype(np.float32))


    def render3D(self, actors, picking=False):
        """Render the 3D actors in the scene.

        """
        if not actors:
            return

        # Get the current modelview*projection matrix
        modelview = self.camera.modelview
        projection = self.camera.projection
        transinv = self.camera.modelview.transinv().rot

        # Propagate the matrices to the uniforms of the shader
        self.shader.uniformMat4('modelview', modelview.gl())
        self.shader.uniformMat4('projection', projection.gl())
        self.shader.uniformMat3('normalstransform', transinv.flatten().astype(np.float32))

        # sort actors in back and front, and select visible
        actors = back(actors) + front(actors)
        actors =  [o for o in actors if o.visible is not False]

        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDepthMask(GL.GL_TRUE)

        if picking:
            # render with pickColor
            actors = [a for a in actors if a.pickable]
            self.pickObjects(actors)

        elif not self.canvas.settings.alphablend:
            # opaque: all actors in order of creation
            self.renderObjects(actors)

        else:
            # alphablend: optimize drawing order
            opaque = [a for a in actors if a.opak]
            transp = [a for a in actors if not a.opak]

            # First render the opaque objects
            self.renderObjects(opaque)

            # Then the transparent ones
            # Disable writing to the depth buffer
            # as everything behind the transparent object
            # also needs to be drawn
            GL.glDepthMask(GL.GL_FALSE)

            if pf.cfg['render/transp_nocull']:
                GL.glDisable(GL.GL_CULL_FACE)

            GL.glEnable(GL.GL_BLEND)
            GL.glBlendEquation(GL.GL_FUNC_ADD)
            if pf.cfg['render/alphablend'] == 'mult':
                GL.glBlendFunc(GL.GL_ZERO, GL.GL_SRC_COLOR)
            elif pf.cfg['render/alphablend'] == 'add':
                GL.glBlendFunc(GL.GL_ONE, GL.GL_ONE)
            elif pf.cfg['render/alphablend'] == 'trad1':
                GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE)
            else:
                GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
            self.renderObjects(transp)
            GL.glDisable(GL.GL_BLEND)

        GL.glDepthMask(GL.GL_TRUE)


    def render2D(self, actors):
        """Render 2D decorations.

        """
        if not actors:
            return
        # Set modelview/projection
        modelview = Matrix4()
        self.shader.uniformMat4('modelview', modelview.gl())

        left = 0.  # -0.5
        right = float(self.canvas.width())  # -0.5
        bottom = 0.  # -0.5
        top = float(self.canvas.height())  # -0.5
        near = -1.
        far = 1.
        projection = orthogonal_matrix(left, right, bottom, top, near, far)
        self.shader.uniformMat4('projection', projection.gl())

        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDisable(GL.GL_CULL_FACE)
        GL.glDepthMask(GL.GL_FALSE)

        # ALPHABLEND
        #
        # We need blending for text rendering!
        #
        # 2D actors are by default opak!
        opaque = [a for a in actors if a.opak is None or a.opak]
        transp = [a for a in actors if a.opak is False]

        # First render the opaque objects
        self.renderObjects(opaque)

        # Then the transparent ones
        # Disable writing to the depth buffer
        # as everything behind the transparent object
        # also needs to be drawn
        # TODO: put this in a function enableDepth(depthmode)
        #   as it is also used in render3D
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendEquation(GL.GL_FUNC_ADD)
        if pf.cfg['render/textblend'] == 'mult':
            GL.glBlendFunc(GL.GL_ZERO, GL.GL_SRC_COLOR)
        elif pf.cfg['render/textblend'] == 'add':
            GL.glBlendFunc(GL.GL_ONE, GL.GL_ONE)
        elif pf.cfg['render/textblend'] == 'trad1':
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE)
        elif pf.cfg['render/textblend'] == 'zero':
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ZERO)
        else:
             GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        self.renderObjects(transp)
        GL.glDisable(GL.GL_BLEND)
        GL.glDepthMask(GL.GL_TRUE)


    def renderBG(self, actors):
        """Render 2D background actors.

        """
        if not actors:
            return

        #print("Render %s backgrounds" % len(actors))

        # Set modelview/projection
        modelview = projection = Matrix4()

        self.shader.uniformMat4('modelview', modelview.gl())
        self.shader.uniformMat4('projection', projection.gl())

        self.canvas.zoom_2D()  # should be combined with above

        # in clip space
        GL.glDisable(GL.GL_DEPTH_TEST)
        self.renderObjects(actors)


    def render(self, scene, picking=False):
        """Render the geometry for the scene."""
        self.shader.bind(picking=picking)

        try:
            if picking:
                # can only pick from actors
                self.render3D(scene.actors, picking)
            else:
                # The back backgrounds
                self.renderBG(back(scene.backgrounds))
                # The 2D back decorations
                self.render2D(back(scene.decorations + scene.annot2d))
                # The 3D stuff
                self.render3D(scene.actors + scene.annot3d, picking)
                # The 2D front decorations
                self.render2D(front(scene.annot2d + scene.decorations))
                # The front backgrounds
                self.renderBG(front(scene.backgrounds))

        finally:
            self.shader.unbind()


def front(actorlist):
    """Return the actors from the list that have ontop=True"""
    return [a for a in actorlist if a.ontop]


def back(actorlist):
    """Return the actors from the list that have ontop=False"""
    return [a for a in actorlist if not a.ontop]


# End
