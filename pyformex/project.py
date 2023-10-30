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
"""project.py

Functions for managing a project in pyFormex.
"""
import gzip
import pickle
import importlib

import pyformex as pf
from pyformex import Path
from pyformex import utils

from pyformex.track import TrackedDict

_signature_ = pf.fullVersion()
default_protocol = pickle.DEFAULT_PROTOCOL

module_relocations = {
    'plugins.mesh': 'pyformex.mesh',
    'plugins.surface': 'pyformex.trisurface',
    'plugins.trisurface': 'pyformex.trisurface',
    'pyformex.plugins.mesh': 'pyformex.mesh',
    'pyformex.plugins.surface': 'pyformex.trisurface',
    'pyformex.plugins.trisurface': 'pyformex.trisurface',
}

class_relocations = {
    'coords.Coords': 'pyformex.coords.Coords',
    'coords.BoundVectors': 'pyformex.plugins.alt.BoundVectors',
    'elements.Element': 'pyformex.elements.ElementType',
    'elements.Line2': 'pyformex.elements.Line2',
    'elements.Tri3': 'pyformex.elements.Tri3',
    'elements.Quad4': 'pyformex.elements.Quad4',
    'mesh.Mesh': 'pyformex.mesh.Mesh',
    'formex.Formex': 'pyformex.formex.Formex'
}


def find_class(module, name):
    """Find a class whose name or module has changed"""
    pf.debug(f"I want to import {name} from {module}", pf.DEBUG.PROJECT)
    clas = f"{module}.{name}"
    pf.debug(f"Object is {clas}", pf.DEBUG.PROJECT)
    if clas in class_relocations:
        module = class_relocations[clas]
        lastdot = module.rfind('.')
        module, name = module[:lastdot], module[lastdot+1:]
        pf.debug(f"  I will try {name} from module {module} instead",
                 pf.DEBUG.PROJECT)
    elif module in module_relocations:
        module = module_relocations[module]
        pf.debug(f"  I will try module {module} instead", pf.DEBUG.PROJECT)
    mod = importlib.import_module(module)
    clas = getattr(mod, name)
    pf.debug(f"Success: Got {clas.__class__.__name__}", pf.DEBUG.PROJECT)
    return clas


class Unpickler(pickle.Unpickler):
    """Customized Unpickler class"""

    def __init__(self, f, try_resolve=True):
        """Initialize the Unpickler"""
        pickle.Unpickler.__init__(self, f, encoding='latin1')
        self.try_resolve = try_resolve
        if not try_resolve:
            pf.debug("NOT TRYING TO RESOLVE RELOCATIONS: "
                     "YOU MAY GET INTO TROUBLE", pf.DEBUG.PROJECT)

    def find_class(self, module, name):
        pf.debug(f"FIND MODULE {module} NAME {name}", pf.DEBUG.PROJECT)
        clas = pickle.Unpickler.find_class(self, module, name)
        if not clas:
            clas = find_class(module, name)
        return clas


