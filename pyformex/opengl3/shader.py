#
##
##  This file is part of pyFormex 2.4  (Thu Feb 25 13:39:20 CET 2021)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2020 (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
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
from pyformex.software import CompareVersion
from pyformex.gui import qtgl
from pyformex.opengl import gl
from pyformex.opengl.gl import GL
import moderngl


# class Context:
#     """The OpenGL context"""
#     def __init__(self):
#         self.ctx = moderngl.create_context()
#         print(self.ctx.info)
#         self.aspect = self.ctx.viewport[2] /  self.ctx.viewport[3]
#         print(f"""
#             Created context:
#             Viewport: {self.ctx.viewport}
#             aspect: {self.aspect}
#             """)
#         self.progs = {}

#     def addProgram(self, name, **kargs):
#         """kargs is a dict of shader sources"""
#         self.progs[name] = self.ctx.program(**kargs)


def findShaders(version=None):
    """Determine the default shader programs"""
    print(f"Selecting shader for OpenGL {version}")
    fmt = qtgl.getOpenGLFormat()
    major, minor = fmt.majorVersion(), fmt.minorVersion()
    aversion = "%s.%s" % (major, minor)
    if version is not None:
        if CompareVersion(version, '<', '3.3'):
            raise ValueError('Only version >= 3.3 is supported')
    else:
        version = aversion

    major, minor = version.split('.')
    glsl = f"{major}{minor}0"

    # Default shaders
    path = pf.pyformexdir / 'opengl3' / 'glsl'
    shadertail = f"_shader_{glsl}.c"
    shaderfiles = {}
    for shader in ['vertex', 'geometry', 'fragment']:
        shaderfile = path / f"{shader}{shadertail}"
        if shaderfile.exists():
            shaderfiles[f"{shader}_shader"] = shaderfile
    pf.debug(f"Found shaders {shaderfiles}", pf.DEBUG.OPENGL)
    return shaderfiles


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
        'offset3',
        'highlightColor',
    ]

    uniforms_vec3_list = [
        'diffcolor',
        'speccolor',
        'lightdir',
    ]

    uniforms = uniforms_int + uniforms_float +  uniforms_vec3 + [
        'modelview',
        'projection',
        'modelviewprojection',
        'normalstransform',
        'pickmat',
        'picking',
    ]

    def __init__(self, canvas, version=None, attributes=None, uniforms=None):
        """Initialize the shader program"""
        print("SHADER INIT")
        pf.ctx = self.ctx = moderngl.create_context()
        pf.debug(self.ctx.info, pf.DEBUG.OPENGL)
        self.aspect = self.ctx.viewport[2] /  self.ctx.viewport[3]
        print(f"""
            Created context:
            Viewport: {self.ctx.viewport}
            aspect: {self.aspect}
            """)
        self.progs = {}
        shaders = findShaders(version)
        for s in shaders:
            with open(shaders[s]) as f:
                shaders[s] = f.read()
        pf.prog = self.progs['default'] = self.prog = self.ctx.program(**shaders)

        if attributes is None:
            attributes = Shader.attributes

        if uniforms is None:
            uniforms = Shader.uniforms

        # self.attribute = self.locations(GL.glGetAttribLocation, attributes)
        # self.uniform = self.locations(GL.glGetUniformLocation, uniforms)
        self.picking = 0  # Default render mode


    # def locations(self, func, keys):
    #     """Create a dict with the locations of the specified keys"""
    #     return dict([(k, func(self.shader, k)) for k in keys])


    def loadUniform(self, name, value):
        """Load a uniform into the shader prog"""
        self.prog[name] = value

    uniformInt = uniformFloat = loadUniform

    def uniformMat4(self, name, mat):
        self.prog[name] = tuple(mat.flat)

    uniformVec3 = uniformMat3 = uniformMat4

    def uniformVec3List(self, name, mat):
        mat = mat.reshape(-1,3).copy()
        mat.resize((4,3))
        #print(name,mat)
        self.prog[name] = [tuple(row) for row in mat]

    def bind(self, picking=False):
        """Bind the shader program"""
        #shaders.glUseProgram(self.shader)
        self.prog['picking'] = picking


    def unbind(self):
        """Unbind the shader program"""
        #shaders.glUseProgram(0)
        pass


    def loadUniforms(self, D):
        """Load the uniform attributes defined in D

        D is a dict with uniform attributes to be loaded into
        the shader program. The attributes can be of type
        int, float, or vec3.
        """
        # for attribs in [
        #         self.uniforms_int, self.uniforms_float, self.uniforms_vec3
        # ]:
        #     for a in attribs:
        #         print(f"SHADER: Loading {a}")
        #         v = D[a]
        #         if v is not None:
        #             self.prog[a] = v
        for attribs, func in [
            (self.uniforms_int, self.uniformInt),
            (self.uniforms_float, self.uniformFloat),
            (self.uniforms_vec3, self.uniformVec3),
            (self.uniforms_vec3_list, self.uniformVec3List),
            ]:
            for a in attribs:
                #print(f"loadUniforms: {a}")
                v = D[a]
                if v is not None:
                    func(a, v)


    # def __del__(self):
    #     """Delete a shader instance.

    #     This will unbind the shader program before deleting it.
    #     """
    #     self.unbind()

# End
