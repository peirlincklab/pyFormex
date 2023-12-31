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
"""Read/write geometry in DXF format.

This module allows to import and export some simple geometrical items
in DXF format.
"""


from pyformex.core import *
from pyformex import curve
from pyformex import utils


# Avoid compilation problems
def execSource(s, g):
    exec(s, g)


def importDXF(filename):
    """Import (parts of) a DXF file into pyFormex.

    This function scans a DXF file for recognized entities and imports
    those entities as pyFormex objects. It is only a very partial importer,
    but has proven to be already very valuable for many users.

    `filename`: name of a DXF file.
    The return value is a list of pyFormex objects.

    Importing a DXF file is done in two steps:

    - First the DXF file is scanned and the recognized entities are
      formatted into a text with standard function calling syntax.
      See :func:`readDXF`.
    - Then the created text is executed as a Python script, producing
      equivalent pyFormex objects.
      See :func:`convertDXF`.

    """
    text = readDXF(filename)
    if text:
        return convertDXF(text)
    else:
        return []


def readDXF(filename):
    """Read a DXF file and extract the recognized entities.

    `filename`: name of a .DXF file.

    Returns a multiline string with one line for each recognized entity,
    in a format that can directly be used by :func:`convertDXF`.

    This function requires the external program `dxfparser` which comes
    with the pyFormex distribution. It currently recognizes entities of
    type 'Arc', 'Line', 'Polyline', 'Vertex'.
    """
    print(filename)
    if utils.External.has('dxfparser'):
        cmd = 'pyformex-dxfparser %s 2>/dev/null' % filename
        print(cmd)
        P = utils.command(cmd, shell=True)
        if P.returncode==0:
            return P.stdout
        else:
            return ''
    else:
        utils.warn('warn_dxf_noparser')
        return ''


Entities = []
Vertices = []

def convertDXF(text):
    """Convert a textual representation of a DXF format to pyFormex objects.

    `text` : a multiline text representation of the contents of a DXF file.
      This text representation can e.g. be obtained by the function
      :func:`readDXF`. It contains lines defining DXF entities. A small
      example::

        Arc(0.0,0.0,0.0,1.0,-90.,90.)
        Arc(0.0,0.0,0.0,3.0,-90.,90.)
        Line(0.0,-1.0,0.0,0.0,1.0,0.0)
        Polyline(0)
        Vertex(0.0,3.0,0.0)
        Vertex(-2.0,3.0,0.0)
        Vertex(-2.0,-7.0,0.0)
        Vertex(0.0,-7.0,0.0)
        Vertex(0.0,-3.0,0.0)

      Each line of the text defines a single entity or starts a multiple
      component entity. The text should be well aligned to constitute a
      proper Python script. Currently, the only defined entities are
      'Arc', 'Line', 'Polyline', 'Vertex'.

    Returns a list of pyFormex objects corresponding to the text. The
    returned objects are of the following type:

        =============         ================================
        function name         object
        =============         ================================
        Arc                   :class:`curve.Arc`
        Line                  :class:`plugins.dxf.Line`
        Polyline              :class:`curve.PolyLine`
        =============         ================================

    No object is returned for the `Vertex` function: they define the
    vertices of a PolyLine.

    """
    import types
    global Entities, Vertices

    Entities = []
    Vertices = []

    # Simple type (Line, Arc) create the object and append it to the
    # Entities list
    # Compound types (like Polyline) append the corresponding
    # EndEntity function to the Entities list


    def EndEntity():
        global Entities, Vertices
        if Entities:
            f = Entities[-1]
            if isinstance(f, types.FunctionType):
                f()

    def Arc(x0, y0, z0, r, a0, a1):
        global Entities, Vertices
        count = len(Entities)
        part = curve.Arc(center=[x0, y0, z0], radius=r, angles=[a0, a1]).setProp(count)
        part.dxftype = 'Arc'
        Entities.append(part)

    def Circle(x0, y0, z0, r):
        Arc(x0, y0, z0, r, 0., 360.)

    def Line(x0, y0, z0, x1, y1, z1):
        global Entities, Vertices
        count = len(Entities)
        part = curve.PolyLine([[x0, y0, z0], [x1, y1, z1]]).setProp(count)
        part.dxftype = 'Line'
        Entities.append(part)

    def Polyline(n):
        global Entities, Vertices
        EndEntity()
        Entities.append(EndPolyline)
        Vertices = []

    def EndPolyline():
        global Entities, Vertices
        count = len(Entities) - 1
        part = curve.PolyLine(Vertices).setProp(count)
        part.dxftype = 'Polyline'
        Entities[-1] = part
        Vertices = []

    def Vertex(x, y, z):
        global Entities, Vertices
        Vertices.append([x, y, z])


    l = {'Line': Line, 'Arc': Arc, 'Circle': Circle, 'Polyline': Polyline, 'EndPolyline': EndPolyline, 'Vertex': Vertex}
    execSource(text, l)
    EndEntity()
    return Entities


def collectByType(entities):
    """Collect the dxf entities by type."""
    coll = {}
    types = {type(i) for i in entities}
    print("DXF collection:")
    for t in types:
        n = t.__name__
        cn = [i for i in entities if isinstance(i, t)]
        print("  items of type %s: %s" % (n, len(cn)))
        coll[n] = cn
    return coll


