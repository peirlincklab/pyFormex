# This file was automatically generated by SWIG (http://www.swig.org).
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
# Version 2.0.4
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.



from sys import version_info
if version_info >= (2, 6, 0):
    def swig_import_helper():
        from os.path import dirname
        import imp
        fp = None
        try:
            fp, pathname, description = imp.find_module('_gl2ps', [dirname(__file__)])
        except ImportError:
            import _gl2ps
            return _gl2ps
        if fp is not None:
            try:
                _mod = imp.load_module('_gl2ps', fp, pathname, description)
            finally:
                fp.close()
            return _mod
    _gl2ps = swig_import_helper()
    del swig_import_helper
else:
    import _gl2ps
del version_info
try:
    _swig_property = property
except NameError:
    pass # Python < 2.2 doesn't have 'property'.
def _swig_setattr_nondynamic(self,class_type,name,value,static=1):
    if (name == "thisown"): return self.this.own(value)
    if (name == "this"):
        if type(value).__name__ == 'SwigPyObject':
            self.__dict__[name] = value
            return
    method = class_type.__swig_setmethods__.get(name, None)
    if method: return method(self, value)
    if (not static):
        self.__dict__[name] = value
    else:
        raise AttributeError("You cannot add attributes to %s" % self)

def _swig_setattr(self, class_type, name, value):
    return _swig_setattr_nondynamic(self, class_type, name, value, 0)

def _swig_getattr(self, class_type, name):
    if (name == "thisown"): return self.this.own()
    method = class_type.__swig_getmethods__.get(name, None)
    if method: return method(self)
    raise AttributeError(name)

def _swig_repr(self):
    try: strthis = "proxy of " + self.this.__repr__()
    except: strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)

try:
    _object = object
    _newclass = 1
except AttributeError:
    class _object : pass
    _newclass = 0


GL2PS_MAJOR_VERSION = _gl2ps.GL2PS_MAJOR_VERSION
GL2PS_MINOR_VERSION = _gl2ps.GL2PS_MINOR_VERSION
GL2PS_PATCH_VERSION = _gl2ps.GL2PS_PATCH_VERSION
GL2PS_EXTRA_VERSION = _gl2ps.GL2PS_EXTRA_VERSION
GL2PS_VERSION = _gl2ps.GL2PS_VERSION
GL2PS_COPYRIGHT = _gl2ps.GL2PS_COPYRIGHT
GL2PS_PS = _gl2ps.GL2PS_PS
GL2PS_EPS = _gl2ps.GL2PS_EPS
GL2PS_TEX = _gl2ps.GL2PS_TEX
GL2PS_PDF = _gl2ps.GL2PS_PDF
GL2PS_SVG = _gl2ps.GL2PS_SVG
GL2PS_PGF = _gl2ps.GL2PS_PGF
GL2PS_NO_SORT = _gl2ps.GL2PS_NO_SORT
GL2PS_SIMPLE_SORT = _gl2ps.GL2PS_SIMPLE_SORT
GL2PS_BSP_SORT = _gl2ps.GL2PS_BSP_SORT
GL2PS_SUCCESS = _gl2ps.GL2PS_SUCCESS
GL2PS_INFO = _gl2ps.GL2PS_INFO
GL2PS_WARNING = _gl2ps.GL2PS_WARNING
GL2PS_ERROR = _gl2ps.GL2PS_ERROR
GL2PS_NO_FEEDBACK = _gl2ps.GL2PS_NO_FEEDBACK
GL2PS_OVERFLOW = _gl2ps.GL2PS_OVERFLOW
GL2PS_UNINITIALIZED = _gl2ps.GL2PS_UNINITIALIZED
GL2PS_NONE = _gl2ps.GL2PS_NONE
GL2PS_DRAW_BACKGROUND = _gl2ps.GL2PS_DRAW_BACKGROUND
GL2PS_SIMPLE_LINE_OFFSET = _gl2ps.GL2PS_SIMPLE_LINE_OFFSET
GL2PS_SILENT = _gl2ps.GL2PS_SILENT
GL2PS_BEST_ROOT = _gl2ps.GL2PS_BEST_ROOT
GL2PS_OCCLUSION_CULL = _gl2ps.GL2PS_OCCLUSION_CULL
GL2PS_NO_TEXT = _gl2ps.GL2PS_NO_TEXT
GL2PS_LANDSCAPE = _gl2ps.GL2PS_LANDSCAPE
GL2PS_NO_PS3_SHADING = _gl2ps.GL2PS_NO_PS3_SHADING
GL2PS_NO_PIXMAP = _gl2ps.GL2PS_NO_PIXMAP
GL2PS_USE_CURRENT_VIEWPORT = _gl2ps.GL2PS_USE_CURRENT_VIEWPORT
GL2PS_COMPRESS = _gl2ps.GL2PS_COMPRESS
GL2PS_NO_BLENDING = _gl2ps.GL2PS_NO_BLENDING
GL2PS_TIGHT_BOUNDING_BOX = _gl2ps.GL2PS_TIGHT_BOUNDING_BOX
GL2PS_POLYGON_OFFSET_FILL = _gl2ps.GL2PS_POLYGON_OFFSET_FILL
GL2PS_POLYGON_BOUNDARY = _gl2ps.GL2PS_POLYGON_BOUNDARY
GL2PS_LINE_STIPPLE = _gl2ps.GL2PS_LINE_STIPPLE
GL2PS_BLEND = _gl2ps.GL2PS_BLEND
GL2PS_TEXT_C = _gl2ps.GL2PS_TEXT_C
GL2PS_TEXT_CL = _gl2ps.GL2PS_TEXT_CL
GL2PS_TEXT_CR = _gl2ps.GL2PS_TEXT_CR
GL2PS_TEXT_B = _gl2ps.GL2PS_TEXT_B
GL2PS_TEXT_BL = _gl2ps.GL2PS_TEXT_BL
GL2PS_TEXT_BR = _gl2ps.GL2PS_TEXT_BR
GL2PS_TEXT_T = _gl2ps.GL2PS_TEXT_T
GL2PS_TEXT_TL = _gl2ps.GL2PS_TEXT_TL
GL2PS_TEXT_TR = _gl2ps.GL2PS_TEXT_TR

