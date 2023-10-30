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
"""Object oriented filesystem paths.

This module defines the :class:`Path` class providing object oriented handling
of filesystem paths. It was created for the pyFormex project
(https://pyformex.org) but can be used independently from other pyFormex
modules.

While our :class:`Path` class has many similarities to the classes in
Python's :mod:`pathlib`, we we had some good reasons to not use that module
and create our own instead:

- Python's pathlib seemed overly complex, with classes as Path, PosixPath,
  WindowsPath, PurePath, PurePosixPath, PureWindowsPath. We just have one
  class (Path) that does it all.
- Despite nearly all OSes implementing paths as strings, Python's
  pathlib.Path is not a string (str), and this created a lot of problems
  for transforming a program to the use of pathlib.Path. All file related
  functions and methods need to be changed to accept str as well as
  pathlib.Path as arguments.
- By contrast, our Path class is subclassed from Python's :class:`str`.
  This was set forward as a requirement, as it was developed for pyFormex
  (https://pyformex.org), which does a lot of string manipulations on
  file paths, and uses a lot of external libraries using strings for
  paths. In initially we tried to use pathlib, but the constant switching
  between Path and str was a real hindrance and we decided to develop our
  own Path class instead. Being a str, a Path can immediately be used in
  all places where a str is used, and all str methods can be applied on a
  Path.
- We did not require compatibility with other OSes besides Linux. Though the
  class could likely be ported to other OSes with minor adjustments, the
  author never did consider doing it by lack of knowledge about Windows file
  systems. But if anyone wants to try it, I'm willing to help.
- Our Path class offers more functionality than Python's, as we have
  collected all path related code from pyFormex into this single module.

Despite the differences, there are also many similarities with
the pathlib classes. We have tried to use as much as possible
the same name and functionality for the class methods.

Because we wanted this module to be of general use, the only dependencies
are some Python standard library modules.

This version is for Python3 only. See pyFormex 1.0.7 for an older version
(with less functionality) that supports both Python2.7 and Python3.x.
"""

import os
import shutil
import re


def hsortkey(s):
    """Create a key for human sorting.

    When humans sort a list of strings, they tend to interprete the
    numerical fields as numbers and sort these parts numerically,
    instead of using the lexicographic sorting as done by a computer.

    This splits a string in digits and non-digits parts, and converts
    the digits parts to int. The resulting list can be used to compare
    the input strings for use in human sorting. This function can be
    used in Python's list.sort method and in the sorted builtin function.
    This version also splits the string at the last occurring dot, and
    makes sure that a numeric part before the dot is sorted after the

    Parameters
    ----------
    s: str
        The string for which to compute a human sorting key.

    Returns
    -------
    list
        A list of items which can be used in sorting methods to compare
        two strings and sort them in a human way. The items are alternatively
        of type str and int. There are always an odd number of items. The
        last item may be an empty string.

    See Also
    --------
    hsortkey_ignore: similar, but ignores the case of the alphabetic parts

    Examples
    --------
    >>> hsortkey('abc23def45ghi')
    ['abc', 23, 'def', 45, 'ghi']
    >>> hsortkey('abc23def45')
    ['abc', 23, 'def', 45, '']
    >>> hsortkey('abc.def')
    ['abc', -1, 'def']
    >>> hsortkey('abc23.def')
    ['abc', 23, '', -1, 'def']
    >>> sorted(['.b', '0b', '.0b', '_b', 'Ab', 'ab'], key=hsortkey)
    ['.0b', '.b', '0b', 'Ab', '_b', 'ab']
    >>> sorted(['a', 'ab', 'a.b', 'a1.b', 'a2.b', 'a10.b'])
    ['a', 'a.b', 'a1.b', 'a10.b', 'a2.b', 'ab']
    >>> sorted(['a', 'ab', 'a.b', 'a1.b', 'a2.b', 'a10.b'], key=hsortkey)
    ['a', 'a.b', 'a1.b', 'a2.b', 'a10.b', 'ab']
    """
    t = s.split('.', maxsplit=1)
    key = re.split(r'(\d+)', t[0])
    if len(t) > 1:
        key = key + [-1] + re.split(r'(\d+)', t[1])
    for i in range(1, len(key), 2):
        key[i] = int(key[i])
    return key


def hsortkey_ignore(s):
    """Create a key for human sorting while ignoring case.

    This is like hsortkey but ignores case.

    Examples
    --------
    >>> hsortkey_ignore('abc23DEF45ghi')
    ['abc', 23, 'def', 45, 'ghi']
    """
    key = hsortkey(s)
    for i in range(0, len(key), 2):
        key[i] = key[i].lower()
    return key


def matchAny(target, *regexps):
    """Check whether target matches any of the regular expressions.

    Parameters
    ----------
    target: str
        String to match with the regular expressions.
    *regexp: sequence of regular expressions.
        The regular expressions to match the target string.

    Returns
    -------
    bool
        True, if target matches at least one of the provided regular
        expressions. False if no matches.

    Examples
    --------
    >>> matchAny('test.jpg', '.*[.]png', '.*[.]jpg')
    True
    >>> matchAny('test.jpeg', '.*[.]png', '.*[.]jpg')
    False
    >>> matchAny('test.jpg')
    False
    """
    for r in regexps:
        if re.fullmatch(r, target):
            return True
    return False


