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
"""Definition of elements for the :class:`~mesh.Mesh` model

This modules provides local numbering schemes of element
connectivities for :class:`~mesh.Mesh` models. It allows a consistent
numbering throughout pyFormex.
When interfacing with other programs, one should be aware
that conversions may be necessary. Conversions to/from external programs
are done by the interface modules.

The module defines the :class:`ElementType` class and a whole slew of its
instances, which are the element types used in pyFormex.
Here is also the definition of the :class:`Elems` class, which is a
specialisation of the :class:`~connectivity.Connectivity` using an
ElementType instance as the eltype. The Elems class is one of the basic
data holders in the :class:`Mesh` model.
"""

import re

import numpy as np

import pyformex as pf
from pyformex import arraytools as at
from pyformex.coords import Coords
from pyformex.connectivity import Connectivity

class InvalidElementType(Exception):
    """Raised for invalid element types."""
    pass

class ElementType():
    """Element types for :class:`Mesh` models.

    An ElementType instance stores all the data that define a particular
    geometrical entity type. It defines the geometrical meaning of a set
    of points in the Mesh geometrical model.

    Several subclasses are defined to easily created families of related
    element types.

    All successfully created element types are stored in the class
    :attr:`register`, from where they can be looked up by their name.

    Parameters
    ----------
    name: str
        The name of the element type. Case is ignored. It is stored in the
        ElementType instance in capitalized form. The key in the register
        is the name in lower case. Often the name has a numeric last
        part equal to the plexitude of the element, but this is not a
        requirement.
    doc: str
        A short description of the element.
    ndim: int
        The dimensionality (:term:`level`) of the element (0..3):

        - 0: point
        - 1: line
        - 2: surface
        - 3: volume
    degree: tuple of int
        For elements that have a parametric formulation, the degree of
        the interpolation functions in the ``ndim`` parametric directions.
    nplex: int
        The plexitude of the element: this is the number of nodes that define
        the geometry of an individual element.
    rst: float :term:`array_like`
        The position of the nodes in parametric space. This array should have
        a shape (ndim, nplex).
    h: tuple of lambda
        A tuple of lambda functions computing the interpolation of the
        element. The tuple should contain exactly nplex functions. Each
        function should take ``ndim`` arguments and return an array
        of nplex values at the nodes. The functions should fulfil the
        finite element requirement:
        ``h[i](rst[:,j]) = 1 if i==j and 0 if i!=j``. This requirement is
        checked when creating the element type.
    order: int :term:`array_like`, optional
        The order in which the nodes are stored, if different from the order
        in ``rst`` and ``h``.
    vertices: float :term:`array_like`, optionally
        The natural coordinates of the nodes (nplex,3). This should be
        be provided if, and only if, the element does not have a parametric
        formulation (specified by degree, rst, h).
        The nodes of the elements are usually defined in a unit space
        [0,1] in each axis direction.
    edges: :class:`Elems`
        A connectivity table listing the edges of the element with local
        node numbers. The eltype of the Elems should be an ElementType
        instance of level 1.
        *This parameter should be provided if and only if the element is
        of level 2 or 3.*
        The edges should be the conceptually correct edges of the element.
        If the element contains edges of different plexitudes, they
        should be specified with the highest plexitude and degenerate
        elements should be used for the lower plexitude edges.
    faces: :class:`Elems`
        A connectivity table listing the faces of the element with local
        node numbers. The eltype of the Elems should be an ElementType
        instance of level 2.
        *This parameter should be provided if and only iff the element is
        of level 3.*
        The faces should be the conceptually correct faces of the element.
        If the element contains faces of different plexitudes, they
        should be specified with the highest plexitude and degenerate
        elements should be used for the lower plexitude faces.
    **kargs: keyword arguments
        Other keyword arguments are stored in the ElementType as is.
        These can also be set after initialization by direct assignment
        to the instance's attribute. Below are some predefined values
        used by pyFormex.
    reverse: int :term:`array_like`
        The order of the nodes for the reversed element. Reversing a line
        element reverses its parametric direction. Reversing a surface element
        reverses the direction of the positive normal. Reversing a volume
        element turns the element inside out (which could possibly be used
        to represent holes in space).
    gl2faces: :class:`Elems`
        A connectivity defining the entities to be used in rendering
        the element. This should only be provided if it the rendered geometry
        should be different from the element itself or from the element
        ``faces``. This is used to draw approximate renderings of elements
        for which there is no correct functionality available: linear
        approximations for higher order elements, triangular subdivisions
        for quadrilaterals. Note that although the name suggests `faces`,
        this connectivity can be of any level.
    gl2edges: :class:`Elems`
        A connectivity defining the entities to be used in `wire` rendering
        of the element. This is like ``gl2faces`` but defines the edges
        to be rendered in the wireframe and smoothwire and flatwire
        rendering modes.
    conversions: dict
        A dict holding the possible strategies for conversion of the element
        to other element types. The key is the target element name, possibly
        extended with an extra string to discriminate between multiple
        strategies leading to the same element. The value is a list of actions
        to undertake to get from the initial element type to the target
        element type. See more details in the section `Element type conversion`
        below.
    extruded: dict
        A dict with data for how to extrude an element to a higher
        level element. Extrusion increases the level of the element with one,
        by creating 1 or 2 new planes of nodes in a new direction.
        The key in the dict is the degree of the extrusion: 1 or 2. The value
        is a tuple (eltype, nodes), where eltype is the target element type
        (an existing ElementType instance) and nodes is a list of nodes numbers
        as they will appear in the new node planes. If nodes is left out of the
        tuple,  they will be ordered exactly like in the original element.
    degenerate: dict
        A dict with data for how to replace a degenerate element with
        a reduced element. A degenerate element has one or more coinciding
        nodes. The reduced elements replaces coinciding nodes with a single
        node yielding an element with lower plexitude.
        The keys in the dict are reduced element types. The values are lists
        of coinciding node conditions and matching reduction schemes: see
        the section **Degenerate element reduction** below for more details.
    subdivide_proxy: ElementType, optional
        An intermediate element type to help in subdividing an element.
        If this is defined, subdivision of the element will be done by
        first converting to the subdivide_proxy type, subdivide that
        element, and convert back to the original.

    Notes
    -----
    The ordering of the ``rst`` and ``h`` defines a fixed local numbering
    scheme of the nodes in the element. It can however be changed by specifying
    the 'order' argument.
    The ordering of the items in ``edges`` and ``faces`` specify the local
    numbering of the edges and faces.
    For solid elements, it is guaranteed that the vertices of all faces are
    numbered in a consecutive order spinning positively around the outward
    normal on the face.

    Some of the parameters of an ElementType are instances of :class:`Elems`,
    but Elems instances contain themselves an :class:`ElementType` instance.
    Therefore care should be taken not to define circular dependencies.
    If the ElementType instances are created in order of increasing level,
    there is no problem with the ``edges`` and ``faces`` parameters, as these
    are of a lower level than the element itself, and will have been defined
    before. For other attributes however this might not always be the case.
    These attributes can then be defined by direct assignment, after the
    needed ElementTypes have been initialized.


    **List of elements**

    The list of available element types can be found from:

    >>> ElementType.list()
    ['point', 'line2', 'line3', 'line4', 'tri3', 'tri6',
     'quad4', 'quad6', 'quad9', 'quad16', 'quad8', 'quad12',
     'tet4', 'tet10', 'tet14', 'tet15', 'wedge6',
     'hex8', 'hex27', 'hex20', 'hex16', 'octa', 'icosa']
    >>> ElementType.printall()
    Available Element Types:
      0-dimensional elements: ['point']
      1-dimensional elements: ['line2', 'line3', 'line4']
      2-dimensional elements: ['tri3', 'tri6', 'quad4', 'quad6', 'quad9',
        'quad16', 'quad8', 'quad12']
      3-dimensional elements: ['tet4', 'tet10', 'tet14', 'tet15', 'wedge6',
        'hex8', 'hex27', 'hex20', 'hex16', 'octa', 'icosa']


    **Element type conversion**

    Element type conversion in pyFormex is a powerful feature to transform
    Mesh type objects. While mostly used to change the element type, there
    are also conversion types that refine the Mesh.

    Available conversion methods are defined in an attribute `conversion`
    of the input element type. This attribute should be a dictionary, where
    the keys are the name of the conversion method and the values describe
    what steps need be taken to achieve this conversion. The method name
    should be the name of the target element, optionally followed by a suffix
    to discriminate between different methods yielding the same target element
    type.
    The suffix should always start with a '-'. The part starting at the '-' will
    be stripped of to set the final target element name.

    E.g., a 'line3' element type is a quadratic line element through three
    points.
    There are two available methods to convert it to 'line2' (straight line
    segments betwee two points), named named 'line2', resp. 'line2-2'.
    The first will transform a 'line3' element in a single 'line2' between
    the two endpoints (i.e. the chord of the quadratic element);
    the second will replace each 'line3' with two straight segments: from
    first to central node, and from central node to end node.

    The values in the dictionary are a list of execution steps to be performed
    in the conversion. Each step is a tuple of a single character defining the
    type of the step, and the data needed by this type of step. The steps are
    executed one by one to go from the source element type to the target.

    Currently, the following step types are defined:

    ==============  =============================================
       Type         Data
    ==============  =============================================
    's' (select)    connectivity list of selected nodes
    'a' (average)   list of tuples of nodes to be averaged
    'v' (via)       string with name of intermediate element type
    'x' (execute)   the name of a proper conversion function
    'r' (random)    list of conversion method names
    ==============  =============================================

    The operation of these methods is as follows:

    - 's' (select): This is the most common conversion type. It selects a set of
      nodes of the input element, and creates one or more new elements with these
      nodes. The data field is a list of tuples defining for each created element
      which node numbers from the source element should be included. This method
      is typically used to reduce the plexitude of the element.

    - 'a' (average): Creates new nodes, the position of which is computed as
      an average of existing nodes. The data field is a list of tuples with
      the numbers of the nodes that should be averaged for each new node. The
      resulting new nodes are added in order at the end of the existing nodes.
      If this order is not the proper local node numbering, an 's' step should
      follow to put the (old and new) nodes in the proper order.
      This method will usually increase the plexitude of the elements.

    - 'v' (via): The conversion is made via an intermediate element type.
      The initial element type is first converted to this intermediate type
      and the result is then transformed to the target type.

    - 'x' (execute): Calls a function to do the conversion. The function takes
      the input Mesh as argument and returns the converted Mesh. Currently this
      function should be a global function in the mesh module. Its name is
      specified as data in the conversion rule.

    - 'r' (random): Chooses a random method between a list of alternatives.
      The data field is a list of conversion method names defined for the
      same element (and thus inside the same dictionary).
      While this could be considered an amusement (e.g. used in the Carpetry
      example), there are serious applications for this, e.g. when
      transforming a Mesh of squares or rectangles into a Mesh of triangles,
      by adding one diagonal in each element.
      Results with such a Mesh may however be different dependent on the choice
      of diagonal. The converted Mesh has directional preferences, not present
      in the original. The Quad4 to Tri3 conversion therefore has the choice to
      use either 'up' or 'down' diagonals. But a better choice is often the
      'random' method, which will put the diagonals in a random direction, thus
      reducing the effect.


    **Degenerate element reduction**

    Each element can have an attribute :attr:`degenerate`, defining some
    rules of how the element can be reduced to a lower plexitude element
    in case it becomes degenerate. An element is said to be degenerate if
    the same node number is used more than once in the connectivity of a
    single element.
    Reduction of degenerate elements is usually only done if the element
    can be reduced to another element of the same level. For example,
    if two node of a quadrilateral element are coinciding, it could be
    replaced with a triangle. Both are level 2 elements.
    When the triangle has two coinciding nodes however, the element is
    normally not reduced to a line (level 1), but rather completely removed
    from the (level 2) model. However, nothing prohibits cross-level reductions.

    The :attr:`degenerate` attribute of an element is a dict where the key
    is a target element and the corresponding value is a list of reduction
    rules. Each rule is a tuple of two items: a set of conditions and
    a node selector to reduce the element.
    The conditions items is itself a tuple of any number of conditions, where
    each condition is a tuple of two node indices. If these nodes are equal,
    the condition is met. If all conditions in a rule are met, the reduction
    rule is applied. The second item in a rule, the node selector, is an index
    specifying the indices of the nodes that should be retained in the new
    (reduced) elements.

    As an example, take the Line3 element, which has 3 nodes defining
    a curved line element. Node 1 is the middle node, and nodes 0 and 2 are
    the end nodes. The element has four ways of being degenerate: nodes 0 and
    1 are the same, nodes 1 and 2 are the same, nodes 0 and 2 are the same,
    and all three nodes are the same. For the first two of them, a reduction
    scheme is defined, reducing the element to a straight line segment (Line2)
    between the two end points::

        Line3.degenerate = {
            Line2: [(((0, 1), ), (0, 2)),
                    (((1, 2), ), (0, 2)), ],
        }

    In this case each of the reduction rules contains only a single
    condition, but there exist cases where multiple conditions have to
    be net at the same time, which is why the condition (0, 1) is itself
    enclosed in a tuple.
    But what about the other degenerate cases. If both end points coincide,
    it is not clear what to do: reduce to a line segment between the
    coincident end points, or between an end point and the middle.
    Here pyFormex made the choice to not reduce such case and leave the
    degenerate Line3 element. But the user could add a rule to e.g.
    reduce the case to a line segment between end point and middle point::

        Line3.degenerate[Line2].append((((0, 2), ), (0, 1)))

    Also the case of three coinciding points is left unhandled. But the user
    could reduce such cases to a Point::

        Line3.degenerate[Point] = [(((0, 1), (1, 2)), (0, ))]

    Here we need two conditions to check that nodes 0, 1 and 2 are equal.
    However, in this case the user probably also wants the third degenerate
    case (nodes 0 and 2 are equal) to be reduced to a Point. So he could
    just use::

        Line3.degenerate[Point] = [(((0, 2), ), (0, ))]


    Attributes
    ----------
    register: dict
        A dict collecting all the created ElementType instances with their
        lower case name as key.
    default: dict
        A dict with the default ElementType for a given plexitude.


    Examples
    --------
    >>> print(ElementType.default)
    {1: Point, 2: Line2, 3: Tri3, 4: Quad4, 6: Wedge6, 8: Hex8}

    """
    # Register of the created element types
    register = {}
    default = {}

    ########
    # Proposed changes in the Element class
    # =====================================
    # - nodal coordinates are specified as follows:
    #   - in symmetry directions: between -1 and +1, centered on 0
    #   - in non-symmetry directions: between 0 and +1, aligned on 0
    # - getCoords() : return coords as is
    # - getAlignedCoords(): return coords between 0 ad 1 and aligned on 0 in all
    #   directions


    def __new__(clas, *args, **kargs):
        """Create a new ElementType instance"""
        # This is here to make sure that all 'ElementType' instances have a
        # _name, even when they are created by unpickling (which does
        # not call __init__). This helps in solving some problems with
        # reading back old pickles, which stored the full ElementType
        # with all its data. Newer versions now only store the
        # name of the ElementType.
        # TODO: We should probably convert the ElementType instances
        # to singleton classes. That would have avoided these problems,
        # as classes are always pickled by name.
        instance = super().__new__(clas)
        instance._name = "no_name"
        return instance

    def _set_elems(self, kargs, attr, ndim):
        """Helper function"""
        if attr in kargs:
            elems = kargs.pop(attr)
            if not isinstance(elems, Elems):
                raise ValueError(f"'{attr}' should be of type Elems")
            setattr(self, attr, elems)

    # def _set_array(self, kargs, attr):
    #     """Helper function"""
    #     if attr in kargs:
    #         arr = kargs.pop(attr)
    #         arr = np.asanyarray(arr)
    #         setattr(self, attr, arr)

    def __init__(self, name, doc, ndim, nplex, register=True,
                 reverse=None, **kargs):
        """Create a new ElementType"""

        lname = name.lower()
        name = name.capitalize()
        if lname in self.__class__.register:
            raise ValueError(
                f"Element type {name} already exists")
        self._name = name
        self.doc = str(doc)
        if ndim not in range(4):
            raise ValueError(
                f"Invalid ndim {ndim}: should be in range(4)")
        self.ndim = ndim
        if nplex <= 0:
            raise ValueError(
                "Plexitude (nplex) should be > 0")
        self.nplex = int(nplex)
        self._set_elems(kargs, 'edges', 1)
        self._set_elems(kargs, 'gl2edges', 1)
        self._set_elems(kargs, 'faces', 2)
        self._set_elems(kargs, 'gl2faces', 2)

        self.reverse = np.s_[::-1] if reverse is None else np.asarray(reverse)

        if 'rst' in kargs:
            self.degree = tuple(kargs.pop('degree'))
            rst = kargs.pop('rst')
            rst = np.atleast_2d(rst)
            if rst.shape != (self.ndim, self.nplex):
                raise ValueError(
                    f"Element {self.name} has incorrect shape for rst: "
                    f"{rst.shape} but expected ({self.ndim}, {self.nplex})")
            self.rst = rst
            if 'h' in kargs:
                self.h = kargs.pop('h')
                if 'fixh' in kargs:
                    f = kargs.pop('fixh')
                    f(self)
            # TODO: we could just keep natureal order, and put this
            # in an 'abq_order' for output to abaqus
            # or make it an option what the internal pyFormex order is
            if 'order' in kargs:
                self.order = kargs.pop('order')
                self.rst = self.rst[:, self.order]
                if hasattr(self, 'h'):
                    self.h = [self.h[i] for i in self.order]
            if 'els' in kargs:
                self._els = kargs.pop('els')
            if 'wts' in kargs:
                self._wts = kargs.pop('wts')

        elif 'vertices' in kargs:
            self._vertices = Coords(kargs['vertices'])

        # reject these obsolete options
        for a in ['drawedges', 'drawedges2', 'drawfaces', 'drawfaces2']:
            if a in kargs:
                print(f"Ignoring attribute {a} of element {name}")
                del kargs[a]

        # other args are added as-is
        if kargs:
            pf.verbose(3, f"REMAINING KARGS: {list(kargs.keys())}")
            self.__dict__.update(kargs)

        # register the element
        if register:
            ElementType.register[name.lower()] = self
            pf.verbose(3, f"Registered element {self}")

        # check the element
        self.check()

    @property
    def name(self):
        return self._name

    @property
    def lname(self):
        return self._name.lower()

    @property
    def r(self):
        return self.rst[0]

    @property
    def s(self):
        return self.rst[1]

    @property
    def t(self):
        return self.rst[2]

    @property
    def vertices(self):
        if hasattr(self, '_vertices'):
            return self._vertices
        return Coords(self.rst.transpose())

    @property
    def dr(self):
        return self.degree[0]

    @property
    def ds(self):
        return self.degree[1]

    @property
    def dt(self):
        return self.degree[2]

    def els(self, *args, **kargs):
        return self._els(self, *args, **kargs)

    def wts(self, *args, **kargs):
        return self._wts(self, *args, **kargs)

    def nvertices(self):
        return self.nplex
    nnodes = nvertices

    def nedges(self):
        """Return the number of edges of the element"""
        try:
            return self.edges.nelems()
        except AttributeError:
            return 0

    def nfaces(self):
        """Return the number of faces of the element"""
        try:
            return self.faces.nelems()
        except AttributeError:
            return 0

    def getEntities(self, level):
        """Return the type and connectivity table of some element entities.

        Parameters
        ----------
        level: int
            The :term:`level` of the entities to return. If negative,
            it is a value relative to the level of the caller. If non-negative,
            it specifies the absolute level. Thus, for an ElementType of
            level 3, getEntities(-1) returns the faces, while for a
            level 2 ElementType, it returns the edges.
            In both cases however, getEntities(1) returns the edges.

        Returns
        -------
        :class:`Elems` | :class:`Connectivity`
            The connectivity table and element type of the entities of
            the specified level. The type is normally Elems.
            If the requested entity level is outside the range 0..ndim,
            an empty Connectivity is returned.

        Examples
        --------
        >>> Tri3.getEntities(0)
        Elems([[0],
               [1],
               [2]], eltype=Point)
        >>> Tri3.getEntities(1)
        Elems([[0, 1],
               [1, 2],
               [2, 0]], eltype=Line2)
        >>> Tri3.getEntities(2)
        Elems([[0, 1, 2]], eltype=Tri3)
        >>> Tri3.getEntities(3)
        Connectivity([], shape=(0, 1))
        """
        if level < 0:
            level = self.ndim + level

        if level < 0 or level > self.ndim:
            return Connectivity()

        if level == 0:
            return Elems(np.arange(self.nplex).reshape((-1, 1)), eltype=Point)

        elif level == self.ndim:
            return Elems(np.arange(self.nplex).reshape((1, -1)), eltype=self)

        elif level == 1:
            return self.edges

        elif level == 2:
            return self.faces

    def getPoints(self):
        """Return the level 0 entities"""
        return self.getEntities(0)

    def getEdges(self):
        """Return the level 1 entities"""
        return self.getEntities(1)

    def getFaces(self):
        """Return the level 2 entities"""
        return self.getEntities(2)

    def getCells(self):
        """Return the level 3 entities"""
        return self.getEntities(3)

    def getElement(self):
        """Return the element connectivity: the entity of level self.ndim"""
        return self.getEntities(self.ndim)

    def getDrawFaces(self, quadratic=False):
        """Return the local connectivity for drawing the element's faces"""
        if not hasattr(self, 'gl2faces'):
            self.gl2faces = self.getFaces()  # .reduceDegenerate()
        return self.gl2faces

    def getDrawEdges(self, quadratic=False):
        """Return the local connectivity for drawing the element's edges"""
        if not hasattr(self, 'gl2edges'):
            self.gl2edges = self.getEdges()  # .reduceDegenerate()
        return self.gl2edges

    def toMesh(self, level=None):
        """Convert the element type to a Mesh.

        Returns a Mesh with a single element of natural size.
        """
        # import here to avoid circular import
        from pyformex.mesh import Mesh
        if level is None:
            level = self.ndim
        return Mesh(self.vertices, self.getEntities(level))

    def toFormex(self):
        """Convert the element type to a Formex.

        Returns a Formex with a single element of natural size.
        """
        return self.toMesh().toFormex()

    def family(self):
        """Return the element family name.

        The element family name is the first part of the lname
        that consists only of lower case letters.
        """
        m = re.match("[a-z]*", self.lname)
        return m[0] if m else ''

    def __str__(self):
        return self._name

    def __repr__(self):
        return self._name

    def report(self):
        return (f"ElementType {self._name}: "
                f"ndim={self.ndim}, nplex={self.nplex}, "
                f"nedges={self.nedges()}, nfaces={self.nfaces()}")

    def isLinear(self):
        return getattr(self, 'linear', None) == self.lname

    def H(self, rst):
        if self.ndim == 0 or not hasattr(self,'h'):
            return None
        elif self.ndim == 1:
            return np.stack([h(rst[0]) for h in self.h])
        elif self.ndim == 2:
            return np.stack([h(rst[0], rst[1]) for h in self.h])
        elif self.ndim == 3:
            return np.stack([h(rst[0], rst[1], rst[2]) for h in self.h])

    def check(self):
        if hasattr(self, 'h'):
            H = self.H(self.rst)
            E = np.eye(self.nplex)
            ok = H.shape == E.shape and np.allclose(H, E)
            pf.verbose(3, f"Element {self} is {'not ' if not ok else ''}ok")
            if not ok:
                print(self.rst)
                print(H)
                raise ValueError("Some element not ok")

    @classmethod
    def list(clas, ndim=None, types=False):
        """Return a list of available ElementTypes.

        Parameters
        ----------
        ndim: int, optional
            If provided, only return the elements of the specified level.
        types: bool, optional
            If True, return ElementType instances. The default is to return
            element names.

        Returns
        -------
        list
            A list of ElementType names (default) or instances.

        Examples
        --------
        >>> ElementType.list()
        ['point', 'line2', 'line3', 'line4', 'tri3', 'tri6',
         'quad4', 'quad6', 'quad9', 'quad16', 'quad8', 'quad12',
         'tet4', 'tet10', 'tet14', 'tet15', 'wedge6',
         'hex8', 'hex27', 'hex20', 'hex16', 'octa', 'icosa']
        >>> ElementType.list(ndim=1)
        ['line2', 'line3', 'line4']
        >>> ElementType.list(ndim=1, types=True)
        [Line2, Line3, Line4]

        """
        eltypes = list(clas.register.values())
        if ndim is not None:
            eltypes = [e for e in eltypes if e.ndim == ndim]
        if types:
            return eltypes
        else:
            return [e.lname for e in eltypes]

    @classmethod
    def printall(clas, lower=False):
        """Print all available element types.

        Prints a list of the names of all available element types,
        grouped by their dimensionality.
        """
        print("Available Element Types:")
        for ndim in range(4):
            print(f"  {ndim}-dimensional elements: {clas.list(ndim)}")


    @classmethod
    def has(clas, elname):
        """Check that an ElementType with the given name exists.

        Parameters
        ----------
        elname: str
            The element name (case insensitive).

        Returns
        -------
        bool
            True if the specified ElementType has been registered.
        """
        return elname.lower() in clas.register


    @classmethod
    def drop(clas, elname):
        """Remove an ElementType from the registry.

        Parameters
        ----------
        elname: str
            The element name (case insensitive).
        """
        elname = elname.lower()
        if elname in clas.register:
            del clas.register[elname]


    @classmethod
    def get(clas, eltype=None, nplex=None, register=True):
        """Find the ElementType matching an element name and/or plexitude.

        Parameters
        ----------
        eltype: :class:`ElementType` | str | None
            The element type or name. If not provided and ``nplex`` is provided,
            the default element type for that plexitude will be used, if it exists.
            If a name, it should be the name of one of the existing ElementType
            instances (case insensitive).
        nplex: int
            The :term:`plexitude` of the element. If provided and an eltype was
            provided, it should match the eltype plexitude. If no eltype was
            provided, the default element type for this plexitude is returned.

        Returns
        -------
        :class:`ElementType`
            The ElementType matching the provided eltype and/or nplex

        Raises
        ------
        ValueError
           If neither ``name`` nor ``nplex`` can resolve into an element type.

        Examples
        --------
        >>> ElementType.get('tri3')
        Tri3
        >>> ElementType.get(nplex=2).lname
        'line2'
        >>> ElementType.get('QUAD4')
        Quad4
        >>> ElementType.get('poly5', register=False)
        Poly5
        >>> ElementType.get('plex17')
        Plex17
        """
        if isinstance(eltype, clas):
            return eltype

        if isinstance(eltype, str):
            eltype = eltype.lower()
            if eltype in clas.register:
                return clas.register[eltype]
            elif eltype == 'polygon' and nplex is not None:
                return clas.polygon(nplex, register=register)
            else:
                m = re.match(r"(poly|plex)(\d+)$", eltype)
                if m:
                    # Create an adhoc Poly... or fake Plex... element
                    name = m.groups()[0]
                    nplex = int(m.groups()[1])
                    if name == 'poly':
                        return clas.polygon(nplex, register=register)
                    else:
                        return clas(eltype, 'A catch-all dummy element', ndim=0,
                                    nplex=nplex, register=False)

        if eltype is None:
            if nplex in clas.default:
                return clas.default[nplex]

        raise InvalidElementType(f"No such element type: {eltype} {nplex}")


    @classmethod
    def polygon(clas, nplex, register=True):
        """Return the Polygon element of the specified plexitude.

        Parameters
        ----------
        nplex: int
            The plexitude of the element, i.e. the number of vertices
            of the polygons. Clearly, nplex should be >= 3.

        Returns
        -------
        ElementType
            An ElementType representing a polygon of the specified
            plexitude. If nplex < 3, an exception is raised.
            For nplex=3 and nplex=4, the returned element type is
            :class:`Tri3` and :class:`Quad4`, respectively. For higher
            plexitude, an element of the :class:`Polygon` family is
            returned, with name Poly## where ## is the plexitude.

        Notes
        -----
        Elements of the :class:`Polygon` family are created on the fly
        when needed, and stored in the element database for later reuse
        if a polygon element of the same plexitude would be required.

        Examples
        --------
        >>> [ElementType.polygon(i, register=False)
        ...     for i in (3, 4, 5, 6, 8, 137)]
        [Tri3, Quad4, Poly5, Poly6, Poly8, Poly137]
        >>> ElementType.polygon(2)
        Traceback (most recent call last):
        ...
        ValueError: nplex=2 is invalid for Polygon elements
        """
        if nplex < 3:
            raise ValueError(f"nplex={nplex} is invalid for Polygon elements")
        elif nplex==3:
            return Tri3
        elif nplex==4:
            return Quad4
        else:
            name = f"Poly{nplex}"
            if ElementType.has(name):
                poly = ElementType.get(name)
            else:
                poly = Polygon(nplex, register=register)
            return poly


