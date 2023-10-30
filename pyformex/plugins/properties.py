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
"""General framework for attributing properties to geometrical elements.

Properties can really be just about any Python object.
Properties can be attributed to a set of geometrical elements.
"""

import copy

import numpy as np

import pyformex as pf
from pyformex import arraytools as at
from pyformex import Path
from pyformex.database import Record, Database
from pyformex.mydict import Dict, CDict


# global materials and section Databases
_matDB = None
_secDB = None

#################################################################
# Container classes used inside PropertyDB

class MaterialDB(Database):
    """A class for storing material properties.

    Parameters
    ----------
    data: dict | str, optional
        If a dict, it contains the Database. If a string, it is the filename
        containing the Database. If an empty string, the configured materials
        database file is loaded. If not provided, an empty Database is created.

    Examples
    --------
    >>> matDB = MaterialDB('')
    >>> print(matDB)
    {
        "steel": {
            "name": "steel",
            "young_modulus": 207000.0,
            "poisson_ratio": 0.3,
            "density": 7.85e-09
        },
    ...
    """
    def __init__(self, data=None, key='name'):
        """Initialize the database."""
        if data == '':
            data = pf.cfg['prop/matdb']
        super().__init__(data=data, key=key) #, record=Dict)


class SectionDB(Database):
    """A class for storing section properties

    Parameters
    ----------
    data: dict | str, optional
        If a dict, it contains the Database. If a string, it is the filename
        containing the Database. If an empty string, the configured materials
        database file is loaded. If not provided, an empty Database is created.

    Examples
    --------
    >>> secDB = SectionDB('')
    >>> print(secDB)
    {
        "kokerre": {
            "name": "kokerre",
            "cross_section": 500,
            "moment_inertia_11": 1256,
            "moment_inertia_12": 695,
            "moment_inertia_22": 365499,
            "torsional_rigidity": 635256
        },
    ...
    """
    def __init__(self, data=None, key='name'):
        """Initialize the database."""
        if data == '':
            data = pf.cfg['prop/secdb']
        super().__init__(data=data, key=key, record=CDict)


#################################################################
# Object classes used inside PropertyDB

