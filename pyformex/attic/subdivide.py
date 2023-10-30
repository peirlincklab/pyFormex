import numpy as np

import pyformex as pf
from pyformex import mesh
from pyformex.elements import Elems, Quad4, Tri3

from pyformex.plugins.interaction_tools import Manipulator
from OpenGL.arrays import vbo


def average_by_connectivity(vertices, connectivity, scale=True):
    """Create a average coordinates by connectivity

    :param vertices: vertices coordinates
    :param connectivity: vertices connectivity
    :param scale: scale
    :return:
    """

    connected = connectivity > -1
    nr_connected = connected.sum(axis=-1)

    average = np.sum(vertices[connectivity] * connected[:, :, np.newaxis], axis=1)
    if scale:
        average[nr_connected > 0] /= nr_connected[nr_connected > 0, np.newaxis]

    return average


class PrimalSubdivision:
    """Primal surface subdivision scheme.

    Primal class on which to build surface subdivision schemes.
    Sets attributes to store connectivity.

    A surface is defined by vertices and elements, and can have a parent subdivision surface.
    """

    def __init__(self, vertices, elements, parent=None):

        # Parent subdivision
        self.parent = parent

        # Reference to original vertices
        self._vertices = vertices
        self._elements = elements

        # Faces connectivity
        self._face_by_nodes = None  # faces defined by node IDs
        self._face_by_edges = None  # faces defined by edge IDs
        self._face_by_faces = None  # faces defined by face IDs

        # Nodes connectivity
        self._node_by_nodes = None  # nodes defined by node IDs
        self._node_by_edges = None  # nodes defined by edge IDs
        self._node_by_faces = None  # nodes defined by face IDs

        # Edges connectivity
        self._edge_by_nodes = None  # edges defined by node IDs
        self._edge_by_edges = None  # edges defined by edge IDs
        self._edge_by_faces = None  # edges defined by face IDs

        # Connectivity levels
        self._nr_edge_faces = None  # number of edges per face
        self._nr_node_edges = None  # number of nodes per edge
        self._nr_node_faces = None  # number of nodes per face

        # Border nodes and edges
        self._border_nodes = None  # nodes at the border
        self._border_edges = None  # edges at the border

        # Node points, edge points and face points
        self._node_points = np.ndarray(shape=self.node_by_nodes.shape[:1] + (3, ), dtype=float)  # node points
        self._edge_points = np.ndarray(shape=self.edge_by_nodes.shape[:1] + (3, ), dtype=float)  # edge points
        self._face_points = np.ndarray(shape=self.face_by_nodes.shape[:1] + (3, ), dtype=float)  # face points

        # Subdivision coordinates
        self._coordinates = np.concatenate([
            self._node_points,
            self._face_points,
            self._edge_points, ], axis=0)

        # Subdivision faces connectivity
        self._faces = None

    @property
    def face_by_nodes(self):
        if self._face_by_nodes is None:
            self._face_by_nodes = self._elements
        return self._face_by_nodes

    @property
    def face_by_edges(self):
        if self._face_by_edges is None:
            self._face_by_edges, self._edge_by_nodes = self._elements.insertLevel(1)
        return self._face_by_edges

    @property
    def face_by_faces(self):
        if self._face_by_faces is None:
            self._face_by_faces = np.arange(self._elements.shape[0])[:, np.newaxis]
        return self._face_by_faces

    @property
    def edge_by_nodes(self):
        if self._edge_by_nodes is None:
            self._face_by_edges, self._edge_by_nodes = self._elements.insertLevel(1)
        return self._edge_by_nodes

    @property
    def node_by_nodes(self):
        if self._node_by_nodes is None:
            self._node_by_nodes = np.arange(self._vertices.shape[0])[:, np.newaxis]
        return self._node_by_nodes

    @property
    def node_by_edges(self):
        if self._node_by_edges is None:
            self._node_by_edges = self.edge_by_nodes.inverse(expand=True)
        return self._node_by_edges

    @property
    def node_by_faces(self):
        if self._node_by_faces is None:
            self._node_by_faces = self.face_by_nodes.inverse(expand=True)
        return self._node_by_faces

    @property
    def edge_by_faces(self):
        if self._edge_by_faces is None:
            self._edge_by_faces = self.face_by_edges.inverse(expand=True)
        return self._edge_by_faces

    @property
    def nr_node_faces(self):

        if self._nr_node_faces is None:
            self._nr_node_faces = np.sum(self.node_by_faces > -1, axis=-1)

        return self._nr_node_faces

    @property
    def nr_node_edges(self):

        if self._nr_node_edges is None:
            self._nr_node_edges = np.sum(self.node_by_edges > -1, axis=-1)

        return self._nr_node_edges

    @property
    def border_nodes(self):

        if self._border_nodes is None:
            self._border_nodes = self.nr_node_faces != self.nr_node_edges

        return self._border_nodes

    @property
    def border_edges(self):

        if self._border_edges is None:
            self._border_edges = np.any(self.edge_by_faces < 0, axis=-1)

        return self._border_edges

    def set_node_points(self):
        """Set position of node points
        """

        self._node_points[:] = self._vertices

    @property
    def node_points(self):

        self.set_node_points()

        return self._node_points

    def set_edge_points(self):
        """Set position of edge points
        """

        self._edge_points[:] = average_by_connectivity(self._vertices, self.edge_by_nodes)

    @property
    def edge_points(self):

        self.set_edge_points()

        return self._edge_points

    def set_face_points(self):
        """Set position of face points
        """

        self._face_points[:] = average_by_connectivity(self._vertices, self.face_by_nodes)

    @property
    def face_points(self):

        self.set_face_points()

        return self._face_points

    @property
    def faces(self):
        """Set connectivity of subdivision

        :return:
        """

        return self._faces

    @property
    def coordinates(self):

        if self.parent is not None:
            _ = self.parent.coordinates

        self._coordinates[:] = np.concatenate([
            self.node_points,
            self.edge_points,
            self.face_points, ], axis=0)

        return self._coordinates

    def subdivide(self, number_of_subdivisions=1):

        if number_of_subdivisions > 1:
            return self.subdivide(number_of_subdivisions - 1).subdivide()
        else:
            return self.__class__(self.coordinates, self.faces, parent=self)


