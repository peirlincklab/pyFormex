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
"""Gambit neutral file exporter.

This module contains some functions to export
pyFormex mesh models to a Gambit neutral file.
"""
from time import strftime, gmtime
import numpy as np

import pyformex as pf
from pyformex import utils
from pyformex import arraytools as at
from pyformex.path import Path

# Gambit starts counting at 1 for elements and nodes
# this defines the offset for nodes (nofs), elements (eofs) and faces (fofs)
nofs, eofs, fofs = 1, 1, 1

# Element type translation from pyFormex to Gambit neutral
pyf_neu_eltype = {
    'line2': (1, 2),
    'line3': (1, 3),
    'quad4': (2, 4),
    'quad8': (2, 8),
    'quad9': (2, 9),
    'tri3':  (3, 3),
    'tri6':  (3, 6),
    # 'tri7':  (3, 7),  # NA
    'hex8': (4, 8),
    'hex20': (4, 20),
    'hex27': (4, 27),
    'wedge6': (5, 6),
    # 'wedge15': (5, 15),  # NA
    # 'wedge18': (5, 18),  # NA
    'tet4': (6, 4),
    'tet10': (6, 10),
    # 'pyram5': (7, 5),  # NA
    # 'pyram13': (7, 13),  # NA
    # 'pyram14': (7, 14),  # NA
    # 'pyram18': (7, 18),  # NA
    # 'pyram19': (7, 19),  # NA
}

# This is the order of the gambit nodes in pyFormex !!!!
neu_pyf_order = {
    'quad8': (0, 2, 4, 6, 1, 3, 5, 7),
    'quad9': (0, 2, 4, 6, 1, 3, 5, 7, 8),
    'tri6': (0, 2, 4, 1, 3, 5),
    'hex8': (0, 1, 3, 2, 4, 5, 7, 6),
    'hex20': (0,2,7,5, 12,14,19,17, 1,4,6,3, 13,16,18,15, 8,9,11,10),
    'tet10': (0, 2, 5, 9, 1, 3, 6, 4, 8, 7),
}

# This is the order of the gambit faces in pyFormex !!!!
pyf_neu_faces = {
    'hex8': (3, 1, 0, 2, 4, 5),
    'hex20': (3, 1, 0, 2, 4, 5),
    'hex27': (3, 1, 0, 2, 4, 5),
    'wedge6': 'TODO',
    'tet4': (3, 1, 0, 2),
    'tet10': (3, 1, 0, 2),
}


def writeHeading(fil, ncoords, nelems, ngroups, nbsets, heading):
    """Write the heading of the Gambit neutral file."""
    datetime = strftime('%d %b %Y    %H:%M:%S', gmtime())
    version = pf.__version__.split('-')[0]
    fil.write(f"""\
        CONTROL INFO 2.4.6
** GAMBIT NEUTRAL FILE
{heading[:80]}
PROGRAM:                GAMBIT     VERSION:  2.4.6
{datetime}
     NUMNP     NELEM     NGRPS    NBSETS     NDFCD     NDFVL
""")
    fil.write('%10i%10i%10i%10i%10i%10i\n' % (
        ncoords, nelems, ngroups, nbsets, 3, 3))
    fil.write('ENDOFSECTION\n')


def writeNodes(fil, coords):
    """Write the nodal coordinates to a Gambit neutral file"""
    pf.verbose(2, f"Writing {len(coords)} nodes")
    fil.write('   NODAL COORDINATES 2.4.6\n')
    for i, n in enumerate(coords):
        fil.write("%10d%20.11e%20.11e%20.11e\n" % ((i+nofs,)+tuple(n)))
    fil.write('ENDOFSECTION\n')


def writeElems(fil, elems, eltyp, nplex):
    """Write the element connectivity to a Gambit neutral file"""
    pf.verbose(2, f"Writing {len(elems)} elements of type {eltyp} mplex {nplex}")
    fmt = '%8d %2d %2d ' + '%8d' * min(7,nplex) + '\n'
    more = nplex-7
    while more > 0:
        fmt += ' '*15 + '%8d' * min(7, more) + '\n'
        more -= 7
    fil.write('      ELEMENTS/CELLS 2.4.6\n')
    for i, e in enumerate(elems+nofs):
        fil.write(fmt%((i+eofs, eltyp, nplex)+tuple(e)))
    fil.write('ENDOFSECTION\n')


def writeGroups(fil, groups):
    """Write element groups to a Gambit neutral file"""
    pf.verbose(2, f"Writing {len(groups)} element groups")
    for i, g in enumerate(groups):
        els = groups[g]
        nels = len(els)
        name = f'prop-{g}'
        flags = (0,)
        nflags = len(flags)
        fil.write('       ELEMENT GROUP 2.4.6\n')
        fil.write('GROUP:%11d ELEMENTS:%11d MATERIAL:%11d NFLAGS:%11d\n' % (
            i+1, nels, g, nflags))
        fil.write('%32s\n' % name)
        fil.write(''.join((f'{flag:>8d}' for flag in flags)) + '\n')
        for i in range(0, nels, 10):
            fil.write(''.join((f'{n:>8d}' for n in els[i:i+10])) + '\n')
        fil.write('ENDOFSECTION\n')


