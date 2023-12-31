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
"""Interface with VTK.

This module provides an interface with some functions of the Python
Visualization Toolkit (VTK).
Documentation for VTK can be found on http://www.vtk.org/

This module provides the basic interface to convert data structures between
vtk and pyFormex.
"""

import sys
import re
import numpy as np

import pyformex as pf
from pyformex import utils
from pyformex import warning
from pyformex import arraytools as at
from pyformex.path import Path
from pyformex.formex import Formex
from pyformex.mesh import Mesh
from pyformex.coords import Coords
from pyformex.varray import Varray
from pyformex.curve import PolyLine


# Make sure we have vtk
utils.Module.require('vtk', '>= 7.0')
import vtk

from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy, get_numpy_array_type, get_vtk_array_type

# List of vtk data types
#~ VTK_POLY_DATA 0
#~ VTK_STRUCTURED_POINTS 1
#~ VTK_STRUCTURED_GRID 2
#~ VTK_RECTILINEAR_GRID 3
#~ VTK_UNSTRUCTURED_GRID 4
#~ VTK_PIECEWISE_FUNCTION 5
#~ VTK_IMAGE_DATA 6
#~ VTK_DATA_OBJECT 7
#~ VTK_DATA_SET 8
#~ VTK_POINT_SET 9
#~ VTK_UNIFORM_GRID 10
#~ VTK_COMPOSITE_DATA_SET 11
#~ VTK_MULTIGROUP_DATA_SET 12
#~ VTK_MULTIBLOCK_DATA_SET 13
#~ VTK_HIERARCHICAL_DATA_SET 14
#~ VTK_HIERARCHICAL_BOX_DATA_SET 15
#~ VTK_GENERIC_DATA_SET 16
#~ VTK_HYPER_OCTREE 17
#~ VTK_TEMPORAL_DATA_SET 18
#~ VTK_TABLE 19
#~ VTK_GRAPH 20
#~ VTK_TREE 21
#~ VTK_SELECTION 22
#~ VTK_DIRECTED_GRAPH 23
#~ VTK_UNDIRECTED_GRAPH 24
#~ VTK_MULTIPIECE_DATA_SET 25
#~ VTK_DIRECTED_ACYCLIC_GRAPH 26
#~ VTK_ARRAY_DATA 27
#~ VTK_REEB_GRAPH 28
#~ VTK_UNIFORM_GRID_AMR 29
#~ VTK_NON_OVERLAPPING_AMR 30
#~ VTK_OVERLAPPING_AMR 31
#~ VTK_HYPER_TREE_GRID 32
#~ VTK_MOLECULE 33
#~ VTK_PISTON_DATA_OBJECT 34
#~ VTK_PATH 35

#~ vtk cell type is an integer. See
#~ http://davis.lbl.gov/Manuals/VTK-4.5/vtkCellType_8h-source.html

VTUtypes = {
    'point': vtk.VTK_VERTEX,
    'line2': vtk.VTK_LINE,
    'tri3': vtk.VTK_TRIANGLE,
    'quad4': vtk.VTK_QUAD,
    'tet4': vtk.VTK_TETRA,
    'wedge6': vtk.VTK_WEDGE,
    'hex8': vtk.VTK_HEXAHEDRON,
    }


# This docstring is extremely confusing
def Update(vtkobj):
    """ Select Update method according to the vtk version. After version 5
    Update is not needed for vtkObjects, only to vtkFilter and vtkAlgortythm classes.

    Note that this applies only to vtkAlgorithm instances. In all other case
    the use of Update is kept. For this cases this function must not be used.
    """
    if isinstance(vtkobj, vtk.vtkAlgorithm):
       vtkobj.Update()
    return vtkobj


def getVTKtype(a):
    """Converts the  data type from a numpy to a vtk array """
    return get_vtk_array_type(a.dtype)

def getNtype(a):
    """Converts the  data type from a  vtk to a numpy array """
    return get_numpy_array_type(a.GetDataType())

def array2VTK(a, vtype=None):
    """Convert a numpy array to a vtk array

    Parameters:

    - `a`: numpy array nx2
    - `vtype`: vtk output array type. If None the type is derived from
        the numpy array type
    """
    if vtype is None:
        vtype = getVTKtype(a)
    return numpy_to_vtk(np.asarray(a, order='C'), deep=1, array_type=vtype)  # .copy() # deepcopy array conversion for C like array of vtk, it is necessary to avoid memry data loss

def array2N(a, ntype=None):
    """Convert a vtk array to a numpy array

    Parameters:

    - `a`: a vtk array
    - `ntype`: numpy output array type. If None the type is derived from
        the vtk array type
    """
    if ntype is None:
        ntype = getNtype(a)
    return np.asarray(vtk_to_numpy(a), dtype=ntype)


def cleanVPD(vpd):
    """Clean the vtkPolyData

    Clean the vtkPolyData, adjusting connectivity, removing duplicate elements
    and coords, renumbering the connectivity. This is often needed after
    setting the vtkPolyData, to make the vtkPolyData fit for use with other
    operations. Be aware that this operation will change the order and
    numbering of the original data.

    Parameters:

    - `vpd`: a vtkPolyData

    Returns the cleaned vtkPolyData.
    """
    cleaner = vtk.vtkCleanPolyData()
    cleaner.SetInputData(vpd)
    cleaner = Update(cleaner)
    return  cleaner.GetOutput()


def checkClean(mesh):
    """Check if the mesh is fused, compacted and renumbered.

    If mesh is not clean (fused, compacted and renumbered),
    vtkCleanPolyData() will clean it before writing a vtp file.
    This should be avoided because the pyformex points and arrays
    may no longer correspond to the vtk points.
    """
    m1 = mesh.fuse().compact().renumber()
    if (m1.coords != mesh.coords).any():
        return False
    if (m1.elems != mesh.elems).any():
        return False
    return True


def coords2VTK(coords):
    """Convert pyFormex class Coords into VTK class vtkPoints"""
    # creating  vtk coords
    pts = vtk.vtkPoints()
    vtype = pts.GetData().GetDataType()
    coordsv = array2VTK(coords, vtype)  # .copy() # deepcopy array conversion for C like array of vtk, it is necessary to avoid memry data loss
    pts.SetNumberOfPoints(len(coords))
    pts.SetData(coordsv)
    return pts


def elems2VTK(elems):
    """Convert pyFormex class Connectivity into VTK class vtkCellArray"""
    # create vtk connectivity
    Nelems = len(elems)
    Ncxel = len(elems[0])
    elmsv = np.concatenate([Ncxel*ones(Nelems).reshape(-1, 1), elems], axis=1).ravel()
    elmsv = array2VTK(elmsv, vtk.vtkIdTypeArray().GetDataType())
    # set vtk Cell data
    datav = vtk.vtkCellArray()
    datav.SetCells(Nelems, elmsv)
    return datav