class ElemSection(CDict):
    """Properties related to the section of an element.

    An element section property can hold the following sub-properties:

    section
      the geometric properties of the section. This can be a dict
      or a string. If it is a string, its value is looked up in the global
      section database. The section dict should at least have a key
      'sectiontype', defining the type of section.

      Currently the following sectiontype values are known by module
      :mod:`fe_abq` for export to Abaqus/Calculix:

        - 'solid'   : a solid 2D or 3D section,
        - 'circ'    : a plain circular section,
        - 'rect'    : a plain rectangular section,
        - 'pipe'    : a hollow circular section,
        - 'box'     : a hollow rectangular section,
        - 'I'       : an I-beam,
        - 'general' : anything else (automatically set if not specified).
        - 'rigid'   : a rigid body

      .. note: Currently only 'solid', 'general' and 'rigid' are allowed.

      The other possible (useful) keys in the section dict depend on the
      sectiontype. Again for :mod:`fe_abq`:

        - for sectiontype 'solid' : thickness
        - the sectiontype 'general': cross_section, moment_inertia_11,
          moment_inertia_12, moment_inertia_22, torsional_constant
        - for sectiontype 'circ': radius
        - for sectiontype 'rigid': refnode, density, thickness

    material
      the element material. This can be a dict or a string.
      Currently known keys to fe_abq.py are: young_modulus,
      shear_modulus, density, poisson_ratio . (see fmtMaterial in fe_abq)
      It should not be specified for rigid sections.

    orientation
      - a Dict, or
      - a list of 3 direction cosines of the first beam section axis.

    """
    def __init__(self, section=None, material=None, orientation=None, **kargs):
        """Create a new element section property. Empty by default."""
        global _matDB, _secDB
        if _matDB is None:
            _matDB = MaterialDB({})
        if _secDB is None:
            _secDB = SectionDB({})
        # Add default 'extra' and 'options' attributes to avoid
        # cascading into the material.
        self.extra = None
        self.options = None
        CDict.__init__(self, **kargs)
        if section is not None:
            self.addSection(section)
        if material is not None:
            self.addMaterial(material)
        if orientation is not None:
            self.orientation = orientation

    def addMaterial(self, material):
        """Create or replace the material properties of the element.

        If the argument is a dict, it will be added to the global MaterialDB.
        If the argument is a string, this string will be used as a key to
        search in the global MaterialDB.
        """
        if isinstance(material, str):
            if material in _matDB:
                self.material = _matDB[material]
            else:
                pf.warning("Material '%s'  is not in the database" % material)
        elif isinstance(material, dict):
            _matDB.add([material])
            self.material = _matDB[material['name']]
        else:
            raise ValueError("Expected a string or a dict")

    def addSection(self, section):
        """Create or replace the section properties of the element.

        If 'section' is a dict, it will be added to the global SectionDB.
        If 'section' is a string, this string will be used as a key to
        search in the global SectionDB.
        """
        if isinstance(section, str):
            if section in _secDB:
                self.section = _secDB[section]
            else:
                pf.warning("Section '%s' is not in the database" % section)
        elif isinstance(section, dict):
            # TODO: WE COULD ADD AUTOMATIC CALCULATION OF SECTION PROPERTIES
            # self.computeSection(section)
            # print(section)
            _secDB[section['name']] = CDict(section)
            self.section = _secDB[section['name']]
        else:
            raise ValueError("Expected a string or a dict")

    def computeSection(self, section):
        """Compute the section characteristics of specific sections."""
        if 'sectiontype' not in section:
            return
        if section['sectiontype'] == 'circ':
            r = section['radius']
            A = np.pi * r**2
            I = np.pi * r**4 / 4      # noqa: E741
            section.update({'cross_section': A,
                            'moment_inertia_11': I,
                            'moment_inertia_22': I,
                            'moment_inertia_12': 0.0,
                            'torsional_constant': 2*I,
                            })
        else:
            raise ValueError("Invalid sectiontype")


class ElemLoad(CDict):
    """Distributed loading on an element."""

    def __init__(self, label=None, value=None, dir=None):
        """Create a new element load. Empty by default.

        An element load can hold the following sub-properties:

        - label: the distributed load type label
        - value: the magnitude of the distibuted load
        - dir: vector specifying the direction of the load
        """
        if label == 'GRAV':
            if dir is None:
                dir = [0, 0, -1]
            if value is None:
                value = 9.81
        Dict.__init__(self, {'label': label, 'value': value, 'dir': dir})


class EdgeLoad(CDict):
    """Distributed loading on an element edge."""

    def __init__(self, edge=-1, label=None, value=None):
        """Create a new element edge load. Empty by default.

        An element edgeload can hold the following sub-properties:
        - edge: the element edge number
        - label: the distributed load type label ('x','y','z').
        - value: the magnitude of the distibuted load.
        """
        Dict.__init__(self, {'edge': edge, 'label': label, 'value': value})


class CoordSystem():
    """A class for storing coordinate systems."""

    valid_csys = 'RSC'

    def __init__(self, csys, cdata):
        """Create a new coordinate system.

        csys is one of 'Rectangular', 'Spherical', 'Cylindrical'. Case is
          ignored and the first letter suffices.
        cdata is a list of 6 coordinates specifying the two points that
          determine the coordinate transformation
        """
        try:
            csys = csys[0].upper()
            if csys not in CoordSystem.valid_csys:
                raise ValueError
            cdata = np.asarray(cdata).flatten()
            if len(cdata) != 6:
                raise ValueError
        except ValueError:
            raise ValueError("Invalid initialization data for CoordSystem")
        self.sys = csys
        self.data = cdata


