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
"""Predefined camera viewing directions

"""
import re

_re_view = re.compile(r"(-?[xyz])(-?[xyz])")

def iconName(viewname):
    """Get the icon name for an axis view"""
    m = _re_view.match(viewname)
    if m:
        x, y = m.group(1), m.group(2)
        iconname = 'view-' + \
            x[-1] + ('l' if x[0]=='-' else 'r') + '-' + \
            y[-1] + ('d' if y[0]=='-' else 'u')
    elif viewname.startswith('iso'):
        iconname = 'view-iso1'
    else:
        iconname = viewname
    return iconname

class ViewAngles(dict):
    """A dict to keep named camera angle settings.

    This class keeps a dictionary of named angle settings. Each value is
    a tuple of (longitude, latitude, twist) camera angles.
    This is a static class which should not need to be instantiated.

    There are seven predefined values: six for looking along global
    coordinate axes, one isometric view.
    """

    built_in_abs_views = {
        'xy': (0.,   0., 0.),
        'x-y': (0., 180., 0.),
        'xz': (0., -90., 0.),
        'x-z': (0.,  90., 0.),
        '-xy': (180.,   0., 0.),
        '-x-y': (180., 180., 0.),
        '-xz': (180.,  90., 0.),
        '-x-z': (180., -90., 0.),
        'yx': (180.,   0., 90.),
        'y-x': (0.,   0., 90.),
        'yz': (90.,   0., 90.),
        'y-z': (-90.,   0., 90.),
        '-yx': (0.,   0., -90.),
        '-y-x': (180.,   0., -90.),
        '-yz': (-90.,   0., -90.),
        '-y-z': (90.,   0., -90.),
        'zx': (-90.,  90., 0.),
        'z-x': (-90., -90., 0.),
        'zy': (-90.,   0., 0.),
        'z-y': (-90., 180., 0.),
        '-zx': (90., -90., 0.),
        '-z-x': (90.,  90., 0.),
        '-zy': (90.,   0., 0.),
        '-z-y': (90., 180., 0.),
        }

    built_in_rel_views = {
        'iso': (45., 35.2644, 0.),
        'iso0': (45., 35.2644, 0.),
        'iso1': (135., 35.2644, 0.),
        'iso2': (225., 35.2644, 0.),
        'iso3': (315., 35.2644, 0.),
        'iso4': (45., -35.2644, 0.),
        'iso5': (135., -35.2644, 0.),
        'iso6': (225., -35.2644, 0.),
        'iso7': (315., -35.2644, 0.),
        }

    aliases = ['front', 'back', 'right', 'left', 'top', 'bottom']

    buttons = aliases + ['iso0', 'iso3']

    defviews = {
        'xy': ['xy', '-xy', '-zy', 'zy', 'x-z', 'xz', 'iso0'],
        'xz': ['xz', '-xz', 'yz', '-yz', 'xy', 'x-y', 'iso0'],
    }
    defaxes = {
        'xy': ((0., -1., 0.), (1., 0., 0.), (0., 0., -1.)),
        'xz': ((0., 0., -1.), (1., 0., 0.), (0., 1., 0.)),
        }

    def __init__(self, data = built_in_rel_views):
       dict.__init__(self, data)
       for a, n in zip(ViewAngles.aliases, ViewAngles.defviews['xy']):
           self[a] = ViewAngles.built_in_abs_views[n]
       self.setOrientation('xz')


    def setOrientation(self, orient):
        """Set standard orientation.

        Parameters
        ----------
        orient: str
            The front orientation. Should be one of 'xy' or 'xz'.
            The other relative orientations are derived from it.

        Returns
        -------
        aliases: list
            List of standard relative orientations
        realnames:
            List of the real orientation anmes corresponding with aliases
        icons:
            List of icon names corresponding with the realnames
        """
        if orient in ViewAngles.defviews:
            self.orient = orient
            self.angle_axes = ViewAngles.defaxes[orient]
            aliases = ViewAngles.buttons
            realnames = ViewAngles.defviews[orient]
            icons = [iconName(n) for n in realnames]
            return aliases, realnames, icons
        else:
            raise ValueError("Invalid front orientation: %s" % orient)


    def get(self, name):
        """Get the angles for a named view.

        Returns a tuple of angles (longitude, latitude, twist) if the
        named view was defined, or None otherwise
        """
        angles = ViewAngles.built_in_abs_views.get(name, None)
        if angles is not None:
            orient = 'xy'
        else:
            angles = dict.get(self, name, None)
            orient = self.orient
        return angles, orient


# The global storage of named views
view_angles = ViewAngles()

def getAngles(name):
    """Get angles (and orient) of a named view."""
    return view_angles.get(name)

def getAngleAxes(orient):
    return view_angles.angle_axes

def getOrientation():
    return view_angles.orient

def setAngles(name, angles):
    """Define new or redefine old view"""
    view_angles[name] = angles

def viewNames():
    """Return a list of all view names"""
    return sorted(list(view_angles.built_in_abs_views.keys()) + list(view_angles.keys()))

def setOrientation(orient):
    return view_angles.setOrientation(orient)


# End
