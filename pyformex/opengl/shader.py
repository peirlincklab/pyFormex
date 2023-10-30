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

"""OpenGL shader programs

Python OpenGL framework for pyFormex

This module is responsible for loading the shader programs
and its data onto the graphics system.

(C) 2013 Benedict Verhegghe and the pyFormex project.

"""

import pyformex as pf
from pyformex.software import SaneVersion
from pyformex.gui import qtgl
from . import gl
from .gl import GL, shaders


def defaultShaders():
    """Determine the default shader programs"""
    glversion = gl.gl_version()
    vendor = glversion['vendor']
    renderer = glversion['renderer']
    version = glversion['version']
    vmajor, vminor = version.split('.')[:2]
    fmt = qtgl.getOpenGLFormat()
    major, minor = fmt.majorVersion(), fmt.minorVersion()
    availversion = "%s.%s" % (vmajor, vminor)
    activeversion = "%s.%s" % (major, minor)
    pf.debug("Vendor: %s; Renderer: %s; Available version: %s; Active version %s" % (vendor, renderer, availversion, activeversion), pf.DEBUG.OPENGL)
    #shortversion = "%s.%s" % (major,minor)
    # Default shaders
    dirname = pf.pyformexdir / 'glsl'
    vertexshader = str(dirname / "vertex_shader")
    fragmentshader = str(dirname / "fragment_shader")
    if not pf.options.shader:

        if SaneVersion(pf.cfg['opengl/version']) >= SaneVersion('3.3'):
            pf.options.shader = '330'

        # Default shaders for some hardware

        pf.debug("Selecting best default shader", pf.DEBUG.OPENGL)

        #if 'Mesa' in renderer or 'Mesa' in version:
        #    pf.options.shader = 'mesa'

        # For Radeon, select 330 if available
        if 'Radeon' in renderer and SaneVersion(availversion) >= SaneVersion('3.3'):
            pf.options.shader = '330'


    if pf.options.shader:
        vertexshader += '_%s' % pf.options.shader
        fragmentshader += '_%s' % pf.options.shader
    vertexshader += '.c'
    fragmentshader += '.c'
    pf.debug(f"Using shaders {vertexshader} and {fragmentshader}", pf.DEBUG.OPENGL)
    return vertexshader, fragmentshader


class Shader():
    """An OpenGL shader consisting of a vertex and a fragment shader pair.

    Class attributes:

    - `_vertexshader` : the vertex shader source.
      By default, a basic shader supporting vertex positions and vertex colors
      is defined

    - `_fragmentshader` : the fragment shader source.
      By default, a basic shader supporting fragment colors is defined.

    - `attributes`: the shaders' vertex attributes.
    - `uniforms`: the shaders' uniforms.
    """

    # Default attributes and uniforms
    attributes = [
    'pickColor',
    'vertexCoords',
    'vertexNormal',
    'vertexColor',
    'vertexTexturePos',
    'vertexScalar',
    'vertexOffset',
    ]

    # int and bool uniforms
    uniforms_int = [
        'highlight',
        'useObjectColor',
        'rgbamode',
        'useTexture',
        'texmode',
        'rendertype',
        'alphablend',
        'drawface',
        'lighting',
        'nlights',
        ]

    uniforms_float = [
        'pointsize',
        'ambient',
        'diffuse',
        'specular',
        'shininess',
        'alpha',
        'bkalpha',
        ]

    uniforms_vec3 = [
        'objectColor',
        'objectBkColor',
        'ambicolor',
        'diffcolor',
        'speccolor',
        'lightdir',
        'offset3',
        'highlightColor',
    ]

    uniforms = uniforms_int + uniforms_float +  uniforms_vec3 + [
        'modelview',
        'projection',
        'modelviewprojection',
        'normalstransform',
        'picking',
    ]

    def __init__(self, canvas, vshader=None, fshader=None, attributes=None, uniforms=None):
        _vertexshader, _fragmentshader = defaultShaders()
        if vshader is None:
            vshader = _vertexshader
        pf.debug("Using vertex shader %s" % vshader, pf.DEBUG.OPENGL)
        with open(vshader) as f:
            VertexShader = f.read()

        if fshader is None:
            fshader = _fragmentshader
        pf.debug("Using fragment shader %s" % fshader, pf.DEBUG.OPENGL)
        with open(fshader) as f:
            FragmentShader = f.read()

        if attributes is None:
            attributes = Shader.attributes

        if uniforms is None:
            uniforms = Shader.uniforms

        vertex_shader = shaders.compileShader(VertexShader, GL.GL_VERTEX_SHADER)
        fragment_shader = shaders.compileShader(FragmentShader, GL.GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vertex_shader, fragment_shader)

        self.attribute = self.locations(GL.glGetAttribLocation, attributes)
        self.uniform = self.locations(GL.glGetUniformLocation, uniforms)
        #self.picking = 0  # Default render mode


    def locations(self, func, keys):
        """Create a dict with the locations of the specified keys"""
        return dict([(k, func(self.shader, k)) for k in keys])


    def uniformInt(self, name, value):
        """Load a uniform integer or boolean into the shader"""
        loc = self.uniform[name]
        GL.glUniform1i(loc, value)


    def uniformFloat(self, name, value):
        """Load a uniform float into the shader"""
        loc = self.uniform[name]
        GL.glUniform1f(loc, value)


    ## def uniformVec3(self,name,value):
    ##     """Load a uniform vec3 into the shader"""
    ##     loc = self.uniform[name]
    ##     GL.glUniform3fv(loc,1,value)


    def uniformVec3(self, name, value):
        """Load a uniform vec3[n] into the shader

        The value should be a 1D array or list.
        """
        loc = self.uniform[name]
        n = len(value) // 3
        GL.glUniform3fv(loc, n, value)


    def uniformMat4(self, name, value):
        """Load a uniform mat4 into the shader"""
        loc = self.uniform[name]
        GL.glUniformMatrix4fv(loc, 1, False, value)


    def uniformMat3(self, name, value):
        """Load a uniform mat3 into the shader"""
        loc = self.uniform[name]
        GL.glUniformMatrix3fv(loc, 1, False, value)


    def bind(self, picking=False):
        """Bind the shader program"""
        shaders.glUseProgram(self.shader)
        self.uniformInt('picking', picking)


    def unbind(self):
        """Unbind the shader program"""
        shaders.glUseProgram(0)


    def loadUniforms(self, D):
        """Load the uniform attributes defined in D

        D is a dict with uniform attributes to be loaded into
        the shader program. The attributes can be of type
        int, float, or vec3.
        """
        for attribs, func in [
            (self.uniforms_int, self.uniformInt),
            (self.uniforms_float, self.uniformFloat),
            (self.uniforms_vec3, self.uniformVec3),
            ]:
            for a in attribs:
                v = D[a]
                if v is not None:
                    func(a, v)


    def __del__(self):
        """Delete a shader instance.

        This will unbinf the shader program before deleting it.
        """
        self.unbind()

# End