class Amplitude():
    """A class for storing an amplitude.

    The amplitude is a list of tuples (time,value).

    `atime` (amplitude time) can be either STEP TIME (default in Abaqus)
    or TOTAL TIME

    `smoothing` (optional) is a float (from 0. to 0.5, suggested value 0.05)
    representing the fraction of the time interval before and after each time
    point during which the piecewise linear time variation will be replaced by
    a smooth quadratic time variation (avoiding infinite accelerations).
    Smoothing should be used in combination with TABULAR (set 0.05 as default
    value?)
    """

    def __init__(self, data, definition='TABULAR', atime='STEP TIME',
                 smoothing=None):
        """Create a new amplitude."""
        if definition in ['TABULAR', 'SMOOTH STEP']:
            if atime in ['STEP TIME', 'TOTAL TIME']:
                self.data = at.checkArray(data, (-1, 2), 'f', 'i')
                self.type = definition
                self.atime = atime
                if definition == 'TABULAR':
                    if smoothing is not None:
                        self.type += f", SMOOTHING={smoothing}"
        else:
            raise ValueError("Expected definition = 'TABULAR' or 'SMOOTH STEP'")


###################################################
# Utility routines


def checkIdValue(values):
    """Check that a variable is a list of (id,value) tuples

    `id` should be convertible to an int, value to a float.
    If ok, return the values as a list of (int,float) tuples.
    """
    try:
        lv = [len(v) for v in values]
        if min(lv) == 2 and max(lv) == 2:
            return [(int(i), float(v)) for i, v in values]
    except Exception:
        raise ValueError("Expected a list of (int,float) tuples")


def checkArrayOrIdValue(values):
    """Check that a variable is a list of values or (id,value) tuples

    This convenience function checks that the argument is either:

    - a list of 6 float values (or convertible to it), or
    - a list of (id,value) tuples where id is convertible to an int,
      value to a float.

    If ok, return the values as a list of (int,float) tuples.

    Examples:
      >>> checkArrayOrIdValue([0,3,4,0,0,0])
      [(1, 3.0), (2, 4.0)]
      >>> checkArrayOrIdValue([(1,3.0),(2,4.0)])
      [(1, 3.0), (2, 4.0)]
      >>> checkArrayOrIdValue([(0,1.0),(2,4.0),(3,5.0),(4,4),(5,3.0),(1,4.0)])
      [(0, 1.0), (2, 4.0), (3, 5.0), (4, 4.0), (5, 3.0), (1, 4.0)]

    """
    try:
        v = at.checkArray(values, (6,), 'f', 'i', ndim=1)
        w = np.where(v != 0.0)[0]
        values = [(i, v[i]) for i in w]
    except Exception:
        values = checkIdValue(values)
    return values


def checkArrayOrIdValueOrEmpty(values):
    """Check that a variable is a list of values or (id,value) tuples or empty.

    This convenience function checks that the argument is either:

    - a list of 6 float values (or convertible to it), or
    - a list of (id,value) tuples where id is convertible to an int,
      value to a float.
    - something representing an empty list

    If ok, return the values as a list of (int,float) tuples.

    Examples:
      >>> checkArrayOrIdValueOrEmpty([0,3,4,0,0,0])
      [(1, 3.0), (2, 4.0)]
      >>> checkArrayOrIdValueOrEmpty([(1,3.0),(2,4.0)])
      [(1, 3.0), (2, 4.0)]
      >>> checkArrayOrIdValueOrEmpty([])
      []

    """
    try:
        if len(values) == 0:
            return []
    except Exception:
        pass
    return checkArrayOrIdValue(values)


def checkString(a, valid):
    """Check that a string a has one of the valid values.

    This is case insensitive, and returns the upper case string if valid.
    Else, an error is raised.
    """
    try:
        a = a.upper()
        if a in valid:
            return a
    except Exception:
        print("Expected one of %s, got: %s" % (valid, a))
    raise ValueError


####################################################
# Create automatic names for node and element sets


def autoName(base, *args):
    return (base + '_%s' * len(args)) % args


# The following are not used by the PropertyDB class,
# but may be convenient for the user in applications

Nset_prefix = 'Nset'
Eset_prefix = 'Eset'


def Nset(*args):
    return autoName(Nset_prefix, *args)


def Eset(*args):
    return autoName(Eset_prefix, *args)


