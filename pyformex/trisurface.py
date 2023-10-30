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
"""Operations on triangulated surfaces.

A triangulated surface is a surface consisting solely of triangles.
Any surface in space, no matter how complex, can be approximated with
a triangulated surface.
"""
import numpy as np

import pyformex as pf
from pyformex import arraytools as at
from pyformex import fileread
from pyformex import filewrite
from pyformex import geomtools
from pyformex import inertia
from pyformex import utils
from pyformex.timer import Timer
from pyformex.path import Path
from pyformex.coords import Coords
from pyformex.connectivity import Connectivity
from pyformex.mesh import Mesh
from pyformex.formex import Formex
from pyformex.geometry import Geometry

__all__ = ['TriSurface', 'fillBorder']

#
# gts commands used:
#   in Debian package: stl2gts gts2stl gtscheck
#   not in Debian package: gtssplit gtscoarsen gtsrefine gtssmooth gtsinside
#


############################################################################
# The TriSurface class

@utils.pzf_register
class TriSurface(Mesh):
    """A class representing a triangulated 3D surface.

    A triangulated surface is a surface consisting of a collection of
    triangles. The TriSurface is subclassed from :class:`~mesh.Mesh` with a
    fixed plexitude of 3.
    The surface contains `ntri` triangles and `nedg` edges. Each triangle
    has 3 vertices with 3 coordinates. The total number of vertices is
    `ncoords`.

    Parameters
    ----------
    args:
        Data to initialize the TriSurface. This can be 1, 2 or 3 arguments
        specifying one the the following data sets:

        - an (ntri,3,3) :term:`array_like` specifying the coordinates of
          the vertices of the triangles,
        - a :class:`~formex.Formex` with plexitude 3,
        - a :class:`~mesh.Mesh` with plexitude 3,
        - an (ncoords,3) :term:`coords_like` with the vertex coordinates
          and an (ntri,3) int :term:`array_like` specifying three vertex indices
          for each of the triangles
        - an (ncoords,3) :term:`coords_like` with the vertex coordinates,
          an (nedg,2) int :term:`array_like` specifying the vertex inidices
          of the edges, and an (ntri,3) int :term:`array_like` specifying
          the edge indices of the triangles.

    prop: int :term:`array_like`, optional
        This keyword argument can be used to attribute property values to
        the elements of the TriSurface, like in the :class:`~mesh.Mesh` class.

    See Also
    --------
    TriSurface.read: read a TriSurface from file
    Formex.toSurface: convert a Formex to a TriSurface
    Mesh.toSurface: convert a Mesh to a TriSurface

    Examples
    --------
    This example is a unit square divided in two triangles with the following
    following layout and numbering of nodes(n), elements(e) and edges::

      n3      4    n2
        o---------o
        |        /|
        |  e1   / |
        |      /  |
        |     /   |
       2|    /1   |3
        |   /     |
        |  /      |
        | /   e0  |
        |/        |
        o---------o
      n0     0     n1

    >>> S = Mesh(eltype='quad4').convert('tri3-u').toSurface()
    >>> print(S)
    TriSurface: nnodes: 4, nelems: 2, nplex: 3, level: 2, eltype: tri3
      BBox: [0. 0. 0.], [1. 1. 0.]
      Size: [1. 1. 0.]
      Length: 4.0  Area: 1.0
    >>> print(S.coords)
    [[0. 0. 0.]
     [1. 0. 0.]
     [1. 1. 0.]
     [0. 1. 0.]]
    >>> print(S.elems)
    [[0 1 2]
     [2 3 0]]
    >>> print(S.nedges(), S.nfaces())
    5 2
    >>> print(S.edges)
    [[0 1]
     [2 0]
     [3 0]
     [1 2]
     [2 3]]
    >>> print(S.elem_edges)
    [[0 3 1]
     [4 2 1]]
    """

    _exclude_members_ = ['intersectionWithLines']

    def __init__(self, *args, prop=None, **kargs):
        """Create a new surface."""
        if hasattr(self, 'edglen'):
            del self.edglen

        if len(args) == 0:
            Mesh.__init__(self, [], [], None, 'tri3')
            return  # an empty surface

        if len(args) == 1:
            # argument should be a suitably structured geometry object
            # TriSurface, Mesh, Formex, Coords, ndarray, ...
            a = args[0]

            if isinstance(a, Mesh):
                if a.nplex() != 3 or a.elName() != 'tri3':
                    raise ValueError(
                        "Only meshes with plexitude 3 and eltype 'tri3' "
                        "can be converted to TriSurface!")
                Mesh.__init__(self, a.coords, a.elems, a.prop, 'tri3')

            else:
                if not isinstance(a, Formex):
                    # something that can be converted to a Formex
                    try:
                        a = Formex(a)
                    except ValueError:
                        raise ValueError(
                            "Can not convert objects of type "
                            f"{type(a)} to TriSurface!")

                # now a is a Formex
                if a.nplex() != 3:
                    raise ValueError("Expected an object with plexitude 3!")

                coords, elems = a.coords.fuse()
                Mesh.__init__(self, coords, elems, a.prop, 'tri3')

        else:
            # arguments are (coords,elems) or (coords,edges,faces)
            coords = Coords(args[0])
            if len(coords.shape) != 2:
                raise ValueError("Expected a 2-dim coordinates array")

            if len(args) == 2:
                # arguments are (coords,elems)
                elems = Connectivity(args[1], nplex=3)
                Mesh.__init__(self, coords, elems, None, 'tri3')


            elif len(args) == 3:
                # arguments are (coords,edges,faces)
                edges = Connectivity(args[1], nplex=2)

                if edges.size > 0 and edges.max() >= coords.shape[0]:
                    raise ValueError("Some vertex number is too high")

                faces = Connectivity(args[2], nplex=3)

                if faces.max() >= edges.shape[0]:
                    raise ValueError("Some edge number is too high")

                elems = faces.combine(edges)
                Mesh.__init__(self, coords, elems, None, 'tri3')

                # since we have the extra data available, keep them
                self._memory = {
                    'edges': edges,
                    'elem_edges': faces,
                }
            else:
                raise RuntimeError("Too many positional arguments")

        if prop is not None:
            self.setProp(prop)


    def __setstate__(self, state):
        """Set the object from serialized state.

        This allows to read back old pyFormex Project files where the
        Surface class did not set an element type.
        """
        if 'areas' in state:
            state['_areas'] = state['areas']
            del state['areas']
        self.__dict__.update(state)
        self.eltype = 'tri3'


    #######################################################################
    #
    #   Return information about a TriSurface
    #

    def nedges(self):
        """Return the number of edges of the TriSurface.

        Note
        ----
        As a side-effect, this computes and stores the
        :attr:`~mesh.Mesh.edges` and :attr:`~mesh.Mesh.elem_edges` arrays.
        The returned value is the first dimension of self.edges.
        """
        return self.edges.shape[0]

    def nfaces(self):
        """Return the number of faces of the TriSurface.

        Note
        ----
        As a side-effect, this computes and stores the
        :attr:`~mesh.Mesh.edges` and :attr:`~mesh.Mesh.elem_edges` arrays.
        The returned value is the first dimension of self.elem_edges.
        Use self.nelems() to get the number of faces without having the
        side effect.
        """
        return self.elem_edges.shape[0]

    def vertices(self):
        """Return the coordinates of the nodes of the TriSurface.

        Note
        ----
        The direct use of the :attr:`coords` is prefered over this method.
        """
        return self.coords

    def shape(self):
        """Return the number of points, edges, faces of the TriSurface.

        Returns
        -------
        ncoords: int
            The number of vertices
        nedges: int
            The number of edges
        nfaces:
            The number of faces
        """
        return self.ncoords(), self.nedges(), self.nfaces()


    #######################################################################
    #
    #   Operations that change the TriSurface itself
    #
    #  Make sure that you know what you're doing if you use these
    #
    #
    # Changes to the geometry should by preference be done through the
    # __init__ function, to ensure consistency of the data.
    # Convenience functions are defined to change some of the data.
    #


    def set_coords(self, coords):
        """Change the coords."""
        self.__init__(coords, self.elems, prop=self.prop)
        return self

    def set_elems(self, elems):
        """Change the elems."""
        self.__init__(self.coords, elems, prop=self.prop)

    def set_edges_faces(self, edges, faces):
        """Change the edges and faces."""
        self.__init__(self.coords, edges, faces, prop=self.prop)


    def append(self, S):
        """Merge another surface with self.

        Notes
        -----
        This just merges the data sets, and does not check
        whether the surfaces intersect or are connected!
        This is intended mostly for use inside higher level functions.
        """
        coords = np.concatenate([self.coords, S.coords])
        elems = np.concatenate([self.elems, S.elems+self.ncoords()])
        ## What to do if one of the surfaces has properties, the other one not?
        ## The current policy is to use zero property values for the Surface
        ## without props
        prop = None
        if self.prop is not None or S.prop is not None:
            if self.prop is None:
                self.prop = np.zeros(shape=self.nelems(), dtype=at.Int)
            if S.prop is None:
                p = np.zeros(shape=S.nelems(), dtype=at.Int)
            else:
                p = S.prop
            prop = np.concatenate((self.prop, p))
        self.__init__(coords, elems, prop=prop)


    #######################################################################
    #
    #   read and write
    #


    @classmethod
    def read(clas, fn, ftype=None, convert=False):
        """Read a surface from file.

        Parameters
        ----------
        fn: :term:`path_like`
            The pathname of the file to be read. The name suffix normally
            normally specifies the file type. Currently the following
            file types can be read:

            - obj, off, ply (polygon formats)
            - gts (libgts format)
            - stl (ascii or binary)
            - neu (Gambit neutral)
            - smesh (tetgen)
            - vtk, vtp (vtk formats)

            Compressed files for the polygon, gts and stl formats are also
            supported, if they are compressed with gzip or bzip2 and have
            an extra name suffix '.gz' or '.bz2', respectively.
            These files are transparently decompressed during reading.
            This allows for a very efficient use of storage space for
            large models.
        ftype: str, optional
            Specifies the file type. This is (only) needed if the filename
            suffix does not specify the file type.

        Examples
        --------
        >>> S = TriSurface.read(pf.cfg['datadir'] / 'horse.off')
        >>> print(S)
        TriSurface: nnodes: 669, nelems: 1334, nplex: 3, level: 2, eltype: tri3
          BBox: [-0.0918 -0.0765 -0.0422], [0.0925 0.0777 0.0428]
          Size: [0.1843 0.1542 0.085 ]
          Length: 0.0  Area: 0.03646  Volume: 0.0002634
        """
        fn = Path(fn)
        if ftype is None:
            ftype, compr = fn.ftype_compr()
        else:
            ftype, compr = Path('a.'+ftype).ftype_compr()

        if ftype == 'pgf':
            res = fileread.readPGF(fn, 1)
            res = next(iter(res.values()))
            if isinstance(res, TriSurface):
                return res
            else:
                raise ValueError(f"File {fn} is not a TriSurface")
        elif ftype == 'gts':
            data = fileread.readGTS(fn)
        elif ftype == 'stl':
            coords, normals, color = fileread.readSTL(fn)
            S = TriSurface(coords)
            # S.addField('elemc', normals, '_fnormals_')
            # S.setNormals(S.getField('_fnormals_').convert('elemn'))
            if color:
                S.attrib(color=color)
            return S
        elif ftype in ['obj', 'off', 'ply']:
            func = getattr(fileread, 'read'+ftype.upper())
            poly = func(fn)
            method = 'reduce' if convert else 'prune'
            S = poly.toSurface(method)
            if poly.elems.maxwidth > 3 and not convert:
                nskip = (poly.elems.maxwidth > 3).sum()
                pf.verbose(1, f"Skipping {nskip} elements of plexitude > 3")
            return S
        # The following do not support compression yet
        elif ftype == 'smesh' and not compr:
            from pyformex.plugins import tetgen
            data = tetgen.readSurface(fn)
        elif ftype == 'neu' and not compr:
            M = fileread.readNEU(fn)
            return M.toSurface()
        elif ftype in ['vtp', 'vtk'] and not compr:
            from pyformex.plugins import vtk_itf
            return vtk_itf.read_vtk_surface(fn)
        else:
            raise ValueError(f"Unknown TriSurface type, cannot read file {fn}")
        return TriSurface(*data)


    def write(self, fn, ftype=None, *, name=None, binary=False, color=None,
              **kargs):
        """Write the surface to file.

        Parameters
        ----------
        fn: :term:`path_like`
            The output file name. The suffix will determine the file format,
            unless explicitely specified by ``ftype``.
            Available formats are: 'pgf', 'gts', 'off',
            'stl', 'stla', 'stlb', 'obj', 'smesh', 'vtp', 'vtk'.
            If there is no suffix, 'off' format is used.
            For most file formats, an extra '.gz' or '.bz2' suffix can be
            added to have the file transparently be compressed by 'gzip' or
            'bzip2', respectively.
        ftype: str, optional
            The output file format. If not provided, it is determined from
            the filename suffix.
            For a 'stl' types, ``ftype`` may be set to 'stla' or 'stlb'
            to force ascii or binary STL format.
        name: str, optional
            A name for the model that will be written into the output file
            if it is a 'pgf' or 'obj' format.
        binary: bool
            If True, use binary format when the file format supports it.
            This is only useful if the file format supports both ascii and
            binary formats (currently 'ply' and 'stl').
        color: :term:`color_like`
            The color of the object to be written in case of a binary stl
            type (see also notes).
        kargs:
            Extra keyword arguments to be passed to the writer.

        Notes
        -----
        If the surface has 'color' in its :class:`Attributes`, the color
        will be written to the file in the case of the formats:
        'pgf', 'stlb', 'stl' with ``binary=True``.

        Examples
        --------
        >>> S = Mesh(eltype='quad4').convert('tri3-u').toSurface()
        >>> with utils.TempDir() as dir:
        ...     fn = dir / 'test.off'
        ...     S.write(fn, name='Square')
        ...     print(fn.read_text())
        Writing surface to file .../test.off (off)
        Wrote 4 vertices, 2 faces
        OFF
        # OFF file written by pyFormex ...
        # name=Square
        4 2 0
        0.0 0.0 0.0
        1.0 0.0 0.0
        1.0 1.0 0.0
        0.0 1.0 0.0
        3 0 1 2
        3 2 3 0
        """
        fn = Path(fn)
        if ftype is None:
            ftype, compr = fn.ftype_compr()
        else:
            ftype, compr = Path('a.'+ftype).ftype_compr()

        if compr and ftype in ['smesh', 'vtp', 'vtk']:
            raise ValueError("Compressed surface export is not active (yet)")

        print(f"Writing surface to file {fn} ({ftype})")
        if ftype == 'pgf':
            filewrite.writePGF(fn, self, name=name)
        elif ftype == 'gts':
            filewrite.writeGTS(fn, self)
            print("Wrote {} vertices, {} edges, {} faces".format(*self.shape()))
        elif ftype in ['off', 'obj', 'ply', 'stl', 'stla', 'stlb',
                       'smesh', 'vtp', 'vtk']:
            if ftype == 'off':
                filewrite.writeOFF(fn, self.coords, [self.elems], name=name,
                                   **kargs)
            elif ftype == 'obj':
                filewrite.writeOBJ(fn, self.coords, [self.elems], name=name)
            elif ftype == 'ply':
                filewrite.writePLY(fn, self.coords, [self.elems], name=name,
                                   binary=binary)
            elif ftype in ['stl', 'stla', 'stlb']:
                kargs = {
                    'binary': binary or ftype == 'stlb',
                    'color': color if color is not None else self.attrib['color']
                }
                filewrite.writeSTL(fn, self.coords[self.elems], **kargs)
            elif ftype == 'smesh':
                from pyformex.plugins import tetgen
                tetgen.writeSurface(fn, self.coords, self.elems)
            elif ftype == 'vtp' or ftype == 'vtk':
                from pyformex.plugins import vtk_itf
                vtk_itf.writeVTP(fn, self, checkMesh=False)
            print(f"Wrote {self.ncoords()} vertices, {self.nelems()} faces")
        else:
            print(f"Cannot save TriSurface as file {fn}")

    ####################### TriSurface Data ######################


    def areaNormals(self):
        """Compute the area and normal vectors of the surface triangles.

        Returns
        -------
        areas: ndarray
            A float (nelems,) shaped array with the areas of the triangles.
        fnormals: ndarray
            A float (nelems, 3) shaped array with the normalized normal
            vectors on the triangles.

        Notes
        -----
        As a side-effect, the returned arrays are stored in the object,
        to avoid recalculation.

        See Also
        --------
        areas: return only the areas
        normals: return only the normals
        avgVertexNormals: return averaged normals at the vertices

        Examples
        --------
        >>> S = Mesh(eltype='quad4').convert('tri3-u').toSurface()
        >>> areas, normals = S.areaNormals()
        >>> print(areas)
        [0.5 0.5]
        >>> print(normals)
        [[0. 0. 1.]
         [0. 0. 1.]]
        """
        areas = self.getField('_areas')
        fnormals = self.getField('_fnormals')
        if areas is None or fnormals is None:
            areas, fnormals = geomtools.areaNormals(self.coords[self.elems])
            self.addField('elemc', areas, '_areas')
            self.addField('elemc', fnormals, '_fnormals')
            return areas, fnormals
        else:
            return areas.data, fnormals.data


    def areas(self):
        """Return the areas of the triangles.

        Returns
        -------
        areas: ndarray
            A float (nelems,) shaped array with the areas of the triangles.

        Notes
        -----
        As a side-effect, the normals are computed as well and both are stored
        in the object, to avoid recalculation.

        See Also
        --------
        :meth:`~mesh.Mesh.area`: return the total area of the surface

        Examples
        --------
        >>> S = Mesh(eltype='quad4').convert('tri3-u').toSurface()
        >>> print(S.areas())
        [0.5 0.5]
        """
        return self.areaNormals()[0]


    def normals(self):
        """Return the normals on the triangles.

        Returns
        -------
        normals: ndarray
            A float (nelems, 3) shaped array with the normalized normal
            vectors on the triangles.

        Notes
        -----
        As a side-effect, the areas are computed as well and both are stored
        in the object, to avoid recalculation.

        See Also
        --------
        avgVertexNormals: return averaged normals at the vertices

        Examples
        --------
        >>> S = Mesh(eltype='quad4').convert('tri3-u').toSurface()
        >>> print(S.normals())
        [[0. 0. 1.]
         [0. 0. 1.]]
        """
        return self.areaNormals()[1]


    def avgVertexNormals(self):
        """Compute the average normals at the vertices.

        TriSurfaces are often used as an approximation of a smooth surface.
        In such case, a more realistic rendering is obtained by using the
        average normals at the vertices instead of the facet normals.
        The normals are computed as the average of the normals on the faces
        connected to the node, using the angle between the edges as weights.

        Returns
        -------
        normals: ndarray
            A float (ncoords, 3) shaped array with the normalized
            averaged normal vectors at the nodes.

        See Also
        --------
        geomtools.polygonAvgNormals: the function used to compute the
            average normals and providing more options and examples.

        Examples
        --------
        The model is an octaeder having its vertices in the directions
        of the global axes.

        >>> from pyformex import simple
        >>> S = simple.sphere(0, base='octa')
        >>> print(S.avgVertexNormals())
        [[ 1.  0.  0.]
         [ 0.  1.  0.]
         [ 0.  0.  1.]
         [-1.  0.  0.]
         [ 0. -1.  0.]
         [ 0.  0. -1.]]
        """
        return geomtools.polygonAvgNormals(self.coords, self.elems)


    def volume(self):
        """Return the enclosed volume of the surface.

        This will only be correct if the surface is a closed manifold.
        """
        x = self.coords[self.elems]
        return inertia.surface_volume(x).sum()


    def nodalWeights(self):
        """Returns point weight based on adjacent area weight.

        One third of the area of each triangle is attributed to each of
        its nodes, and the results are summed at the nodes.

        Returns
        -------
        np.ndarray
            Area based point weight array.

        Examples
        --------
        >>> from pyformex.simple import Cube
        >>> S = Cube().convert('tri3-u').toSurface()
        >>> print(S.nodalWeights())
        [1.     0.6667 0.6667 0.6667 0.6667 0.6667 1.     0.6667]
        >>> print(S.nodalWeights().sum())
        6.0
        """
        areas = self.areas()
        pweight = at.nodalSum(areas, self.elems)[0]
        return pweight.reshape(-1) / 3


    def inertia(self, model='C', density=1.0, totalmass=None):
        """Return inertia related quantities of the surface.

        Parameters
        ----------
        model: 'C' | 'W' | 'X' | 'A' | 'V'
            Defines how the mass is distributed over the model.

            - 'C': The mass of each triangle is concentrated at
              the centroid of the triangle. This is the default.
            - 'W': The mass of each triangle is concentrated at the nodes
              of the triangles, attributing ont third to each.
            - 'X': The mass is concentrated at the nodes, attributing an
              equal share of the total mass to each of them.
            - 'A': The mass is evenly distributed over the triangles. This
              is currently not implemented!
            - 'V', the mass is evenly distributed over the volume inside
              the surface.

        density: float
            A constant density (mass per unit area, or mass per unit volume
            with ``model='V'``. This allows the returned inertia values to
            be realistic.

        Returns
        -------
        :class:`~inertia.Inertia`
            An Inertia instance with the following attributes:

            - mass: the total mass (float)
            - ctr:: the center of mass: float (3,)
            - tensor: the inertia tensor in the central axes: shape (3,3)

        Notes
        -----
        The 'A' model is currently not implemented. The 'C' model
        neglects the inertia of each triangle around its own centroid.

        It is currently not possible to specify variable density.

        Examples
        --------
        This is an approximation of a spherical surface with radius R=1.
        A perfect spherical surface with density 1 has a mass
        ``M = 4 πR^2 = 12.566...`` and a rotational inertia
        ``2/3 MR^2 = 8.377...``.

        >>> from pyformex.simple import sphere
        >>> S = sphere(8)
        >>> I = S.inertia()
        >>> print(I.mass)
        12.50...
        >>> print(I.tensor)
        [[ 8.2735  0.     -0.    ]
         [ 0.      8.2735  0.    ]
         [-0.      0.      8.2735]]

        The results are smaller than the theoretical, because the nodes
        are on the sphere, but the triangle centroids are slightly inside.
        Therefore, concentrating the mass at the nodes gives better results.

        >>> I = S.inertia(model='X')
        >>> print(I.mass)
        12.50...
        >>> print(I.tensor)
        [[ 8.3375  0.     -0.    ]
         [ 0.      8.3375  0.    ]
         [-0.      0.      8.3375]]

        Let's use an area-equivalent spherical approximation instead: this
        has the nodes slightly outside the sphere and the centroids inside.
        As expected, it delivers the correct mass.

        >>> SA = sphere(8, equiv='A')
        >>> I = SA.inertia()
        >>> print(I.mass)
        12.566...
        >>> print(I.tensor)
        [[ 8.3533 -0.     -0.    ]
         [-0.      8.3533 -0.    ]
         [-0.     -0.      8.3533]]

        Considered as a volume, the mass of a perfect sphere is
        4/3 πR^2 = 4.188... and the inertia is 2/5 MR^2 = 1.675....

        >>> I = S.inertia(model='V')
        >>> print(I.mass)
        4.1526...
        >>> print(I.tensor)
        [[ 1.6515  0.     -0.    ]
         [ 0.      1.6515 -0.    ]
         [-0.     -0.      1.6515]]

        With a volume-equivalent model, we get:

        >>> SV = sphere(8, equiv='V')
        >>> I = SV.inertia(model='V')
        >>> print(I.mass)
        4.188...
        >>> print(I.tensor)
        [[ 1.6755 -0.      0.    ]
         [-0.      1.6755 -0.    ]
         [ 0.     -0.      1.6755]]
       """
        if model == 'V':
            x = self.coords[self.elems]
            V, C, I = inertia.surface_volume_inertia(x)  # noqa: E741
            I = inertia.Tensor(I)  # noqa: E741
            I = inertia.Inertia(I, mass=V, ctr=C)  # noqa: E741
        elif model == 'W':
            xmass = self.nodalWeights()
            I = self.coords.inertia(mass=xmass)
        elif model == 'X':
            xmass = np.full((self.ncoords(),), self.area() / self.ncoords())
            I = self.coords.inertia(mass=xmass)
        else:
            I = self.centroids().inertia(mass=self.areas())  # noqa: E741
        I.mass *= density
        I *= density  # noqa: E741
        return I


    def curvature(self, neigh=1):
        """Compute curvature parameters at the nodes.

        Parameters
        ----------
        neigh: int
            The maximum number of edge steps allowed from a node to its
            neigbors to have them included in the node's neigborhood.

        Returns
        -------
        :class:`~utils.Namespace`
            An object with the following attributes:

            - S: the shape index
            - C: the curvedness
            - K: the Gaussian curvature
            - H: the mean curvature
            - k1: the first principal curvature
            - k2: the second principal curvature
            - d1: the first principal direction
            - d2: the second principal direction

        Notes
        -----
        Algorithms are based on Koenderink and Van Doorn, 1992 and
        Dong and Wang, 2005.

        The shape index varies between -1 and +1 and classifies the
        surface as follows::

           concave     concave                   convex     convex
           ellipsoid   cylinder   hyperboloid    cylinder   ellipsoid
          +----------+----------+--------------+----------+----------+
         -1        -5/8       -3/8            3/8        5/8         1
        """
        # calculate neigh-ring neighborhood of the nodes
        adj = _adjacency_arrays(self.edges, nsteps=neigh)[-1]
        adjNotOk = adj<0
        # remove the nodes that have less than three adjacent nodes,
        adjNotOk[(adj>=0).sum(-1) <= 2] = True
        # calculate unit length average normals at the nodes p
        # a weight 1/|gi-p| could be used (gi=center of the face fi)
        p = self.coords
        n = self.avgVertexNormals()
        # double-precision: this will allow us to check the sign of the angles
        # BV: why is double precision needed to check a sign???
        p = p.astype(np.float64)
        n = n.astype(np.float64)
        vp = p[adj] - p[:, np.newaxis]
        vn = n[adj] - n[:, np.newaxis]
        # where adjNotOk, set vectors = [0.,0.,0.]
        # this will result in NaN values
        vp[adjNotOk] = 0.
        vn[adjNotOk] = 0.
        # calculate unit length projection of vp onto the tangent plane
        t = geomtools.projectionVOP(vp, n[:, np.newaxis])
        t = at.normalize(t)
        # calculate normal curvature
        with np.errstate(divide='ignore', invalid='ignore'):
            k = at.dotpr(vp, vn) / at.dotpr(vp, vp)
        # calculate maximum normal curvature and corresponding coordinate system
        try:
            imax = np.nanargmax(k, -1)
            kmax = k[np.arange(len(k)), imax]
            tmax = t[np.arange(len(k)), imax]
        except Exception:
            # bug with numpy.nanargmax: cannot convert float NaN to integer
            kmax = np.resize(np.NaN, (k.shape[0]))
            tmax = np.resize(np.NaN, (t.shape[0], 3))
            w = ~(np.isnan(k).all(1))
            imax = np.nanargmax(k[w], -1)
            kmax[w] = k[w, imax]
            tmax[w] = t[w, imax]
        tmax1 = tmax
        tmax2 = np.cross(n, tmax1)
        tmax2 = at.normalize(tmax2)
        # calculate angles (tmax1,t)
        theta, rot = geomtools.rotationAngle(
            np.repeat(tmax1[:, np.newaxis], t.shape[1], 1),
            t, angle_spec=at.RAD)
        theta = theta.reshape(t.shape[:2])
        rot = rot.reshape(t.shape)
        # check the sign of the angles
        d = at.dotpr(rot, n[:, np.newaxis])/(
            # divide by length for round-off errors
            at.length(rot)*at.length(n)[:, np.newaxis])
        cw = np.isclose(d, [-1.])
        theta[cw] = -theta[cw]
        # calculate coefficients
        ct = np.cos(theta)
        st = np.sin(theta)
        a = kmax
        a11 = np.nansum(ct**2 * st**2, -1)
        a12 = np.nansum(ct * st**3, -1)
        a22 = np.nansum(st**4, -1)
        a13 = np.nansum((k-a[:, np.newaxis] * ct**2) * ct*st, -1)
        a23 = np.nansum((k-a[:, np.newaxis] * ct**2) * st**2, -1)
        denom = (a11*a22-a12**2)
        b = (a13*a22-a23*a12)/denom
        c = (a11*a23-a12*a13)/denom
        del a11, a12, a22, a13, a23
        # calculate the Gaussian and mean curvature
        K = a*c - b**2/4
        H = (a+c)/2
        del a, c
        # calculate the principal curvatures and principal directions
        kk = np.sqrt(H**2-K)
        k1 = H + kk
        k2 = H - kk
        theta0 = 0.5*np.arcsin(b/(k2-k1))
        ct = np.cos(theta0)
        st = np.sin(theta0)
        w = np.apply_along_axis(np.isclose, 0, -b, 2*(k2-k1)*ct*st)
        theta0w = np.pi-theta0[w]
        ct[w] = np.cos(theta0w)
        st[w] = np.sin(theta0w)
        e1 = ct[:, np.newaxis]*tmax1 +st[:, np.newaxis]*tmax2
        e2 = ct[:, np.newaxis]*tmax2 -st[:, np.newaxis]*tmax1
        # calculate the shape index and curvedness
        S = 2./np.pi * np.arctan((k1+k2)/(k1-k2))
        C = np.sqrt((k1**2 + k2**2) / 2)
        return utils.Namespace(K=K, H=H, S=S, C=C, k1=k1, k2=k2, d1=e1, d2=e2)


    # TODO: store this information internally
    def surfaceType(self):
        """Check whether the TriSurface is a manifold, orientable and closed.

        Returns
        -------
        manifold: bool
            True if the surface is a manifold
        orientable: bool
            True if the surface is an orientable manifold
        closed: bool
            True if the surface is a closed manifold
        mincon: int
            The minimum number of triangles at any edge
        maxcon: int
            The maximum  number of triangles at any edge

        See Also
        --------
        isManifold: check if a surface is a manifold
        isOrientable: check if a surface is an orientable manifold
        isClosedManifold: check if a surface is a closed manifold

        Notes
        -----
        A Möbius ring is an open non-orientable manifold. A Klein bottle
        is a closed non-orientable (self-intersecting) manifold.

        Examples
        --------
        >>> from pyformex import simple
        >>> simple.sphere(4).surfaceType()
        (True, True, True, 2, 2)
        >>> simple.MoebiusRing().toSurface().surfaceType()
        (True, False, False, 1, 2)
        >>> from pyformex.examples.KleinBottle import KleinBottle
        >>> S = KleinBottle().toSurface()
        >>> S.surfaceType()
        (True, True, False, 1, 2)
        >>> S.fuse().surfaceType()
        (True, False, True, 2, 2)
        """
        if self.nelems() == 0:
            return False, False, False, 0, 0
        ncon = self.nEdgeConnected()
        maxcon = ncon.max()
        mincon = ncon.min()
        manifold = maxcon == 2
        closed = mincon == 2
        orientable = len(self.amborientedEdges()) == 0 if manifold else False
        return manifold, orientable, closed, mincon, maxcon


    ####### MANIFOLD #################


    def isManifold(self):
        """Check whether the TriSurface is a manifold.

        A surface is a manifold if for every point of the surface a small
        sphere exists that cuts the surface to a part that can continuously
        be deformed to an open disk.

        Returns
        -------
        bool
            True if the surface is a manifold.
        """
        return self.surfaceType()[0]


    def isClosedManifold(self):
        """Check whether the TriSurface is a closed manifold.

        A closed manifold is a manifold where each edge has exactly
        two triangles connected to it.

        Returns
        -------
        bool
            True if the surface is a closed manifold.
        """
        stype = self.surfaceType()
        return stype[0] and stype[2]


    def isConvexManifold(self):
        """Check whether the TriSurface is a convex manifold.

        Returns
        -------
        bool
            True if the surface is a convex manifold.

        Examples
        --------
        >>> from pyformex import simple
        >>> simple.sphere(4).isConvexManifold()
        True
        """
        return self.isManifold() and self.edgeAngles().min()>=0.


    def isOrientable(self):
        """Check whether the TriSurface is an orientable manifold.

        A surface is an orientable manifold if it is a manifold and if
        for all edges where two triangles meet, the triangles have the
        two nodes in opposite order in their element definition.
        This also means that if the two triangles are rotated around the
        edge to fall in the same plane, with their third vertex at
        opposite sides of the edge, the triangles have the same positive
        normal.

        Returns
        -------
        bool
            True if the surface is orientable.

        See Also
        --------
        amborientedEdges: list the edges where the normals are opposite
        """
        return self.surfaceType()[1]


    # TODO: We should probably add optional sorting (# connections) here
    # TODO: this could be moved into Mesh.nonManifoldEdges if it works
    #       for all level 2 Meshes
    def nonManifoldEdges(self):
        """Return the non-manifold edges.

        Non-manifold edges are edges having more than two triangles
        connected to them.

        Returns
        -------
        int array
            The indices of the non-manifold edges in a TriSurface.
            These indices refer to the list of edges as stored in
            :attr:`~Mesh.edges`.
        """
        return np.where(self.nEdgeConnected()>2)[0]


    def nonManifoldEdgesFaces(self):
        """Return the non-manifold edges and faces.

        Non-manifold edges are edges that are connected to more than
        two faces.

        Returns
        -------
        edges: int array
            The indices of the non-manifold edges.
        faces: int array
            The indices of the faces connected to any of the non-manifold edges.
        """
        conn = self.edgeConnections()
        ed = (conn!=-1).sum(axis=1)>2
        fa = np.unique(conn[ed])
        return np.arange(len(ed))[ed], fa[fa!=-1]


    def removeNonManifold(self):
        """Remove the non-manifold edges.

        Removes the non-manifold edges by iteratively applying
        :meth:`removeDuplicate` and :meth:`collapseEdge` until no edge
        has more than two connected triangles.

        Returns
        -------
        TriSurface
            The reduced surface.
        """
        S = self.removeDuplicate()
        non_manifold_edges = self.nonManifoldEdges()
        while non_manifold_edges.any():
            print(f"# nonmanifold edges: {len(non_manifold_edges)}")
            maxcon = S.nEdgeConnected().max()
            wmax = np.where(S.nEdgeConnected()==maxcon)[0]
            S = S.collapseEdge(wmax[0])
            S = S.removeDuplicate()
            non_manifold_edges = S.nonManifoldEdges()
        return S


    def amborientedEdges(self):
        """Return the amboriented edges.

        Amboriented edges are edges where two triangles are connected
        with different orientation, making the surface non-orientable.

        Returns
        -------
        int array
            The indices of the amboriented edges in a TriSurface.

        Notes
        -----
        This requires that the surface is a manifold. Non-manifold edges
        are also amboriented, but are not included in this list. An error is
        raised if there are non-manifold edges.

        In a manifold surface there are only two triangles possible at an
        edge,and they should have the edge nodes numbered in different order
        for the surface to be orientable. Thus all the edges should come out
        as unique when permutations='none' is used
        in :func:`arraytools.uniqueRowsIndex`. The non-unique edges are
        the amboriented edges.
        """
        ncon = self.nEdgeConnected()
        if ncon.max() > 2:
            raise ValueError("The surface is not a manifold!")
        all_edges = self.elems.selectNodes(1)
        uniq, uniqid = at.uniqueRowsIndex(all_edges, permutations='all')
        nuniq, nuniqid = at.uniqueRowsIndex(all_edges, permutations='none')
        w = at.complement(nuniq, len(all_edges))
        ambo = uniqid[w]
        ambo.sort()
        return ambo


    ###### BORDER ######################


    def borderEdges(self):
        """Find the border edges of a TriSurface.

        Border edges are edges that belong to only one element.

        Returns
        -------
        bool ndarray
            An array of length self.nedges() that is True for the
            edges that are on the border of the surface.

        Examples
        --------
        >>> S = Mesh(eltype='quad4').convert('tri3-u').toSurface()
        >>> print(S.borderEdges())
        [ True False  True  True  True]
        """
        return self.nEdgeConnected() <= 1


    def borderEdgeNrs(self):
        """Returns the numbers of the border edges.

        Returns
        -------
        int array
            The indices of the border edges.
            These indices refer to the list of edges as stored in
            :attr:`~Mesh.edges`.

        Examples
        --------
        >>> S = Mesh(eltype='quad4').convert('tri3-u').toSurface()
        >>> print(S.borderEdgeNrs())
        [0 2 3 4]
        """
        return np.where(self.nEdgeConnected() <= 1)[0]


    def borderNodeNrs(self):
        """Detect the border nodes of TriSurface.

        The border nodes are the vertices belonging to the border edges.

        Returns
        -------
        int array
            The indices of the border nodes.
        """
        border = self.edges[self.borderEdgeNrs()]
        return np.unique(border)


    def checkBorder(self):
        """Find the border contours of a TriSurface.

        Returns
        -------
        list of :class:`~elements.Elems`
            A list of connectivity tables. Each table holds the
            subsequent line segments of one continuous contour of the border
            of the surface.

        Examples
        --------
        >>> S = Mesh(eltype='quad4').convert('tri3-u').toSurface()
        >>> S.checkBorder()
        [Elems([[0, 1],
               [1, 2],
               [2, 3],
               [3, 0]], eltype=Line2)]

        """
        border = self.edges[self.borderEdges()]
        if len(border) > 0:
            return border.chained()
        else:
            return []


    def border(self, compact=True):
        """Return the border meshes of a TriSurface.

        Parameters
        ----------
        compact: bool
            If True (default), the returned meshes are compacted.
            Setting compact=False will return all Meshes with the full
            surface coordinate sets. This is e.g useful for filling the
            border and merging the result with the original surface.

        Returns
        -------
        list of :class:`~mesh.Mesh`
            The complete border of the surface is returned as a list
            of plex-2 Meshes. Each Mesh constitutes a continuous part
            of the border.
        """
        ML = [Mesh(self.coords, e) for e in self.checkBorder()]
        if compact:
            ML = [M.compact() for M in ML]
        return ML


    def fillBorder(self, method='radial', dir=None, compact=True):
        """Fill the border areas of a surface.

        Parameters
        ----------
        method: str
            One of the methods accepted by the :func:`fillBorder` function:
            'radial', 'border' or 'planar.
        dir: (3,) :term:`array_like`, optional
            Only used with ``method='planar'``: the projection direction.
            See :func:`fillBorder`.
        compact: bool
            If True (default), the returned surfaces are compacted. If False,
            they still retain all the nodes of the original surface.

        Returns
        -------
        list of TriSurface
            The list of surfaces that fill all the border contours of the
            input surface as obtained by :meth:border'. If the surface
            is initially closed, an empty list is returned.

            The surfaces will have property values higher than those of
            the parent surface. Thus, if they are added to the surface
            to close the holes in it, the different parts can still be
            identified.

        See Also
        --------
        close: closes the surface by adding the border fills
        :func:`trisurface.fillBorder`: fill a contour with a TriSurface
        """
        if self.prop is None:
            mprop = 1
        else:
            mprop = self.prop.max()+1
        return [fillBorder(b, method, dir).setProp(mprop+i)
                for i, b in enumerate(self.border(compact=compact))]


    def close(self, method='radial', dir=None):
        """Close all the holes in a surface.

        Computes the hole filling surfaces and adds them to the
        surface to make it a closed surface. Parameters are like for
        :meth:`fillBorder`.

        Returns
        -------
        TriSurface
            A TriSurface which is the merging of the input surface
            with the surfaces returned by :meth:`fillBorder`.

        See Also
        --------
        fillBorder: compute the hole filling surfaces
        """
        # TODO: check that the normals are correctly oriented
        border = self.fillBorder(method, dir, compact=method=='radial')
        if method == 'radial':
            # The borders are compacted: merge them
            return self.concatenate([self]+border)
        else:
            # The borders use the same nodal coordinates as the input
            # just merge elems and props
            # TODO: this should be moved into the merging method
            elems = np.concatenate([m.elems for m in [self]+border], axis=0)
            if self.prop is None:
                prop = np.zeros(shape=self.nelems(), dtype=at.Int)
            else:
                prop = self.prop
            prop = np.concatenate([prop] + [m.prop for m in border])
            return TriSurface(self.coords, elems, prop=prop)


    #########################
    ##  Quality  measures  ##
    #########################


    def edgeLengths(self):
        """Returns the lengths of all edges

        Returns
        -------
        float array
            The length of all the edges, in the order of :attr:`Mesh.edges`.

        Notes
        -----
        As a side effect, this computes and stores the connectivities
        of the edges to nodes and of the elements to edges in the
        attributes ``edges``, resp. ``elem_edges``.
        """
        edg = self.coords[self.edges]
        return at.length(edg[:, 1]-edg[:, 0])


    @utils.warning("trisurface_edgeangles")
    def edgeAngles(self, return_mask=False):
        """Return the signed angles over all edges.

        The edge angles are the angles between the faces connected to
        that edge. It is the angle between the 2 face normals. The surface
        should be a manifold (having max. 2 faces per edge). The returned
        angles are in degrees in the range ]-180, 180]. The sign of the
        angle determines the convexity of the surface over that edge:

        - angle < 0: concave
        - angle = 0: flat
        - angle > 0: convex
        - angle = 180: folded

        Parameters
        ----------
        return_mask: bool
            If True, also returns the mask of edges connecting two faces.

        Returns
        -------
        angles: float array
            An array with for each edge the angle between the normals on
            the two faces sharing that edge. For edges connected to only
            one element, a value 0 is returned.
        mask: bool array
            True for the edges that connect two faces. Only returned if
            return_mask is True.

        Notes
        -----
        As a side effect, this method also sets the area, normals,
        elem_edges and edges attributes.
        """
        # get connections of edges to faces
        conn = self.elem_edges.inverse(expand=True)
        if conn.shape[1] > 2:
            raise RuntimeError("The TriSurface is not a manifold")
        # get normals on all faces
        n = self.normals()
        # Flag edges that connect two faces
        conn2 = (conn >= 0).sum(axis=-1) == 2
        # get adjacent facet normals for 2-connected edges
        n = n[conn[conn2]]
        edg = self.coords[self.edges]
        edg = edg[:, 1]-edg[:, 0]
        ang = geomtools.rotationAngle(n[:, 0], n[:, 1], m=edg[conn2],
                                      angle_spec=at.DEG)
        # Initialize signed angles to all 0. values
        sangles = np.zeros((conn.shape[0],))
        sangles[conn2] = ang
        # Clip to the -180...+180. range
        sangles = sangles.clip(min=-180., max=180.)
        # Return results
        if return_mask:
            return sangles, conn2
        else:
            return sangles


    def featureEdges(self, angle=60., minangle=None):
        """Return the feature edges of the surface.

        Feature edges are edges that are prominent features of the geometry.
        They are either border edges or edges where the normals on the two
        adjacent triangles differ more than a given value.
        The non feature edges then represent edges on a rather smooth surface.

        Parameters
        ----------
        angle: float
            The minimum value of the angle (in degrees) between the normals on
            two adjacent triangles in order for the edge to be considered a
            feature edge.
        minangle: float, optional
            The maximum negative edge angle value for concave edges to be
            considered feature edges. If not specified, this is set equal
            to -angle.

        Returns
        -------
        bool array
            An array with shape (nedg,) where the feature edges
            are marked True. These are the edges where sel.edgeAngles()
            is outside the range [minangle, angle].

        Notes
        -----
        As a side effect, this also sets the `elem_edges` and `edges`
        attributes, which can be used to get the edge data with the same
        numbering as used in the returned mask. Thus, the following
        constructs a Mesh with the feature edges of a surface S::

             p = S.featureEdges()
             Mesh(S.coords,S.edges[p])
        """
        if minangle is None:
            minangle = -angle
        angles = self.edgeAngles()
        return (angles < minangle) | (angles > angle)


    # TODO: store these data in Fields
    def _compute_data(self):
        """Compute data for all edges and faces."""
        if hasattr(self, 'edglen'):
            return
        areas = self.areas()
        self.edglen = self.edgeLengths()
        facedg = self.edglen[self.elem_edges]
        self.peri = facedg.sum(axis=-1)
        self.edgmin = facedg.min(axis=-1)
        self.edgmax = facedg.max(axis=-1)
        self.altmin = 2*areas / self.edgmax
        self.aspect = self.edgmax/self.altmin
        qual_equi = np.sqrt(np.sqrt(3.)) / 6.
        self.qual = np.sqrt(areas) / self.peri / qual_equi


    def quality(self):
        """Compute a quality measure for the triangle schapes.

        The quality of a triangle is defined as the ratio of the square
        root of its surface area to its perimeter, divided by the same
        ratio for an equilateral triangle with the same area.  The quality
        thus has a value 1.0 for an equilateral triangle and tends to 0.0
        for a very stretched triangle.

        Returns
        -------
        array:
            A float array with the quality of each of the triangles.

        Examples
        --------
        This model has four triangles with increasing shear. The first
        is an equilateral triangle. The last is the most obtuse.

        >>> F = Formex('3:064')
        >>> S = Formex.concatenate([F.shear(0,1,a).trl(0,2*a)
        ...     for a in [0.5, 1., 1.5, 2.]]
        ...     ).toSurface().scale([1., np.sqrt(3.)/2, 1.])
        >>> print(S.areas())
        [0.433 0.433 0.433 0.433]
        >>> print(S.perimeters())
        [3.     3.1889 3.7321 4.5023]
        >>> print(S.aspectRatio())
        [1.1547 2.0207 3.4641 5.4848]
        >>> print(S.quality())
        [1.     0.9408 0.8038 0.6663]
        """
        self._compute_data()
        return self.qual


    def aspectRatio(self):
        """Return the apect ratio of the triangles of the surface.

        The aspect ratio of a triangle is the ratio of the longest edge
        over the smallest altitude of the triangle.
        Equilateral triangles have the smallest aspect ratio: 2/√3.

        Returns
        -------
        array:
            A float array with the aspect ratio of each of the triangles.

        See Also
        --------
        quality: compute a quality measure for triangular meshes
        """
        self._compute_data()
        return self.aspect


    def perimeters(self):
        """Return the perimeters of all triangles.

        Returns
        -------
        array:
            A float array with the perimeter of each of the triangles.

        See Also
        --------
        quality: compute a quality measure for triangular meshes
        """
        self._compute_data()
        return self.peri


    def smallestAltitude(self):
        """Return the smallest altitude of the triangles of the surface."""
        self._compute_data()
        return self.altmin


    def longestEdge(self):
        """Return the longest edge of the triangles of the surface."""
        self._compute_data()
        return self.edgmax


    def shortestEdge(self):
        """Return the shortest edge of the triangles of the surface."""
        self._compute_data()
        return self.edgmin


    def stats(self):
        """Return a text with full statistics about the surface."""
        bbox = self.bbox()
        manifold, orientable, closed, mincon, maxcon = self.surfaceType()
        self._compute_data()
        area = self.area()
        qual = self.quality()
        s = f"""
Size: {self.ncoords()} vertices, {self.nedges()} edges and {self.nfaces()} faces
Bounding box: min {bbox[0]}, max {bbox[1]}
Minimal/maximal number of connected faces per edge: {mincon}/{maxcon}
Surface is{'' if manifold else ' not'} a{' closed' if closed else ''} manifold
Facet area: min {self.areas().min():.4f}; mean {self.areas().mean():.4f}; max {self.areas().max():.4f}
Edge length: min {self.edglen.min():.4f}; mean {self.edglen.mean():.4f}; max {self.edglen.max():.4f}
Smallest altitude: {self.altmin.min():.4f}; largest aspect ratio: {self.aspect.max():.4f}
Quality: {qual.min():.4f} .. {qual.max():.4f}
"""  # noqa: E501
        if manifold:
            angles = self.edgeAngles()
            if closed:
                volume = self.volume()

            s += (f"Angle between adjacent facets: min: {angles.min()}; "
                  f"mean: {angles.mean()}; max: {angles.max()}\n")

        s += f"Total area: {area}; "
        if manifold and closed:
            s += f"Enclosed volume: {volume}"
        else:
            s += "No volume (not a closed manifold!)"
        return s


    def distanceOfPoints(self, X, return_points=False):
        """Find the distances of points X to the TriSurface.

        The distance of a point is the minimum of:
        - the smallest perpendicular distance to any of the facets;
        - the smallest perpendicular distance to any of the edges;
        - the smallest distance to any of the vertices.

        Parameters
        ----------
        X: :term:`coords_like`
            An (nX,3) shaped float array with the coordinates of nX points.
        return_points: bool, optional
            If True, also returns an array with the closest points on the
            surface.

        Returns
        -------
        dist: array
            A float array of length nX with the distance of the points to the
            surface.
        footpoints: array
            Only returned if return_points = True: an array with shape (nX,3)
            holding the coordinates of the footpoints on the surface.
        """
        t = Timer(auto=True)
        with t.newtag("Vertex distance"):
            # distance from vertices
            ind, dist = geomtools.closest(X, self.coords, return_dist=True)
            if return_points:
                points = self.coords[ind]

        with t.newtag("Edge distance"):
            # distance from edges
            Ep = self.coords[self.edges]
            res = geomtools.edgeDistance(X, Ep, return_points)  # OKpid, OKdist, (OKpoints)
            okE, distE = res[:2]
            closer = distE < dist[okE]
            if closer.size > 0:
                dist[okE[closer]] = distE[closer]
                if return_points:
                    points[okE[closer]] = res[2][closer]

        with t.newtag("Face distance"):
            # distance from faces
            Fp = self.coords[self.elems]
            res = geomtools.faceDistance(X, Fp, return_points)  # OKpid, OKdist, (OKpoints)
            okF, distF = res[:2]
            closer = distF < dist[okF]
            if closer.size > 0:
                dist[okF[closer]] = distF[closer]
                if return_points:
                    points[okF[closer]] = res[2][closer]

        if return_points:
            return dist, points
        else:
            return dist


    def degenerate(self):
        """Return a list of the degenerate faces according to area and normals.

        A triangle is degenerate if its area is less or equal to zero or the
        normal has a nan.

        Returns
        -------
        int array
            The sorted list of indices of the degenerate elements.
        """
        return geomtools.degenerate(*self.areaNormals())


    def removeDegenerate(self, compact=False):
        """Remove the degenerate elements from a TriSurface.

        Parameters
        ----------
        compact: bool, optional
            If True, the TriSurface is compacted after removing the
            degenerate elements.

        Returns
        -------
        TriSurface
            A TriSurface with all the degenerate elements removed.
            By default, the coords attribute is unaltered and will still contain
            all points, even ones that are no longer connected to any element.
            If ``compact=True``, unused nodes are removed.
        """
        return self.cselect(self.degenerate(), compact=compact)


    def collapseEdge(self, edg):
        """Collapse an edge in a TriSurface.

        Collapsing an edge removes the triangles connected to the edge
        and replaces the two vertices of the edge with a single one,
        placed at the center of the edge.
        Triangles connected to one of the edge vertices, will
        become connected to the new vertex.

        Parameters
        ----------
        edg: int
            The index of the edg to be removed. This is an index in the
            :attr:`edges` array.

        Returns
        -------
        TriSurface
            An almost equivalent surface with the specified edge removed.
        """
        # remove the elements connected to the collapsing edge
        invee = self.elem_edges.inverse(expand=True)
        els = invee[edg]
        els = els[els>=0]
        keep = at.complement(els, n=self.nelems())
        elems = self.elems[keep]
        prop = self.prop
        if prop is not None:
            prop = prop[keep]
        # replace the first node with the mean of the two
        # TODO: If one vertex is on the border and the other is not,
        # use the border vertex coordinates instead of the mean
        node0, node1 = self.edges[edg]
        elems[elems==node1] = node0
        coords = self.coords.copy()
        coords[node0] = 0.5 * (coords[node0] + coords[node1])
        return TriSurface(coords, elems, prop=prop).compact()


    ##############  Transform surface #############################
    # All transformations return a new surface


    def offset(self, distance=1.):
        """Offset a surface with a certain distance.

        Parameters
        ----------
        distance: float
            Distance over which the points should be moved.

        Returns
        -------
        TriSurface
            A TriSurface obtaine by moving all the nodes of the input surface
            over the specified distance in the direction of the averaged
            normal vector.
        """
        n = self.avgVertexNormals()
        coordsNew = self.coords + n*distance
        return TriSurface(coordsNew, self.elems, prop=self.prop)


    @utils.warning('warn_dualMesh')
    def dualMesh(self, method='median'):
        """Return the dual mesh of a compacted triangulated surface.

        Creates a new triangular mesh where all triangles with prop `p`
        represent the dual mesh region around the original surface node `p`.

        Parameters
        ----------
        method: 'median' | 'voronoi'

        Returns
        -------
        Mesh
            The dual Mesh. The elements have property numbers equal to
            the node number around which they are based.

        .. Note: This needs more explanation.
        """
        if self.ncoords()!=self.compact().ncoords():
            raise ValueError("Expected a compacted surface")
        Q = self.convert('quad4', fuse=False)
        if method == 'voronoi':
            from pyformex.geomtools import triangleCircumCircle
            Q.coords[-self.nelems():] = triangleCircumCircle(
                self.coords[self.elems], bounding=False)[1]
        nconn = Q.nodeConnections()[np.arange(self.ncoords())]
        p = np.zeros(Q.nelems(), dtype=int)
        for i, conn in enumerate(nconn):
            p[conn[conn>-1]]=i
        Q = Q.setProp(p)
        return Q


    ##################  Partitioning a surface  #############################


    def partitionByAngle(self, angle=60., sort='number'):
        """Partition the surface by splitting it at sharp edges.

        The surface is partitioned in parts in which all elements can be
        reached without ever crossing a sharp edge angle. More precisely,
        any two triangles will belong to the same part if the can be connected
        by a line in the surface that does not cross an edge between
        two elements having their normals differ more than the specified
        angle.

        Parameters
        ----------
        angle: float
            The minimum value of the angle (in degrees) between the normals on
            two adjacent triangles in order for the edge to be considered a
            sharp edge.
        sort: str
            Defines how the resulting parts are sorted (by assigning them
            increasing part numbers). The following sort criteria are currently
            defined (any other value will return the parts unsorted):

            - 'number': sort in decreasing order of the number of triangles
              in the part. This is the default.
            - 'area': sort according to decreasing surface area of the part.

        Returns
        -------
        int array
            An int array specifying for each triangle to which part it belongs.
            Values are in the range 0..nparts.

        Notes
        -----
        In order for the operation to be non-trivial, the specified edges,
        possibly together with (parts of) the border, should form one or
        more closed loops.

        Beware that the existence of degenerate elements may cause
        unexpected results. If unsure, use the :meth:`removeDegenerate`
        method first to remove those elements.
        """
        feat = self.featureEdges(angle=angle)
        return self.partitionByCurve(feat, sort)


    # This may replace CutWithPlane after it has been proved stable
    # and has been expanded to multiple planes
    def cutWithPlane1(self, p, n, side='', return_intersection=False, atol=0.):
        """Cut a surface with a plane.

        Cut the surface with a plane defined by a point p and normal n.


        .. warning:: This is experimental and may not work correctly.

        Parameters
        ----------
        p: float :term:`array_like` (3,)
            A point in the cutting plane.
        n: float :term:`array_like` (3,)
            The normal vector to the cutting plane.
        side: '' | '+' | '-'
            Selects the returned parts. Default ('') is to return a tuple
            of two surfaces, with the parts at the positive,
            resp. negative side of the plane, as defined by the normal vector.
            If a '+' or '-' is specified, only the corresponding part
            is returned.

        Returns
        -------
        Spos: TriSurface, optional
            The part of the surfacec at the positive side of thr plane (p,n).
            Only returned if side is '' or  '+'.
        Sneg: TriSurface, optional
            The part of the surfacec at the negative side of thr plane (p,n).
            Only returned if side is '' or  '-'.

        The returned surfaces have their normals fixed wherever possible.
        Prop values are set containing the triangle number in the
        original surface from which the elements resulted.
        """
        def finalize(Sp, Sn, I):
            # Result
            res = []
            if side in '+':
                Sp = Sp.compact()
                res.append(Sp)
            if side in '-':
                Sn = Sn.compact()
                res.append(Sn)
            if return_intersection:
                res.append(I)
            if len(res) == 1:
                res = res[0]
            else:
                res = tuple(res)
            return res

        from pyformex.formex import _sane_side, _select_side
        side = _sane_side(side)

        p = at.checkArray(p, size=3, kind='f', allow='i').reshape(3)
        n = at.checkArray(n, size=3, kind='f', allow='i').reshape(3)

        # Make sure we inherit element number
        save_prop = self.prop
        self.prop = np.arange(self.elems.shape[0])

        # Compute distance to plane of all vertices
        d = self.distanceFromPlane(p, n)

        p_pos = d > 0.
        p_neg = d < 0.
        p_in = ~(p_pos+p_neg)
        p_posin = p_pos + p_in
        p_negin = p_neg + p_in

        # Reduce the surface to the part intersecting with the plane:
        # Remember triangles with all vertices at same side
        # Elements completely in the plane end up in both parts.
        # BV: SHOULD WE CHANGE THIS???
        # TODO: put them only in negative?, as the volume is at the
        # negative side of the elements.
        all_p = p_posin[self.elems].all(axis=-1)
        all_n = p_negin[self.elems].all(axis=-1)
        S = self.cselect(all_p+all_n)
        Sp = self.select(all_p)
        Sn = self.select(all_n)
        # Restore properties
        self.prop = save_prop

        # If there is no intersection, we're done
        # (we might have cut right along facet edges!)
        if S.nelems() == 0:
            res = _select_side(side, [Sp, Sn])
            return res

        #######################
        # Cut S with the plane.
        #######################
        # First define facets in terms of edges
        coords = S.coords
        edg = S.edges
        fac = S.elem_edges
        ele = S.elems

        # Get the edges intersecting with the plane: 1 up and 1 down vertex
        d_edg = d[edg]
        edg_1_up = (d_edg > 0.).sum(axis=1) == 1
        edg_1_do = (d_edg < 0.).sum(axis=1) == 1
        cutedg = edg_1_up * edg_1_do
        ind = np.where(cutedg)[0]
        if ind.size == 0:
            raise ValueError("This really should not happen!")

        # Compute the intersection points
        M = Mesh(S.coords, edg[cutedg])
        x = geomtools.intersectSegmentWithPlane(
            M.toFormex().coords, p, n, mode='pair', atol=atol)
        # Create inverse index to lookup the point using the edge number
        rev = at.inverseUniqueIndex(ind) + coords.shape[0]
        # Concatenate the coords arrays
        coords = coords.concatenate([coords, x])

        # For each triangle, compute the number of cutting edges
        cut = cutedg[fac]
        ncut = cut.sum(axis=1)

        if (ncut < 1).any() or (ncut > 2).any():
            # Maybe we should issue a warning and ignore these cases?
            print("NCUT: ", ncut)
            raise ValueError(
                "I expected all triangles to be cut along 1 or 2 edges. "
                "I do not know how to proceed now.")

        if return_intersection:
            IS = Mesh(eltype='line2')

        # Process the elements cutting one edge
        #######################################
        ncut1 = ncut==1
        if ncut1.any():
            prop1 = np.where(ncut1)[0]
            fac1 = fac[ncut1]
            ele1 = ele[ncut1]
            cutedg1 = cutedg[fac1]
            cut_edges = fac1[cutedg1]

            # Identify the node numbers
            # 0 : vertex on positive side
            # 1 : vertex in plane
            # 2 : new point dividing edge
            # 3 : vertex on negative side
            elems = np.column_stack([
                ele1[p_pos[ele1]],
                ele1[p_in[ele1]],
                rev[cut_edges],
                ele1[p_neg[ele1]],
            ])

            if side in '+':
                Sp += TriSurface(coords, elems[:, 0:3], prop=prop1)
            if side in '-':
                Sn += TriSurface(coords, elems[:, 1:4], prop=prop1)

        # Process the elements cutting two edges
        ########################################
        print("Cutting 2 edges")
        ncut2 = ncut==2     # selector over whole range
        print(ncut)
        print(ncut2)
        print(p_pos.sum(axis=-1)==2)
        if ncut2.any():
            prop2 = np.where(ncut2)[0]
            fac2 = fac[ncut2]
            ele2 = ele[ncut2]
            pp2 = p_pos[ele2]
            print("ele", ele2, pp2)
            ncut2p = pp2.sum(axis=-1)==1   # selector over ncut2 elems
            ncut2n = pp2.sum(axis=-1)==2
            print(ncut2p, ncut2n)

            if ncut2p.any():
                prop1 = prop2[ncut2p]
                fac1 = fac2[ncut2p]
                ele1 = ele2[ncut2p]

                print("ele1,1p", ele1)
                cutedg1 = cutedg[fac1]
                print(cutedg, fac1, cutedg1, fac1[cutedg1])
                cut_edges = fac1[cutedg1].reshape(-1, 2)

                corner = ele1[p_pos[ele1]]
                quad = edg[cut_edges].reshape(-1, 4)
                quad2 = quad[quad != corner.reshape(-1, 1)]
                # Identify the node numbers
                # 0   : vertex on positive side
                # 1,2 : new points dividing edges
                # 3,4 : vertices on negative side
                elems = np.column_stack([
                    ele1[p_pos[ele1]],
                    rev[cut_edges],
                    quad2.reshape(-1, 2)
                    # ele1[p_neg[ele1]].reshape(-1,2),
                ])

                if side in '+':
                    Sp += TriSurface(coords, elems[:, 0:3], prop=prop1)
                if side in '-':
                    Sn += TriSurface(coords, elems[:, 1:4], prop=prop1)
                    Sn += TriSurface(coords, elems[:, 2:5], prop=prop1)

            if ncut2n.any():
                # print "# one vertex at negative side"
                prop1 = np.where(ncut2n)[0]
                fac1 = fac[ncut2n]
                ele1 = ele[ncut2n]

                cutedg1 = cutedg[fac1]
                cut_edges = fac1[cutedg1].reshape(-1, 2)
                # print cut_edges

                corner = ele1[p_neg[ele1]]
                # print corner
                quad = edg[cut_edges].reshape(-1, 4)
                # print quad
                # print quad != corner.reshape(-1,1)
                quad2 = quad[quad != corner.reshape(-1, 1)]
                # print quad2

                # 0   : vertex on negative side
                # 1,2 : new points dividing edges
                # 3,4 : vertices on positive side
                elems = np.column_stack([
                    quad2.reshape(-1, 2),
                    # we can not use this, because order of the 2 vertices
                    # is importtant
                    # ele1[p_pos[ele1]].reshape(-1,2),
                    rev[cut_edges],
                    ele1[p_neg[ele1]],
                ])
                # print elems

                if side in '+':
                    Sp += TriSurface(coords, elems[:, 0:3], prop=prop1)
                    Sp += TriSurface(coords, elems[:, 1:4], prop=prop1)
                if side in '-':
                    Sn += TriSurface(coords, elems[:, 2:5], prop=prop1)

        return finalize(Sp, Sn, IS)
        # Result
        if side in '+':
            Sp = Sp.compact()
        if side in '-':
            Sn = Sn.compact()
        return _select_side(side, [Sp, Sn])


    def cutWithPlane(self, *args, **kargs):
        """Cut a surface with a plane or a set of planes.

        Cut the surface with one or more planes and return either one side
        or both. This uses a conversion to a 3-plex Formex to do the
        cutting, and then converts the results back to TriSurface(s).
        The parameters are the same as in :meth:`Formex.CutWithPlane`.
        The returned surface(s) will have the normals fixed wherever possible.
        """
        S = self.toFormex().cutWithPlane(*args, **kargs)
        return S.toSurface().fixNormals('internal')


    def intersectionWithLines(self, p, p1, method='line', atol=1.e-5):
        """Compute the intersection points with a set of lines.

        Parameters
        ----------
        p: :term:`coords_like` (nlines,3)
            A first point for each of the lines to intersect.
        p1 :term:`coords_like` (nlines,3)
            The second point defining the lines to intersect.
        method: 'line' | 'segment' | ' ray'
            Define whether the points ``p`` and ``p1`` define an infinitely
            long line, a finite segment p-p1 or a half infinite ray (p->p1).
        atol : float
            Tolerance to be used in deciding whether an intersection point on
            a border edge is inside the surface or not.

        Returns
        -------
        X: Coords (nipts, 3)
            A fused set of intersection points
        ind: int array (nipts, 3)
            An array identifying the related intersection points, lines and
            triangle.

        Notes
        -----
        A line laying in the plane of a triangle does not generate
        intersections.

        This method is faster than the similar function
        :func:`geomtools.intersectionPointsLWT`.

        Examples
        -------
        >>> T = Formex('3:.12.34').toSurface()
        >>> L = Coords([[[0.,0.,0.], [0.,0.,1.]],
        ...             [[0.5,0.5,0.5], [0.5,0.5,1.]],
        ...             [[0.2,0.7,0.0], [0.2,0.7,1.]],
        ...             ])
        >>> P,X = T.intersectionWithLines(L[:,0,:], L[:,1,:])
        >>> print(P)
        [[0.  0.  0. ]
         [0.5 0.5 0. ]
         [0.2 0.7 0. ]]
        >>> print(X)
        [[0 0 0]
         [0 0 1]
         [1 1 0]
         [1 1 1]
         [2 2 1]]
        """
        return geomtools.intersectLineWithTriangle(
            self.coords[self.elems], p, p1, method=method, atol=atol)


    def intersectionWithPlane(self, p, n, atol=1.e-5, sort='number'):
        """Return the intersection lines with plane (p,n).

        Parameters
        ----------
        p: :term:`coords_like` (3,)
            A point in the cutting plane.
        n: :term:`coords_like` (3,)
            The positive normal on the plane
        atol: float
            Tolerance value to consider points lying in the plane. A small
            positive value is recommended in order to include triangle edges
            that happen to fall exactly in the cutting plane.
        sort: 'number' | 'distance'
            The sorting method for the connected components in the output Mesh.
            The default 'number' sorts in decreasing number of elements in the
            component. Setting to 'distance' will sort the parts according to
            increasing distance from the point p.

        Returns
        -------
        :Mesh
            The intersection of the TriSurface with the plane. This is a Mesh
            of eltype 'line'. The line segments in the Mesh are ordered in a
            way to form continuous lines. The Mesh has property numbers such
            that all segments forming a single continuous part have the same
            property value. The parts are assigned property numbers
            according to their sort order.

        Notes
        -----
        The splitProp() method can be used to get a list of separate Meshes.
        """
        n = np.asarray(n)
        p = np.asarray(p)
        # First reduce the surface to the part cutting the plane
        tp, tc, tn = self.testPlane(p, n, atol=-atol)
        S = self.select(tc)
        # If there is no intersection, we're done
        if S.nelems() == 0:
            return Mesh(Coords(), Connectivity(nplex=2, eltype='line2'))

        Mparts = []
        coords = S.coords
        edg = S.edges
        fac = S.elem_edges
        ele = S.elems
        d = coords.distanceFromPlane(p, n)
        d_edg = d[edg]
        edg_1_up = (d_edg > 0.).sum(axis=1) == 1
        edg_1_do = (d_edg < 0.).sum(axis=1) == 1
        w = edg_1_up * edg_1_do
        ind = np.where(w)[0]

        # compute the intersection points
        if ind.size != 0:
            rev = at.inverseUniqueIndex(ind)
            M = Mesh(S.coords, edg[w])
            x = geomtools.intersectSegmentWithPlane(
                M.toFormex().coords, p, n, mode='pair', atol=atol, returns='x')

        # For each triangle, compute the number of cutting edges
        cut = w[fac]
        ncut = cut.sum(axis=1)

        # Split the triangles based on the number of inside vertices
        d_ele = d[ele]
        ins = d_ele == 0.
        nins = ins.sum(axis=1)
        ins0, ins1, ins2, ins3 = [np.where(nins==i)[0] for i in range(4)]

        # No inside vertices -> 2 cutting edges
        if ins0.size > 0:
            cutedg = fac[ins0][cut[ins0]].reshape(-1, 2)
            e0 = rev[cutedg]
            Mparts.append(Mesh(x, e0, eltype='line2').compact())

        # One inside vertex
        if ins1.size > 0:
            ncut1 = ncut[ins1]
            cut10, cut11 = [np.where(ncut1==i)[0] for i in range(2)]
            # 0 cutting edges: does not generate a line segment
            # 1 cutting edge
            if cut11.size != 0:
                e11ins = ele[ins1][cut11][ins[ins1][cut11]].reshape(-1, 1)
                cutedg = fac[ins1][cut11][cut[ins1][cut11]].reshape(-1, 1)
                e11cut = rev[cutedg]
                x11 = Coords.concatenate([coords, x], axis=0)
                e11 = np.concatenate([e11ins, e11cut+len(coords)], axis=1)
                Mparts.append(Mesh(x11, e11, eltype='line2').compact())

        # Two inside vertices -> 0 cutting edges
        if ins2.size > 0:
            e2 = ele[ins2][ins[ins2]].reshape(-1, 2)
            Mparts.append(Mesh(coords, e2, eltype='line2').compact())

        # Three inside vertices -> 0 cutting edges
        if ins3.size > 0:
            insedg = fac[ins3].reshape(-1)
            insedg.sort(axis=0)
            double = insedg == np.roll(insedg, 1, axis=0)
            insedg = np.setdiff1d(insedg, insedg[double])
            if insedg.size != 0:
                e3 = edg[insedg]
                Mparts.append(Mesh(coords, e3, eltype='line2').compact())

        # Done with getting the segments
        if len(Mparts) == 0:
            # No intersection: return empty mesh
            return Mesh(Coords(), Connectivity(nplex=2, eltype='line2'))
        else:
            M = Mesh.concatenate(Mparts)

            # Remove degenerate and duplicate elements
            M = Mesh(M.coords, M.elems.removeDegenerate().removeDuplicate())

            # Split in connected loops
            parts = M.elems.chained()
            prop = np.concatenate([[i]*part.nelems()
                                   for i, part in enumerate(parts)])
            elems = np.concatenate(parts, axis=0)
            if sort == 'distance':
                d = np.array([M.coords[part].distanceFromPoint(p).min()
                              for part in parts])
                srt = np.argsort(d)
                inv = at.inverseUniqueIndex(srt)
                prop = inv[prop]
            return Mesh(M.coords, elems, prop=prop)


    def slice(self, dir=0, nplanes=20):
        """Intersect a surface with a series of parallel planes.

        Parameters
        ----------
        dir: int | :term:`array_like` (3,)
            The direction of the normal on the planes. A single
            int (0..2) may be used to specify one of the global axes.
        nplanes: int
            The number of planes to be used. The planes are spread at
            equal distances over the bbox of the surface.

        Returns
        -------
        : list of :class:`~mesh.Mesh`
           A list of `nplanes` Meshes of type 'line2', being the
           intersections of the surface with each of the planes.

        Notes
        -----
        The intersections are obtained with :meth:`intersectionWithPlane`.
        See there for more dretails on the returned Meshes.
        """
        o = self.center()
        if at.isInt(dir):
            dir = at.unitVector(dir)
        xmin, xmax = self.coords.directionalExtremes(dir, o)
        P = Coords.interpolate(xmin, xmax, nplanes)
        return [self.intersectionWithPlane(p, dir) for p in P]


    def refine(self, max_edges=None, min_cost=None, method='gts', log=False):
        """Refine a TriSurface.

        Refining a TriSurface means increasing the number of triangles and
        reducing their size, while keeping the changes to the modeled surface
        minimal.
        Construct a refined version of the surface.
        This uses the external program `gtsrefine`. The surface
        should be a closed orientable non-intersecting manifold.
        Use the :meth:`check` method to find out.

        Parameters:

        - `max_edges`: int: stop the refining process if the number of
          edges exceeds this value
        - `min_cost`: float: stop the refining process if the cost of refining
          an edge is smaller
        - `log`: boolean: log the evolution of the cost
        - `verbose`: boolean: print statistics about the surface
        """
        if method == 'gts':
            return self.gts_refine(max_edges, min_cost, log)

        # THIS IS WORK IN PROGRESS
        edglen = at.length(self.coords[self.edges[:, 1]]
                           - self.coords[self.edges[:, 0]])
        print(edglen)
        return self


    def similarity(self, S):
        """Compute the similarity with another TriSurface.

        Compute a quantitative measure of the similarity of the volumes
        enclosed by two TriSurfaces. Both the calling and the passed
        TriSurface should be closed manifolds (see :meth:`isClosedManifold`).

        Returns a tuple (jaccard, dice, overlap).
        If A and B are two closed manifolds, VA and VB are their respective
        volumes, VC is the volume of the intersection of A and B, and VD is
        the volume of the union of A and B, then the following similarity
        measures are defined:

        - jaccard coefficient: VC / VD
        - dice: 2 * VC / (VA + VB)
        - overlap: VC / min(VA,VB)

        Both jaccard and dice range from 0 when the surfaces are completely
        disjoint to 1 when the surfaces are identical. The overlap coefficient
        becomes 1 when one of the surfaces is completely inside the other.

        This method uses gts library to compute the intersection or union.
        If that fails, nan values are returned.
        """
        A, B = self, S
        VA = A.volume()
        VB = B.volume()
        try:
            VC = A.boolean(B, '*').volume()
            VD = VA + VB - VC
        except Exception:
            try:
                VD = A.boolean(B, '+').volume()
                VC = VA + VB - VD
            except Exception:
                VC = VD = np.nan

        dice = 2 * VC / (VA+VB)
        overlap = VC / min([VA, VB])
        jaccard = VC / VD
        return jaccard, dice, overlap


    def fixNormals(self, method=None, *, outwards=True, return_parts=False,
                   inplace=True):
        """Fix the orientation of the normals.

        Some surface operations may result in improperly oriented normals,
        switching directions from one triangle to the adjacent one.
        This method tries to reverse triangles with improperly oriented
        normals so that a singly oriented surface may be achieved.

        Parameters
        ----------
        method: 'admesh' | 'internal'
            The method to be used. If not specified, the default 'internal'
            is used and a warning is shown about the changed default.
            The 'internal' method does not rely on external software, and is
            relatively fast. As it does not fuse the nodes nor compacts the
            node array, it guarantees that the numbering of nodes and elements
            is retained.
            The 'admesh' uses an external program and needs to write the
            surface to a file and read it back. This method will always
            do a fuse and compaction, so if the surface was not fused and
            compacted before the call, the result may have different node
            and/or element numberings.
        outwards: bool
            If True (default), a test is done whether the surface is a closed
            manifold, or a set of closed manifolds, and if so, the normals are
            oriented outwards. Setting this value to False may result in a
            closed surfaces with all normals pointing inside.
        return_parts: bool
            If True, also returns an index identifying to which connected part
            each of the triangles belong. Part numbers are in order of
            decreasing number of triangles.

        Raises
        ------
        ValueError: if the surface is not a manifold. Such a surface is not
            orientable.
        """
        if self.nelems() == 0:
            # Allow for empty surfaces
            if return_parts:
                return self, []
            else:
                return self
        stype = self.surfaceType()
        if not stype[0]:
            raise ValueError("The surface is not a manifold")
        if method is None:
            utils.warn("fixnormals_default", uplevel=1)
            method = 'internal'
        if method == 'admesh':
            S = self.fixNormals_admesh()
            parts = None
        elif method == 'internal':
            S, parts = self.fixNormals_internal()
        if (outwards or return_parts) and (parts is None):
            parts = S.partitionByConnection()
        if outwards and stype[0] and stype[2]:
            parts = at.sortSubsets(parts)
            for p in np.unique(parts):
                w = parts==p
                Si = S.select(w)
                if Si.volume() < 0.:
                    S = S.reverse(w, inplace=inplace)
        if return_parts:
            return S, parts
        else:
            return S

    def fixNormals_internal(self):
        """Fix normals using an internal algorithm.

        This is normally invoked as ``fixNormals('internal')``.
        See :meth:`fixNormals`.
        """
        # define elems in function of edges
        hi = self.elem_edges
        # find amboriented edges
        ambo = self.amborientedEdges()
        if len(ambo) == 0:
            # everything is ok
            return self, None
        # Do a walk over edge connections, splitting in parts
        # at ambo edges (and border edges)
        inv = hi.inverse(expand=True)
        adj = hi.adjacency(exclude=ambo)
        p = adj.frontWalk(frontinc=0, partinc=1)
        S = self
        # Remember which parts have been fixed
        parts = []

        def start_part():
            # find the largest remaining part
            unique, counts = np.unique(p, return_counts=True)
            if len(unique) == len(parts):
                # No more parts to do
                return S
            if len(parts) > 0:
                # remove the already handled parts
                w = unique.searchsorted(parts)
                counts[w] = 0
            # take the largest remaining
            return unique[np.argmax(counts)]

        largest = start_part()
        do_reverse = True
        while len(ambo) > 0:
            # find the edges to be fixed in the largest
            amboedges = np.intersect1d(ambo, hi[p==largest])
            if len(amboedges) == 0:
                # nothing anymore to fix in this part
                # register it, and start a new part
                parts.append(largest)
                largest = start_part()
                do_reverse = True
                continue
            neighbors = inv[amboedges]
            nbrs = neighbors[p[neighbors] != largest]
            nbrps = np.unique(p[nbrs])
            # Revert neighbor parts and make same part as largest
            rev = np.full(p.shape, False, dtype=bool)
            for pi in nbrps:
                ok = p==pi
                p[ok] = largest
                rev ^= ok
            if do_reverse:
                S = S.reverse(rev)
            # and remove the amboedges from ambo
            ambo = np.setdiff1d(ambo, amboedges)
            if len(ambo) == 0:
                break
            do_reverse = not do_reverse
        return S, p


    ###################################################################
    ##    Methods using admesh/GTS
    ##############################


    def fixNormals_admesh(self):
        """Fix normals using admesh.

        This is normally invoked as ``fixNormals('admesh')``.
        See :meth:`fixNormals`.
        """
        with utils.TempDir() as tmpdir:
            tmp = tmpdir / 'surface.stl'
            tmp1 = tmpdir / 'surface.off'
            pf.verbose(2, f"Writing temp file {tmp}")
            self.write(tmp, 'stl')
            pf.verbose(2, f"Fixing surface by converting to OFF format {tmp1}")
            fileread.stlConvert(tmp, tmp1)
            pf.verbose(2, f"Reading result from {tmp1}")
            S = TriSurface.read(tmp1)
        S.setProp(self.prop)
        return S


    def check(self, matched=True, verbose=False):
        """Check the surface using gtscheck.

        Uses the external program `gtscheck` to check whether the surface
        is an orientable, non self-intersecting manifold.
        This is a necessary condition for using the `gts` methods:
        split, coarsen, refine, boolean. Additionally, the surface should be
        closed: this can be checked with :meth:`isClosedManifold`.

        Parameters
        ----------
        matched: bool
            If True, self intersecting triangles are returned as element
            indices of self. This is the default. If False, the self
            intersecting triangles are returned as a separate TriSurface.
        verbose: bool
            If True, prints the statistics reported by the gtscheck
            command.

        Returns
        -------
        status: int
            Return code from the checking program. One of the following:

            - 0: the surface is an orientable, non self-intersecting manifold.
            - 1: the created GTS file is invalid: this should normally not occur.
            - 2: the surface is not an orientable manifold. This may be due to
              misoriented normals. The :meth:`fixNormals` and :meth:`reverse`
              methods may be used to help fixing the problem in such case.
            - 3: the surface is an orientable manifold but is
              self-intersecting. The self intersecting triangles are returned as
              the second return value.

        intersect: None | list of ints | TriSurface
            None in case of a ``status`` 0, 1 or 2. For ``status`` value 3,
            returns the self intersecting triangles as a list of element
            numbers (if ``matched`` is True) or as a TriSurface (if ``matched``
            is False).

        """
        with utils.TempDir() as tmpdir:
            tmp = tmpdir / 'surface.gts'
            self.write(tmp, 'gts')
            P = utils.system("gtscheck -v", stdin=tmp)
            if verbose:
                print(P.returncode)
            if P.returncode == 0:
                print("The surface is an orientable "
                      "non self-intersecting manifold")
                res = None
            elif P.returncode==2:
                print("The surface is not an orientable manifold "
                      "(this may be due to badly oriented normals)")
                res = None
            elif P.returncode==3:
                print("The surface is an orientable manifold "
                      "but is self-intersecting")
                tmp = tmpdir / 'intersect.gts'
                print(f"Writing temp file {tmp}")
                with open(tmp, 'w') as fil:
                    fil.write(P.stdout)
                res = TriSurface.read(tmp)
                if matched:
                    res = self.matchCentroids(res)
            else:
                print("Status of gtscheck not understood")
                res = None
            return P.returncode, res


    def split(self, base, verbose=False):
        """Split the surface using gtssplit.

        Splits the surface into connected and manifold components.
        This uses the external program `gtssplit`. The surface
        should be a closed orientable non-intersecting manifold.
        Use the :meth:`check` method to find out.

        This method creates a series of files with given base name,
        each file contains a single connected manifold.
        """
        with utils.TempDir() as tmpdir:
            tmp = tmpdir / 'surface.gts'
            print(f"Writing surface to file {tmp}")
            self.write(tmp, 'gts')
            cmd = f"gtssplit -v {base}"
            if verbose:
                cmd += ' -v'
            print(f"Splitting with command\n {cmd}")
            P = utils.command(cmd, stdin=tmp, shell=True)
            if P.returncode or verbose:
                print(P.stdout)
            #
            # TODO: WE SHOULD READ THESE FILES BACK !!!
            #


    def coarsen(self, min_edges=None, max_cost=None,
                mid_vertex=False, length_cost=False, max_fold=1.0,
                volume_weight=0.5, boundary_weight=0.5, shape_weight=0.0,
                progressive=False, log=False, verbose=False):
        """Coarsen a surface using gtscoarsen.

        Construct a coarsened version of the surface.
        This uses the external program `gtscoarsen`. The surface
        should be a closed orientable non-intersecting manifold.
        Use the :meth:`check` method to find out.

        Parameters
        ----------
        min_edges: int
            Stop the coarsening process if the number of edges was to fall
            below it.
        max_cost: float
            Stop the coarsening process if the cost of collapsing an edge is
            larger than the specified value.
        mid_vertex: bool
            Use midvertex as replacement vertex instead of the default, which
            is a volume optimized point.
        length_cost: bool
            Use length^2 as cost function instead of the default optimized
            point cost.
        max_fold: float
             Maximum fold angle in degrees.
        volume_weight: float
            Weight used for volume optimization.
        boundary_weight: float
            Weight used for boundary optimization.
        shape_weight: float
            Weight used for shape optimization.
        progressive: bool
            If True, write progressive surface file.
        log: bool
            If Trye, log the evolution of the cost.
        verbose: bool
            If True, print statistics about the surface.
        """
        if min_edges is None and max_cost is None:
            min_edges = self.nedges() // 2
        cmd = 'gtscoarsen'
        if min_edges:
            cmd += f" -n {min_edges}"
        if max_cost:
            cmd += f" -c {max_cost}"
        if mid_vertex:
            cmd += " -m"
        if length_cost:
            cmd += " -l"
        if max_fold:
            cmd += f" -f {max_fold}"
        cmd += f" -w {volume_weight}"
        cmd += f" -b {boundary_weight}"
        cmd += f" -s {shape_weight}"
        if progressive:
            cmd += " -p"
        if log:
            cmd += " -L"
        if verbose:
            cmd += " -v"
        with utils.TempDir() as tmpdir:
            tmp = tmpdir / "surface.gts"
            tmp1 = tmpdir / "surface1.gts"
            print(f"Writing temp file {tmp}")
            self.write(tmp, "gts")
            print(f"Coarsening with command\n {cmd}")
            P = utils.command(cmd, stdin=tmp, stdout=tmp1)
            if P.returncode or verbose:
                print(P.stdout)
            print(f"Reading coarsened model from {tmp1}")
            S = TriSurface.read(tmp1)
            return S


    def gts_refine(self, max_edges=None, min_cost=None, log=False, verbose=False):
        """Refine the TriSurface.

        Refining a TriSurface means increasing the number of triangles and
        reducing their size, while keeping the changes to the modeled surface
        minimal.
        This uses the external program `gtsrefine`. The surface
        should be a closed orientable non-intersecting manifold.
        Use the :meth:`check` method to find out.

        Parameters
        ----------
        max_edges: int
            Stop the refining process if the number of edges exceeds this value.
        min_cost: float
            Stop the refining process if the cost of refining an edge is smaller.
            (Not recommended).
        log: bool
            If True, log the evolution of the cost.
        verbose: bool
            If True, print statistics about the surface.

        Notes
        -----
        If neither max_edges nor min_cost are specified, the refining process
        aims to double the number of edges.
        """
        if max_edges is None and min_cost is None:
            max_edges = self.nedges() * 2
        cmd = "gtsrefine"
        if max_edges:
            cmd += f" -n {max_edges}"
        if min_cost:
            cmd += f" -c {min_cost}"
        # TODO: DANGEROUS OPTION: the program gets into an infinite loop!
        # if log:
        #     cmd += " -L"
        if verbose:
            cmd += " -v"
        with utils.TempDir() as tmpdir:
            tmp = tmpdir / "surface.gts"
            tmp1 = tmpdir / "surface1.gts"
            print(f"Writing temp file {tmp}")
            self.write(tmp, "gts")
            print(f"Refining with command\n {cmd}")
            P = utils.command(cmd, stdin=tmp, stdout=tmp1)
            if P.returncode or verbose:
                print(P.stdout)
            print(f"Reading refined model from {tmp1}")
            S = TriSurface.read(tmp1)
            return S


    def gts_smooth(self, niter=1, lamb=0.5, verbose=False):
        """Smooth the surface using gtssmooth.

        Smooth a surface by applying iterations of a Laplacian filter.
        This uses the external program `gtssmooth`. The surface
        should be a closed orientable non-intersecting manifold.
        Use the :meth:`check` method to find out.

        Parameters
        ----------
        lamb: float
            Laplacian filter parameter.
        niter: int
            Number of iterations.
        verbose: bool
            If True, print statistics about the surface.

        """
        cmd = "gtssmooth"
        # if fold_smoothing:
        #     cmd += f" -f {fold_smoothing}"
        cmd += f" {lamb} {niter}"
        if verbose:
            cmd += " -v"
        with utils.TempDir() as tmpdir:
            tmp = tmpdir / "surface.gts"
            tmp1 = tmpdir / "surface1.gts"
            print(f"Writing temp file {tmp}")
            self.write(tmp, "gts")
            print(f"Smoothing with command\n {cmd}")
            P = utils.command(cmd, stdin=tmp, stdout=tmp1)
            if P.returncode or verbose:
                print(P.stdout)
            print(f"Reading smoothed model from {tmp1}")
            S = TriSurface.read(tmp1)
            return S


    def gts_set(self, surf, op, prop=[1, 1, 2, 2], check=False, verbose=False):
        """Perform a boolean operation with another surface.

        Boolean operations between surfaces are a basic operation in
        free surface modeling. Both surfaces should be closed orientable
        non-intersecting manifolds. Use the :meth:`check` method to find out.

        Following is a list of defined operations, where surface 1 relates to
        `self` and surface 2 to the `surf` argument. For simplicity, the
        operations are identified by a short string. All returned surfaces
        are manifolds. The first four are the basic parts: these may be closed
        or not. The following operations are constructed by combining some
        of the basic results. These are mathematical set operation on the
        volumes inside the surfaces, and always result in closed surfaces.

        ========= =========================================== ==========================
        Operation Result                                      Computed from
        ========= =========================================== ==========================
        ``i``     the part of surface 1 inside surface 2
        ``o``     the part of surface 1 outside surface 2
        ``2i``    the part of surface 2 inside surface 1
        ``2o``    the part of surface 2 outside surface 1
        --------- ------------------------------------------- --------------------------
        ``+``     the union of surfaces 1 and 2               ``o`` plus ``2o``
        ``*``     the intersection of surfaces 1 and 2        ``i`` plus ``2i``
        ``-``     the difference of surface 1 minus surface 2 ``o`` plus reversed ``2i``
        ``2-``    the difference of surface 2 minus surface 1 ``i`` plus reversed ``2o``
        ``^``     the symmetric difference of the surfaces    ``+`` plus reversed ``*``
        ========= =========================================== ==========================

        Parameters
        ----------
        surf: TriSurface
            Another TriSurface that is a closed manifold surface.
        op: str or list of str
            The operation(s) to perform: one of the operations specified
            above, or a list of such operations. A special value ``a`` will
            return the full list of 9 surfaces in the above order.
        prop: list of int
            A list of 4 integer values that will be set as props on the
            four base surfaces, to facilitate identification of the parts
            of the result(s). The default value will give prop values 1 or
            2 depending on the original surface the parts belonged to.
            Specifying None or an empty list will return surfaces without
            props.
        check: bool
            If True, a check is done that the surfaces are not self-intersecting;
            if one of them is, the set of self-intersecting faces is written
            (as a GtsSurface) on standard output
        verbose: bool
             If True, print statistics about the surface.

        Returns
        -------
        :class:`TriSurface` or list thereof
            A single manifold surface, or a list of such surfaces, corresponding
            to the specified oppetaion(s). The base operation may not be closed.
            The set operations always are closed.

        Note
        ----
        This method uses the external command 'gtsset' and will not run if
        it is not installed (available from pyformex/extras).
        """
        from pyformex.plugins.gts_itf import gtsset
        base = gtsset(self, surf, op='a', filt='', ext='.gts',
                      check=check, verbose=verbose)
        if not base:
            raise ValueError("Error computing the base surfaces.")
        # Function to compute the requested surface(s)
        if prop:
            base['s1in2'].setProp(prop[0])
            base['s1out2'].setProp(prop[1])
            base['s2in1'].setProp(prop[2])
            base['s2out1'].setProp(prop[3])

        def getres(o):
            if o == 'i':
                return base['s1in2']
            elif o == 'o':
                return base['s1out2']
            elif o == '2i':
                return base['s2in1']
            elif o == '2o':
                return base['s2out1']
            elif o == '+':
                return base['s1out2'] + base['s2out1']
            elif o == '*':
                return base['s1in2'] + base['s2in1']
            elif o == '-':
                return base['s1out2'] + base['s2in1'].reverse()
            elif o == '2-':
                return base['s2out1'] + base['s1in2'].reverse()
            elif o == '^':
                return (base['s1out2'] + base['s2out1']
                        + (base['s1in2'] + base['s2in1']).reverse())

        if op == 'a':
            op = ['i', 'o', '2i', '2o', '+', '*', '-', '2-', '^']

        if utils.isString(op):
            return getres(op)
        else:
            return [getres(o) for o in op]


    def boolean(self, surf, op, check=False, verbose=False):
        """Perform a boolean operation with another surface.

        Boolean operations between surfaces are a basic operation in
        free surface modeling. Both surfaces should be closed orientable
        non-intersecting manifolds.
        Use the :meth:`check` method to find out.

        The boolean operations are set operations on the enclosed volumes:
        union('+'), difference('-') or intersection('*').

        Parameters
        ----------
        surf: TriSurface
            Another TriSurface that is a closed manifold surface.
        op: '+', '-' or '*'
            The boolean operation to perform: union('+'), difference('-')
            or intersection('*').
        check: bool
            If True, a check is done that the surfaces are not self-intersecting;
            if one of them is, the set of self-intersecting faces is written
            (as a GtsSurface) on standard output
        verbose: bool
             If True, print statistics about the surface.

        Returns
        -------
        TriSurface
            A closed manifold TriSurface that is the volume union, difference or
            intersection of self with surf.

        Note
        ----
        This method uses the external command 'gtsset' and will not run if
        it is not installed (available from pyformex/extras).
        """
        from pyformex.plugins.gts_itf import gtsset
        return gtsset(self, surf, op, filt='', ext='.gts',
                      check=check, verbose=verbose).fuse().compact()


    def intersection(self, surf, check=False, verbose=False):
        """Return the intersection curve(s) of two surfaces.

        Boolean operations between surfaces are a basic operation in
        free surface modeling. Both surfaces should be closed orientable
        non-intersecting manifolds.
        Use the :meth:`check` method to find out.

        Parameters
        ----------
        surf: TriSurface
            A closed manifold surface.
        check: bool, optional
            If True, a check is made that the surfaces are not self-intersecting;
            if one of them is, the set of self-intersecting faces is written
            (as a GtsSurface) on standard output
        verbose: bool, optional
            If True, statistics about the surface are printed on stdout.

        Returns
        -------
        Mesh
            A Mesh with eltype Line2 holding all the line segments of the
            intersection curve(s).
        """
        from pyformex.plugins.gts_itf import gtsset
        return gtsset(self, surf, op='*', ext='.list', curve=True,
                      check=check, verbose=verbose)


    def inside(self, pts, method='gts', tol='auto', multi=True, keep=False):
        """Test which of the points pts are inside the surface.

        Parameters
        ----------
        pts: :term_`coords_like`
            The points to check agains the surface.
        method`: str
            Method to be used for the detection. Depending on
            the software you have installed the following are possible:

            - 'gts': provided by pyformex-extra (default)
            - 'vtk': provided by python-vtk (slower)

        tol: float
            Tolerance on equality of floating point values.
        multi: bool
            If True, uses multiprocessing to speed up the operation.
            Only used with method='gts'.
        keep: bool
            If True, the temporary directory with intermediate results is
            not erased. This may be useful for debugging purposes. Only
            used with method='gts'.

        Returns
        -------
        int array
            The indices of the points that are inside the surface.
            The indices refer to the onedimensional list
            of points as obtained from Coords(pts).points().

        """
        pts = Coords(pts).points()
        if method == 'gts':
            from pyformex.plugins import gts_itf
            return gts_itf.inside(self, pts, tol, multi=multi, keep=keep)
        elif method == 'vtk':
            from pyformex.plugins import vtk_itf
            return vtk_itf.inside(self, pts, tol)


    def outside(self, pts, **kargs):
        """Returns the points outside the surface.

        This is the complement of :meth:`inside`. See there for
        parameters and return value.
        """
        return at.complement(self.inside(pts, **kargs), len(pts))


    def voxelize(self, n, bbox=0.01, return_formex=False):
        """Voxelize the volume inside a closed surface.

        Parameters
        ----------
        n: int or (int, int, int)
            Resolution, i.e. number of voxel cells to use along the three axes.
            If a single int is specified, the number of cells will be adapted
            according to the surface's :meth:`sizes` (as the voxel cells are
            always cubes). The specified number of voxels will be used along the
            largest direction.
        bbox: float or (point,point)
            Defines the bounding box of the volume that needs to be voxelized.
            A float specifies a relative amount to add to the surface's bounding
            box. Note that this defines the bounding box of the centers of the
            voxels.
        return_formex: bool
            If True, also returns a Formex with the centers of the voxels.

        Returns
        -------
        voxels: int array (nz,ny,nx)
            The array has a value 1 for the voxels whose center is inside the
            surface, else 0.
        centers: Formex
            A plex-1 Formex with the centers of the voxels, and property values
            0 or 1 if the point is respectively outside or inside the surface.
            The voxel cell ordering in the Formex is z-direction first, then y,
            then x.

        Notes
        -----
        See also example Voxelize, for saving the voxel values in a stack
        of binary images.

        """
        if not self.isClosedManifold():
            raise ValueError("The surface is non a closed manifold")

        from pyformex import simple
        if at.isFloat(bbox):
            a, b = 1.0+bbox, bbox
            bbox = self.bbox()
            bbox = [a*bbox[0]-b*bbox[1], a*bbox[1]-b*bbox[0]]
        bbox = at.checkArray(bbox, shape=(2, 3), kind='f')
        if at.isInt(n):
            sz = bbox[1]-bbox[0]
            step = sz.max() / (n-1)
            n = np.ceil(sz / step).astype(at.Int)
        n = at.checkArray(n, shape=(3,), kind='i')
        X = simple.regularGrid(bbox[0], bbox[0]+n*step, n, swapaxes=True)
        ind = self.inside(X)
        vox = np.zeros(n+1, dtype=np.uint8)
        vox.ravel()[ind] = 1
        if return_formex:
            P = Formex(X.reshape(-1, 3))
            P.setProp(vox.ravel())
            return vox, P
        return vox


    def remesh(self, *, method='acvd', **kargs):
        """Create a quality remesh of the TriSurface.

        Remeshing a TriSurface means replacing the surface with a new mesh
        of triangles, which are more equally shaped, while trying to keep
        the represented surface as close as possible to the original.

        Parameters
        ----------
        method: str
            One of 'acvd' or 'instant'. The first character suffices.
            Depending on this value, one of the :meth:`remesh_acvd`,
            :meth:`remesh_instant` is called.

            The 'acvd' method is included with pyFormex and is normally
            always available on a successful install. The 'instant' method
            requires an external program 'instant-meshes'. The Help menu
            contains an option to install it.
        kargs:
            Keyword arguments to be passed to the specific method
            selected. See the specific method for explanation of the
            parameters.

        Returns
        -------
        TriSurface | Mesh | None
            In most cases a TriSurface is returned. The 'instant'
            method however allows remeshing to quads. In that cases a
            Mesh of eltype 'quad4' is returner. If the external conversion
            failed, None is returned.

        Raises
        ------
        ValueError:
            If the requested external remeshing program is not available.

        See Also
        --------
        :func:`lib.clust.remesh_acvd`: remesh using the ACVD technique
        remesh_instant: remesh using the external program 'instant-meshes'
        """
        print(f"Before remeshing: {self}")
        if method[:1] == 'a':
            from pyformex.lib.clust import remesh_acvd
            kargs = utils.selectDict(kargs, ['npoints', 'ndiv'])
            S = remesh_acvd(self, **kargs)
        elif method[:1] == 'i':
            kargs = utils.selectDict(kargs, [
                'infile', 'outfile', 'threads', 'deterministic', 'crease',
                'smooth', 'dominant', 'intrinsic', 'boundaries', 'posy',
                'rosy', 'scale', 'faces', 'vertices', 'nplex'])
            S = remesh_instant(self, **kargs)
        print(f"After remeshing: {S}")
        return S


    def tetgen(self, quality=2.0, volume=None, filename=None):
        """Create a tetrahedral mesh inside the surface.

        This uses :func:`~plugins.tetgen.tetMesh` to generate a quality
        tetrahedral mesh inside the surface. The surface should be a closed
        manifold.

        Parameters
        ----------
        quality: float
            The quality of the output tetrahedral mesh. The value is a
            constraint on the circumradius-to-shortest-edge ratio. The
            default (2.0) already provides a high quality mesh. Providing
            a larger value will reduce quality but increase speed. With
            quality=None, no quality constraint will be imposed.
        volume: float, optional
            If provided, applies a maximum tetrahedron volume constraint.
        filename: :term:`path_like`
            Specifies where the intermediate files will be stored.
            The default will use a temporary directory which will be destroyed
            after return. If the path of an existing directory is provided,
            the files will be stored in that directory with a name 'surface.off'
            for the original surface model and files 'surface.1.*' for the
            generated tetrahedral model (in tetgen format).
            If the path does not exist or is an existing file, the parent
            directory should exist and files are stored with the given
            file name as base. Existing files will be silently overwritten.

        Returns
        -------
        Mesh
            A tetrahedral Mesh (eltype='tet4') filling the input surface,
            provided the :func:`~plugins.tetgen.tetMesh` function finished
            successfully.

        """
        from pyformex.plugins import tetgen
        if filename is None:
            tmpdir = utils.TempDir()
            fn = Path(tmpdir.name) / 'surface.off'
        else:
            filename = Path(filename)
            if filename.exists() and filename.is_dir():
                fn = filename / 'surface.off'
            elif filename.parent.exists():
                fn = filename.with_suffix('.off')
            else:
                raise ValueError(f"Invalid filename specified: {filename}")
        self.write(fn, signature=False)
        res = tetgen.tetMesh(fn, quality, volume)
        return res['tetgen.ele']


    # Set TriSurface methods defined elsewhere
    from pyformex.plugins.webgl import surface2webgl
    webgl = surface2webgl


    @utils.deprecated_by('TriSurface.facetArea', 'TriSurface.areas')
    def facetArea(self):
        return self.areas()


    ###################
    ## PZF interface ##

    def pzf_dict(self):
        kargs = Geometry.pzf_dict(self)
        kargs['elems'] = self.elems
        return kargs

    pzf_args = ['coords', 'elems']

