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
"""Toolbars for the pyFormex GUI.

This module defines the functions for creating the pyFormex window toolbars.
"""
import pyformex as pf
from pyformex import utils
from pyformex.gui import QtGui, QPixmap
from pyformex.gui import widgets


############################## functions for the pick button ############


def pick(mode, *, tool='pix', filter=None, oneshot=False,
         func=None, pickable=None, prompt=None, _rect=None, minobj=0,
         **kargs):
    """Enter interactive picking mode and return selection.

    See :func:`gui.qtcanvas.Canvas.pick` for more details.
    This function differs in that it provides an extra interactive interface
    in the statusbar: OK/Cancel buttons to stop the picking operation,
    and comboboxes to change the picking tool and filters.

    Parameters
    ----------
    mode: str
        Defines what to pick : one of 'actor', 'element' or 'point'.
        'actor' picks complete actors. 'element' picks elements from one or
        more actor(s). 'point' picks points of Formices or nodes of Meshes.
    tool: str
        Defines what picking tool to use. One of 'pix', 'any' or 'all'.
        With 'pix' items are picked if they have any visible pixels in the
        pick rectangle. With 'any', items are picked if any of their points
        are inside the pick rectangle. With 'all', items are picked if all
        their points are inside the rectangle.
    filter: str
        The picking filter that is activated on entering the pick mode.
        It should be one of the Canvas.selection_filters: 'none', 'single',
        'closest', 'connected'.
        The active filter can be changed from a combobox in the statusbar.
        The available filters depend on the picking tool.
    oneshot: bool.
        If True, the function returns as soon as the user ends
        a picking operation. The default is to let the user
        modify his selection and to return only after an explicit
        cancel (ESC or right mouse button).
    func: callable, optional
        If specified, this function will be called after each
        atomic pick operation. The Collection with the currently selected
        objects is passed as an argument. This can e.g. be used to highlight
        the selected objects during picking.
    pickable: list of Actors, optional
        List of Actors from which can be picked. The default is to use
        a list with all Actors having the pickable=True attribute (which is
        the default for newly constructed Actors).
    prompt: str
        The text printed to prompt the user to start picking. If None,
        a default prompt is printed. Specify an empty string to avoid printing
        a prompt.
    minobj: int

    Returns
    -------
    Collection
        A (possibly empty) Collection with the picked items.
        After return, the value of the pf.canvas.selection_accepted variable
        can be tested to find how the picking operation was exited:
        True means accepted (right mouse click, ENTER key, or OK button),
        False means canceled (ESC key, or Cancel button). In the latter case,
        the returned Collection is always empty. Ther returned Collection
        also remains available in pf.canvas.selection until a new pick is
        started.
    """
    from pyformex.gui import draw

    def _tool_filter_choices(tool):
        """Return the possible selection filters for the tool"""
        if mode == 'element':
            filters = pf.canvas.selection_filters
        else:
            filters = pf.canvas.selection_filters[:3]
        return filters

    def _set_selection_filter(item):
        """Set the selection filter mode

        This function is used to change the selection filter from the
        selection InputCombo widget.
        s is one of the strings in selection_filters.
        """
        s = item.value()
        if pf.canvas.pick_mode is not None and s in pf.canvas.selection_filters:
            # filter changed during picking: restart
            pf.canvas.start_selection(None, pf.canvas.pick_tool, s)

    def _set_pick_tool(item):
        """Set the value of the pick tool (first 3 chars)"""
        nonlocal filters, filter_combo, tool
        pf.canvas.pick_tool = item.value()[:3].lower()
        filters = _tool_filter_choices(tool)
        #print("CHANGE FILTERS",tool,filters)
        filter_combo.setChoices(filters)
        filter_combo.setValue(filters[0])

    if pf.canvas.pick_mode is not None:
        draw.warning("You need to finish the previous picking operation first!")
        return

    if mode not in pf.canvas.pick_modes:
        draw.warning(f"Invalid picking {mode=}. "
                     f"Expected one of {pf.canvas.pick_modes=}")
        return

    pick_buttons = widgets.ButtonBox('Selection:', [
        ('Cancel', pf.canvas.cancel_selection),
        ('OK', pf.canvas.accept_selection)])
    # combobox for filter selection
    filters = _tool_filter_choices(tool)
    filter_combo = widgets.InputCombo(
        'Filter:', None, choices=filters, func=_set_selection_filter)
    if filter is not None and filter in filters:
        filter_combo.setValue(filter)
    # combobox for tool switching
    pick_tools = {'pix': 'Pixels', 'any': 'Any Point', 'all': 'All Points'}
    txt = pick_tools[tool]
    tool_combo = widgets.InputCombo(
        'Pick by ', txt, choices=list(pick_tools.values()),
        func=_set_pick_tool)

    if prompt is None:
        prompt = f"Pick: Mode {mode}; Tool {tool}; Filter {filter}"
    if prompt:
        print(prompt)
    pf.GUI.statusbar.addWidget(pick_buttons)
    pf.GUI.statusbar.addWidget(filter_combo)
    pf.GUI.statusbar.addWidget(tool_combo)
    try:
        if pf.debugon(pf.DEBUG.PICK):
            print(f"PICK {mode=}, {tool=}, {func=}, {filter=}, "
                  f"{pickable=}, {_rect=}, {minobj=}")
        sel = pf.canvas.pick(mode, tool, oneshot, func,
                                 filter, pickable, _rect, minobj)
    finally:
        # cleanup
        if pf.canvas.pick_mode is not None:
            pf.canvas.finish_selection()
        pf.GUI.statusbar.removeWidget(pick_buttons)
        pf.GUI.statusbar.removeWidget(filter_combo)
        pf.GUI.statusbar.removeWidget(tool_combo)
    return sel


