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

"""A collection of graphical tools for pyFormex.

This is a collection of graphical tools for the pyFormex GUI. Many of
these tools can be invoked from the Tools menu.
"""

import pyformex as pf
from pyformex.core import np, at, gt, utils, Coords, Formex, Mesh, TriSurface
from pyformex.collection import Collection
from pyformex.gui import draw as gs
from pyformex.gui.draw import _T, _I


def mergedSurface(*objects):
    """Create a single surface from multiple Geometry objects

    Parameters
    ----------
    objects: list of Geometry
        Any number of Geometry subclass instances. The objects that are
        TriSurface or convertible to TriSurface are merged into a single
        surface. The other ones are skipped with a message.

    Returns
    -------
    TriSurface
        A single TriSurface containing all the geometry objects convertable
        to surface.
    """
    surfaces = []
    for i, obj in enumerate(objects):
        if not isinstance(obj, TriSurface):
            try:
                obj = obj.toSurface()
            except Exception:
                print(type(obj))
                print(f"Skipping object {i}: can not be converted to TriSurface")
                continue
        surfaces.append(obj)
    if surfaces:
        return TriSurface.concatenate(surfaces)
    return TriSurface()

########################### Labels ####################################

class Label:
    """A colored string attached to a point in 3D.

    Parameters
    ----------
    point: :term:`coords_like` (3,)
        The coordinates of the point where the label is attached.
    text: str
        The string to display at the given point
    color: int
        The color to display the string with. It is an index into
        the current palette (pf.canvas.settings.colormap)

    Notes
    -----
    The Label class is intended to add discrete annotations to a rendering.
    It should not be used to add large annotation sets, like the numbers
    of all elements or nodes. Use :func:`drawNumbers` for that purpose.
    """
    def __init__(self, point, text, color=0):
        self.point = Coords(point).reshape(3,)
        self.text = str(text)
        self.color = int(color)

    def __repr__(self):
        return f"Label({list(self.point)}, '{self.text}', {self.color})"

    def __str__(self):
        with np.printoptions(sign=' ', floatmode='fixed'):
            return f"({self.color}) {np.array2string(self.point, separator=', ')}: {self.text}"

    def match(self, point=None, text=None, color=None):
        """Check if Label attributes match the given values.

        Returns
        -------
        True if the Label's attributes match all the specified arguments.
        """
        return ((point is None or np.allclose(self.point, point)) and
                (text is None or self.text == text) and
                (color is None or self.color == color))

    def print(self, prefix=''):
        """Print a Label to the console"""
        gs.printc(f"{prefix}{self}", color=self.color)

    def edit(self, xactions=[]):
        """Interactively edit a Label.

        Pops up a Dialog to edit each of the Label's attributes.
        A list of extra action tuples (buttontext, function) may
        be specified to add extra action buttons on the Dialog.
        The default has a Cancen and an OK button.
        """
        res = gs.askItems(caption='Edit Label', items=[
            _I('point', self.point, itemtype='point'),
            _I('text', self.text),
            _I('color', self.color),
        ], actions=xactions+[('Cancel',), ('OK',)])
        if res:
            self.__init__(**res)
            return True
        return False