def writeBCsets(fil, bcsets, eltyp, order):
    """Write boundary conditions to a Gambit neutral file"""
    pf.verbose(2, f"Writing {len(bcsets)} BC sets")
    for bc in bcsets:
        fil.write('BOUNDARY CONDITIONS 2.4.6\n')
        faces = bcsets[bc]
        if order is not None:
            faces[:, 1] = order[faces[:, 1]]
        faces += (eofs, fofs)  # Gambit starts counting from 1
        itype = 1  # currently only face BC
        nentry = len(faces)
        nvalues = 0
        ibcodes = (6, ) # currently ELEMENT_SIDE only
        fmt = '%32s' + '%8d' * (3+len(ibcodes)) + '\n'
        fil.write(fmt % ((bc, itype, nentry, nvalues) + ibcodes))
        for v in faces:
            fil.write('%10d%5d%5d\n'%(v[0], eltyp, v[1]))
        fil.write('ENDOFSECTION\n')


def writeNEU(filename, M, bcsets={}, heading=None):
    """Export a Mesh in Gambit neutral format

    Parameters
    ----------
    filename: :term:`path_like`
        The output file name, commonly having a suffix '.neu'.
        If the suffix ends on '.gz' or '.bz2', the file will transparently
        be compressed during writing.
    M: :class:`Mesh`
        The Mesh to be be written to the file.
        If the Mesh has prop values, an element group will be added to the
        file for each of the unique values in M.prop. The prop value will
        be written as the material type number.
        If M has no prop values, a single group of all elements is written
        with material type number 0.
    heading: str
        A title line to be shown in the .neu file header.
    bcsets: dict
        A dictionary of boundary conditions where the keys are names and
        the values are arrays with two columns: column one are the element
        numbers and column two are the local face numbers. See Notes

    See also
    -----
    https://web.stanford.edu/class/me469b/handouts/gambit_write.pdf

    Notes
    -----
    bcsets is currently limited to writing ELEMENT/SIDE boundary conditions
    for the faces of volume elements of eltype 'tet4', 'hex8' or 'hex20'.
    The borderface arrays for use in bcsets can be obtained from the second
    return value in::

        M.getFreeEntities(level=-1,return_indices=True)

    or from matching a surface Mesh::

        M.matchFaces(S)[1]

    Examples
    --------
    >>> from pyformex.mesh import Mesh
    >>> f = Path('test_filewrite.neu')
    >>> M = Mesh(eltype='quad4')
    >>> writeNEU(f, M)
    >>> print(f.read_text())
            CONTROL INFO 2.4.6
    ** GAMBIT NEUTRAL FILE
    Generated by pyFormex ...
    PROGRAM:                GAMBIT     VERSION:  2.4.6
    ...
         NUMNP     NELEM     NGRPS    NBSETS     NDFCD     NDFVL
             4         1         1         0         3         3
    ENDOFSECTION
       NODAL COORDINATES 2.4.6
             1   0.00000000000e+00   0.00000000000e+00   0.00000000000e+00
             2   1.00000000000e+00   0.00000000000e+00   0.00000000000e+00
             3   1.00000000000e+00   1.00000000000e+00   0.00000000000e+00
             4   0.00000000000e+00   1.00000000000e+00   0.00000000000e+00
    ENDOFSECTION
          ELEMENTS/CELLS 2.4.6
           1  2  4        1       2       3       4
    ENDOFSECTION
           ELEMENT GROUP 2.4.6
    GROUP:          1 ELEMENTS:          1 MATERIAL:          0 NFLAGS:          1
                              prop-0
           0
           0
    ENDOFSECTION

    >>> f.remove()
    """
    filename = Path(filename)
    pf.verbose(1, f"Write NEU file {filename.absolute()}")
    if heading is None:
        heading = f"Generated by {pf.fullVersion()}"
    elname = M.elName()
    try:
        eltyp, nplex = pyf_neu_eltype[elname]
    except KeyError:
        raise ValueError(
            f"A Mesh with '{M.elName()}' can not be exported to .neu format,"
            f" supported eltypes are {list(pyf_neu_eltype)}")
    ncoords = M.ncoords()
    nelems = M.nelems()
    if nplex != M.nplex():
        raise pf.ImplementationError("Non-matching plexitude!")
    if elname in neu_pyf_order:
        order = at.inverseUniqueIndex(neu_pyf_order[elname])
        elems = M.elems[:, order]
    else:
        elems = M.elems
    if M.prop is None:
        groups = { 0: np.arange(nelems) }
    else:
        groups = M.propDict()
    with utils.File(filename, 'w') as fil:
        writeHeading(fil, ncoords, nelems, len(groups), len(bcsets), heading)
        writeNodes(fil, M.coords)
        writeElems(fil, elems, eltyp, nplex)
        writeGroups(fil, groups)
        if bcsets:
            try:
                order = np.array(pyf_neu_faces[elname], dtype=at.Int)
            except KeyError:
                order = None
            writeBCsets(fil, bcsets, eltyp, order)
        pf.verbose(2, f"Mesh exported to {filename}")
    pf.verbose(2, f"File size: {filename.size} bytes")


# End
