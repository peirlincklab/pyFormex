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
"""Functions for the Pref menu.

"""
import pyformex as pf
from pyformex import utils
from pyformex import gui
from pyformex import plugins
from pyformex.gui import widgets, toolbar, draw
from pyformex.main import savePreferences
from pyformex.gui.draw import _I, _G, _C, _T


def updateSettings(res, save=None):
    """Update the current settings (store) with the values in res.

    res is a dictionary with configuration values.
    The current settings will be updated with the values in res.

    If res contains a key '_save_', or a `save` argument is supplied,
    and its value is True, the preferences will also be saved to the
    user's preference file.
    Else, the user will be asked whether he wants to save the changes.
    Add '_save_:False' to res or use save=False to not save and not
    being asked.
    """
    pf.debug("\nACCEPTED SETTINGS\n%s"% res, pf.DEBUG.CONFIG)
    if save is None:
        save = res.get('_save_', None)
    if save is None:
        save = draw.ack("Save the current changes to your configuration file?")

    # Do not use 'pf.cfg.update(res)' here!
    # It will not work with our Config class!

    todo = set([])  # a set to uniquely register updatefunctions
    if save:
        print("Settings: set and saved")
    else:
        print("Settings: set for this session only")
    for k in res:
        if k.startswith('_'):  # skip temporary variables
            continue
        changed = False

        # first try to set in prefs, as these will cascade to cfg
        if save and pf.prefcfg[k] != res[k]:
            print(f" prefcfg: {k} = {res[k]}")
            # TODO, we could do a check if pf.prefcfg[k] == pf.refcfg[k],
            # and if so, delete pf.prefcfg[k]
            pf.prefcfg[k] = res[k]
            # We delete pf.cfg[k] here, to avoid having to set it twice
            if k in pf.cfg:
                del pf.cfg[k]
            changed = True

        # if not saved, set in cfg
        if pf.cfg[k] != res[k]:
            print(f" cfg: {k} = {res[k]}")
            pf.cfg[k] = res[k]
            changed = True

        if changed and pf.GUI:
            # register the corresponding update function
            if k in _activate_settings:
                todo.add(_activate_settings[k])

    # We test for pf.GUI in case we want to call updateSettings before
    # the GUI is created
    if pf.GUI:
        for f in todo:
            try:
                f()
            except Exception as e:
                print('!' * 72)
                print("Got an exception while updating settings with %s" % f)
                print(e)

    pf.debug("\nNEW SETTINGS\n%s"%pf.cfg, pf.DEBUG.CONFIG)
    pf.debug("\nNEW PREFERENCES\n%s"%pf.prefcfg, pf.DEBUG.CONFIG)
    savePreferences()


