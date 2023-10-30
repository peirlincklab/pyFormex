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

import numpy as np
import pyformex as pf
from pyformex import formex

from pyformex.gui import QtCore
from pyformex.gui import qtcanvas
from OpenGL.arrays import vbo


class Manipulator:

    def __init__(self, actor, canvas=None, app=None, selection_width=20, select_closest=True, extra=None, **kwargs):
        """Manipulate actor

        :param actor: drawable actor
        :param canvas: canvas where actor is drawn
        :param app: pyformex app
        :param selection_width: selection width in pixels
        :param select_closest: select closest item
        :param kwargs: options for highlighting
        """

        self.actor = actor

        # Use currently active canvas and app if not specified
        if canvas is None:
            self.canvas = pf.canvas
        else:
            self.canvas = canvas

        if app is None:
            self.app = pf.app
        else:
            self.app = app

        self.selection_width = selection_width
        self.select_closest = select_closest
        self.highlight = dict()
        self.highlight.update(**kwargs)

        self.extra = extra

    def start(self):
        """Start manipulation

        :return:
        """

        self.canvas.update()

        # Initialize selected nodes actor attribute
        setattr(self.actor, 'selected', None)
        setattr(self.actor, 'highlighting', None)

        # Start loop of events
        self.canvas.mousehandler.set(qtcanvas.LEFT, qtcanvas.NONE,
                                     self.left_mouse_button)
        self.canvas.mousehandler.set(qtcanvas.RIGHT, qtcanvas.NONE,
                                     self.canvas.emit_done)
        self.canvas.signals.DONE.connect(self.stop)

        self.canvas.adjust_busy = True

        timer = QtCore.QThread()
        while self.canvas.adjust_busy:

            timer.msleep(10)

            self.app.processEvents()

        # Restore actor to original state
        delattr(self.actor, 'selected')
        delattr(self.actor, 'highlighting')

    def left_mouse_button(self, x, y, action):
        """Actions upon left mouse click

        :param x:
        :param y:
        :param action:
        :return:
        """

        if self.extra is not None:
            self.extra(self.canvas, self.actor)

        # Node dragging
        if action == 1:

            if self.actor.selected.any():
                self.canvas.previous = self.move_actor_nodes(
                    x, y, self.canvas.previous)

        # Finish
        elif action == 2:
            self.canvas.removeActor(self.actor.highlighting)

        # Initialize
        else:

            self.canvas.previous = None
            self.actor.highlighting = None

            self.actor.selected = self.select(x, y)

            if self.actor.highlighting is not None:
                self.canvas.addActor(self.actor.highlighting)

        self.canvas.update()

    def stop(self):
        """Stop manipulation by right click

        :return:
        """

        self.canvas.mousehandler.reset(qtcanvas.LEFT, qtcanvas.NONE)
        self.canvas.mousehandler.reset(qtcanvas.RIGHT, qtcanvas.NONE)

        self.canvas.DONE.disconnect(self.stop)
        self.canvas.adjust_busy = False

    def select(self, x, y):
        """Select a node, edge or element

        :param x:
        :param y:
        :return:
        """

        # Actor coordinates in camera system
        xyz = self.canvas.camera.toNDC(
            self.actor.coords, rect=(x, y, self.selection_width, self.selection_width))

        # Select a node
        selected = self.select_node(xyz)

        # If no node is selected, check if an edge is selected
        if not selected.any():

            # Select an edge
            selected = self.select_edge(xyz)

            # If no edge is selected, check if an element is selected
            if not selected.any():

                # Select an face
                selected = self.select_element(xyz)

                if selected.any() and self.highlight:

                    self.actor.highlighting = formex.Formex(
                        self.actor.coords[self.actor.elems[
                            selected[self.actor.elems].all(axis=-1)]],
                        eltype=self.actor.eltype.lname
                    ).actor(**self.highlight)

            else:

                # Highlight edge
                if self.highlight:
                    self.actor.highlighting = formex.Formex(
                        self.actor.coords[self.actor.elems[:, self.actor.edges][
                            selected[self.actor.elems[:, self.actor.edges]].all(axis=-1)]]
                    ).actor(**self.highlight)

        else:

            # Highlight point
            if self.highlight:
                self.actor.highlighting = self.actor.coords[selected].actor(**self.highlight)

        return selected

    def select_node(self, xyz):
        """Select a node

        :param xyz:
        :return:
        """

        xy = xyz[:, :2]
        z = xyz[:, 2]

        # Select a point
        selected = np.sum(xy ** 2, axis=-1) <= 1.0

        if selected.sum() > 1 and self.select_closest:
            selected[selected] = z[selected] == z[selected].min()

        return selected

    def select_edge(self, xyz):
        """Select an edge

        :param xyz:
        :return:
        """

        xy = xyz[:, :2]
        z = xyz[:, 2]

        selected = np.zeros(xyz.shape[:1], dtype=bool)

        # Camera coordinates
        edges = xy[self.actor.elems[:, self.actor.edges]]

        # Find intersecting edges by solving quadratic equation
        p = edges[:, :, 1] - edges[:, :, 0]
        q = edges[:, :, 0]

        a = np.sum(p * p, axis=-1)
        b = np.sum(p * q, axis=-1) * 2
        c = np.sum(q * q, axis=-1) - 1

        # Discriminant
        d = b ** 2 - 4 * a * c

        # First test for intersections
        t = (d > 0.) & (a > 0.)

        # Solutions of equation
        t1 = (-b[t] - d[t] ** 0.5) / (2 * a[t])
        t2 = (-b[t] + d[t] ** 0.5) / (2 * a[t])

        # Second test for intersections
        t[t] &= (t1 >= 0) & (t1 <= 1) | (t2 >= 0) & (t2 <= 1)

        if t.any() and self.select_closest:
            mid = z[self.actor.elems[:, self.actor.edges]].mean(axis=-1)

            t &= mid == mid[t].min()

        # Adjust selection
        selected[self.actor.elems[:, self.actor.edges][t]] = True

        return selected

    def select_element(self, xyz):
        """Select an element

        :param xyz:
        :return:
        """

        xy = xyz[:, :2]
        z = xyz[:, 2]

        selected = np.zeros(xyz.shape[:1], dtype=bool)

        # Camera coordinates
        edges = xy[self.actor.elems[:, self.actor.edges]]

        test_0 = (edges[:, :, 0, 1] > 0) != (edges[:, :, 1, 1] > 0)
        test_1 = (edges[:, :, :, 0] > 0).any(axis=-1)

        test_2 = ~ np.equal(edges[:, :, 1, 1], edges[:, :, 0, 1])

        test_2[test_2] = (edges[:, :, 0, 0][test_2] - edges[:, :, 0, 1][test_2] * (
                edges[:, :, 1, 0] - edges[:, :, 0, 0])[test_2] / (
                                  edges[:, :, 1, 1] - edges[:, :, 0, 1])[test_2]) > 0

        test = (test_0 & test_1 & test_2).sum(axis=-1) % 2 == 1

        if test.any() and self.select_closest:
            mid = z[self.actor.elems].mean(axis=-1)

            test &= mid == mid[test].min()

        selected[self.actor.elems[test]] = True

        return selected

    # Node movement
    def move_actor_nodes(self, x, y, previous=None):
        """Drag nodes of the actor

        :param x:
        :param y:
        :param previous:
        :return:
        """

        # Coordinates of moving point
        moving = self.canvas.unproject(x, y, 0.).projectOnPlane(
            self.canvas.camera.rot.T[2], self.actor.coords[self.actor.selected].center())

        if previous is None:
            previous = moving

        self.actor.coords[self.actor.selected] += moving - previous
        self.actor.object.coords[:] = self.actor.coords

        # Updated interpolation
        self.actor.vbo = vbo.VBO(self.actor.coords[self.actor.elems])

        if self.actor.highlighting is not None:

            self.actor.highlighting.coords += moving - previous
            self.actor.highlighting.vbo = vbo.VBO(
                self.actor.highlighting.coords[self.actor.highlighting.elems])

        self.canvas.update()

        return moving