def FindListItem(l, p):
    """Find the item p in the list l.

    If p is an item in the list (not a copy of it!), this returns
    its position. Else, -1 is returned.

    Matches are found with a 'is' function, not an '=='.
    Only the first match will be reported.
    """
    for i, j in enumerate(l):
        if j is p:
            return i
    return -1


def RemoveListItem(l, p):
    """Remove the item p from the list l.

    If p is an item in the list (not a copy of it!), it is removed from
    the list.
    Matches are found with a 'is' comparison. This is different from the
    normal Python list.remove() method, which uses '=='.
    As a result, we can find complex objects which do not allow '==',
    such as ndarrays.
    """
    i = FindListItem(l, p)
    if i >= 0:
        del l[i]


#############################################################
# Properties Database

class PropertyDB():
    """A database class for all properties.

    This class collects all properties that can be set on a
    geometrical model.

    This should allow for storing:

    - materials
    - sections
    - any properties
    - node properties
    - elem properties
    - model properties (current unused: use unnamed properties)

    Materials and sections use their own database for storing. They can be
    specified on creating the property database.

    Parameters
    ----------
    matdb: :class:`MaterialDB`
        The material database to be used. It can be a MaterialDB object,
        or data to initialize it: a dict with the database contents, or a
        filename where the MaterialDB can be read. The default empty string
        will read the configured material database file. Specifying None
        creates an empty MaterialDB.
    secdb: :class:`SectionDB`
        The section database to be used. It can be a SectionDB object,
        or data to initialize it: a dict with the database contents, or a
        filename where the SectionDB can be read. The default empty string
        will read the configured section database file. Specifying None
        creates an empty SectionMaterialDB.

    """

    bound_strings = ['XSYMM', 'YSYMM', 'ZSYMM', 'ENCASTRE', 'PINNED']

    def __init__(self, matdb='', secdb=''):
        """Create a new properties database."""
        self.prop = []
        self.nprop = []
        self.eprop = []
        self.matDB = matdb
        self.secDB = secdb

    @property
    def matDB(self):
        return self._matDB

    @matDB.setter
    def matDB(self, matdb):
        """Set the global materials database.

        Parameters
        ----------
        matdb: :class:`MaterialDB`
            A MateriaDB object or data to initialize it.
            If matdb is a :class:`MaterialDB` MaterialDB, it will be used
            directly in the properties. Else, a new MaterialDB will be
            created, initialized from matdb. An empty string loads the
            configured materials database, while {} creates an empty MaterialDB.
        """
        global _matDB
        if isinstance(matdb, MaterialDB):
            self._matDB = matdb
        else:
            self._matDB = MaterialDB(matdb)
        _matDB = self._matDB

    @property
    def secDB(self):
        return self._secDB

    @secDB.setter
    def secDB(self, secdb):
        """Set the global sections database.

        If sec is a SectionDB, it will directly be used in the properties.
        Else, a new SectionDB will be created, initialized from sec.
        The default None will load the configure sections database,
        while {} will create an empty SectionDB.
        """
        global _secDB
        if isinstance(secdb, SectionDB):
            self._secDB = secdb
        else:
            self._secDB = SectionDB(secdb)
        _secDB = self._secDB


    @classmethod
    def autoName(clas, kind, *args):
        return autoName((kind+'set').capitalize(), *args)

    def print(self):
        """Print the property database"""
        print("General properties")
        for p in self.getProp(''):
            print(p)
        print("Node properties")
        for p in self.getProp('n'):
            print(p)
        print("Element properties")
        for p in self.getProp('e'):
            print(p)


    def Prop(self, kind='', tag=None, set=None, name=None, **kargs):
        """Create a new property, empty by default.

        A property can hold almost anything, just like any Dict type.
        It has however four predefined keys that should not be used for
        anything else than explained hereafter:

        - nr: a unique id, that never should be set/changed by the user.
        - tag: an identification tag used to group properties
        - name: the name to be used for this set. Default is to use an
          automatically generated name.
        - set: identifies the geometrical elements for which the defined
          properties will hold. This can be either:

          - a single number,
          - a list of numbers,
          - the name of an already defined set,
          - a list of such names.

        Besides these, any other fields may be defined and will be added
        without checking.
        """
        d = CDict()
        # update with kargs first, to make sure tag,set and nr are sane
        d.update(dict(**kargs))

        prop = getattr(self, kind+'prop')
        d.nr = len(prop)
        if tag is not None:
            d.tag = str(tag)
        if name is None and 'setname' in kargs:
            # allow for backwards compatibility
            pf.utils.warn("warn_properties_setname")
            name = kargs['setname']
        if name is None and isinstance(set, str):
            ### convenience to allow set='name' as alias for name='name'
            ### to reuse already defined set
            name, set = set, name
        if name is None:
            name = self.autoName(kind, d.nr)
        elif not isinstance(name, str):
            raise ValueError("Property name should be a string")
        d.name = name
        if set is not None:
            if isinstance(set, int) or isinstance(set, str):
                set = [set]
            d.set = np.unique(set)

        prop.append(d)
        return d


    def getProp(self, kind='', rec=None, tag=None, attr=[], noattr=[],
                delete=False):
        # TODO: This should maybe change to operate on the property keys
        # and finally return the selected keys or properties?
        """Return all properties of type kind matching tag and having attr.

        kind is either '', 'n', 'e' or 'm'
        If rec is given, it is a list of record numbers or a single number.
        If a tag or a list of tags is given, only the properties having a
        matching tag attribute are returned.

        attr and noattr are lists of attributes. Only the properties having
        all the attributes in attr and none of the properties in noattr are
        returned.
        Attributes whose value is None are treated as non-existing.

        If delete==True, the returned properties are removed from the database.
        """
        prop = getattr(self, kind+'prop')
        if rec is not None:
            if not isinstance(rec, list):
                rec = [rec]
            rec = [i for i in rec if i < len(prop)]
            prop = [prop[i] for i in rec]
        if tag is not None:
            if not isinstance(tag, list):
                tag = [tag]
            tag = [str(t) for t in tag]  # tags are always converted to strings
            prop = [p for p in prop if 'tag' in p and p['tag'] in tag]
        for a in attr:
            prop = [p for p in prop if a in p and p[a] is not None]
        for a in noattr:
            prop = [p for p in prop if a not in p or p[a] is None]
        if delete:
            self._delete(prop, kind=kind)
        return prop


    def _delete(self, plist, kind=''):
        """Delete the specified properties from the database.

        plist is a list of property records (not copies of them!),
        such as returned by getProp.
        The kind parameter can specify a specific property database.
        """
        prop = getattr(self, kind+'prop')
        if not isinstance(plist, list):
            plist = [plist]
        for p in plist:
            RemoveListItem(prop, p)
        self._sanitize(kind)


    def _sanitize(self, kind):
        """Sanitize the record numbers after deletion"""
        prop = getattr(self, kind+'prop')
        for i, p in enumerate(prop):
            p.nr = i


    def delProp(self, kind='', rec=None, tag=None, attr=[]):
        """Delete properties.

        This is equivalent to getProp() but the returned properties
        are removed from the database.
        """
        return self.getProp(kind=kind, rec=rec, tag=tag, attr=attr, delete=True)


    def nodeProp(self, prop=None, set=None, name=None, tag=None, cload=None,
                 bound=None, displ=None, veloc=None, accel=None, csys=None,
                 ampl=None, **kargs):
        """Create a new node property, empty by default.

        A node property can contain any combination of the following fields:

        - tag: an identification tag used to group properties (this is e.g.
          used to flag Step, increment, load case, ...)
        - set: a single number or a list of numbers identifying the node(s)
          for which this property will be set, or a set name
          If None, the property will hold for all nodes.
        - cload: a concentrated load: a list of 6 float values
          [FX,FY,FZ,MX,MY,MZ] or a list of (dofid,value) tuples.
        - displ,veloc,accel: prescribed displacement, velocity or
          acceleration: a list of 6 float values [UX,UY,UZ,RX,RY,RZ] or
          a list of tuples (dofid,value)
        - bound: a boundary condition: a string, a list of 6 codes (0/1), or
          a list of tuples (dofid, value)
        - csys: a CoordSystem
        - ampl: the name of an Amplitude
        """
        try:
            d = kargs
            if cload is not None:
                d['cload'] = checkArrayOrIdValue(cload)
            if displ is not None:
                d['displ'] = checkArrayOrIdValueOrEmpty(displ)
            if veloc is not None:
                d['veloc'] = checkArrayOrIdValueOrEmpty(veloc)
            if accel is not None:
                d['accel'] = checkArrayOrIdValueOrEmpty(accel)
            if bound is not None:
                if isinstance(bound, str):
                    d['bound'] = checkString(bound, self.bound_strings)
                elif isinstance(bound, list):
                    if not isinstance(bound[0], tuple):
                        d['bound'] = at.checkArray1D(bound, kind='i', size=6)
                    else:
                        d['bound'] = bound  # unchecked
            if csys is not None:
                if isinstance(csys, CoordSystem):
                    d['csys'] = csys
                else:
                    raise ValueError("Invalid Coordinate System")

            # Currently unchecked!
            if ampl is not None:
                d['ampl'] = ampl
            return self.Prop(kind='n', prop=prop, tag=tag, set=set, name=name,
                             **d)
        except Exception:
            print(f"tag={tag}, set={set}, name={name}, cload={cload}, "
                  f"bound={bound}, displ={displ}, csys={csys}")
            raise ValueError("Invalid Node Property")


    def elemProp(self, prop=None, grp=None, set=None, name=None, tag=None,
                 section=None, eltype=None, dload=None, eload=None,
                 ampl=None, **kargs):
        """Create a new element property, empty by default.

        An elem property can contain any combination of the following fields:

        - tag: an identification tag used to group properties (this is e.g.
          used to flag Step, increment, load case, ...)
        - set: a single number or a list of numbers identifying the element(s)
          for which this property will be set, or a set name
          If None, the property will hold for all elements.
        - grp: an elements group number (default None). If specified, the
          element numbers given in set are local to the specified group.
          If not, elements are global and should match the global numbering
          according to the order in which element groups will be specified
          in the Model.
        - eltype: the element type (currently in Abaqus terms).
        - section: an ElemSection specifying the element section properties.
        - dload: an ElemLoad specifying a distributed load on the element.
        - ampl: the name of an Amplitude
        """
        try:
            d = {}
            if eltype is not None:
                d['eltype'] = eltype.upper()
            if section is not None:
                d['section'] = section
            if dload is not None:
                d['dload'] = dload
            if eload is not None:
                d['eload'] = eload
            # Currently unchecked!
            if ampl is not None:
                d['ampl'] = ampl
            d.update(kargs)
            return self.Prop(kind='e', prop=prop, tag=tag, set=set, name=name,
                             **d)
        except Exception:
            raise ValueError(
                f"Invalid Elem Property\n  tag={tag}, set={set}, name={name}, "
                f"eltype={eltype}, section={section}, dload={dload}, "
                f"eload={eload}")


    def __deepcopy__(self, memo):
        """Create a deep copy of ourself."""
        cls = self.__class__
        newdict = cls.__new__(cls)
        for k in self:
            newdict[k] = copy.deepcopy(self[k], memo)
        return newdict