def convert2VPD(M, clean=False):
    """Convert pyFormex data to vtkPolyData.

    Convert a pyFormex Mesh or Coords or open PolyLine object into vtkPolyData.
    This is limited to vertices, lines, and polygons.

    Parameters:

    - `M`: a Coords or Mesh or open PolyLine. If M is a Coords type it will be saved as
      VERTS. Else...
    - `clean`: if True, the resulting vtkPolyData will be cleaned by calling
      cleanVPD.

    If the Mesh has a prop array the properties are added as cell data array in an array called prop.
    This name should be protected from the user to allow to convert properties from/to the vtk interface.

    Returns a vtkPolyData.
    """
    pf.debug('STARTING CONVERSION FOR DATA OF TYPE %s '%type(M), pf.DEBUG.VTK)

    if isinstance(M, Formex):
        M = M.toMesh()

    if isinstance(M, Coords):
        M = Mesh(M, np.arange(M.ncoords()))
        elems = M.elems
    elif isinstance(M, PolyLine):
        if M.closed == True:
            raise ValueError('only an OPEN polyline can be convert to a vtkPolyData. Convert a closed polyline into a line2 Mesh.')
        M = M.toMesh()
        elems = np.arange(M.ncoords()).reshape(1, -1)  # a polyline in vtk has one single element
    elif isinstance(M, Mesh):
        elems = M.elems
    else:
        raise ValueError('conversion of %s type to vtkPolyData is not yet supported'%type(M))

    plex = elems.shape[1]
    vpd = vtk.vtkPolyData()  # create a vtkPolyData variable
    pts = coords2VTK(M.coords)  # creating  vtk coords
    vpd.SetPoints(pts)
    datav = elems2VTK(elems)  # create vtk connectivity as vtkCellArray

    if M.nplex() == 1:  # point mesh
        try:
            pf.debug("setting VERTS for data with %s maximum number of point for cell "%plex, pf.DEBUG.VTK)
            vpd.SetVerts(datav)
        except Exception:
            raise ValueError("Error in saving  VERTS")
    elif M.nplex() == 2:  # line2 mesh or polyline
        try:
            pf.debug("setting LINES for data with %s maximum number of point for cell "%plex, pf.DEBUG.VTK)
            vpd.SetLines(datav)
        except Exception:
            raise  ValueError("Error in saving  LINES")
    else:  # polygons
        try:
            pf.debug("setting POLYS for data with %s maximum number of point for cell "%plex, pf.DEBUG.VTK)
            vpd.SetPolys(datav)
        except Exception:
            raise ValueError("Error in saving  POLYS")

    if M.prop is not None:  # convert prop numbers into vtk array
        vtype = vtk.vtkIntArray().GetDataType()
        vprop = array2VTK(M.prop, vtype)
        vprop.SetName('prop')
        vpd.GetCellData().AddArray(vprop)

    vpd = Update(vpd)
    if clean:
        vpd = cleanVPD(vpd)
    return vpd


def convert2VTU(M):
    """Convert pyFormex Mesh to vtk unstructured grid.

    Return a VTK unstructured grid (VTU) supports any element type and
    is therefore an equivalent of pyFormex class Mesh.
    """
    # create vtk coords
    pts = coords2VTK(M.coords)
    # create vtk connectivity
    datav = elems2VTK(M.elems)
    # find vtu cell type
    vtuCellType = VTUtypes[M.elName()]


    # create the vtu
    vtu = vtk.vtkUnstructuredGrid()
    vtu.SetPoints(pts)
    vtu.SetCells(vtuCellType, datav)

    if M.prop is not None:  # convert prop numbers into vtk array
        vtype = vtk.vtkIntArray().GetDataType()
        vprop = array2VTK(M.prop, vtype)
        vprop.SetName('prop')
        vtu.GetCellData().AddArray(vprop)

    vtu = Update(vtu)
    return vtu


def convertVPD2Triangles(vpd):
    """Convert a vtkPolyData to a vtk triangular surface.

    Convert a vtkPolyData to a vtk triangular surface. This is convenient
    when vtkPolyData are non-triangular polygons.

    Parameters:

    - `vpd`: a vtkPolyData

    Returns
    """
    triangles = vtk.vtkTriangleFilter()
    triangles.SetInputData(vpd)
    triangles = Update(triangles)
    return triangles.GetOutput()



def coordsFromVTK(vtkpoints):
    """Convert VTK class vtkPoints into pyFormex class Coords """
    coords = None
    if  vtkpoints.GetData().GetNumberOfTuples():
        coords = Coords(array2N(vtkpoints.GetData()))
    return coords


def convertFromVPD(vpd, samePlex=True):
    """Convert a vtkPolyData into pyFormex objects.

    Parameters:

    - `vpd`: a vtkPolyData
    - `samePlex`: True if you are sure that all lines and polys have the same element type

    Returns:

        - a list with points, cells, polygons, lines, vertices numpy arrays if samePlex is True
         or pyFormex varray if samePlex is False.
        - `fielddata` : a dict of {name:fielddata_numpy_array}
        - `celldata` : a dict of {name:celldata_numpy_array}
        - `pointdata` : a dict of {name:pointdata_numpy_array}


    Returns None for the missing arrays, empty dict for empty data.
    """
    coords = cells = polys = lines = verts = None
    fielddata = celldata = pointdata = dict()

    if vpd is None:
        pf.debug('The vtkPolyData is None', pf.DEBUG.VTK)
        return [coords, cells, polys, lines, verts], fielddata, celldata, pointdata

    # getting points coords
    if  vpd.GetPoints().GetData().GetNumberOfTuples():
        coords = Coords(array2N(vpd.GetPoints().GetData()))
        pf.debug('Saved points coordinates array', pf.DEBUG.VTK)

    vtkdtype = vpd.GetDataObjectType()
    # getting Cells
    if vtkdtype not in [0]:  # this list need to be updated according to the data type
        if  vpd.GetCells().GetData().GetNumberOfTuples():
            if samePlex == True:
                Nplex = vpd.GetCells().GetMaxCellSize()
                cells = array2N(vpd.GetCells().GetData()).reshape(-1, Nplex+1)[:, 1:]
                pf.debug('Saved cells connectivity array', pf.DEBUG.VTK)
            else:
                cells =  Varray(array2N(vpd.GetCells().GetData()))  # vtkCellArray to varray
                pf.debug('Saved cells connectivity varray', pf.DEBUG.VTK)

    # getting Strips
    if vtkdtype not in [4]:  # this list need to be updated according to the data type
        if vpd.GetStrips().GetData().GetNumberOfTuples():
            utils.warn("VTK_strips")
            vpd = convertVPD2Triangles(vpd)

    # getting polygons
    if vtkdtype not in [4]:  # this list need to be updated according to the data type
        if  vpd.GetPolys().GetData().GetNumberOfTuples():
            if samePlex == True:
                Nplex = vpd.GetPolys().GetMaxCellSize()
                polys = array2N(vpd.GetPolys().GetData()).reshape(-1, Nplex+1)[:, 1:]
                pf.debug('Saved cells connectivity array', pf.DEBUG.VTK)
            else:
                polys =  Varray(array2N(vpd.GetPolys().GetData()))  # vtkCellArray to varray
                pf.debug('Saved cells connectivity varray', pf.DEBUG.VTK)

    # getting Lines
    if vtkdtype not in [4]:  # this list need to be updated according to the data type
        if  vpd.GetLines().GetData().GetNumberOfTuples():
            if samePlex == True:
                Nplex = vpd.GetLines().GetMaxCellSize()
                lines = array2N(vpd.GetLines().GetData()).reshape(-1, Nplex+1)[:, 1:]
                pf.debug('Saved lines connectivity array', pf.DEBUG.VTK)
            else:
                lines =  Varray(array2N(vpd.GetLines().GetData()))  # this is the case of polylines
                pf.debug('Saved lines connectivity varray', pf.DEBUG.VTK)

    # getting Vertices
    if vtkdtype not in [4]:  # this list need to be updated acoorind to the data type
        if  vpd.GetVerts().GetData().GetNumberOfTuples():
            Nplex = vpd.GetVerts().GetMaxCellSize()
            verts = array2N(vpd.GetVerts().GetData()).reshape(-1, Nplex+1)[:, 1:]
            pf.debug('Saved verts connectivity array', pf.DEBUG.VTK)

    def builddatadict(data):
        """It helps finding empty and non-empty array data (field, cell and point)
        """
        arraynm = [data.GetArrayName(i) for i in range(data.GetNumberOfArrays())]
        #first get the None data
        emptyarraynm = [an for an in arraynm if data.GetArray(an) is None]
        emptydata = [data.GetArray(an) for an in emptyarraynm]
        emptydata = dict(zip(emptyarraynm, emptydata))
        #then get the non-None data (ie. with an array)
        arraynm = [an for an in arraynm if data.GetArray(an) is not None]
        okdata = [array2N(data.GetArray(an)) for an in arraynm]
        okdata = dict(zip(arraynm, okdata))
        #now merge the empty and non-empty data
        okdata.update(emptydata)
        pf.debug('Non-empty Data Arrays:%s'% arraynm, pf.DEBUG.VTK)
        pf.debug('Empty Data Arrays:%s'% emptyarraynm, pf.DEBUG.VTK)
        return okdata

    # getting Fields
    if vpd.GetFieldData().GetNumberOfArrays():
        fielddata = vpd.GetFieldData()
        pf.debug('*Field Data Arrays', pf.DEBUG.VTK)
        fielddata = builddatadict(fielddata)

    # getting cells data
    if vpd.GetCellData().GetNumberOfArrays():
        celldata = vpd.GetCellData()
        pf.debug('*Cell Data Arrays', pf.DEBUG.VTK)
        celldata = builddatadict(celldata)

    # getting points data
    if vpd.GetPointData().GetNumberOfArrays():
        pointdata = vpd.GetPointData()
        pf.debug('*Point Data Arrays', pf.DEBUG.VTK)
        pointdata = builddatadict(pointdata)

    return [coords, cells, polys, lines, verts], fielddata, celldata, pointdata