def settings():
    """Interactively change the pyformex settings.

    Creates a dialog to change (most of) the pyformex user configuration.
    To change the canvas setttings, use menus.Viewport.canvasSettings.
    """
    from pyformex.opengl import canvas
    from pyformex import sendmail
    from pyformex.elements import ElementType

    dia = None
    _actionbuttons = pf.cfg['gui/all_actionbuttons']
    #print(f"{_actionbuttons=}")
    #_actionbuttons = ['play', 'rerun', 'step', 'continue', 'stop', 'edit', 'info']
    #print(f"{_actionbuttons=}")

    # gui_console_options = {'n': 'New PyConsole (default)', 'b': 'Message board only', 'c': 'Console only', 'bc': 'Message board and Console'}

    def close():
        dia.close()

    def accept(save=False):
        if not dia.validate():
            print("Invalid data! Changes not accepted!")
            return
        res = dia.results
        dia.close()
        res['_save_'] = save
        ok_plugins = utils.subDict(res, '_plugins/')
        res['gui/pluginmenus'] = [p for p in ok_plugins if ok_plugins[p]]
        res['gui/actionbuttons'] = [t for t in _actionbuttons if res['_gui/%sbutton'%t]]
        if res['webgl/script'] == 'custom':
            res['webgl/script'] = res['_webgl_script']
        if res['webgl/guiscript'] == 'custom':
            res['webgl/guiscript'] = res['_webgl_guiscript']
        updateSettings(res)

    def acceptAndSave():
        accept(save=True)

    def autoSettings(keylist):
        return [_I(k, pf.cfg[k]) for k in keylist]

    def changeDirs(dircfg):
        """dircfg is a config variable that is a list of dirs"""
        setDirs(dircfg)
        dia.updateData({dircfg: pf.cfg[dircfg]})

    def changeScriptDirs():
        changeDirs('scriptdirs')
    def changeAppDirs():
        changeDirs('appdirs')

    enablers = []

    # Use _ to avoid adding these items in the config
    plugin_items = [_I('_plugins/'+name, name in pf.cfg['gui/pluginmenus'], text=text) for name, text in plugins.PluginMenu.list()]

    ##### GENERAL settings #####
    general_settings = [
        _I('syspath', tooltip="If you need to import modules from a non-standard path, you can supply additional paths to search here."),
        _I('editor', tooltip="The command to be used to edit a script file. The command will be executed with the path to the script file as argument."),
        _I('viewer', tooltip="The command to be used to view an HTML file. The command will be executed with the path to the HTML file as argument."),
        _I('browser', tooltip="The command to be used to browse the internet. The command will be executed with an URL as argument."),
       # Don't do this: it makes the dialog way too wide!
       # _I('help/docs'),
        _I('autorun', text='Startup script', tooltip='This script will automatically be run at pyFormex startup'),
        _I('scriptdirs', text='Script Paths', tooltip='pyFormex will look for scripts in these directories', buttons=[('Edit', changeScriptDirs)]),
        _I('appdirs', text='Applicationt Paths', tooltip='pyFormex will look for applications in these directories', buttons=[('Edit', changeAppDirs)]),
        _I('autoglobals', text='Auto Globals', tooltip='If checked, global Application variables of any Geometry type will automatically be copied to the pyFormex global variable dictionary (PF), and thus become available in the GUI'),
        _I('showapploaderrors', text='Show Application Load Error Traceback', tooltip='Show a traceback of exceptions occurring at Application Load time instead of just ignoring failing apps.'),
        _I('openlastproj', text="Reload last project on startup"),
        _I('plot2d', text="Prefered 2D plot library", choices=['matplotlib', 'gnuplot']),
    ]

    ##### STARTUP settings #####
    # Make sure splash image exists
    cur = pf.cfg['gui/splash']
    if not cur.exists():
        pf.cfg['gui/splash'] = cur = pf.refcfg['gui/splash']
    splashviewer = widgets.ImageView(cur, maxheight=200)
    bindings_choices = ('any',) + gui.BINDINGS
    bindings_current = pf.cfg['gui/bindings'].lower()
    startup_settings = [
        _I('_info_01_', 'The settings on this page will only become active after restarting pyFormex', itemtype='info'),
        _I('gui/bindings', bindings_current, choices=bindings_choices, tooltip="The Python bindings for the Qt libraries"),
        _I('gui/splash', text='Splash image', itemtype='filename', filter='img', mode='exist', preview=splashviewer),
        splashviewer,
    ]
    ##### GUI settings #####
    gui_appearance = [
        _I('gui/style', pf.app.currentStyle(), choices=pf.app.getStyles()),
        _I('gui/font', pf.app.font().toString(), 'font'),
        # _I('gui/fontfamily', pf.app.font().family()),
        # _I('gui/fontsize', pf.app.font().pointSize()),
        ]
    toolbartip = "Currently, changing the toolbar position will only be in effect when you restart pyFormex"
    gui_components = [
        _I('gui/%s'%t, pf.cfg['gui/%s'%t], text=getattr(pf.GUI, t).windowTitle(), choices=['left', 'right', 'top', 'bottom'], itemtype='radio', tooltip=toolbartip) for t in ['camerabar', 'modebar', 'viewbar']
        ]
    # Use _ to avoid adding these items in the config
    gui_buttons = [
        _I('_gui/%sbutton'%t, t in pf.cfg['gui/actionbuttons'], text="%s Button" % t.capitalize()) for t in _actionbuttons
        ]
    gui_options1 = [
        _I('gui/redirect', pf.cfg['gui/redirect'], choices=['oe','o','e','']),
        _I('gui/coordsbox'),
        _I('gui/shrinkbutton', pf.cfg['gui/shrinkbutton']),
        _I('gui/timeoutbutton', pf.cfg['gui/timeoutbutton']),
        _I('gui/timeoutvalue', pf.cfg['gui/timeoutvalue']),
    ]
    gui_options2 = [
        _I('gui/buttonsattop', pf.cfg['gui/buttonsattop']),
        _I('gui/smart_placement', pf.cfg['gui/showfocus']),
        _I('gui/allow_old_dialog_items', pf.cfg['gui/allow_old_dialog_items']),
        _I('gui/easter_egg', pf.cfg['gui/easter_egg']),
    ]
    gui_settings = [
        _G('Appearance', gui_appearance),
        _G('Components', [
            _C('col1', gui_components,),
            _C('col2', gui_buttons, spacer='l'),
        ]),
        _G('Options', [
            _C('col1',gui_options1,),
            _C('col2',gui_options2, spacer='l'),
        ]),
    ]

    ##### CANVAS settings #####
    canvas_settings = [
        _I('gui/frontview', pf.cfg['gui/defviews'], itemtype='hradio', choices=['xy', 'xz'], tooltip="Axes defining the front view"),
        _I('gui/showfocus', pf.cfg['gui/showfocus']),
        _I('_not_active_', 'More canvas settings can be set from the Viewport Menu', itemtype='info', text=''),
    ]

    ##### DRAWING settings #####
    drawing_settings = [
        _I('draw/rendermode', pf.cfg['draw/rendermode'], choices=list(canvas.CanvasSettings.RenderProfiles)),
        _I('draw/wait', pf.cfg['draw/wait']),
        _I('draw/picksize', pf.cfg['draw/picksize']),
        _I('draw/disable_depth_test', pf.cfg['draw/disable_depth_test'], text='Disable depth testing for transparent actors'),
        _I('render/avgnormaltreshold', pf.cfg['render/avgnormaltreshold']),
        _I('_info_00_', '', itemtype='info', text='Changes to the options below will only become effective after restarting pyFormex!'),
        _I('draw/quadline', text='Draw as quadratic lines', itemtype='select', check=True, choices=ElementType.list(1), tooltip='Line elements checked here will be drawn as quadratic lines whenever possible.'),
        _I('draw/quadsurf', text='Draw as quadratic surfaces', itemtype='select', check=True, choices=ElementType.list(2)+ElementType.list(3), tooltip='Surface and volume elements checked here will be drawn as quadratic surfaces whenever possible.'),

    ]
    ##### MOUSE settings #####
    mouse_settings = autoSettings(['gui/rotfactor', 'gui/panfactor', 'gui/zoomfactor', 'gui/autozoomfactor', 'gui/dynazoom', 'gui/wheelzoom', 'gui/wheelzoomfactor'])


    ##### WEBGL settings #####
    scripts = [
        pf.cfg['webgl/script'],
#        "https:///fewgl-0.2.js",
#        (pf.cfg['datadir'] / 'fewgl.js').as_uri(),
        ]
    if pf.installtype == 'G':
        fewgl_dir = pf.pyformexdir.parent / "fewgl"
        if fewgl_dir.exists():
            scripts += [(fewgl_dir / f).as_uri() for f in ['fewgl.js', 'fewgl_debug.js']]
    scripts.append('custom')
    guiscripts = [
        pf.cfg['webgl/guiscript'],
        #        "https://net.feops.com/public/webgl/xtk_xdat.gui.js",
        #       (pf.cfg['datadir'] / 'xtk_xdat.gui.js').as_uri(),
        ]
    guiscripts.append('custom')
    webgl_settings = [
        _I('webgl/script', pf.cfg['webgl/script'], text='WebGL base script', choices=scripts),
        _I('_webgl_script', '', text='URL for local WebGL base script', itemtype='filename', filter='js', mode='exist'),
        _I('webgl/guiscript', pf.cfg['webgl/guiscript'], text='GUI base script', choices=guiscripts),
        _I('_webgl_guiscript', '', text='URL for local GUI base script'),
        _I('webgl/autogui', pf.cfg['webgl/autogui'], text='Always add a standard GUI'),
        _I('webgl/devel', pf.cfg['webgl/devel'], text='Use the pyFormex source WebGL script'),
        _I('webgl/devpath', pf.cfg['webgl/devpath'], text='Path to the pyFormex source WebGL script'),
        ]
    enablers.extend([
        ('webgl/script', 'custom', '_webgl_script'),
        ('webgl/guiscript', 'custom', '_webgl_guiscript'),
        ('webgl/devel', True, 'webgl/devpath'),
        ])

    ##### ENVIRONMENT settings #####
    mail_settings = [
        _I('mail/sender', pf.cfg['mail/sender'], text="My mail address"),
        _I('mail/server', pf.cfg['mail/server'], text="Outgoing mail server")
        ]
    environment_settings = [
        _G('Mail', mail_settings),
        # _G('Jobs',jobs_settings),
    ]
    dia = widgets.Dialog(
        caption='pyFormex Settings',
        store=pf.cfg, save=False,
        scroll=True,        # This may have some large input pages
        size=(0.6, 0.9),
        buttonsattop=True,  # Put buttons at top (For all users)
        items=[
            _T('General', general_settings),
            _T('Startup', startup_settings),
            _T('GUI', gui_settings),
            _T('Canvas', canvas_settings),
            _T('Drawing', drawing_settings),
            _T('Mouse', mouse_settings),
            _T('Plugins', plugin_items),
            _T('WebGL', webgl_settings),
            _T('Environment', environment_settings),
        ],
        # enablers=enablers,
        actions=[
            ('Cancel', close),
            ('Accept for this session', accept),
            ('Accept and Save', acceptAndSave),
        ],
    )
    dia.show()