class Labels:
    """A flexibel collection of point annotations

    The Labels class can hold a collection of Label items
    and provides function to interactively add, remove, or edit
    the labels. It can automatically generate text and color for
    new labels. Labels can also be added programmatically.
    In autodraw mode all changes are dynamically
    propagated to the rendering.

    Parameters
    ----------
    gentext: callable, optional
        A function that returns the text for a new label. The
        default will generate texts like 'point-0', 'point-1'...
    gencolor: callable, optional
        A function that returns the color index for a new label.
        The default generates the sequence 0, 1,...
    pointsize: int
        The size of the point drawn where the label is attached.
    gravity: str
        The gravity for alignment of the string with the attachment point.
    fontsize: int
        The font size to use for the label text.
    autodraw: bool
        If True (default), the labels are (re)drawn automatically after
        each add or remove operation.
    autoprint: bool
        If True (default), every label that is added is also printed to the
        console with its color.
    """
    def __init__(self, gentext=None, gencolor=None,
                 pointsize=10, gravity='ne', fontsize=20,
                 autodraw=True, autoprint=True):
        if callable(gentext):
            self.gentext = staticmethod(gentext)
        else:
            self.gentext = utils.autoName('point')
        if callable(gencolor):
            self.gencolor = staticmethod(gencolor)
        else:
            self.gencolor = utils.Counter()
        self.actors = []
        self.pointsize = float(pointsize)
        self.gravity = str(gravity)
        self.fontsize = int(fontsize)
        self.autodraw = bool(autodraw)
        self.autoprint = bool(autoprint)
        self.clear()

    def clear(self):
        """Remove all labels."""
        if self.autodraw:
            self.undraw()
        self.labellist = np.array([], dtype=object)
        self.actors = []

    def __iter__(self):
        """Return an iterator for the Collection"""
        return self.labellist

    @property
    def nlabels(self):
        """Return the number of labels"""
        return len(self.labellist)

    @property
    def points(self):
        """Return a Coords with all label attachment points"""
        return Coords([l.point for l in self.labellist])

    @property
    def texts(self):
        """Return a list with all label texts"""
        return [l.text for l in self.labellist]

    @property
    def colors(self):
        """Return an int array with all labels colors"""
        return np.array([l.color for l in self.labellist], dtype=at.Int)

    def __str__(self):
        return 'Labels:\n' + '\n'.join([f"  {l}" for l in self.labellist])

    def __getitem__(self, index):
        return self.labellist[index]

    def printc(self, header='LABELS:', indent='  '):
        """Print the list of labels in color on the console"""
        if header:
            print(header)
        for l in self.labellist:
            gs.printc(f"{indent}{l}", color=l.color)

    def add(self, labels):
        """Add one or more labels

        Parameters
        ----------
        labels: Label | list[Label]
            One or more :class:`Label` instances to add to the Labels.
        """
        if isinstance(labels, Label):
            labels = [labels]
        if (isinstance(labels, list) and all(
                isinstance(i, Label) for i in labels)):
            self.labellist = np.append(self.labellist, labels)
            if self.autodraw:
                self.draw()
            if self.autoprint:
                for label in labels:
                    label.print()
        else:
            raise ValueError("Expected Label or list of Labels")

    def genLabel(self, point, text=None, color=None):
        """Create a new Label without adding it to the collection.

        Parameters: see :class:`Label`.

        Returns
        -------
        Label
            A Label with the provided attributes or where not provided,
            those generated by the specified or default gentext/gencolor
            function. This Label is not automatically added to the Labels
            collection.

        See Also
        --------
        add: add a Label to the Labels collection
        addLabel: create a Label and add it to the collection
        """
        point = Coords(point).reshape(1,3)
        text = self.gentext() if text is None else str(text)
        color = self.gencolor() if color is None else int(color)
        return Label(point, text, color)

    def addLabel(self, point, text=None, color=None):
        """Create a new label and add it to the collection."""
        label = self.genLabel(point, text, color)
        self.add(label)
        return label

    def match(self, point=None, text=None, color=None):
        """Match labels by point, text and/or color

        Matches all labels in the collection with the given parameters.

        Returns
        -------
        bool array
             A bool array holding True or False for every Label in the
             collection.

        See Also
        --------
        find: return indices of matching labels
        """
        return np.array([item.match(point, text, color)
                         for item in self.labellist], dtype=np.bool)

    def find(self, point=None, text=None, color=None):
        """Return indices fo matching labels.

        Returns
        -------
        int array
            The indices of the labels matching the provided parameters.
        """
        return at.where_1d(self.match(point, text, color))

    def remove(self, point=None, text=None, color=None):
        """Remove labels by point coordinates, text or color

        Removes all the labels matching the provided parameters.
        """
        rem = self.match(point, text, color)
        self.labellist = self.labellist[~rem]
        if self.autodraw:
            self.draw()

    def removeLabel(self, label):
        """Remove a label

        Parameters
        ----------
        label: Label
            A Label to be removed.

        Removed all the labels matching the provided Label's attributes.
        """
        self.remove(label.point, label.text, label.color)

    def draw(self):
        """Draw the collection of labels.

        This keeps track of the generated scene actors, and removes the
        previous ones when a new draw is done. Two actors are drawn: one
        with the dots representing the points, and one with the text strings.
        """
        color = self.colors
        A = [
            gs.draw(self.points, color=color, pointsize=self.pointsize,
                    ontop=True, rendertype=4, bbox='last', view=None),
            gs.drawMarks(self.points, self.texts, colors=color,
                         gravity=self.gravity, size=self.fontsize)
        ]
        gs.drawActor(self.actors[2:])
        gs.undraw(self.actors[:2])
        self.actors[:2] = A

    def undraw(self):
        """Remove the labels from the rendering"""
        gs.undraw(self.actors)