def writeVTP(fn, mesh, fielddata={}, celldata={}, pointdata={}, checkMesh=True, writernm=None):
    """Write a Mesh in .vtp or .vtk file format.

    - `fn`: a filename with .vtp or .vtk extension.
    - `mesh`: a Mesh of level 0, 1 or 2 (and volume Mesh in case of .vtk)
    - `fielddata`: dictionary of arrays associated to the fields (?).
    - `celldata`: dictionary of arrays associated to the elements.
    - `pointdata`: dictionary of arrays associated to the points (renumbered).
    - `checkMesh`: bool: if True, raises a warning if mesh is not clean.
    - `writernm`: specify which vtk writer should be used.
     If None the writer is selected based on fn extension.

    If the Mesh has property numbers, they are stored in a vtk array named prop.
    Additional arrays can be added and will be written as type double.

    The user should take care that the mesh is already fused, compacted and
    renumbered. If not, these operations will be done by vtkCleanPolyData()
    and the points may no longer correspond to the point data arrays.

    The .vtp or .vtk file can be viewed in paraview.

    VTP format can contain

    - polygons: triangles, quads, etc.
    - lines
    - points

    VTU format has been tested with

    - Mesh of type: point,line2,tri3,quad4,tet4,hex8

    """
    fn = Path(fn)
    if checkMesh:
        if not checkClean(mesh):
            utils.warn("warn_writevtp_notclean")
        dupl = mesh.elems.listDuplicate()
        if len(dupl)>0:
            utils.warn("warn_writevtp_duplicates", data=(np.array2string(dupl, separator=',')))

    ftype = fn.lsuffix
    if writernm is None:
        if ftype == '.vtp':
            writer = vtk.vtkXMLPolyDataWriter()
            lvtk = convert2VPD(mesh, clean=False)  # this is not forced to clean the mesh anymore
        elif ftype == '.vtk':
            writer = vtk.vtkDataSetWriter()
            lvtk = convert2VTU(mesh)
        elif ftype == '.vtu':
            writer = vtk.vtkXMLDataSetWriter()
            lvtk = convert2VTU(mesh)
        else:
            raise ValueError('extension not recongnized')
    elif writernm == 'vtkPolyDataWriter':
            writer = vtk.vtkPolyDataWriter()
            lvtk = convert2VPD(mesh, clean=False)  # this is not forced to clean the mesh anymore

    if mesh.prop is not None:  # convert prop numbers into vtk array
        vtype = vtk.vtkIntArray().GetDataType()
        vtkprop = array2VTK(mesh.prop, vtype)
        vtkprop.SetName('prop')
        lvtk.GetCellData().AddArray(vtkprop)
    for k in fielddata.keys():  # same numbering of mesh.elems??
        vtype = vtk.vtkDoubleArray().GetDataType()
        if fielddata[k].shape[0]!=mesh.nelems():
            print((fielddata[k].shape,))
            utils.warn("warn_writevtp_shape")
        vtkdata = array2VTK(fielddata[k], vtype)
        vtkdata.SetName(k)
        lvtk.GetFieldData().AddArray(vtkdata)
    for k in celldata.keys():  # same numbering of mesh.elems
        vtype = vtk.vtkDoubleArray().GetDataType()
        if celldata[k].shape[0]!=mesh.nelems():
            utils.warn("warn_writevtp_shape")
        vtkdata = array2VTK(celldata[k], vtype)
        vtkdata.SetName(k)
        lvtk.GetCellData().AddArray(vtkdata)
    for k in pointdata.keys():  # same numbering of mesh.coords
        vtype = vtk.vtkDoubleArray().GetDataType()
        if pointdata[k].shape[0]!=mesh.ncoords():  # mesh should be clean!!
            print((pointdata[k].shape, mesh.ncoords()))
            utils.warn("warn_writevtp_shape2")
        vtkdata = array2VTK(pointdata[k], vtype)
        vtkdata.SetName(k)
        lvtk.GetPointData().AddArray(vtkdata)
    #~ print(('************lvtk', lvtk))
    writer.SetInputData(lvtk)
    writer.SetFileName(fn)
    writer.Write()


def writeVTPmany(fn, items):
    """Writes many objects in vtp or vtk file format.

    item can be a list of items supported by convert2VPD (mesh of coords, line2, tri3 and quad4)
    or convert2VTU (mesh of coords, line2, tri3, quad4, tet4 and hex8).

    This is experimental!
    """
    fn = Path(fn)
    ftype = fn.lsuffix

    if ftype=='.vtp':
        writer = vtk.vtkXMLPolyDataWriter()
        apd = vtk.vtkAppendPolyData()
        vtkitems = [convert2VPD(M=m) for m in items]
    elif ftype=='.vtk':
        writer = vtk.vtkDataSetWriter()
        apd = vtk.vtkAppendFilter()
        vtkitems = [convert2VTU(M=m) for m in items]
    for lvtk in vtkitems:
        apd.AddInputData(lvtk)
    vtkobj = apd.GetOutput()
    writer.SetInputData(vtkobj)
    writer.SetFileName(fn)
    writer.Write()


def readVTKObject(fn, samePlex=True, readernm=None):
    """Read a vtp/vtk file

    Read a vtp/vtk file and return coords, list of elems, and a dict of arrays.

    Parameters

    - `fn`: a filename with any vtk object extension (vtp or vtk for the moment).


    Returns the same output of convertFomVPD:

        - a list with coords, cells, polygons, lines, vertices numpy arrays
        - `fielddata` : a dict of {name:fielddata_numpy_array}
        - `celldata` : a dict of {name:celldata_numpy_array}
        - `pointdata` : a dict of {name:pointdata_numpy_array}


    Returns None for the missing data.
    The dictionary of arrays can include the elements ids (e.g. properties).
    """
    fn = Path(fn)
    allreadersnm = 'vtkXMLPolyDataReader, vtkDataSetReader, vtkUnstructuredGridReader, vtkPolyDataReader,vtkStructuredPointsReader, vtkStructuredGridReader, vtkRectilinearGridReader'
    if readernm is None:
        ftype = fn.lsuffix
        if ftype=='.vtp':
            reader, readernm = vtk.vtkXMLPolyDataReader(), 'vtkXMLPolyDataReader'
        if ftype=='.vtk':
            reader, readernm = vtk.vtkDataSetReader(), 'vtkDataSetReader'
    else:
        if readernm == 'vtkXMLPolyDataReader':
            reader = vtk.vtkXMLPolyDataReader()
        elif readernm == 'vtkDataSetReader':
            reader = vtk.vtkDataSetReader()
        elif readernm == 'vtkUnstructuredGridReader':
            reader = vtk.vtkUnstructuredGridReader()
        elif readernm == 'vtkPolyDataReader':
            reader = vtk.vtkPolyDataReader()
        elif readernm == 'vtkStructuredPointsReader':
            reader = vtk.vtkStructuredPointsReader()
        elif readernm == 'vtkStructuredGridReader':
            reader = vtk.vtkStructuredGridReaderr()
        elif readernm == 'vtkRectilinearGridReaderr':
            reader = vtk.vtkRectilinearGridReader()
        else:
            raise ValueError('unknown reader %s, please specify an alternative reader: %s'%(readernm, allreadersnm))

    reader.SetFileName(fn)
    reader = Update(reader)
    if reader.GetErrorCode()!=0:
        utils.warn('the default vtk reader %s raised an error, please specify an alternative reader: %s'%(readernm, allreadersnm))
    vpd = reader.GetOutput()  # vtk object
    if vpd is None:
        utils.warn('vpd is undefined (None),  please check vtk filename and vtk reader')
    pf.debug('file %s read with vtk reader: %s'%(fn, readernm),)
    return convertFromVPD(vpd, samePlex=samePlex)