def askConfigPreferences(items, prefix=None, store=None):
    """Ask preferences stored in config variables.

    Items in list should only be keys. store is usually a dictionary, but
    can be any class that allow the setdefault method for lookup while
    setting the default, and the store[key]=val syntax for setting the
    value.
    If a prefix is given, actual keys will be 'prefix/key'.
    The current values are retrieved from the store, and the type returned
    will be in accordance.
    If no store is specified, the global config pf.cfg is used.

    This function can be used to change individual values by a simpler
    interface than the full settings dialog.
    """
    if store is None:
        store = pf.cfg
    if prefix:
        items = ['%s/%s' % (prefix, i) for i in items]
    itemlist = [_I(i, store[i]) for i in items] + [
        _I('_save_', True, text='Save changes')
        ]
    res = widgets.Dialog(itemlist, caption='pyFormex User Preferences').getResults()
    #pf.debug(res,pf.DEBUG.CONFIG)
    if res and store==pf.cfg:
        updateSettings(res)
    return res


def set_mat_value(field):
    key = field.text().replace('material/', '')
    val = field.value()
    vp = pf.GUI.viewports.current
    mat = vp.material
    mat.setValues(**{key: val})
    #print vp.material
    #vp.resetLighting()
    vp.update()


def setRendering():
    """Interactively change the render parameters.

    """
    from pyformex.opengl import canvas

    vp = pf.GUI.viewports.current
    dia = None

    def set_render_value(field):
        key = field.name()
        val = field.value()
        updateSettings({key: val}, save=False)
        vp = pf.GUI.viewports.current
        vp.resetLighting()
        vp.update()

    def enableLightParams(mode):
        if dia is None:
            return
        mode = str(mode)
        on = mode.startswith('smooth')
        for f in ['ambient', 'material']:
            dia['render/'+f].setEnabled(on)
        dia['material'].setEnabled(on)

    def updateLightParams(item):
        if dia is None:
            return
        matname = item.value()
        mat = pf.GUI.materials[matname]
        val = utils.prefixDict(mat.dict(), 'material/')
        dia.updateData(val)

    def close():
        dia.close()

    def accept(save=False):
        if not dia.validate():
            return
        print("RESULTS", dia.results)
        if dia.results['render/mode'].startswith('smooth'):
            res = utils.subDict(dia.results, 'render/', strip=False)
            matname = dia.results['render/material']
            matdata = utils.subDict(dia.results, 'material/')
            # Currently, set both in cfg and Material db
            pf.cfg['material/%s' % matname] = matdata
            pf.GUI.materials[matname] = canvas.Material(matname, **matdata)

            for i in range(4):
                key = 'light/light%s' % i
                res[key] = utils.subDict(dia.results, key+'/', strip=True)
        else:
            res = utils.selectDict(dia.results, ['render/mode', 'render/lighting'])
        res['_save_'] = save
        #print("RES", res)
        updateSettings(res)
        #print(pf.cfg)
        vp = pf.GUI.viewports.current
        vp.resetLighting()
        #if pf.cfg['render/mode'] != vp.rendermode:
        print("SETMODE %s %s" % (pf.cfg['render/mode'], pf.cfg['render/lighting']))
        vp.setRenderMode(pf.cfg['render/mode'], pf.cfg['render/lighting'])
        #print(vp.rendermode,vp.settings.lighting)
        vp.update()
        toolbar.updateLightButton()

    def acceptAndSave():
        accept(save=True)

    def changeLight(field):
        print(field)
        accept()

    def createDialog():
        matnames = list(pf.GUI.materials.keys())
        mat = vp.material
        print("createDialog: %s" % vp.settings.lighting)

        #light0 = {'enabled':True,'ambient':0.0,'diffuse':0.6,'specular':0.4,'position':(1., 1., 2., 0.)}
        light_items = []
        for i in range(4):
            name = 'light%s' % i
            light = pf.cfg['light/%s'%name]
            items = _T(name, [
                _I("enabled", text="Enabled", value=light['enabled']),
                _I("ambient", text="Ambient", value=light['ambient'],
                    itemtype='color', func=changeLight),
                _I("diffuse", text="Diffuse", value=light['diffuse'],
                    itemtype='color', func=changeLight),
                _I("specular", text="Specular", value=light['specular'],
                    itemtype='color', func=changeLight),
                _I("position", text="Position", value=light['position'][:3],
                    itemtype='point'),
                ])
            light_items.append(items)

        items = [
            _I('render/mode', vp.rendermode, text='Rendering Mode',
                choices=draw.renderModes()),  # ,func=enableLightParams),
            _I('render/lighting', vp.settings.lighting, text='Use Lighting'),
            _I('render/ambient', vp.lightprof.ambient, itemtype='slider',
                min=0, max=100, scale=0.01, func=set_render_value,
               text='Global Ambient Lighting'),
            _G('light', text='Lights', items=light_items),
            _I('render/material', vp.material.name, text='Material',
                choices=matnames, func=updateLightParams),
            _G('material', text='Material Parameters', items=[
                _I(a, text=a, value=getattr(mat, a), itemtype='slider',
                    min=0, max=100, scale=0.01,
                    func=set_mat_value) for a in [
                        'ambient', 'diffuse', 'specular', 'emission']] + [
                _I(a, text=a, value=getattr(mat, a), itemtype='slider',
                    min=1, max=128, scale=1.,
                   func=set_mat_value) for a in ['shininess']
                ]),
            ]

        enablers = [
            ('render/lighting', True, 'render/ambient', 'render/material', 'material'),
            ]
        dia = widgets.Dialog(
            caption='pyFormex Render Settings',
            enablers = enablers,
            #store=pf.cfg, save=False,
            items=items,
            #prefix='render/',
            autoprefix=True,
            actions=[
                ('Cancel', close),
                ('Apply and Save', acceptAndSave),
                ('Apply for this session', accept),
                ]
            )
        enableLightParams(vp.rendermode)
        return dia

    dia = createDialog()
    dia.show()


