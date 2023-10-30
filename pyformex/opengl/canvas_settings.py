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
"""This modules defines the CanvasSettings class

"""
import pyformex as pf
from pyformex import utils
from pyformex import arraytools as at
from pyformex import colors
from pyformex.mydict import Dict
from .sanitize import saneColor


############### OpenGL Lighting #################################

class Material():
    def __init__(self, name, ambient=0.2, diffuse=0.2, specular=0.9,
                 emission=0.1, shininess=2.0):
        self.name = str(name)
        self.ambient = float(ambient)
        self.diffuse = float(diffuse)
        self.specular = float(specular)
        self.emission = float(emission)
        self.shininess = float(shininess)


    def setValues(self, **kargs):
        #print "setValues",kargs
        for k in kargs:
            #print k,kargs[k]
            if hasattr(self, k):
                #print getattr(self,k)
                setattr(self, k, float(kargs[k]))
                #print getattr(self,k)


    def dict(self):
        """Return the material light parameters as a dict"""
        return dict([(k, getattr(self, k)) for k in ['ambient', 'diffuse', 'specular', 'emission', 'shininess']])


    def __str__(self):
        return """MATERIAL: %s
    ambient:  %s
    diffuse:  %s
    specular: %s
    emission: %s
    shininess: %s
""" % (self.name, self.ambient, self.diffuse, self.specular, self.emission, self.shininess)


def getMaterials():
    mats = pf.refcfg['material']
    mats.update(pf.prefcfg['material'])
    mats.update(pf.cfg['material'])
    return mats


def createMaterials():
    mats = getMaterials()
    matdb = {}
    for m in mats:
        matdb[m] = Material(m, **mats[m])
    return matdb


class Light():
    """A class representing an OpenGL light.

    The light can emit 3 types of light: ambient, diffuse and specular,
    which can have different color and are all off by default.


    """

    def __init__(self, ambient=0.0, diffuse=0.0, specular=0.0,
                 position=[0., 0., 1.], enabled=True):
        self.setValues(ambient, diffuse, specular, position)
        self.enable(enabled)

    def setValues(self, ambient=None, diffuse=None, specular=None, position=None):
        if ambient is not None:
            self.ambient = colors.GLcolor(ambient)
        if diffuse is not None:
            self.diffuse = colors.GLcolor(diffuse)
        if specular is not None:
            self.specular = colors.GLcolor(specular)
        if position is not None:
            self.position = at.checkArray(position, (3,), 'f')

    def enable(self, onoff=True):
        self.enabled = bool(onoff)

    def disable(self):
        self.enable(False)


    def __str__(self, name=''):
        return """LIGHT%s (enabled: %s):
    ambient color:  %s
    diffuse color:  %s
    specular color: %s
    position: %s
""" % (name, self.enabled, self.ambient, self.diffuse, self.specular, self.position)


class LightProfile():
    """A lightprofile contains all the lighting parameters.

    Currently this consists off:
    - `ambient`: the global ambient lighting (currently a float)
    - `lights`: a list of 1 to 4 Lights
    """

    def __init__(self, ambient, lights):
        self.ambient = ambient
        self.lights = lights


    def __str__(self):
        s = """LIGHTPROFILE:
    global ambient:  %s
    """ % self.ambient
        for i, l in enumerate(self.lights):
            s += '  ' + l.__str__(i)
        return s


##################################################################
#
#  The Canvas Settings
#

