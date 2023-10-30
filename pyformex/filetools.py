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
"""A collection of file utilities.

"""
import os
import re
import tempfile

from pyformex.path import Path


####################################################################
##  File compression ##
#######################

class File:
    """Read/write files with transparent file compression.

    This class is a context manager providing transparent file compression
    and decompression. It is commonly used in a `with` statement, as follows::

      with File('filename.ext','w') as f:
          f.write('something')
          f.write('something more')

    This will create an uncompressed file with the specified name, write some
    things to the file, and close it. The file can be read back similarly::

      with File('filename.ext','r') as f:
          for line in f:
              print(f)

    Because :class:`File` is a context manager, the file is
    automatically closed when leaving the `with` block.

    So far this doesn't look very different from using :func:`open`.
    But when specifying a filename ending on '.gz' or '.bz2', the File class
    will be automatically compress (on writing) or decompress (on reading)
    the file. So your code can just stay the same as above. Just use a
    proper filename.

    Parameters
    ----------
    filename: :term:`path_like`
        Path of the file to open.
        If the filename ends with '.gz' or '.bz2', transparent (de)compression
        will be used, with gzip or bzip2 compression algorithms respectively.
        For other file names, it can be forced with the `compr` argument.
    mode: str
        File open mode: 'r' for read, 'w' for write or 'a' for
        append mode. See also the Python documentation for the
        :func:`.open` builtin function.
        For compressed files, append mode is not yet available.
    compr: 'gz' | 'bz2'
        The compression algorithm to be used: gzip or bzip2.
        If not provided and the file name ends with '.gz' or '.bz2',
        `compr` is set automatically from the extension.
    level: int (1..9)
        Compression level for gzip/bzip2.
        Higher values result in smaller files, but require longer compression
        times. The default of 5 gives already a fairly good compression ratio.
    delete_temp: bool
        If True (default), the temporary files needed to
        do the (de)compression are deleted when the File instance is closed.
        This can be set to False to keep the files (mainly intended for
        debugging).


    The File class can also be used outside a ``with`` statement. In that case
    the user has to open and close the File himself. The following are more
    or less equivalent with the above examples (the ``with`` statement is
    better at handling exceptions)::

      fil = File('filename.ext','w')
      f = fil.open()
      f.write('something')
      f.write('something more')
      fil.close()

    This will create an uncompressed file with the specified name, write some
    things to the file, and close it. The file can be read back similarly::

      fil = File('filename.ext','r')
      f = fil.open()
      for line in f:
          print(f)
      fil.close()
    """
    def __init__(self, filename, mode, compr=None, level=5, delete_temp=True):
        """Initialize the File instance"""
        filename = Path(filename)
        if compr is None:
            if filename.suffix in ['.gz', '.bz2']:
                # A recognized compression format
                compr = filename.suffix[1:]

        self.name = filename
        self.tmpfile = None
        self.tmpname = None
        self.mode = mode
        self.compr = compr
        self.level = level
        self.delete = delete_temp
        self.file = None


    def open(self):
        """Open the File in the requested mode.

        This can be used to open a File object outside a `with`
        statement. It returns a Python file object that can be used
        to read from or write to the File. It performs the following:

        - If no compression is used, ope the file in the requested mode.
        - For reading a compressed file, decompress the file to a temporary
          file and open the temporary file for reading.
        - For writing a compressed file, open a tem[porary file for writing.

        See the documentation for the :class:`File` class for an example of
        its use.
        """
        if not self.compr:
            # Open an uncompressed file:
            # - just open the file with specified mode
            self.file = open(self.name, self.mode)

        elif self.mode[0:1] in 'ra':
            # Open a compressed file in read or append mode:
            # - first decompress file
            self.tmpname = gunzip(self.name, unzipped='', remove=False)
            # - then open the decompressed file in read/append mode
            self.file = open(self.tmpname, self.mode)

        else:
            # Open a compressed file in write mode
            # - open a temporary file (to be compressed after closing)
            self.tmpfile = TempFile(prefix='File-', mode=self.mode, delete=False)
            self.tmpname = self.tmpfile.name
            self.file = self.tmpfile.file

        return self.file


    # this is needed to make it a context manager
    __enter__ = open


    def close(self):
        """Close the File.

        This can be used to close the File if it was not opened using a
        `with` statement. It performs the following:

        - The underlying file object is closed.
        - If the file was opened in write or append mode and compression is
          requested, the file is compressed.
        - If a temporary file was in use and delete_temp is True,
          the temporary file is deleted.

        See the documentation for the :class:`File` class for an example of
        its use.

        """
        self.file.close()
        if self.compr and self.mode[0:1] in 'wa':
            # compress the resulting file
            gzip(self.tmpname, gzipped=self.name, remove=True,
                 compr=self.compr, level=self.level)
        if self.tmpname and self.delete:
            Path(self.tmpname).remove()


    def __exit__(self, exc_type, exc_value, traceback):
        """Close the File

        """
        if exc_type is None:
            self.close()
            return True

        else:
            # An exception occurred
            if self.file:
                self.file.close()

            if self.tmpfile:
                self.tmpfile.close()

            if self.tmpname and self.delete:
                Path(self.tmpname).remove()

            return False


    def reopen(self, mode='r'):
        """Reopen the file, possibly in another mode.

        This allows e.g. to read back data from a just saved file
        without having to destroy the File instance.

        Returns the open file object.
        """
        self.close()
        self.mode = mode
        return self.open()