def addAppdir(path, name=None, dircfg='appdirs'):
    """Add a path to the appdirs"""
    from pyformex.gui import appMenu
    if path.is_dir():
        p = path
    else:
        p = path.parent
    if not p.is_dir():
        print("Invalid path: %s" % path)
        return
    if name is None:
        name = p.name.capitalize()
    pf.prefcfg[dircfg].append((name, p))
    appMenu.reloadMenu(mode=dircfg[:-4])


def setDirs(dircfg):
    """Configure the paths from which to read apps/scripts

    Parameters
    ----------
    dircfg: str
        The name of a config variable that holds a list of directories.
        It should be one of 'appdirs' or 'scriptdirs'.
        The config value should be a list of tuples ('label','path').
    """
    _dia = None
    _table = None

    mode = dircfg[:-4]
    if mode == 'app':
        title = 'Application paths'
    else:
        title='Script paths'

    def insertRow():
        fn = draw.askDirname(pf.cfg['workdir'], change=False)
        if fn:
            _table.model().insertRows()
            _table.model()._data[-1] = [fn.name.capitalize(), fn]
        _table.update()

    def removeRow():
        row = _table.currentIndex().row()
        _table.model().removeRows(row, 1)
        _table.update()

    def moveUp():
        row = _table.currentIndex().row()
        if row > 0:
            a, b = _table.model()._data[row-1:row+1]
            _table.model()._data[row-1:row+1] = b, a
        _table.setFocus()  # For some unkown reason, this seems needed to
                          # immediately update the widget
        _table.update()
        pf.app.processEvents()

    def reloadMenu():
        if _dia.validate():
            data = [tuple(d) for d in _dia.results[dircfg]]
            pf.prefcfg[dircfg] = pf.cfg[dircfg] = [tuple(d) for d in data]
            pf.debug(f"Set {dircfg} to {pf.prefcfg[dircfg]}", pf.DEBUG.CONFIG)
            from pyformex.gui import appMenu
            appMenu.reloadMenu(mode=mode)

    def close():
        _dia.close()

    data = [list(c) for c in pf.cfg[dircfg]]
    _dia = widgets.Dialog(caption=title, items = [
        _I(dircfg, data, itemtype='table', chead = ['Label', 'Path']),
    ], actions = [
        ('New', insertRow),
        ('Delete', removeRow),
        ('Move Up', moveUp),
        ('Apply', reloadMenu),
        ('Close', close),
    ])
    _table = _dia[dircfg].input
    _dia.show()

    return _dia


