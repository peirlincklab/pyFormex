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
"""Seed

Graphical feedback to the creeation of non-uniform seeds.
"""

_level = 'normal'
_topics = ['meshing']
_techniques = ['seed', 'dialog', 'fslider', 'undraw']

from pyformex.gui.draw import *

# globals
base = None
seed_ticks = None
x = None
SA = None
dialog = None
saved_e = None


def create_globals():
    """Create globals"""
    global base, seed_ticks, x
    n = 40
    baseline = Formex('l:1')
    ticks = Formex('l:4').scale(0.1).replicate(n+1, step=1./n)
    base = List([baseline, ticks])
    seed_ticks = Formex('l:2').scale(0.1).replicate(n+1, step=1./n)
    x = at.unitDivisor(n)


def show_base():
    """Draw the fixed base and lock camera"""
    unlockCamera()
    clear()
    linewidth(2)
    view('front')
    draw(base)
    lockCamera()


def redraw(e0, e1=None):
    """Redraw seeds with new value for e0,e1"""
    global SA, saved_e
    if e1 is None:
        e1 = e0
    saved_e = (e0, e1)
    seeds = at.unitAttractor(x, e0, e1)
    print("e0=%s, e1=%s: %s" % (e0, e1, seeds))
    seed_ticks.coords.x = seeds.reshape(-1, 1)
    SB = draw(seed_ticks, color=red)
    undraw(SA)
    SA = SB


def do_slider(fld):
    fld.setEnabled(False)  # Avoid a stream of events we can't handle
    if fld.name() == 'e0':
        redraw(fld.value(), saved_e[1])
    elif fld.name() == 'e1':
        redraw(saved_e[0], fld.value())
    fld.setEnabled(True)


def show():
    """Accept data, redraw seeds"""
    if dialog.validate():
        e0 = dialog.results['e0']
        e1 = dialog.results['e1']
        redraw(e0, e1)


def close():
    global dialog
    if dialog:
        dialog.close()
        dialog = None
    unlockCamera()
    print("Releasing lock")
    scriptRelease(__file__)


def timeOut():
    try:
        show()
    finally:
        close()


def create_dialog():
    global dialog
    if dialog is not None:
        return

    dialog = Dialog(caption = 'Seed parameters', items = [
        _I('e0', 0.0, itemtype='fslider', min=-1.0, max=1.0, dec=1, scale=0.02,
            func=do_slider, tooltip='Attractor force to 0.0'),
        _I('e1', 0.0, itemtype='fslider', min=-1.0, max=1.0, dec=1, scale=0.02,
           func=do_slider, tooltip='Attractor force to 1.0'),
        ], actions = [('Close', close), ('Show', show)], default = 'Show',
    )
    # Always install a timeout in official examples!
    dialog.show(timeoutfunc=timeOut)


def run():
    """Show the uniform seeds and the seed dialog"""
    create_globals()
    show_base()
    redraw(0., 0.)
    create_dialog()
    scriptLock(__file__)


if __name__ == '__draw__':
    run()
# End
