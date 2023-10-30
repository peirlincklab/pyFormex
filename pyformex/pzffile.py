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

"""A multifunctional file format for saving pyFormex geometry or projects.

This module defines the PzfFile class which is the new implementation of
the PZF file format.
"""
import time
import json
import zipfile
import re

import numpy as np

import pyformex as pf
from pyformex import utils
from pyformex.path import Path

__all__ = ['PzfFile']

_pzf_version = '2.0'
_text_encoding = 'utf-8'
_metafile = '__METADATA'
_dict_formats = ['c', 'j', 'p', 'r', 'P']
# locals for eval()
_eval_locals = {'array': np.array, 'int32': np.int32, 'float32': np.float32}

class ClassNotRegistered(Exception):
    pass
class InvalidFilename(Exception):
    pass
class InvalidKey(Exception):
    pass
class InvalidFormat(Exception):
    pass


class Config:
    """A very simple config parser.

    This class contains two static functions: 'dumps' to dump
    a dict to a string, and 'loads' to load back the dict from
    the string.

    The string format is such that it can easily be read and
    edited. Each of the items in the dict is stored on a line
    of the form 'key = repr(value)'. On loading back, each line
    is split on the first appearance of a '='. The first part
    is stripped and used as key, the second part is eval'ed and
    used as value.
    """
    @staticmethod
    def dumps(d):
        """Dump a dict to a string in Config format."""
        D = {}
        for k in d:
            if (not isinstance(k, str) or k.startswith(' ')
                    or k.endswith(' ')):
                print(repr(k))
                raise ValueError("Invalid key for Config")
            v = d[k]
            if isinstance(v, (str, int, float, tuple, list)):
                pass
            elif isinstance(v, np.ndarray):
                v = v.tolist()
            else:
                raise ValueError(
                    f"A value of type {type(v)} can not be serialized "
                    "in Config format")
            D[k] = v
        return '\n'.join([f"{k} = {D[k]!r}" for k in D])

    @staticmethod
    def loads(s):
        """Load a dict from a string in Config format"""
        d = {}
        for line in s.split('\n'):
            if line.startswith('#'):
                continue
            kv = line.split('=', maxsplit=1)
            if len(kv) == 2:
                key = kv[0].strip()
                val = eval(kv[1])
                d[key] = val
        return d

    @staticmethod
    def pzf_load(**kargs):
        return dict(**kargs)


_register = {
    'Config': Config,
    'array': np.asarray,
    'str': str,
    'dict': dict,
}

def register(clas, name=None):
    """Register a class in the pzf i/o module

    A registered class can be exported to a PZF file.

    Returns
    -------
    class
        The provided class is returned, so that this method can be used as
        a decorator. Normally though, one uses the :func:`utils.pzf_register`
        as decorator.
    """
    _ = clas.pzf_dict  # force an AttributeError if no pzf_dict
    _register[name if name else clas.__name__] = clas
    return clas


def dict2str(d, fmt):
    """Nicely format a dict so it can be imported again

    Examples
    --------
    >>> d = {'a': 0, 'b': (0,1), 'c': 'string'}
    >>> print(dict2str(d, 'c'))
    a = 0
    b = (0, 1)
    c = 'string'
    >>> print(dict2str(d, 'j'))
    {"a": 0, "b": [0, 1], "c": "string"}
    >>> print(dict2str(d, 'r'))
    {'a': 0, 'b': (0, 1), 'c': 'string'}
    """
    if fmt == 'c':
        return Config.dumps(d)
    elif fmt == 'j':
        return json.dumps(d)
    elif fmt == 'p':
        import pprint
        return pprint.pformat(d, indent=2, compact=True)
    elif fmt == 'r':
        return repr(d)
    elif fmt == 'P':
        import pickle
        return pickle.dumps(d)