def labelPoints(labels=None, gentext=None, edit=False):
    """Interactively create/edit/remove point labels.

    Starts a point picking mode and creates a label for every picked
    point. The labels are collected in a Labels instance, can be edited
    and removed, and are drawn automatically.

    Parameters
    ----------
    labels: Labels, optional
        A Labels collection of labels. If provided, the labels are added to
        this collection and existing labels can be edited. If not provided,
        a default Labels is created.
    gentext: callable, optional
        Only used if no ``labels`` was provided. The created default Labels
        will then use this function to generate the label text.
    edit: bool, optional
        If True (default), every generated label will immediately show
        an edit Dialog to change its attributes. If False, generated
        labels can not be changed, but may be edited afterwards.

    Returns
    -------
    Labels
        The Labels collection: either the update one that was passed in,
        or a newly generated one.

    Notes
    -----
    Points can be picked one by one or multiple at once. Picked points
    are then handled one by one. If no label exists at point, a new one
    is generated. If edit is True, the label (new or old) can then be
    edited. The edit dialog allows to accept, change or remove the label.
    When all points are handled, a new pick can be done.
    If the CTRL key is depressed during picking, existing labels at the points
    are removed instead of adding/editing labels.
    The procedure stops when the ESC key or right mouse button is pressed.
    The Labels collection is then returned. Labels.undraw() can be used
    to remove them from the screen, and Labels.draw() to show them again.

    Currently, if you edit the coordinates of a point thus that they do
    not match a point of a regular actor, you will not be able to pick
    that point again and thus to edit/remove that label.
    """
    def modify_labels(self):
        from pyformex.gui.qtcanvas import _PICK_SET, _PICK_ADD, _PICK_REMOVE
        nonlocal labels
        def remove(b):
            labels.removeLabel(label)
            b.parent().parent.reject()
        xactions = [('Remove', remove)]
        self.highlightSelection(self.picked)
        points = getPoints(self.picked)
        if self.mod in (_PICK_ADD, _PICK_SET):
            for p in points:
                ids = labels.find(p)
                if len(ids) == 0 and self.mod == _PICK_ADD:
                    label = labels.addLabel(p)
                    if edit:
                        ids = [-1]
                if edit:
                    for i in ids:
                        label = labels.labellist[i]
                        if label.edit(xactions=xactions):
                            labels.draw()
        elif self.mod == _PICK_REMOVE:
            for p in points:
                labels.remove(p)
        self.removeHighlight()

    def label_points_func(self):
        nonlocal labels
        self.selection.keep_order = True  # TODO:this should be an option of pick
        #self.modify_selection()
        modify_labels(self)
        print("Current labels:", labels, sep='\n')

    if isinstance(labels, Labels):
        labels.draw()
    else:
        labels = Labels(gentext=gentext)
    gs.pick('point', func=label_points_func)
    return labels


# Label text options for labelPoints2D
def label_coords2D(P, prec):
    return f" ({P.x:{prec}}, {P.y:{prec}})"

def label_dist2D(P, Q, prec):
    PQ = Q-P
    # return f" h={PQ.x:{prec}}, v={PQ.y:{prec}}, d={at.length(PQ[:2]):{prec}}"
    return f" dist={at.length(PQ[:2]):{prec}} ({PQ.x:{prec}}, {PQ.y:{prec}})"

