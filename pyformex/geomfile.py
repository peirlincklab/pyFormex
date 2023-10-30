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

"""Export/import of files in pyFormex's native PGF format

This module defines a class to work with files in the native
pyFormex Geometry File (PGF) format.
"""

import re

import numpy as np

import pyformex as pf
from pyformex.software import SaneVersion as Version
from pyformex import Path
from pyformex import utils
from pyformex import filewrite
from pyformex import arraytools as at
from pyformex.formex import Formex
from pyformex.mesh import Mesh
# We need to import the Mesh subclasses that can be read !
from pyformex.trisurface import TriSurface

__all__ = ['GeometryFile']

class GeometryFile():
    """A class to handle files in the pyFormex Geometry File format.

    The pyFormex Geometry File (PGF) format allows the persistent storage
    of most of the geometrical objects available in pyFormex using a format
    that is independent of the pyFormex version. It guarantees a possible read
    back in future versions. The format is simple and public, and hence
    also allows read back from other software.

    See http://pyformex.org/doc/file_format for a full description
    of the file format(s). Older file formats are supported for reading.

    Other than just geometry, the pyFormex Geometry File format can also
    store some attributes of the objects, like names and colors.
    Future versions will also allow to store field variables.

    The GeometryFile class uses the utils.File class to access the files,
    and thus provides for transparent compression and decompression of the
    files. When making use of the compression, the PGF files will remain small
    even for complex models.

    A PGF file starts with a specific header identifying the format and
    version. When opening a file for reading, the PGF header is read
    automatically, and the file is thus positioned ready for reading
    the objects. When opening a file for writing (not appending!), the
    header is automatically written, and the file is ready for writing objects.

    In append mode however, nothing is currently done with the header.
    This means that it is possible to append to a file using a format
    different from that used to create the file initially. This is not a
    good practice, as it may hinder the proper read back of the data.
    Therefore, append mode should only be used when you are sure that
    your current pyFormex uses the same format as the already stored file.
    As a reminder, warning is written when opening the file in append mode.

    The `filename`, `mode`, `compr`, `level` and `delete_temp` arguments are
    passed to the utils.File class. See :class:`utils.File` for more
    details.

    Parameters
    ----------
    filename: :term:`path_like`
        The name of the file to open. If the file name ends with '.gz' or
        '.bz2', transparent (de)compression will be used, as provided by
        the :class:`utils.File` class.
    mode: 'rb', 'wb' or 'ab'
        Specifies that the file should be opened in read, write or append mode
        respectively. If omitted, an existing file will be opened in read mode
        and a non-existing in write mode. Opening an existing file in 'wb' mode
        will overwrite the file, while opening it in 'ab' mode will allow to
        append to the file.
    compr: 'gz' or 'bz2'
        The compression type to be used: gzip or bzip2. If the file name is
        ending with '.gz' or '.bz2', this is set automatically from the
        suffix.
    level: int 1..9
        Compression level for gzip/bzip2. Higher values result in smaller
        files, but require longer compression times. The default of 5 gives
        already a fairly good compression ratio.
    delete_temp: bool
        If True (default), the temporary files needed to do the (de)compression
        are deleted when the GeometryFile is closed.
    sep: str
        Separator string to be used when writing numpy arrays to the file.
        An empty string will make the arrays being written in
        binary format. Any other string will force text mode, and the ``sep``
        string is used as a separator between subsequent array elements.
        See also :func:`numpy.tofile`.
    ifmt: str
        Format for integer items. If provided, and sep is not empty, arrays
        will be written as in line per line text mode.
        If None (default), arrays are written as a single block, which
        resulting in very long lines.
    ffmt: str
        Format for float items. If provided, and sep is not empty, arrays
        will be written as in line per line text mode.
        If None (default), arrays are written as a single block, which
        resulting in very long lines.
    version: str
        Version of PGF format to use when writing. Currently available are
        '1.9', '2.0', '2.1'. The default is '2.1'.

    """

    _version_ = '2.1'

    # Changes in 2.1:
    # Always open files in binary mode (whether arrays are written
    # as text or as binary blobs)

    def __init__(self, filename, mode=None, compr=None, level=5,
                 delete_temp=True, sep=' ', ifmt=None, ffmt=None, version=None):
        """Create the GeometryFile object."""
        filename = Path(filename)
        if version is None:
            version = GeometryFile._version_
        if version not in ['1.9', '2.0', '2.1']:
            raise ValueError(f"Can not read/write GeometryFile "
                             f"of version {version}")
        self.version = version

        if mode is None:
            if filename.exists():
                mode = 'rb'
            else:
                mode = 'wb'
        # Always force binary mode
        if 'b' not in mode:
            mode += 'b'

        # Check final mode
        if mode not in ['rb', 'wb', 'ab']:
            raise ValueError(f"Invalid file  open mode {mode} ")

        pf.debug(f"Opening PGF file {filename} in {mode} mode", pf.DEBUG.PGF)
        self.file = utils.File(filename, mode, compr, level, delete_temp)
        self._autoname = None

        if self.writing:
            self.sep = sep
            self.fmt = {'i': ifmt, 'f': ffmt}

        self.open()


    def readline(self):
        """Read a line from the file"""
        s = self.fil.readline()
        s = s.decode('latin1')  # accepts all 256 bytes as chars
        return s


    def writeline(self, s):
        """Write a text line to the file"""
        if not s.endswith('\n'):
            s += '\n'
        s = s.encode('latin1')  # accepts all 256 bytes as chars
        self.fil.write(s)


    @property
    def writing(self):
        return self.file.mode[0:1] in 'wa'


    @property
    def autoname(self):
        if self._autoname is None:
            self._autoname = utils.autoName(utils.projectName(self.file.name))
        return self._autoname


    def open(self):
        self.fil = self.file.open()
        if self.writing:
            self.writeHeader()
        else:
            self.readHeader()


    def reopen(self, mode='rb'):
        """Reopen the file, possibly changing the mode.

        The default mode for the reopen is 'rb'
        """
        self.fil = self.file.reopen(mode)
        if self.writing:
            self.writeHeader()
        else:
            self.readHeader()


    def close(self):
        """Close the file.

        """
        self.file.close()


    def checkWritable(self):
        if not self.writing:
            raise RuntimeError("File is not opened for writing")
        if not self.header_done:
            self.writeHeader()


    def writeHeader(self):
        """Write the header of a pyFormex geometry file.

        The header identifies the file as a pyFormex geometry file
        and sets the following global values:

        - `version`: the version of the geometry file format
        - `sep`: the default separator to be used when not specified in
          the data block
        """
        self.writeline(f"# pyFormex Geometry File (http://pyformex.org) "
                       f"version='{self.version}'; sep='{self.sep}'")
        self.header_done = True


    def writeData(self, data, sep):
        """Write an array of data to a pyFormex geometry file.

        If fmt is None, the data are written using numpy.tofile, with
        the specified separator. If sep is an empty string, the data block
        is written in binary mode, leading to smaller files.
        If fmt is specified, each
        """
        if not self.writing:
            raise RuntimeError("File is not opened for writing")
        filewrite.writeData(self.fil, data, sep=sep,
                            fmt=self.fmt[data.dtype.kind])
        self.writeline('')  # Add a '\n'


    def write(self, geom, name=None, sep=None):
        """Write a collection of Geometry objects to the Geometry File.

        Parameters
        ----------
        geom: object
            An object of one the supported Geometry data types
            or a list or dict of such objects, or a WebGL objdict.
            Currently exported geometry objects are
            :class:`Coords`, :class:`Formex`, :class:`Mesh`,
            :class:`PolyLine`, :class:`BezierSpline`.

        Returns
        -------
        int
            The number of objects written.
        """
        self.checkWritable()
        nobj = 0
        if isinstance(geom, dict):
            for name in geom:
                nobj += self.writeGeometry(geom[name], name)
        elif isinstance(geom, list):
            for obj in geom:
                ## if hasattr(obj, 'obj'):
                ##     # This must be a WebGL object dict
                ##     nobj += self.writeDict(obj)
                ## else:
                nobj += self.writeGeometry(obj, sep=sep)
        else:
            nobj += self.writeGeometry(geom, name, sep)

        return nobj


    def writeGeometry(self, geom, name=None, sep=None):
        """Write a single Geometry object.

        Writes a single Geometry object to the Geometry File, using the
        specified name and separator.

        Parameters
        ----------
        geom: a supported Geometry type object
            Currently supported Geometry objects are
            :class:`Coords`, :class:`Formex`, :class:`Mesh`,
            :class:`TriSurface`, :class:`PolyLine`, :class:`BezierSpline`.
            Other types are skipped, and a message is written, but processing
            continues.
        name: str, optional
            The name of the object to be stored in the file.
            If not specified, and the object has an `attrib` dict containing
            a name, that value is used. Else an object name is generated
            from the file name.
            On readback, the object names are used as keys to store the objects
            in a dict.
        sep: str
            The separator to be used for writing this
            object. If not specified, the value given in the constructor will
            be used. This argument allows to override it on a per object base.

        Returns 1 if the object has been written, 0 otherwise.
        """
        self.checkWritable()

        if isinstance(geom, (Formex, Mesh, TriSurface)):
            writefunc = self.writeFMT
        else:
            try:
                writefunc = getattr(self, 'write'+geom.__class__.__name__)
            except Exception as e:
                pf.warning(f"Can not (yet) write objects of type "
                           f"{type(geom)} to geometry file: skipping")
                print(e)
                return 0

        if name is None:
            name = geom.attrib.name
        if name is None:
            name = next(self.autoname)

        try:
            writefunc(geom, name, sep)
        except Exception as e:
            pf.warning(f"Error while writing objects of type "
                       f"{type(geom)} to geometry file: skipping")
            print(e)
            return 0

        if geom.attrib and Version(self.version) >= Version('2.0'):
            try:
                self.writeAttrib(geom.attrib)
            except Exception:
                pf.warning(f"Error while writing objects of "
                           f"type {type(geom)} to geometry file: skipping")
                return 0

        return 1


    def writeFMT(self, F, name=None, sep=None):
        """Write a Formex, Mesh or TriSurface.

        Parameters
        ----------
        F: :class:`Formex`, :class:`Mesh` or :class:`TriSurface`
            The object to be written.
        name: str
            See :meth:`writeGeometry`
        sep: str
            See :meth:`writeGeometry`

        Notes
        -----
        This writes a header line with these attributes and arguments:
        objtype, ncoords, nelems, nplex, props(True/False),
        eltype, normals(True/False), color, sep, name.
        This is followed by the array data for: coords, elems, prop,
        normals, color

        The objtype can/should be overridden for subclasses.
        """
        objtype = F.__class__.__name__
        if objtype not in ['Mesh', 'Formex', 'TriSurface']:
            raise ValueError(f"Invalid object type {objtype}")
        if sep is None:
            sep = self.sep
        hasprop = F.prop is not None
        hasnorm = hasattr(F, 'normals') and \
            isinstance(F.normals, np.ndarray) and \
            F.normals.shape == (F.nelems(), F.nplex(), 3)
        color = None
        colormap = None
        Fc = F.attrib['color']
        if Fc is not None:
            if isinstance(Fc, str):
                color = Fc
            else:
                try:
                    Fc = at.checkArray(Fc, kind='f')
                    colormap = None
                    colorshape = Fc.shape
                except Exception:
                    Fc = at.checkArray(Fc, kind='i')
                    colormap = 'default'
                    colorshape = Fc.shape + (3,)
                if colorshape == (3,):
                    color = tuple(Fc)
                elif colorshape == (F.nelems(), 3):
                    color = 'element'
                elif colorshape == (F.nelems(), F.nplex(), 3):
                    color = 'vertex'
                else:
                    raise ValueError(f"Incorrect color shape: {str(colorshape)}")

        head = (    # use parentheses to allow string continuation
            f"# objtype='{objtype}'; "
            f"ncoords={F.npoints()}; nelems={F.nelems()}; nplex={F.nplex()}; "
            f"props={hasprop}; normals={hasnorm}; "
            f"color={repr(color)}; sep='{sep}'"
        )
        if name:
            head += f"; name='{name}'"
        if F.elName():
            head += f"; eltype='{F.elName()}'"
        if colormap:
            head += f"; colormap='{colormap}'"
        self.writeline(head)

        # Apply a fix to avoid a fewgl bug
        #
        # pyFormex webgl exporter exports in pgf format.
        # Unfortunately, due to a bug in fewgl pgf reader, geometries
        # having a first value in the coords block that starts with a
        # bit pattern corresponding with a '#' byte, (dec 35), can not
        # be read back. The solution is to force the first bit (the least
        # significant bit of the mantisse) to zero. This will make sure
        # the bit pattern does not match dec 35 ('#'), and have a
        # neglectable influence on the value. (Still the solution below
        # resets the original value).
        if pf.cfg['webgl/avoid_fewgl_read_pgf_bug']:
            save_first = F.coords[0, 0]
            # Force least significant bit of the first byte to zero
            F.coords.view(np.int32)[0, 0] &= -2
        self.writeData(F.coords, sep)
        if pf.cfg['webgl/avoid_fewgl_read_pgf_bug']:
            F.coords[0, 0] = save_first

        if not objtype == 'Formex':
            self.writeData(F.elems, sep)
        if hasprop:
            self.writeData(F.prop, sep)
        if hasnorm:
            self.writeData(F.normals, sep)
        if color == 'element' or color == 'vertex':
            self.writeData(Fc, sep)
        for field in F.fields:
            fld = F.fields[field]
            self.writeline(f"# field='{fld.fldname}'; fldtype='{fld.fldtype}'; "
                           f"shape={repr(fld.data.shape)}; sep='{sep}'")
            self.writeData(fld.data, sep)


    def writeCurve(self, F, name=None, sep=None, objtype=None, extra=None):
        """Write a Curve to a pyFormex geometry file.

        This function writes any curve type to the geometry file.
        The `objtype` is automatically detected but can be overridden.

        The following attributes and arguments are written in the header:
        ncoords, closed, name, sep.
        The following attributes are written as arrays: coords
        """
        if sep is None:
            sep = self.sep
        head = (f"# objtype='{F.__class__.__name__}'; "
                f"ncoords={F.coords.shape[0]}; "
                f"closed={ F.closed}; sep='{sep}'")
        if name:
            head += f"; name='{name}'"
        if extra:
            head += extra
        self.writeline(head)
        self.writeData(F.coords, sep)


    def writePolyLine(self, F, name=None, sep=None):
        """Write a PolyLine to a pyFormex geometry file.

        This is equivalent to writeCurve(F,name,sep,objtype='PolyLine')
        """
        self.writeCurve(F, name=name, sep=sep, objtype='PolyLine')


    def writeBezierSpline(self, F, name=None, sep=None):
        """Write a BezierSpline to a pyFormex geometry file.

        This is equivalent to writeCurve(F,name,sep,objtype='BezierSpline')
        """
        self.writeCurve(F, name=name, sep=sep, objtype='BezierSpline',
                        extra=f"; degree={F.degree}")


    def writeNurbsCurve(self, F, name=None, sep=None, extra=None):
        """Write a NurbsCurve to a pyFormex geometry file.

        This function writes a NurbsCurve instance to the geometry file.

        The following attributes and arguments are written in the header:
        ncoords, nknots, closed, name, sep.
        The following attributes are written as arrays: coords, knots
        """
        if sep is None:
            sep = self.sep
        head = (f"# objtype='{F.__class__.__name__}'; "
                f"ncoords={F.coords.shape[0]}; nknots={F.knots.shape[0]}; "
                f"closed={F.closed}; sep='{sep}'")
        if name:
            head += f"; name='{name}'"
        if extra:
            head += extra
        self.writeline(head)
        self.writeData(F.coords, sep)
        self.writeData(F.knots, sep)


    def writeNurbsSurface(self, F, name=None, sep=None, extra=None):
        """Write a NurbsSurface to a pyFormex geometry file.

        This function writes a NurbsSurface instance to the geometry file.

        The following attributes and arguments are written in the header:
        ncoords, nknotsu, nknotsv, closedu, closedv, name, sep.
        The following attributes are written as arrays: coords, knotsu, knotsv
        """
        if sep is None:
            sep = self.sep
        head = (f"# objtype='{F.__class__.__name__}'; "
                f"ncoords={F.coords.shape[0]}; nuknots={F.uknots.shape[0]}; "
                f"nvknots={F.vknots.shape[0]}; "
                f"uclosed={F.closed[0]}; vclosed={F.closed[1]}; sep='{sep}'")
        if name:
            head += f"; name='{name}'"
        if extra:
            head += extra
        self.writeline(head)
        self.writeData(F.coords, sep)
        self.writeData(F.uknots, sep)
        self.writeData(F.vknots, sep)


    def writeAttrib(self, attrib):
        """Write the Attributes block of the Geometry

        Parameters
        ----------
        attrib: :class:`Attributes`
            The Attributes dict of a Geometry object.

        Warning
        -------
        This is work in progress. Not all Attributes can currently
        be stored in the PGF format.
        """
        def filter_attrib(attrib):
            """Filter the storable attributes.

            Currently, only bool, int, float and str types are stored.
            """
            okkeys = [k for k in attrib if (k != 'color')
                      and (isinstance(attrib[k], (bool, int, float, str))
                           or at.isInt(attrib[k])
                           or at.isFloat(attrib[k]))]
            return utils.selectDict(attrib, okkeys)

        # We rely on Attributes __repr__ method, but multiple line
        # representations are coerced to a single line to allow readback

        # Select the exportable attributes
        okattr = filter_attrib(attrib)
        if okattr:
            # In case we would allow array attributes, we need to set
            # numpy printoptions to display the full array, not a truncated one
            with np.printoptions(threshold=np.inf):
                # Get a reversible representation of the attrib dict
                s = repr(filter_attrib(okattr))
            # Remove the newlines, so everything can be read as a single line
            s = re.sub('\n *', '', s)
            # In case arrays are stored, remove the dtype (only int and float
            # dtypes are supported, and type is obvious from the stored values)
            s = re.sub(r', *dtype=[^)]*\)', ')', s)
            # Write the result to the file
            self.writeline(f"# attrib = {s}")


    #######################################################################
    ### READING ###


    def read(self, count=-1, warn_version=True):
        """Read objects from a pyFormex Geometry File.

        This function reads objects from a Geometry File until the file
        ends, or until `count` objects have been read.
        The File should have been opened for reading.

        A count may be specified to limit the number of objects read.

        Returns a dict with the objects read. The keys of the dict are the
        object names found in the file. If the file does not contain
        object names, they will be autogenerated from the file name.

        Note that PGF files of version 1.0 are no longer supported.
        The use of formats 1.1 to 1.5 is deprecated, and users are
        urged to upgrade these files to a newer format. Support for
        these formats may be removed in future.
        """
        if self.writing:
            print("File is opened for writing, not reading.")
            return {}

        self.results = {}
        self.geometry = None  # used to make sure fields follow geom block

        if Version(self.version) < Version('1.6'):
            if warn_version:
                pf.warning(
                    f"This is an old PGF format ({self.version}). "
                    "We recommend you to convert it to a newer format. "
                    "The geometry import menu contains an item to upgrade "
                    "a PGF file to the latest format "
                    f"({GeometryFile._version_}).")
            return self.readLegacy(count)

        while True:
            s = self.readline()

            if len(s) == 0:   # end of file
                break

            if s.startswith('#'):

                # Remove the leading '#' and space
                s = s[1:].strip()

                if s.startswith('objtype'):
                    if count > 0 and len(self.results) >= count:
                        break
                    self.readGeometry(**self.decode(s))

                elif s.startswith('field'):
                    self.readField(**self.decode(s))

                elif s.startswith('attrib'):
                    self.readAttrib(**self.decode(s))

                elif s.startswith('pyFormex Geometry File'):
                    # we have a new header line
                    self.readHeader(s)

            # Unrecognized lines are silently ignored, whether starting
            # with a '#' or not.
            # We recommend to start all comments lines with a '#' though.

        self.file.close()

        return self.results


    def decode(self, s):
        """Decode the announcement line.

        Returns a dict with the interpreted values of the line.
        """
        # Empty dict for return value
        kargs = {}
        # Dict with defined symbols used in the string repr in PGF format
        loc = {'array': np.array}
        try:
            exec(s, loc, kargs)
        except Exception:
            raise RuntimeError(
                "This does not look like a regular pyFormex geometry file. "
                f"I got stuck on the following line:\n==> {s}")
        return kargs


    def readHeader(self, s=None):
        """Read the header of a pyFormex geometry file.

        Without argument, reads a line from the file and interpretes it as
        a header line. This is normally used to read the first line of the
        file. A string `s` may be specified to interprete further lines as
        a header line.
        """
        if s is None:
            s = self.readline()

        pf.debug(f"PGF header line: {s}", pf.DEBUG.PGF)
        pos = s.rfind(')')
        s = s[pos+1:].strip()
        kargs = self.decode(s)
        self.version = kargs['version']
        self.sep = kargs['sep']
        self.header_done = True


    def doHeader(self, version='1.1', sep='', **kargs):
        """Read the header of a pyFormex geometry file.

        Sets detected default values
        """

        self.version = version
        self.sep = sep
        self.header_done = True


    def readGeometry(self, objtype='Formex', name=None, nelems=None,
                     ncoords=None, nplex=None, props=None, eltype=None,
                     normals=None, color=None, colormap=None, closed=None,
                     degree=None, nknots=None, sep=None, size=None, **kargs):
        """Read a geometry record of a pyFormex geometry file.

        If an object was successfully read, it is set in self.geometry
        """
        pf.debug(f"Reading object of type {objtype}", pf.DEBUG.INFO)
        self.geometry = None

        if objtype == 'Formex':
            obj = self.readFormex(nelems, nplex, props, eltype, sep)
        elif objtype in ['Mesh', 'TriSurface']:
            obj = self.readMesh(ncoords, nelems, nplex, props, eltype,
                                normals, sep, objtype)
        # Can not yet write Polygons
        # elif objtype == 'Polygons':
        #     obj = self.readPolygons(ncoords, nelems, size, props, sep)
        elif objtype == 'PolyLine':
            obj = self.readPolyLine(ncoords, closed, sep)
        elif objtype == 'BezierSpline':
            obj = self.readBezierSpline(ncoords, closed, degree, sep)
        elif objtype == 'NurbsCurve':
            obj = self.readNurbsCurve(ncoords, nknots, closed, sep)
        elif objtype in globals() and hasattr(globals()[objtype], 'read_geom'):
            obj = globals()[objtype].read_geom(self, **kargs)
        else:
            obj = None
            print(f"Can not (yet) read objects of type {objtype} "
                  "from geometry file: skipping")

        if obj is not None:
            if color is not None:
                if isinstance(color, str):
                    # Check for special values:
                    if color == 'element':
                        colorshape = (nelems,)
                    elif color == 'vertex':
                        colorshape = (nelems, nplex,)
                    elif color == '':
                        # Fix for pre 1.9 versions using color='' for no color
                        color = colorshape = None
                    else:
                        # string should be a color name
                        colorshape = None

                    if colorshape:
                        if colormap == 'default':
                            colortype = at.Int
                        else:
                            colortype = at.Float
                            colorshape += (3,)

                        try:
                            # Read the color array
                            color = at.readArray(self.fil, colortype,
                                                 colorshape, sep=sep)
                        except Exception as e:
                            print("Invalid color array on PGF file: skipped. "
                                  f"Traceback: {e}")
                            color = None

                else:
                    # A single color encoded in the attribute
                    if colormap == 'default':
                        colortype = 'i'
                    else:
                        colortype = 'f'
                    colorshape = (3,)
                    try:
                        color = at.checkArray(color, colorshape, colortype)
                    except Exception as e:
                        print("Invalid color attribute on PGF file: skipped. "
                              f"Traceback: {e}")
                        color = None

            obj.attrib.color = color

            # store the geometry object, and remember as last
            if name is None:
                name = next(self.autoname)
            self.results[name] = self.geometry = obj


    def readField(self, field=None, fldtype=None, shape=None, sep=None, **kargs):
        """Read a Field defined on the last read geometry.

        """
        data = at.readArray(self.fil, at.Float, shape, sep=sep)
        self.geometry.addField(fldtype, data, field)


    def readAttrib(self, attrib=None, **kargs):
        """Read an Attributes dict defined on the last read geometry.

        """
        try:
            self.geometry.attrib(**attrib)
        except Exception:
            # Attributes readback may produce an error with
            # complex data types, e.g. vertex color array
            pf.warning("GeometryFile.read: Error while reading an Attribute "
                       "block. The current version does not support the "
                       "readback of some complex attribute data types "
                       "(like a vertex color array). All attributes in "
                       "this block will be skipped.")


    def readFormex(self, nelems, nplex, props, eltype, sep):
        """Read a Formex from a pyFormex geometry file.

        The coordinate array for nelems*nplex points is read from the file.
        If present, the property numbers for nelems elements are read.
        From the coords and props a Formex is created and returned.
        """
        ndim = 3
        f = at.readArray(self.fil, at.Float, (nelems, nplex, ndim), sep=sep)
        if props:
            p = at.readArray(self.fil, at.Int, (nelems,), sep=sep)
        else:
            p = None
        return Formex(f, p, eltype)


    def readMesh(self, ncoords, nelems, nplex, props, eltype,
                 normals, sep, objtype='Mesh'):
        """Read a Mesh from a pyFormex geometry file.

        The following arrays are read from the file:
        - a coordinate array with `ncoords` points,
        - a connectivity array with `nelems` elements of plexitude `nplex`,
        - if present, a property number array for `nelems` elements.

        Returns the Mesh constructed from these data, or a subclass if
        an objtype is specified.
        """

        ndim = 3
        x = at.readArray(self.fil, at.Float, (ncoords, ndim), sep=sep)
        e = at.readArray(self.fil, at.Int, (nelems, nplex), sep=sep)
        if props:
            p = at.readArray(self.fil, at.Int, (nelems,), sep=sep)
        else:
            p = None
        M = Mesh(x, e, p, eltype)
        if objtype != 'Mesh':
            try:
                clas = locals()[objtype]
            except Exception:
                clas = globals()[objtype]
            M = clas(M)
        if normals:
            n = at.readArray(self.fil, at.Float, (nelems, nplex, ndim), sep=sep)
            M.normals = n
        return M


    def readPolyLine(self, ncoords, closed, sep):
        """Read a Curve from a pyFormex geometry file.

        The coordinate array for ncoords points is read from the file
        and a Curve of type `objtype` is returned.
        """
        from pyformex.curve import PolyLine
        ndim = 3
        coords = at.readArray(self.fil, at.Float, (ncoords, ndim), sep=sep)
        return PolyLine(control=coords, closed=closed)


    def readBezierSpline(self, ncoords, closed, degree, sep):
        """Read a BezierSpline from a pyFormex geometry file.

        The coordinate array for ncoords points is read from the file
        and a BezierSpline of the given degree is returned.
        """
        from pyformex.curve import BezierSpline
        ndim = 3
        coords = at.readArray(self.fil, at.Float, (ncoords, ndim), sep=sep)
        return BezierSpline(control=coords, closed=closed, degree=degree)


    def readNurbsCurve(self, ncoords, nknots, closed, sep):
        """Read a NurbsCurve from a pyFormex geometry file.

        The coordinate array for ncoords control points and the nknots
        knot values are read from the file.
        A NurbsCurve of degree p = nknots - ncoords - 1 is returned.
        """
        from pyformex.plugins.nurbs import NurbsCurve
        ndim = 4
        coords = at.readArray(self.fil, at.Float, (ncoords, ndim), sep=sep)
        knots = at.readArray(self.fil, at.Float, (nknots,), sep=sep)
        return NurbsCurve(control=coords, knots=knots, closed=closed)


    def readNurbsSurface(self, ncoords, nuknots, nvknots, uclosed, vclosed, sep):
        """Read a NurbsSurface from a pyFormex geometry file.

        The coordinate array for ncoords control points and the nuknots and
        nvknots values of uknots and vknots are read from the file.
        A NurbsSurface of degree ``pu = nuknots - ncoords - 1``  and
        ``pv = nvknots - ncoords - 1`` is returned.
        """
        from pyformex.plugins.nurbs import NurbsSurface
        ndim = 4
        coords = at.readArray(self.fil, at.Float, (ncoords, ndim), sep=sep)
        uknots = at.readArray(self.fil, at.Float, (nuknots,), sep=sep)
        vknots = at.readArray(self.fil, at.Float, (nvknots,), sep=sep)
        return NurbsSurface(control=coords, knots=(uknots, vknots),
                            closed=(uclosed, vclosed))


    #######################################################################
    ### OLD READ FUNCTIONS ###


    def readLegacy(self, count=-1):
        """Read the objects from a pyFormex Geometry File format <= 1.7.

        This function reads all the objects of a Geometry File.
        The File should have been opened for reading, and the header
        should have been read previously.

        A count may be specified to limit the number of objects read.

        Returns a dict with the objects read. The keys of the dict are the
        object names found in the file. If the file does not contain
        object names, they will be autogenerated from the file name.
        """
        if not self.header_done:
            self.readHeader()
        eltype = None  # for compatibility with pre 1.1 .formex files
        while True:
            # !! BEWARE
            # Make sure that all useful variables in the header are
            # reset to defaults, to avoid inheriting values from a
            # previous object
            #
            objtype = 'Formex'  # the default obj type
            obj = None
            nelems = None
            nplex = None
            ncoords = None
            sep = self.sep
            name = None
            normals = None
            color = None
            props = None
            closed = None
            nparts = None
            nknots = None

            s = self.readline()
            if len(s) == 0:   # end of file
                break

            if not s.startswith('#'):  # not a header: skip
                continue

            try:
                exec(s[1:].strip())
                # pf.debug(f"READ COLOR: {str(color)}",pf.DEBUG.INFO)
            except Exception:
                nelems = ncoords = None

            if nelems is None and ncoords is None:
                # For historical reasons, this is a certain way to test
                # that no geom data block is following
                pf.debug(f"SKIPPING {s}", pf.DEBUG.LEGACY)
                continue  # not a legal header: skip

            pf.debug(f"Reading object of type {objtype}", pf.DEBUG.INFO)

            # OK, we have a legal header, try to read data
            if objtype == 'Formex':
                obj = self.readFormex(nelems, nplex, props, eltype, sep)
            elif objtype in ['Mesh', 'TriSurface']:
                obj = self.readMesh(ncoords, nelems, nplex, props, eltype,
                                    normals, sep, objtype)
            elif objtype == 'PolyLine':
                obj = self.readPolyLine(ncoords, closed, sep)
            elif objtype == 'BezierSpline':
                if 'nparts' in s:
                    # This looks like a version 1.3 BezierSpline
                    obj = self.oldReadBezierSpline(ncoords, nparts, closed, sep)
                else:
                    if 'degree' not in s:
                        # compatibility with 1.4  BezierSpline records
                        degree = 3
                    obj = self.readBezierSpline(ncoords, closed, degree, sep)
            elif objtype == 'NurbsCurve':
                obj = self.readNurbsCurve(ncoords, nknots, closed, sep)
            elif objtype in globals() and hasattr(globals()[objtype], 'read_geom'):
                obj = globals()[objtype].read_geom(self)
            else:
                print(f"Can not (yet) read objects of type {objtype} "
                      "from geometry file: skipping")
                continue  # skip to next header


            if obj is not None:
                try:
                    color = at.checkArray(color, (3,), 'f')
                    obj.color = color
                except Exception:
                    pass

                if name is None:
                    name = next(self.autoname)
                self.results[name] = obj

            if count > 0 and len(self.results) >= count:
                break

        self.file.close()

        return self.results


    def oldReadBezierSpline(self, ncoords, nparts, closed, sep):
        """Read a BezierSpline from a pyFormex geometry file version 1.3.

        The coordinate array for ncoords points and control point array
        for (nparts,2) control points are read from the file.
        A BezierSpline of degree 3 is constructed and returned.
        """
        from pyformex.curve import BezierSpline
        ndim = 3
        coords = at.readArray(self.fil, at.Float, (ncoords, ndim), sep=sep)
        control = at.readArray(self.fil, at.Float, (nparts, 2, ndim), sep=sep)
        return BezierSpline(control=at.interleave(
            coords, control[:,0], control[:,1]), closed=closed)


    def rewrite(self):
        """Convert the geometry file to the latest format.

        The conversion is done by reading all objects from the geometry file
        and writing them back. Parts that could not be successfully read will
        be skipped.
        """
        self.reopen('r')
        obj = self.read(warn_version=False)
        self.version = GeometryFile._version_
        if obj is not None:
            self.reopen('w')
            self.write(obj)
        self.close()

# End
