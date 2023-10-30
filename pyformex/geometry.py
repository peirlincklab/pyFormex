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
"""A generic interface to the Coords transformation methods

This module defines a generic Geometry superclass which adds all the
possibilities of coordinate transformations offered by the
Coords class to the derived classes.
"""
from abc import ABC, abstractmethod

import numpy as np

import pyformex as pf
from pyformex import utils
import pyformex.arraytools as at
from pyformex.coords import Coords
from pyformex.attributes import Attributes
from pyformex.olist import List


#####################
# Decorators

def _coords_property1(funcname):
    """Export a property on the .coords attribute of the object.

    This is NOT a decorator function.
    It would be good to make it into a decorator though.
    """
    doc = f"""Return the `{funcname}` property of the `coords` attribute of the Geometry object.

    See :attr:`coords.Coords.{funcname}` for details.
    """
    return property(lambda s: getattr(s.coords, funcname), doc=doc)

def _coords_transform(func):
    """Perform a transformation on the .coords attribute of the object."""
    coords_func = getattr(Coords, func.__name__)

    def newf(self, *args, **kargs):
        return self._set_coords(coords_func(self.coords, *args, **kargs))
    newf.__name__ = func.__name__
    newf.__doc__ = (
        f"Apply the :class:`~coords.Coords.{func.__name__}` transformation "
        "to the Geometry object.\n\n"
        f"See :meth:`coords.Coords.{func.__name__}` for details.")
    return newf

def _coords_method(func):
    """Call a method on the .coords attribute of the object."""
    coords_func = getattr(Coords, func.__name__)

    def newf(self, *args, **kargs):
        return coords_func(self.coords, *args, **kargs)
    newf.__name__ = func.__name__
    newf.__doc__ = (
        f"Call Coords.{func.__name__} method "
        "on the Geometry object's coords.\n\n"
        f"See :meth:`coords.Coords.{func.__name__}` for details.")
    return newf


################################