def str2dict(s, fmt):
    """Read a dict from a string representation

    Examples
    --------
    >>> s = "{'a': 0, 'b': (0,1), 'c': 'string'}"
    """
    if fmt == 'c':
        return Config.loads(s)
    elif fmt == 'j':
        return json.loads(s)
    elif fmt in ['p', 'r']:
        val = eval(s, {}, _eval_locals)
        return val
    elif fmt == 'P':
        import pickle
        return pickle.loads(s)


str_decode = {
    'b': lambda s: False if s == 'False' else True,
    'i': int,
    'f': float,
    's': str,
}


def convert_load_1_0(name, clas, attr, val):
    """Convert an item from 1.0 format to 2.0"""
    if name == '_camera':
        clas = 'Camera'
        attr = 'kargs:c'
    elif name == '_canvas':
        clas = 'dict'
        attr = 'dict:c'
    elif attr == 'attrib':
        attr = 'attrib:j'
    elif attr == 'closed':
        # existence means True
        val = True
    elif attr == 'eltype':
        # value is string encoded in name
        attr = 'eltype:s'
        val = ''
    elif attr == 'degree':
        # value is int encoded in name
        attr = 'degree:i'
        val = ''
    return name, clas, attr, val


def split_format_1_0(contents):
    """convert old format string into a metadata dict"""
    s = contents.split(maxsplit=2)
    return {
        'format': s[0],
        'version': s[1],
        'creator': s[2],
    }


def convert_files_1_0(tmpdir):
    """Convert files from 1.0 format to 2.0"""
    for name in tmpdir.filenames():
        if name.startswith('__'):
            # system file: should be skipped
            continue
        text = None
        stem, suffix = name.rsplit('.', maxsplit=1)
        s = stem.split('__')
        if len(s) < 3:
            raise InvalidFilename(name)
        objname, clas, attr = s[:3]
        if objname == '_canvas':
            newname = '_canvas__MultiCanvas__kargs:c.txt'
        elif objname == '_camera':
            newname = '_camera__Camera__kargs:c.txt'
        elif attr == 'attrib':
            newname = utils.rreplace(name, '__attrib.txt', '__attrib:j.txt')
        elif attr == 'closed':
            newname = utils.rreplace(name, '__closed.npy', '__closed:b__True')
            text = ''
        elif attr == 'eltype':
            newname = utils.rreplace(name, '.npy', '')
            newname = utils.rreplace(newname, 'eltype', 'eltype:s')
            text = ''
        elif attr == 'degree':
            newname = utils.rreplace(name, '.npy', '')
            newname = utils.rreplace(newname, 'degree', 'degree:i')
            text = ''
        else:
            newname = name
        # convert to format 2 separators
        s = newname.split('__')
        dirname = ':'.join(s[:2])
        newname = '__'.join(s[2:])
        newname = f"{dirname}/{newname}"
        path = tmpdir / name
        if text is not None:
            path.write_text(text)
        print(f"{name} ---> {newname}")
        newpath = tmpdir / newname
        newpath.parent.mkdir(exist_ok=True)
        path.move(newpath)


def load_object(clas, kargs):
    """Restore an object from the kargs read from file"""
    pf.verbose(3, f"Loading {clas}")
    # if clas == 'dict':
    #     return kargs.get('dict', {})
    Clas = _register.get(clas, None)
    if Clas is None:
        raise ClassNotRegistered(f"Objects of class '{clas}' can not be loaded")
    # Get the positional arguments
    args = [kargs.pop(arg) for arg in getattr(Clas, 'pzf_args', [])]
    pf.verbose(3, f"Got {len(args)} args, kargs: {list(kargs.keys())})")
    if hasattr(Clas, 'pzf_load'):
        O = Clas.pzf_load(*args, **kargs)
    else:
        O = Clas(*args, **kargs)
    return O