def setDebug():
    options = [i.name for i in pf.DEBUG]
    options.remove('ALL')
    options.remove('NONE')
    items = [_I(o, pf.DEBUG[o] in pf.options.debuglevel) for o in options]
    n = (len(options)+1) // 2
    cols = [_C('col', items[:n]), _C('col', items[n:]), ]
    res = draw.askItems(cols)
    if res:
        debug = pf.DEBUG.level([o for o in res if res[o]])
        print(f"Setting debuglevel to {debug}")
        pf.options.debuglevel = debug


def resetWarnings():
    """Reset the warning filters to the default."""
    if draw.showWarning('This will remove all your warning filters and return them to factory defaults. This may only become effective in your next session.', actions=['Cancel', 'OK']) == 'OK':
        del pf.prefcfg['warnings/filters']
        # There should never be such a value, but just in case:
        del pf.cfg['warnings/filters']
        # Reload the filters here to activate the new setting
        utils.resetWarningFilters()


def resetDefaults():
    if draw.showWarning('This will reset all the current pyFormex settings to your stored defaults.', actions=['Cancel', 'OK']) == 'OK':
        pf.cfg.clear()


def resetFactory():
    if draw.showWarning('Beware! This will throw away all your personalized pyFormex settings and return to the shipped default settings.\nSome settings may only become active after you restart pyFormex.', actions=['Cancel', 'OK']) == 'OK':
        pf.cfg.clear()
        pf.prefcfg.clear()