#########################################################################
##  Elems
############


class Elems(Connectivity):
    """A Connectivity where the eltype is an ElementType subclass.

    This is a :class:`Connectivity` with knowledge about the
    geometrical meaning of the element type. It is used to store the
    connectivity table of a :class:`Mesh` instance.
    It is also used to store some subitems in the :class:`ElementType`.

    Parameters
    ----------
    data: int :term:`array_like`
        The connectivity data to initialize the Elems. The data should be
        2-dim with shape ``(nelems,nplex)``, where ``nelems`` is the number
        of elements and ``nplex`` is the plexitude of the elements.
        It can be a list, an ndarray or a Connectivity. In the latter case
        it usually shares the storage with that object.
    eltype: class | str
        The element type of the Elems. It is either a subclass of
        :class:`elements.ElementType` or the :meth:`name` of such a subclass.
        That subclass should have the same plexitude as the connectivity
        data. If not provided and the default element type for that plexitude
        will be used if such exists in :attr:`Elementtype.default`.

    Examples
    --------
    >>> L = [[0,1,2],[0,1,3]]
    >>> Elems(L)
    Elems([[0, 1, 2],
           [0, 1, 3]], eltype=Tri3)
    >>> Elems(L, 'tri3')
    Elems([[0, 1, 2],
           [0, 1, 3]], eltype=Tri3)
    >>> Elems(L, Tri3)
    Elems([[0, 1, 2],
           [0, 1, 3]], eltype=Tri3)
    >>> C = Connectivity(L, eltype='tri3')
    >>> Elems(C)
    Elems([[0, 1, 2],
           [0, 1, 3]], eltype=Tri3)
    >>> Elems(C, 'tri3')
    Elems([[0, 1, 2],
           [0, 1, 3]], eltype=Tri3)
    >>> Elems(C, Tri3)
    Elems([[0, 1, 2],
           [0, 1, 3]], eltype=Tri3)
    """
    def __new__(self, data, eltype=None):
        """Create a new Elems"""
        if not isinstance(data, Connectivity):
            data = Connectivity(data=data, eltype=eltype)
        if not isinstance(data.eltype, ElementType):
            data.eltype = ElementType.get(data.eltype, data.nplex())
        if eltype is not None:
            # if eltype == 'polygon':
            #     eltype = ElementType.polygon(data.nplex())
            # else:
            eltype = ElementType.get(eltype, data.nplex())
            if data.nplex() != eltype.nplex:
                if data.nelems() == 0:
                    # Set correct plexitude for empty Elems
                    data = data.reshape(0, eltype.nplex)
                else:
                    raise InvalidElementType(
                        f"Data plexitude ({data.nplex()}) != "
                        f"eltype plexitude ({eltype.nplex})")
            if data.eltype != eltype:
                data.eltype = eltype
        return data.view(self)

    def __repr__(self):
        """String representation of an Elems"""
        res = np.ndarray.__repr__(self)
        res = re.sub("[)]$", f", eltype={self.eltype._name})", res)
        return res

    def __setstate__(self, state):
        """Allow an Elems to be properly unpickled"""
        # An Elems is pickled like a Connectivity, with the
        # ElementType's name as eltype.
        # After unpickling, the eltype should be converted
        # to an ElementType.
        Connectivity.__setstate__(self, state)
        if isinstance(self.eltype, str):
            self.eltype = ElementType.get(self.eltype)
        else:
            # This is a FIX for old pickles that stored full ElementType data
            name = self.eltype.__dict__.get('_name', None)
            if name == 'no_name':
                name = None
            self.eltype = ElementType.get(name, self.shape[1])


    def levelSelector(self, level):
        """Return a selector for lower level entities.

        Parameters
        ----------
        level: int
            An specifying one of the hierarchical levels of element
            entities. See :meth:`Element.getEntities`.

        Returns
        -------
        :class:`Elems`
            A new Elems object with shape
            ``(self.nelems*selector.nelems,selector.nplex)``.

        Examples
        --------
        >>> E = Elems([[0,1,2],[0,1,3],[0,5,3]],'tri3')
        >>> E.levelSelector(1)
        Elems([[0, 1],
               [1, 2],
               [2, 0]], eltype=Line2)

        """
        sel = self.eltype.getEntities(level)
        return Elems(sel, sel.eltype)


    def selectNodes(self, selector):
        """Return a Connectivity with subsets of the nodes.

        Parameters
        ----------
        selector: int | int :term:`array_like`
            A single int specifies a relative or absolute hierarchical level
            of element entities (See the Element class). A 2-dim int array
            selector is then constructed automatically from
            ``self.eltype.getEntities(selector)``.

            Else, it is a 2-dim int array like (often a
            :class:`~connectivity.Connectivity` or another :class:`Elems`.
            Each row of `selector` holds a list of the local node numbers that
            should be retained in the new Connectivity table.

            As an example, if the Elems is plex-3 representing triangles,
            a selector [[0,1],[1,2],[2,0]] would extract the edges of the
            triangle. The same would be obtained with ``selector=-1`` or
            ``selector=1``.

        Returns
        -------
        :class:`Elems` | :class:`~connectivity.Connectivity`
            An Elems or Connectivity object with eltype equal to that of the
            selector. This means that if the selector has an eltype that is
            one of the elements defined in :mod:`elements`, the return type
            will be Elems, else Connectivity.
            The shape is ``(self.nelems*selector.nelems,selector.nplex)``.
            Duplicate elements created by the selector are retained.

        Examples
        --------
        >>> E = Elems([[0,1,2],[0,1,3],[0,5,3]])
        >>> sel = E.levelSelector(1)
        >>> E.selectNodes(sel)
        Elems([[0, 1],
              [1, 2],
              [2, 0],
              [0, 1],
              [1, 3],
              [3, 0],
              [0, 5],
              [5, 3],
              [3, 0]], eltype=Line2)
        >>> E.selectNodes(Elems([[0,1],[0,2]],eltype=Line2))
        Elems([[0, 1],
               [0, 2],
               [0, 1],
               [0, 3],
               [0, 5],
               [0, 3]], eltype=Line2)
        >>> E.selectNodes([[0,1],[0,2]])
        Connectivity([[0, 1],
                      [0, 2],
                      [0, 1],
                      [0, 3],
                      [0, 5],
                      [0, 3]])
        """
        if at.isInt(selector):
            selector = self.levelSelector(selector)
        else:
            selector = Connectivity(selector)
        lo = Connectivity.selectNodes(self, selector)
        clas = Elems if lo.eltype is not None else Connectivity
        return clas(lo, eltype=lo.eltype)


    def insertLevel(self, selector, permutations='all'):
        """Insert an extra hierarchical level in a Connectivity table.

        A Connectivity table identifies higher hierarchical entities in
        function of lower ones. This method inserts an extra level in the
        hierarchy.
        For example, if you have volumes defined in function of points,
        you can insert an intermediate level of edges, or faces.
        Each element may generate multiple instances of the intermediate level.

        Parameters
        ----------
        selector: int | int :term:`array_like`
            A single int specifies a relative or absolute hierarchical level
            of element entities (See the Element class). A 2-dim int array
            selector is then constructed automatically from
            ``self.eltype.getEntities(selector)``.

            Else, it is a 2-dim int array like (often a
            :class:`~connectivity.Connectivity` or another :class:`Elems`.
            Each row of `selector` holds a list of the local node numbers that
            should be retained in the new Connectivity table.
        permutations: str
            Defines which permutations of the row data are allowed while still
            considering the rows equal. Equal rows in the intermediate level
            are collapsed into single items. Possible values are:

            - 'none': no permutations are allowed: rows must match the same date
              at the same positions.
            - 'roll': rolling is allowed. Rows that can be transformed into
              each other by rolling are considered equal;
            - 'all': any permutation of the same data will be considered an
              equal row. This is the default.

        Returns
        -------
        hi: :class:`~connectivity.Connectivity`
            A Connecivity defining the original elements
            in function of the intermediate level ones.
        lo: :class:`Elems` | :class:`~connectivity.Connectivity`
            An Elems or Connectivity object with eltype equal to that of the
            selector. This means that if the selector has an eltype that is
            one of the elements defined in :mod:`elements`, the return type
            will be Elems, else Connectivity.

        The resulting node numbering of the created intermediate entities
        (the `lo` return value) respects the numbering order of the original
        elements and the applied the selector, but in case of collapsing
        duplicate rows, it is undefined which of the collapsed sequences is
        returned.
        Because the precise order of the data in the collapsed rows is lost,
        it is in general not possible to restore the exact original table
        from the two result tables.
        See however :meth:`mesh.Mesh.getBorder` for an application where an
        inverse operation is possible, because the border only contains
        unique rows.

        See also :meth:`mesh.Mesh.combine`, which is an almost inverse operation
        for the general case, if the selector is complete.
        The resulting rows may however be permutations of the original.

        Examples
        --------
        >>> E = Elems([[0,1,2],[0,1,3],[0,5,3]], 'tri3')
        >>> hi, lo = E.insertLevel(1)
        >>> hi
        Connectivity([[0, 4, 1],
                      [0, 5, 2],
                      [3, 6, 2]])
        >>> lo
        Elems([[0, 1],
               [2, 0],
               [3, 0],
               [0, 5],
               [1, 2],
               [1, 3],
               [5, 3]], eltype=Line2)
        >>> hi, lo = E.insertLevel([[0,1],[1,2],[2,0]])
        >>> hi
        Connectivity([[0, 4, 1],
                      [0, 5, 2],
                      [3, 6, 2]])
        >>> lo
        Connectivity([[0, 1],
                      [2, 0],
                      [3, 0],
                      [0, 5],
                      [1, 2],
                      [1, 3],
                      [5, 3]])
        >>> E = Elems([[0,1,2,3]],'quad4')
        >>> hi, lo = E.insertLevel([[0,1,2],[1,2,3],[0,1,1],[0,0,1],[1,0,0]])
        >>> hi
        Connectivity([[1, 2, 0, 0, 0]])
        >>> lo
        Connectivity([[0, 1, 1],
                      [0, 1, 2],
                      [1, 2, 3]])
        """
        if at.isInt(selector):
            selector = self.levelSelector(selector)
        else:
            selector = Connectivity(selector)
        hi, lo = Connectivity.insertLevel(self, selector,
                                          permutations=permutations)
        lo.eltype = selector.eltype
        return hi, lo


    def reduceDegenerate(self, target=None, return_indices=False):
        """Reduce degenerate elements to lower plexitude elements.

        This will try to reduce the degenerate elements of the Elems
        to lower plexitude elements. This is only possible if the ElementType
        has an attribute :attr:`degenerate` containing the proper reduction
        rules.

        Parameters
        ----------
        target: str, optional
            Target element name. If provided, only reductions to that element
            type are performed. Else, all the target element types for which
            a reduction scheme is available, will be tried.
        return_indices: bool, optional
            If True, also returns the indices of the elements in the
            input Elems that are contained in each of the parts returned.

        Returns
        -------
        conn: list of Elems instances
            A list of Elems of which the first one contains the originally
            non-degenerate elements, the next one(s) contain the reduced
            elements (per reduced element type) and the last one contains
            elements that could not be reduced (this may be absent).
            In the following cases a list with only the original is returned:

            - there are no degenerate elements in the Elems;
            - the ElementType does not have any reduction scheme defined;
            - the ElementType does not have a reduction scheme fot the target.
        ind: list of indices, optional
            Only returned if ``return_indices`` is True: the indices of the
            elements of ``self`` contained in each item in ``conn``.

        Note
        ----
        If the Elems is part of a :class:`~mesh.Mesh`, you should
        use the :meth:`mesh.Mesh.splitDegenerate` method instead, as that
        will preserve the property numbers in the resulting Meshes.

        The returned reduced Elems may still be degenerate for
        their own element type.

        See Also
        --------
        mesh.Mesh.splitDegenerate: split mesh in non-degenerate and reduced

        Examples
        --------
        >>> Elems([[0,1,2],[0,1,3]],eltype=Line3).reduceDegenerate()
        [Elems([[0, 1, 2],
                [0, 1, 3]], eltype=Line3)]
        >>> C = Elems([[0,1,2],[0,1,1],[0,3,2]],eltype='line3')
        >>> C.reduceDegenerate()
        [Elems([[0, 1, 2],
                [0, 3, 2]], eltype=Line3), \
        Elems([[0, 1]], eltype=Line2)]
        >>> C = Elems([[0,1,2],[0,1,1],[0,3,2],[1,1,1],[0,0,2]],eltype=Line3)
        >>> C.reduceDegenerate()
        [Elems([[0, 1, 2],
                [0, 3, 2]], eltype=Line3), \
        Elems([[1, 1],
               [0, 2],
               [0, 1]], eltype=Line2)]
        >>> conn, ind = C.reduceDegenerate(return_indices=True)
        >>> conn
        [Elems([[0, 1, 2],
                [0, 3, 2]], eltype=Line3),
        Elems([[1, 1],
               [0, 2],
               [0, 1]], eltype=Line2)]
        >>> ind
        [array([0, 2]), array([3, 4, 1])]
        """
        if not hasattr(self.eltype, 'degenerate'):
            # Can not reduce
            return [self]

        degen = self.testDegenerate()
        if not degen.any():
            # Nothing to reduce
            return [self]

        # get all reductions for this eltype
        strategies = self.eltype.degenerate

        # if target, keep only those leading to target
        if target is not None:
            target = ElementType.get(target)
            s = strategies.get(target, [])
            if s:
                strategies = {target: s}
            else:
                strategies = {}

        if not strategies:
            # No matching strategies
            return [self]

        # non-degenerate: keep
        conn = [self[~degen]]
        ind = [np.where(~degen)[0]]

        # degenerate: reduce
        e = self[degen]
        i = np.where(degen)[0]

        for totype in strategies:

            ids = np.array([], dtype=at.Int)
            elems = []

            for conditions, selector in strategies[totype]:
                cond = np.array(conditions)
                try:
                    w = (e[:, cond[:, 0]] == e[:, cond[:, 1]]).all(axis=1)
                    sel = np.where(w)[0]
                except Exception:
                    raise ValueError(
                        f"Invalid data in {self.eltype}.degenerate:\n"
                        f"{totype} = {(conditions, selector)}")
                    sel = []
                if len(sel) > 0:
                    elems.append(e[sel][:, selector])
                    ids = np.concatenate([ids, i[sel]])
                    # remove the reduced elems from e
                    e = e[~w]
                    i = i[~w]
                    if e.nelems() == 0:
                        break

            if elems:
                elems = np.concatenate(elems)
                conn.append(Elems(elems, eltype=totype))
                ind.append(ids)

            if e.nelems() == 0:
                break

        if e.nelems() > 0:
            conn.append(e)
            ind.append(ids)

        if return_indices:
            return conn, ind
        else:
            return conn


    def extrude(self, nnod, degree):
        """Extrude an Elems to a higher level Elems.

        Parameters
        ----------
        nnod: int
            Node increment for each new node plane. It should be
            higher than the highest node number in self.
        degree: int
            Number of node planes to add. This is also the degree of
            the extrusion. Currently it is limited to 1 or 2.

        The extrusion adds ``degree`` planes of nodes, each with a node
        increment ``nnod``, to the original Elems and then selects
        the target nodes from it as defined by the
        ``self.eltype.extruded[degree]`` value.

        Returns
        -------
        Elems
            An Elems for the extruded element.

        Examples
        --------
        >>> a = Elems([[0,1],[1,2]],eltype=Line2).extrude(3,1)
        >>> print(a)
        [[0 1 4 3]
         [1 2 5 4]]
        >>> print(a.eltype.lname)
        quad4
        >>> a = Elems([[0,1,2],[0,2,3]],eltype=Line3).extrude(4,2)
        >>> print(a)
        [[ 0  2 10  8  1  6  9  4  5]
         [ 0  3 11  8  2  7 10  4  6]]
        >>> print(a.eltype.lname)
        quad9

        """
        try:
            eltype, reorder = self.eltype.extruded[degree]
        except Exception:
            try:
                eltype = self.eltype.lname
            except Exception:
                eltype = None
            raise ValueError("I don't know how to extrude an Elems"
                             "of eltype '{eltype}' in degree {degree}")
        # create hypermesh Elems
        elems = np.concatenate([self+i*nnod for i in range(degree+1)], axis=-1)
        # Reorder nodes if necessary
        if len(reorder) > 0:
            elems = elems[:, reorder]
        return Elems(elems, eltype=eltype)


    def getFreeEntities(self, level=-1, return_indices=False):
        """Return the free entities of the specified level.

        Parameters
        ----------
        level: int
            The :term:`level` of the entities to return. If negative,
            it is a value relative to the level of the caller. If non-negative,
            it specifies the absolute level.
        return_indices: bool
            If True, also returns an index array (nentities,2) for inverse
            lookup of the higher entity (column 0) and its local
            lower entity number (column 1).

        Returns
        -------
        :class:`~elements.Elems`
            A connectivity table with the free entities of the
            specified level. Free entities are entities
            that are only connected to a single element.

        See Also
        --------
        :meth:`Mesh.getFreeEntities`: return the free entities of a Mesh
        :meth:`Mesh.getBorder`: return the border entities of a Mesh

        Examples
        --------
        >>> elems = Elems([[0, 1, 3], [3, 2, 0]], eltype='tri3')
        >>> elems.getFreeEntities(1)
        Elems([[0, 1],
               [2, 0],
               [1, 3],
               [3, 2]], eltype=Line2)
        >>> elems.getFreeEntities(1,True)[1]
        array([[0, 0],
               [1, 1],
               [0, 1],
               [1, 0]])
        """
        hi, lo = self.insertLevel(level)
        if hi.size == 0:
            if return_indices:
                return Connectivity(), []
            else:
                return Connectivity()

        hiinv = hi.inverse(expand=True)
        ncon = (hiinv>=0).sum(axis=1)
        isbrd = (ncon<=1)   # < 1 should not occur
        brd = lo[isbrd]
        if not return_indices:
            return brd

        # also return indices where the border elements come from
        binv = hiinv[isbrd]
        enr = binv[binv >= 0]  # element number
        a = hi[enr]
        b = np.arange(lo.shape[0])[isbrd].reshape(-1, 1)
        fnr = np.where(a==b)[1]   # local border part number
        return brd, np.column_stack([enr, fnr])


