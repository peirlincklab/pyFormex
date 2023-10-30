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
"""Operations on triangulated surfaces using GTS functions.

This module provides access to GTS from inside pyFormex.
"""
import numpy as np
import re

import pyformex as pf
from pyformex import utils
from pyformex import arraytools as at
from pyformex.path import Path
from pyformex.coords import Coords, bboxIntersection
from pyformex.formex import Formex
from pyformex.mesh import Mesh
from pyformex.multi import multitask

#
# gts commands used:
#   in Debian package: stl2gts gts2stl gtscheck
#   not in Debian package: gtssplit gtscoarsen gtsrefine gtssmooth gtsinside
#

def read_intersectioncurve(fn):
    """Read the intersection curve of a boolean operation

    Parameters
    ----------
    fn: :term:`path_like`
        The name of a file containing an intersection curve produced
        by :func:`gtsset`.

    Returns
    -------
    Mesh
        A Mesh of eltype Line2 containing the line segments on the
        intersection curve.
    """
    RE = re.compile(r"^VECT 1 2 0 2 0 (?P<data>.*)$")
    r = []
    for line in open(fn, 'r'):
        m = RE.match(line)
        if m:
            r.append(m.group('data'))
    nelems = len(r)
    x = np.fromstring('\n'.join(r), sep=' ').reshape(-1, 2, 3)
    return Formex(x).toMesh()


def gtsset(surf1, surf2, op, filt='', ext='', curve=False, check=False,
           verbose=False):
    """Perform boolean/intersection methods on TriSurfaces.

    Boolean operations between two surfaces are a basic operation in
    free surface modeling. Both surfaces should be closed orientable
    non-intersecting manifolds. This means they represent an enclosed
    volume. :meth:`TriSurface.check` can be used to find out if the
    surface is ok.

    The boolean operations are set operations on the enclosed volumes:
    union('+'), difference('-') or intersection('*').

    This uses the external program ``gtsset`` to do the actual computation.

    Parameters
    ----------
    surf1: TriSurface
        The first TriSurface (should be a closed orientable
        non-intersecting manifold).
    surf2: TriSurface
        The second TriSurface (should be a closed orientable
        non-intersecting manifold).
    op: '+', '-', '*' or 'a'
        The boolean operation to perform: union('+'), difference('-')
        or intersection('*'), or 'a' to compute all parts of the intersection,
        allowing to compose different results.
    filt: str
        A filter command to be executed on the gtsset output. The string
        should start with a '|', and the filter will be run as a pipe
        on the gtsset output and should produce the filtered output on
        stdout.
    ext: str
        The extension to be added on the ``result`` file.
    curve: bool
        If True, an intersection curve is computed, else a new surface.

    Returns
    -------
    TriSurface | dict | Mesh | None:

        - if curve is False and op is one of '+', '-' or '\*': the resulting
          TriSurface;
        - if curve is False and op is 'a': a dict with four keys, each having
          a TriSurface as value:

          - 's1in2': the part of surf1 that is inside surf2,
          - 's1out2': the part of surf1 that is outside surf2,
          - 's2in1': the part of surf2 that is inside surf1,
          - 's2out1': the part of surf2 that is outside surf1;

        - if curve is True: a Mesh of eltype Line2, containing the intersection
          curve(s);
        - if surf1 and surf2 do not intersect: None.

    Note
    ----
    The prefered way to invoke this function is by usint the :class:`TriSurface`
    methods: :meth:`TriSurface.gts_set`, :meth:`TriSurface.boolean and
    :meth:`TriSurface.intersection`.

    """
    utils.External.require('gts-extra')

    # import here to avoid circular import
    from pyformex.trisurface import TriSurface
    op = {
        '+': 'union',
        '-': 'diff',
        '*': 'inter',
        'a': 'all',
    }[op]
    options = ''
    if curve:
        options += '-i'
    if check:
        options += ' -s'
    if verbose:
        options += ' -v'
    with utils.TempDir() as tmpdir:
        tmp = tmpdir / 'surface1.gts'
        tmp1 = tmpdir / 'surface2.gts'
        tmp2 = tmpdir / ('result'+ext)
        #print("Writing temp file %s" % tmp)
        surf1.write(tmp, 'gts')
        #print("Writing temp file %s" % tmp1)
        surf2.write(tmp1, 'gts')
        print(f"Performing boolean operation {op}")
        cmd = f"cd {tmpdir} && gtsset {options} {op} {tmp} {tmp1} {filt}"
        P = utils.system(
            cmd, stdout=open(tmp2, 'w'), shell=True, verbose=verbose)
        if P.returncode or verbose:
            print(P.stdout)
        if P.returncode:
            print(P.stderr)
            print("""The boolean procedure didn't return any results.""")
            return None
        if curve:
            res = read_intersectioncurve(tmp2)
        elif op=='all':
            res = {}
            for k in ['s1in2', 's1out2', 's2in1', 's2out1']:
                res[k] = TriSurface.read(tmpdir / (k+'.gts'))
        else:
            res = TriSurface.read(tmp2)
        return res