def pointInsideObject(S, P, tol=0., check_surface=True):
    """vtk function to test which of the points P are inside surface S

    Test which of the points pts are inside the surface surf.

    Parameters:

    - `S`: a TriSurface specifying a closed surface
    - `P`: a Coords (npts,3) specifying npts points
    - `tol`: a tolerance applied on matching float values
    - `check_surface`: bool.  A boolean flag to first check whether the surface is
       a closed manifold. If True and the surface is not a closed manifold, all points
       will be marked outside. Note that if this check is not performed and the surface
       is not closed, the results are undefined.

    Returns a bool array with True/False for points inside/outside the surface.
    """
    vpp = convert2VPD(P)
    vps = convert2VPD(S, clean=False)

    enclosed_pts = vtk.vtkSelectEnclosedPoints()
    enclosed_pts.SetInputData(vpp)
    enclosed_pts.SetTolerance(tol)
    # according to the documentation SetSurfaceData in VTK 7 is only
    # used in vtkSelectEnclosedPoints. A general function is not needed
    if vtk.VTK_MAJOR_VERSION <= 5:
        enclosed_pts.SetSurface(vps)
    if vtk.VTK_MAJOR_VERSION >= 6:
        enclosed_pts.SetSurfaceData(vps)
    enclosed_pts.SetCheckSurface(check_surface)
    enclosed_pts = Update(enclosed_pts)
    inside_arr = enclosed_pts.GetOutput().GetPointData().GetArray('SelectedPoints')
    enclosed_pts.ReleaseDataFlagOn()
    enclosed_pts.Complete()
    del enclosed_pts
    if inside_arr is None:
        return np.zeros(P.shape[0], dtype='bool')
    return array2N(inside_arr, 'bool')


def inside(surf, pts, tol='auto'):
    """Test which of the points pts are inside the surface surf.

    Parameters:

    - `surf`: a TriSurface specifying a closed surface
    - `pts`: a Coords (npts,3) specifying npts points
    - `tol`: a tolerance applied on matching float values

    Returns an integer array with the indices of the points that are
    inside the surface.

    See also :meth:`gts_itf.inside` for an equivalent and faster
    alternative.
    """
    if tol == 'auto':
        tol = 0.
    return np.where(pointInsideObject(surf, pts, tol))[0]


def intersectionWithLines(self, q, q2, method='line', atol=1e-5, closest=False, reorder=False):
    """Compute the intersection of surf with lines.

    Parameters:

    - `self`: Formex, Mesh or TriSurface
    - `q`,`q2`: (...,3) shaped arrays of points, defining
          a set of lines.
    - `atol`:  tolerance
    - `method`: a string (line) defining if the line, is a full-line. Otherwise  the provided segments
            are used for the intersections
    - `closest`:  boolean. If True returns only the closest point to the first point of each segment.
    - `reorder`:  boolean. If True reorder the points according to the the line order.

    Returns:
    - a fused set of intersection points (Coords)
    - a (1,3) array with the indices of intersection point, line and
      triangle
    """
    from pyformex.geomtools import distance
    from pyformex.simple import cuboid, principalBbox
    from pyformex.formex import connect
    from pyformex.gui.draw import draw

    q = np.asarray(q).reshape(-1, 3)
    q2 = np.asarray(q2).reshape(-1, 3)

    if method=='line':
        # expand the segments to ensure to be in the bbox of self.
        # The idea is to check the max distance between the bboxes of lines and self
        # then scale usin shrink all the segments of the relative factor between the distance
        # and the minimum segment. The set of lines is cut and the 2 points corresponding to a single line are used as
        # new q and q2.
        # NOTE THE ALGORYTHM IS VERY DEPENDENT ON THE SEGMENT'S SIZES. FOR THIS REASON IS CLIPPED
        # ON THE TARGET BBOX
        # The subdivision is NECESSARY as the implicit function do not work well with vtkLines with low resolution
        #giving rounded corners of the box function or no lines in return. the values of 20 minimum points per line within the
        # target bbox has been chosen after various resolution tests
        lines = connect([q, q2], eltype='line2')
        off = lines.toMesh().lengths().min()

        bbl = principalBbox(lines)
        bbs = principalBbox(self.coords)
        # The bbox is scale x 2. this is need to avoid some numerical error which may give a too short line cut
        bbs = bbs.trl(-bbs.center()).scale(2).trl(bbs.center())
        d = distance(bbs.coords, bbl.coords).max()
        nsub=int(2*(1+2*(d+off)/off/bbs.sizes().max()))

        lines = lines.shrink((d+off)/off).toMesh().setProp(prop='range').subdivide(nsub)
        verts = vtkCut(lines, implicitdata=bbs.toSurface(), method='surface')

        if verts is None:
            return

        idprops = at.inverseIndex(verts.prop[..., np.newaxis])
        idprops = idprops[(idprops==-1).sum(axis=1)==0, :]

        if idprops.shape[0]!=q.shape[0]:
            pf.warning('Not all lines were clipped')

        q = verts.coords[verts.elems[idprops[:, 0]]].squeeze().reshape(-1, 3)
        q2 = verts.coords[verts.elems[idprops[:, 1]]].squeeze().reshape(-1, 3)



    if atol:
        self = self.toFormex().shrink(1+atol).toMesh()

    vsurf = convert2VPD(self, clean=False)
    loc = vtk.vtkOBBTree()
    loc.SetDataSet(vsurf)
    loc.SetTolerance(0)
    loc.BuildLocator()
    loc = Update(loc)

    cellids = []
    lineids = []
    pts = []

    cellidstmp = [vtk.vtkIdList() for i in range(q.shape[0])]
    ptstmp = [vtk.vtkPoints() for i in range(q.shape[0])]

    [loc.IntersectWithLine(q[i], q2[i], ptstmp[i], cellidstmp[i]) for i in range(q.shape[0])]

    loc.FreeSearchStructure()
    del loc

    [[cellids.append(cellidstmp[i].GetId(j)) for j in range(cellidstmp[i].GetNumberOfIds())] for i in range(q.shape[0])]
    [[lineids.append(i) for j in range(cellidstmp[i].GetNumberOfIds())] for i in range(q.shape[0])]
    [[pts.append(ptstmp[i].GetData().GetTuple3(j)) for j in range(ptstmp[i].GetData().GetNumberOfTuples())] for i in range(q.shape[0])]

    cellids = np.asarray(cellids)
    lineids = np.asarray(lineids)
    pts = np.asarray(pts)

    if closest:
        d = at.length((pts-q[lineids]))
        ind = ma.masked_values(at.inverseIndex(lineids.reshape(-1, 1)), -1)
        d = ma.array(d[ind], mask=ind<0).argmin(axis=1)
        ind = ind[np.arange(ind.shape[0]), d].compressed()
        pts = pts[ind]
        lineids = lineids[ind]
        cellids = cellids[ind]

    pts, j=Coords(pts).fuse()

    # This option has been tested only with closest=True
    if reorder:
        hitsxline = at.inverseIndex(lineids.reshape(-1, 1))
        j = j[hitsxline[np.where(hitsxline>-1)]]
        lineids = lineids[hitsxline[np.where(hitsxline>-1)]]
        cellids = cellids[hitsxline[np.where(hitsxline>-1)]]
        pts=pts[j]


    if method=='line':
        lineids=verts.prop[idprops[:, 0]][lineids]

    return pts, np.column_stack([j, lineids, cellids])


