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
#

"""Camera tools

Some extra tools to handle the camera.
"""

import pyformex as pf
from pyformex.gui.widgets import simpleInputItem as _I, Dialog
from pyformex.arraytools import stuur

dialog = None

def getCameraSettings(cam):
        # USING 'eye' creates an endless recursion!!!
    return dict([(k, getattr(cam, k)) for k in ['focus', 'dist', 'fovy', 'aspect', 'area', 'near', 'far']])


def apply():
    global dialog
    if dialog.validate():
        settings = dialog.results
        print(f"NEW SETTINGS", settings)
        cam = pf.canvas.camera
        cam.setClip(settings['near'], settings['far'])
        pf.canvas.update()


def close():
    global dialog
    if dialog:
        dialog.close()
        dialog = None


def updateSettings(cam):
    global dialog
    settings = getCameraSettings(cam)
    dialog.updateData(settings)

def setNear(fld):
    val = fld.value()/100.
    cam = pf.canvas.camera
    res = stuur(val, [0., 0.5, 1.0], [0.01*cam.dist, cam.dist, 100.*cam.dist])
    #print "%s = %s" % (val,res)
    cam.setClip(res, cam.far)
    pf.canvas.update()
def setFar(fld):
    val = fld.value()/100.
    cam = pf.canvas.camera
    res = stuur(val, [0., 0.5, 1.0], [0.01*cam.dist, cam.dist, 100.*cam.dist])
    #print "%s = %s" % (val,res)
    cam.setClip(cam.near, res)
    pf.canvas.update()


def showCameraTool():
    """Show the camera settings dialog.

    This function pops up a dialog where the user can interactively
    adjust the current camera settings.

    The function can also be called from the ``Camera->Settings`` menu.
    """
    global dialog
    cam = pf.canvas.camera
    settings = getCameraSettings(cam)
    print(f"CAMERA SETTINGS {settings}")
    print(f"CAMERA DICT {cam.__dict__}")
    settings['near'] = cam.near/cam.dist
    settings['far'] = cam.far/cam.dist

    dialog = Dialog(
        caption="Camera settings",
        store=settings, save=False,
        items=[
            _I('focus', dec=6, text='Focus', itemtype='point',
               tooltip='The point where the camera is looking at.'),
            # _I('eye', dec=6, text='Eye', itemtype='point',
            #    tooltip='The position of the camera eye.'),
            _I('dist', dec=6, text='Distance',
               tooltip='The distance of the camera to the focus point.'),
            _I('fovy', dec=6, text='Field of View',
               tooltip='The vertical opening angle of the camera lens.'),
            _I('aspect', dec=6, text='Aspect ratio',
               tooltip='Ratio of vertical over horizontal lens opening angles.'),
            # _I('area',text='Visible area',
            # tooltip="Relative part of the camera area that is visible "
            # "in the viewport.'),
            _I('near', dec=6, text='Near clipping plane',
               itemtype='fslider', func=setNear,
               tooltip='Distance of the near clipping plane to the camera.'),
            _I('far', dec=6, text='Far clipping plane',
               itemtype='fslider', func=setFar,
               tooltip='Distance of the far clipping plane to the camera.'),
        ],
        actions = [
            ('Close', close),
            ('Apply',apply),
        ], default='Close',
    )
    cam.modelview_callback = updateSettings
    dialog.show()


if __name__ == '__draw__':
    showCameraTool()

# End