##########################################################################
## Temporary Files ##
#####################


class TempDir(tempfile.TemporaryDirectory):
    """A temporary directory that can be used as a context manager.

    This is a wrapper around Python's tempfile.TemporaryDirectory,
    with the following differences:

    - the default value for prefix is set to ``pyf_``,
    - it has an extra attribute '.path' returning the directory name as a Path,
    - the context manager returns a Path instead of a str,
    - the context wrapper can automatically change into the tempdir
    - the context manager automatically changes back to the original workdir

    """
    def __init__(self, suffix=None, prefix='pyf_', dir=None, chdir=False, keep=False):
        super().__init__(suffix, prefix, dir)
        self.prev = os.getcwd()
        self.chdir = chdir
        self.keep = keep

    @property
    def path(self):
        return Path(self.name)

    def __enter__(self):
        if self.chdir:
            os.chdir(self.name)
        return self.path

    def __exit__(self, *args):
        os.chdir(self.prev)
        if not self.keep:
            super().__exit__(*args)


def TempFile(*args, **kargs):
    """Return a temporary file that can be used as a context manager.

    This is a wrapper around Python's tempfile.NamedTemporaryFile,
    with the difference that the returned object has an extra attribute
    '.path', returning the file name as a Path.
    """
    tmpfile = tempfile.NamedTemporaryFile(*args, **kargs)
    tmpfile.path = Path(tmpfile.name)
    return tmpfile


# TODO: in Python3.11 this can be based op Python's contextlib.chdir

class ChDir:
    """A context manager to temporarily change the working directory.

    The context manager changes the current working directory and guarantees
    to come back to the previous, even if an exception occurs.

    Parameters
    ----------
    dirname: :term:`path_like` | None
        The relative or absolute path name of the directory to change into.
        If the directory does not exist, it will be created, unless
        ``create=False`` was specified.
        If None, a temporary working directory will be created and used,
        and be deleted with all its contents on leaving the contex.
    create: bool
        If True(default), the directory (including missing parents) will be
        created if it does not exist.
        If False, and a path was specified for ``dirname``, the directory
        should exist and be accessible.

    Returns
    -------
    context
        A context manager object that can be used in a with statement.
        On entry , it changes into the specified or temporary directory,
        and on exit it change back to the previous working directory.

    Raises
    ------
    OSError or subclass
        If the specified path can no be changed into or can not be created.

    Examples
    --------
    >>> olddir = os.getcwd()
    >>> with ChDir() as newdir:
    ...    print(os.getcwd()==newdir, newdir!=olddir)
    True True
    >>> os.getcwd()==olddir
    True

    """

    def __init__(self, dirname=None, create=True):
        self.saved = Path.cwd()
        if dirname is None:
            self.tempdir = tempfile.TemporaryDirectory()
            self.path = Path(self.tempdir.name)
        else:
            self.tempdir = None
            self.path = Path(dirname)
            if not self.path.exists():
                self.path.mkdir(parents=True)

    def __enter__(self):
        os.chdir(self.path)
        if self.tempdir is not None:
            self.tempdir.__enter__()
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.saved)
        if self.tempdir is not None:
            return self.tempdir.__exit__(exc_type, exc_val, exc_tb)
        return False


