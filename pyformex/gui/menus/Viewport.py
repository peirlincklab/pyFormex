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
"""Viewport Menu.

This module defines the functions of the Viewport menu.
"""
import pyformex as pf
from pyformex import Path
from pyformex import utils
from pyformex import arraytools as at
from pyformex.gui import widgets, draw, views
from pyformex.opengl import canvas
from pyformex.gui.draw import _I
from .Settings import updateSettings

def setTriade():
    try:
        pos = pf.canvas.triade.pos
        size = pf.canvas.triade.size
    except Exception:
        pos = 'lb'
        size = 50
    res = draw.askItems([
        _I('triade', True),
        _I('pos', pos, choices=[
            'lt', 'lc', 'lb', 'ct', 'cc', 'cb', 'rt', 'rc', 'rb']),
        _I('size', size),
        ])
    if res:
        draw.setTriade(res['triade'], res['pos'], res['size'])


def setGrid():
    canvasgrid_settings = dict([
        (k, pf.cfg['canvasgrid/'+k]) for k in ['showgrid', 'spacing', 'size',
                'linewidth', 'color', 'twocolor', 'color2', 'ontop']])
    res = draw.askItems(store=canvasgrid_settings, save=False, items=[
        _I('showgrid', True, text='Show grid'),
        _I('spacing', text='Distance between grid lines'),
        _I('size', text='Total grid size (0=canvas size)'),
        _I('linewidth', text='Line width'),
        _I('color', itemtype='color', text='Line color'),
        _I('twocolor',),
        _I('color2', itemtype='color', text='Second line color'),
        _I('ontop', ),
        _I('_save_', False, text='Save as my defaults'),
        ], enablers=[
            ('twocolor', True, 'color2')
        ])
    if res:
        if res['twocolor']:
            color = (res['color'], res['color2'])
        else:
            color = res['color']
        s = res['size'] if res['size'] >= 1 else None
        if res['showgrid']:
            draw.setGrid(on=res['showgrid'], d=res['spacing'], s=s, linewidth=res['linewidth'], ontop=res['ontop'], color=color, lighting=False)
        save = res['_save_']
        del res['showgrid']
        del res['_save_']
        res = utils.prefixDict(res, prefix='canvasgrid/')
        res['_save_'] = save
        print(res)
        updateSettings(res)


def setBgColor():
    """Interactively set the viewport background colors."""
    global bgcolor_dialog
    from pyformex.opengl.sanitize import saneColor
    bgmodes = pf.canvas.settings.bgcolor_modes
    mode = pf.canvas.settings.bgmode
    print(pf.canvas.settings.bgcolor)
    color = saneColor(pf.canvas.settings.bgcolor).reshape(-1,3)
    if color.shape[0] != 4:
        color = at.resizeAxis(color, 4, 0)
    cur = Path(pf.canvas.settings.bgimage)
    showimage = cur.exists()
    if not showimage:
        cur = pf.cfg['gui/splash']
    viewer = widgets.ImageView(cur, maxheight=200)

    def changeColor(field):
        if not bgcolor_dialog.validate():
            return
        res = bgcolor_dialog.results
        if res:
            setBackground(**res)

    bgcolor_dialog = widgets.Dialog(
        [
            _I('mode', mode, choices=bgmodes),
            _I('color1', color[0], itemtype='color', func=changeColor, text='Background color 1 (Bottom Left)'),
            _I('color2', color[1], itemtype='color', func=changeColor, text='Background color 2 (Bottom Right)'),
            _I('color3', color[2], itemtype='color', func=changeColor, text='Background color 3 (Top Right)'),
            _I('color4', color[3], itemtype='color', func=changeColor, text='Background color 4 (Top Left'),
            _I('showimage', showimage, text='Show background image'),
            _I('image', cur, text='Background image', itemtype='filename', filter='img', mode='exist', preview=viewer),
            viewer,
            _I('_save_', False, text='Save as default'),
            ],
        caption='Background settings',
        enablers=[
            ('mode', 'vertical', 'color4'),
            ('mode', 'horizontal', 'color2'),
            ('mode', 'full', 'color2', 'color3', 'color4'),
            ('showimage', True, 'image'),
            #('mode', 'solid', '_save_'),
           ]
        )
    res = bgcolor_dialog.getResults()
    if res:
        setBackground(**res)