############################################################################


def fillBorder(border, method='radial', dir=None):
    """Create a triangulated surface inside a given closed polygonal line.

    Parameters
    ----------
    border: :class:`PolyLine`, :class:`Mesh` or :class:`Coords`
        A closed polygonal line that forms the border of the triangulated
        surface to be created. The polygon does not have to be planar.
        The line can be provided as one of the following:

        - a closed PolyLine,
        - a 2-plex Mesh, with a Connectivity table such that the elements
          in the specified order form a closed polyline,
        - a simple Coords holding the subsequent vertices of the polygonal
          border line.
    method: str
        Specifies the algorithm to be used to fill the polygon. Currently
        available are:

        - 'radial': this method adds a central point and connects all border
          segments with the center to create triangles.
        - 'border': this method creates subsequent triangles by connecting the
          endpoints of two consecutive border segments and thus works its way
          inwards until the hole is closed. Triangles are created at the line
          segments that form the smallest angle.
        - 'planar': this method projects the border on a plane, fills the
          border in 2D, then maps that back to the original border.
          The projection direction can be specified with ``dir``.

        See also Notes below.
    dir: (3,) :term:`array_like`, optional
        A vector specyfing the direction of the projection in the case of
        ``method='planar'``. If not provided, the best direction is
        automatically choosen.


    Returns
    -------
    TriSurface
        A TriSurface filling the hole inside the border.

    Notes
    -----
    The 'radial' method produces nice results if the border is relative smooth,
    nearly convex and nearly planar. It adds an extra point though, which may
    be unwanted. On irregular 3D borders there is a high change that the
    resulting TriSurface contains intersecting triangles.

    The 'border' method is slower on large borders, does not introduce any
    new point and has a better chance of avoiding intersecting triangles
    on irregular 3D borders.

    The 'planar' method gives very good results if the border curve is more
    or less planar.

    The resulting surface can be checked for intersecting triangles with the
    :meth:`check` method.
    """
    from pyformex.curve import PolyLine
    if isinstance(border, Mesh) and border.nplex()==2:
        if method == 'radial':
            border = border.compact()
        coords = border.coords
        elems = border.elems[:, 0]
    elif isinstance(border, PolyLine):
        coords = border.coords
        elems = None
    elif isinstance(border, Coords):
        coords = border.reshape(-1, 3)
        elems = None
    else:
        raise ValueError("Expected a 2-plex Mesh, "
                         "a PolyLine or a Coords array as first argument")

    if elems is None:
        elems = np.arange(coords.shape[0])

    n = elems.shape[0]
    if n < 3:
        raise ValueError("Expected at least 3 points.")

    if method == 'radial':
        coords = Coords.concatenate([coords, coords.center()])
        elems = np.column_stack([elems, np.roll(elems, -1),
                                 n*np.ones(elems.shape[0], dtype=at.Int)])

    elif method == 'border':
        # creating elems array at once (more efficient than appending)
        tri = -np.ones((n-2, 3), dtype=at.Int)
        # compute all internal angles
        x = coords[elems]
        e = np.arange(n)
        v = np.roll(x, -1, axis=0) - x
        v = at.normalize(v)
        c = at.vectorPairCosAngle(np.roll(v, 1, axis=0), v)
        # loop in order of smallest angles
        itri = 0
        while n > 3:
            # find minimal angle
            j = c.argmin()
            i = (j - 1) % n
            k = (j + 1) % n
            tri[itri] = [e[i], e[j], e[k]]
            # remove the point j of triangle i,j,k
            # recompute adjacent angles of edge i,k
            ii = (i-1) % n
            v1 = at.normalize([v[e[ii]], x[e[k]] - x[e[i]]])
            v2 = at.normalize([x[e[k]] - x[e[i]], v[e[k]]])
            cnew = at.vectorPairCosAngle(v1, v2)
            c = np.roll(np.concatenate([cnew, np.roll(c, 1-j)[3:]]), j-1)
            e = np.roll(np.roll(e, -j)[1:], j)
            n -= 1
            itri += 1
        tri[itri] = e
        elems = elems[tri]

    elif method == 'planar':
        from pyformex.plugins import polygon
        x = coords[elems]
        e = np.arange(x.shape[0])

        if dir is None:
            dir = geomtools.smallestDirection(x)

        X, C, A, a = polygon.projected(x, dir)
        P = polygon.Polygon(X)
        if P.area() < 0.0:
            P = P.reverse()
            e = at.reverseAxis(e, 0)
        S = P.fill()
        e = e[S.elems]
        elems = elems[e]

    else:
        raise ValueError("Strategy should be either 'radial', 'border' or 'planar'")

    return TriSurface(coords, elems)


