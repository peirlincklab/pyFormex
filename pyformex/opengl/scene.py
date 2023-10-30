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
"""OpenGL 3D scene.

"""

import numpy as np

from pyformex import arraytools as at
from pyformex import coords
from .actors import Actor


class ItemList(list):
    """A list of drawn objects of the same kind.

    This is used to collect the Actors, Decorations and Annotations
    in a scene.
    Currently the implementation does not check that the objects are of
    the proper type or are not occurring multiple times.
    """

    def __init__(self, scene):
        self.scene = scene
        list.__init__(self)

    def add(self, items):
        """Add one or more items to an ItemList."""
        if not isinstance(items, (tuple, list)):
            items = [items]
        for a in items:
            if a not in self:
                self.append(a)

    def delete(self, items, sticky=True):
        """Remove item(s) from an ItemList.

        Parameters:

        - `items`: a single item or a list or tuple of items
        - `sticky`: bool: if True, also sticky items are removed.
          The default is to not remove sticky items.
          Sticky items are items having an attribute sticky=True.

        """
        if not isinstance(items, (tuple, list)):
            items = [items]
        for a in items:
            if a in self:
                self.remove(a)
#            #
#            ## TODO: we should probably standardize on using ids
#            ##
#            #
#            try:
#            except Exception:
#                print("Could not remove object of type %s from list" % type(a))
#                ids = [id(i) for i in self]
#                try:
#                    ind = ids.index(id(a))
#                    print("However, the object is in the list: removing it by id")
#                    del self[ind]
#                except Exception:
#                    print("The object is not in the list: skipping")


    def clear(self, sticky=False):
        """Clear the list.

        Parameters:

        - `sticky`: bool: if True, also sticky items are removed.
          The default is to not remove sticky items.
          Sticky items are items having an attribute sticky=True.

        """
        if sticky:
            del self[:]
        else:
            self[:] = [a for a in self if (hasattr(a, 'sticky') and a.sticky)]



##################################################################
#
#  The Scene
#