# Functions defined to delay binding

def updateDefViews():
    pf.GUI.setViewButtons(pf.cfg['gui/frontview'])

def coordsbox():
    """Toggle the coordinate display box on or off"""
    pf.GUI.coordsbox.setVisible(pf.cfg['gui/coordsbox'])

def timeoutbutton():
    """Toggle the timeout button on or off"""
    toolbar.addTimeoutButton(pf.GUI.toolbar)

def updateCanvas():
    pf.canvas.update()

def updateStyle():
    pf.app.setAppearance()

def updateToolbars():
    pf.GUI.updateToolBars()

def updatePlugins():
    plugins.loadConfiguredPlugins()

def updateBackground():
    pf.canvas.update()

def updateAppdirs():
    pf.GUI.updateAppdirs()

def updateDrawWait():
    pf.GUI.drawwait = pf.cfg['draw/wait']

def updateQtBindings():
    pf.warning("You changed the Python Qt bindings setting to '%s'.\nThis setting will only become active after you restart pyFormex." % pf.cfg['gui/bindings'])


# This sets the functions that should be called when a setting has changed
_activate_settings = {
    'gui/bindings': updateQtBindings,
    'gui/coordsbox': coordsbox,
    'gui/frontview': updateDefViews,
    'gui/timeoutbutton': timeoutbutton,
    'gui/showfocus': updateCanvas,
    'gui/style': updateStyle,
    'gui/font': updateStyle,
    'gui/camerabar': updateToolbars,
    'gui/viewbar': updateToolbars,
    'gui/modebar': updateToolbars,
    'gui/pluginmenus': updatePlugins,
    'canvas/bgmode': updateBackground,
    'canvas/bgcolor': updateBackground,
    'canvas/bgimage': updateBackground,
    'appdirs': updateAppdirs,
    'draw/wait': updateDrawWait,
    }