class Project(TrackedDict):
    """Project: a persistent storage of pyFormex data.

    A pyFormex Project is a regular Python dict that can contain named data
    of any kind, and can be saved to a file to create persistence over
    different pyFormex sessions.

    The :class:`Project` class is used by pyFormex for the ``pyformex.PF``
    global variable that collects variables exported from pyFormex scripts.
    While projects are mostly handled through the pyFormex GUI, notably the
    *File* menu, the user may also create and handle his own Project objects
    from a script.

    Because of the way pyFormex Projects are written to file,
    there may be problems when trying to read a project file that was
    created with another pyFormex version. Problems may occur if the
    project contains data of a class whose implementation has changed,
    or whose definition has been relocated. Our policy is to provide
    backwards compatibility: newer versions of pyFormex will normally
    read the older project formats. Saving is always done in the
    newest format, and these can generally not be read back by older
    program versions (unless you are prepared to do some hacking).

    .. warning:: Compatibility issues.

       Occasionally you may run into problems when reading back an
       old project file, especially when it was created by an unreleased
       (development) version of pyFormex. Because pyFormex is evolving fast,
       we can not test the full compatibility with every revision
       You can file a support request on the pyFormex `support tracker`_.
       and we will try to add the required conversion code to
       pyFormex.

       The project files are mainly intended as a means to easily save lots
       of data of any kind and to restore them in the same session or a later
       session, to pass them to another user (with the same or later pyFormex
       version), to store them over a medium time period. Occasionally opening
       and saving back your project files with newer pyFormex versions may help
       to avoid read-back problems over longer time.

       For a problemless long time storage of Geometry type objects you may
       consider to write them to a pyFormex Geometry file (.pgf) instead, since
       this uses a stable ascii based format. It can however (currently) only
       store obects of class Geometry or one of its subclasses.

    Parameters
    ----------
    filename: :term:`path_like`
        The name of the file where the Project data will be saved.
        If the file exists (and `access` is not `w`), it should be a previously
        saved Project and an attempt will be made to load the data from this
        file into the Project. If this fails, an error is raised.

        If the file exists and `access` is `w`, it will be overwritten,
        destroying any previous contents.

        If no filename is specified, a temporary file will be created when
        the Project is saved for the first time. The file with not be
        automatically deleted. The generated name can be retrieved from the
        filename attribute.

    access: str, optional
        The access mode of the project file: 'wr' (default), 'rw', 'w' or 'r'.
        If the string contains an 'r' the data from an existing file will be
        read into the Project. If the string starts with an 'r', the file should
        exist. If the string contains a 'w', the data can be written back to
        the file. The 'r' access mode is a read-only mode.

        ======  ===============  ============  ===================
        access  File must exist  File is read  File can be written
        ======  ===============  ============  ===================
          r           yes             yes             no
          rw          yes             yes             yes
          wr          no         if it exists         yes
          w           no              no              yes
        ======  ===============  ============  ===================

    convert: bool, optional
        If True (default), and the file is opened for reading, an
        attempt is made to open old projects in a compatibility mode, doing the
        necessary conversions to new data formats. If convert is set to False,
        only the latest format can be read and older formats will generate
        an error.

    signature: str, optional
        A text that will be written in the header record of the
        file. This can e.g. be used to record format version info.

    compression: int (0-9)
        The compression level. For large data sets, compression leads
        to much smaller files. 0 is no compression, 9 is maximal compression.
        The default is 4.

    binary: bool
        If False and no compression is used, storage is done
        in an ASCII format, allowing to edit the file. Otherwise, storage
        uses a binary format. Using binary=False is deprecated.

    data: dict, optional
        A dict-like object to initialize the Project contents. These data
        may override values read from the file.

    protocol: int,optional
        The protocol to be used in pickling the data to file. If not specified,
        the highest protocol supported by the pickle module is used.

    Examples
    --------
    >>> d = dict(a=1,b=2,c=3,d=[1,2,3],e={'f':4,'g':5})
    >>> P = Project()
    >>> P.update(d)
    >>> print(P)
    Project name: None
      access: wr    mode: b     gzip: 5
      signature: pyFormex ...
      contents: ['a', 'b', 'c', 'd', 'e']
    >>> print(repr(P))
    {'a': 1, 'b': 2, 'c': 3, 'd': [1, 2, 3], 'e': ...}
    >>> with utils.TempFile() as tmp:
    ...     P.save(filename=tmp.path, quiet=True)
    ...     P.clear()
    ...     print(repr(P))
    ...     P.load(quiet=True)
    {}
    >>> print(repr(P))
    {'a': 1, 'b': 2, 'c': 3, 'd': [1, 2, 3], 'e': ...}
    """

    # Historically there have been a few different formats of the
    # written Project files (.pyf). This variable holds the latest
    # version.
    latest_format = 3

    def __init__(self, filename=None, access='wr', *, convert=True,
                 signature=_signature_, compression=5, binary=True,
                 data={}, protocol=default_protocol):
        """Create a new project."""
        self.filename = Path(filename) if filename else None
        self.access = access
        self.signature = str(signature)
        self.gzip = compression if compression in range(1, 10) else 0
        self.mode = 'b' if binary or compression > 0 else ''
        if protocol is None:
            protocol = default_protocol
        self.protocol = min(protocol, pickle.HIGHEST_PROTOCOL) \
            if self.mode == 'b' else 0

        super().__init__()
        if self.filename and self.filename.exists() and 'r' in self.access:
            # read existing contents
            self.load(try_resolve=convert)
            self.hits = 0
        if data:
            self.update(data)
        if self.filename and self.access=='w':
            # destroy existing contents
            self.filename.truncate()
        pf.debug(f"Initial hits = {self.hits}", pf.DEBUG.PROJECT)


    def __str__(self):
        return f"""\
Project name: {self.filename}
  access: {self.access}    mode: {self.mode}     gzip: {self.gzip}
  signature: {self.signature}
  contents: {self.contents()}
"""

    def contents(self):
        return sorted(self.keys())


    def header_data(self):
        """Construct the data to be saved in the header."""
        store_attr = ['signature', 'gzip', 'mode', 'autofile', '_autoscript_']
        store_vals = [getattr(self, k, None) for k in store_attr]
        return dict([(k, v) for k, v in zip(store_attr, store_vals)
                     if v is not None])


    def save(self, filename=None, quiet=False):
        """Save the project to file."""
        if filename is not None:
            self.filename = Path(filename)
        if self.filename is None:
            raise ValueError(
                "No filename specified for the Project: can not save it")
        if 'w' not in self.access:
            pf.debug("Not saving because Project file opened readonly",
                     pf.DEBUG.PROJECT)
            return

        if not quiet:
            print(f"Project variables changed: {self.hits}")
            print(
                f"Saving project {self.filename} with protocol {self.protocol}, "
                f"mode {self.mode} and compression {self.gzip}")

        with self.filename.open('w'+self.mode) as f:
            # write header
            header = f"{self.header_data()}\n".encode('utf-8')
            f.write(header)
            f.flush()
            if self.gzip:
                pyf = gzip.GzipFile(mode='w'+self.mode,
                                    compresslevel=self.gzip, fileobj=f)
                pickle.dump(self, pyf, self.protocol)
                pyf.close()
            else:
                pickle.dump(self, f, self.protocol)
        self.hits = 0


    def readHeader(self, f, quiet=False):
        """Read the header from a project file.

        f is the file opened for reading.
        Tries to read the header from different legacy formats,
        and if successful, adjusts the project attributes according
        to the values in the header.
        Returns the open file if successful.
        """
        self.format = -1
        fpos = f.tell()
        s = f.readline()
        pf.debug(f"Project Header: {s}", pf.DEBUG.PROJECT)
        # Try subsequent formats
        try:
            # newest format has header in text format
            header = eval(s)
            self.__dict__.update(header)
            self.format = 3
        except Exception:

            # try OLD new format: the first pickle contains attributes
            try:
                p = pickle.load(f)
                self.__dict__.update(p)
                self.format = 2
            except Exception:
                s = s.strip()
                if not quiet:
                    print(f"Header = '{s}'")
                if s=='gzip' or s=='' or 'pyFormex' in s:
                    # transitional format
                    self.gzip = 5
                    self.format = 1
                    # NOT SURE IF THIS IS OK, NEED EXAMPLE FILE
                    f.seek(fpos)
                else:
                    # headerless format
                    f.seek(0)
                    self.gzip = 0
                    self.format = 0

        return f


    def load(self, filename=None, try_resolve=True, quiet=False):
        """Load a project from file.

        The loaded definitions will update the current project.
        """
        if filename is not None:
            self.filename = Path(filename)
        if self.filename is None:
            raise ValueError(
                "No filename specified for the Project: can not load")
        if not quiet:
            print(f"Reading project file: {self.filename}")
        with self.filename.open('rb') as f:
            f = self.readHeader(f, quiet)
            if self.format < Project.latest_format:
                if not quiet:
                    print(f"Format looks like {self.format}")
                utils.warn('warn_old_project')
            pos = f.tell()
            if self.gzip > 0:
                if not quiet:
                    print("Unpickling gzip")
                pyf = gzip.GzipFile(fileobj=f, mode='rb')
                p = Unpickler(pyf, try_resolve).load()
                pyf.close()
            else:
                if not quiet:
                    print("Unpickling clear")
                f.seek(pos)
                p = Unpickler(f, try_resolve).load()
            self.update(p)


    def convert(self, filename=None):
        """Convert an old format project file.

        The project file is read, and if successful, is immediately
        saved. By default, this will overwrite the original file.
        If a filename is specified, the converted data are saved to
        that file.
        In both cases, access is set to 'wr', so the tha saved data can
        be read back immediately.
        """
        self.load(try_resolve=True)
        print(f"GOT KEYS {list(self.keys())}")
        if filename is not None:
            self.filename = Path(filename)
        self.access = 'w'
        print(f"Will now save to {self.filename}")
        self.save()


    def uncompress(self, verbose=True):  # noqa: C901
        """Uncompress a compressed project file.

        The project file is read, and if successful, is written
        back in uncompressed format. This allows to make conversions
        of the data inside.
        """
        if self.filename is None:
            return
        if verbose:
            print(f"Uncompressing project file: {self.filename}")
        with self.filename.open('rb') as f:
            f = self.readHeader(f)
            if verbose:
                print(self.format, self.gzip)
            if self.gzip:
                try:
                    pyf = gzip.GzipFile(self.filename, 'r', self.gzip, f)
                except Exception:
                    self.gzip = 0

            if self.gzip:
                fn = self.filename.replace('.pyf', '_uncompressed.pyf')
                fu = open(fn, 'w'+self.mode)
                h = self.header_data()
                h['gzip'] = 0
                fu.write(f"{h}\n")
                while True:
                    x = pyf.read()
                    if x:
                        fu.write(x)
                    else:
                        break
                fu.close()
                if verbose:
                    print(f"Uncompressed {self.filename} to {fn}")

            else:
                utils.warn("warn_project_compression")


    def delete(self):
        """Unrecoverably delete the project file."""
        if self.filename:
            Path(self.filename).remove()


# End
