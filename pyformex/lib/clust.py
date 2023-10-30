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
#

"""Point based clustering module.

"""
import numpy as np
from scipy import sparse

from pyformex import arraytools as at
from pyformex.trisurface import TriSurface
from pyformex.lib import clust_c


class Clustering():
    """Uniform point clustering based on ACVD.

    Parameters
    ----------
    mesh : TriSurface

    Notes
    -----
    The algorithm is based on pyvista/pyacvd but is a reimplementation
    using pyFormex data types and techniques.
    """

    def __init__(self, S, _opt=False):
        """Check inputs and initializes neighbors"""
        self.S = S
        self.clusters = None
        self.nclus = None
        self.remesh = None
        # Compute point weights and weighted points
        self._area, self._wcent = weighted_points(self.S)
        # neighbors and edges
        self._neigh, self._nneigh = neighbors_from_mesh(S)
        self._edges = S.edges.astype(at.Int)
        self._opt = _opt

    def cluster(self, nclus, maxiter=100):
        """Cluster points """
        clusters, ndisc = clust_c.cluster(
            self._neigh, self._nneigh, self._area, self._wcent,
            self._edges,  nclus, maxiter)
        if clusters.min() < 0:
            raise ValueError("Cluster optimization failed: {ndisc} isolated clusters")
        clusters = at.renumberClusters(clusters)
        self.clusters = clusters
        self.nclus = clusters.max() + 1
        return clusters, ndisc

    def create_mesh(self, flipnorm=True):
        """ Generates mesh from clusters """
        if flipnorm:
            cnorm = self.cluster_norm()
        else:
            cnorm = None
        # Generate mesh
        self.remesh = create_mesh(self.S, self._area, self.clusters,
                                  cnorm, flipnorm)
        return self.remesh


    def cluster_norm(self):
        """ Return cluster norms """
        if not hasattr(self, 'clusters'):
            raise Exception('No clusters available')

        # Normals of original mesh
        norm = self.S.avgVertexNormals()

        # Compute normalized mean cluster normals
        cnorm = np.empty((self.nclus, 3))
        cnorm[:, 0] = np.bincount(self.clusters, weights=norm[:, 0] * self._area)
        cnorm[:, 1] = np.bincount(self.clusters, weights=norm[:, 1] * self._area)
        cnorm[:, 2] = np.bincount(self.clusters, weights=norm[:, 2] * self._area)
        weights = ((cnorm * cnorm).sum(1)**0.5).reshape((-1, 1))
        weights[weights == 0] = 1
        cnorm /= weights
        return cnorm


def cluster_centroid(cent, area, clusters):
    """ Computes an area normalized centroid for each cluster """

    # Check if null cluster exists
    null_clusters = np.any(clusters == -1)
    if null_clusters:
        clusters = clusters.copy()
        clusters[clusters == -1] = clusters.max() + 1

    wval = cent * area.reshape(-1, 1)
    cweight = np.bincount(clusters, weights=area)
    cweight[cweight == 0] = 1

    cval = np.vstack((np.bincount(clusters, weights=wval[:, 0]),
                      np.bincount(clusters, weights=wval[:, 1]),
                      np.bincount(clusters, weights=wval[:, 2]))) / cweight

    if null_clusters:
        cval[:, -1] = np.inf

    return cval.T


def create_mesh(S, area, clusters, cnorm, flipnorm=True):
    """Generates a new TriSurface given cluster data

    Returns
    -------
    TriSurface

    """
    elems = S.elems
    points = S.coords
    if points.dtype != np.double:
        points = points.astype(np.double)

    # Compute centroids
    ccent = np.ascontiguousarray(cluster_centroid(points, area, clusters))

    # Create sparse matrix storing the number of adjcent clusters a point has
    rng = np.arange(elems.shape[0]).reshape((-1, 1))
    a = np.hstack((rng, rng, rng)).ravel()
    b = clusters[elems].ravel()  # take?
    c = np.ones(len(a), dtype='bool')

    boolmatrix = sparse.csr_matrix((c, (a, b)), dtype='bool')

    # Find all points with three neighboring clusters.  Each of the three
    # cluster neighbors becomes a point on a triangle
    nadjclus = boolmatrix.sum(1)
    adj = np.array(nadjclus == 3).nonzero()[0]
    idx = boolmatrix[adj].nonzero()[1]

    # Append these points and faces
    points = ccent
    f = idx.reshape((-1, 3))

    # Remove duplicate faces
    f = f[unique_row_indices(np.sort(f, 1))]

    # Mean normals of clusters each face is build from
    if flipnorm:
        adjcnorm = cnorm[f].sum(1)
        adjcnorm /= np.linalg.norm(adjcnorm, axis=1).reshape(-1, 1)

        # and compare this with the normals of each face
        newnorm = TriSurface(points, f).normals()
        # print(f"newnorm {newnorm.shape}")

        # If the dot is negative, reverse the order of those faces
        agg = (adjcnorm * newnorm).sum(1)  # dot product
        mask = agg < 0.0
        f[mask] = f[mask, ::-1]

    return TriSurface(points,f)


