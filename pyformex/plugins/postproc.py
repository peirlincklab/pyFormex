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

"""Postprocessing functions

Postprocessing means collecting a geometrical model and computed values
from a numerical simulation, and render the values on the domain.
"""

import numpy as np


# Some functions to calculate a scalar value from a vector
# TODO: base these on numpy.linalg.norm or arraytools.norm
def norm2(A):
    return np.sqrt(np.square(np.asarray(A)).sum(axis=-1))


def norm(A, x):
    return np.power(np.power(np.asarray(A), x).sum(axis=-1), 1./x)


def max(A):
    return np.asarray(A).max(axis=-1)


def min(A):
    return np.asarray(A).min(axis=-1)


def frameScale(nframes=10, cycle='up', shape='linear'):
    """Return a sequence of scale values between -1 and +1.

    ``nframes`` : the number of steps between 0 and -1/+1 values.

    ``cycle``: determines how subsequent cycles occur:

      ``'up'``: ramping up

      ``'updown'``: ramping up and down

      ``'revert'``: ramping up and down then reverse up and down

    ``shape``: determines the shape of the amplitude curve:

      ``'linear'``: linear scaling

      ``'sine'``: sinusoidal scaling
    """
    s = np.arange(nframes+1)
    if cycle in ['updown', 'revert']:
        s = np.concatenate([s, np.fliplr(s[:-1].reshape((1, -1)))[0]])
    if cycle in ['revert']:
        s = np.concatenate([s, -np.fliplr(s[:-1].reshape((1, -1)))[0]])
    return s.astype(float)/nframes


# End