def gzip(filename, gzipped=None, remove=True, level=5, compr='gz'):
    r"""Compress a file in gzip/bzip2 format.

    Parameters
    ----------
    filename: :term:`path_like`
        The input file name.
    gzipped: :term:`path_like`, optional
        The output file name. If not specified, it will be set to
        the input file name + '.' + `compr`. An existing output file will be
        overwritten.
    remove: bool
        If True (default), the input file is removed after
        successful compression.
    level: int 1..9
        The gzip/bzip2 compression level.
        Higher values result in smaller files, but require longer compression
        times. The default of 5 gives already a fairly good compression ratio.
    compr: 'gz' | 'bz2'
        The compression algorithm to be used.
        The default is 'gz' for gzip compression. Setting to 'bz2' will use
        bzip2 compression.
    Returns
    -------
    :class:`Path`
        The path of the compressed file.

    Examples
    --------
    >>> f = Path('./test_gzip.out')
    >>> f.write_text('This is a test\n'*100)
    1500
    >>> print(f.size)
    1500
    >>> g = gzip(f)
    >>> print(g)
    test_gzip.out.gz
    >>> print(g.size)
    60
    >>> f.exists()
    False
    >>> f = gunzip(g)
    >>> f.exists()
    True
    >>> print(f.read_text().split('\n')[50])
    This is a test
    >>> g.exists()
    False

    """
    filename = Path(filename)
    if gzipped is None:
        gzipped = filename + '.' + compr
    if compr == 'gz':
        import gzip
        gz = gzip.GzipFile(gzipped, 'wb', compresslevel=level)
    elif compr == 'bz2':
        import bz2
        gz = bz2.BZ2File(gzipped, 'wb', compresslevel=level)
    else:
        raise ValueError("`compr` should be 'gz' or 'bz2'")
    with open(filename, 'rb') as fil:
        gz.write(fil.read())
    gz.close()
    if remove:
        filename.remove()
    return gzipped


def gunzip(filename, unzipped=None, remove=True, compr='gz'):
    """Uncompress a file in gzip/bzip2 format.

    Parameters
    ----------
    filename: :term:`path_like`
        The compressed input file name (usually ending in '.gz' or
        '.bz2').
    unzipped: :term:`path_like`, optional
        The output file name. If not provided and `filename` ends with
        '.gz' or '.bz2', it will be set to the `filename` with the '.gz' or
        '.bz2' removed.
        If not provided and `filename` does not end in '.gz' or '.bz2',
        or if an empty string is provided, the name of a temporary file is
        generated. Since you will normally want to read something from the
        decompressed file, this temporary file is not deleted after closing.
        It is up to the user to delete it (using the returned file name) when
        the file has been dealt with.
    remove: bool
        If True (default), the input file is removed after successful
        decompression. You probably want to set this to False when
        decompressing to a temporary file.
    compr: 'gz' | 'bz2'
        The compression algorithm used in the input file.
        If not provided, it is automatically set from the extension of the
        `filename` if that is either '.gz' or '.bz2', or else the default 'gz'
        is used.

    Returns
    -------
    :class:`Path`
        The name of the uncompressed file.

    Examples
    --------
    See `gzip`.
    """
    filename = Path(filename)
    if filename.suffix in ['.gz', '.bz2']:
        compr = filename.suffix[1:]
    if compr == 'gz':
        import gzip
        gz = gzip.GzipFile(filename, 'rb')
    elif compr == 'bz2':
        import bz2
        gz = bz2.BZ2File(filename, 'rb')
    else:
        raise ValueError("`compr` should be 'gz' or 'bz2'")
    if unzipped is None and filename.endswith('.'+compr):
        unzipped = filename.without_suffix
    if unzipped:
        fil = open(unzipped, 'wb')
    else:
        fil = TempFile(prefix='gunzip-', delete=False)
        unzipped = fil.name
    fil.write(gz.read())
    gz.close()
    fil.close()
    if remove:
        filename.remove()
    return unzipped