def label_angle2D(P, Q, R, prec):
    angle = gt.rotationAngle(R-Q, P-Q, m=(0.,0.,1.), angle_spec=at.DEG)[0]
    print(angle)
    return f" angle={angle:{prec}}"


def labelPoints2D(query='point', *,
                  surface=None, missing='r', zvalue=None, npoints=-1,
                  labels=None, gravity='e', drawstyle=2, linewidth=2,
                  prec='+.4f', labeltext=None,
#                  every=1, keeplines=False
                  ):
    """Interactively create and label points on a plane or a surface.

    Puts the user in an interactive projective mode where each mouse click
    generates a 3D point. Since the mouse click only generates two coordinates
    (in a plane perpendicular to the camera axis), the third coordinate
    (depth) has to be defined by projection in the direction of the camera
    axis) onto a surface or a plane. This only works well visually if the camera
    is in projection mode. Therefore perspective mode is switched off during
    the operation (which may slightly change the rendering) and the camera is
    locked. The camera is restored at the end.

    The 'query' parameter defines what type of info is put in the labels
    attached to the/some points. There are currently 4 modes:

    - 'point': every point is labeled with an index.
    - 'coords': every point is labeled with the 2D coordinates of the point.
    - 'dist': every second point is labeled with the 2D distance from the
      previous point.
    - 'angle': after every third point the penultimate point is labeled with
      the 2D angle between the 2D line segments from that point to the next
      and to the previous point.

    All labeled points are collected in a
    :class:`~pyformex.plugins.tools.Labels` instance.
    The operation ends when either a required number of labeled points is
    generated, or the user stops the interactive mode by accepting (right
    mouse button or ENTER key) or cancelling (ESC key).

    Parameters
    ----------
    query: str
        Defines what type of information is put in the labels and how many
        points are labeled. It should be one of 'point', 'coords', 'dist'
        or 'angle'. See explanation above.
    surface: :class:`TriSurface` | '_merged_', optional
        A surface on which to draw the points. If provided, the points are
        created on that surface. A special value '_merged_' will create
        a merged surface of all current actors that can be converted to
        surfaces. Thus it is possible to draw points on a quad Mesh or even
        on the surface of a volume Mesh.
        Mouse clicks outside the surface are handled according to the missing
        parameter.
        Note that this function does not draw the surface itself. The caller
        must make sure that the proper surface is drawn beforehand to guide
        the user in putting the points.
    missing: 'r' | 'o' | 'e'
        In surface mode, defines what to do when clicking outside the surface:
        with the default 'r', no point is created; with 'o', a point is created
        on a plane in front of the surface; with 'e' a ProjecionMissing is
        raised.
    zvalue: float, optional
        The depth value of a plane perpendicular on the camera axis on which
        the points will be created. It is measured from the focus
        point towards the camera eye. Only used if no surface was provided.
        If not provided (and neither is surface), a plane through
        the camera focus is used.
    npoints: int, optional
        The number of points to be created. If < 0 (default), an unlimited number
        of points can be created. It is stopped by clicking the right
        mouse button of hitting ENTER.
    labels: :class:`Labels`, optional
        The Labels class where the generated points should be added. If not
        provided, a new Labels instance is created.
    gravity: str | None
        If not None, overrides the gravity for the labels.
    drawstyle: int
        Type of line decorations drawn with query = 'point' or 'coords'.
    linewidth: float
         Line width to be used in line decorations.
    prec: str
        Format string to use for each of the coordinate values.
    labeltext: callable | None
        If provided, overrides the default label text generator. The
        parameters passed to the callable depend on the query mode: for
        'point' and 'coords', it is (P, prec), where P is the point in camera
        coodinates and prec is the prec argument; for 'dist' mode, two
        points are passed (P, Q, prec) and for 'angle' mode three points
        (P, Q, R, prec).

    Returns
    -------
    labels: :class:`Labels`
        Returns the passed or created Labels instance, with the generated
        points added to it. The 3D global coordinates of the points can be
        obtained from labels.points.

    See Also
    --------
    :func:`pyformex.plugins.tools_menu.labelPoints2DDialog`: provides a
        dialog to set and remember some of the parameters for this function
        and then calls this function with the global Labels collection of the
        Tools menu.
    """
    if isinstance(labels, Labels):
        labels.draw()
    else:
        labels = Labels()
    if gravity is not None:
        labels.gravity = str(gravity)
    color = 0 if labels.colors.size == 0 else labels.colors.max() + 1
    if not labeltext:
        labeltext = {
            'point': None,
            'coords': label_coords2D,
            'dist': label_dist2D,
            'angle': label_angle2D,
            }[query]
    if query != 'coords':
        drawstyle = 0

    def connectPoints(P, Q, style=1):
        """Draw connection between two points"""
        nonlocal color, labels, cs
        PP = P.toCS(cs)
        QQ = Q.toCS(cs)
        RR = Coords([QQ.x, PP.y, 0.])
        #SS = Coords([QQ.x, QQ.y, 0.])
        R = RR.fromCS(cs)
        #S = SS.fromCS(cs)
        if abs(style) == 1:
            F = Formex([[P, Q]]).setProp(color)
        elif abs(style) == 2:
            F = Formex([[P, R], [R, Q]]).setProp(color)
        elif abs(style) == 3:
            F = PolyLine([P, (Q.x, P.y, P.z), (Q.x, Q.y, P.z), Q]).setProp(color)
        A = gs.draw(F, color='prop', linewidth=linewidth, ontop=True)
        #labels.actors.append(A)
        return A

    def add_point(self):
        nonlocal surface, color, labels, cs
        P = self.drawn
        if surface:
            P = P.projectOnSurface(
                surface, dir=pf.canvas.camera.axis, missing=missing)
            if P.shape[0] == 0:
                return  # No point is created
        self.drawing = Coords.concatenate([self.drawing, P])
        if query in ['point', 'coords']:
            P = self.drawing[-1]
            if drawstyle:
                connectPoints(cs.o, P, drawstyle)
            PP = P.toCS(cs)
            text = None if labeltext is None else labeltext(PP, prec)
            label = labels.addLabel(P, text=text, color=color)
            color += 1
        else:
            if query == 'dist' and len(self.drawing) % 2 == 0:
                P, Q = self.drawing[-2:]
                drawn.append(connectPoints(P, Q))
                PP, QQ = P.toCS(cs), Q.toCS(cs)
                text = labeltext(PP, QQ, prec)
                label = labels.addLabel(0.5*(P+Q), text=text, color=color)
                color += 1
            elif query == 'angle' and len(self.drawing) % 3 == 0:
                P, Q, R = self.drawing[-3:]
                drawn.extend([connectPoints(P, Q), connectPoints(Q, R)])
                PP, QQ, RR = P.toCS(cs), Q.toCS(cs), R.toCS(cs)
                text = labeltext(PP, QQ, RR, prec)
                label = labels.addLabel(Q, text=text, color=color)
                color += 1


    drawn = []
    canvas = pf.canvas
    cam = canvas.camera
    _save_perspective = cam.perspective
    gs.perspective(False)
    cam.lock()  # Needed to ensure unproject
    cs = cam.coordsys()
    if surface == '_merged_':
        surface = mergedSurface(*[a.object for a in canvas.actors])
    if isinstance(surface, TriSurface):
        # Use a z value guaranteeing the closest point to the viewer
        zvalue = surface.center().toCS(cs)[2] + 0.5 * surface.dsize()
    else:
        surface = None
        if zvalue is None:
            zvalue = 0.
    front = Coords((0., 0., zvalue)).fromCS(cs)
    zplane = cam.project(front).reshape(3)[2]
    canvas.idraw(zplane=zplane, func=add_point, mouseline=False)
    canvas.removeHighlight()
    cam.unlock()
    gs.perspective(_save_perspective)
    labels.actors.append(drawn)
    return labels