def convertTransform4x4FromVtk(transform):
    """Convert a VTK transform to numpy array

    Convert a vtk transformation instance vtkTrasmorm into a 4x4 transformation
    matrix array
    """
    trMat4x4 = [[transform.GetMatrix().GetElement(r, c) for c in range(4)] for r in range(4)]
    return np.asarray(trMat4x4)


def convertTransform4x4ToVtk(trMat4x4):
    """Convert a numpy array to a VTK transform

    Convert a 4x4 transformation matrix array into a vtkTransform instance
    """
    trMatVtk = vtk.vtkTransform()
    [[trMatVtk.GetMatrix().SetElement(r, c, trMat4x4[r, c]) for c in range(4)] for r in range(4)]
    return trMatVtk


def transform(source, trMat4x4):
    """Apply a 4x4 transformation

    Apply a 4x4 transformation matrix array to `source` whcih can be
    a Geometry surface or Coords class.

    Returns a copy of the source object with transformed coordinates
    """
    vtksource = convert2VPD(source)
    trMat4x4 = convertTransform4x4ToVtk(trMat4x4)
    transformFilter = vtk.vtkTransformPolyDataFilter()
    transformFilter.SetInputData(vtksource)
    transformFilter.SetTransform(trMat4x4)
    transformFilter = Update(transformFilter)
    coords = coordsFromVTK(transformFilter.GetOutput().GetPoints())
    if isinstance(source, Coords):
        return coords
    else:
        sourceout=source.copy()
        sourceout.coords=coords
        return sourceout


def _vtkCutter(self, vtkif):
    """Cut a Mesh with a vtk implicit function.

    Parameters:

    - `mesh`: a Mesh.
    - `vtkif`: a vtk implicit function.

    In vtk `cut` means intersection: mesh dimension is reduced by one.
    Returns a mesh of points if self is a line2 mesh,
    a mesh of lines if self is a surface tri3 or quad4 mesh,
    a triangular mesh if self is tet4 or hex8 mesh.
    If there is no intersection returns None.
    This functions should not be used by the user.
    VTK implicit functions are listed here:
    http://www.vtk.org/doc/nightly/html/classvtkImplicitFunction.html
    """
    vtkobj = convert2VTU(self)
    cutter = vtk.vtkCutter()
    cutter.SetCutFunction(vtkif)
    cutter.SetInputData(vtkobj)
    cutter = Update(cutter)
    cutter = cutter.GetOutput()
    [coords, cells, polys, lines, verts], fielddata, celldata, pointdata=convertFromVPD(cutter, samePlex=True)

    prop=None
    if 'prop' in celldata:
        prop = celldata['prop']

    if verts is not None:  # self was a line mesh
        return Mesh(coords, verts).setProp(prop)
    elif lines is not None:  # self was a surface mesh
        return Mesh(coords, lines).setProp(prop)
    elif polys is not None:  # self was a volume mesh
        return Mesh(coords, polys).setProp(prop)
    else:
        return None  # no intersection found


def _vtkClipper(self, vtkif, insideout):
    """Clip a Mesh with a vtk implicit function.

    Parameters:

    - `mesh`: a Mesh.
    - `vtkif`: a vtk implicit function.
    - `insideout`: bool or boolean integer(0 or 1) to selet the select the side
        of the selection

    Returns:
      - `m`: list of Mesh of different element types.

    In vtk `clip` means that the intersected elements are cut to
    get a part of a mesh. Here vtkClipDataSet has been used.
    More efficient functions are available for PolyData or volumes
    but the results are the same. Note that the quality of the cut depends
    on the resolution of the input, and can give rounded corners of the clipped
    region. This does not occur clipping with a vtkPlane. Maybe we should
    find a way to use only this.
    This functions should not be used by the user.
    """
    from pyformex.elements import Tet4, ElementType

    if self.eltype.ndim <= 2:
        vtkobj = convert2VPD(self)
    elif self.eltype.ndim == 3:
        vtkobj = convert2VTU(self)

    clipper = vtk.vtkClipDataSet()
    clipper.SetInputData(vtkobj)
    clipper.SetClipFunction(vtkif)
    clipper.SetInsideOut(int(insideout))
    clipper = Update(clipper)
    clipper = clipper.GetOutput()
    [coords, cells, polys, lines, verts], fielddata, celldata, pointdata = convertFromVPD(vpd=clipper, samePlex=False)

    prop = None
    if 'prop' in celldata:
        prop = celldata['prop']

    m = []
    ulens, lens=cells.sameLength()
    for c, ul, l in zip(cells.split(), ulens, lens):
        if self.eltype.ndim == 3 and ul == 4:
            eltype = Tet4
        else:
            if ul in ElementType.default:
                eltype = ElementType.default[ul]
            else:
                raise ValueError('Unexpected element type: please report it to developers!')

        m.append(Mesh(coords, c, eltype=eltype))
        if prop is not None:
            m[-1].setProp(prop[l])
    return m


# Implicit Functions
def _vtkPlane(p, n):
    plane = vtk.vtkPlane()
    plane.SetOrigin(p)
    plane.SetNormal(n)
    return plane

def _vtkPlanes(p, n):
    """ Set a vtkPlanes implicit function.

     Parameters:

    - `p` : points of the planes
    - `n`: correspondent normals of the planes

    In vtkPlanes p and n need to define a convex set of planes,
    and the normals must point outside of the convex region.
    """
    planes = vtk.vtkPlanes()
    planes.SetNormals(array2VTK(n))
    planes.SetPoints(coords2VTK(p))
    return planes

def _vtkSurfacePlanes(self):
    """ Convert a convex closed manifold surface into vtkPlanes"""
    if self.isClosedManifold() and self.isConvexManifold():
        raise warning('The input should be a convex closed manifold TriSurface. Results may be incorrect.')
    return _vtkPlanes(p=self.centroids(), n=self.normals())


def _vtkSphere(c, r):
    sphere = vtk.vtkSphere()
    sphere.SetCenter(c)
    sphere.SetRadius(r)
    return sphere


# TODO: this is broken because of the non-existent CoordinateSystem
# Either someone fixes it, or it will get removed.
# trf2CS is needed by _vtkBox
# removed 20-10-2023 since nobody wants to fix it
# def trf2CS(CS, angle_spec=at.DEG):
#     """Return the transformations to change coordinate system.

#     Return a series of ordered transformations required to position
#     an object into a new cartesian coordinate system (CS):
#     scaling, rotation about x, rotation about y, rotation about z, translation.
#     The scaling is needed for CS with non-unitary axes'vectors.
#     Scaling, rotations and translations should be applied in order.
#     An error is raised if CS is not orthogonal because
#     shearing is not supported.
#     """
#     def isOrthogonal(CS, tol=1.e-4):
#         """Check if a coordinate system is orthogonal
#         """
#         from pyformex.geomtools import rotationAngle
#         r, ax = rotationAngle(CS[0]-CS[3], CS[1]-CS[3])
#         if abs(r-90.)<tol:
#             if np.sum(abs(at.normalize(CS[2]-CS[3]) - ax))<tol:
#                 return True
#         return False
#     if isOrthogonal(CS) == False:
#         raise ValueError('the coordinate system is not orthogonal')
#     sz = at.length(CS[:3]-CS[3])  # axes`s length
#     j = [3, 0, 2]  # z,x,o
#     mat, t = at.trfmat(CoordinateSystem()[j], CS[j])
#     rx, ry, rz = at.cardanAngles(mat, angle_spec)
#     return sz, rx, ry, rz, t