def instant_meshes(infile, outfile=None, **kargs):
    """Remesh a tri3 mesh to a quality tri3 and/or quad4 mesh

    Uses the external 'Instant Meshes' program to remesh a tri3 mesh
    to a tri3 and/or quad4 mesh of the desired quality.

    Parameters
    ----------
    infile: :term:`path_like`
        An .obj file containing a pure tri3 mesh.
    outfile: :term:`path_like`
        The output file with the quad (or quad dominated) Mesh.
        It can be a .obj or .ply file. If not provided, it is generated
        from the input file with the '.obj' suffix replaced 'with _quad.obj'.
    threads: int
        Number of threads to use in parallel computations.
    deterministic: bool
        If True, prefer (slower) deterministic algorithms. Default False.
    crease: float
        Dihedral angle threshold for creases.
    smooth: int
        Number of smoothing & ray tracing reprojection steps (default: 2).
        Setting this to 0 may result in degenerate quads (with two adjacent
        edges along the same line).
    dominant: bool
        If True, generate a quad dominant mesh instead of a pure quad mesh.
        The output may contain some triangles and pentagones as well.
        Default False.
    intrinsic: bool
        If True, use intrinsic mode (extrinsic is the default).
    boundaries: bool
        If True, align the result on the boundaries. Default False.
        Only applies when the surface is not closed.
    posy: 3 | 4 | 6
        Specifies the position symmetry type. Default 4.
    rosy: 2 | 4 | 6
        Specifies the orientation symmetry type. Default 4.
    scale: float
        The intended edge length of the quad elements. Ignored if either
        faces or vertices is provided. See notes.
    faces: int
        The intended number of quads in the output mesh. Ignored if
        vertices is provided. See notes.
    vertices: int
        The intended number of vertices in the output mesh. See notes.

    Returns
    -------
    Path | None
        The path of the output file if the conversion was successful, else None.

    Notes
    -----
    The 'Instant Meshes' executable should be installed as 'instant-meshes'.

    To control the output resolution, one should specify exactly one of
    scale, faces or vertices. These are mutually exclusive.

    If a pure quad mesh is requested (the default), the number of
    faces and vertices is likely to end up being around 4 times larger and
    the edges two times shorter than requested.
    This is because the initial remeshing may end up with some
    triangles and/or pentagons, which then require a subdivision of all faces
    into smaller quads. You may anticipate to this by specifying smaller values.
    This late subdivision is not done if ``dominant=True``
    is specified, or if the initial remesh does not have any triangles or
    pentagons.

    With dominant=False, posy = 3 or 6 results in a Tri3 Mesh, while posy = 4
    yields a Quad4 Mesh. The best quality is usually obtained with posy=rosy=6
    to produce triangles and posy=rosy=4 for quads.

    See Also
    --------
    :meth:`TriSurface.remesh`: apply remeshing on a TriSurface
    """
    # This is currently not useful
    # knn: int
    #    Point cloud mode: number of adjacent points to consider.
    utils.External.require('instant-meshes')
    infile = Path(infile)
    if outfile:
        outfile = Path(outfile)
    else:
        outfile = infile.with_suffix('_quad.obj')
    cmd = ['instant-meshes', '-o', str(outfile)]
    # Make sure we only have one of scale, faces, vertices
    utils.mutexkeys(kargs, ['vertices', 'faces', 'scale'])
    # Process kargs
    for key in kargs:
        if not isinstance(kargs[key], bool) or kargs[key] is True:
            cmd.append(f'--{key}')
        if not isinstance(kargs[key], bool):
            cmd.append(str(kargs[key]))
    cmd.append(str(infile))
    P = utils.command(cmd)
    return outfile if P.returncode==0 else None