class CanvasSettings(Dict):
    """A collection of settings for an OpenGL Canvas.

    The canvas settings are a collection of settings and default values
    affecting the rendering in an individual viewport. There are two type of
    settings:

    - mode settings are set during the initialization of the canvas and
      can/should not be changed during the drawing of actors and decorations;
    - default settings can be used as default values but may be changed during
      the drawing of actors/decorations: they are reset before each individual
      draw instruction.

    Currently the following mode settings are defined:

    - bgmode: the viewport background color mode
    - bgcolor: the viewport background color: a single color or a list of
      colors (max. 4 are used).
    - bgimage: background image filename
    - alphablend: boolean (transparency on/off)

    The list of default settings includes:

    - fgcolor: the default drawing color
    - bkcolor: the default backface color
    - slcolor: the highlight color
    - colormap: the default color map to be used if color is an index
    - bklormap: the default color map to be used if bkcolor is an index
    - textcolor: the default color for text drawing
    - smooth: boolean (smooth/flat shading)
    - lighting: boolean (lights on/off)
    - culling: boolean
    - transparency: float (0.0..1.0)
    - avgnormals: boolean
    - wiremode: integer -3..3
    - pointsize: the default size for drawing points
    - marksize: the default size for drawing markers
    - linewidth: the default width for drawing lines

    Any of these values can be set in the constructor using a keyword argument.
    All items that are not set, will get their value from the configuration
    file(s).
    """

    # A collection of default rendering profiles.
    # These contain the values different from the overall defaults
    RenderProfiles = {
        'wireframe': Dict({
            'smooth': False,
            'fill': False,
            'lighting': False,
            'alphablend': False,
            'transparency': 1.0,
            'wiremode': -1,
            'avgnormals': False,
            }),
        'smooth': Dict({
            'smooth': True,
            'fill': True,
            'lighting': True,
            'alphablend': False,
            'transparency': 0.5,
            'wiremode': -1,
            'avgnormals': False,
            }),
        'smooth_avg': Dict({
            'smooth': True,
            'fill': True,
            'lighting': True,
            'alphablend': False,
            'transparency': 0.5,
            'wiremode': -1,
            'avgnormals': True,
            }),
        'smoothwire': Dict({
            'smooth': True,
            'fill': True,
            'lighting': True,
            'alphablend': False,
            'transparency': 0.5,
            'wiremode': 1,
            'avgnormals': False,
            }),
        'flat': Dict({
            'smooth': False,
            'fill': True,
            'lighting': False,
            'alphablend': False,
            'transparency': 0.5,
            'wiremode': -1,
            'avgnormals': False,
            }),
        'flatwire': Dict({
            'smooth': False,
            'fill': True,
            'lighting': False,
            'alphablend': False,
            'transparency': 0.5,
            'wiremode': 1,
            'avgnormals': False,
            }),
        }
    bgcolor_modes = ['solid', 'vertical', 'horizontal', 'full']
    edge_modes = ['none', 'feature', 'all']

    def __init__(self, **kargs):
        """Create a new set of CanvasSettings."""
        Dict.__init__(self)
        self.reset(kargs)

    def reset(self, d={}):
        """Reset the CanvasSettings to its defaults.

        The default values are taken from the configuration files.
        An optional dictionary may be specified to override (some of) these defaults.
        """
        self.update(pf.refcfg['canvas'])
        self.update(self.RenderProfiles[pf.prefcfg['draw/rendermode']])
        self.update(pf.prefcfg['canvas'])
        self.update(pf.cfg['canvas'])
        if d:
            self.update(d)

    def update(self, d, strict=True):
        """Update current values with the specified settings

        Returns the sanitized update values.
        """
        ok = self.checkDict(d, strict)
        Dict.update(self, ok)

    @classmethod
    def checkDict(clas, dict, strict=True):
        """Transform a dict to acceptable settings."""
        ok = {}
        for k, v in dict.items():
            try:
                if k in ['bgcolor', 'fgcolor', 'bkcolor', 'slcolor',
                          'colormap', 'bkcolormap', 'textcolor']:
                    if v is not None:
                        v = saneColor(v)
                elif k in ['bgimage']:
                    v = str(v)
                elif k in ['smooth', 'fill', 'lighting', 'culling',
                           'alphablend', 'avgnormals', ]:
                    v = bool(v)
                elif k in ['linewidth', 'pointsize', 'marksize']:
                    v = float(v)
                elif k in ['wiremode']:
                    v = int(v)
                elif k == 'linestipple':
                    v = [int(vi) for vi in v]
                elif k == 'transparency':
                    v = max(min(float(v), 1.0), 0.0)
                elif k == 'bgmode':
                    v = str(v).lower()
                    if not v in clas.bgcolor_modes:
                        raise
                elif k == 'marktype':
                    pass
                elif k == 'rendermode':
                    if v in ['wireframe', 'smooth', 'smoothwire',
                             'flat', 'flatwire']:
                        pass
                    else:
                        raise
                else:
                    raise
                ok[k] = v
            except Exception:
                if strict:
                    raise ValueError(
                        f"Invalid key/value for CanvasSettings: {k} = {v}")
        return ok


    def activate(self):
        """Activate the default canvas settings in the GL machine."""
        from . import gl
        for k in self:
            if k in ['smooth', 'fill', 'linewidth', 'pointsize']:
                func = getattr(gl, 'gl_'+k)
                try:
                    func(self[k])
                except Exception:
                    print(f"Error in setting {k} with func {func}")
                    raise

    def __str__(self):
        # atoms = []
        # for k in self:
        #     print(k)
        #     try:
        #         s = f"{k} = {self[k]!r}"
        #     except:
        #         s = f"{k} = FAIL"
        #     print(s)
        #     atoms.append(s)
        # return '\n'.join(atoms)

        return utils.formatDict(self)


    ## def setMode(self):
    ##     """Activate the mode canvas settings in the GL machine."""
    ##     GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    ##     if self.bgcolor.ndim > 1:
    ##         color = self.bgcolor[0]
    ##     else:
    ##         color = self.bgcolor
    ##     GL.glClearColor(*colors.RGBA(color))



    @staticmethod
    def extractCanvasSettings(d):
        """Split a dict in canvas settings and other items.

        Returns a tuple of two dicts: the first one contains the items
        that are canvas settings, the second one the rest.
        """
        return (utils.select(d, pf.refcfg['canvas']),
                utils.remove(d, pf.refcfg['canvas']))


### End