# TODO: Use opengl.matrix.Matrix4
# When 4x4 matrices will be added to pyFormex, the box
# could be also sheared by first rotating and then scaling.
# removed 20-10-2023 because of missing trf2CS
# def _vtkBox(p=None, trMat4x4=None):
#     """_Return scaled an positioned vtkBox.

#     Parameters:

#     - `p`: a coordinate system, 4 coords, a formex or a mesh.
#     - `trMat4x4`: a 4x4 matrix.

#     A vtkBox is an implicit vtk function defining a scaled cuboid in space.
#     In order to place the cuboid in space you cannot assing coordinates to
#     this vtk class, but you can transform an original box
#     using affine transformations. In general a 4x4 matrix
#     would be appropriate but it is not yet implemented in pyFormex.
#     !! INCORRECT: opengl.matrix has Matrix4 class
#     Alternatively, 4 points corresponding to the x,y,z,o of an orthogonal
#     coordinate system can be used. In this case p can be either a list of 4 coords,
#     a coordinate system, a cuboid defined as hex8-element Formex
#     or Mesh (in this case only 4 points are taken).
#     """
#     box = vtk.vtkBox()

#     if trMat4x4 is not None:
#         if p is not None:
#             raise ValueError('a box cannot be defined both by coordinates and matrix')
#         else:
#             vtkMat4x4 = convertTransform4x4ToVtk(trMat4x4)
#             box.SetTransform(vtkMat4x4)
#             return box
#     elif p is not None:
#         if isinstance(p, Mesh):
#             p = p.toFormex()
#         if isinstance(p, Formex):
#             p = p.points()[[1, 3, 4, 0]]
#         L, r0, r1, r2, trv = trf2CS(p)
#         box = vtkBox()  # vtk equivalent of simple.cuboid(xmin=xmin,xmax=xmax)
#         box.SetXMin([0., 0., 0.])
#         box.SetXMax(L)
#         trans = vtk.vtkTransform()
#         trans.RotateWXYZ(-r0, 1., 0., 0.)
#         trans.RotateWXYZ(-r1, 0., 1., 0.)
#         trans.RotateWXYZ(-r2, 0., 0., 1.)
#         trans.Translate(-trv)
#         box.SetTransform(trans)
#         return box


def vtkCut(self, implicitdata, method=None):
    """Cut (get intersection of) a Mesh with plane(s), a sphere or a box.

    Parameters:

    - `self`: a Mesh (line2,tri3,quad4).
    - `implicitdata`: list or vtkImplicitFunction. If list it must contains the
        parameter for the predefined implicit functions:

        -  method ==  `plane` : a point and normal vector defining the cutting plane.
        -  method ==  `sphere` :  center and radius defining a sphere.
        -  method ==  `box`  : either a 4x4 matrix to apply affine transformation (not yet implemented)
            or a box (cuboid) defined by 4 points, a formex or a mesh. See _vtkBox.
        -  method ==  `boxplanes`  : Coords, Mesh or Formex. Coords array of shape (2,3) specifying
            minimal  and coordinates of the box. Formex or Mesh specifying one hexahedron. See _vtkPlanesBox.
        -  method ==  `planes`  : points :term:`array_like` of shape (npoints,3) and
                normal vectors :term:`array_like` of shape (npoints,3) defining the cutting planes.
        -  method ==  `surface`  : a closed convex manifold trisurface.

    - `method`: str or None. If string allowed values are `plane`, `sphere`,
        `box`, `boxplanes`, `planes`, `surface` to select the correspondent implicit functions by providing the
        `implicitdata` parameters. If None a vtkImplicitFunction must be passed directly
        in `implicitdata`

    Cutting reduces the mesh dimension by one.
    Returns a mesh of points if self is a line2 mesh,
    a mesh of lines if self is a surface tri3 or quad4 mesh,
    a triangular mesh if self is tet4 or hex8 mesh.
    If there is no intersection returns None.
    """
    if method=='plane':
        p, n = implicitdata
        return _vtkCutter(self, _vtkPlane(p, n))
    elif method=='sphere':
        c, r = implicitdata
        return _vtkCutter(self, _vtkSphere(c, r))
    # Removed because of missing _vtkBox
    # elif method=='box':
    #     box = implicitdata
    #     return _vtkCutter(self, _vtkBox(box))
    # BV: uncommented both as there are two implementations of 'boxplanes
    # TODO: somebody should fix this
    # elif method=='boxplanes':
    #     box = implicitdata
    #     return _vtkCutter(self, _vtkBoxPlanes(box))
    # elif method=='boxplanes':
    #     utils.warn('warn_vtkboxplanes_removed')
    #     raise ValueError('method boxplanes has been removed, use surface')
    #     # TODO this has to be removed
    elif method=='surface':
        s = implicitdata
        return _vtkCutter(self, _vtkSurfacePlanes(s))
    elif method is None:
        return _vtkCutter(self, implicitdata)
    else:
        raise ValueError('implicit object for cutting not well specified')


def vtkClip(self, implicitdata, method=None, insideout=False):
    """Clip (split) a Mesh with plane(s), a sphere or a box.

    Parameters:

    - `self`: a Mesh.
    - `implicitdata`: list or vtkImplicitFunction. If list it must contains the
        parameter for the predefined implicit functions:

        -  method ==  `plane` : a point and normal vector defining the cutting plane.
        -  method ==  `sphere` :  center and radius defining a sphere.
        -  method ==  `box`  : either a 4x4 matrix to apply affine transformation (not yet implemented)
            or a box (cuboid) defined by 4 points, a formex or a mesh. See _vtkBox.
        -  method ==  `boxplanes`  : Coords, Mesh or Formex. Coords array of shape (2,3) specifying
            minimal  and coordinates of the box. Formex or Mesh specifying one hexahedron. See _vtkPlanesBox.
        -  method ==  `planes`  : points :term:`array_like` of shape (npoints,3) and
                normal vectors :term:`array_like` of shape (npoints,3) defining the cutting planes.
        -  method ==  `surface`  : a closed convex manifold trisurface.

    - `method`: str or None. If string allowed values are `plane`,`planes`, `sphere`,
        `box` to select the correspondent implicit functions by providing the
        `implicitdata` parameters. If None a vtkImplicitFunction must be passed directly
        in `implicitdata`
    - `insideout`:boolean or an integer with values 0 or 1 to choose which side of the mesh should be returned.

    Clipping does not reduce the mesh dimension.
    Returns always a list of meshes, each one having the same element type.
    None is returned if a mesh does not exist (e.g. clipping with a box which is outside the mesh).
    The mesh density can influence the clipping results, especially with solid elements.
    In this case the corner of the implicit function can be smoothed resulting in wrong clipping at these
    locations.
    """
    if method=='plane':
        p, n = implicitdata
        return _vtkClipper(self, _vtkPlane(p, n), insideout)
    elif method=='sphere':
        c, r = implicitdata
        return _vtkClipper(self, _vtkSphere(c, r), insideout)
    # elif method=='box':
    #     box = implicitdata
    #     return _vtkClipper(self, _vtkBox(box), insideout)
    elif method=='boxplanes':
        utils.warn('warn_vtkboxplanes_removed')
        # TODO this has to be removed
        raise ValueError('method boxplanes has been removed, use surface')
    elif method=='planes':
        p, n = implicitdata
        return _vtkClipper(self, _vtkPlanes(p, n), insideout)
    elif method=='surface':
        s = implicitdata
        return _vtkClipper(self, _vtkSurfacePlanes(s), insideout)
    elif method is None:
        return _vtkClipper(self, implicitdata, insideout)
    else:
        raise ValueError('implicit object for cutting not well specified')