def setBackground(mode, color1, color2, color3, color4, showimage, image, _save_):
    if mode == 'solid':
        color = color1
    elif mode == 'vertical':
        color = [color1, color1, color4, color4]
    elif mode == 'horizontal':
        color = [color1, color2, color2, color1]
    else:
        color = [color1, color2, color3, color4]
    if not showimage:
        image = ''
    pf.canvas.setBackground(color=color, image=image)
    pf.canvas.update()
    if _save_:
        updateSettings({
            'canvas/bgmode': mode,
            'canvas/bgcolor': color,
            'canvas/bgimage': image,
            '_save_': _save_})


def setColors():
    """Set the canvas colors"""

    save_settings = pf.prefcfg['canvas']

    def close():
        nonlocal dia
        dia.close()

    def reset():
        pass

    def setFgColor(fgcolor, save):
        if save:
            del pf.cfg['canvas/fgcolor']
            pf.prefcfg['canvas/fgcolor'] = fgcolor
        else:
            pf.cfg['canvas/fgcolor'] = fgcolor
        pf.canvas.setFgColor(fgcolor)

    def setSlColor(slcolor, save):
        if save:
            del pf.cfg['canvas/slcolor']
            pf.prefcfg['canvas/slcolor'] = slcolor
        else:
            pf.cfg['canvas/slcolor'] = slcolor
        pf.canvas.setSlColor(slcolor)

    def accept(save=False):
        nonlocal dia
        res = dia.results
        dia.close()
        setFgColor(res['fgcolor'], save)
        setSlColor(res['slcolor'], save)
        pf.canvas.update()

    def acceptAndSave():
        accept(save=True)

    def on_color_change(field=None):
        nonlocal dia
        if not dia.validate():
            return
        res = dia.results
        accept()

    dia = widgets.Dialog([
        _I('fgcolor', pf.canvas.settings.fgcolor, itemtype='color',
           text='Foreground color', func=on_color_change,
           tooltip='The default color used in drawing operations'),
        _I('slcolor', pf.canvas.settings.slcolor, itemtype='color',
           text='Highlight color', func=on_color_change,
           tooltip='The color used for selected items in picking operations'),
        ], actions=[
            ('Cancel', close),
            ('Accept for this session', accept),
            ('Accept and Save', acceptAndSave),
        ])
    dia.show()


def setLineWidth():
    """Change the default line width."""
    print(f"LINEWIDTH {pf.canvas.settings.linewidth}")
    res = draw.askItems([
        _I('Line Width', pf.canvas.settings.linewidth)
    ], caption='Choose default line width')
    print(res)
    if res:
        pf.canvas.setLineWidth(res['Line Width'])


def setCanvasSize():
    """Save the current viewport size"""
    res = draw.askItems([
        _I('w', pf.canvas.width()),
        _I('h', pf.canvas.height())
        ], caption='Canvas size')
    if res:
        draw.canvasSize(res['w'], res['h'])