def gtsinside(surf, pts, dir, keep=False):
    """Test whether points are inside a closed surface.

    This tests whether a point is inside a closed surface
    by shooting a ray from the point in a certain direction
    and tests whether the number of intersections with the surface
    is odd (inside) or even (outside). Shooting directions are
    limited to one of the global axes directions.

    Parameters
    ----------
    surf: TriSurface
        The TriSurface (should be a closed orientable
        non-intersecting manifold).
    pts: :term:`coords_like`
        A Coords with shape (npts, 3)
    dir: int
        The global axis that will be used as shooting direction.

    Returns
    -------
    array
        An int array with the indices of the points that are inside the surface.

    Note
    ----
    This function is not intended to be used directly.
    False negatives or positives may occur when the ray passes precisely
    through the edge of triangles. Use :func:`inside` instead.
    """
    # roll, because the external always shoots in x-direction
    S = surf.rollAxes(dir)
    P = pts.rollAxes(dir)
    with utils.TempDir(keep=keep) as tmpdir:
        if keep:
            print(f"Using temp dir {tmpdir}")
        tmp0 = tmpdir / 'surface.gts'
        tmp1 = tmpdir / 'points.dta'
        tmp2 = tmpdir / 'result.out'
        tmp3 = tmpdir / 'result.stderr'
        #print("Writing temp file %s" % tmp0)
        S.write(tmp0, 'gts')
        #print("Writing temp file %s" % tmp1)
        with open(tmp1, 'w') as f:
            P.tofile(f, sep=' ', format='%f')
            f.write('\n')
        #print("Performing inside testing")
        cmd = "gtsinside %s %s" % (tmp0, tmp1)
        from pyformex import process
        P = process.run(cmd, stdout=open(tmp2, 'w'), stderr=open(tmp3, 'w'))
        if P.returncode:
            print("An error occurred during the testing.\nSee file %s for more details." % tmp2)
            print(P.stdout)
            return None
        #print("Reading results from %s" % tmp2)
        ind = np.fromfile(tmp2, sep=' ', dtype=at.Int)
    return ind


def inside(surf, pts, atol='auto', multi=True, keep=False):
    """Test which of the points pts are inside the surface.

    This uses the ray shooting technique of gtsinside, but avoids (most of)
    the false negatives/positives. It does this by shooting
    in three directions (the three global axis directions) and returning
    the majority vote of the three outcomes.

    Parameters
    ----------
    surf: TriSurface
        The TriSurface (should be a closed orientable
        non-intersecting manifold).
    pts: :term:`coords_like`
        A Coords with shape (npts, 3) or Formex with shape (npts, 1, 3).
    atol: float
        Tolerance used in restricting the points set to the surface's
        bounding box.
    multi: bool
        If True (default), rund the three shooting directions n parallel.
        This reduces the total processing time.
    keep: bool
        If True, the temporary directory with intermediate results is
        not erased. This may be useful for debugging purposes.

    Returns
    -------
    array:
        An int array with the indices of the points that are
        inside the surface.

    See Also
    --------
    TriSurface.inside: the prefered way to call this function
    """
    utils.External.require('gts-extra')

    # We use a Formex so that we can use the prop for keeping the indices
    if not isinstance(pts, Formex):
        pts = Formex(pts)

    if atol == 'auto':
        atol = pts.dsize()*0.001

    # determine bbox of common space of surface and points
    bb = bboxIntersection(surf, pts)
    if bb.size == 0:
        # No bbox intersection: no points inside
        return array([], dtype=Int)

    # Limit the points to the common part
    # Add point numbers as property, to allow return of original numbers
    pts.setProp(np.arange(pts.nelems()))
    pts = pts.clip(pts.testBbox(bb, atol=atol))
    #print(f"Clipped points: {pts.prop}")

    ins = np.zeros((3, pts.nelems()), dtype=bool)
    if not multi:
        for i in range(3):
            #dirs = np.roll(np.arange(3), -i)[1:]
            # clip the surface perpendicular to the shooting direction
            # !! gtsinside seems to fail sometimes when using clipping
            #S = surf  # .clip(testBbox(surf,bb,dirs=dirs,atol=atol),compact=False)
            # find inside points shooting in direction i
            ok = gtsinside(surf, pts.coords, i)
#                           tmpdir = None if tmpdir is None else
#                           Path(tmpdir)/f"gtsinside-{i}")
            ins[i, ok] = True
    else:
        tasks = [(gtsinside, (surf, pts.coords, i)) for i in range(3)]
        ind = multitask(tasks, 3)
        for i in range(3):
            ins[i, ind[i]] = True

    ok = np.where(ins.sum(axis=0) > 1)[0]
    return pts.prop[ok]


# End
