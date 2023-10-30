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

"""Dialog

Example demonstrating the components of input dialogs.
"""

_level = 'normal'
_topics = []
_techniques = ['dialog']

from pyformex.gui.draw import *

# BV
# not working correctly:
# - tooltip on group/tab

input_text = [
    _I('label', text="Just a label without value", itemtype='label', tooltip="itemtype='label' without value."),
     _I('labeltxt', text="", itemtype='label', tooltip="itemtype='label' and value in reStructuredText.", value="""..

Header
------
A label with a value. In this case some text written in reStructuredText.
The label text is empty.
"""),
    _I('info', 'A constant info field', text="itemtype 'info'", itemtype='info', tooltip="This is an informational field that can not be changed"),
    _I('string', 'A string input field', text="itemtype str", itemtype='string', tooltip="This is a single line string input field"),
    _I('text', 'A multiline text input field', text="itemtype 'text'", itemtype='text', tooltip="This is a multiline text input field"),
]

input_select_1 = [
    _I('bool', False, text="itemtype bool", stretch='ba', tooltip="This is a boolean field that can only get the values True or False, by checking or unchecking the box"),
    _I('select', ['First', 'Third'], text="itemtype 'select'", itemtype='select', choices=['First', 'Second', 'Third', 'Fourth'], tooltip="This is a an input field allowing you to select one or more of a set of predefined values"),
    _I('select_single', ['First', 'Third'], text="itemtype 'select' (single)", itemtype='select', choices=['First', 'Second', 'Third', 'Fourth'], single=True, tooltip="This is like 'list', but allowing only a single value to be selected"),
    _I('select_check', ['First', 'Third'], text="itemtype 'select' (check)", itemtype='select', choices=['First', 'Second', 'Third', 'Fourth'], check=True, tooltip="This is a an input field allowing you to select one of a set of predefined values"),
]

input_select_2 = [
    _I('combo', 'Third', text="itemtype 'combo'", choices=['First', 'Second', 'Third', 'Fourth'], tooltip="This is a an input field allowing you to select one of a set of predefined values"),
    _I('radio', 'Third', text="itemtype (h)radio", itemtype='radio', choices=['First', 'Second', 'Third', 'Fourth'], tooltip="Like 'select', this allows selecting one of a set of predefined values"),
    _I('vradio', 'Third', text="itemtype (v)radio", itemtype='vradio', choices=['First', 'Second', 'Third', 'Fourth'], tooltip="Like 'radio', but items are placed vertically"),
        _I('push','Third',text="itemtype (h)push",itemtype='push', choices=['First','Second','Third','Fourth'],tooltip="Yet another method to select one of a set of predefined values"),
        _I('vpush','Third',text="itemtype (v)push",itemtype='vpush', choices=['First','Second','Third','Fourth'],tooltip="Like 'push', but items are placed vertically"),
]

input_select = [
    _C('sel', input_select_1, maxwidth=600),
    _C('sel', input_select_2, maxwidth=600),
    ]

input_numerical = [
    _I('integer', 37, text="any int", tooltip="An integer input field"),
    _I('bounded', 50, text="a bounded integer (45..55)", min=45, max=55,
       tooltip="Accepts an integer in the interval [45,55]"),
    _I('float', 37., text="any float", tooltip="A float input field"),
    _I('boundedf', 20.7357, text="a bounded float", min=23.5, max=23.9, dec=2,
       tooltip="A bounded float input field. The interval is [23.5,23.9]"),
    _I('slider', 3, text="an int slider", min=0, max=10, itemtype='slider',
       tooltip="An integer input field with a slider to help set the value."),
    _I('fslider', 0, text="a float slider", min=-23.5, max=250.0, dec=1,
       itemtype='fslider', scale=0.01,
       tooltip="A float input field with a slider to set the value."),
    _I('ivector', [640, 400], itemtype='ivector', text="an integer vector",
       tooltip="An integer vector input field"),
    ]

input_special = [
    _I('file', __file__, itemtype='filename'),
    _I('color', colors.pyformex_pink, itemtype='color', text="Color", tooltip="An inputfield allowing to select a color. The current color is pyFormex pink."),
    _I('font', '', itemtype='font'),
    _I('point', [0., 0., 0.], itemtype='point'),
    _C('column1', [
        _I('point1', [0., 0., 0.], itemtype='point'),
        _I('point2', [0., 0., 0.], itemtype='point'),
        _I('point3', [0., 0., 0.], itemtype='point'),
       ], maxwidth=500),
    _C('column2', [
        _I('point4', [0., 0., 0.], itemtype='point'),
        _I('point5', [0., 0., 0.], itemtype='point'),
       ], maxwidth=500),
    _I('final text', ''),
    ]

input_tabgroup = [
    _I('enable1', False, text="Enable group 1",
       tooltip = "Check the box to enable group 1"),
    _G('group1', input_text[1:4], text="Text input group",
       tooltip='This is the header of group 1'),
    _I('enable2', False, text="Enable group 2",
       tooltip = "Check the box to enable group 2"),
    _G('group2', input_select_1[:3], text="Select input group",
       tooltip="This is the header of group 2"),
    _G('group3', input_special[:3], text="Special input group", check=True,
       tooltip="Group 3 has a checkbox to enable/disable the group"),
    ]

input_data = [
    _T('Text', input_text[:3], width=600),
    _T('Selection', input_select, width=600),
    _T('Numerical', input_numerical, width=600),
    _T('Special', input_special, width=600),
    _T('tabgroup', input_tabgroup, text="Groups", width=600),
    ]

input_enablers = [
    ('tabgroup/enable1', True, 'tabgroup/group1'), # 'tabgroup/group2/sel/radio'),
    ('tabgroup/enable2', True, 'tabgroup/group2', 'tabgroup/group1/string'),
    ]


def show():
    """Accept the data and show the results"""
    if dialog.validate():
        showText(utils.formatDict(dialog.results))


def close():
    global dialog
    if dialog:
        dialog.close()
        dialog = None
    #print("# Release script lock")
    scriptRelease(__file__)


def timeOut():
    """What to do on a Dialog timeout event.

    As a policy, all pyFormex examples should behave well on a
    dialog timeout.
    Most users can simply ignore this.
    """
    show()
    close()


def run():
    global dialog

    # Create the modeless dialog widget
    dialog = Dialog(input_data, enablers=input_enablers, autoprefix=True,
                    caption='Dialog',
                    actions = [('Close', close), ('Show', show)],
                    default='Show',
                    scroll=True, size=(0.75, 0.85)
    )

    # Show the dialog and let the user have fun
    dialog.show(timeoutfunc=timeOut)

    # Block other scripts
    scriptLock(__file__)

if __name__ == '__draw__':
    run()

# End