def distance(self, ref, normals=None, loctol=1e-3, normtol=1e-5, return_cellids=False):
    """Computes the distance of object from a reference object ref

    Parameters:

    - `self`: any pyFormex Geometry or Coords object.
    - `ref`: any pyFormex Geometry or Coords object.
    - `normals`: arraylike of shape (ncoords,3). Normals at each vertex of ref.
        If not specified, otherwise normals are computed using vtkPolyDataNormals.
    - `loctol`: float. Tolerance for the locator precision.
    - `normtol`: float. Tolerance for the signed distance vector.
    - `return_cellids`: boolean. If True an array containing the cell ids of the `ref`
        closest to each point of `self`


    Returns a tuple with the distances, distance vectors, and signed distances.

    """
    point = np.zeros([3])

    self = convert2VPD(self, clean=False)
    ref = convert2VPD(ref, clean=False)
    npts = self.GetNumberOfPoints()

    if normals is not None:
        normals=numpy_to_vtk(normals)
    else:
        normals=vtk.vtkPolyDataNormals()
        normals.ComputeCellNormalsOn()
        normals.SetInputData(ref)
        normals = Update(normals)
        normals = normals.GetOutput().GetCellData().GetNormals()


    loc = vtk.vtkCellLocator()
    loc.SetDataSet(ref)
    loc.SetTolerance(loctol)
    loc.BuildLocator()
    loc=Update(loc)

    dist=[[], [], []]
    cellnids=[]
    nxcell=[]
    hitcellid=[]

    for i in range(npts):
        self.GetPoint(i, point)
        celltmp = vtk.vtkGenericCell()
        cellidtmp = vtk.mutable(0)
        subid = vtk.mutable(0)
        disttmp = vtk.mutable(0.)
        closestPoint = np.zeros([3])
        loc.FindClosestPoint(point, closestPoint, celltmp, cellidtmp, subid, disttmp)

        distanceVector = closestPoint-point
        distance = at.length(distanceVector)

        dist[0].append(distance)
        dist[1].append((distanceVector).tolist())

        cellnids.append(int(cellidtmp))
        #~ hitcellid.append(loc.FindCell(closestPoint)

        if normals is not None:
            nxcell.append(normals.GetTuple3(cellnids[-1]))

    dist[2] = np.asarray(dist[0]).copy()
    nxcell = np.asarray(nxcell)
    cellnids = np.asarray(cellnids)
    hitcellid = np.asarray(hitcellid)

    if normals is not None:
        dist[2][np.where(at.dotpr(nxcell, dist[1])<=normtol)] *= -1

    dist=[np.asarray(d) for d in dist]
    if not(return_cellids):
        return dist
    else:
        return dist, cellnids

def meshQuality(self, measure):
    """Compute the quality of the elements using a given metric.

    Parameters:

    - `self`: a Geometry object.

    - `measure`: string defining the quality measure.
      This parameter needs to complete the vtk command with the correct
      capitalization.

    For the allowed quality metrics check :
    http://www.vtk.org/doc/nightly/html/classvtkMeshQuality.html

    Example:

    >>> from pyformex.elements import Hex8
    >>> h=Hex8.toMesh()
    >>> meshQuality(h,'MaxAspectFrobenius')
    array([ 1.])

    """
    vtkobj = convert2VTU(self)
    quality = vtk.vtkMeshQuality()
    quality.SetInputData(vtkobj)
    elname = re.split("\d+", self.elName())[0].capitalize()
    if elname == 'Tri':
        elname ='Triangle'  # only exception
    eval('quality.Set' + elname + 'QualityMeasureTo' + measure +'()')
    quality = Update(quality)
    return array2N(quality.GetOutput().GetCellData().GetArray('Quality'))


def octree(surf, tol=0.0, npts=1, return_levels = False):
    """Compute the octree structure of the surface.

    Returns the octree structure of surf according to the maximum
    tolerance tol and the maximum number of points npts in each octant.
    It returns an hexahedral mesh containing all levels of the octree
    with property equal to the number of point of the in each region.
    If return_levels is True, it also return a list of integer arrays
    containing the location of all the hehahedroons of each level.

    """
    from pyformex.formex import Formex
    from pyformex.connectivity import Connectivity
    from pyformex.simple import cuboid

    vm = convert2VPD(surf, clean=False)
    loc = vtk.vtkOctreePointLocator()
    loc.SetDataSet(vm)
    loc.SetTolerance(tol)
    loc.SetMaximumPointsPerRegion(npts)

    loc.BuildLocator()
    rep = vtk.vtkPolyData()
    loc = Update(loc)

    regions = []
    ptsinregion = []
    levels = []

    for lf in range(loc.GetNumberOfLeafNodes()):
        bds = np.zeros(6)
        loc.GetRegionBounds(lf, bds)
        bds = bds.reshape(3, 2).T
        region = cuboid(bds[0], bds[1],)
        ptsinregion.append(loc.GetPointsInRegion(lf).GetNumberOfTuples())
        regions.append(region.coords[0])

    regions = Formex(regions).toMesh().setProp(np.asarray(ptsinregion, dtype=int32))
    if not(return_levels):
        loc.FreeSearchStructure()
        del loc
        return regions

    pfrep = []
    for level in range(loc.GetLevel()+1):
        loc.GenerateRepresentation(level, rep)
        reptmp = convertFromVPD(rep)[0]
        reptmp[2] = reptmp[2].reshape(-1, 6*4)[:, (0, 1, 2, 3, 9, 8, 11, 10)]
        reptmp[0] = reptmp[0][Connectivity(reptmp[2]).renumber()[1]]
        lm = Mesh(reptmp[0], reptmp[2])
        centroids = lm.matchCentroids(regions)
        pfrep.append(np.where(centroids>-1))

    loc.FreeSearchStructure()
    del loc

    return regions, pfrep




def delaunay2D(object, alpha=0.0, tol=0.001, offset = 1.25, bound_tri=False, constraints=None):
    """Constructs a 2D Delaunay triangulation from a Coords object or a Geometry.

    Parameters:

    - `object`: Coords or Geometry (or subclasses).
    - `alpha`: float. Specify alpha (or distance) value to control output of this filter.
        If alpha == 0, the output is a convex hull. If non-zero alpha distance value is
        specified will give concave hull.(The notion of alpha value is derived from
        Edelsbrunner's work on "alpha shapes".)
    - `tol`: float. Specify a tolerance to control discarding of closely spaced points.
    - `offset`: float. Specify a multiplier to control the size of the initial, bounding
      Delaunay triangulation.
    - `bound_tri`: boolean. Boolean controls whether bounding triangulation points
      (and associated triangles) are included in the output.
    - `constraints`: Geometry (or subclasses). Specify the source object used
      to specify constrained edges and loops. If set, and lines/polygons are defined, a
      constrained triangulation is created. The lines/polygons are assumed to reference
      points in the input point set (i.e. point ids are identical in the input and source).
      Note that this method does not connect the pipeline. See SetSourceConnection
      for connecting the pipeline.

    Returns a list of Geometry (or subclass).Usually the output is a triangle mesh,
    but if a non-zero alpha distance value is specified the utput may result in arbitrary
    combinations of triangles, lines, and vertices.
    """
    chull = vtk.vtkDelaunay2D()
    chull.SetInputData(convert2VPD(object))
    chull.SetAlpha(alpha)
    chull.SetTolerance(tol)
    chull.SetOffset(offset)
    chull.SetBoundingTriangulation(bound_tri)
    if constraints is not None:
        raise NotImplementedError
    chull = Update(chull)
    chull=convertFromVPD(chull.GetOutput(), samePlex=False)
    coords=chull[0][0]
    elems=chull[0][2].split()
    eltyps=['point', 'line2', 'tri3']
    meshes=[]
    for els in elems:
        meshes.append(Mesh(coords, els, eltype=eltyps[els.shape[1]-1]))
    return meshes


@utils.deprecated_by('convexHull', 'delaunay3D')
def convexHull(object):
    pass