def picksel(obj_type, **kargs):
    """Pick and print selection"""
    sel = pick(obj_type, **kargs)
    print(sel)


def report_func(self):
    from pyformex.plugins import tools
    self.removeHighlight()
    self.highlightSelection(self.picked)
    print(tools.report(self.picked))


def query(obj_type, **kargs):
    """Enter interactive query mode.

    Enters a continuous picking mode where the user can pick objects
    and the picked objects are reported in detail. This is usually called
    from the toolbar Query buttons. The query mode stays active until
    the user cancels pick mode (with ESC or right mouse button). distan

    Parameters
    ----------
    obj_type: str
        Defines what to pick : one of 'actor', 'element' or 'point'
    **kargs:
        Extra parameters to be passed to :func:`pick`
    """
    return pick(obj_type, func=report_func, **kargs)


# TODO: we could have a mode that shows distance on every point selected
def query_distance(colorid=0, colorstep=1, show=True, prec=None):
    """Enter interactive distance query mode

    In distance query mode, the user picks subsequent single points.
    For every second point picked, the distance to the previous point
    is shown. The distances are shown and printed with subsequent colors
    from the canvas default colormap or from a custom colormap in
    pf.cfg['draw/querypalette'].
    """
    import numpy as np
    from pyformex.formex import Formex
    from pyformex.gui import draw
    if prec is None:
        prec = np.get_printoptions()['precision']

    def every2_showdistance(self):
        nonlocal points, colorid, drawn
        if not self.picked:
            return
        k, i = next(self.picked.singles())
        self.actors[k].addHighlightPoints(np.array([i]))
        P = self.actors[k].object.points()[i]
        print(f"Actor {k}, point {i}, coords {P}")
        points.append([k, i, P])
        if len(points) % 2 == 0:
            P0, P1 = (points[i][2] for i in range(-2, 0))
            d = P1.distanceFromPoint(P0)
            draw.printc(f"Distance: {d:.{prec}}", color=colorid)
            if show:
                lines = draw.draw(
                    Formex([[P0, P1]]), linewidth=2, color=colorid,
                    rendertype=4, ontop=True, bbox='last', view=None)
                marks = draw.drawMarks(
                    [0.5 * (P0 + P1)], [f"={d:.{prec}}"], size=20, color=colorid)
                pf.canvas.update()
                drawn.extend([lines, marks])
            colorid += colorstep

    points=[]
    drawn = []
    print("Pick single points, every 2nd shows distance")
    print(f"{pf.cfg['draw/querypalette']=}")
    with draw.TempPalette(pf.cfg['draw/querypalette']):
        pick('point', filter='closest', func=every2_showdistance, prompt='')
    return {'points': points, 'drawn': drawn}