def zipfile_write_array(zipf, fname, val, datetime=None, compress=True):
    """Write a numpy array to an open ZipFile

    Parameters
    ----------
    zipf: ZipFile
        A ZipFIle that is open for writing.
    fname: str
        The filename as it will be set in the zip archive.
    val: ndarray
        The data to be written into the file. It should be a numpy.ndarray
        or data that can be converted to one.
    datetime: tuple, optional
        The date and time mark to be set on the file. It should be a tuple
        of 6 ints: (year, month, day, hour, min, sec). If not provided,
        the current date/time is used.
    compress: bool, optional
        If True, the data will be compressed with the zipfile.ZIP_DEFLATED
        method.
    """
    if datetime is None:
        datetime = time.localtime(time.time())[:6]
    val = np.asanyarray(val)
    zinfo = zipfile.ZipInfo(filename=fname, date_time=datetime)
    if compress:
        zinfo.compress_type = zipfile.ZIP_DEFLATED
    with zipf._lock:
        with zipf.open(zinfo, mode='w', force_zip64=True) as fil:
            np.lib.format.write_array(fil, val)


class PzfFile:
    """An archive file in PZF format.

    PZF stands for 'pyFormex zip format'. A complete description of the
    format and API is given in :ref:`cha:fileformats`.

    This is the implementation of version 2.0 of the PZF file format.
    The format has minor changes from the (unpublished) 1.0 version
    and is able to read (but not write) the older format.

    A PZF file is actually a ZIP archive, written with the standard Python
    ZipFile module. Thus, its contents are individual files. In the
    current format 2.0, the PzfFile writer creates only three types of files,
    marked by their suffix:

    - .npy: a file containing a single NumPy array in Numpy's .npy format;
    - .txt: a file containing text in a utf-8 encoding;
    - no suffix: an empty file: the info is in the file name.

    The filename carry important information though. Usually they follow the
    scheme name__class__attr, where name is the object name, class the object's
    class name (to be used on loading) and attr is the name of the attribute
    that has its data in the file. Files without suffix have their information
    in the filename.

    Saving objects to a PZF file is as simple as::

        PzfFile(filename).save(**kargs)

    Each of the keyword arguments provided specifies an object to be saved
    with the keyword as its name.

    To load the objects from a PZF file, do::

        dic =  PzfFile(filename).load()

    This returns a dict containing the pyFormex objects with their names as
    keys.

    Limitations: currently, only objects of the following classes can be stored:
    str, dict, numpy.ndarray,
    Coords, Formex, Mesh, TriSurface, PolyLine, BezierSpline, CoordSys,
    Camera, Canvas settings.
    Using the API (see :ref:`cha:fileformats`) this can however
    easily be extended to any other class of objects.

    Parameters
    ----------
    filename: :term:`path_like`
        Name of the file from which to load the objects.
        It is normally a file with extension '.pzf'.


    Notes
    -----
    See also the example SaveLoad.

    """
    def __init__(self, filename):
        self.filename = Path(filename)
        self.meta = {}
        self.legacy = False

    @property
    @utils.memoize
    def _sep1(self):
        return '__' if self.legacy else ':'

    @property
    @utils.memoize
    def _sep2(self):
        return '__' if self.legacy else '/'

    @property
    @utils.memoize
    def RE_filename(self):
        # file name format:  name:clas/key[.suffix]
        return re.compile(
            rf'^(?P<name>[^/]+?){self._sep1}'
            rf'(?P<clas>[^/]+?){self._sep2}'
            rf'(?P<key>[^/.]+)'
            rf'(?P<suffix>\.[^.]+)?$')


    ###############################################
    ## WRITING ##

    def write_metadata(self, zipf, compress):
        """Write the metadata"""
        zipf.writestr(f"__FORMAT__PZF__{_pzf_version}", '')
        meta = {
            'format': 'PZF',
            'version': _pzf_version,
            'creator': pf.fullVersion(),
            'datetime': time.localtime(time.time())[:6],
            'compress': compress,
        }
        # Currently write meta data in a file and comments
        zipf.writestr(_metafile, Config.dumps(meta))
        # zipf.comment = meta.encode(_text_encoding)
        self.meta = meta


    # TODO:
    # - use a single 'open' method
    # - zipf attribute or subclass PzfFile from ZipFile ?
    # - mode 'r' : read meta
    # - mode 'w' : write meta
    # - mode 'a' : read format and check
    # - mode 'x' : check that file does not exist

    def write_files(self, savedict, *, compress=True, mode='w'):
        """Save a dict to a PZF file

        Parameters
        ----------
        savedict: dict
            Dict with object attributes to store. The keys are subdirectory
            names in objname:classname format. The values are dicts with
            the indiviudal filenames as keys and values that are either str,
            dict or array_like.
        """
        if mode=='a':
            with zipfile.ZipFile(self.filename, mode='r') as zipf:
                info = self.read_format(zipf)
                if info['version'] != _pzf_version:
                    raise InvalidFormat(
                        "Appending to a PZF file requires a version match\n"
                        f"Current version: {_pzf_version}, "
                        f"PZF file version: {info['version']}\n")

        with zipfile.ZipFile(self.filename, mode=mode) as zipf:
            if mode != 'a':
                self.write_metadata(zipf, compress)
            for obj in savedict:
                for key, val in savedict[obj].items():
                    if isinstance(val, dict):
                        if len(key) > 1 and key[-2] == ':':
                            fmt = key[-1]
                            if fmt not in _dict_formats:
                                valid = ':' + ', :'.join(_dict_formats)
                                raise ValueError(
                                    "pzf_dict: invalid key for a dict type, "
                                    f"expected a modifier ({valid})")
                            val = dict2str(val, fmt)
                    fname = f"{obj}{self._sep2}{key}"
                    if val is None:
                        zipf.writestr(fname, '')
                    elif isinstance(val, str):
                        zipf.writestr(fname+'.txt', val)
                    else:
                        zipfile_write_array(
                            zipf, fname+'.npy', val, datetime=self.meta['datetime'],
                            compress=compress)


    def save(self, _camera=False, _canvas=False, _compress=True, _append=False,
             **kargs):
        """Save pyFormex objects to the PZF file.

        Parameters
        ----------
        kargs: keyword arguments
            The objects to be saved. Each object will be saved with a name
            equal to the keyword argument. The keyword should not end with
            an underscore '_', nor contain a double underscore '__'. Keywords
            starting with a single underscore are reserved for special use
            and should not be used for any other object.

        Notes
        -----
        Reserved keywords:
        - '_camera': stores the current camerasettings
        - '_canvas': stores the full canvas layout and camera settings
        - '_compress'

        Examples
        --------
        >>> with utils.TempDir() as d:
        ...     pzf = PzfFile(d / 'myzip.pzf')

        See also example SaveLoad.

        """
        pf.verbose(1, f"Write {'compressed ' if _compress else ''}"
                   f"PZF file {self.filename.absolute()}")
        savedict = {}
        if _camera:
            kargs['_camera'] = pf.canvas.camera
        if _canvas:
            kargs['_canvas'] = pf.GUI.viewports
            if '_camera' in kargs:
                # Do not store camera if we have canvas
                del kargs['_camera']
        for name in kargs:
            if name.endswith('_') or '__' in name or name=='':
                raise InvalidKey(f"Invalid object name '{name}' for savePZF")
            obj = kargs[name]
            clas = obj.__class__.__name__
            if clas == 'ndarray':
                clas = 'array'
                d = {'a': obj}
            elif clas == 'str':
                d = {'object': obj}
            elif clas == 'dict':
                d = {'kargs:p': obj}
            else:
                try:
                    d = obj.pzf_dict()
                except Exception as e:
                    print(e)
                    pf.verbose(
                        1, f"!! Object {name} of type {type(obj)} can not (yet) "
                        f"be written to PZF file: skipping it.")
                    continue
            obj = f"{name}{self._sep1}{clas}"
            savedict[obj] = d
            pf.verbose(2, f"Saving {len(d)} file(s) for object {obj}")
        self.write_files(savedict,
                         compress=_compress, mode='a' if _append else 'w')


    def add(self, **kargs):
        """Add objects to an existing PZF file.

        This is a convenient wrapper of :meth:`save` with the `_add` argument
        set to True.
        """
        return self.save(_add=True, **kargs)


    ###############################################
    ## READING ##

    def read_format(self, zipf):
        """Read the format"""
        info = {}
        for f in zipf.namelist():
            if f.startswith('__FORMAT'):
                pf.verbose(3, f"Reading file format: {f}")
                s = f.split('__')
                if len(s) > 3:
                    info = {
                        'format': s[2],
                        'version': s[3],
                    }
                elif f == '__FORMAT.txt':
                    # read legacy format
                    self.legacy = True
                    contents = zipf.read(f).decode(_text_encoding)
                    info = split_format_1_0(contents)
                break
        if info.get('format', None) != 'PZF':
            raise InvalidFormat(
                f"{self.filename} is not a proper PZF format file.")
        return info


    def read_metadata(self, zipf):
        """Read the metadata"""
        meta = self.read_format(zipf)
        if not self.legacy:
            contents = zipf.read(_metafile).decode(_text_encoding)
            meta.update(Config.loads(contents))
        if 'compress' not in meta:
            meta['compress'] = False
            for info in zipf.infolist():
                if info.compress_type != zipfile.ZIP_STORED:
                    meta['compress'] = True
                    break
        self.meta = meta
        self.comment = zipf.comment
        return meta


    def read_files(self, files=None):
        """Read files from a ZipFile

        Parameters
        ----------
        files: list|str, optional
            A list of filenames to read. Default is to read all files.
            The filenames may contain * and ? wildcards. For convenience,
            a single string may be specified and will be put in a list.
            Thus, ``read_files('F:*')`` will read all files related to the object
            named 'F'.

        Returns
        -------
        dict
            A dict with the filenames as keys and the interpreted
            file contents as values. Files ending in '.npy' are returned
            as a numpy array. Files ending in '.txt' are returned as a
            (multiline) string except if the stem of the filename ends
            in one of ':c', ':j' or ':r', in which case a dict is
            returned.

        See Also
        --------
        load: read files and convert the contents to pyFormex objects.
        """
        pf.verbose(2, f"Reading PZF file {self.filename}")
        d = {}
        with zipfile.ZipFile(self.filename, 'r') as zipf:
            try:
                self.read_metadata(zipf)
            except Exception as e:
                print(e)
                raise InvalidFormat(
                    f"Error reading {self.filename}\n"
                    f"This is probably not a proper PZF file.")

            allfiles = zipf.namelist()
            if files is None:
                files = allfiles
            else:
                import fnmatch
                if isinstance(files, str):
                    files = [files]
                files = [f for f in allfiles if
                         any([fnmatch.fnmatch(f, pattern) for pattern in files])]
            for f in files:
                m = self.RE_filename.match(f)
                if not m:
                    # skip system files and unrecognized files
                    if not f.startswith('__'):
                        pf.verbose(2, f"Skipping unrecognized {f}")
                    continue
                pf.verbose(3, f"Reading PZF item {f}")
                pf.verbose(3, f"Groups {m.groups()}")
                name, clas, key, suffix = m.groups()
                if suffix == '.npy':
                    # numpy array in npy format
                    with zipf.open(f, 'r') as fil:
                        val = np.lib.format.read_array(fil)
                elif suffix == '.txt':
                    # text file
                    val = zipf.read(f).decode(_text_encoding)
                else:
                    # empty file
                    val = ''
                s = key.split('__')
                attr = s[0]
                if self.legacy:
                    name, clas, attr, val = convert_load_1_0(name, clas, attr, val)
                if len(attr) > 1 and attr[-2] == ':':
                    # process storage modifiers
                    fmt = attr[-1]
                    attr = attr[:-2]
                    if fmt in _dict_formats:
                        # decode a serialized dict:
                        val = str2dict(val, fmt)
                    elif fmt in str_decode:
                        # val in filename
                        val = str_decode[fmt](s[1])
                pf.verbose(3, f"{name} {type(val)} "
                           f" ({len(val) if hasattr(val, '__len__') else val})")
                if name not in d:
                    d[name] = {'class': clas}
                od = d[name]
                if attr == 'kargs' and isinstance(val, dict):
                    od.update(val)
                elif attr == 'field':
                    if 'fields' not in od:
                        od['fields'] = []
                    od['fields'].append((s[1], s[2], val))
                else:
                    od[attr] = val
        if pf.verbosity(2):
            print(f"Object attributes read from {self.filename}")
            for name in d:
                print(f"{name}: {sorted(d[name].keys())}")
        return d


    def load(self, objects=None):
        """Load pyFormex objects from a file in PZF format

        Parameters
        ----------
        objects: list of str, optional
            A list of specification strings to delimit the objects loaded
            from the PZF file. Each object spec should be in the format
            name:class and can contain * and ? wildcards.
            Thus ``[ 'F:*', 'M*:Mesh' ]`` will load the object named 'F'
            and all objects of class Mesh whose name starts with an 'M'.
            Default is to load all objects contained in the archive.

        Returns
        -------
        dict
            A dict with the objects read from the file. The keys in the dict
            are the object names used when creating the file.

        Notes
        -----
        If the returned dict contains a camera setting, the camera can be
        restored as follows::

            if '_camera' in d:
                pf.canvas.initCamera(d['_camera'])
                pf.canvas.update()

        See also example SaveLoad.

        See Also
        --------
        read: read files and return contents as arrays, dicts and strings.
        """
        if objects:
            if not isinstance(objects, (list, tuple)):
                raise ValueError("Invalid objects specification")
            files = [f"{obj}{self._sep2}*" for obj in objects]
        else:
            files = None

        d = self.read_files(files=files)
        for k in d.keys():
            clas = d[k].pop('class')
            fields = d[k].pop('fields', None)
            attrib = d[k].pop('attrib', None)
            try:
                obj = load_object(clas, d[k])
            except ClassNotRegistered as e:
                print(e)
                print("Skipping this object")
                d[k] = None
                continue
            if fields:
                for fldtype, fldname, data in fields:
                    obj.addField(fldtype, data, fldname)
            if attrib:
                obj.attrib(**attrib)
            if obj is None:
                del d[k]
            else:
                d[k] = obj
        return d


    ###############################################
    ## OTHER ##

    def version(self):
        """Get the version of the PZF format"""
        with zipfile.ZipFile(self.filename, 'r') as zipf:
            return self.read_format(zipf)['version']


    def metadata(self):
        """Get metadata from a ZipFile

        """
        with zipfile.ZipFile(self.filename, 'r') as zipf:
            self.read_metadata(zipf)
        return self.meta


    # @utils.memoize
    def files(self):
        """Return a list with the filenames"""
        with zipfile.ZipFile(self.filename, 'r') as zipf:
            return zipf.namelist()


    # @utils.memoize
    def objects(self):
        """Return a list with the objects stored in the PZF files"""
        names = []
        for f in self.files():
            m = self.RE_filename.match(f)
            if m:
                obj = f"{m[1]}{self._sep1}{m[2]}"
                if obj not in names:
                    names.append(obj)
        return names


    def extract(self, path, files=None):
        """Extract the PzfFile to the give path

        Parameters
        ----------
        path: :term:`path_like`
            Path of the directory where the PZF file should be extracted.
        files: list of str, optional
            The list of files to extract. Default is to extract all files.

        See also
        --------
        zip: zip the files in a directory into a PZF archive
        """
        with zipfile.ZipFile(self.filename, 'r') as zipf:
            self.read_metadata(zipf)
            zipf.extractall(path, files)


    def zip(self, path, files=None, compress=True):
        """Zip files from a given path to a PzfFile

        Parameters
        ----------
        path: :term:`path_like`
            Path of a directory with PZF file contents. This will normally
            be a directory where a PZF file was previously extracted.
        files: list of str, optional
            The list of files to zip. The file names are relative to path.
            Default is to zip all files in path.

        Note
        ----
        This can be used in cli mode on an extracted PZF file.
        For example, if a PZF file was extracted to s folder 'out',
        that folder can be zipped back into a PZF file with the command::

            pyformex -c 'PzfFile("new.pzf").zip("out")'

        See also
        --------
        extract: extract the files from a PZF archive
        """
        path = Path(path)
        if files is None:
            files = path.listTree()
        with zipfile.ZipFile(self.filename, 'w') as zipf:
            self.write_metadata(zipf, compress)
            for f in files:
                if f.startswith('__'):
                    continue
                if compress and f.endswith('.npy'):
                    compress_type = zipfile.ZIP_DEFLATED
                else:
                    compress_type = zipfile.ZIP_STORED
                zipf.write(path / f, arcname=f, compress_type=compress_type)


    def convert(self, filename=None, compress=None):
        """Convert a PZF file to the current format.

        Parameters
        ----------
        compress: bool
            Specifies whether the converted file should use compression.
            If not provided, compression will be used if the old file did.
        filename: str, optional
            Optional name of the output pzf file. This is useful if you
            want to keep the original file.
            If not provided, the converted file will replace the original.
        compress: bool, optional
            Specify whether the output pzf should use compression or not.
            The default is to use compression if the original was compressed.

        Notes
        -----
        Newer versions can convert files written with older versions,
        but the reverse is not necessarily True.

        convert can also be used to compress a previously uncompressed
        PZF file of the same version.
        """
        if self.metadata()['version'] == _pzf_version:
            pf.verbose(1, f"{self.filename} is already version {_pzf_version}")
            return
        with utils.TempDir() as tmpdir:
            self.extract(tmpdir)
            if compress is None:
                compress=self.meta['compress']
            if self.legacy:
                convert_files_1_0(tmpdir)
            if filename:
                self.filename = filename
            self.zip(tmpdir, compress=compress)


    def removeFiles(self, *files):
        """Remove selected files from the archive"""
        from .software import External
        if not files:
            return
        External.require('zip')
        args = ('zip', '-d', self.filename) + files
        P = utils.command(args)
        return P


    def remove(self, *objects):
        """Remove the named objects from the archive

        Parameters
        ----------
        *objects: sequence of str
            One or more strings specifying the objects to be removed
            from the PZF file. Each object spec should be in the format
            name:class (as returned by :meth:`objects`) and can contain
            * and ? wildcards.
            Thus ``remove('F*', '*:Mesh')`` will remove all objects
            whose name starts with an F or that are of class Mesh.
        """
        self.removeFiles(*(f"{obj}{self._sep2}*" for obj in objects if obj))


    def read_file(self, filename):
        """Return the contents of a text file from the zip archive"""
        with zipfile.ZipFile(self.filename, 'r') as zipf:
            if filename.endswith('.txt'):
                return zipf.read(filename).decode(_text_encoding)
            else:
                return ''


# Not yet deprecated

# @utils.deprecated_by('savePZF(filename, kargs)', 'PzfFile(filename).save(kargs)')
def savePZF(filename, **kargs):
    PzfFile(filename).save(**kargs)

# @utils.deprecated_by('loadPZF(filename)', 'PzfFile(filename).load()')
def loadPZF(filename):
    return PzfFile(filename).load()

# End