def toLines(coll, chordal=0.01, arcdiv=None):
    """Convert the dxf entities in a dxf collection to a plex-2 Formex

    This converts Lines, Arcs and PolyLines to plex-2 elements and collects
    them in a single Formex.
    The chordal and arcdiv parameters are passed to :meth:`Arc.approx` to set
    the accuracy for the approximation of the Arc by line segments.
    """
    Lines = []
    for k, v in coll.items():
        if k in ['Line', 'PolyLine']:
            Lines.extend([a.toFormex() for a in v])
        elif k == 'Arc':
            Lines.extend([a.toFormex(chordal=chordal, ndiv=arcdiv) for a in v])
    return Formex.concatenate(Lines)


class DxfExporter():
    """Export geometry in DXF format.

    While we certainly do not want to promote proprietary software,
    some of our users occasionally needed to export some model in
    DXF format.
    This class provides a minimum of functionality.
    """

    def __init__(self, filename, terminator='\n'):
        """Open a file for export in DXF format.

        No check is done that the file has a '.dxf' extension.
        The file will by default be written in UNIX line termination mode.
        An existing file will be overwritten without warning!
        """
        self.filename = filename
        self.fil = open(self.filename, 'w')
        self.term = terminator


    def write(self, s):
        """Write a string to the dxf file.

        The string does not include the line terminator.
        """
        self.fil.write(s+self.term)


    def out(self, code, data):
        """Output a string data item to the dxf file.

        code is the group code,
        data holds the data
        """
        self.write('%3s' % code)
        self.write('%s' % data)


    def close(self):
        """Finalize and close the DXF file"""
        self.out(0, 'EOF')
        self.fil.close()


    def section(self, name):
        """Start a new section"""
        self.out(0, 'SECTION')
        self.out(2, name)


    def endSection(self):
        """End the current section"""
        self.out(0, 'ENDSEC')


    def entities(self):
        """Start the ENTITIES section"""
        self.section('ENTITIES')


    def layer(self, layer):
        """Export the layer"""
        self.out(8, layer)


    def vertex(self, x, layer=0):
        """Export a vertex.

        x is a (3,) shaped array
        """
        self.out(0, 'VERTEX')
        self.out(8, layer)
        for i in range(3):
            self.out(10*(i+1), x[i])


    def line(self, x, layer=0):
        """Export a line.

        x is a (2,3) shaped array
        """
        self.out(0, 'LINE')
        self.out(8, layer)
        for j in range(2):
            for i in range(3):
                self.out(10*(i+1)+j, x[j][i])


    def polyline(self, x, layer=0):
        """Export a polyline.

        x is a (nvertices,3) shaped array
        """
        self.out(0, 'POLYLINE')
        self.out(8, layer)
        for xi in x:
            self.vertex(xi, layer)
        self.out(0, 'SEQEND')


    def arc(self, C, R, a, layer=0):
        """Export an arc.

        """
        self.out(0, 'ARC')
        self.out(8, layer)
        for k, v in [
            (10, C[0]),
            (20, C[1]),
            (30, C[2]),
            (40, R),
            (50, a[0]),
            (51, a[1]),
            ]:
            self.out(k, v)


def exportDXF(filename, F):
    """Export a Formex to a DXF file

    Currently, only plex-2 Formices can be exported to DXF.
    """
    if F.nplex() != 2:
        raise ValueError("Can only export plex-2 Formices to DXF")
    dxf = DxfExporter(filename)
    dxf.entities()
    for i in F:
        dxf.line(i)
    dxf.endSection()
    dxf.close()


def exportDxf(filename, coll):
    """Export a collection of dxf parts a DXF file

    coll is a list of dxf objects

    Currently, only dxf objects of type 'Line' and 'Arc' can be exported.
    """
    dxf = DxfExporter(filename)
    dxf.entities()
    for ent in coll:
        print(type(ent), ent)
        if isinstance(ent, curve.Line):
            dxf.line(ent.coords)
        elif isinstance(ent, curve.Arc):
            dxf.arc(ent.getCenter(), ent.radius, ent.angles)
        elif isinstance(ent, curve.PolyLine):
            dxf.polyline(ent.coords)
        else:
            utils.warn('warn_dxf_export', data=type(ent))

    dxf.endSection()
    dxf.close()



def dxftext(obj):
    """
    Examples
    --------
    >>> L = curve.Line([[0.,0.,0.], [0.,1.,0.]])
    >>> print(dxftext(L))
    Line(0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
    >>> A = curve.Arc(center=[0.,0.,0.], radius=1., angles=(-90., 90.))
    >>> print(dxftext(A))
    Arc(0.0, 0.0, 0.0, 1.0, 270.0, 450.0)
    """
    if isinstance(obj, curve.Line):
        d = tuple(obj.coords.ravel())
        s = f"Line{d}"
    elif isinstance(obj, curve.Arc):
        d = (*obj.center, obj.radius, *obj.angles)
        s = f"Arc{d}"
    return s

def exportDxfText(filename, parts):
    """Export a set of dxf entities to a .dxftext file."""
    fil = open(filename, 'w')
    for p in parts:
        fil.write(dxftext(p)+'\n')
    fil.close()


# An example

if __name__ == '__draw__':
    #chdir(__file__)
    from pyformex.simple import circle
    c = circle(360./20., 360./20., 360.)
    draw(c)
    exportDXF('circle1.dxf', c)

#End