#######################################################################
# The collection of default pyFormex elements
#############################################

# A constant we use a lot
e3 = 1./3.
f3 = 2*e3

##########################################
#### Interpolation functions

# 1d, 2d 3d lagrange over a range (0,1)
# 1-dim lagrange formulated directly for degree 1,2,3
lagrange = {
    1: [
        lambda r: 1.-r,
        lambda r: r,
    ],
    2: [
        lambda r: 2*(0.5-r)*(1.-r),
        lambda r: 4*r*(1.-r),
        lambda r: -2*r*(0.5-r),
    ],
    3: [
        lambda r: 9/2*(e3-r)*(f3-r)*(1.-r),
        lambda r: 27/2*r*(f3-r)*(1.-r),
        lambda r: -27/2*r*(e3-r)*(1.-r),
        lambda r: 9/2*r*(e3-r)*(f3-r),
    ]
}

# 2-dim lagrange function factory
def lagrange2(dr, ds, i, j):
    return lambda r,s: lagrange[dr][i](r) * lagrange[ds][j](s)

# 3-dim lagrange function factory
def lagrange3(dr, ds, dt, i, j, k):
    return lambda r,s,t: lagrange[dr][i](r) * lagrange[ds][j](s) * lagrange[dt][k](t)


def seeds(div, degree):
    if at.isInt(div):
        r = np.linspace(0., 1., degree*div+1)
    else:
        r = np.asarray(div)
        if degree > 1:
            a = np.linspace(0., 1., degree+1)[:-1]
            b = [(1.-a)*b + a*c for b,c in zip(r[:-1], r[1:])]
            b.append([1.])
            r = np.concatenate(b)
    return r