##########################################################################
##  ZIP Files
#####################


def zipList(filename):
    """List the files in a zip archive

    Returns a list of file names
    """
    from zipfile import ZipFile
    zfil = ZipFile(filename, 'r')
    return zfil.namelist()


def zipExtract(filename, members=None):
    """Extract the specified member(s) from the zip file.

    The default extracts all.
    """
    from zipfile import ZipFile
    zfil = ZipFile(filename, 'r')
    zfil.extractall(members=members)


###################### file conversion ###################


def dos2unix(infile):
    """Convert a text file to unix line endings."""
    return system(f"sed -i 's|$|\\r|' {infile}")


def unix2dos(infile, outfile=None):
    """Convert a text file to dos line endings."""
    return system(f"sed -i 's|\\r||' {infile}")


def countLines(fn):
    """Return the number of lines in a text file."""
    P = system(["wc", fn])
    if P.returncode == 0:
        return int(P.stdout.split()[0])
    else:
        return 0



def hsorted(l):
    """Sort a list of strings in human order.

    When human sort a list of strings, they tend to interprete the
    numerical fields like numbers and sort these parts numerically,
    instead of the lexicographic sorting by the computer.

    Returns the list of strings sorted in human order.

    Example:
    >>> hsorted(['a1b','a11b','a1.1b','a2b','a1'])
    ['a1', 'a1.1b', 'a1b', 'a2b', 'a11b']
    """
    from pyformex.path import hsortkey
    return sorted(l, key=hsortkey)


def numsplit(s):
    """Split a string in numerical and non-numerical parts.

    Returns a series of substrings of s. The odd items do not contain
    any digits. The even items only contain digits.
    Joined together, the substrings restore the original.

    The number of items is always odd: if the string ends or starts with a
    digit, the first or last item is an empty string.

    Example:

    >>> print(numsplit("aa11.22bb"))
    ['aa', '11', '.', '22', 'bb']
    >>> print(numsplit("11.22bb"))
    ['', '11', '.', '22', 'bb']
    >>> print(numsplit("aa11.22"))
    ['aa', '11', '.', '22', '']
    """
    return re.compile(r'(\d+)').split(s)


def splitDigits(s, pos=-1):
    """Split a string at a sequence of digits.

    The input string is split in three parts, where the second part is
    a contiguous series of digits. The second argument specifies at which
    numerical substring the splitting is done. By default (pos=-1) this is
    the last one.

    Returns a tuple of three strings, any of which can be empty. The
    second string, if non-empty is a series of digits. The first and last
    items are the parts of the string before and after that series.
    Any of the three return values can be an empty string.
    If the string does not contain any digits, or if the specified splitting
    position exceeds the number of numerical substrings, the second and
    third items are empty strings.

    Example:

    >>> splitDigits('abc123')
    ('abc', '123', '')
    >>> splitDigits('123')
    ('', '123', '')
    >>> splitDigits('abc')
    ('abc', '', '')
    >>> splitDigits('abc123def456fghi')
    ('abc123def', '456', 'fghi')
    >>> splitDigits('abc123def456fghi',0)
    ('abc', '123', 'def456fghi')
    >>> splitDigits('123-456')
    ('123-', '456', '')
    >>> splitDigits('123-456',2)
    ('123-456', '', '')
    >>> splitDigits('')
    ('', '', '')
    """
    g = numsplit(s)
    n = len(g)
    i = 2*pos
    if i >= -n and i+1 < n:
        if i >= 0:
            i += 1
        return ''.join(g[:i]), g[i], ''.join(g[i+1:])
    else:
        return s, '', ''