def remesh_instant(S, *, infile=None, outfile=None, nplex=None, **kargs):
    """Create a quality remesh of the TriSurface.

    Uses :func:`instant_meshes` to remesh a TriSurface into a
    quality Tri3 or Quad4 Mesh.

    Parameters
    ----------
    S: TriSurface
        The TriSurface to be remeshed.
    infile: :term:`path_like`
        The name of an .obj file where the TriSurface will be stored for
        processing. If not provided, a temporary file is used.
    outfile: :term:`path_like`
        The name of an .obj file for storing the output Mesh.
        If not provided, it is generated from the infile
        with the '.obj' suffix replaced 'with _remesh.obj'.
    nplex: 3 | 4
        This is a convenient parameter to quickly create a quality mesh
        of triangles or quads. It overwrites the parameters rosy and posy
        with values 6 for nplex=3 and 4 for nplex=4.
    kargs:
        Other keyword arguments passed to :func:`instant_meshes`.
        All the keyword parameters accepted by that function,
        except for 'dominant, can be specified here.

    Returns
    -------
    Mesh | None
        A Mesh of eltype 'tri3' or 'quad4' if the conversion was
        successful, or else None.

    Notes
    -----
    If neither scale, faces or vertices is provided, vertices
    will be set equal to the number of vertices in the TriSurface.
    This is because the default of :func:`instant_meshes` results in a
    much too coarse Mesh.

    If the boundaries parameter is not provided, it is set True
    if the TriSurface is not a closed manifold.

    As a side effect, if file names were specified, the .obj files
    with the original TriSurface and remeshed surface remain available.
    """
    utils.External.require('instant-meshes')
    from pyformex.core import readGeometry
    if infile:
        infile = Path(infile)
    else:
        fil = utils.TempFile(prefix='pyformex-', suffix='.obj')
        infile = fil.path
    S.write(infile)
    if outfile:
        outfile = Path(outfile)
    else:
        if infile:
            outfile = infile.with_suffix('_remesh.obj')
        else:
            fil2 = utils.TempFile(prefix='pyformex-', suffix='.obj')
            outfile = fil2.path
    # Currently force dominant=False
    if nplex == 3:
        kargs['rosy'] = kargs['posy'] = 6
    elif nplex == 4:
        kargs['rosy'] = kargs['posy'] = 4
    kargs['dominant'] = False
    if not ('scale' in kargs or 'faces' in kargs or 'vertices' in kargs):
        kargs['vertices'] = S.ncoords()
    if 'boundaries' not in kargs:
        kargs['boundaries'] = not S.isClosedManifold()
    print(kargs)
    outfile = instant_meshes(infile=infile, outfile=outfile, **kargs)
    if outfile:
        res = readGeometry(outfile)
        if res:
            k = list(res)[0]
            M = res[k]
            if M.elName() == 'tri3':
                M = M.toSurface()
            return M