class QuadSubdivision(PrimalSubdivision):
    """Quadrilateral subdivision

    Every face of the surface is subdivided into quadrilaterals.
    """

    @property
    def faces(self):
        """Set connectivity of subdivision

        :return:
        """

        if self._faces is None:

            node_offset = 0

            edge_offset = node_offset + self.node_points.shape[0]
            face_offset = edge_offset + self.edge_points.shape[0]

            level = self.face_by_edges.shape[1]

            faces = []
            for i in range(level):
                faces.append(
                    np.ndarray(shape=(
                        self.face_by_nodes.shape[0], 4), dtype=int))

                j = i % level
                k = (i + level - 1) % level

                faces[-1][:, (i + 0) % 4] = self.face_by_nodes[:, j] + node_offset
                faces[-1][:, (i + 1) % 4] = self.face_by_edges[:, j] + edge_offset
                faces[-1][:, (i + 2) % 4] = self.face_by_faces[:, 0] + face_offset
                faces[-1][:, (i + 3) % 4] = self.face_by_edges[:, k] + edge_offset

            faces = np.concatenate(faces, axis=0)

            self._faces = Elems(faces, eltype=Quad4)

        return self._faces

    @property
    def mesh(self):

        return mesh.Mesh(self.coordinates, self.faces, eltype=Quad4)