def delaunay3D(object, alpha=0.0, tol=0.001, offset=2.5, bound_tri=False):
    """Constructs a 3D Delaunay triangulation from a Coords object or a Geometry.

    Parameters:

    - `object`: Coords or Geometry (or subclasses).
    - `alpha`: float. Specify alpha (or distance) value to control output of this filter.
        If alpha == 0, the output is a convex hull. If non-zero alpha distance value is
        specified will give concave hull.(The notion of alpha value is derived from
        Edelsbrunner's work on "alpha shapes".)
    - `tol`: float. Specify a tolerance to control discarding of closely spaced points.
    - `offset`: float. Specify a multiplier to control the size of the initial, bounding
      Delaunay triangulation.
    - `bound_tri`: boolean. Boolean controls whether bounding triangulation points
      (and associated triangles) are included in the output.

    Returns a list of Geometry (or subclass).Usually the output is a tetrahedral mesh,
    but if a non-zero alpha distance value is specified the utput may result in arbitrary
    combinations of tetrahedrons, triangles, lines, and vertices.
    """

    chull = vtk.vtkDelaunay3D()
    chull.SetInputData(convert2VPD(object))
    chull.SetAlpha(alpha)
    chull.SetTolerance(tol)
    chull.SetOffset(offset)
    chull.SetBoundingTriangulation(bound_tri)
    chull = Update(chull)
    chull=convertFromVPD(chull.GetOutput(), samePlex=False)
    coords=chull[0][0]
    elems=chull[0][1].split()
    eltyps=['point', 'line2', 'tri3', 'tet4']
    meshes=[]
    for els in elems:
        meshes.append(Mesh(coords, els, eltype=eltyps[els.shape[1]-1]))
    return meshes


# TODO: check if this is needed. Can be replaced with
#       Mesh.convert or TriSurface.remesh or TriSurface.coarsen
def decimate(self, targetReduction=0.5, boundaryVertexDeletion=True):
    """Decimate a surface (both tri3 or quad4) and returns a trisurface

    - `self` : is a tri3 or quad4 surface
    - `targetReduction` : float (from 0.0 to 1.0) : desired number of triangles relative to input number of triangles
    - `boundaryVertexDeletion` : bool : if True it allows boundary point deletion

    """
    from pyformex.trisurface import TriSurface

    vpd = convert2VPD(self, clean=True)  # convert pyFormex surface to vpd
    vpd = convertVPD2Triangles(vpd)
    vpd = cleanVPD(vpd)

    filter = vtk.vtkDecimatePro()
    filter.SetInputData(vpd)
    filter.SetTargetReduction(targetReduction)
    filter.SetBoundaryVertexDeletion(boundaryVertexDeletion)
    filter.PreserveTopologyOn()
    filter = Update(filter)

    vpd = filter.GetOutput()
    vpd = cleanVPD(vpd)

    [coords, cells, polys, lines, verts], fielddata, celldata, pointdata=convertFromVPD(vpd)  # convert vpd to pyFormex surface
    pf.debug(('%d faces decimated into %d triangles'%(self.nelems(), len(polys))), pf.DEBUG.VTK)
    return TriSurface(coords, polys)


# TODO
# add meshes line 2 , vtk handles polylines also with >2 elements conneted to a node
def coarsenPolyLine(self, target=0.5):
    """Coarsen a PolyLine.

    - `self` : PolyLine
    - `target` : float in range [0.0,1.0], percentage of coords to  be reduced.

    Returns a PolyLine with a reduced number of points.
    """
    vpd = convert2VPD(self, clean=True)  # convert pyFormex PolyLine to vpd
    vpd = cleanVPD(vpd)
    filter = vtk.vtkDecimatePolylineFilter()
    filter.SetInputData(vpd)
    filter.SetTargetReduction(target)

    filter = Update(filter)
    vpd = filter.GetOutput()
    vpd = cleanVPD(vpd)

    [coords, cells, polys, lines, verts], fielddata, celldata, pointdata=convertFromVPD(vpd)  # convert vpd to pyFormex surface
    pf.debug(('%d coords decimated into %d coords'%(self.ncoords()-1, len(lines))), pf.DEBUG.VTK)
    return PolyLine(coords)


def findElemContainingPoint(self, pts):
    """Find indices of elements containing points.

    Parameters:

    - `self`: a Mesh (point, line, surface or volume meshes)
    - `pts`: a Coords (npts,3) specifying npts points

    This is experimental!
    Returns an integer array with the indices of the elems containing the points, returns -1 if no cell is found.
    Only one elem index per points is returned, which is probably the one with lower index number.
    VTK FindCell seems not having tolerance in python. However, the user could enlarge (unshrink) all elems.
    Docs on http://www.vtk.org/doc/nightly/html/classvtkAbstractCellLocator.html#a0c980b5fcf6adcfbf06932185e89defb
    """
    vpd = convert2VTU(Mesh(self))
    cellLocator=vtk.vtkCellLocator()
    cellLocator.SetDataSet(vpd)
    cellLocator.BuildLocator()
    cellids = np.array([cellLocator.FindCell(pts[i]) for i in range(len(pts))])
    pf.debug('%d (of %d) points have not been found inside any cell'%(sum(cellids==-1), len(pts)), pf.DEBUG.VTK)
    return cellids


def read_vtk_surface(fn):
    from pyformex.trisurface import TriSurface
    [coords, cells, polys, lines, verts], fielddata, celldata, pointdata = readVTKObject(fn)
    if cells is None:
        data = (coords, polys)
    elif polys is None:
        data = (coords, cells)
    else:
        raise "Both polys and cells are in file %s"%fn
    if 'prop' in celldata.keys():
        kargs = {'prop': celldata['prop']}
    return TriSurface(*data)


def import3ds(fn, vtkcolor='color'):
    """Import an object from a .3ds file and returns a list of colored meshes.

    It reads and converts a .3ds file into a list of colored meshes,
    by using vtk as intermediate step.

    Parameters:

    - `fn`: filename (.3ds or .3DS)
    - `vtkcolor`: select which color to read from the vtk class: `color` or `specular`.
     The class vtkOpenGLProperty has multiple fields with colors.

    Free 3D galleries are
    archive3d.net
    archibase.net
    """
    importer = vtk.vtk3DSImporter()
    #~ importer.ComputeNormalsOn()
    importer.SetFileName(fn)
    importer.Read()
    ren = importer.GetRenderer()
    actors=ren.GetActors()
    ML = []
    for i in range(0, actors.GetNumberOfItems()):
        act=actors.GetItemAsObject(i)
        if vtk.VTK_MAJOR_VERSION <= 5:
            act.GetNextPart()
        else:
            act.GetBounds()
        propOfActor = act.GetProperty()  # print (dir(propOfActor))#print list the methods to extract the 3ds such as camera settings and colors.
        if vtkcolor == 'color':
            col = propOfActor.GetColor()  # also camera and other things can be extracted!!
        elif vtkcolor == 'specular':
            col = propOfActor.GetSpecularColor()
        else:
            raise ValueError('the color you selected is not yet implemented')
        obj = act.GetMapper()
        obj = obj.GetInputAsDataSet()
        obj = Update(obj)
        [coords, cells, polys, lines, verts], fielddata, celldata, pointdata = convertFromVPD(vpd=obj, samePlex=True)
        m = Mesh(coords, polys)
        m.attrib(color=col)
        ML.append(m)
    pf.debug('model contains %d objects with a total of %d triangles'%(len(ML), Mesh.concatenate(ML).nelems()), pf.DEBUG.VTK)
    return ML


def install_trisurface_methods():
    """Install extra TriSurface methods

    """
    from pyformex import trisurface
    trisurface.TriSurface.decimate = decimate
    trisurface.TriSurface.findElemContainingPoint = findElemContainingPoint

def install_mesh_methods():
    """Install extra Mesh methods

    """
    from pyformex import mesh
    mesh.Mesh.vtkCut = vtkCut
    mesh.Mesh.vtkClip = vtkClip

install_trisurface_methods()
install_mesh_methods()

# End