class Geometry(ABC):
    """A virtual base class for all geometry classes in pyFormex.

    The Geometry class is a generic parent class for all geometry classes
    in pyFormex. It is not intended to be used directly, but only through
    derived classes.
    Examples of derived classes are :class:`~formex.Formex`,
    :class:`~mesh.Mesh`, :class:`~trisurface.TriSurface`,
    :class:`~curve.PolyLine`, :class:`~curve.BezierSpline`,
    :class:`~plugins.nurbs.NurbsCurve, :class:`~plugins.nurbs.NurbsCurve,
    :class:`~polygons.Polygons`.

    The basic entity of geometry is the point, defined by its coordinates.
    The Geometry class expects these to be stored in a :class:`~coords.Coords`
    object assigned to the :attr:`coords` attribute (it is the responsability
    of the derived class object initialisation to do this).

    The Geometry class exposes the following attributes of the :attr:`coords`
    attribute, so that they can be directly used on the Geometry object:
    :attr:`xyz`,
    :attr:`x`,
    :attr:`y`,
    :attr:`z`,
    :attr:`xy`,
    :attr:`yz`,
    :attr:`xz`.

    The Geometry class exposes a large set of Coords methods for direct use
    on the derived class objects. These methods are automatically executed
    on the ``coords`` attribute of the object. One set of such methods are
    those returning some information about the Coords:
    :meth:`points`,
    :meth:`bbox`,
    :meth:`center`,
    :meth:`bboxPoint`,
    :meth:`centroid`,
    :meth:`sizes`,
    :meth:`dsize`,
    :meth:`bsphere`,
    :meth:`bboxes`,
    :meth:`inertia`,
    :meth:`principalCS`,
    :meth:`principalSizes`,
    :meth:`distanceFromPlane`,
    :meth:`distanceFromLine`,
    :meth:`distanceFromPoint`,
    :meth:`directionalSize`,
    :meth:`directionalWidth`,
    :meth:`directionalExtremes`.
    Thus, if F is an instance of class :class:`~formex.Formex`, then one
    can use ``F.center()`` as a convenient shorthand for ``F.coords.center()``.

    Likewise, most of the transformation methods of the :class:~coords.Coords`
    class are exported through the Geometry class to the derived classes.
    When called, they will return a new object identical to the original,
    except for the coordinates, which are transformed by the specified method.
    Refer to the correponding :class:`~coords.Coords` method for the precise
    arguments of these methods:
    :meth:`scale`,
    :meth:`adjust`,
    :meth:`translate`,
    :meth:`centered`,
    :meth:`align`,
    :meth:`rotate`,
    :meth:`shear`,
    :meth:`reflect`,
    :meth:`affine`,
    :meth:`toCS`,
    :meth:`fromCS`,
    :meth:`transformCS`,
    :meth:`position`,
    :meth:`cylindrical`,
    :meth:`hyperCylindrical`,
    :meth:`toCylindrical`,
    :meth:`spherical`,
    :meth:`superSpherical`,
    :meth:`toSpherical`,
    :meth:`circulize`,
    :meth:`bump`,
    :meth:`flare`,
    :meth:`map`,
    :meth:`map1`,
    :meth:`mapd`,
    :meth:`copyAxes`,
    :meth:`swapAxes`,
    :meth:`permuteAxes`,
    :meth:`rollAxes`,
    :meth:`projectOnPlane`,
    :meth:`projectOnSphere`,
    :meth:`projectOnCylinder`,
    :meth:`isopar`,
    :meth:`addNoise`,
    :meth:`rot`,
    :meth:`trl`.

    Geometry is a lot more than points however. Therefore the Geometry
    and its derived classes can represent higher level entities, such as
    lines, planes, circles, triangles, cubes,... These entities are often
    represented by multiple points: a line segment would e.g. need two points,
    a triangle three. Geometry subclasses can implement collections
    of many such entities, just like the :class:`~coords.Coords` can hold
    many points. We call these geometric entities 'elements'. The subclass
    must at least define a method :meth:`nelems` returning the number
    of elements in the object, even if there is only one.

    The Geometry class allows the attribution of a property number
    per element. This is an integer number that can be used as the subclass
    or user wants. It could be just the element number, or a key into
    a database with lots of more element attributes. The Geometry class
    provides methods to handle these property numbers.

    The Geometry class provides a separate mechanism to store attributes
    related to how the geometry should be rendered. For this purpose
    the class defines an ``attrib`` attribute which is an object of
    class :class:`~attributes.Attributes`. This attribute is callable
    to set any key/value pairs in its dict. For example,
    ``F.attrib(color=yellow)`` will make the object F always be drawn
    in yellow.

    The Geometry class provides for adding fields to instances of the
    derived classes. Fields are numerical data (scalar or vectorial)
    that are defined over the geometry. For example, if the geometry
    represents a surface, the gaussian curvature of that surface is a
    field defined over the surface. Field data are stored in
    :class:`~field.Field` objects and the Geometry object stores them
    internally in a dict object with the field name as key. The dict is
    kept in an attribute ``fields`` that is only created when the first
    Field is added to the object.

    Finally, the Geometry class also provides the interface for storing
    the Geometry object on a file in pyFormex's own 'pgf' format.


    Note
    ----
    When subclassing the Geometry class, care should be taken to obey
    some rules in order for all the above to work properly.
    See `UserGuide`.

    """
    # REMOVED for new Sphinx

    # Attributes
    # ----------
    # coords: :class:`~coords.Coords`
    #     A Coords object that holds the coordinates of the points required
    #     to describe the type of geometry.
    # prop: int array
    #     Element property numbers. This is a 1-dim int array with length
    #     :meth:`nelems`. Each element of the
    #     Geometry can thus be assigned an integer value. It is up the
    #     the subclass to define if and how its instances are divided into
    #     elements, and how to use this element property number.
    # attrib: :class:`~attributes.Attributes`
    #     An Attributes object that is primarily used to define persisting
    #     drawing attributes (like color) for the Geometry object.
    # fields: dict
    #     A dict with the Fields defined on the object. This atribute only
    #     exists when at least one Field has been defined. See :meth:`addField`.

    # _attributes_ = [ 'xyz', 'x', 'y', 'z', 'xy', 'xz', 'yz' ]


    def __init__(self):
        """Initialize a Geometry"""
        self.prop = None
        self.coords = None
        self.attrib = Attributes()

    # TODO: put Attributes in self._attrib, make self.attrib a property
    #       and setAttrib a property setter

    def setAttrib(self, **kargs):
        """Set attributes on the Geometry.

        While the attributes can be directly set by calling self.attrib,
        using this function returns the parent object and can thus be chained
        in a sequence of calls::

            M = Mesh(...)
            M.attrib(**kargs)
            M = M.transform(...)

        can thus be replaced by::

            M = Mesh(...).setAttrib(**kargs).transform(...)
        """
        self.attrib(**kargs)
        if 'name' in kargs:
            pf.PF[kargs['name']] = self
        return self


    ##########################################################################
    #
    #   Set the coords
    #
    ##########################################################################


    def _set_coords_inplace(self, coords):
        """Replace the current coords with new ones.

        """
        coords = Coords(coords)
        if coords.shape == self.coords.shape:
            self.coords = coords
            return self
        else:
            raise ValueError("Invalid reinitialization of Geometry coords")


    def _set_coords_copy(self, coords):
        """Return a copy of the object with new coordinates replacing the old.

        """
        return self.copy()._set_coords_inplace(coords)


    # The default _set_coords inherited by subclasses
    _set_coords = _set_coords_copy



    xyz = _coords_property1('xyz')
    x = _coords_property1('x')
    y = _coords_property1('y')
    z = _coords_property1('z')
    xy = _coords_property1('xy')
    xz = _coords_property1('xz')
    yz = _coords_property1('yz')

    @xyz.setter
    def xyz(self, value):
        self.coords.xyz = value

    @x.setter
    def x(self, value):
        self.coords.x = value

    @y.setter
    def y(self, value):
        self.coords.y = value

    @z.setter
    def z(self, value):
        self.coords.z = value

    @xy.setter
    def xy(self, value):
        self.coords.xy = value

    @yz.setter
    def yz(self, value):
        self.coords.yz = value

    @xz.setter
    def xz(self, value):
        self.coords.xz = value


    ##########################################################################
    #
    #   Return information about the coords
    #
    ##########################################################################


    @abstractmethod
    def nelems(self):
        """Return the number of elements in the Geometry.

        Returns
        -------
        int
            The number of elements in the Geometry. This is an abstract
            method that should be reimplemented by the derived class.
        """
        return 0


    def level(self):
        """Return the dimensionality of the Geometry

        The level of a :class:`Geometry` is the dimensionality of the
        geometric object(s) represented:

        - 0: points
        - 1: line objects
        - 2: surface objects
        - 3: volume objects

        Returns
        -------
        int
            The level of the Geometry, or -1 if it is unknown. This
            should be implemented by the derived class. The Geometry
            base class always returns -1.

        """
        return -1


    def info(self):
        """Return a short string representation about the object

        """
        return (f"Geometry: coords shape = {self.coords.shape}; "
                f"level = {self.level()}")


    @_coords_method
    def points(self):
        pass

    @_coords_method
    def bbox(self):
        pass

    @_coords_method
    def center(self):
        pass

    @_coords_method
    def bboxPoint(self, *args, **kargs):
        pass

    @_coords_method
    def centroid(self):
        pass

    @_coords_method
    def sizes(self):
        pass

    @_coords_method
    def dsize(self):
        pass

    @_coords_method
    def bsphere(self):
        pass

    @_coords_method
    def bboxes(self):
        pass

    @_coords_method
    def inertia(self, *args, **kargs):
        pass

    @_coords_method
    def principalCS(self, *args, **kargs):
        pass

    @_coords_method
    def principalSizes(self):
        pass

    @_coords_method
    def distanceFromPlane(self, *args, **kargs):
        pass

    @_coords_method
    def distanceFromLine(self, *args, **kargs):
        pass

    @_coords_method
    def distanceFromPoint(self, *args, **kargs):
        pass

    @_coords_method
    def directionalSize(self, *args, **kargs):
        pass

    @_coords_method
    def directionalWidth(self, *args, **kargs):
        pass

    @_coords_method
    def directionalExtremes(self, *args, **kargs):
        pass


    def convexHull(self, dir=None, return_mesh=True):
        """Return the convex hull of a Geometry.

        This is the :meth:`~coords.Coords.convexHull` applied to the
        ``coords`` attribute, but it has ``return_mesh=True`` as
        default.

        Returns
        -------
        Mesh
            The convex hull of the geometry.
        """
        return self.coords.convexHull(dir, return_mesh)


    def testPlane(self, p, n, atol=0.0):
        """Test what parts of a Formex or Mesh are at either side of a plane.

        Parameters
        ----------
        p: :term:`array_like` (3,)
            A point in the testing plane
        n: :term:`array_like` (3,)
            The positive normal on the plane
        atol: float
            Tolerance value to be added to the tests. Specifying a small
            positive value will make sure that elements located at one
            side of the plane, but having one or more points inside the
            plane, will be considered completely at one side. A negative
            value will include these elements with the ones vut by the
            plane.


        Returns
        -------
        tp: bool array (nelems,)
            True for the elements that are completely at the positive side
            of the plane
        tc: bool array (nelems,)
            True for the elements that are cut by the plane
        tn: bool array (nelems,)
            True for the elements that are completely at the negative side
        """
        tp = self.test(dir=n, min=p, atol=atol)
        tn = self.test(dir=n, max=p, atol=atol)
        tc = ~(tp+tn)
        return tp, tc, tn


    def testBbox(self, bb, dirs=(0, 1, 2), nodes='any', atol=0.):
        """Test which part of a Formex or Mesh is inside a given bbox.

        The Geometry object needs to have a :meth:`test` method,
        This is the case for the :class:`~formex.Formex` and
        :class:`~mesh.Mesh` classes.
        The test can be applied in 1, 2 or 3 viewing directions.

        Parameters
        ----------
        bb: Coords (2,3) or alike
            The bounding box to test for.
        dirs: tuple of ints (0,1,2)
            The viewing directions in which to check the bbox bounds.
        nodes:
            Same as in :meth:`formex.Formex.test` or :meth:`mesh.Mesh.test`.

        Returns
        -------
        bool array
            The array flags the elements that are inside the given
            bounding box.
        """
        test = [self.test(nodes=nodes, dir=i, min=bb[0][i], max=bb[1][i],
                          atol=atol) for i in dirs]
        return np.stack(test).all(axis=0)


    ########### Coords transformations #################

    @_coords_transform
    def scale(self, *args, **kargs):
        pass

    def resized(self, size=1., tol=1.e-5):
        """Return a copy of the Geometry scaled to the given size.

        size can be a single value or a list of three values for the
        three coordinate directions. If it is a single value, all directions
        are scaled to the same size.
        Directions for which the geometry has a size smaller than tol times
        the maximum size are not rescaled.
        """
        s = self.sizes()
        size = Coords(np.resize(size, (3,)))
        ignore = s<tol*s.max()
        s[ignore] = size[ignore]
        return self.scale(size/s)


    @_coords_transform
    def adjust(self, *args, **kargs):
        pass

    @_coords_transform
    def translate(self, *args, **kargs):
        pass

    @_coords_transform
    def centered(self, *args, **kargs):
        pass

    @_coords_transform
    def align(self, *args, **kargs):
        pass

    @_coords_transform
    def rotate(self, *args, **kargs):
        pass

    @_coords_transform
    def shear(self, *args, **kargs):
        pass

    @_coords_transform
    def reflect(self, *args, **kargs):
        pass

    @_coords_transform
    def affine(self, *args, **kargs):
        pass

    @_coords_transform
    def toCS(self, *args, **kargs):
        pass

    @_coords_transform
    def fromCS(self, *args, **kargs):
        pass

    @_coords_transform
    def transformCS(self, *args, **kargs):
        pass

    @_coords_transform
    def position(self, *args, **kargs):
        pass

    @_coords_transform
    def cylindrical(self, *args, **kargs):
        pass

    @_coords_transform
    def hyperCylindrical(self, *args, **kargs):
        pass

    @_coords_transform
    def toCylindrical(self, *args, **kargs):
        pass

    @_coords_transform
    def spherical(self, *args, **kargs):
        pass

    @_coords_transform
    def superSpherical(self, *args, **kargs):
        pass

    @_coords_transform
    def toSpherical(self, *args, **kargs):
        pass

    @_coords_transform
    def circulize(self, *args, **kargs):
        pass

    @_coords_transform
    def bump(self, *args, **kargs):
        pass

    @_coords_transform
    def flare(self, *args, **kargs):
        pass

    @_coords_transform
    def map(self, *args, **kargs):
        pass

    @_coords_transform
    def map1(self, *args, **kargs):
        pass

    @_coords_transform
    def mapd(self, *args, **kargs):
        pass

    @_coords_transform
    def copyAxes(self, *args, **kargs):
        pass

    @_coords_transform
    def swapAxes(self, *args, **kargs):
        pass

    @_coords_transform
    def permuteAxes(self, *args, **kargs):
        pass

    @_coords_transform
    def rollAxes(self, *args, **kargs):
        pass

    @_coords_transform
    def projectOnPlane(self, *args, **kargs):
        pass

    @_coords_transform
    def projectOnSphere(self, *args, **kargs):
        pass

    @_coords_transform
    def projectOnCylinder(self, *args, **kargs):
        pass

    @_coords_transform
    def isopar(self, *args, **kargs):
        pass

    @_coords_transform
    def addNoise(self, *args, **kargs):
        pass

    rot = rotate
    trl = translate


    ##########################################################################
    #
    #  Operations on property numbers
    #
    ##########################################################################


    def setProp(self, prop=None):
        """Create or destroy the property array for the Geometry.

        A property array is a 1-dim integer array with length equal
        to the number of elements in the Geometry. Each element thus has its
        own property number. These numbers can be used for any purpose.
        In derived classes like :class:`~formex.Formex` and :class`~mesh.Mesh`
        they play an import role when creating new geometry: new elements
        inherit the property number of their parent element.
        Properties are also preserved on pure coordinate transformations.

        Because elements with different property numbers can be drawn in
        different colors, the property numbers are also often used to impose
        color.

        Parameters
        ----------
        prop: int, int :term:`array_like` or 'range'
            The property number(s) to assign to the elements. If a single int,
            all elements get the same property value.
            If the number of passed values is less than the number of elements,
            the list will be repeated. If more values are passed than the
            number of elements, the excess ones are ignored.

            A special value ``'range'`` may be given to set the property
            numbers equal to the element number. This is equivalent to
            passing ``arange(self.nelems())``.

            A value None (default) removes the properties from the Geometry.

        Returns
        -------
            The calling object ``self``, with the new properties inserted
            or with the properties deleted if argument is None.

        Note
        ----
        This is one of the few operations that change the object in-place.
        It still returns the object itself, so that this operation can be
        used in a chain with other operations.

        See Also
        --------
        toProp: Create a valid set of properties for the object
        whereProp: Find the elements having some property value

        """
        if prop is None:
            self.prop = None
        else:
            if isinstance(prop, str):
                if prop == 'range':
                    prop = np.arange(self.nelems())
            self.prop = self.toProp(prop)
        return self


    def toProp(self, prop):
        """Create a valid set of properties for the object.

        Parameters
        ----------
        prop: int or int :term:`array_like`
            The property values to turn into a valid set for the object.
            If a single int, all elements get the same property value.
            If the number of passed values is less than the number of elements,
            the list will be repeated. If more values are passed than the
            number of elements, the excess ones are ignored.

        Returns
        -------
        int array
            A 1-dim int array that is valid as a property array for
            the Geometry object. The length of the array will is
            ``self.nelems()`` and the dtype is :attr:`~arraytools.Int`.

        See Also
        --------
        setProp: Set the properties for the object
        whereProp: Find the elements having some property value

        Note
        ----
        When you set the properties (using :meth:`setProp`) you do not
        need to call this method to validate the properties. It is implicitely
        called from :meth:`setProp`.

        """
        prop = at.checkArray1D(prop, kind='i', allow='u')
        return np.resize(prop, (self.nelems(),)).astype(at.Int)


    def maxProp(self):
        """Return the highest property value used.

        Returns
        -------
        int
            The highest value used in the properties array, or -1
            if there are no properties.
        """
        if self.prop is None:
            return -1
        else:
            return self.prop.max()


    def propSet(self):
        """Return a list with unique property values in use.

        Returns
        -------
        int array
            The unique values in the properties array. If no
            properties are defined, an empty array is returned.


        """
        if self.prop is None:
            return np.array([], dtype=at.Int)
        else:
            return np.unique(self.prop)


    def propDict(self):
        """Return a dict with the elements grouped per prop value.

        Returns
        -------
        dict
            A dict where the keys are the unique prop values and the
            values are the lists of element numbers having that prop value.
            The dict is empty if the object doen't have prop numbers.

        """
        if self.prop is None:
            return {}
        else:
            return dict([(v, np.where(self.prop == v)[0])
                         for v in self.propSet()])


    def whereProp(self, prop):
        """Find the elements having some property value.

        Parameters
        ----------
        prop: int or int :term:`array_like`
            The property value(s) to be found.

        Returns
        -------
        int array
           A 1-dim int array with the indices of all the elements that
           have the property value ``prop``, or one of the values in ``prop``.

           If the object has no properties, an empty array is returned.

        See Also
        --------
        setProp: Set the properties for the object
        toProp: Create a valid set of properties for the object
        selectProp: Return a Geometry object with only the matching elements

        """
        if self.prop is not None:
            prop = np.unique(prop)
            if prop.size > 0:
                return np.concatenate([np.where(self.prop==v)[0] for v in prop])
        return np.array([], dtype=at.Int)


    ##########################################################################
    #
    #  Making copies and selections
    #
    ##########################################################################


    def copy(self):
        """Return a deep copy of the Geometry  object.

        Returns
        -------
        Geometry (or subclass) object
            An object of the same class as the caller, having all the
            same data (for :attr:`coords`, :attr:`prop`, :attr:`attrib`,
            :attr:`fields`, and any other attributes possibly set by the
            subclass), but not sharing any data with the original object.

        Note
        ----
        This is seldomly used, because it may cause wildly superfluous
        copying of data. Only used it if you absolutely require data
        that are independent of those of the caller.
        """
        from copy import deepcopy
        return deepcopy(self)


    @abstractmethod
    def _select(self, selected, **kargs):
        """Low level selection

        This is an abstract method and has to be reimplemented by the
        derived classes.
        """
        pass


    def select(self, sel, compact=False):
        """Select some element(s) from a Geometry.

        Parameters
        ----------
        sel: index-like
            The index of element(s) to be selected. This can be anything that
            can be used as an index in an array:

                - a single element number
                - a list, or array, of element numbers
                - a bool list, or array, of length self.nelems(),
                  where True values flag the elements to be selected
        compact: bool, optional
            This option is only useful for subclasses that have a
            ``compact`` method, such as :class:`mesh.Mesh` and its subclasses.
            If True, the returned object will be compacted, i.e.
            unused nodes are removed and the nodes are renumbered from
            zero. If False (default), the node set and numbers
            are returned unchanged.

        Returns
        -------
        Geometry (or subclass) object
            An object of the same class as the caller, but only containing
            the selected elements.

        See Also
        --------
        cselect: Return all but the selected elements.
        clip: Like select, but with compact=True as default.

        """
        utils.warn("warn_select_changed")
        return self._select(sel, compact=compact)


    def cselect(self, sel, compact=False):
        """Return the Geometry with the selected elements removed.

        Parameters
        ----------
        sel: index-like
            The index of element(s) to be selected. This can be anything that
            can be used as an index in an array:

                - a single element number
                - a list, or array, of element numbers
                - a bool list, or array, of length self.nelems(),
                  where True values flag the elements to be selected
        compact: bool, optional
            This option is only useful for subclasses that have a
            ``compact`` method, such as :class:`mesh.Mesh` and its subclasses.
            If True, the returned object will be compacted, i.e.
            unused nodes are removed and the nodes are renumbered from
            zero. If False (default), the node set and numbers
            are returned unchanged.

        Returns
        -------
        Geometry (or subclass) object
            An object of the same class as the caller, but containing
            all but the selected elements.

        See Also
        --------
        select: Return a Geometry with only the selected elements.
        cclip: Like cselect, but with compact=True as default.

        """
        utils.warn("warn_select_changed")
        return self._select(at.complement(sel, self.nelems()), compact=compact)


    def clip(self, sel):
        """Return a Geometry only containing the selected elements.

        This is equivalent to :meth:`select` with ``compact=True``.

        See Also
        --------
        select: Return a Geometry with only the selected elements.
        cclip: The complement of clip, returning all but the selected elements.

        """
        return self.select(sel, compact=True)


    def cclip(self, sel):
        """Return a Geometry with the selected elements removed.

        This is equivalent to :meth:`select` with ``compact=True``.

        See Also
        --------
        cselect: Return a Geometry with only the selected elements.
        clip: The complement of cclip, returning only the selected elements.
        """
        return self.cselect(sel, compact=True)


    def selectProp(self, prop, compact=False):
        """Select elements by their property value.

        Parameters
        ----------
        prop: int or int :term:`array_like`
            The property value(s) for which the elements should be selected.

        Returns
        -------
        Geometry (or subclass) object
            An object of the same class as the caller, but only containing
            the elements that have a property value equal to ``prop``, or
            one of the values in ``prop``.
            If the input object has no properties, a copy containing all
            elements is returned.

        See Also
        --------
        cselectProp: Return all but the elements with property ``prop``.
        whereProp: Get the numbers of the elements having a specified property.
        select: Select the elements with the specified indices.

        """
        if self.prop is None:
            return self.copy()
        else:
            return self._select(self.whereProp(prop), compact=compact)


    def cselectProp(self, prop, compact=False):
        """Return an object without the elements with property `val`.

        Parameters
        ----------
        prop: int or int :term:`array_like`
            The property value(s) of the elements that should be left out.

        Returns
        -------
        Geometry (or subclass) object
            An object of the same class as the caller, with all but
            the elements that have a property value equal to ``prop``, or
            one of the values in ``prop``.
            If the input object has no properties, a copy containing all
            elements is returned.

        See Also
        --------
        selectProp: Return only the elements with property ``prop``.
        whereProp: Get the numbers of the elements having a specified property.
        cselect: Remove elements by their index.

        """
        if self.prop is None:
            return self.copy()
        else:
            return self.cselect(self.whereProp(prop), compact=compact)


    def splitProp(self, prop=None, compact=True):
        """Partition a Geometry according to the values in prop.

        Parameters
        ----------
        prop: int :term:`array_like`, optional
            A 1-dim int array with length ``self.nelems()`` to be used in place
            of the objects own :attr:`prop` attribute. If None (default),
            the latter will be used.

        Returns
        -------
        :class:`~olist.List` of Geometry objects
            A list of objects of the same class as the caller.
            Each object in the list contains all the elements having the
            same value of `prop`. The number of objects in the list is
            equal to the number of unique values in `prop`. The list is
            sorted in ascending order of the `prop` value.

            If `prop` is None and the the object has no `prop` attribute,
            an empty list is returned.
        """
        if prop is None:
            prop = self.prop
        else:
            prop = self.toProp(prop)
        if prop is None:
            split = []
        else:
            split = [self.select(prop==p, compact=compact) for p in np.unique(prop)]
        return List(split)


    ##########################################################################
    #
    #  Operations on fields
    #
    ##########################################################################


    def addField(self, fldtype, data, fldname):
        """Add :class:`~field.Field` data to the :class:`Geometry`.

        Field data are scalar or vectorial data defined over the
        Geometry. This convenience function creates a :class:`~field.Field`
        object with the specified data and adds it to the Geometry object's
        :attr:`fields` dict.

        Parameters
        ----------
        fldtype: str
            The field type. See :class:`~field.Field` for details.
        data: :term:`array_like`
            The field data. See :class:`~field.Field` for details.
        fldname: str
            The field name. See :class:`~field.Field` for details. This name
            is also used as key to store the Field in the :attr:`fields`
            dict.

        Returns
        -------
        :class:`~field.Field`
            The constructed and stored Field object.

        Note
        ----
        Whenever a Geometry object is exported to a PGF file,
        all Fields stored inside the Geometry object are included
        in the PGF file.

        See Also
        --------
        fields: Return a dict with all Fields on the Geometry.
        getField: Retrieve a Field by its name.
        delField: Deleted a Field.
        convertField: Convert the Field to another Field type.
        fieldReport: Return a short overview of the stored Fields

        Examples
        --------
        >>> from pyformex.mesh import Mesh
        >>> M = Mesh(eltype='quad4').subdivide(2)
        >>> fld1 = M.addField('elemc', np.asarray([0,1,1,2]), 'elemnr')
        >>> print(fld1)
        Field 'elemnr', type 'elemc', shape (4,), nnodes=9, nelems=4, nplex=4
        [0 1 1 2]
        >>> fld2 = M.convertField('elemnr', 'node', 'onnodes')
        >>> fld3 = M.getField('onnodes')
        >>> print(fld3)
        Field 'onnodes', type 'node', shape (9, 1), nnodes=9, nelems=4, nplex=4
        [[0. ]
         [0.5]
         [1. ]
         [0.5]
         [1. ]
         [1.5]
         [1. ]
         [1.5]
         [2. ]]
        >>> print(M.fieldReport())
        Field 'elemnr', fldtype 'elemc', dtype int64, shape (4,)
        Field 'onnodes', fldtype 'node', dtype float64, shape (9, 1)
        """
        from pyformex.field import Field

        if not hasattr(self, 'fieldtypes') or fldtype not in self.fieldtypes:
            raise ValueError(f"Can not add field of type '{fldtype}' "
                             f"to a {self.__class__.__name__}")

        fld = Field(self, fldtype, data, fldname)
        return self._add_field(fld)


    def _add_field(self, field):
        """Low level function to add a Field"""
        if not hasattr(self, '_fields'):
            self._fields = {}
        self._fields[field.fldname] = field
        return field


    @property
    def fields(self):
        """Return the Fields dict of the Geometry.

        Returns
        -------
        dict
            A dict with the :class:`term:`Field` objects that were
            attached to the Geometry. The keys are the Field names.
            If the Geometry has no Fields, an empty dict is returned.
        """
        return getattr(self, '_fields', {})


    def getField(self, fldname):
        """Get the data field with the specified name.

        Parameters
        ----------
        fldname: str
            The name of the Field to retrieve.

        Returns
        -------
        :class:`~field.Field`
            The data field with the specified name, if it exists
            in the Geometry object's :attr:`fields`.
            Returns None if no such key exists.

        Examples
        --------
        See :meth:`addFields`.
        """
        return self.fields.get(fldname, None)


    def delField(self, fldname):
        """Delete the Field with the specified name.

        Parameters
        ----------
        fldname: str
            The name of the Field to delete from the Geometry object.
            A nonexisting name is silently ignored.
        """
        if fldname in self.fields:
            del self.fields[fldname]


    def convertField(self, fldname, totype, toname):
        """Convert the data field with the specified name to another type.

        Parameters
        ----------
        fldname: str
            The name of the data Field to convert to another type.
            A nonexisting name is silently ignored.
        totype: str
            The field type to convert to.
            See :class:`~field.Field` for details.
        toname: str
            The name of the new (converted) Field (and key to store it).
            If the same name is specified as the old Field, that one will
            be overwritten by the new. Otherwise, both will be kept in the
            Geometry object's :attr:`fields` dict.

        Returns
        -------
        :class:`~field.Field`
            The converted and stored data field.
            Returns None if the original data field does not exist.

        Examples
        --------
        See :meth:`addFields`.
        """
        if fldname in self.fields:
            fld = self.fields[fldname].convert(totype, toname)
            return self._add_field(fld)


    def fieldReport(self):
        """Return a short report of the stored fields

        Returns
        -------
        str
            A multiline string with the stored Fields' attributes:
            name, type, dtype and shape.

        """
        return '\n'.join([
            f"Field '{f.fldname}', fldtype '{f.fldtype}', "
            f"dtype {f.data.dtype}, shape {f.data.shape}"
            for f in self.fields.values()])


    ##########################################################################
    #
    #  Export/import to/from PGF/PZF files
    #
    ##########################################################################


    # TODO: this should allow pzf as well
    def write(self, filename, sep=' ', mode='w', **kargs):
        """Write a Geometry object to a PGF file"""
        from pyformex import filewrite
        filewrite.writePGF(filename, self, sep=sep, mode=mode, **kargs)


    @classmethod
    def read(clas, filename):
        """Read a single Geometry object from a PGF file"""
        from pyformex import fileread
        res = fileread.readPGF(filename, 1)
        return next(iter(res.values()))


    ###################
    ## PZF interface ##

    def pzf_dict(self):
        """Construct common part of all Geometry pzf dicts"""
        kargs = {}
        kargs['coords'] = self.coords
        if self.prop is not None:
            kargs['prop'] = self.prop
        if self.fields:
            for k in self.fields:
                fld = self.fields[k]
                kargs[f'field__{fld.fldtype}__{k}'] = fld.data
        if self.attrib.keys():
            kargs['attrib:j'] = self.attrib
        return kargs


# End