class Scene():
    """An OpenGL scene.

    The Scene is a class holding a collection of actors, annotations and
    decorations. It can also have a background. Actors are the 3D geometry
    constituting the actual scene. Annotations are explicatif objects
    attached to the geometry (actor name and id, element and node numbers,
    normals, ...); they can be 2D or 3D but live in a 3D world.
    Decorations are 2D or 3D objects attached to the canvas. Background
    objects are 2D decorations that are drown when the canvas is cleared.

    ==========  ==========  ====  ========  ============================
    object      rendertype  view  attached  remarks
    ==========  ==========  ====  ========  ============================
    Actor           0        3D      3D
    3D annot        4        3D      3D     no rendertype yet
    2D annot        1        2D      3D     single attacment point
    2D annot       -1        2D      3D     multiple attachment points
    2D decor        2        2D      2D
    3D decor       -2        3D      2D     axes display
    background      3        2D      2D
    ==========  ==========  ====  ========  ============================

    See Also
    --------
    Drawable: base class for scene objects
    """

    def __init__(self, canvas=None):
        """Initialize an empty scene with default settings."""
        self.canvas = canvas
        self.actors = ItemList(self)
        self.annot3d = ItemList(self)
        self.annot2d = ItemList(self)
        self.decorations = ItemList(self)
        self.backgrounds = ItemList(self)
        self.actorlist = {
            0: self.actors,
            4: self.annot3d,
            1: self.annot2d,
            -1: self.annot2d,
            2: self.decorations,
            -2: self.decorations,
            3: self.backgrounds,
            }
        self._bbox = None


    @property
    def annotations(self):
        """Return all annotations"""
        return self.annot3d + self.annot2d


    @property
    def bbox(self):
        """Return the bounding box of the scene.

        The bounding box is normally computed automatically as the
        box enclosing all Actors in the scene. Decorations and
        Annotations are not included. The user can however set the
        bbox himself, in which case that value will be used.
        It can also be set to the special value None to force
        recomputing the bbox from all Actors.
        """
        if self._bbox is None:
            self.set_bbox(self.actors)
        return self._bbox


    @bbox.setter
    def bbox(self, bb):
        """Set the bounding box of the scene.

        This can be used to set the scene bounding box to another value
        than the one autocomputed from all actors.

        bb is a (2,3) shaped array specifying a bounding box.
        A special value None may be given to force
        recomputing the bbox from all Actors.
        """
        if bb is None:
            bb = self.actors
        self.set_bbox(bb)


    def set_bbox(self, bb):
        """Set the bounding box of the scene.

        This can be used to set the scene bounding box to another value
        than the one autocomputed from all actors.

        bb is a (2,3) shaped array specifying a bounding box.
        A special value None may be given to force
        recomputing the bbox from all Actors.
        """
        self._bbox = sane_bbox(coords.bbox(bb))


    def changeMode(self, canvas, mode=None):
        """This function is called when the rendering mode is changed

        This method should be called to update the actors on a rendering
        mode change.
        """
        for a in self.actors:
            a.changeMode(canvas)


    def addAny(self, actor):
        """Add any actor type or a list thereof.

        This will add any actor/annotation/decoration item or a list
        of any such items  to the scene. This is the prefered method to add
        an item to the scene, because it makes sure that each item is added
        to the proper list.
        """
        if isinstance(actor, Actor):
            self.actorlist[actor.rendertype].add(actor)
            if actor.rendertype == 0:
                self._bbox = None
            actor.prepare(self.canvas)
            actor.changeMode(self.canvas)
        elif isinstance(actor, (tuple, list)):
            [self.addAny(a) for a in actor]


    def removeAny(self, actor):
        """Remove a list of any actor/highlights/annotation/decoration items.

        This will remove the items from any of the canvas lists in which the
        item appears.
        itemlist can also be a single item instead of a list.
        If None is specified, all items from all lists will be removed.
        """
        if isinstance(actor, Actor):
            self.actorlist[actor.rendertype].delete(actor)
            if actor.rendertype == 0:
                self._bbox = None
        elif isinstance(actor, (tuple, list)):
            [self.removeAny(a) for a in actor]
        self._bbox = None


    def drawn(self, obj):
        """List the graphical representations of the given object.

        Returns a list with the actors that point to the specifief object.
        """
        return [a for a in self.actors if a.object is obj]


    def removeDrawn(self, obj):
        """Remove all graphical representations of the given object.

        Removes all actors returned by :meth:`drawn(obj)`.
        """
        self.removeAny(self.drawn(obj))


    def clear(self, sticky=False):
        """Clear the whole scene"""
        for v in self.actorlist.values():
            v.clear(sticky)


    def removeHighlight(self, actors=None):
        """Remove the highlight from the actors in the list.

        If no actors list is specified, all the highlights are removed.
        """
        if actors is None:
            actors = self.actors
        for actor in actors:
            actor.removeHighlight()


    def highlighted(self):
        """List highlighted actors"""
        return [a for a in self.actors if a.highlighted()]


    def removeHighlighted(self):
        """Remove the highlighted actors."""
        self.removeAny(self.highlighted())


    def report(self):
        """Report the contents of the scene"""
        return (f"SCENE: "
                f"{len(self.actors)} actors, "
                f"{len(self.annotations)} annotations, "
                f"{len(self.decorations)} decorations"
                f"{len(self.backgrounds)} backgrounds"
                )


##########################################
# Utility functions
#

def sane_bbox(bb):
    """Return a sane nonzero bbox.

    bb should be a (2,3) float array or compatible
    Returns a (2,3) float array where the values of the second
    row are guaranteed larger than the first.
    A value 1 is added in the directions where the input bbox
    has zero size. Also, any NaNs will be transformed to numbers.
    """
    bb = at.checkArray(bb, (2, 3), 'f')
    # make sure we have no NaNs in the bbox
    try:
        bb = np.nan_to_num(bb)
    except Exception as e:
        print("Invalid Bbox: %s" % bb)
        raise e
    # make sure bbox size is nonzero in all directions
    sz = bb[1]-bb[0]
    ds = 0.01 * at.length(sz)
    if ds == 0.0:
        ds = 0.5    # when bbox is zero in all directions
    bb[0, sz==0.0] -= ds
    bb[1, sz==0.0] += ds
    return coords.Coords(bb)

### End