# TODO: check if we can replace this with frontwalks
def _adjacency_arrays(elems, nsteps=1):
    """Create adjacency arrays for 2-node elements.

    elems is a (nr,2) shaped integer array.
    The result is a list of adjacency arrays, where row i of adjacency array j
    holds a sorted list of the nodes that are connected to node i via a shortest
    path of j elements, padded with -1 values to create an equal list length
    for all nodes.
    This is: [adj0, adj1, ..., adjj, ... , adjn] with n=nsteps.

    Examples
    --------
    >>> for a in _adjacency_arrays([[0,1],[1,2],[2,3],[3,4],[4,0]],3):
    ...     print(a)
    [[0]
     [1]
     [2]
     [3]
     [4]]
    [[1 4]
     [0 2]
     [1 3]
     [2 4]
     [0 3]]
    [[2 3]
     [3 4]
     [0 4]
     [0 1]
     [1 2]]
    []

    """
    elems = Connectivity(elems)
    if len(elems.shape) != 2 or elems.shape[1] != 2:
        raise ValueError("""Expected a set of 2-node elements.""")
    if nsteps < 1:
        raise ValueError("""The shortest path should be at least 1.""")
    # Construct table of nodes connected to each node
    adj1 = elems.adjacency('n')
    m = adj1.shape[0]
    adj = [np.arange(m).reshape(-1, 1), adj1]
    nodes = adj1
    step = 2
    while step <= nsteps and nodes.size > 0:
        # Determine adjacent nodes
        t = nodes < 0
        nodes = adj1[nodes]
        nodes[t] = -1
        nodes = nodes.reshape((m, -1))
        nodes = nodes.normalize()
        # Remove nodes of lower adjacency
        ladj = np.concatenate(adj[-2:], -1)
        t = [np.in1d(n, l, assume_unique=True) for n, l in zip(nodes, ladj)]
        t = np.asarray(t)
        nodes[t] = -1
        nodes = nodes.sortRows()
        # Store current nodes
        adj.append(nodes)
        step += 1
    return adj



##########################################################################
####### Deprecated functions #######################


# End
