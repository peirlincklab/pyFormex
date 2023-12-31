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

"""Bezier

level = 'beginner'
topics = ['geometry','curve']
techniques = ['connect','color','solve']

"""


_level = 'beginner'
_topics = ['geometry', 'curve']
_techniques = ['connect', 'color', 'solve']

from pyformex.gui.draw import *

def build_matrix(atoms, vars):
    """Build a matrix of functions of coords.

    atoms is a list of text strings each representing a function of variables
    defined in vars.
    vars is a dictionary where the keys are variable names appearing in atoms
    and the values are 1-dim arrays of values. All variables should have the
    same shape !
    A matrix is returned where each row contains the values of atoms evaluated
    for one set of the variables.
    """
    keys = list(vars)
    nval = len(vars[keys[0]])
    aa = np.zeros((nval, len(atoms)), at.Float)
    for k, a in enumerate(atoms):
        res = eval(a, vars)
        aa[:, k] = eval(a, vars)
    return aa


class Bezier():
    """A class representing a Bezier curve"""

    atoms = {
        1: ('1-t', 't'),
        2: ('(1-t)**2', '2*t*(1-t)', 't**2'),
        3: ('(1-t)**3', '3*t*(1-t)**2', '3*t**2*(1-t)', 't**3'),
        }

    def __init__(self, pts):
        """Create a bezier curve.

        pts is an Coords array with at least 2 points.
        A Bezier curve of degree npts-1 is constructed between the first
        and the last points.
        """
        self.pts = pts


    def at(self, t):
        """Returns the points of the curve for parameter values t"""
        deg = self.pts.shape[0] - 1
        aa = build_matrix(Bezier.atoms[deg], {'t': t})
        return np.dot(aa, self.pts)


def drawNumberedPoints(x, color):
    x = Formex(x)
    draw(x, color=color)
    drawNumbers(x, color=color)

def run():
    resetAll()
    n = 100
    t = np.arange(n+1)/float(n)

    for d in np.arange(4) * 0.2:
        x = Coords([[0., 0.], [1./3., d], [2./3., 4*d**2], [1., 0.]])
        drawNumberedPoints(x, red)
        H = Formex(x.reshape(2, 2, 3))
        draw(H, color=red)
        curve = Bezier(x)
        F = Formex(curve.at(t))
        G = connect([F, F], bias=[0, 1])
        draw(G)

if __name__ == '__draw__':
    run()
# End