##################################### Test ###########################

if __name__ == '__script__' or __name__ == '__draw__':

    P = PropertyDB()

    Stick = P.Prop(color='green', name='Stick', weight=25,
                   comment='This could be anything: a gum, a frog, a usb-stick,...')
    print(Stick)

    author = P.Prop(tag='author', alias='Alfred E Neuman',
                    address=Dict({'street': 'Krijgslaan', 'city': 'Gent',
                                   'country': 'Belgium'}))

    print(P.getProp(tag='author')[0])

    Stick.weight=30
    Stick.length=10
    print(Stick)

    print(author.street)
    author.street='Voskenslaan'
    print(author.street)
    print(author.address.street)
    author.address.street = 'Wiemersdreef'
    print(author.address.street)

    author = P.Prop(tag='author', name='John Doe',
                    address={'city': 'London', 'street': 'Downing Street 10',
                             'country': 'United Kingdom'})
    print(author)

    for p in P.getProp(rec=[0, 2]):
        print(p.name)

    for p in P.getProp(tag=['author']):
        print(p.name)

    for p in P.getProp(attr=['name']):
        print(p.nr)


    P.Prop(set=[0, 1, 3], name='green_elements', color='green')
    P.Prop(name='green_elements', transparent=True)
    a = P.Prop(set=[0, 2, 4, 6], thickness=3.2)
    P.Prop(name=a.name, material='steel')

    for p in P.getProp(attr=['name']):
        print(p)

    P.Prop(set='green_elements', transparent=False)
    for p in P.getProp(attr=['name']):
        if p.name == 'green_elements':
            print(p.nr, p.transparent)

    print("before")
    for p in P.getProp():
        print(p)

    P.getProp(attr=['transparent'], delete=True)
    P.delProp(attr=['color'])
    pl = P.getProp(rec=[5, 6])
    print(pl)
    P._delete(pl)

    print("after")
    for p in P.getProp():
        print(p)

    times = np.arange(10)
    values = np.square(times)
    amp = Amplitude(np.column_stack([times, values]))
    P.Prop(amplitude=amp, name='amp1')

    P1 = [1.0, 1.0, 1.0, 0.0, 0.0, 0.0]
    P2 = [0.0] * 3 + [1.0] * 3
    B1 = [1] + [0] * 5
    CYL = CoordSystem('cylindrical', [0, 0, 0, 0, 0, 1])
    # node property on single node
    P.nodeProp(1, cload=[5, 0, -75, 0, 0, 0])
    # node property on nodes 2 and 3
    P.nodeProp(set=[2, 3], bound='pinned')
    # node property on ALL nodes
    P.nodeProp(cload=P1, bound=B1, csys=CYL, ampl='amp1')
    # node property whose set will be reused
    nset1 = P.nodeProp(tag='step1', set=[2, 3, 4], cload=P1).nr
    # node properties with an already named set
    P.nodeProp(tag='step2', set=Nset(nset1), cload=P2)

    print('nodeproperties')
    print(P.nprop)

    print('all nodeproperties')
    print(P.getProp('n'))

    print("properties 0 and 2")
    for p in P.getProp('n', rec=[0, 2]):
        print(p)

    print("tags 1 and step1")
    for p in P.getProp('n', tag=[1, 'step1']):
        print(p)

    print("cload attributes")
    for p in P.getProp('n', attr=['cload']):
        print(p)

    # Load the configured databases
    P.matDB = ''
    P.secDB = ''
    print(P.matDB)
    print(P.secDB)

    vert = ElemSection('IPEA100', 'steel')
    hor = ElemSection({'name': 'IPEM800',
                       'A': 951247,
                       'I': CDict({'Ix': 1542, 'Iy': 6251, 'Ixy': 352})},
                      {'name': 'S400', 'E': 210, 'fy': 400})
    circ = ElemSection({'name': 'circle', 'radius': 10, 'sectiontype': 'circ'},
                       'steel')

    print("Materials")
    Mat = P.matDB
    for m in Mat:
        print(Mat[m])

    print("Sections")
    Sec = P.secDB
    for s in Sec:
        print(Sec[s])

    q1 = ElemLoad('PZ', 2.5)
    q2 = ElemLoad('PY', 3.14)

    top = P.elemProp(set=[0, 1, 2], eltype='B22', section=hor, dload=q1)
    column = P.elemProp(eltype='B22', section=vert)
    diagonal = P.elemProp(eltype='B22', section=hor)
    bottom = P.elemProp(section=hor, dload=q2, ampl='amp1')


    print('elemproperties')
    for p in P.eprop:
        print(p)

    print("section properties")
    for p in P.getProp('e', attr=['section']):
        print(p.nr)

    P.Prop(set='cylinder', name='cylsurf', surftype='element', label='SNEG')

    print(P.getProp(attr=['surftype']))

# End