def query_angle(colorid=0, colorstep=1, show=True, prec=None):
    """Enter interactive angle query mode

    In angle query mode, the user picks subsequent single points.
    For every third point picked, the angle between the vectors from
    first to second and from secont to third is shown.
    The angles are shown and printed with subsequent colors
    from the canvas default colormap or from a custom colormap in
    pf.cfg['draw/querypalette'].
    """
    import numpy as np
    from pyformex.formex import Formex
    from pyformex.gui import draw
    from pyformex import geomtools as gt
    if prec is None:
        prec = np.get_printoptions()['precision']

    def angle_report(P0, P1, P2, color):
        angle, n = gt.rotationAngle(P0-P1, P2-P1)
        angle, n = angle[0], n[0]
        draw.printc(f"Angle: {angle:.{prec}} degrees, axis: {n}",
                        color=color)
        lines = draw.draw(Formex([[P0, P1],[P1, P2]]), linewidth=3, color=color,
                          rendertype=4, ontop=True, bbox='last', view=None)
        marks = draw.drawMarks([(P0+P1+P2)/3], [f"{angle:.{prec}}"], size=20,
                               color=color, gravity='')
        pf.canvas.update()
        return [lines, marks]

    def every3_showangle(self):
        nonlocal points, colorid, drawn, temp
        if not self.picked:
            return
        k, i = next(self.picked.singles())
        self.actors[k].addHighlightPoints(np.array([i]))
        P = self.actors[k].object.points()[i]
        print(f"Actor {k}, point {i}, coords {P}")
        points.append([k, i, P])
        if len(points) % 3 == 2:
            P0, P1 = (points[i][2] for i in range(-2, 0))
            temp = draw.draw(Formex([[P0, P1]]), linewidth=3,
                             color=colorid, rendertype=4, ontop=True,
                             bbox='last', view=None)
        elif len(points) % 3 == 0:
            P0, P1, P2 = (points[i][2] for i in range(-3, 0))
            drawn += angle_report(P0, P1, P2, colorid)
            colorid += colorstep
            draw.undraw(temp)
            temp = None

    temp = None
    points = []
    drawn = []
    print("Pick single points, every 3rd shows angle at middle point")
    with draw.TempPalette(pf.cfg['draw/querypalette']):
        pick('point', filter='closest', func=every3_showangle, prompt='')
    draw.undraw(temp)
    return {'points': points, 'drawn': drawn}


################### General Button Functions ###########

def addButton(toolbar, tooltip, icon, func, repeat=False, toggle=False,
              checked=False, icon0=None, enabled=True):
    """Add a button to a toolbar.

    - `toolbar`: the toolbar where the button will be added
    - `tooltip`: the text to appear as tooltip
    - `icon`: name of the icon to be displayed on the button,
    - `func`: function to be called when the button is pressed,
    - `repeat`: if True, the `func` will repeatedly be called if button is
      held down.
    - `toggle`: if True, the button is a toggle and stays in depressed state
      until pressed again.
    - `checked`: initial state for a toggle buton.
    - `icon1`: for a toggle button, icon to display when button is not checked.
    """
    iconset = QtGui.QIcon()
    icon_on = QPixmap(utils.findIcon(icon))
    iconset.addPixmap(icon_on, QtGui.QIcon.Normal, QtGui.QIcon.On)
    if toggle and icon0:
        icon_off = QPixmap(utils.findIcon(icon0))
        iconset.addPixmap(icon_off, QtGui.QIcon.Normal, QtGui.QIcon.Off)
    a = toolbar.addAction(iconset, tooltip, func)
    a.setEnabled(enabled)
    b = toolbar.widgetForAction(a)
    if repeat:
        b.setAutoRepeat(True)
        b.setAutoRepeatDelay(500)
        b.clicked.connect(a.trigger)
        #b.clicked.connect(func)
    if toggle:
        raise ValueError("use widgets.ToggleToolButton instead")
    b.setToolTip(tooltip)
    return b


def removeButton(toolbar, button):
    """Remove a button from a toolbar."""
    toolbar.removeAction(button)


################### Main toolbar ###########

pickmenudata ={
    'title': 'Pick tools',
    'items' : [
        ('Pick point', picksel, {'data':'point', 'icon':'pick-point'}),
        ('Pick element', picksel, {'data':'element', 'icon':'pick-element'}),
        ('Pick actor', picksel, {'data':'actor', 'icon':'pick-actor'}),
    ],
    'default': 'Pick element',
}