def gl2psBeginPage(*args):
  return _gl2ps.gl2psBeginPage(*args)
gl2psBeginPage = _gl2ps.gl2psBeginPage

def gl2psEndPage():
  return _gl2ps.gl2psEndPage()
gl2psEndPage = _gl2ps.gl2psEndPage

def gl2psSetOptions(*args):
  return _gl2ps.gl2psSetOptions(*args)
gl2psSetOptions = _gl2ps.gl2psSetOptions

def gl2psGetOptions(*args):
  return _gl2ps.gl2psGetOptions(*args)
gl2psGetOptions = _gl2ps.gl2psGetOptions

def gl2psBeginViewport(*args):
  return _gl2ps.gl2psBeginViewport(*args)
gl2psBeginViewport = _gl2ps.gl2psBeginViewport

def gl2psEndViewport():
  return _gl2ps.gl2psEndViewport()
gl2psEndViewport = _gl2ps.gl2psEndViewport

def gl2psText(*args):
  return _gl2ps.gl2psText(*args)
gl2psText = _gl2ps.gl2psText

def gl2psTextOpt(*args):
  return _gl2ps.gl2psTextOpt(*args)
gl2psTextOpt = _gl2ps.gl2psTextOpt

def gl2psSpecial(*args):
  return _gl2ps.gl2psSpecial(*args)
gl2psSpecial = _gl2ps.gl2psSpecial

def gl2psDrawPixels(*args):
  return _gl2ps.gl2psDrawPixels(*args)
gl2psDrawPixels = _gl2ps.gl2psDrawPixels

def gl2psEnable(*args):
  return _gl2ps.gl2psEnable(*args)
gl2psEnable = _gl2ps.gl2psEnable

def gl2psDisable(*args):
  return _gl2ps.gl2psDisable(*args)
gl2psDisable = _gl2ps.gl2psDisable

def gl2psPointSize(*args):
  return _gl2ps.gl2psPointSize(*args)
gl2psPointSize = _gl2ps.gl2psPointSize

def gl2psLineWidth(*args):
  return _gl2ps.gl2psLineWidth(*args)
gl2psLineWidth = _gl2ps.gl2psLineWidth

def gl2psBlendFunc(*args):
  return _gl2ps.gl2psBlendFunc(*args)
gl2psBlendFunc = _gl2ps.gl2psBlendFunc
# This file is compatible with both classic and new-style classes.