########################### Planes ####################################

class Plane():

    def __init__(self, points, normal=None, size=(1.0, 1.0)):
        pts = Coords(points)
        if pts.shape == (3,) and normal is not None:
            P = pts
            n = Coords(normal)
            if n.shape != (3,):
                raise ValueError("normal does not have correct shape")
        elif pts.shape == (3, 3,):
            P = pts.centroid()
            n = np.cross(pts[1]-pts[0], pts[2]-pts[0])
        else:
            raise ValueError("points has incorrect shape (%s)" % str(pts.shape))
        s = Coords(size)
        self.P = P
        self.n = n
        self.s = s


    def point(self):
        return self.P

    def normal(self):
        return self.n

    def size(self):
        return self.s

    def bbox(self):
        return self.P.bbox()

    def __str__(self):
        return 'P:%s n:%s s:%s' % (list(self.P), list(self.n),
                                   (list(self.s[0]), list(self.s[1])))


    def actor(self, **kargs):
        from pyformex.opengl import actors
        actor = actors.PlaneActor(n=self.n, P=self.P, **kargs)
        return actor


################# Report information about picked objects ################

def getPoints(K):
    """Return all points in the Collection as a Coords"""
    points = []
    if K.obj_type == 'point':
        for k in K.keys():
            v = K[k]
            o = pf.canvas.actors[k].object
            points.append(o.points()[v])
    return Coords.concatenate(points)


