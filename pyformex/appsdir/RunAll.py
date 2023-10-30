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
"""RunAll

This application can be used to automatically run a sequence of
pyFormex examples. It is often used to test pyFormex functionality.
"""

import random
import pyformex as pf
from pyformex import script
from pyformex.gui.draw import scriptRelease, askItems, _I


def runAll(startfrom='A', stopat='[', count=-1, recursive=True,
           timeout=1.0, pause=1.0, shuffle=False):
    """Run all apps with a name in the range [startfrom,stopat[.

    Runs the apps with a name >= `startfrom` and < `stopat`.
    The default will run all apps starting with a capital (like
    the examples). Specify None to disable the limit.
    If count is positive, at most count scripts are executed.
    If recursive is True, also the files in submenu are played.
    If random is True, the files in any submenu are shuffled before running.
    """
    from pyformex.gui.draw import layout, reset, sleep
    from pyformex.gui import widgets

    # Get the Apps Examples menu
    appmenu = pf.GUI.menu['App']
    examples = appmenu['Examples']['Byname']

    files = examples.listApps()
    print(f"Total number of apps: {len(files)}")
    print(f"Start from {startfrom}; stop at {stopat}; count {count}; random {shuffle}")
    if startfrom is not None:
        files = [f for f in files if f.split('.')[-1] >= startfrom]
    if stopat is not None:
        files = [f for f in files if f.split('.')[-1] < stopat]
    if shuffle:
        random.shuffle(files)
    if count >= 0:
        files = files[:count]

    print(f"Apps to play: {len(files)}" )
    print(files)

    if files:
        # Run these appss
        pf.GUI.enableButtons(pf.GUI.actions, ['Stop'], True)
        pf.GUI.runallmode = True
        save = widgets.input_timeout
        pf.GUI.drawlock.free()
        widgets.input_timeout = timeout
        try:
            for f in files:
                layout(1)
                reset()
                pf.PF.clear()
                print("Running app '%s'" % f)
                script.runAny(f, wait=True)
                script.breakpt(msg="Breakpoint from runall")
                if script.exitrequested:
                    break
                sleep(pause)
        finally:
            widgets.input_timeout = save
            pf.GUI.drawlock.allow()
            pf.GUI.runallmode = False
            pf.GUI.enableButtons(pf.GUI.actions, ['Stop'], False)


def run():
    # Save the name of the current app
    my_name = pf.GUI.curfile.bg.buttons()[1].text()
    res = askItems(caption=__name__, store=__name__+'_data', items=[
        _I('startfrom', 'A', text='Start from'),
        _I('stopat', '[', text='Stop at'),
        _I('count', -1, text='Count', tooltip='Give -1 for all'),
        _I('shuffle', True, text='Play in random order'),
        _I('timeout', 0.5, text='Timeout dialogs after (secs)'),
        _I('pause', 1.0, text='Time to pause after each app'),
    ])
    if res:
        print(res)
        print(pf.PF['appsdir.RunAll_data'])
        scriptRelease('__auto/app__')
        runAll(**res)
    pf.GUI.setcurfile(my_name)


if __name__ == "__draw__":

    pf.warning("This can only be run as an App, not as a Script!")

# End