def canvasSettings():
    """Interactively change the canvas settings.

    Creates a dialog to change the canvasSettings of the current or any other
    viewport
    """
    dia = None

    def close():
        dia.close()

    def getVp(vp):
        """Return the vp corresponding with a vp choice string"""
        if vp == 'current':
            vp = pf.GUI.viewports.current
        elif vp == 'focus':
            vp = pf.canvas
        else:
            vp = pf.GUI.viewports.all[int(vp)]
        return vp

    def on_change(field):
        if not dia.validate():
            return
        res = {field.key: dia.results[field.key]}
        apply_data(res)

    def apply_data(res):
        print(f"Changing Canvas settings: {res}")
        pf.canvas.settings.update(res, strict=False)
        pf.canvas.redrawAll()
        pf.canvas.update()

    def accept(save=False):
        if not dia.validate():
            return
        res = dia.results
        vp = getVp(res['viewport'])
        pf.debug("Changing Canvas settings for viewport %s to:\n%s"%(pf.GUI.viewports.viewIndex(vp), res), pf.DEBUG.CANVAS)
        pf.canvas.settings.update(res, strict=False)
        pf.canvas.redrawAll()
        pf.canvas.update()
        if save:
            res = utils.prefixDict(res, 'canvas/')
            print(res)
            res['_save_'] = save
            del res['canvas/viewport']
            updateSettings(res)

    def acceptAndSave():
        accept(save=True)

    def changeViewport(item):
        vp = item.value()
        if vp == 'current':
            vp = pf.GUI.viewports.current
        elif vp == 'focus':
            vp = pf.canvas
        else:
            vp = pf.GUI.viewports.all[int(vp)]
        dia.updateData(vp.settings)

    canv = pf.canvas
    vp = pf.GUI.viewports
    pf.debug("Focus: %s; Current: %s" % (canv, vp), pf.DEBUG.CANVAS)
    s = canv.settings

    vp_choices = ['focus', 'current'] + [
        str(i) for i in range(len(pf.GUI.viewports.all))]
    dia = widgets.Dialog(
        caption='Canvas settings',
        store=canv.settings, save=False,
        items=[
            _I('viewport', choices=vp_choices, func=changeViewport),
            _I('fgcolor', itemtype='color', func=on_change),
            _I('slcolor', itemtype='color', func=on_change),
            _I('pointsize', func=on_change),
            _I('linewidth', func=on_change),
            _I('linestipple',),
            _I('smooth'),
            _I('fill'),
            _I('lighting'),
            _I('culling'),
            _I('alphablend'),
            _I('transparency', min=0.0, max=1.0),
            _I('avgnormals',),
            ],
        enablers=[
            ('alphablend', ('transparency')),
            ],
        actions=[
            ('Close', close),
            ('Apply and Save', acceptAndSave),
            ('Apply', accept),
            ],
        )
    dia.show()


def viewportLayout():
    """Interactively set the viewport layout.

    Creates a dialog that allows the user to set the viewport layout.
    If the user accepts valid data, the viewport layout is changed
    accordingly. The contents of existing viewports remaining in the
    new layout is retained.
    """
    nvps = len(pf.GUI.viewports.all)
    directions = ['rowwise', 'columnwise']
    curdir = 0 if pf.GUI.viewports.rowwise else 1
    ncols = pf.GUI.viewports.ncols
    nrows = (nvps+ncols-1) // ncols
    if curdir == 1:
        nrows, ncols = ncols, nrows
    res = draw.askItems([
        _I('nvps', nvps, text='Number of viewports'),
        _I('dir', directions[curdir], text='Layout direction', choices=directions),
        _I('ncols', ncols, text='Number of columns'),
        _I('nrows', nrows, text='Number of rows'),
    ], enablers=[('dir', directions[0], 'ncols'), ('dir', directions[1], 'nrows')
    ], caption='Viewport configuration')

    if res:
        nvps = res['nvps']
        rowwise = directions.index(res['dir']) == 0
        if rowwise:
            ncols = res['ncols']
            nrows = None
        else:
            ncols = None
            nrows = res['nrows']
        pf.GUI.viewports.changeLayout(nvps, ncols, nrows)