def report(K):
    if K is not None and hasattr(K, 'obj_type'):
        if K.obj_type == 'actor':
            return reportActors(K)
        elif K.obj_type == 'element':
            return reportElements(K)
        elif K.obj_type == 'point':
            return reportPoints(K)
        elif K.obj_type == 'edge':
            return reportEdges(K)
        elif K.obj_type == 'prop':
            return reportProps(K)
        elif K.obj_type == 'partition':
            return reportPartitions(K)
    return ''


def indent_str(s, n):
    """Indent a multiline string"""
    return '\n'.join([' '*n + line for line in s.split('\n')])


def reportActors(K):
    def _format(actor):
        if hasattr(actor.object, 'report'):
            return indent_str(actor.object.report(), 2)
        else:
            return f"  {actor.getType()}"

    s = "Actor report\n"
    v = K.get(-1, [])
    s += f"Actors {v}\n"
    s += '\n'.join([f"  Actor {k}:" + _format(pf.canvas.actors[k]) for k in v])
    return s


def reportElements(K):
    s = "Element report\n"
    for k in K.keys():
        v = K[k]
        obj = pf.canvas.actors[k].object
        s += f"Actor {k} ({obj.__class__.__name__}); Elements {v}\n"
        for p in v:
            if isinstance(obj, Formex):
                s += at.stringar(f"  Element {p}: ", obj.coords[p])
            elif isinstance(obj, Mesh):
                e = obj.elems[p]
                s += f"  Element {p}: {e}\n"
                s += at.stringar("    Coords: ", obj.coords[e])
            if p != v[-1]:
                s += '\n'
    return s


def reportPoints(K):
    s = "Point report\n"
    for k in K.keys():
        v = K[k]
        A = pf.canvas.actors[k]
        s += "Actor %s (type %s); Points %s\n" % (k, A.getType(), v)
        x = A.object.points()
        for p in v:
            s += "  Point %s: %s\n" % (p, x[p])
    return s


def reportProps(K):
    s = "Property report\n"
    for k in K.keys():
        v = K[k]
        A = pf.canvas.actors[k]
        t = A.getType()
        s += "Actor %s (type %s); Props %s\n" % (k, t, v)
        for p in v:
            w = np.where(A.object.prop == p)[0]
            s += "  Elements with prop %s: %s\n" % (p, w)
    return s


def reportEdges(K):
    s = "Edge report\n"
    for k in K.keys():
        v = K[k]
        A = pf.canvas.actors[k]
        s += "Actor %s (type %s); Edges %s\n" % (k, A.getType(), v)
        e = A.edges()
        for p in v:
            s += "  Edge %s: %s\n" % (p, e[p])