class Path(str):
    """A filesystem path which also behaves like a str.

    A Path instance represents a valid path to a file in the filesystem,
    existing or not. Path is thus a subclass of str that can only represent
    strings that are valid as file paths. The constructor will always
    normalize the path.

    Parameters
    ----------
    args: :term:`path_like`, ...
        One or more path components that will be concatenated to form the
        new Path. Each component can be a str or a Path.
        It can be relative or absolute. If multiple absolute components are
        specified, the last one is used.


    The following all create the same Path:

    >>> Path('/pyformex/gui/menus')
    Path('/pyformex/gui/menus')
    >>> Path('/pyformex', 'gui', 'menus')
    Path('/pyformex/gui/menus')
    >>> Path('/pyformex', Path('gui'), 'menus')
    Path('/pyformex/gui/menus')

    But this is different:

    >>> Path('/pyformex', '/gui', 'menus')
    Path('/gui/menus')

    Spurious slashes and single and double dots are collapsed:

    >>> Path('/pyformex//gui///menus')
    Path('/pyformex/gui/menus')
    >>> Path('/pyformex/./gui/menus')
    Path('/pyformex/gui/menus')
    >>> Path('/pyformex/../gui/menus')
    Path('/gui/menus')

    Note
    ----
    The collapsing of double dots is different from the :mod:`pathlib` behavior.
    Our Path class follows the :func:`os.path.normpath` behavior here.

    Empty string and no arguments create a Path to the current directory:

    >>> Path('')
    Path('.')
    >>> Path()
    Path('.')

    **Operators**:
    The slash operator helps create child paths, similarly to
    :func:`os.path.join`.
    The plus operator can be used to add a trailing part without a slash
    separator. The equal operator allows comparing paths.

    >>> p = Path('/etc') / 'init.d' / 'apache2'
    >>> p
    Path('/etc/init.d/apache2')
    >>> p + '.d'
    Path('/etc/init.d/apache2.d')
    >>> p1 = Path('/etc') + '/init.d/apache2'
    >>> p1 == p
    True

    Note
    ----
    Unlike the :mod:`pathlib`, our Path class does not provide the possibility
    to join a str and a Path with a slash operator: the first component must
    be a Path.


    **Properties**:
    The following properties give access to different components of the Path:

    - :attr:`parts`: a tuple with the various parts of the Path,
    - :attr:`parent`: the parent directory of the Path
    - :attr:`parents`: a tuple with the subsequent parent Paths
    - :attr:`name`: a string with the final component of the Path
    - :attr:`suffix`: the file extension of the final component, if any
    - :attr:`stem`: the final component without its suffix
    - :attr:`lsuffix`: the suffix in lower case
    - :attr:`ftype`: the suffix in lower case and without the leading dot

    Note
    ----
    We currently do not have the following properties available with
    pathlib: drive, root, anchor, suffixes


    Attributes
    ----------
    sortkey: callable
        This class attribute is a callable used as the key in sorting file
        names. The default is set to :func:`path.hsortkey`, but it can be
        changed in case the user want to have another sorting method by
        default. Setting it to None will use lexical sorting.

    Examples
    --------
    >>> Path('/a/b')
    Path('/a/b')
    >>> Path('a/b//c')
    Path('a/b/c')
    >>> Path('a/b/./c')
    Path('a/b/c')
    >>> Path('a/b/../c')
    Path('a/c')
    >>> Path('a/b/.../c')
    Path('a/b/.../c')
    >>> Path('//a/b')
    Path('//a/b')
    >>> Path('///a/b')
    Path('/a/b')
    >>> p = Path('/etc/init.d/')
    >>> p.parts
    ('/', 'etc', 'init.d')
    >>> p.parent
    Path('/etc')
    >>> p.parents
    (Path('/etc'), Path('/'))
    >>> p0 = Path('pyformex/gui/menus')
    >>> p0.parts
    ('pyformex', 'gui', 'menus')
    >>> p0.parents
    (Path('pyformex/gui'), Path('pyformex'), Path('.'))
    >>> Path('../pyformex').parents
    (Path('..'), Path('.'))
    >>> p.name
    'init.d'
    >>> p.stem
    'init'
    >>> p.suffix
    '.d'
    >>> p1 = Path('Aa.Bb')
    >>> p1.suffix, p1.lsuffix, p1.ftype
    ('.Bb', '.bb', 'bb')
    >>> p.exists()
    True
    >>> p.is_dir()
    True
    >>> p.is_file()
    False
    >>> p.is_symlink()
    False
    >>> p.is_absolute()
    True
    >>> Path('/var/run').is_symlink()
    True
    """
    # This is here to avoid double index (we have explicit Attribute above
    # Maybe define a property/setter with that doc and the remove this
    _exclude_members_ = ['sortkey']
    sortkey = hsortkey

    # @property
    # @classmethod
    # def sortkey(clas):
    #     return clas._sortkey
    # @sortkey.setter
    # @classmethod
    # def sortkey(clas, key):
    #     _sortkey = key


    def __new__(clas, *args):
        """Create a new Path instance"""
        if len(args) == 1 and isinstance(args[0], Path):
            return args[0]
        if len(args) == 0:
            args = ['']
        return str.__new__(clas, os.path.normpath(os.path.join(*args)))

    def __truediv__(self, component):
        """Defines / operator for joining path components"""
        return Path(os.path.join(self, component))

    # We do not define __rtruediv__: use Path('...') / instead

    def __add__(self, suffix):
        """Defines + operator for joining path suffixes"""
        return Path(str(self)+suffix)

    def __repr__(self):
        """String representation of a path"""
        return ''.join(["Path('", self, "')"])

    @property
    def parts(self):
        """Split the Path in its components.

        Returns
        -------
        tuple of str
            The various components of the Path

        Examples
        --------
        >>> Path('/a/b/c/d').parts
        ('/', 'a', 'b', 'c', 'd')
        >>> Path('a/b//d').parts
        ('a', 'b', 'd')
        >>> Path('a/b/./d').parts
        ('a', 'b', 'd')
        >>> Path('a/b/../d').parts
        ('a', 'd')
        >>> Path('a/b/.../d').parts
        ('a', 'b', '...', 'd')
        """
        parts = []
        p = os.path.normpath(self)
        while True:
            head, tail = os.path.split(p)
            if tail:
                parts.insert(0, tail)
            if head == '':
                break
            if head[-1] == '/':
                parts.insert(0, head)
                break
            p = head
        return tuple(parts)

    @property
    def parents(self):
        """Return the parents of the Path.

        Returns
        -------
        tuple of Path
            The subsequent parent directories of the Path
        """
        parents = [self.parent]
        while parents[-1] != '/' and parents[-1] != '.':
            parents.append(parents[-1].parent)
        return tuple(parents)

    @property
    def parent(self):
        """Return the parent directory.

        Returns
        -------
        Path
            The parent directory of the Path.
        """
        return Path(os.path.dirname(self))

    @property
    def name(self):
        """Return the final path component.

        Returns
        -------
        str
            The final component of the Path.
        """
        return os.path.basename(self)

    @property
    def stem(self):
        """Return the final path component without its suffix.

        Returns
        -------
        str
            The final component of the Path without its :attr:`suffix`.

        Examples
        --------
        >>> Path('aA.bB').stem
        'aA'
        """
        stem, ext = os.path.splitext(self.name)
        if ext == '.':
            stem += ext
        return stem

    @property
    def suffix(self):
        """Return the file extension of the Path component.

        The file extension is the last substring of the final component
        starting at a dot that is neither the start nor the end
        of the component.

        Returns
        -------
        str
            The file extension of the Path, including the leading dot.

        Examples
        --------
        >>> Path('aA.bB').suffix
        '.bB'
        """
        ext = os.path.splitext(self)[1]
        if ext == '.':
            ext = ''
        return ext

    @property
    def lsuffix(self):
        """Return the file extension in lower case.

        Returns
        -------
        str
            The suffix of the Path, converted to lower case.

        Examples
        --------
        >>> Path('aA.bB').lsuffix
        '.bb'
        """
        return self.suffix.lower()

    @property
    def ftype(self):
        """Return the file extension in lower case and with the leading dot.

        Returns
        -------
        str
            The lsuffix of the Path without the leading dot.

        Examples
        --------
        >>> Path('aA.bB').ftype
        'bb'
        """
        return self.suffix.lower().lstrip('.')

    @property
    def without_suffix(self):
        """Return the Path without the suffix.

        The file suffix is the last substring of the final component
        starting at a dot that is neither the start nor the end
        of the component.

        Returns
        -------
        Path
            The Path without the suffix.

        Notes
        -----
        This is equivalent to::

            self.parent / self.stem

        If the path has no suffix, the output is identical to the input.

        Examples
        --------
        >>> f = Path('/dD/aA.bB')
        >>> f.without_suffix
        Path('/dD/aA')
        >>> f.parent / f.stem
        Path('/dD/aA')
        """
        return Path(os.path.splitext(self)[0])

    def exists(self):
        """Return True if the Path exists"""
        return os.path.exists(self)

    def is_dir(self):
        """Return True if the Path exists and is a directory"""
        return os.path.isdir(self)

    def is_readable_dir(self):
        """Return True if the Path exists and is a readable directory"""
        return (os.path.isdir(self) and
                os.access(self, os.R_OK | os.X_OK))

    def is_writable_dir(self):
        """Return True if the Path exists and is a writable directory"""
        return (os.path.isdir(self) and
                os.access(self, os.R_OK | os.W_OK | os.X_OK))

    def is_file(self):
        """Return True if the Path exists and is a file"""
        return os.path.isfile(self)

    def is_readable_file(self):
        """Return True if the Path exists and is a readable file"""
        return (os.path.isfile(self) and
                os.access(self, os.R_OK))

    def is_writable_file(self):
        """Return True if the Path exists and is a writable directory"""
        return (os.path.isfile(self) and
                os.access(self, os.R_OK | os.W_OK))

    def is_readable(self):
        """Return True if the Path exists and is readable (dir or file)"""
        perm = os.R_OK
        if self.is_dir():
            perm |= os.X_OK
        res = os.access(self, perm)
        print(f"{self} is readable: {res}")
        return res

    def is_writable(self):
        """Return True if the Path is writable (dir or file)"""
        perm = os.R_OK | os.W_OK
        if self.is_dir():
            perm |= os.X_OK
        return os.access(self, perm)

    def is_symlink(self):
        """Return True if the Path exists and is a symlink"""
        return os.path.islink(self)

    def is_badlink(self):
        """Return True if the Path exists and is a bad symlink

        A bad symlink is a symlink that points to a non-existing file
        """
        return os.path.islink(self) and not os.path.exists(self.resolve())

    def is_absolute(self):
        """Return True if the Path is absolute.

        The Path is absolute if it start with a '/'.

        >>> Path('/a/b').is_absolute()
        True
        >>> Path('a/b').is_absolute()
        False
        """
        return os.path.isabs(self)

    def with_name(self, name):
        """Return a new Path with the filename changed.

        Parameters
        ----------
        name: str
            Name to replace the last component of the Path

        Returns
        -------
        Path
            A Path where the last component has been changed to ``name``.

        Examples
        --------
        >>> Path('data/testrun.inp').with_name('testimg.png')
        Path('data/testimg.png')
        """
        return self.parent / name    # noqa

    def with_suffix(self, suffix):
        """Return a new Path with the suffix changed.

        Parameters
        ----------
        suffix: str
            Suffix to replace the last component's :meth:`suffix`.
            The replacement string will normally start with a dot.
            If it doesn't, no dot is added. See Examples.

        Returns
        -------
        Path
            A Path where the suffix of the last component has been changed
            to ``suffix``.

        Examples
        --------
        >>> Path('data/testrun.inp').with_suffix('.cfg')
        Path('data/testrun.cfg')
        >>> Path('data/testrun.inp').with_suffix('_1.inp')
        Path('data/testrun_1.inp')
        """
        return Path(os.path.splitext(self)[0] + suffix)

    def absolute(self):
        """Return an absolute version of the path.

        Returns
        -------
        Path
            The absolute filesystem path of the Path. This alsorks if the
            Path does not exist. It does not resolve symlinks.

        See Also
        --------
        resolve: return an absolute path resolving any symlinks.

        Examples
        --------
        >>> Path('.').absolute() # doctest: +ELLIPSIS
        Path('...')
        >>> Path('something').absolute() # doctest: +ELLIPSIS
        Path('.../something')
        """
        return Path(os.path.abspath(self))

    def resolve(self):
        """Return absolute path resolving all symlinks.

        Returns
        -------
        Path
            The absolute filesystem path of the Path, resolving all symlinks.
            This also works if any of the Path components does not exist.

        Examples
        --------
        >>> p = Path('something/inside').resolve()
        >>> p == Path(f"{os.getcwd()}/something/inside")
        True
        """
        return Path(os.path.realpath(self))

    def expanduser(self):
        """Expand the ~ and ~user in Path.

        A leading '~' in the Path is expanded tot the home directory
        of the user executing the code. A leading '~user' is expanded
        to the home directory of the user named 'user'.

        Returns
        -------
        Path
            The Path with ~ and ~user expanded, the latter only if user
            exists.

        Examples
        --------
        >>> import getpass
        >>> user = getpass.getuser()
        >>> p = Path('~').expanduser()
        >>> p1 = Path(f"~{user}").expanduser()
        >>> p2 = Path(f"{os.environ['HOME']}")
        >>> p == p1 == p2
        True
        """
        return Path(os.path.expanduser(self))

    def as_uri(self):
        """Return the Path as an URI.

        Returns
        -------
        str
            A string starting with 'file://' followed by the resolved
            absolute path of the Path. Also ~ and ~user are expanded
            (if user exists).

        Examples
        --------
        >>> p = Path('~/some/file.html').as_uri()
        >>> p == f"file://{os.environ['HOME']}/some/file.html"
        True
        """
        return 'file://' + self.expanduser().resolve()

    def samefile(self, other_file):
        """Test whether two pathnames reference the same actual file

        Parameters
        ----------
        other: :term:`path_like`
            Another file path to compare with.

        Returns
        -------
        bool
            True if the other file is actually the same file as self.

        Examples
        --------
        >>> Path.home().samefile(Path('~').expanduser())
        True
        """
        return os.path.samefile(self, other_file)

    def commonprefix(self, *other):
        """Return the longest common leading part in a list of paths.

        Parameters
        ----------
        *other: one or more :term:`path_like`
            Other file path(s) to compare with.

        Returns
        -------
        Path
            The longest common leading part in all the file paths.

        Examples
        --------
        >>> p = Path('/etc/password')
        >>> q = Path('/etc/profile')
        >>> p.commonprefix(p,q,'/etc/pam.d')
        Path('/etc/p')
        >>> p.commonprefix(p,q,'/etc/group')
        Path('/etc')
        >>> p.commonpath(p,q,'/etc/pam.d')
        Path('/etc')
        """
        return Path(os.path.commonprefix([self]+list(other)))

    def commonpath(self, *other):
        """Return the longest common sub-path in a list of paths.

        Parameters
        ----------
        *other: one or more :term:`path_like`
            Other file path(s) to compare with.

        Returns
        -------
        Path
            The longest common sub-path in all the file paths.

        Examples
        --------
        >>> p = Path('/etc/password')
        >>> p.commonpath(p,'/etc/pam.d')
        Path('/etc')
        """
        return Path(os.path.commonpath([self]+list(other)))

    def joinpath(self, *other):
        """Join two or more path components.

        Parameters
        ----------
        *other: one or more :term:`path_like`
            Other path components to join to self.

        Notes
        -----
        This alternative to using the slash operator is especially
        useful if the components are a computed and/or long sequence.

        Examples
        --------
        >>> home = Path.home()
        >>> p1 = home.joinpath('.config', 'pyformex', 'pyformex.conf')
        >>> p2 = home / '.config' / 'pyformex' / 'pyformex.conf'
        >>> p1 == p2
        True
        """
        return Path(os.path.join(self, *other))

    def relative_to(self, other):
        """Return a relative path version of a path.

        Parameters
        ----------
        other: :term:`path_like`
            Another file path to compare with.

        Returns
        -------
        Path:
            Path relative to other pointing to same file as self.

        See Also
        --------
        absolute: make a Path absolute

        Examples
        --------
        >>> Path('/usr/local/bin').relative_to('/usr/bin')
        Path('../local/bin')

        """
        return Path(os.path.relpath(self, start=other))

    def mkdir(self, mode=0o775, parents=False, exist_ok=False):
        """Create a directory.

        Parameters
        ----------
        mode: int
            The mode to be set on the created directory.
        parents: bool
            If True, nonexisting intermediate directories will also be
            created. The default requires all parent directories to exist.
        exist_ok: bool
            If True and the target already exist and is a directory, it will
            be silently accepted. The default (False) will raise an exeption
            if the target exists.

        """
        if self.exists():
            if exist_ok and self.resolve().is_dir():
                self.chmod(mode)
            else:
                raise ValueError(f"{self!r} exists already")
        else:
            if parents:
                os.makedirs(self, mode)
            else:
                os.mkdir(self, mode)

    def rmdir(self):
        """Remove an empty directory."""
        os.rmdir(self)

    def unlink(self):
        """Remove an existing file."""
        os.unlink(self)

    def remove(self):
        """Remove a file, but silently ignores non-existing."""
        if self.exists():
            self.unlink()

    def removeTree(self, top=True):
        """Recursively delete a directory tree.

        Parameters
        ----------
        top: bool
            If True (default), the top level directory will be removed as well.
            If False, the top level directory will be kept, and only its
            contents will be removed.
        """
        shutil.rmtree(self)
        if not top:
            self.mkdir(exist_ok=True)

    def move(self, dst):
        """Rename or move a file or directory

        Parameters
        ----------
        dst: :term:`path_like`
            Destination path.

        Returns
        -------
        Path
            The new Path.

        Notes
        -----
        Changing a directory component will move the file. Moving a file
        accross file system boundaries may not work. If the destination
        is an existing file, it will be overwritten.
        """
        os.replace(self, dst)
        return Path(dst)

    def copy(self, dst):
        """Copy the file under another name.

        Parameters
        ----------
        dst: :term:`path_like`
            Destination path.
        """
        return Path(shutil.copy(self, dst))

    def symlink(self, dst):
        """Create a symlink for this Path.

        Parameters
        ----------
        dst: :term:`path_like`
            Path of the symlink, which will point to self if successfully
            created.
        """
        os.symlink(self, dst)
        return Path(dst)

    def touch(self):
        """Create an empty file or update an existing file's timestamp.

        If the file does not exist, it is create as an empty file.
        If the file exists, it remains unchanged but its time of last
        modification is set to the current time.
        """
        self.open('a').close()

    def truncate(self):
        """Create an empty file or truncate an existing file.

        If the file does not exist, it is create as an empty file.
        If the file exists, its contents is erased.
        """
        self.open('w').close()

    def chmod(self, mode):
        """Change the access permissions of a file.

        Parameters
        ----------
        mode: int
            Permission mode to set on the file. This is usually given as
            an octal number reflecting the access mode bitfield. Typical
            values in a trusted environment are 0o664 for files and 0o775
            for directories. If you want to deny all access for others,
            the values are 0o660 and 0o770 respectively.
        """
        return os.chmod(self, mode)

    @property
    def stat(self):
        """Return the full stat info for the file.

        Returns
        -------
        stat_result
            The full stat results for the file Path.

        Notes
        -----
        The return value can be interrogated using Python's stat module.
        Often used values can also be got from Path methods :meth:`mtime`,
        :meth:`size`, :meth:`owner`, :meth:`group`.
        """
        return os.stat(self)

    @property
    def mtime(self):
        """Return the (UNIX) time of last change."""
        return self.stat.st_mtime

    @property
    def size(self):
        """Return the file size in bytes."""
        return self.stat.st_size

    @property
    def owner(self):
        """Return the login name of the file owner."""
        import pwd
        return pwd.getpwuid(self.stat.st_uid).pw_name

    @property
    def group(self):
        """Return the group name of the file gid."""
        import grp
        return grp.getgrgid(self.stat.st_gid).gr_name

    def open(self, mode='r', buffering=-1, encoding=None, errors=None):
        """Open the file pointed to by the Path.

        Parameters are like in Python's built-in :func:`.open` function.
        """
        return open(self, mode=mode, buffering=buffering,
                    encoding=encoding, errors=errors)

    def read_bytes(self):
        """Open the file in bytes mode, read it, and close the file."""
        with self.open(mode='rb') as f:
            return f.read()

    def write_bytes(self, data):
        """Open the file in bytes mode, write to it, and close the file."""
        with self.open('wb') as f:
            return f.write(data)

    def read_text(self, encoding=None, errors=None):
        """Open the file in text mode, read it, and close the file."""
        with self.open(mode='r', encoding=encoding, errors=errors) as f:
            return f.read()

    def write_text(self, text, encoding=None, errors=None):
        """Open the file in text mode, write to it, and close the file.

        Examples
        --------
        >>> p = Path('my_text_file')
        >>> p.write_text('Text file contents')
        18
        >>> p.read_text()
        'Text file contents'
        """
        with self.open('w', encoding=encoding, errors=errors) as f:
            return f.write(text)

    def read_lines(self, encoding=None, errors=None):
        """Open the file in text mode, read line by line, and close the file."""
        with self.open(mode='r', encoding=encoding, errors=errors) as f:
            for line in f:
                yield line.strip('\n')

    def write_lines(self, lines, end='\n', encoding=None, errors=None):
        """Open the file in text mode, write lines it, and close the file.

        Examples
        --------
        >>> p = Path('my_text_file1')
        >>> p.write_lines(['line 1', 'line 2'])
        >>> for line in p.read_lines(): print(line)
        line 1
        line 2
        """
        with self.open('w', encoding=encoding, errors=errors) as f:
            for line in lines:
                f.write(line+end)

    def scandir(self, types='H', pat=None, glob=None):
        """Iterate over all or some entries in a directory.

        Parameters
        ----------
        types: str
            A string with zero or more of the following characters limiting
            the entries to be returned certain types:

            h: a hidden path (its name is starting with a dot)
            d: a directory path
            f: a file path
            s: a symlink path

            The upper case of these characters are used to exclude those
            types from the result. Thus, the default types='H' will return
            all entries except the hidden ones.

        Returns
        -------
        A generator for entries in the directory path. If the Path is not
        a directory or not accessible, an exception is raised.

        See also
        --------
        iterdir: yield Path strings for the entries in the directory

        Examples
        --------
        >>> rootdirs = Path('/').scandir(types='Hd')
        >>> '/bin' in (d.path for d in rootdirs if d.name.startswith('b'))
        True
        """
        # TODO: In Python 3.10 use a match statement instead
        def match_type(entry, c):
            if c == 'h':
                return entry.name[0] == '.'
            elif c == 'd':
                return entry.is_dir()
            elif c == 'f':
                return entry.is_file()
            elif c == 's':
                return entry.is_symlink()
            else:
                raise ValueError(f"Invalid type {c}")
        if glob:
            import fnmatch
            pat = fnmatch.translate(glob)
        for entry in os.scandir(self):
            ok = True
            for c in types:
                lc = c.lower()
                m = match_type(entry, lc)
                ok &= m if lc == c else (not m)
                if not ok:
                    break
            if pat:
                if not re.fullmatch(pat, entry.name):
                    ok = False
            if ok:
                yield(entry)

    def iterdir(self, *args, **kargs):
        """Yield Path objects of the directory contents.

        This is like :meth:`scandir` but returns the entries as
        Path strings instead of plain strings.
        """
        for child in self.scandir(*args, **kargs):
            yield Path(child)

    def list(self, types='', sort=True, include=(), exclude=()):
        r"""List the entries in a directory path.

        Parameters
        ----------
        types: str, optional
            A string specifying which entry types should be included
            in the result. See :meth:`scandir`.
        sort: callable | bool, optional
            A callable to compute a sort key from the path name.
            Any other value evaluating to True will use the default
            :func:`Path.sortkey` providing case sensitive human sorting:
            numerical parts of the path name are sorted in numerical order.
            Any value evaluating to False leaves the list unsorted.
        include: :term:`re` or tuple of re
            Regular expression(s) for entry names to include in the list.
            Entries will be included if they match any of the re's.
        exclude: :term:`re` or tuple of re
            Regular expression(s) for entry names to exclude from the list.
            Entries will be excluded if they match any of the re's.
            Exclude matching is done after the include matching, so if both
            are provided and an entry maches both an include and an exclude re,
            it will not be included in the output list.

        Returns
        -------
        list of str
            List of the names of the entries that are of the specified types
            and match the include and exclude patterns, if provided.

        Notes
        -----
        The include and exclude patters are Python regular expressions (re)
        and the matches are done with re.fullmatch, thus the entire entry
        name needs to match the re. Thus, to get all Python sourec files,
        use ``include=r'.*\.py'``. Glob style file patterns can be translated
        to re's with :func:`fnmatch.translate`.

        Examples
        --------
        >>> Path('/').list('Hd', include='.*bin')
        ['bin', 'sbin']
        >>> Path('/').list('Hd', include='b.*', exclude='bu.*')
        ['bin', 'boot']
        """
        entries = [i.name for i in self.scandir(types=types)]
        if include:
            if isinstance(include, (str, bytes)):
                include = (include, )
            entries = [e for e in entries if matchAny(e, *include)]
        if exclude:
            if isinstance(exclude, (str, bytes)):
                exclude = (exclude, )
            entries = [e for e in entries if not matchAny(e, *exclude)]
        if sort:
            if not callable(sort):
                sort = Path.sortkey
            entries.sort(key=sort)
        return entries

    def dirnames(self, types='Hd', sort=True):
        """List the subdirectories in a directory path.

        Parameters
        ----------
        sort: callable | bool, optional
            Defines if and how to sort the entries. See :meth:`list`

        Returns
        -------
        list of str
            A list of the names of all directory type entries in the
            Path. If the Path is not a directory or not accessible,
            an exception is raised.

        Examples
        --------
        >>> Path('/').dirnames(types='H')
        ['bin', 'boot', ...]
        """
        if 'd' not in types:
            types += 'd'
        return self.list(types=types, sort=sort)

    def filenames(self, types='Hf', sort=True):
        """List the files in a directory path.

        Parameters
        ----------
        sort: callable | bool, optional
            Defines if and how to sort the entries. See :meth:`list`

        Returns
        -------
        list of str
            A list of the names of all file type entries in the
            Path. If the Path is not a directory or not accessible,
            an exception is raised.

        Examples
        --------
        >>> Path(__file__).parent.filenames(types='H')
        [...'path.py'...]

        See also
        --------
        allfiles: list all files, including those in subdirectories
        """
        if 'f' not in types:
            types += 'f'
        return self.list(types=types, sort=sort)

    def walk(self, *, sort=True, dtypes='HSd', ftypes='HSf',
             includedir=(), excludedir=(), includefile=(), excludefile=(),
             mindepth=0, maxdepth=-1, onerror=None,
             ):
        """Recursively walk through a directory.

        This walks top-down through the directory, yielding tuples
        ``root, dirs, files``, like :func:`os.walk`.

        Regular expressions can be provided to exclude or include only
        some specific directories or files.

        Parameters
        ----------
        sort: callable | bool, optional
            Defines if and how to sort the entries. See :meth:`list`
        dtypes: str, optional
            A string specifying which directory entry types should be included
            in the result. See :meth:`scandir`. The string should at least
            contain a 'd'. The default 'HSd' will not include hidden directories
            nor follow symlinked directories.
        ftypes: str, optional
            A string specifying which directory entry types should be included
            in the result. See :meth:`scandir`. The string should at least
            contain a 'f'. The default 'HSf' will not include hidden files
            nor symlinked files.
        excludedir: :term:`re` or tuple of re's
            Regular expression(s) for dirnames to exclude from the tree scan.
        excludefile: :term:`re`
            Regular expression(s) for filenames to exclude from the file list.
        includedir: :term:`re` or tuple of re's, optional
            Regular expression(s) for dirnames to include in the tree scan.
        includefile: :term:`re`
            Regular expression(s) for filenames to include in the file list.
        maxdepth: int, optional
            The maximum number of directory levels to descend. If < 0, descend
            all the way.
        onerror: callable, optional
            Exception handler that will be called when the walk fails to access
            some path. The callable is passed the exception and if it returns,
            the path causing the exception is skipped. Providing a do nothing
            function will just silently ignore the exceptions. If not provided,
            the exception is raised.

        Returns
        -------
        generator
            A generator for walking through a directory top down.
            The generator yields tuple (root, dirs, files) just like
            :func:`os.walk`, but the items returned can be restricted by many
            parameters.

        Notes
        -----
        Include patterns are applied before exclude patterns.
        If neither exclude nor include patterns are provided,
        all subdirectories are scanned and all files are reported.
        If only exclude patterns are provided, all directories and files
        except those matching any of the exclude patterns.
        If only include patterns are provided, only those matching at least
        one of the patterns are included.
        If both exclude and include patterns are provided, items are only
        listed if they match at least one of the include patterns but none
        of the exclude patterns.

        Directories where the user has no access permissions are silently
        skipped.
        """
        try:
            dirs = self.list(types=dtypes, sort=sort,
                             include=includedir, exclude=excludedir)
            if mindepth <= 0:
                yield self, dirs, self.list(
                    types=ftypes, sort=sort,
                    include=includefile, exclude=excludefile)
        except Exception as e:
            dirs = []
            if callable(onerror):
                onerror(e)
            else:
                raise e
        if maxdepth == 0:
            return
        for d in dirs:
            for res in (self / d).walk(
                    sort=sort, dtypes=dtypes, ftypes=ftypes,
                    includedir=includedir, excludedir=excludedir,
                    includefile=includefile, excludefile=excludefile,
                    maxdepth=maxdepth-1, mindepth=mindepth-1, onerror=onerror):
                yield res

    def walkTree(self, relative=False, include=[], exclude=[],
                 **kargs):
        """Generate a tree of directories and files under a directory path.

        This is like walk, but yields (dirpath, files) tuples and provides
        some extra options.

        Parameters
        ----------
        relative: bool
            If True, the reported dirpath is relative to self,
            else it is relative to the current directory from
            where the function is called.
        include: :term:`re` or tuple of re
            Regular expression(s) for files to be included in the list.
            Files will be included if their path matches any of the re's.
            If not provided, all files will be included.
        exclude: :term:`re` or tuple of re
            Regular expression(s) for files to be excluded from the list.
            Entries will be excluded if their path matches any of the re's.
            Exclude matching is done after the include matching, so if both
            are provided and an file maches both an include and an exclude re,
            it will not be included in the output list.
        **kargs: any of the arguments of :meth:`walk` can be provided.

        Returns
        -------
        generator
            A generator for walking through a directory top down.
            The generator yields tuples (dirpath, files).
        """
        for root, dirs, files in self.walk(**kargs):
            dirname = root.relative_to(self) if relative else root
            files = [dirname / f for f in files]
            if include:
                if isinstance(include, (str, bytes)):
                    include = (include, )
                files = [f for f in files if matchAny(f, *include)]
            if exclude:
                if isinstance(exclude, (str, bytes)):
                    exclude = (exclude, )
                files = [f for f in files if not matchAny(f, *exclude)]
            yield dirname, files

    def listTree(self, relative=False, include=[], exclude=[],
                 **kargs):
        """List files under a directory path recursively.

        Parameters
        ----------
        relative: bool
            If True, the reported filenames are relative to self,
            else, they are relative to the current directory from
            where the function is called.
        include: :term:`re` or tuple of re
            Regular expression(s) for files to be included in the list.
            Files will be included if their path matches any of the re's.
        exclude: :term:`re` or tuple of re
            Regular expression(s) for files to be excluded from the list.
            Entries will be excluded if their path matches any of the re's.
            Exclude matching is done after the include matching, so if both
            are provided and an file maches both an include and an exclude re,
            it will not be included in the output list.
        """
        # remove some undocumented parameters
        kargs.pop('symlinks', None)
        kargs.setdefault('sort', kargs.pop('sorted', True))
        allfiles = []
        for root, dirs, files in self.walk(**kargs):
            d = root.relative_to(self) if relative else root
            files = [d/f for f in files]
            if include:
                if isinstance(include, (str, bytes)):
                    include = (include, )
                files = [f for f in files if matchAny(f, *include)]
            if exclude:
                if isinstance(exclude, (str, bytes)):
                    exclude = (exclude, )
                files = [f for f in files if not matchAny(f, *exclude)]
            allfiles.extend(files)
        return allfiles

    def glob(self, pattern=None, *, recursive=True):
        r"""Return a list of paths matching a pattern.

        Parameters
        ----------
        pattern: str, optional
            A pattern to join to the Path to create the full search
            pattern. The search pattern can contain \* and ? wildcards,
            and [] character ranges, and the extended \*\* wildcard if
            recursive is True.
        recursive: bool
            If True (default), match recursively. A \*\* wildcard
            matches all existing files and all subdirectories
            of any level. If followed by a /, it only matches
            directories.
            If False, \*\* behaves the same as a single \*.

        Returns
        -------
        list of Path
            A sorted list of existing paths matching the pattern.

        Notes
        -----
        This method works differently from :meth:`pathlib.Path.glob`.
        Wildcards can also be part of the calling Path.
        Thus, ``Path(path).glob(pat)`` is equivalent to
        ``(Path(path) / pat).glob()``.

        See Also
        --------
        listTree: find files matching regular expressions

        Examples
        --------
        >>> Path('/etc/init.d').glob()
        [Path('/etc/init.d')]
        >>> mydir = Path(__file__).parent
        >>> (mydir / 'pr*.py').glob()
        [Path('.../pyformex/process.py'), Path('.../pyformex/project.py')]
        >>> (mydir / 'pa*.py').glob()
        [Path('.../pyformex/path.py')]
        >>> (mydir / '**/pa*t*.py').glob()
        [Path('.../pyformex/path.py'), Path('.../pyformex/plugins/partition.py')]
        >>> (mydir / '**/pa*t*.py').glob(recursive=False)
        [Path('.../pyformex/plugins/partition.py')]
        """
        import glob
        pattern = self if pattern is None else self / pattern
        return sorted([Path(i) for i in glob.glob(pattern, recursive=recursive)],
                      key=Path.sortkey)

    def filetype(self, compressed=['.gz', '.bz2']):
        """Return a normalized file type based on the filename suffix.

        The returned suffix is in most cases the part of the filename starting
        at the last dot. However, if the thus obtained suffix is one of the
        specified compressed types (default: .gz or .bz2) and the file contains
        another dot that is not at the start of the filename, the returned suffix
        starts at the penultimate dot.
        This allows for transparent handling of compressed files.

        Parameters
        ----------
        compressed: list of str
            List of suffixes that are considered compressed file types.

        Returns
        -------
        str
            The filetype. This is the file suffix converted to lower case
            and without the leading dot. If the suffix is included in
            ``compressed``, the returned suffix also includes the preceding
            suffix part, if any.

        See Also
        --------
        ftype: the file type without accounting for compressed types


        Examples
        --------
        >>> Path('pyformex').filetype()
        ''
        >>> Path('pyformex.pgf').filetype()
        'pgf'
        >>> Path('pyformex.pgf.gz').filetype()
        'pgf.gz'
        >>> Path('pyformex.gz').filetype()
        'gz'
        >>> Path('abcd/pyformex.GZ').filetype()
        'gz'
        """
        ext = self.lsuffix
        if ext in compressed:
            ext1 = Path(self.stem).lsuffix
            if ext1:
                ext = ext1+ext
        return ext.lstrip('.')

    def ftype_compr(self, compressed=['.gz', '.bz2']):
        """Return the file type and compression based on suffix.

        Parameters
        ----------
        compressed: list of str
            List of suffixes that are considered compressed file types.

        Returns
        -------
        ftype: str
            File type based on the last suffix if it is not a compression
            type, or on the penultimate suffix if the file is compressed.
        compr: str
            Compression type. This is the last suffix if it is one of the
            compressed types, or an empty string otherwise.

        Examples
        --------
        >>> Path('pyformex').ftype_compr()
        ('', '')
        >>> Path('pyformex.pgf').ftype_compr()
        ('pgf', '')
        >>> Path('pyformex.pgf.gz').ftype_compr()
        ('pgf', 'gz')
        >>> Path('pyformex.gz').ftype_compr()
        ('gz', '')
        """
        ftype = self.filetype(compressed)
        i = ftype.find('.')
        if i >= 0:
            return ftype[:i], ftype[i+1:]
        else:
            return ftype, ''

    @staticmethod
    def cwd():
        """Return the current working directory

        Returns
        -------
        Path
            The current working directory.

        """
        return Path(os.getcwd())

    @staticmethod
    def home():
        """Return the user's home directory.

        Returns
        -------
        Path
            The user's home directory as defined by the environment
            variable HOME.
        """
        return Path(os.environ['HOME'])


if __name__ == "__main__":
    import doctest
    failures, tests = doctest.testmod(
        optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)
    print(f"{__file__}: Tests: {tests}; Failures: {failures}")

# End