######################## Useful classes ##################


class NameSequence:
    """A class for autogenerating sequences of names.

    Sequences of names are autogenerated by combining a fixed string with
    a numeric part. The latter is incremented at each creation of a new
    name (by using the next() function or by calling the NameSequence).

    Parameters
    ----------
    template: str
        Either a template to generate the names, or an example name from
        which the template can be derived. If the string contains a '%'
        character, it is considered a template and will be used as such.
        It must be a valid template to format a single int value. For
        example, a template 'point-%d' with a value 5 will generate a name
        'point-5'.

        If the string does not contain a '%' character, a template is generated
        as follows. The string is split in three parts (prefix, numeric,
        suffix), where numeric only contains digits and suffix does not contain
        any digits. Thus, numeric is the last numeric part in the string.
        Use ``ext`` if the variable part is not the last numeric part of names.
        If the string does not contain any numeric part, it is split as a file
        name in stem and suffix, and '-0' is appended to the stem. Thus,
        'point.png' will be treated like 'point-0.png'. Finally, if the string
        is empty, it is replaced with '0'. To create the template, the
        numeric part is replaced with a '%0#d' format (where # is the
        length of the numeric part, concatened again with prefix and suffix,
        and ``ext`` is appended. Also, the start value is set to the numeric
        part (unless a nonzero start value is provided).
    ext: str, optional
        If provided, this is an invariable string appended to the template.
        It is mostly useful when providing a full name as ``template`` and
        the variable numeric part is not the last numeric part in the name.
        For example, NameSequence('x1', '.5a') will generate names 'x1.5a',
        'x2.5a', ...
    start: int, optional
        Starting value for the numerical part. If ``template`` contains a full
        name, it will only be acknowledged if nonzero.
    step: int, optional
        Step for incrementing the numerical value.

    Notes
    -----
    If N is a NameSequence, then next(N) and N() are equivalent.

    Examples
    --------
    >>> N = NameSequence('obj')
    >>> next(N)
    'obj-0'
    >>> N()
    'obj-1'
    >>> [N() for i in range(3)]
    ['obj-2', 'obj-3', 'obj-4']
    >>> N.peek()
    'obj-5'
    >>> N()
    'obj-5'
    >>> N.template
    'obj-%d'
    >>> N = NameSequence('obj-%03d', start=5)
    >>> [next(N) for i in range(3)]
    ['obj-005', 'obj-006', 'obj-007']
    >>> N = NameSequence('obj-005')
    >>> [next(N) for i in range(3)]
    ['obj-005', 'obj-006', 'obj-007']
    >>> N = NameSequence('abc.98', step=2)
    >>> [next(N) for i in range(3)]
    ['abc.98', 'abc.100', 'abc.102']
    >>> N = NameSequence('abc-8x.png')
    >>> [next(N) for i in range(3)]
    ['abc-8x.png', 'abc-9x.png', 'abc-10x.png']
    >>> N.template
    'abc-%01dx.png'
    >>> N.glob()
    'abc-*x.png'
    >>> next(NameSequence('abc','.png'))
    'abc-0.png'
    >>> next(NameSequence('abc.png'))
    'abc-0.png'
    >>> N = NameSequence('/home/user/abc23','5.png')
    >>> [next(N) for i in range(2)]
    ['/home/user/abc235.png', '/home/user/abc245.png']
    >>> N = NameSequence('')
    >>> next(N), next(N)
    ('0', '1')
    >>> N = NameSequence('12')
    >>> next(N), next(N)
    ('12', '13')

    """
    def __init__(self, template, ext='', start=0, step=1):
        """Initialize a new NameSequence"""
        self.nr = int(start)
        self.step = int(step)
        if '%' in template:
            self.template = template
        else:
            self.set_template_from_name(template, ext)
            if start != 0:
                self.nr = int(start)
        try:
            s = self.peek()
        except:
            raise ValueError("Invalid parameters for NameSeq")

    def peek(self):
        """Peek at the next name"""
        return self.template % self.nr

    def __next__(self):
        """Return the next name"""
        name = self.peek()
        self.nr += self.step
        return name

    __call__ = __next__

    def set_template_from_name(self, name, ext=''):
        """Set template and current number from a given name"""
        prefix, number, suffix = splitDigits(name)
        if len(number) > 0:
            self.nr = int(number)
            fmt = f"%0{len(number)}d"
        else:
            self.nr = 0
            if name:
                p = Path(name)
                prefix, suffix = p.stem, p.suffix
                fmt = "-%d"
            else:
                prefix = suffix = ''
                fmt = "%d"
        self.template = prefix+fmt+suffix+ext

    def glob(self):
        """Return a UNIX glob pattern for the generated names.

        A NameSequence is often used as a generator for file names.
        The glob() method returns a pattern that can be used in a
        UNIX-like shell command to select all the generated file names.
        """
        m = re.match(r'(.*)%\d*d(.*)', self.template)
        if m:
            return f"{m.group(1)}*{ m.group(2)}"
        else:
            raise ValueError("Invalid template")