def reportPartitions(K):
    s = "Partition report\n"
    for k in K.keys():
        P = K[k][0]
        A = pf.canvas.actors[k]
        t = A.getType()
        for l in P.keys():
            v = P[l]
            s += "Actor %s (type %s); Partition %s; Elements %s\n" % (k, t, l, v)
            if t == 'Formex':
                e = A
            elif t == 'TriSurface':
                e = A._elems
            for p in v:
                s += "  Element %s: %s\n" % (p, e[p])
    return s


def getObjectItems(obj, items, mode):
    """Get the specified items from object."""
    if mode == 'actor':
        return [obj[i].object for i in items if hasattr(obj[i], 'object')]
    elif mode in ['element', 'partition']:
        if hasattr(obj, 'object') and hasattr(obj.object, 'select'):
            return obj.object.select(items)
    elif mode == 'point':
        if hasattr(obj, 'points'):
            return obj.object.points()[items]
    return None


def getCollection(K):
    """Returns a collection."""
    if K.obj_type == 'actor':
        return [pf.canvas.actors[int(i)].object for i in K.get(-1, [])
                if hasattr(pf.canvas.actors[int(i)], 'object')]
    elif K.obj_type in ['element', 'point']:
        return [getObjectItems(pf.canvas.actors[k], K[k], K.obj_type)
                for k in K.keys()]
    elif K.obj_type == 'partition':
        return [getObjectItems(pf.canvas.actors[k], K[k][0][prop], K.obj_type)
                for k in K.keys() for prop in K[k][0].keys()]
    else:
        return None


def growCollection(K, **kargs):
    """Grow the collection with n frontal rings.

    K should be a collection of elements.
    This should work on any objects that have a growSelection method, like
    a Mesh.
    """
    if K.obj_type == 'element':
        for k in K.keys():
            o = pf.canvas.actors[k].object
            print(o)
            if hasattr(o, 'growSelection'):
                K[k] = o.growSelection(K[k], **kargs)
            else:
                utils.warn(f"Can not grow selection on type {type(o)}")


def partitionCollection(K):
    """Partition the collection according to node adjacency.

    The actor numbers will be connected to a collection of property numbers,
    e.g. 0 [1 [4,12] 2 [6,20]], where 0 is the actor number, 1 and 2 are the
    property numbers and 4, 12, 6 and 20 are the element numbers.
    """
    sel = getCollection(K)
    if len(sel) == 0:
        print("Nothing to partition!")
        return
    if K.obj_type == 'actor':
        actor_numbers = K.get(-1, [])
        K.clear()
        for i in actor_numbers:
            K.add(np.arange(sel[int(i)].nelems()), i)
    prop = 1
    j = 0
    for i in K.keys():
        p = sel[j].partitionByConnection() + prop
        print("Actor %s partitioned in %s parts" % (i, p.max()-p.min()+1))
        C = Collection()
        C.set(np.transpose(np.asarray([p, K[i]])))
        K[i] = C
        prop += p.max()-p.min()+1
        j += 1
    K.obj_type = 'partition'


def getPartition(K, prop):
    """ Remove all partitions with property not in prop."""
    for k in K.keys():
        for p in K[k][0].keys():
            if p not in prop:
                K[k][0].remove(K[k][0][p], p)


def exportObjects(obj, name, single=False):
    """Export a list of objects under the given name.

    If obj is a list, and single=True, each element of the list is exported
    as a single item. The items will be given the names name-0, name-1, etc.
    Else, the obj is exported as is under the name.
    """
    from pyformex.script import export
    if single and isinstance(obj, list):
        export(dict([(f"name-{i}", v) for i, v in enumerate(obj)]))
    else:
        export({name: obj})


def actorDialog(actorids):
    """Create an actor dialog for the specified actors (by index)

    """
    print("actorDialog %s" % actorids)
    actors = [pf.canvas.actors[i] for i in actorids]
    res = gs.askItems([_T("actor_%s" % i, [
        _I('name', str(a.name)),
        _I('type', str(a.getType()), readonly=True),
        _I('visible', bool(a.visible)),
        _I('alpha', float(a.alpha)),
        _I('objcolor', str(a.objcolor), itemtype='color'),
    ]) for i, a in zip(actorids, actors)])
    print(res)

# End