querymenudata = {
    'title': 'Query tools',
    'items' : [
        ('Query point', query, {'data':'point', 'icon':'query-point'}),
        ('Query element', query, {'data':'element', 'icon':'query-element'}),
        ('Query actor', query, {'data':'actor', 'icon':'query-actor'}),
        ('Query distance', query_distance, {'icon':'query-dist'}),
        ('Query angle', query_angle, {'icon':'query-angle'}),
   ],
    'default': 'Query element',
}


def addActionButtons(toolbar):
    """Add the script action buttons to the toolbar."""
    from pyformex.gui import draw
    from pyformex.gui.menus import File
    action = {}
    avail_buttons = [
        ("Play", "next", draw.play, False),
        ("ReRun", "rerun", draw.replay, False),
        ## ( "Step", "nextstop", draw.step, False ),
        ("Continue", "ff", draw.fforward, False),
        ("Stop", "stop", draw.raiseExit, False),
        ("Edit", "pencil", File.editApp, False),
#        ("Info", "info", draw.showDoc, False),
        ("Query", "query", querymenudata, True),
        ("Pick", "pick", pickmenudata, True),
        ]
    # Filter configured buttons
    show_buttons = pf.cfg['gui/actionbuttons']
    show_buttons = [b for b in avail_buttons if b[0].lower() in show_buttons]
    for name, icon, func, enabled in show_buttons:
        if callable(func):
            b = addButton(toolbar, name, icon, func, enabled=enabled)
        elif isinstance(func, dict):
            b = widgets.DropDownToolButton(toolbar, **func)
        action[name] = b
    return action


################# Camera action toolbar ###############


def addCameraButtons(toolbar):
    """Add the camera buttons to a toolbar."""
    # The buttons have the following fields:
    #  0 : tooltip
    #  1 : icon
    #  2 : function
    # optional:
    #  3 : REPEAT  (default True)
    from pyformex.gui.menus import Camera
    buttons = [
        ("Rotate left", "rotleft", Camera.getfunc('rotLeft')),
        ("Rotate right", "rotright", Camera.getfunc('rotRight')),
        ("Rotate down", "rotdown", Camera.getfunc('rotDown')),
        ("Rotate up", "rotup", Camera.getfunc('rotUp')),
        ("Twist right", "twistright", Camera.getfunc('twistRight')),
        ("Twist left", "twistleft", Camera.getfunc('twistLeft')),
        ("Translate left", "left", Camera.getfunc('panLeft')),
        ("Translate right", "right", Camera.getfunc('panRight')),
        ("Translate down", "down", Camera.getfunc('panDown')),
        ("Translate up", "up", Camera.getfunc('panUp')),
        ("Zoom In", "zoomin", Camera.getfunc('dollyIn')),
        ("Zoom Out", "zoomout", Camera.getfunc('dollyOut')),
        ("Zoom All", "zoomall", Camera.getfunc('zoomAll'), False),
        ("Zoom Rectangle", "zoomrect", Camera.getfunc('zoomRectangle'), False),
    ]
    for but in buttons:
        icon = widgets.pyformexIcon(but[1])
        a = toolbar.addAction(icon, but[0], but[2])
        b = toolbar.children()[-1]  # Get the QToolButton for the last action
        if len(but) < 4 or but[3]:
            b.setAutoRepeat(True)
            b.setAutoRepeatDelay(500)
            # This causes a double action on the button click
            # only use it if we can detach the button press from trigger
            #b.released.connect(a.trigger)
        if len(but) >= 5:
            pass
            # This is currently not used
            #b.setCheckable(but[4])
            #b.released.connect(a.toggle)

        b.setToolTip(but[0])


#######################################################################
# Canvas Toggle buttons #
#########################

class ViewportToggle(widgets.ToggleToolButton):
    """A toolbar button that toggles the state of a Viewpor attribute

    attr: one of 'perspective',
    """
    def __init__(self, toolbar, icons, attr, checked=False, tooltip=''):
        self._vp = toolbar.parent().viewports
        self.attr = attr
        super().__init__(
            toolbar, icons, func=self.setstate, status=self.getstate,
            checked=self.getstate(), # THIS DOES NOT WORK
            #checked=False,
            tooltip=tooltip)

    def getstate(self):
        """Get the current state of the viewport attribute."""
        vp = self._vp.current
        return False if vp is None else vp.getToggle(self.attr)

    def setstate(self, onoff=None):
        """Toggle the state of the viewport attribute."""
        vp = self._vp.current
        if onoff is None:
            onoff = not vp.getToggle(self.attr)
        else:
            onoff = bool(onoff)
        vp.setToggle(self.attr, onoff)
        vp.update()
        pf.app.processEvents()