################### automatic naming of objects ##########################

_autoname = {}

def autoName(clas):
    """Return the autoname class instance for objects of type clas.

    This allows for objects of a certain class to be automatically
    named throughout pyFormex.

    Parameters
    ----------
    clas: str or class or object
        The object class name. If a str, it is the class name. If a class,
        the name is found from it. If an object, the name is taken from
        the object's class. In all cases the name is converted to lower
        case

    Returns
    -------
    NameSequence instance
        A NameSequence that will generate subsequent names corresponding
        with the specified class.

    Examples
    --------
    >>> from pyformex.formex import Formex
    >>> F = Formex()
    >>> print(next(autoName(Formex)))
    formex-0
    >>> print(next(autoName(F)))
    formex-1
    >>> print(next(autoName('Formex')))
    formex-2

    """
    if isinstance(clas, str):
        name = clas
    else:
        try:
            name = clas.__name__
        except Exception:
            try:
                name = clas.__class__.__name__
            except Exception:
                raise ValueError("Expected an instance, class or string")
    name = name.lower()
    if name not in _autoname:
        _autoname[name] = NameSequence(name+'-0')
    return _autoname[name]


def listFonts(mono=False):
    """List the fonts known to the system.

    Parameters
    ----------
    mono: bool
        If True, only returns the monospace fonts. Default is to return all
        fonts.

    Returns
    -------
    list of :class:`Path`
        A list of the font files found on the system.

    Notes
    -----
    This uses the 'fc-list' command from the fontconfig package and will
    produce a warning if fontconfig is not installed.
    """
    cmd = "fc-list : file | sed 's|.*file=||;s|:||'"
    P = system(cmd, shell=True)
    if P.returncode:
        warning("fc-list could not find your font files.\n"
                "Maybe you do not have fontconfig installed?")
        fonts = []
    else:
        fonts = sorted([Path(f.strip()) for f in P.stdout.split('\n')])
        if len(fonts[0]) <= 1:
            fonts = fonts[1:]
    if mono:
        fonts = [f for f in fonts if is_valid_mono_font(f)]
    return fonts