def setDrawWait():
    askConfigPreferences(['draw/wait'])


# We have a parameter here because it is used in a file watcher
def reloadPreferences(preffile=None):
    """Reload the preferences from the user preferences file"""
    if preffile is None:
        preffile = pf.preffile
    if preffile:
        pf.prefcfg.load(preffile)


def editPreferences():
    """Edit the preferences file

    This allows the user to edit all his stored preferences through his
    normal editor. The current preferences are saved to the user preferences
    file before it is loaded in the editor. When the user saves the
    preferences file, the stored preferences will be reloaded into
    pyFormex. This will remain active until the user selects the
    'File->Save Preferences Now' option from the GUI.
    """
    if pf.preffile is None:
        pf.warning("You have no writable preferences file")
        return

    if not savePreferences():
        if pf.warning("Could not save to preferences file %s\nEdit the file anyway?" % pf.preffile) == 'Cancel':
            return

    pf.GUI.filewatch.addWatch(pf.preffile, reloadPreferences)
    P = draw.editFile(pf.preffile)
    # TODO: Unfinished, untested


def saveAndUnwatchPreferences():
    """Save the current preferences to the user preferences file.

    This also has the side effect of no longer watching the preferences
    file for changes, if the user has loaded it into the editor.
    """
    if pf.preffile:
        pf.GUI.filewatch.removeWatch(pf.preffile)
        savePreferences()


def reloadAndUnwatchPreferences():
    """Reload the current preferences from the user preferences file.

    This also has the side effect of no longer watching the preferences
    file for changes, if the user has loaded it into the editor.
    """
    if pf.preffile:
        pf.GUI.filewatch.removeWatch(pf.preffile)
        reloadPreferences()


MenuData = ('Settings', [
    ('Settings Dialog', settings),
    ('Debug', setDebug),
    # ('Options', setOptions),
    ('Draw Wait', setDrawWait),
    ('Rendering Params', setRendering),
    ('Reset Warning Filters', resetWarnings),
    ('Reset to My Defaults', resetDefaults),
    ('Reset to Factory Defaults', resetFactory),
    ('---', None),
    ('Edit Preferences File', editPreferences),
    ('Save Preferences', saveAndUnwatchPreferences),
    ('Reload Preferences', reloadAndUnwatchPreferences),
    ])

# End