def updateViewportButtons(vp):
    if vp.focus:
        transparency_button.update_status()
        light_button.update_status()
        normals_button.update_status()
        perspective_button.update_status()
        wire_button.update_status()


################# Wire Button ###############

# TODO: this is special: toggles an int between + and -

wire_button = None  # the toggle wire button

def addWireButton(toolbar):
    global wire_button

    def wire_button_getstate():
        vp = toolbar.parent().viewports.current
        return False if vp is None else vp.settings['wiremode'] > 0

    wire_button = widgets.ToggleToolButton(
        toolbar, icons=('wirenone', 'wireall'),
        func=wire_button_setstate, status=wire_button_getstate,
        checked=False, tooltip='Toggle Wire Mode')


def wire_button_setstate():
    vp = pf.GUI.viewports.current
    vp.setWireMode()
    vp.update()
    pf.app.processEvents()


def updateWireButton():
    """Update the wire button to correct state."""
    if wire_button:   # This button is optional!
        wire_button.update_status()


################# Transparency Button ###############

transparency_button = None  # the toggle transparency button

def addTransparencyButton(toolbar):
    global transparency_button
    transparency_button = ViewportToggle(
        toolbar, icons=('transparent', 'transparent'), attr='alphablend',
        checked=False, tooltip='Toggle Transparent Mode')

def updateTransparencyButton():
    """Update the transparency button to correct state."""
    transparency_button.update_status()


################# Lights Button ###############

light_button = None

def addLightButton(toolbar):
    global light_button
    light_button = ViewportToggle(
        toolbar, icons=('lamp', 'lamp-on'), attr='lighting',
        checked=False, tooltip='Toggle Lights')

def updateLightButton():
    """Update the light button to correct state."""
    light_button.update_status()


################# Normals Button ###############

normals_button = None

def addNormalsButton(toolbar):
    global normals_button
    normals_button = ViewportToggle(
        toolbar, icons=('normals-ind', 'normals-avg'), attr='avgnormals',
        checked=False, tooltip='Toggle Normals Mode')

def updateNormalsButton():
    """Update the normals button to correct state."""
    normals_button.update_status()


################# Perspective Button ###############

perspective_button = None

def addPerspectiveButton(toolbar):
    global perspective_button
    perspective_button = ViewportToggle(
        toolbar, icons=('project', 'perspect'), attr='perspective',
        checked=True, tooltip='Toggle Perspective/Projective Mode')

def updatePerspectiveButton():
    """Update the perspective button to correct state."""
    perspective_button.update_status()

def setPerspective():
    perspective_button.setstate(True)

def setProjection():
    perspective_button.setstate(False)

################# Timeout Button ###############

timeout_button = None  # the timeout toggle button

def toggleTimeout(onoff=None):
    if onoff is None:
        onoff = widgets.input_timeout < 0
    if onoff:
        timeout = pf.cfg['gui/timeoutvalue']
    else:
        timeout = -1

    widgets.setInputTimeout(timeout)
    onoff = widgets.input_timeout > 0
    if onoff:
        # THIS SUSPENDS ALL WAITING! WE SHOULD IMPLEMENT A TIMEOUT!
        # BY FORCING ALL INDEFINITE PAUSES TO A WAIT TIME EQUAL TO
        # WIDGET INPUT TIMEOUT
        pf.debug("FREEING the draw lock")
        pf.GUI.drawlock.free()
    else:
        pf.debug("ALLOWING the draw lock")
        pf.GUI.drawlock.allow()
    return onoff


def addTimeoutButton(toolbar):
    """Add or remove the timeout button,depending on cfg."""
    global timeout_button
    if pf.cfg['gui/timeoutbutton']:
        if timeout_button is None:
            timeout_button = addButton(toolbar, 'Toggle Timeout', 'clock', toggleTimeout, toggle=True, checked=False)
    else:
        if timeout_button is not None:
            removeButton(toolbar, timeout_button)
            timeout_button = None


def timeout(onoff=None):
    """Programmatically toggle the timeout button"""
    if timeout_button is not None:
        timeout_button.setChecked(toggleTimeout(onoff))



# End