def unique_row_indices(a):
    """ Indices of unique rows """
    b = np.ascontiguousarray(a).view(
        np.dtype((np.void, a.dtype.itemsize * a.shape[1])))
    _, idx = np.unique(b, return_index=True)
    return idx


def weighted_points(S):
    """Returns point weight based on area weight and weighted points.
    Points are weighted by adjcent area faces.

    Parameters
    ----------
    S : TriSurface
        Triangular surface mesh.

    Returns
    -------
    pweight : np.ndarray, np.double
        Point weight array

    wvertex : np.ndarray, np.double
        Vertices multiplied by their corresponding weights.
    """
    areas = S.areas()
    pweight = at.nodalSum(areas, S.elems)[0]
    wvertex = S.coords*pweight
    return pweight.reshape(-1), wvertex


def neighbors_from_mesh(S):
    """Assemble neighbor array.  Assumes all-triangular mesh.

    Parameters
    ----------
    S : TriSurface
        TriSurface to assemble neighbors from.

    Returns
    -------
    neigh : int np.ndarray [:, ::1]
        Indices of each neighboring node for each node.
        -1 entries are at the end!

    nneigh : int np.ndarray [::1]
        Number of neighbors for each node.
    """
    adj = S.adjacency(kind='n')
    adj = np.require(adj[:,::-1], dtype=np.int32, requirements='C')
    nadj = (adj>=0).sum(-1)
    nadj = np.require(nadj, dtype=np.int32, requirements='C')
    return adj, nadj


def remesh_acvd(S, npoints=-1, ndiv=3):
    """Remesh a TriSurface using an ACDV clustering method

    Parameters
    ----------
    S: TriSurface
        The TriSurface to be remeshed.
    npoints: int, optional
        The approximat number of vertices in the output mesh.
        If negative(default), it is set to the number of vertices
        in the input surface.
    ndiv: int, optional
        The number of subdivisions to created in order to have a finer
        mesh for the clustering method. A higher number results
        in a more regular mesh, at the expense of a longer computation
        time.

    Returns
    -------
    TriSurface
        The remeshed TriSurface, resembling the input mesh, but having
        a more regular mesh. Note that if the input Mesh contains
        sharp folds, you may need to clean up the surface by calling
        :meth:`removeNonManifold` and/or :meth:`fixNormals`.

    Notes
    -----
    This uses a clustering technique based on
    https://www.creatis.insa-lyon.fr/site7/en/acvd to resample the mesh.
    The actual implementation is a modification of
    https://github.com/pyvista/pyacvd, directly using pyFormex data
    structures instead of pyvista/vtk PolyData.

    The meaning of the ndiv paramter is different from that in the
    pyvista/pyacvd module. In pyFormex we can directly set the final
    number of subdivisions and the sub division is done in a single step.
    In pyvista/pyacvd one specifies a number of subdivision
    steps and each step subdivides in 2. Thus a value of nsub = 3 in
    pyvista/pyacvd corresponds to ndiv = 2^3 = 8 in pyFormex. pyFormex
    allows subdivision numbers that are not powers of two. This is not
    possible in pyvista/pyacvd.
    """
    if npoints < 0:
        npoints = S.ncoords()
    if ndiv > 1:
        S = S.subdivide(ndiv).fuse().compact()
        print(f"Subdivide: {S.ncoords()} vertices")
    clus = Clustering(S)
    clus.cluster(npoints)
    return clus.create_mesh()

# End