##########
# ndim = 0
##########

Point = ElementType(
    'point', "A single point",
    ndim = 0,
    nplex = 1,
    vertices = [[0., 0., 0.]]
)

##########
# ndim = 1
##########

class Lagrange1D(ElementType):
    def __init__(self, deg, **kargs):
        ndim = 1
        nplex = deg+1
        degree = (deg,)
        name = f"Line{nplex}"
        doc = f"A {nplex}-node line element (degree {degree})"
        rst = np.linspace(0., 1., nplex)
        h = lagrange[deg]
        super().__init__(name=name, doc=doc, ndim=ndim, degree=degree,
                         nplex=nplex, rst=rst, h=h, **kargs)

    def els(self, nr):
        return np.row_stack([(np.arange(self.nplex) + i*self.dr)
                            for i in range(nr)])

    def wts(self, rdiv):
        r = seeds(rdiv, self.dr)
        H = np.stack([h(r) for h in self.h])
        return H.reshape((len(self.h), -1)).transpose()


Line2 = Lagrange1D(1)
Line3 = Lagrange1D(2)
Line4 = Lagrange1D(3)

Line3.gl2faces = Elems([(0, 1), (1, 2)], Line2)
Line4.gl2faces = Elems([(0, 1), (1, 2), (2, 3)], Line2)

##########
# ndim = 2
##########