class CatmullClarkSubdivision(QuadSubdivision):
    """Catmull-Clark subdivision

    Implementation of the Catmull-Clark subdivision scheme
    """

    @property
    def edge_points(self):

        edge_points = super(CatmullClarkSubdivision, self).edge_points
        face_points = super(CatmullClarkSubdivision, self).face_points

        edge_face_avg = average_by_connectivity(face_points, self.edge_by_faces)

        edge_dsp = (edge_face_avg - edge_points) / 2
        edge_dsp[self.border_edges] = 0

        return edge_points + edge_dsp

    @property
    def node_points(self):

        node_points = super(CatmullClarkSubdivision, self).node_points
        edge_points = super(CatmullClarkSubdivision, self).edge_points
        face_points = super(CatmullClarkSubdivision, self).face_points

        node_face_avg = average_by_connectivity(face_points, self.node_by_faces)
        node_edge_avg = average_by_connectivity(edge_points, self.node_by_edges)

        node_dsp = 1 * node_face_avg + 2 * node_edge_avg - 3 * node_points
        node_dsp /= self.nr_node_faces[:, np.newaxis]

        node_by_edges_border = self.node_by_edges[self.border_nodes]
        node_by_edges_border[~self.border_edges[self.node_by_edges][self.border_nodes]] = -1

        node_dsp[self.border_nodes] = (
                average_by_connectivity(edge_points, node_by_edges_border) - node_points[self.border_nodes]) / 2

        return node_points + node_dsp


class TriSubdivision(PrimalSubdivision):
    """Triangle subdivision

    Every face of the surface is subdivided into triangles.
    """

    @property
    def faces(self):
        """Set connectivity of subdivision

        :return:
        """

        if self._faces is None:

            node_offset = 0
            edge_offset = node_offset + self.node_points.shape[0]

            level = self.face_by_edges.shape[1]

            faces = []
            for i in range(level):
                faces.append(
                    np.ndarray(shape=(
                        self.face_by_nodes.shape[0], 3), dtype=int))

                faces[-1][:, 0] = self.face_by_edges[:, (i + 0) % level] + edge_offset
                faces[-1][:, 1] = self.face_by_nodes[:, (i + 1) % level] + node_offset
                faces[-1][:, 2] = self.face_by_edges[:, (i + 1) % level] + edge_offset

            faces.append(
                np.ndarray(shape=(
                    self.face_by_nodes.shape[0], 3), dtype=int))

            for i in range(3):
                faces[-1][:, i] = self.face_by_edges[:, i] + edge_offset

            faces = np.concatenate(faces, axis=0)

            self._faces = Elems(faces, eltype=Tri3)

        return self._faces

    @property
    def mesh(self):

        return mesh.Mesh(self.coordinates, self.faces, eltype=Tri3)


def main():
    """Main function for testing
    """

    # Template mesh for surface subdivision
    template = mesh.Mesh(eltype='quad4').getBorderMesh().extrude(4, 2, 360.).trl(0, 0.3).cylindrical([0, 2, 1])
    template = template.cselect(1)
    template = template.fuse()

    # Apply Catmull-Clark subdivision scheme
    sub = CatmullClarkSubdivision(template.coords, template.elems)
    sub = sub.subdivide(number_of_subdivisions=3)

    if pf.canvas is not None:

        pf.canvas.removeAll()
        pf.canvas.addActor(template.actor(color=0, mode='wireframe'))
        pf.canvas.addActor(sub.mesh.actor(color=1))

        def update_actor(c, a):
            """Update the surface actor

            :param c: canvas
            :param a: actor
            :return:
            """

            # Updating the coordinates of the template mesh suffices to
            # update the subdivision surface since the reference is kept
            template.coords[:] = a.coords

            surf = sub.mesh.actor()
            c.actors[1].vbo = vbo.VBO(surf.coords[surf.elems])

        adjust = Manipulator(
            pf.canvas.actors[0],
            extra=update_actor,
            color=3,
            marksize=10,
            linewidth=3, )

        adjust.start()


if __name__ == '__main__':

    main()

if __name__ == '__draw__':

    main()