def is_valid_mono_font(fontfile):
    """Filter valid monotype fonts

    Parameters
    ----------
    fontfile: Path
        Path of a font file.

    Returns
    -------
    bool
        True if the provided font file has a .ttf suffix, is a fixed width
        font and the font basename is not listed in the 'fonts/ignore'
        configuration variable.
    """
    from pyformex import freetype as ft
    return fontfile.suffix == '.ttf' and \
        fontfile.name not in pf.cfg['fonts/ignore'] and \
        ft.Face(fontfile).is_fixed_width


def defaultMonoFont():
    """Return a default monospace font for the system."""
    fonts = listFonts(mono=True)
    if not fonts:
        raise ValueError("I could not find any monospace font file on your system")
    for f in fonts:
        if f.endswith('DejaVuSansMono.ttf'):
            return f
    return fonts[0]


def listMonoFonts():
    """List only the monospace fonts

    See Also
    --------
    listFonts
    """
    return listFonts(mono=True)


def diskSpace(path, units=None, ndigits=2):
    """Returns the amount of diskspace of a file system.

    Parameters
    ----------
    path: :term:`path_like`
        A path name inside the file system to be probed.
    units: str
        If provided, results are reported in this units. See
        :meth:`humanSize` for possible values. The default
        is to return the number of bytes.
    ndigits: int
        If provided, and also ``units`` is provided, specifies the number
        of decimal digits to report. See :meth:`humanSize` for details.

    Returns
    -------
    total: int | float
        The total disk space of the file system containing ``path``.
    used: int | float
        The used disk space on the file system containing ``path``.
    available: int | float
        The available disk space on the file system containing ``path``.

    Notes
    -----
    The sum ``used + available`` does not necessarily equal ``total``,
    because a file system may (and usually does) have reserved blocks.
    """
    stat = os.statvfs(Path(path).resolve())
    total = stat.f_blocks * stat.f_frsize
    avail = stat.f_bavail * stat.f_frsize
    used = (stat.f_blocks - stat.f_bfree) * stat.f_frsize
    if units:
        total = humanSize(total, units, ndigits)
        avail = humanSize(avail, units, ndigits)
        used = humanSize(used, units, ndigits)
    return total, used, avail


def humanSize(size, units, ndigits=-1):
    """Convert a number to a human size.

    Large numbers are often represented in a more human readable
    form using k, M, G prefixes. This function returns the input
    size as a number with the specified prefix.

    Parameters
    ----------
    size: int or float
        A number to be converted to human readable form.
    units: str
        A string specifying the target units. The first character should
        be one of k,K,M,G,T,P,E,Z,Y. 'k' and 'K' are equivalent. A second
        character 'i' can be added to use binary (K=1024) prefixes instead of
        decimal (k=1000).
    ndigits: int, optional
        If provided and >=0, the result will be rounded to this number of
        decimal digits.

    Returns
    -------
    float
        The input value in the specified units and possibly rounded
        to ``ndigits``.

    Examples
    --------
    >>> humanSize(1234567890,'k')
    1234567.89
    >>> humanSize(1234567890,'M',0)
    1235.0
    >>> humanSize(1234567890,'G',3)
    1.235
    >>> humanSize(1234567890,'Gi',3)
    1.15
    """
    size = float(size)
    order = '.KMGTPEZY'.find(units[0].upper())
    if units[1:2] == 'i':
        scale = 1024.
    else:
        scale = 1000.
    size = size / scale**order
    if ndigits >= 0:
        size = round(size, ndigits)
    return size


def getDocString(pyfile):
    """Return the docstring from a Python file.

    Parameters
    ----------
    pyfile: :term:`path_like`
        The file to seach for the docstring.

    Returns
    -------
    str
        The first multiline string (delimited by triple double/single quote
        characters) from the file.
    """
    s = Path(pyfile).read_text()
    for marker in ('"""', "'''"):
        i = s.find(marker)
        if i >= 0:
            j = s.find(marker, i+1)
            if j >= i+3:
                return s[i+3:j]
    return ''


# selftest
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    print(sys.path)
    failures, tests = doctest.testmod(
        optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)
    print(f"{__file__}: Tests: {tests}; Failures: {failures}")

### End