def tri3_els(self, nr, ns=None):
    # ns is not used: always equal to nr
    n = nr+1
    els1 = [np.row_stack([np.array([0, 1, n-j])
                          + i for i in range(nr-j)])
            + j * n - j*(j-1)//2 for j in range(nr)]
    els2 = [np.row_stack([np.array([1, 1+n-j, n-j])
                          + i for i in range(nr-j-1)])
            + j * n - j*(j-1)//2 for j in range(nr-1)]
    elems = np.row_stack(els1+els2)
    return elems

# New tri3_wts: accepts unequal divisions.
def tri3_wts(self, rdiv, sdiv=None):
    r = seeds(rdiv, self.dr)
    nr = len(r)
    if sdiv is None:
        s, ns = r, nr
    else:
        s = seeds(sdiv, self.ds)
        ns = len(s)
        if nr != ns:
            raise ValueError("Tri3: number of divisions along r and s"
                             " directions should be equal")
    ij = np.row_stack([(i,j) for j in range(ns) for i in range(nr-j)])
    rst = np.column_stack(
        [(r[i], s[j]) for j in range(ns) for i in range(nr-j)])
    # Fix for unequal divisions
    for m in range(ij.shape[0]):
        i, j = ij[m]
        if i > 0 and j > 0:
            l = i+j
            a, b = rst[:,m]
            d, e = r[l], s[l]
            p = 1./(a/d + b/e)
            rst[:,m] *= p
    return np.column_stack([1.-rst[0]-rst[1], rst[0], rst[1]])

def tri6_els(self, nr, ns=None):
    # ns is not used: always equal to nr
    n5 = 2*nr+1
    n9 = 4*nr+1
    els1 = [
        np.row_stack([
            np.array([0, 2, n9-4*j, 1, n5+1-2*j, n5-2*j])
            + 2*i for i in range(nr-j)])
        + j * n9 - 2*j*(j-1) for j in range(nr)]
    els2 = [
        np.row_stack([
            np.array([2, n9+2-4*j, n9-4*j, n5+2-2*j, n9+1-4*j, n5+1-2*j])
            + 2*i for i in range(nr-j-1)]) +
        + j * n9 - 2*j*(j-1) for j in range(nr-1)]
    elems = np.row_stack(els1+els2)
    return elems

def tri6_wts(self, rdiv, sdiv=None):
    r = seeds(rdiv, self.dr)
    nr = len(r)
    if sdiv is None:
        s, ns = r, nr
    else:
        s = seeds(sdiv, self.ds)
        ns = len(s)
        if nr != ns:
            raise ValueError("Tri3: number of divisions along r and s"
                             " directions should be equal")
    ij = np.row_stack([(i,j) for j in range(ns) for i in range(nr-j)])
    rst = np.column_stack(
        [(r[i], s[j]) for j in range(ns) for i in range(nr-j)])
    # Fix for unequal divisions
    for m in range(ij.shape[0]):
        i, j = ij[m]
        if i > 0 and j > 0:
            l = i+j
            a, b = rst[:,m]
            d, e = r[l], s[l]
            p = 1./(a/d + b/e)
            rst[:,m] *= p
    r, s = rst
    # r, s = np.meshgrid(r, s)
    H = np.stack([h(r,s) for h in self.h])
    nr = len(r)
    H = H.reshape((len(self.h), -1)).transpose()
    H = np.concatenate([H[nr*j:nr*j+nr-j] for j in range(nr)])
    return H

Tri3 = ElementType(
    'tri3', "A 3-node triangle",
    ndim = 2,
    nplex = 3,
    degree = (1,1),
    edges = Elems([(0, 1), (1, 2), (2, 0)], Line2),
    els = tri3_els,
    wts = tri3_wts,
    rst = [[0., 1., 0.],
           [0., 0., 1.]],
    h = [
        lambda r, s: 1.-r-s,
        lambda r, s: r,
        lambda r, s: s,
    ],
)

Tri6 = ElementType(
    'tri6', "A 6-node triangle",
    ndim = 2,
    nplex = 6,
    degree = (2,2),
    edges = Elems([(0, 3, 1), (1, 4, 2), (2, 5, 0)], Line3),
    reverse = (2, 1, 0, 4, 3, 5),
    gl2faces = Elems([(0, 3, 5), (3, 1, 4), (4, 2, 5), (3, 4, 5)], Tri3),
    gl2edges = Elems([(0, 3), (3, 1), (1, 4), (4, 2), (2, 5), (5, 0)], Line2),
    els = tri6_els,
    wts = tri6_wts,
    rst = [[0., 1., 0., 0.5, 0.5, 0.0],
           [0., 0., 1., 0.0, 0.5, 0.5]],
    h = [
        lambda r, s: (1.-r-s)*(1.-2*r-2*s),
        lambda r, s: r*(2*r-1.),
        lambda r, s: s*(2*s-1.),
        lambda r, s: 4*(1.-r-s)*r,
        lambda r, s: 4*r*s,
        lambda r, s: 4*(1.-r-s)*s,
    ],
)

##############
# Family: quad
##

## Lagrange ##

class Lagrange2D(ElementType):
    def __init__(self, dr, ds, name=None, **kargs):
        ndim = 2
        degree = (dr,ds)
        nplex = (dr+1)*(ds+1)
        if name is None:
            if dr == ds:
                name = f"Quad{nplex}"
            else:
                name = f"Lag2D_{dr}_{ds}"
        doc = f"Lagrange quadrilateral, degree {degree}, nplex {nplex}"
        r = np.linspace(0, 1, dr+1)
        s = np.linspace(0, 1, ds+1)
        r, s = np.meshgrid(r, s)
        rst = np.row_stack([r.ravel(), s.ravel()])
        h =[lagrange2(dr, ds, i, j) for j in range(ds+1) for i in range(dr+1)]
        super().__init__(name=name, doc=doc, ndim=ndim, degree=degree,
                         nplex=nplex, rst=rst, h=h, **kargs)

    def els(self, nr, ns=None):
        if ns is None:
            ns = nr
        dr, ds = self.degree
        ntr = dr*nr + 1
        nts = ds*ns + 1
        n = ntr*nts
        grid = np.arange(n).reshape(nts,ntr)
        stack = []
        dr1, ds1 = dr+1, ds+1
        for j in range(ns):
            jds = j*ds
            for i in range(nr):
                idr = i*dr
                elij = grid[jds:jds+ds1, idr:idr+dr1]
                elij = elij.flat
                if hasattr(self, 'order'):
                    elij = elij[self.order]
                stack.append(elij)
        return np.row_stack(stack)

    def wts(self, rdiv, sdiv=None):
        r = seeds(rdiv, self.dr)
        nr = len(r)
        if sdiv is None:
            s, ns = r, nr
        else:
            s = seeds(sdiv, self.ds)
            ns = len(s)
        r, s = np.meshgrid(r, s)
        H = np.stack([h(r,s) for h in self.h])
        return H.reshape((len(self.h), -1)).transpose()


Quad4 = Lagrange2D(
    1, 1,
    order = [0, 1, 3, 2],
    edges = Elems([(0, 1), (1, 2), (2, 3), (3, 0)], Line2),
)

Quad6 = Lagrange2D(
    2, 1,
    name = 'Quad6',
    order = [0, 2, 5, 3, 1, 4],
    reverse = [1, 0, 3, 2, 4, 5],
    edges = Elems([(0, 4, 1), (1, 1, 2), (2, 5, 3), (3, 3, 0)], Line3),
    gl2edges = Elems([(0, 4), (4, 1), (1, 2), (2, 5), (5, 3), (3, 0)], Line2),
    gl2faces = Elems([(0, 4, 5, 3), (4, 1, 2, 5)], Quad4),
)

Quad9 = Lagrange2D(
    2, 2,
    order = [0, 2, 8, 6, 1, 5, 7, 3, 4],
    reverse = (3, 2, 1, 0, 6, 5, 4, 7, 8),
    edges = Elems([(0, 4, 1), (1, 5, 2), (2, 6, 3), (3, 7, 0)], Line3),
    gl2edges = Elems([(0, 4), (4, 1), (1, 5), (5, 2), (2, 6), (6, 3),
                      (3, 7), (7, 0)], Line2),
    gl2faces = Elems([(0, 4, 8, 7), (1, 5, 8, 4), (2, 6, 8, 5),
                      (3, 7, 8, 6), ], Quad4),
)

Quad16 = Lagrange2D(
    3, 3,
    reverse = (3, 2, 1, 0, 7, 6, 5, 4, 11, 10, 9, 8, 15, 14, 13, 12),
    edges = Elems([(0, 1, 2, 3), (3, 7, 11, 15), (15, 14, 13, 12),
                   (12, 8, 4, 0)], Line4),
    gl2edges = Elems([(0, 1), (1, 2), (2, 3), (3, 7), (7, 11), (11, 15),
                      (15, 14), (14, 13), (13, 12), (12, 8), (8, 4), (4, 0)],
                     Line2),
    gl2faces = Elems(Quad4.els(3)[:,[(0,1,2),(2,3,0)]].reshape(-1,3), Tri3),
)

## Serendipity ##

Quad8 = ElementType(
    'quad8', "An 8-node serendipity quadrilateral of degree {degree}",
    ndim = 2,
    nplex = 8,
    degree = (2,2),
    reverse = (3, 2, 1, 0, 6, 5, 4, 7),
    edges = Quad9.edges,
    gl2edges = Quad9.gl2edges,
    gl2faces = Elems([(0, 4, 7), (1, 5, 4), (2, 6, 5), (3, 7, 6),
                      (4, 5, 6), (4, 6, 7)], Tri3),
    rst = Quad9.rst[:,:8],
    h = [
        lambda r, s: 2*(1.-r)*(1.-s)*(0.5-r-s),
        lambda r, s: 2*r*(1.-s)*(r-s-0.5),
        lambda r, s: 2*r*s*(r+s-1.5),
        lambda r, s: 2*(1.-r)*s*(s-r-0.5),
        lambda r, s: 4*r*(1.-r)*(1.-s),
        lambda r, s: 4*r*s*(1.-s),
        lambda r, s: 4*r*s*(1.-r),
        lambda r, s: 4*(1.-r)*s*(1.-s),
    ],
    subdiv_proxy = Quad9,
)

# Quad13 = ElementType(
#     'quad13', "A 13-node serendipity quadrilateral of degree {degree}",
#     ndim = 2,
#     nplex = 13,
#     degree = (3,3),
#     reverse = (3, 2, 1, 0, 9, 8, 7, 6, 5, 4, 11, 10, 12),
#     edges = Elems([(0, 4, 5, 1), (1, 6, 7, 2), (2, 8, 9, 3), (3, 10, 11, 0)],
#                   Line4),
#     gl2faces = Elems([(0, 4, 11), (1, 6, 5), (2, 8, 7), (3, 10, 9),
#                       (11, 4, 12), (4, 5, 12), (5, 6, 12), (6, 7, 12),
#                       (7, 8, 12), (8, 9, 12), (9, 10, 12), (10, 11, 12)], Tri3),
#     rst = [[0., 1., 1., 0., e3, f3, 1., 1., f3, e3, 0., 0., 0.5],
#            [0., 0., 1., 1., 0., 0., e3, f3, 1., 1., f3, e3, 0.5]],
#     h = [
#          lambda r, s: 9/2 * (r-1) * (s-1) * (r+s-e3) * (r+s-f3),
#          lambda r, s: -9/2 * r * (s-1) * (r-s-e3) * (r-s-f3),
#          lambda r, s: 9/2 * r * s * (r+s-4*e3) * (r+s-5*e3),
#          lambda r, s: -9/2 * (r-1) * s * (r-s+e3) * (r-s+f3),
#          lambda r, s: -27/2 * r * (r-1.) * (r-f3) * (s-1),
#          lambda r, s: 27/2 * r * (r-1.) * (r-e3) * (s-1),
#          lambda r, s: 27/2 * r * s * (s-1) * (s-f3),
#          lambda r, s: -27/2 * r * s * (s-1) * (s-e3),
#          lambda r, s: -27/2 * r * (r-1.) * (r-e3) * s,
#          lambda r, s: 27/2 * r * (r-1.) * (r-f3) * s,
#          lambda r, s: 27/2 * (r-1) * s * (s-1) * (s-e3),
#          lambda r, s: -27/2 * (r-1) * s * (s-1) * (s-f3),
#          lambda r, s: 16 * r * (r-1) * s * (s-1),
#         ],
# )
# Quad13.gl2edges = Quad13.edges.selectNodes(Line4.gl2faces)

# Two not registered Lagrange type elements
# So that we have their automatically generated interpolation functions
Lag2D_3_1 = Lagrange2D(3, 1, register=False)
# reverse = (3, 2, 1, 0, 7, 6, 5, 4),
# edges = Elems([(0, 1, 2, 3), (3, 7, 7, 7), (7, 6, 5, 4),
#                (4, 0, 0, 0)], Line4),
# gl2edges = Elems([(0, 1), (1, 2), (2, 3), (3, 7), (7, 6), (6, 5),
#                   (5, 4), (4, 0)], Line2),
# gl2faces = Elems(Quad4.els(3,1)[:,[(0,1,2),(2,3,0)]].reshape(-1,3), Tri3),
Lag2D_1_3 = Lagrange2D(1, 3, register=False)
# reverse = (3, 2, 1, 0, 7, 6, 5, 4),
# edges = Elems([(0, 1, 1, 1), (1, 3, 5, 7), (7, 6, 6, 6),
#                (6, 4, 2, 0)], Line4),
# gl2edges = Elems([(0, 1), (1, 3), (3, 5), (5, 7), (7, 6), (6, 4),
#                   (4, 2), (2, 0)], Line2),
# gl2faces = Elems(Quad4.els(1,3)[:,[(0,1,2),(2,3,0)]].reshape(-1,3), Tri3),


def Quad12_fixh(self):
    """Compute the 4 corner interpolation functions"""
    for i in range(4):
        v = self.h[i](self.r, self.s)
        w = np.where(~np.isclose(v, 0.))[0]
        w = w[w!=i]
        v = v[w]
        h = [self.h[j] for j in w]
        self.h[i] = lambda r, s, j=i, vv=v, hh=h: Quad4.h[j](r, s) \
            - vv[0] * hh[0](r,s) \
            - vv[1] * hh[1](r,s) \
            - vv[2] * hh[2](r,s) \
            - vv[3] * hh[3](r,s)

Quad12 = ElementType(
    'quad12', "A 12-node serendipity quadrilateral of degree {degree}",
    ndim = 2,
    nplex = 12,
    degree = (3,3),
    reverse = (3, 2, 1, 0, 9, 8, 7, 6, 5, 4, 11, 10),
    edges = Elems([(0, 4, 5, 1), (1, 6, 7, 2), (2, 8, 9, 3), (3, 10, 11, 0)],
                  Line4),
    gl2faces = Elems([(0, 4, 11), (1, 6, 5), (2, 8, 7), (3, 10, 9),
                      (4, 5, 6), (6, 7, 8), (8, 9, 10), (10, 11, 4),
                      (4, 6, 8), (8, 10, 4)], Tri3),
    rst = [[0., 1., 1., 0., e3, f3, 1., 1., f3, e3, 0., 0.],
           [0., 0., 1., 1., 0., 0., e3, f3, 1., 1., f3, e3]],
    h = [
        lambda r, s: Quad4.h[0](r, s),
        lambda r, s: Quad4.h[1](r, s),
        lambda r, s: Quad4.h[2](r, s),
        lambda r, s: Quad4.h[3](r, s),
        lambda r, s: -27/2 * r * (r-1.) * (r-f3) * (s-1),
        lambda r, s: 27/2 * r * (r-1.) * (r-e3) * (s-1),
        lambda r, s: 27/2 * r * s * (s-1) * (s-f3),
        lambda r, s: -27/2 * r * s * (s-1) * (s-e3),
        lambda r, s: -27/2 * r * (r-1.) * (r-e3) * s,
        lambda r, s: 27/2 * r * (r-1.) * (r-f3) * s,
        lambda r, s: 27/2 * (r-1) * s * (s-1) * (s-e3),
        lambda r, s: -27/2 * (r-1) * s * (s-1) * (s-f3),
    ],
    fixh = Quad12_fixh,
    subdiv_proxy = Quad16,
)
Quad12.gl2edges = Quad12.edges.selectNodes(Line4.gl2faces)

######### 3D ###################

#############
# Family: tet
##

def tet4_els(self, nr, ns=None, nt=None):
    # ns, nt not used: requires nr = ns = nt
    n = nr+1  # number of points along an edge
    a = -np.ones((n,n,n), dtype=at.Int)
    nodid = 0
    for k in range(n):
        for j in range(n-k):
            for i in range(n-j-k):
                a[k,j,i] = nodid
                nodid += 1
    els1 = np.row_stack([
        (a[k,j,i], a[k,j,i+1], a[k,j+1,i], a[k+1,j,i])
        for k in range(nr) for j in range(nr-k) for i in range(nr-j-k)])
    n1 = nr-1
    els2 = [np.row_stack([
        (a[k+1,j,i], a[k+1,j+1,i], a[k+1,j,i+1], a[k,j+1,i]),
        (a[k,j+1,i], a[k,j+1,i+1], a[k+1,j+1,i], a[k+1,j,i+1]),
        (a[k,j+1,i], a[k+1,j,i], a[k,j,i+1], a[k+1,j,i+1]),
        (a[k+1,j,i+1], a[k,j+1,i+1], a[k,j,i+1], a[k,j+1,i]),
    ]) for k in range(n1) for j in range(n1-k) for i in range(n1-j-k)]
    return np.concatenate([els1] + els2)


def tet4_wts(self, rdiv, sdiv=None, tdiv=None):
    r = seeds(rdiv, self.dr)
    nr = len(r)
    if sdiv is None:
        s, ns = r, nr
    else:
        s = seeds(sdiv, self.ds)
        ns = len(s)
    if tdiv is None:
        t, nt = s, ns
    else:
        t = seeds(tdiv, self.dt)
        nt = len(t)
    if nr != ns:
        raise ValueError("Tet4: number of divisions along r, s and t"
                         " directions should be equal")
    ijk = np.row_stack([(i,j,k) for k in range(nt)
                       for j in range(ns-k) for i in range(nr-k-j)])
    rst = np.column_stack([(r[i], s[j], t[k]) for k in range(nt)
                           for j in range(ns-k) for i in range(nr-k-j)])
    # fix for unequal divisions
    for m in range(ijk.shape[0]):
        i, j, k = ijk[m]
        if sum([i > 0, j > 0, k > 0]) > 1:
            l = i+j+k
            a, b, c = rst[:,m]
            d, e, f = r[l], s[l], t[l]
            p = 1./(a/d + b/e + c/f)
            rst[:,m] *= p
    return np.column_stack([1.-rst[0]-rst[1]-rst[2], rst[0], rst[1], rst[2]])

Tet4 = ElementType(
    'tet4', "A 4-node tetrahedron",
    ndim = 3,
    nplex = 4,
    degree = (1,1,1),
    reverse = (0, 1, 3, 2),
    edges = Elems([(0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3)], Line2),
    faces = Elems([(0, 3, 2), (0, 1, 3), (0, 2, 1), (1, 2, 3),], Tri3),
    rst = [[0., 1., 0., 0.],
           [0., 0., 1., 0.],
           [0., 0., 0., 1.]],
    h = [
        lambda r, s, t: 1.-r-s-t,
        lambda r, s, t: r,
        lambda r, s, t: s,
        lambda r, s, t: t,
    ],
    els = tet4_els,
    wts = tet4_wts,
)

Tet10 = ElementType(
    'tet10', "A 10-node tetrahedron",
    ndim = 3,
    nplex = 10,
    degree = (2,2,2),
    reverse = (0, 1, 3, 2, 4, 6, 5, 9, 8, 7),
    edges = Elems([(0, 4, 1), (1, 7, 2), (2, 5, 0), (0, 6, 3), (1, 9, 3),
                   (2, 8, 3)], Line3),
    faces = Elems([(0, 3, 2, 6, 8, 5), (0, 1, 3, 4, 9, 6),
                   (0, 2, 1, 5, 7, 4), (1, 2, 3, 7, 8, 9)], Tri6),
    rst = [[0., 1., 0., 0., 0.5, 0.0, 0.0, 0.5, 0.0, 0.5],
           [0., 0., 1., 0., 0.0, 0.5, 0.0, 0.5, 0.5, 0.0],
           [0., 0., 0., 1., 0.0, 0.0, 0.5, 0.0, 0.5, 0.5]],
    h = [
        lambda r, s, t: 2*(r+s+t-1.)*(r+s+t-0.5),
        lambda r, s, t: 2*r*(r-0.5),
        lambda r, s, t: 2*s*(s-0.5),
        lambda r, s, t: 2*t*(t-0.5),
        lambda r, s, t: -4*r*(r+s+t-1.),
        lambda r, s, t: -4*s*(r+s+t-1.),
        lambda r, s, t: -4*t*(r+s+t-1.),
        lambda r, s, t: 4*r*s,
        lambda r, s, t: 4*s*t,
        lambda r, s, t: 4*r*t,
    ],
    subdiv_proxy = Tet4,
)
Tet10.gl2faces = Tet10.faces.selectNodes(Tri6.gl2faces)
Tet10.gl2edges = Tet10.edges.selectNodes(Line3.gl2faces)

Tet14 = ElementType(
    'tet14', "A 14-node tetrahedron",
    ndim = 3,
    nplex = 14,
    vertices = Coords.concatenate([
        Tet10.vertices,
        [(e3, e3, 0.0),
         (0.0, e3, e3),
         (e3, 0.0, e3),
         (e3, e3, e3),
         ]]),
    edges = Tet10.edges,
    faces = Tet10.faces,  # We do not have a Tri7 yet!
    # faces = Elems([(0, 2, 1, 5, 7, 4, 10), (0, 1, 3, 4, 9, 6, 11),
    #                (0, 3, 2, 6, 8, 5, 12), (1, 2, 3, 2, 7, 8, 13)]), Tri7)
    reverse = (0, 1, 3, 2, 4, 6, 5, 9, 8, 7, 12, 11, 10, 13),
    gl2faces = Tet10.gl2faces,
    gl2edges = Tet10.gl2edges,
    subdiv_proxy = Tet4,
)

Tet15 = ElementType(
    'tet15', "A 15-node tetrahedron",
    ndim = 3,
    nplex = 15,
    vertices = Coords.concatenate([
        Tet14.vertices,
        [(0.25, 0.25, 0.25),
         ]]),
    edges = Tet14.edges,
    faces = Tet14.faces,
    reverse = (0, 1, 3, 2, 4, 6, 5, 9, 8, 7, 12, 11, 10, 13, 14),
    gl2faces = Tet14.gl2faces,
    gl2edges = Tet14.gl2edges,
    subdiv_proxy = Tet4,
)



###############
# Family: wedge
##

Wedge6 = ElementType(
    'wedge6', "A 6-node wedge element",
    ndim = 3,
    nplex = 6,
    degree = (1,1,1),
    reverse = (3, 4, 5, 0, 1, 2),
    rst = [[0., 1., 0., 0., 1., 0.],
           [0., 0., 1., 0., 0., 1.],
           [0., 0., 0., 1., 1., 1.]],
    edges = Elems([(0, 1), (1, 2), (2, 0), (0, 3), (1, 4), (2, 5), (3, 4),
                   (4, 5), (5, 3)], 'line2'),
    faces = Elems([(0, 2, 1, 1), (3, 4, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4),
                   (0, 3, 5, 2)], Quad4),
)
# Wedge6.gl2faces = Wedge6.faces.selectNodes(Quad4.gl2faces).removeDegenerate()

#############
# Family: hex
##

class Lagrange3D(ElementType):
    def __init__(self, dr, ds, dt, **kargs):
        ndim = 3
        degree = (dr,ds,dt)
        nplex = (dr+1)*(ds+1)*(dt+1)
        name = f"Hex{nplex}"
        doc = f"A {nplex}-node hexahedral of degree {degree}"
        r = np.linspace(0, 1, dr+1)
        s = np.linspace(0, 1, ds+1)
        t = np.linspace(0, 1, dt+1)
        t, s, r = np.meshgrid(t, s, r, indexing='ij')  # !!! Notice order
        rst = np.row_stack([r.ravel(), s.ravel(), t.ravel()])
        h = [lagrange3(dr, ds, dt, i, j, k)
             for k in range(dt+1) for j in range(ds+1) for i in range(dr+1)]
        super().__init__(name=name, doc=doc, ndim=ndim, degree=degree,
                         nplex=nplex, rst=rst, h=h, **kargs)

    def els(self, nr, ns=None, nt=None):
        if ns is None:
            ns = nr
        if nt is None:
            nt = ns
        dr, ds, dt = self.degree
        ntr = dr*nr + 1
        nts = ds*ns + 1
        ntt = dt*nt + 1
        n = ntr*nts*ntt
        grid = np.arange(n).reshape(ntt,nts,ntr)
        stack = []
        dr1, ds1, dt1 = dr+1, ds+1, dt+1
        for k in range(nt):
            kdt = k*dt
            for j in range(ns):
                jds = j*ds
                for i in range(nr):
                    idr = i*dr
                    elij = grid[kdt:kdt+dt1, jds:jds+ds1, idr:idr+dr1]
                    elij = elij.flat
                    if hasattr(self, 'order'):
                        elij = elij[self.order]
                    stack.append(elij)
        return np.row_stack(stack)

    def wts(self, rdiv, sdiv=None, tdiv=None):
        r = seeds(rdiv, self.dr)
        nr = len(r)
        if sdiv is None:
            s, ns = r, nr
        else:
            s = seeds(sdiv, self.ds)
            ns = len(s)
        if tdiv is None:
            t, nt = s, ns
        else:
            t = seeds(tdiv, self.dt)
            nt = len(t)
        t, s, r = np.meshgrid(t, s, r, indexing='ij')
        H = np.stack([h(r,s,t) for h in self.h])
        return H.reshape((len(self.h), -1)).transpose()


Hex8 = Lagrange3D(
    1, 1, 1,
    order = [0, 1, 3, 2, 4, 5, 7, 6],
    reverse = (4, 5, 6, 7, 0, 1, 2, 3),
    edges = Elems([(0, 1), (1, 2), (2, 3), (3, 0),
                   (4, 5), (5, 6), (6, 7), (7, 4),
                   (0, 4), (1, 5), (2, 6), (3, 7)], Line2),
    faces = Elems([(0, 4, 7, 3), (1, 2, 6, 5),
                   (0, 1, 5, 4), (3, 7, 6, 2),
                   (0, 3, 2, 1), (4, 5, 6, 7)], Quad4),
)
# Hex8.gl2faces = Hex8.faces.selectNodes(Quad4.gl2faces)


# THIS ELEMENT USES A REGULAR NODE NUMBERING!!
# WE MIGHT SWITCH OTHER ELEMENTS TO THIS REGULAR SCHEME TOO
# AND ADD THE RENUMBERING TO THE FE OUTPUT MODULES
Hex27 = Lagrange3D(
    2, 2, 2,
    reverse = np.arange(27).reshape((3,9))[::-1].ravel(),
    edges = Elems([(0, 1, 2), (6, 7, 8), (18, 19, 20), (24, 25, 26),
                  (0, 3, 6), (2, 5, 8), (18, 21, 24), (20, 23, 26),
                   (0, 9, 18), (2, 11, 20), (6, 15, 24), (8, 17, 26)], Line3),
    faces = Elems([(0, 18, 24, 6, 9, 21, 15, 3, 12),
                   (2, 8, 26, 20, 5, 17, 23, 11, 14),
                   (0, 2, 20, 18, 1, 11, 19, 9, 10),
                   (6, 24, 26, 8, 15, 25, 17, 7, 16),
                   (0, 6, 8, 2, 3, 7, 5, 1, 4),
                   (18, 20, 26, 24, 19, 23, 25, 21, 22)], Quad9),
)
Hex27.gl2edges = Hex27.edges.selectNodes(Line3.gl2faces)
Hex27.gl2faces = Hex27.faces.selectNodes(Quad9.gl2faces)


## Serendipity ##

Hex20 = ElementType(
    'hex20', "A 20-node hexahedron",
    ndim = 3,
    nplex = 20,
    degree = (2,2,2),
    order = (0, 1, 2, 3, 8, 9, 10, 11, 4, 5, 6, 7, 12, 13, 14, 15, 16,17,18,19),
    reverse = (4, 5, 6, 7, 0, 1, 2, 3, 12, 13, 14, 15, 8, 9, 10, 11, 16, 17,
               18, 19),
    edges = Elems([(0, 8, 1), (1, 9, 2), (2, 10, 3), (3, 11, 0),
                   (4, 12, 5), (5, 13, 6), (6, 14, 7), (7, 15, 4),
                   (0, 16, 4), (1, 17, 5), (2, 18, 6), (3, 19, 7)], Line3),
    faces = Elems([(0, 4, 7, 3, 16, 15, 19, 11), (1, 2, 6, 5, 9, 18, 13, 17),
                   (0, 1, 5, 4, 8, 17, 12, 16), (3, 7, 6, 2, 19, 14, 18, 10),
                   (0, 3, 2, 1, 11, 10, 9, 8), (4, 5, 6, 7, 12, 13, 14, 15)],
                  Quad8),
    rst = np.row_stack([
        np.concatenate([Quad8.rst, Quad8.rst, Quad8.rst[:,:4]], axis=-1),
        np.concatenate([[0.]*8, [1.]*8, [0.5]*4]),
    ]),
    h = [lambda r,s,t, hj=hi: hj(r,s)*lagrange[2][0](t) for hi in Quad8.h] +
        [lambda r,s,t, hj=hi: hj(r,s)*lagrange[2][2](t) for hi in Quad8.h] +
        [lambda r,s,t, hj=hi: hj(r,s)*lagrange[2][1](t) for hi in Quad8.h[:4]],
    subdiv_proxy = Hex27,
)
Hex20.gl2edges = Hex20.edges.selectNodes(Line3.gl2faces)
Hex20.gl2faces = Hex20.faces.selectNodes(Quad8.gl2faces)

Hex16 = ElementType(
    'hex16', "A 16-node serendipity hexahedron of degree (2,2,1)",
    ndim = 3,
    nplex = 16,
    degree = (2,2,1),
    order = [0, 1, 2, 3, 8, 9, 10, 11, 4, 5, 6, 7, 12, 13, 14, 15],
    reverse = (4, 5, 6, 7, 0, 1, 2, 3, 12, 13, 14, 15, 8, 9, 10, 11),
    edges = Elems([(0, 8, 1), (1, 9, 2), (2, 10, 3), (3, 11, 0),
                  (4, 12, 5), (5, 13, 6), (6, 14, 7), (7, 15, 4),
                   (0, 0, 4), (1, 1, 5), (2, 2, 6), (3, 3, 7)], Line3),
    faces = Elems([(0, 4, 7, 3, 0, 15, 7, 11), (1, 2, 6, 5, 9, 2, 13, 5),
                   (0, 1, 5, 4, 8, 1, 12, 4), (3, 7, 6, 2, 3, 14, 6, 10),
                   (0, 3, 2, 1, 11, 10, 9, 8), (4, 5, 6, 7, 12, 13, 14, 15)],
                  Quad8),
    rst = np.row_stack([
        np.concatenate([Quad8.rst, Quad8.rst], axis=-1),
        np.concatenate([[0.]*8, [1.]*8]),
    ]),
    # !! Notice the use of a local variable hj to replace global hi !!
    h = [lambda r,s,t, hj=hi: hj(r,s)*(1.-t) for hi in Quad8.h] +
        [lambda r,s,t, hj=hi: hj(r,s)*t for hi in Quad8.h],
    subdiv_proxy = Hex20,
)
Hex16.gl2edges = Hex16.edges.selectNodes(Line3.gl2faces).removeDegenerate()
Hex16.gl2faces = Hex16.faces.selectNodes(Quad8.gl2faces).removeDegenerate()


##########################################################
# Some exotic elements not meant for Finite Element applications
# Therefore we only have one of each, with minimal node sets
# TODO: These should probably be moved to another module, as
# they are not really 'elements' but rather meshes.
# But it is easy to use the Mesh methods to get edges and faces :)

##############
# Family: poly
##

# TODO: add conversion to 'tri3'
class Polygon(ElementType):
    """A Polygon element type.

    This element type is useful to define a Mesh of polygons that
    all have the same plexitude. The polygon elements are created
    on demand.

    Examples
    --------
    >>> P = Polygon(5, register=False)
    >>> print(P)
    Poly5
    >>> print(P.getFaces())
    [[0 1 2 3 4]]
    >>> print(P.getDrawFaces())
    [[0 1 2 3 4]]
    >>> print(P.getEdges())
    [[0 1]
     [1 2]
     [2 3]
     [3 4]
     [4 0]]
    >>> print(P.getDrawEdges())
    [[0 1]
     [1 2]
     [2 3]
     [3 4]
     [4 0]]
    """
    def __init__(self, nplex, name=None, **kargs):
        from pyformex.formex import Formex
        ndim = 2
        degree = (1, 1)
        if name is None:
            name = f"Poly{nplex}"
        doc = f"Polygon with {nplex} vertices"
        vertices = Formex([[[1.,0.,0.]]]).rosette(nplex).points()
        elem = np.arange(nplex, dtype=at.Int)
        edges = np.column_stack([elem, np.roll(elem, -1)])
        edges = Elems(edges, eltype=Line2)
        super().__init__(name=name, doc=doc, ndim=ndim, degree=degree,
                         nplex=nplex, vertices=vertices, edges=edges,
                         **kargs)


Octa = ElementType(
    'octa',
    """An octahedron: a regular polyhedron with 8 triangular faces.

    nfaces = 8, nedges = 12, nvertices = 6

    All the faces are equilateral triangles.
    All points of the octahedron lie on a sphere with unit radius.
    """,
    ndim = 3,
    nplex = 6,
    vertices = [(1.0,  0.0,  0.0),
                (0.0,  1.0,  0.0),
                (0.0,  0.0,  1.0),
                (-1.0,  0.0,  0.0),
                (0.0, -1.0,  0.0),
                (0.0,  0.0, -1.0),
                ],
    edges = Elems([(0, 1),  (1, 3), (3, 4), (4, 0),
                  (0, 5),  (5, 3), (3, 2), (2, 0),
                  (1, 2),  (2, 4), (4, 5), (5, 1)], 'line2'),
    faces = Elems([(0, 1, 2),  (1, 3, 2), (3, 4, 2), (4, 0, 2),
                   (1, 0, 5),  (3, 1, 5), (4, 3, 5), (0, 4, 5)], Tri3),
    reverse = (3, 1, 2, 0, 4, 5),
)


from pyformex.arraytools import golden_ratio as phi  # noqa: E402

Icosa = ElementType(
    'icosa',
    """An icosahedron: a regular polyhedron with 20 triangular faces.

    nfaces = 20, nedges = 30, nvertices = 12

    All points of the icosahedron lie on a sphere with unit radius.

    """,
    ndim = 3,
    nplex = 12,
    vertices = Coords([(0.0, 1.0, phi),
                       (0.0, -1.0, phi),
                       (0.0, 1.0, -phi),
                       (0.0, -1.0, -phi),
                       (1.0, phi, 0.0),
                       (-1.0, phi, 0.0),
                       (1.0, -phi, 0.0),
                       (-1.0, -phi, 0.0),
                       (phi, 0.0, 1.0),
                       (phi, 0.0, -1.0),
                       (-phi, 0.0, 1.0),
                       (-phi, 0.0, -1.0),
                       ]),
    edges = Elems([(0, 1),  (0, 8), (1, 8), (0, 10), (1, 10),
                  (2, 3),  (2, 9), (3, 9), (2, 11), (3, 11),
                  (4, 5),  (4, 0), (5, 0), (4, 2), (5, 2),
                  (6, 7),  (6, 1), (7, 1), (6, 3), (7, 3),
                  (8, 9),  (8, 4), (9, 4), (8, 6), (9, 6),
                  (10, 11), (10, 5), (11, 5), (10, 7), (11, 7)], 'line2'),
    faces = Elems([(0, 1, 8),  (1, 0, 10),
                   (2, 3, 11), (3, 2, 9),
                   (4, 5, 0),  (5, 4, 2),
                   (6, 7, 3),  (7, 6, 1),
                   (8, 9, 4),  (9, 8, 6),
                   (10, 11, 7), (11, 10, 5),
                   (0, 8, 4),  (1, 6, 8),
                   (0, 5, 10), (1, 10, 7),
                   (2, 11, 5), (3, 7, 11),
                   (2, 4, 9),  (3, 9, 6)], Tri3),
    reverse = (2, 3, 0, 1, 4, 5, 6, 7, 9, 8, 11, 10),
)

############################################
# list of default element type per plexitude
ElementType.default = {
    1: Point,
    2: Line2,
    3: Tri3,
    4: Quad4,
    6: Wedge6,
    8: Hex8,
}


######################################################################
# element type conversions
##########################
Line2.linear = 'line2'
Line2.conversions = {
    'line3': [('a', [(0, 1)]),
              ('s', [(0, 2, 1)]),
              ],
    'line2-2': [('v', 'line3'),
                ('s', [(0, 2), (2, 1)]), ],
}
Line3.linear = 'line2'
Line3.conversions = {
    'line2': [('s', [(0, 2)]), ],
    'line2-2': [('s', [(0, 1), (1, 2)]), ],
}
Tri3.linear = 'tri3'
Tri3.conversions = {
    'tri3-3': [('a', [(0, 1, 2), ]),
               ('s', [(0, 1, 3), (1, 2, 3), (2, 0, 3)]),
               ],
    'tri3-4': [('v', 'tri6'), ],
    'tri6': [('a', [(0, 1), (1, 2), (2, 0)]), ],
    'quad4': [('v', 'tri6'), ],
}
Tri6.linear = 'tri3'
Tri6.conversions = {
    'tri3': [('s', [(0, 1, 2)]), ],
    'tri3-4': [('s', [(0, 3, 5), (3, 1, 4), (4, 2, 5), (3, 4, 5)]), ],
    'quad4': [('a', [(0, 1, 2), ]),
              ('s', [(0, 3, 6, 5), (1, 4, 6, 3), (2, 5, 6, 4)]),
              ],
}
Quad4.linear = 'quad4'
Quad4.conversions = {
    'tri3': 'tri3-u',
    'tri3-r': [('r', ['tri3-u', 'tri3-d']), ],
    'tri3-u': [('s', [(0, 1, 2), (2, 3, 0)]), ],
    'tri3-d': [('s', [(0, 1, 3), (2, 3, 1)]), ],
    'tri3-x': [('a', [(0, 1, 2, 3)]),
               ('s', [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]),
               ],
    'tri3-*': [('v', 'quad9'), ],
    'quad8': [('a', [(0, 1), (1, 2), (2, 3), (3, 0)])],
    'quad4-4': [('v', 'quad9'), ],
    'quad9': [('v', 'quad8'), ],
    'quad12': [('n', [[e3, f3, 1., 1., f3, e3, 0., 0.],
                      [0., 0., e3, f3, 1., 1., f3, e3]]), ],
}
Quad6.linear = 'quad4'
Quad6.conversions = {
    'tri3': [('v', 'quad4'), ],
    'quad4': [('s', [(0, 4, 5, 3), (4, 1, 2, 5)]), ],
    'quad8': [('a', [(0, 3), (1, 2)]),
              ('s', [(0, 1, 2, 3, 4, 7, 5, 6)])],
    'quad9': [('a', [(0, 3), (1, 2), (4, 5)]), ],
}
Quad8.linear = 'quad4'
Quad8.conversions = {
    'tri3': [('v', 'quad9'), ],
    'tri3-v': [('s', [(0, 4, 7), (1, 5, 4), (2, 6, 5),
                      (3, 7, 6), (5, 6, 4), (7, 4, 6)]), ],
    'tri3-h': [('s', [(0, 4, 7), (1, 5, 4), (2, 6, 5),
                      (3, 7, 6), (4, 5, 7), (6, 7, 5)]), ],
    'quad4': [('s', [(0, 1, 2, 3)]), ],
    'quad4-4': [('v', 'quad9'), ],
    'quad9': [('a', [(4, 5, 6, 7)]), ],
}
Quad9.linear = 'quad4'
Quad9.conversions = {
    'quad8': [('s', [(0, 1, 2, 3, 4, 5, 6, 7)]), ('c', None)],
    'quad4': [('v', 'quad8'), ],
    'quad4-4': [
        ('s', [(0, 4, 8, 7), (4, 1, 5, 8), (7, 8, 6, 3), (8, 5, 2, 6)]), ],
    'tri3': 'tri3-d',
    'tri3-d': [('s', [(0, 4, 7), (4, 1, 5), (5, 2, 6), (6, 3, 7),
                      (7, 4, 8), (4, 5, 8), (5, 6, 8), (6, 7, 8)]), ],
    'tri3-*': [('s', [(0, 4, 8), (4, 1, 8), (1, 5, 8), (5, 2, 8),
                      (2, 6, 8), (6, 3, 8), (3, 7, 8), (7, 0, 8)]), ],
}
Quad16.linear = 'quad4'
Quad16.conversions = {
    'quad12': [('s', [(0,3,15,12,1,2,7,11,14,13,8,4)]), ],
    'quad4': [('s', [(0,3,15,12)]), ],
    'quad4-9': [('s', Quad4.els(3)[:,Quad4.order]), ],
}
Quad12.linear = 'quad4'
Quad12.conversions = {
    'quad16': [('n', [[e3, f3, e3, f3], [e3, e3, f3, f3]]),
               ('s', [(0,4,5,1,11,12,13,6,10,14,15,7,3,9,8,2)]), ],
    'quad4': [('s', [(0,1,2,3)]), ],
}

Tet4.linear = 'tet4'
Tet4.conversions = {
    'tet4-4': [
        ('a', [(0, 1, 2, 3)]),
        ('s', [(0, 1, 2, 4), (0, 3, 1, 4), (1, 3, 2, 4), (2, 3, 0, 4)]), ],
    'tet10': [('a', [(0, 1), (0, 2), (0, 3), (1, 2), (2, 3), (1, 3)]), ],
    'tet14': [('v', 'tet10'), ],
    'tet15': [('v', 'tet14'), ],
    'hex8': [('v', 'tet15'), ],
}
Tet10.linear = 'tet4'
Tet10.conversions = {
    'tet4':  [('s', [(0, 1, 2, 3,)]), ],
    'tet14': [('a', [(0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 2, 3), ]), ],
    'tet15': [('v', 'tet14'), ],
    'hex8': [('v', 'tet15'), ],
}
Tet14.linear = 'tet4'
Tet14.conversions = {
    'tet10': [('s', [(0, 1, 2, 3, 4, 5, 6, 7, 8, 9)]), ],
    'tet4': [('v', 'tet10'), ],
    'tet15': [('a', [(0, 1, 2, 3), ]), ],
    'hex8': [('v', 'tet15'), ],
}
Tet15.linear = 'tet4'
Tet15.conversions = {
    'tet14':  [('s', [(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13)]), ],
    'tet10':  [('v', 'tet14'), ],
    'tet4':  [('v', 'tet10'), ],
    'hex8':  [
        ('s', [(0, 4, 10, 5, 6, 12, 14, 11), (4, 1, 7, 10, 12, 9, 13, 14),
               (5, 10, 7, 2, 11, 14, 13, 8), (6, 12, 14, 11, 3, 9, 13, 8)]), ],
}
Wedge6.linear = 'wedge6'
Wedge6.conversions = {
    'tet4': 'tet4-3',
    # tet4-3 is a compatible tet4-3 scheme
    'tet4-3': [('x', 'wedge6_tet4'), ],
    # tet4-3? has quad diagonals that meet at the same node
    # Here are two (out of six) variants.
    # The schemes may be incompatible at common quad surfaces
    # They are normally only used by tet4-3 conversion
    'tet4-3l': [('s', [(1, 2, 0, 5), (1, 0, 4, 5), (0, 4, 5, 3)]), ],
    'tet4-3r': [('s', [(1, 2, 0, 4), (2, 0, 4, 5), (0, 4, 5, 3)]), ],
    # tet4-8 has no quad diagonals that meet at the same node
    # this case requires a Steiner point
    'tet4-8': [
        ('a', [(0, 1, 2, 3, 4, 5), ]),
        ('s', [(2, 0, 1, 6), (5, 1, 6, 2), (0, 4, 1, 6), (4, 0, 3, 6),
               (2, 3, 0, 6), (5, 4, 3, 6), (5, 1, 4, 6), (3, 2, 5, 6)]), ],
    # tet4-11 has two diagonals, so is always conforming
    'tet4-11': [
        ('a', [(0, 1, 4, 3), (1, 2, 5, 4), (0, 2, 5, 3)]),
        ('s', [(0, 1, 2, 6), (0, 6, 2, 8), (1, 2, 6, 7), (2, 6, 7, 8),
               (1, 7, 6, 4), (0, 6, 8, 3), (2, 8, 7, 5), (6, 7, 8, 3),
               (3, 7, 8, 5), (3, 4, 7, 5), (3, 6, 7, 4)]), ],
}
Hex8.linear = 'hex8'
Hex8.conversions = {
    # The default tet4 provides a compatible scheme with 24 tet4's
    'tet4': 'tet4-24',
    # This scheme only uses 6 tet4's and is compatible
    # if the wedge6 subdivision is compatible.
    'tet4-w': [('v', 'wedge6'), ],
    # The smallest number of tet4 possible, but not compatible.
    'tet4-5': [
        ('s', [(0, 1, 2, 5), (2, 3, 0, 7), (5, 7, 6, 2),
               (7, 5, 4, 0), (0, 5, 2, 7)]), ],
    # This should not be used: default tet4 is better
    # tet4-6 producing compatible triangles on opposite faces
    # (but an adjacent hex might not be compatible)
    'tet4-6': [
        ('s', [(0, 2, 3, 7), (0, 2, 7, 6), (0, 4, 6, 7),
               (0, 6, 1, 2), (0, 6, 4, 1), (5, 6, 1, 4), ]), ],
    # Commented out, because incorrect
    # 'tet4-8': [
    #     ('s', [(0, 1, 3, 4), (1, 2, 0, 5), (2, 3, 1, 6), (3, 0, 2, 7),
    #            (4, 7, 5, 0), (5, 4, 6, 1), (6, 5, 7, 2), (7, 6, 4, 3), ]), ],
    # A scheme that is always compatible
    'tet4-24': [
        ('a', [(0, 3, 2, 1), (0, 1, 5, 4), (0, 4, 7, 3), (1, 2, 6, 5),
               (2, 3, 7, 6), (4, 5, 6, 7)]),
        ('a', [(0, 1, 2, 3, 4, 5, 6, 7)]),
        ('s', [(0, 1, 8, 14), (1, 2, 8, 14), (2, 3, 8, 14), (3, 0, 8, 14),
               (0, 4, 9, 14), (4, 5, 9, 14), (5, 1, 9, 14), (1, 0, 9, 14),
               (0, 3, 10, 14), (3, 7, 10, 14), (7, 4, 10, 14), (4, 0, 10, 14),
               (1, 5, 11, 14), (5, 6, 11, 14), (6, 2, 11, 14), (2, 1, 11, 14),
               (2, 6, 12, 14), (6, 7, 12, 14), (7, 3, 12, 14), (3, 2, 12, 14),
               (4, 7, 13, 14), (7, 6, 13, 14), (6, 5, 13, 14), (5, 4, 13, 14),
               ]), ],
    'wedge6': [('s', [(0, 1, 2, 4, 5, 6), (2, 3, 0, 6, 7, 4)]), ],
    'wedge6-r': [('s', [(0, 4, 5, 3, 7, 6), (0, 5, 1, 3, 6, 2)]), ],
    'hex8-8': [('v', 'hex20'), ],
    'hex20': [('a', [(0, 1), (1, 2), (2, 3), (3, 0),
                     (4, 5), (5, 6), (6, 7), (7, 4),
                     (0, 4), (1, 5), (2, 6), (3, 7), ]), ],
    'hex27': [('v', 'hex20'), ],
}
Hex16.linear = 'hex8'
Hex16.conversions = {
    'hex8': [('v', 'hex20'), ],
    'hex20': [('a', [(0, 4), (1, 5), (2, 6), (3, 7)]),
              ('s', [(0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
                      10, 11, 12, 13, 14, 15, 16, 17, 18, 19)])],
}
Hex20.linear = 'hex8'
Hex20.conversions = {
    'hex8': [('s', [(0, 1, 2, 3, 4, 5, 6, 7)]), ],
    'hex8-8': [('v', 'hex27'), ],
    'hex16': [('s', [(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)]), ],
    'hex27': [('a', [(8, 9, 10, 11), (8, 17, 12, 16), (11, 19, 15, 16),
                     (18, 13, 17, 9), (18, 14, 19, 10), (12, 13, 14, 15), ]),
              ('a', [(20, 21, 22, 23, 24, 25), ]),
              ('s', [(0, 8, 1, 11, 20, 9, 3, 10, 2, 16, 21, 17, 22, 26, 23,
                      19, 24, 18, 4, 12, 5, 15, 25, 13, 7, 14, 6), ]),
              ],
    'tet4': [('v', 'hex8'), ],
}
Hex27.linear = 'hex8'
Hex27.conversions = {
    'hex8-8': [('s', [(0, 1, 4, 3, 9, 10, 13, 12),
                      (1, 2, 5, 4, 10, 11, 14, 13),
                      (3, 4, 7, 6, 12, 13, 16, 15),
                      (4, 5, 8, 7, 13, 14, 17, 16),
                      (9, 10, 13, 12, 18, 19, 22, 21),
                      (10, 11, 14, 13, 19, 20, 23, 22),
                      (12, 13, 16, 15, 21, 22, 25, 24),
                      (13, 14, 17, 16, 22, 23, 26, 25), ]), ],
    'hex20': [('s', [(0, 2, 8, 6, 18, 20, 26, 24, 1, 5, 7, 3, 19, 23, 25, 21,
                      9, 11, 17, 15)]), ],
}

##########################################################
# Extrusion database
####################
#
# NEED TO CHECK THIS !!!!:
# For degree 2, the default order is:
#   first plane, intermediate plane, last plane.

Point.extruded = {1: (Line2, []),
                  2: (Line3, [0, 2, 1])}
Line2.extruded = {1: (Quad4, [0, 1, 3, 2])}
Line3.extruded = {1: (Quad6, [0, 2, 5, 3, 1, 4]),
                  2: (Quad9, [0, 2, 8, 6, 1, 5, 7, 3, 4]), }
Tri3.extruded = {1: (Wedge6, [])}
Quad4.extruded = {1: (Hex8, [])}
Quad8.extruded = {
    1: (Hex16, [0, 1, 2, 3, 8, 9, 10, 11, 4, 5, 6, 7, 12, 13, 14, 15]),
    2: (Hex20, [0, 1, 2, 3, 16, 17, 18, 19, 4, 5, 6, 7,
                20, 21, 22, 23, 8, 9, 10, 11])}
# BV: If Quad9 would be numbered consecutively, extrusion would be as easy as
# Quad9.extruded = { 2: (Hex27, [] }
Quad9.extruded = {2: (Hex27, [0, 4, 1, 7, 8, 5, 3, 6, 2,
                              9, 13, 10, 16, 17, 14, 12, 15, 11,
                              18, 22, 19, 25, 26, 23, 21, 24, 20, ])}

############################################################
# Reduction of degenerate elements
##################################

Line3.degenerate = {
    Line2: [(((0, 1), ), (0, 2)),
            (((1, 2), ), (0, 2)), ],
}

Quad4.degenerate = {
    Tri3: [(((0, 1), ), (0, 2, 3)),
           (((1, 2), ), (0, 1, 3)),
           (((2, 3), ), (0, 1, 2)),
           (((3, 0), ), (0, 1, 2)), ],
}

Hex8.degenerate = {
    Wedge6: [(((0, 1), (4, 5)), (0, 2, 3, 4, 6, 7)),
             (((1, 2), (5, 6)), (0, 1, 3, 4, 5, 7)),
             (((2, 3), (6, 7)), (0, 1, 2, 4, 5, 6)),
             (((3, 0), (7, 4)), (0, 1, 2, 4, 5, 6)),
             (((0, 1), (3, 2)), (0, 4, 5, 3, 7, 6)),
             (((1, 5), (2, 6)), (0, 4, 5, 3, 7, 6)),
             (((5, 4), (6, 7)), (0, 4, 1, 3, 7, 2)),
             (((4, 0), (7, 3)), (0, 5, 1, 3, 6, 2)),
             (((0, 3), (1, 2)), (0, 7, 4, 1, 6, 5)),
             (((3, 7), (2, 6)), (0, 3, 4, 1, 2, 5)),
             (((7, 4), (6, 5)), (0, 3, 4, 1, 2, 5)),
             (((4, 0), (5, 1)), (0, 3, 7, 1, 2, 6)), ],
}

Wedge6.degenerate = {
    Tet4: [(((0, 1), (0, 2)), (0, 3, 4, 5)),
           (((3, 4), (3, 5)), (0, 1, 2, 3)),
           (((0, 3), (1, 4)), (0, 1, 2, 5)),
           (((0, 3), (2, 5)), (0, 1, 2, 4)),
           (((1, 4), (2, 5)), (0, 1, 2, 3)), ],
}


# End