def drawOptions(d={}):
    """Set the Drawing options.

    A dictionary may be specified to override the current defaults.
    """
    draw.setDrawOptions(d)
    #print(pf.canvas.drawoptions)
    res = draw.askItems(caption="Draw options",  items=[
        _I('view', choices=['None']+views.viewNames(),
           tooltip="Camera viewing direction"),
        _I('bbox', choices=['auto', 'last'],
           tooltip="Automatically focus/zoom on the last drawn object(s)"),
        _I('clear_', tooltip="Clear the canvas on each drawing action"),
        _I('shrink',
           tooltip="Shrink all elements to make their borders better visible"),
        _I('shrink_factor',
           tooltip="Shrink factor to use when shrink mode is active"),
        _I('wait', tooltip="Activate the draw lock, guaranteeing the rendering"
           "will be visible for some time ('drawdelay')"),
        _I('silent', tooltip="Silently ignore non-drawable objects"),
        ], store=pf.canvas.drawoptions, save=False,
    )
    if not res:
        return
    if res['view'] == 'None':
        res['view'] = None
    draw.setDrawOptions(res)


def cameraSettings():
    from pyformex.plugins import cameratools
    cameratools.showCameraTool()


def openglSettings():
    dia = None
    def apply_():
        if dia.validateData():
            canvas.glSettings(dia.results)
    def close():
        dia.close()

    dia = widgets.Dialog(caption='OpenGL settings', items=[
        _I('Line Smoothing', 'Off', itemtype='radio', choices=['On', 'Off']),
        _I('Polygon Mode', None, itemtype='radio', choices=['Fill', 'Line']),
        _I('Polygon Fill', None, itemtype='radio', choices=['Front and Back', 'Front', 'Back']),
        _I('Culling', 'Off', itemtype='radio', choices=['On', 'Off']),
        # These are currently set by the render mode
        #            ('Shading',None,'radio',{'choices':['Smooth','Flat']}),
        #            ('Lighting',None,'radio',{'choices':['On','Off']}),
    ], actions=[('Done', close), ('Apply', apply_)])
    dia.show()

def lineSmoothOn():
    canvas.glLineSmooth(True)

def lineSmoothOff():
    canvas.glLineSmooth(False)

def singleViewport(reset=True):
    draw.layout(1)
    if reset:
        draw.resetAll()


def clearAll():
    for vp in pf.GUI.viewports.all:
        vp.removeAll()
        vp.clearCanvas()
        vp.update()
    pf.app.processEvents()


def showObjectDialog(show=True):
    """Show the object dialog for the current scene.

    """
    from pyformex.opengl import objectdialog
    dia = objectdialog.objectDialog(pf.canvas.actors)
    if dia:
        if show:
            dia.show()
    else:
        print("There are no editable attributes in the current actors")
    return dia



MenuData = ('Viewport', [
    ('Clear', draw.clear),
    ('Clear All Viewports', clearAll),
    ('Remove Highlight', draw.removeHighlight),
    ('Axes Triade', setTriade),
    ('Canvas Grid', setGrid),
    ('Background Color', setBgColor),
    ('Viewport Colors', setColors),
    ('LineWidth', setLineWidth),
    ('Canvas Size', setCanvasSize),
    ('Canvas Settings', canvasSettings),
    ('Draw Options', drawOptions),
    ('Camera Settings', cameraSettings),
    ('OpenGL Settings', openglSettings),
    ('Redraw', draw.redraw),
    ('Object Dialog', showObjectDialog),
    ('Reset viewport', draw.reset),
    ('Reset layout', singleViewport),
    ('Change viewport layout', viewportLayout),
    ('Add new viewport', draw.addViewport),
    ('Remove last viewport', draw.removeViewport),
    ('Save', draw.saveCanvas),
    ('Load', draw.loadCanvas),
    ])


# TODO: Fix problems

# Viewport->Linewidth
# Viewport->Foreground Color
# Viewport->Highlight Color
# Viewport->Canvas Settings: change focus
# Viewport->Camera Settings: multiple failures
# Viewport->OpenGL Settings: multiple failures


def create_menu():
    """Create the plugin menu."""


# End
