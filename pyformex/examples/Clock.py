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

"""Clock

Shows an analog clock running for a short time
"""

_level = 'advanced'
_topics = []
_techniques = ['timer']

from pyformex.gui.draw import *
from pyformex import simple
from datetime import datetime
from pyformex.gui import QtCore
from pyformex.opengl.textext import *

class AnalogClock():
    """An analog clock built from Formices"""

    def __init__(self, lw=2, mm=0.75, hm=0.85, mh=0.7, hh=0.6, sh=0.9):
        """Create an analog clock."""
        self.linewidth = lw
        self.circle = simple.circle()
        radius = Formex('l:2')
        self.mainmark = radius.subdivide([mm, 1.0])
        self.hourmark = radius.subdivide([hm, 1.0])
        self.mainhand = radius.subdivide([0.0, mh])
        self.hourhand = radius.subdivide([0.0, hh])
        if sh > 0.0:
            self.secshand = radius.subdivide([0.0, sh])
        else:
            self.secshand = None
        self.hands = []
        self.timer = None


    def draw(self):
        """Draw the clock (without hands)"""
        draw(self.circle, color='black', linewidth=self.linewidth)
        draw(self.mainmark.rosette(4, 90), color='black', linewidth=self.linewidth)
        draw(self.hourmark.rot(30).rosette(2, 30).rosette(4, 90),
             color='black', linewidth=0.5*self.linewidth)


    def drawTime(self, hrs, min, sec=None):
        """Draw the clock's hands showing the specified time.

        If no seconds are specified, no seconds hand is drawn.
        """
        hrot = - hrs*30. - min*0.5
        mrot = - min*6.
        undraw(self.hands)
        MH = draw(self.mainhand.rot(mrot), bbox=None, color='red', linewidth=self.linewidth)
        HH = draw(self.hourhand.rot(hrot), bbox=None, color='red', linewidth=self.linewidth)
        self.hands = [MH, HH]
        if self.secshand and sec:
            srot = - sec*6.
            SH = draw(self.secshand.rot(srot), bbox=None, color='orange', linewidth=0.5*self.linewidth)
            self.hands.append(SH)


    def drawNow(self):
        """Draw the hands showing the current time."""
        now = datetime.now()
        self.drawTime(now.hour, now.minute, now.second)
        breakpt("The clock has been stopped!")


    def run(self, granularity=1, runtime=100):
        """Run the clock for runtime seconds, updating every granularity."""
        if granularity > 0.0:
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.drawNow)
            self.timer.start(1000*granularity)
        if runtime > 0.0:
            self.timeout = QtCore.QTimer()
            self.timeout.timeout.connect(self.stop)
            self.timeout.setSingleShot(True)
            self.timeout.start(1000*runtime)


    def stop(self):
        """Stop a running clock."""
        print("STOP")
        if self.timer:
            self.timer.stop()



class DigitalClock():
    """A digital clock"""

    def __init__(self, seconds=True):
        """Create an analog clock."""
        self.seconds = bool(seconds)
        self.len = 8 if self.seconds else 5
        self.F = Formex('4:0123').replic(self.len)
        self.ft = FontTexture('NotoSansMono-Condensed.3x32.png', 24)
        self.timer = None
        self.actor = None

    def drawTime(self, hrs, min, sec):
        """Draw the clock with the specified time"""
        text = f"{hrs:02d}:{min:02d}"
        if self.seconds:
            text += f":{sec:02d}"
        tc = self.ft.texCoords(text)
        A = draw(self.F, color=pyformex_pink, texture=self.ft, texcoords=tc,
             texmode=2, ontop=True)
        undraw(self.actor)
        self.actor = A

    def drawNow(self):
        """Draw the hands showing the current time."""
        now = datetime.now()
        self.drawTime(now.hour, now.minute, now.second)
        breakpt("The clock has been stopped!")

    draw = drawNow

    def run(self, granularity=1, runtime=100):
        """Run the clock for runtime seconds, updating every granularity."""
        if granularity > 0.0:
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.drawNow)
            self.timer.start(1000*granularity)
        if runtime > 0.0:
            self.timeout = QtCore.QTimer()
            self.timeout.timeout.connect(self.stop)
            self.timeout.setSingleShot(True)
            self.timeout.start(1000*runtime)

    def stop(self):
        """Stop a running clock."""
        print("STOP")
        if self.timer:
            self.timer.stop()



def run():
    reset()
    res = askItems(items=[
        _I('Clock type', choices=['Analog', 'Digital'], itemtype='radio'),
        _I('runtime', 15, text='Run time (seconds)'),
    ])
    if res:
        if res['Clock type'] == 'Analog':
            C = AnalogClock()
        else:
            C = DigitalClock()
        C.draw()
        setDrawOptions({'bbox': None, 'view': None})
        C.drawNow()
        C.run()
        sleep(res['runtime'])
        C.stop()
        print(pf.scriptlock)

if __name__ == '__draw__':
    run()
# End
