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
"""Detecting and checking installed software

A module to help with detecting required software and helper software,
and to check the versions of it.
"""

import os
import sys
import importlib
import re
import operator

import pyformex as pf
from pyformex import process

# We have included this source here because distutils will be removed
# from Python, the replacement setuptools.distutils does not contain
# version.LooseVersion, and the recommanded Version replacement from
# packaging.version only deals with Python style version numbers.
# We however also want to treat version numbers of a bunch of non-Python
# packages, which may not follow Python's versioning style.

class RequirementError(Exception):
    pass


class Version:
    """Abstract base class for version numbering classes.  Just provides
    constructor (__init__) and reproducer (__repr__), because those
    seem to be the same for all version numbering classes; and route
    rich comparisons to _cmp.

    Based on distutils.version, which is scheduled for withdrawal from Python.

    Interface for version-number classes -- must be implemented
    by the following classes (the concrete ones -- Version should
    be treated as an abstract class)::

        __init__ (string) - create and take same action as 'parse'
        parse (string)    - convert a string representation to whatever
                            internal representation is appropriate for
                            this style of version numbering
        __str__ (self)    - convert back to a string; should be very similar
                            (if not identical to) the string supplied to parse
        __repr__ (self)   - generate Python code to recreate
                            the instance
        _cmp (self, other) - compare two version numbers ('other' may
                            be an unparsed version string, or another
                            instance of your version class)
    """
    def __init__ (self, vstring):
        self.parse(vstring)

    def __repr__ (self):
        return "%s ('%s')" % (self.__class__.__name__, str(self))

    def __eq__(self, other):
        c = self._cmp(other)
        if c is NotImplemented:
            return c
        return c == 0

    def __lt__(self, other):
        c = self._cmp(other)
        if c is NotImplemented:
            return c
        return c < 0

    def __le__(self, other):
        c = self._cmp(other)
        if c is NotImplemented:
            return c
        return c <= 0

    def __gt__(self, other):
        c = self._cmp(other)
        if c is NotImplemented:
            return c
        return c > 0

    def __ge__(self, other):
        c = self._cmp(other)
        if c is NotImplemented:
            return c
        return c >= 0


class SaneVersion(Version):
    """Version numbering for anarchists and software realists.

    Based on distutils.version, which is scheduled for removal from Python.

    Implements the standard interface for version number classes as
    described above.  A version number consists of a series of numbers,
    separated by either periods or strings of letters.  When comparing
    version numbers, the numeric components will be compared
    numerically, and the alphabetic components lexically.  The following
    are all valid version numbers, in no particular order:

        1.5.1
        1.5.2b2
        161
        3.10a
        8.02
        3.4j
        1996.07.12
        3.2.pl0
        3.1.1.6
        2g6
        11g
        0.960923
        2.2beta29
        1.13++
        5.5.kw
        2.0b1pl0

    In fact, there is no such thing as an invalid version number under
    this scheme; the rules for comparison are simple and predictable,
    but may not always give the results you want (for some definition
    of "want").

    Examples
    --------
    >>> SaneVersion('2.2beta29').version
    [2, 2, 'beta', 29]
    """
    component_re = re.compile(r'(\d+ | [a-z]+ | \.)', re.VERBOSE)

    def parse (self, vstring):
        # I've given up on thinking I can reconstruct the version string
        # from the parsed tuple -- so I just store the string here for
        # use by __str__
        self.vstring = vstring
        components = [x for x in self.component_re.split(vstring)
                      if x and x != '.']
        for i, obj in enumerate(components):
            try:
                components[i] = int(obj)
            except ValueError:
                pass
        self.version = components

    def __str__ (self):
        return self.vstring

    def __repr__ (self):
        return "SaneVersion ('%s')" % str(self)

    def _cmp (self, other):
        if isinstance(other, str):
            other = SaneVersion(other)
        elif not isinstance(other, SaneVersion):
            return NotImplemented

        if self.version == other.version:
            return 0
        if self.version < other.version:
            return -1
        if self.version > other.version:
            return 1


class Software():
    """Register for software versions.

    This class holds a register of the version of installed software.
    The class is not intended to be used directly, but rather through the
    derived classes Module and External.

    Parameters
    ----------
    name: str
        The software name as known in pyFormex: this is often the same as
        the real software name, but can be different if the real software
        name is complex. We try to use simple lower case names in pyFormex.


    The default software object only has two attributes:

    Examples
    --------
    >>> np = Software('numpy')
    >>> Software.print_all()
      numpy (** Not Found **)
    >>> Software.has('numpy')
    ''
    >>> np.detect('detected')
    'detected'
    >>> Software.has('numpy')
    'detected'
    >>> Software.require('numpy')
    >>> Software.has('foo')
    Traceback (most recent call last):
    pyformex.software.RequirementError: foo is not a registered Software
    >>> foo = Software('foo')
    >>> Software.require('foo')
    Traceback (most recent call last):
    pyformex.software.RequirementError: Required Software 'foo' (foo) not found
    >>> Software.print_all()
      numpy (detected)
      foo (** Not Found **)
    >>> Software('foo')
    Traceback (most recent call last):
    ValueError: A Software with name 'foo' is already registered
    """
    register = dict()

    def __init__(self, name):
        """Create a registered software name"""
        if name in Software.register:
            raise ValueError(f"A {self.__class__.__name__} "
                             f"with name '{name}' is already registered")
        self.name = name
        self._version = None
        self.__class__.register[name] = self

    def __str__(self):
        return f"{self.__class__.__name__} {self.name} {self._version}"


    @property
    def version(self):
        """Return the version of the software, if installed.

        If the software has already been detected, just returns the
        stored version string. Else, runs the software :meth:`detect`
        method and stores and returns the version string.

        Returns
        -------
        str
            The version of the software, or an empty string if the software
            can not be detected.
        """
        if self._version is None:
            self.detect()
        return self._version

    @version.setter
    def version(self, value):
        self._version = value


    def detect(self, version='', fatal=False, quiet=False):
        """Detect the version of the software.

        Parameters
        ----------
        version: str
            The version string to be stored for a detected software.
            The default empty string means the software was not detected.
            Derived classes should call this method fromt their detect
            method and pass a non-empty string for detected softwares.
        fatal: bool, optional
            If True and the software can not be loaded, a fatal exception
            is raised. Default is to silently ignore the problem and return
            an empty version string.
        quiet: bool, optional
            If True, the whole operation is done silently. The only
            information about failure will be the returned empty version string.

        Returns
        -------
        str
            The version string of the software, empty if the software can not
            be loaded.

        Notes
        -----
        As a side effect, the detected version string is stored for later
        reuse. Thus subsequent tests will not try to re-detect.
        """
        if version:
            pf.debug(f"Congratulations! You have {self.name} ({version})",
                     pf.DEBUG.DETECT)
        else:
            if not fatal:
                pf.debug(f"ALAS! I could not find {self.__class__.__name__} "
                         f"'{self.name}' on your system", pf.DEBUG.DETECT)
            if fatal:
                raise pf.RequirementsError(
                    f"""\
                    A required {self.__class__.__name__} was not found:
                    {self.name}
                    You should install this software and restart pyFormex.\
                    """)
        self.version = version
        return self.version


    @classmethod
    def detect_all(clas):
        """Detect all registered softwares.

        Usually, the detection is only performed when needed.
        Calling this method will perform the detection for all
        registered softwares.
        """
        for name in clas.register:
            clas.register[name].detect()


    @classmethod
    def print_all(clas):
        """Print the list of registered softwares"""
        for name in clas.register:
            version = clas.register[name].version
            if not version:
                version = '** Not Found **'
            print(f"  {name} ({version})")


    @classmethod
    def detected(clas, all=False):
        """Return the successfully detected softwares and their version

        Returns
        -------
        dict
            A dict with the software name as key and the detected version
            as value.
        """
        return dict([(k, clas.register[k].version) for k in
                     clas.register if all or clas.register[k].version])


    @classmethod
    def has(clas, name, check=False, fatal=False, quiet=False):
        """Test if we have the named software available.

        Returns a nonzero (version) string if the software is available,
        or an empty string if it is not.

        By default, the software is only checked on the first call.
        The optional argument check==True forces a new detection.
        """
        if name not in clas.register:
            raise RequirementError(f"{name} is not a registered {clas.__name__}")
        if check or clas.register[name].version is None:
            clas.register[name].detect(fatal=fatal, quiet=quiet)
        return clas.register[name].version


    @classmethod
    def check(clas, name, version):
        """Check that we have a required  version of a software.

        """
        ver = clas.has(name)
        return compareVersion(ver, version)


    @classmethod
    def require(clas, name, version=None):
        """Ensure that the named Python software/version is available.

        Checks that the specified software is available, and that its version
        number is not lower than the specified version.
        If no version is specified, any version is ok.

        Returns if the required software/version could be loaded, else an
        error is raised.

        """
        if pf.sphinx:
            # Do not check when building docs
            return

        ver = clas.has(name)
        if not ver:
            realname = clas.register[name].name
            errmsg = f"""..

    **{clas.__name__} {name} not found!**

    You activated some functionality requiring the {clas.__name__} '{realname}'.
    However, the {clas.__name__} '{realname}' could not be found.
    Probably it is not installed on your system.
    """
            pf.error(errmsg)
            raise RequirementError(f"Required {clas.__name__} '{name}' ({realname}) not found")

        else:
            if version is not None:
                if not compareVersion(ver, version):
                    realname = clas.register[name].name
                    errmsg = f"""..

    **{clas.__name__} version {name} ({ver}) does not meet requirements ({version})!**

    You activated some functionality requiring {clas.__name__} '{realname}'.
    However, the required version for that software could not be found.
    """
                    pf.error(errmsg)
                    raise RequirementError(
                        f"Required version ({version}) of {clas.__name__} "
                        f"'{name}' ({realname}) not found")



class Module(Software):
    """Register for Python module version detection rules.

    This class holds a register of version detection rules for installed
    Python modules. Each instance holds the rule for one module, and
    it is automatically registered at instantiation. The modules used
    by pyFormex are declared in this module, but users can add their own
    just by creating a Module instance.

    Parameters
    ----------
    name: str
        The module name as known in pyFormex: this is often the same as
        the Python module name, but can be different if the Python module
        name is complex. We try to use simple lower case names in pyFormex.
    modname: str, optional
        The correct Python package.module name. If not provided, it is
        equal to the pyFormex name.
    attr: str or tuple of str, optional
        If a str, it is the name of the attribute holding the module version.
        This should be an attribute of the module `modname`. The default
        is '__version__', as it is used by many projects.
        If the version is not stored in a direct attribute of the same module
        as used for the detection, then a tuple of strings can be specified,
        starting with the Python module name in which the version attribute
        is stored, and a list of subsequent attribute names leading to the
        version. In this case the first element of the tuple is always a
        module name. If it is the same as `modname`, an empty string may be
        specified.
        If the final attribute is a callable, it will be called to get the
        version. The result is always converted to str before being stored
        as the version.
    incompatible: tuple of str, optional
        A list of incompatible modules. If any of these modules is loaded,
        the Module will not be tried. Beware: this should be the actual module
        names, not the pyFormex component name, which is all lower case.

    Examples
    --------
    >>> Module.register.clear()
    >>> Module.detect_all()
    >>> Module.print_all()
    >>> np = Module('numpy')
    >>> pil = Module('pil', modname='PIL', attr='VERSION')
    >>> Module.print_all()
      numpy (1...)
      pil (** Not Found **)
    >>> SaneVersion(Module.has('numpy')) >= SaneVersion('1.16')
    True
    >>> Module.print_all()
      numpy (1...)
      pil (** Not Found **)
    >>> Module.has('foo')
    Traceback (most recent call last):
    pyformex.software.RequirementError: foo is not a registered Module
    >>> Module.require('foo')
    Traceback (most recent call last):
    pyformex.software.RequirementError: foo is not a registered Module
    >>> foo = Module('foo','FooBar')
    >>> Module.has('foo')
    ''
    >>> Module.require('foo')
    Traceback (most recent call last):
    pyformex.software.RequirementError: Required Module 'foo' (FooBar) not found

    Now fake a detection of Module 'foo'

    >>> Module.register['foo'].version = '1.2.3'
    >>> Module.has('foo')
    '1.2.3'
    >>> Module.require('foo')
    >>> Module.require('foo','>= 1.1.7')
    >>> Module.require('foo','>= 1.3.0')
    Traceback (most recent call last):
    pyformex.software.RequirementError: Required version (>= 1.3.0) of Module 'foo' (FooBar) not found

    """

    register = dict()

    def __init__(self, name, modname=None, attr=None, incompatible=None):
        """Create a registered Python module detection rule"""
        super().__init__(name)
        if modname is None:
            modname = name   # default: name == modname
        if attr is None:
            attr = '__version__'   # many packages use this
        self.name = modname
        self.attr = attr
        self.incompatible = incompatible


    def detect(self, fatal=False, quiet=False):
        """Detect the version of the module.

        Parameters
        ----------
        fatal: bool, optional
            If True and the module can not be loaded, a fatal exception
            is raised. Default is to silently ignore the problem and return
            an empty version string.
        quiet: bool, optional
            If True, the whole operation is done silently. The only
            information about failure will be the returned empty version string.

        Returns
        -------
        str
            The version string of the module, empty if the module can not
            be loaded.

        Notes
        -----
        As a side effect, the detected version string is stored for later
        reuse. Thus subsequent tests will not try to re-detect.
        """
        try:
            pf.debug(self.name, pf.DEBUG.DETECT)
            if self.incompatible:
                if any([m in sys.modules for m in self.incompatible]):
                    raise ImportError(
                        f"Module {self.name} is incompatible with"
                        f" {self.incompatible}")
            m = importlib.import_module(self.name)
            pf.debug(m, pf.DEBUG.DETECT)
            if isinstance(self.attr, str):
                # simple attribute in loaded module
                ver = (self.attr,)
            else:
                # tuple of subsequent attributes, first is module name
                if self.attr[0]:
                    m = importlib.import_module(self.attr[0])
                    pf.debug(m, pf.DEBUG.DETECT)
                ver = self.attr[1:]
            for a in ver:
                m = getattr(m, a)
                pf.debug(m, pf.DEBUG.DETECT)
        except Exception as e:
            # failure: unexisting or unregistered modules
            if fatal:
                raise e
            m = ''
            # If the attribute is a callable, call it
        if callable(m):
            m = m()
            # if a tuple is returned, turned it into a string
            if isinstance(m, tuple):
                m = '.'.join(map(str, m))
        # make sure version is a string (e.g. gl2ps uses a float!)
        version = str(m)
        super().detect(version, fatal)
        return self.version


Module('pyformex')
Module('calpy')
Module('docutils')
Module('gl2ps', attr='GL2PS_VERSION')
Module('gnuplot', modname='Gnuplot')
# Module('ipython', modname='IPython',)
# Module('ipython-qt', modname='IPython.frontend.qt',)
Module('matplotlib')
Module('meshio')
Module('moderngl')
Module('numpy')
Module('pil', modname='PIL')
Module('pydicom')
Module('pyopengl', modname='OpenGL')
Module('pyqt5', modname='PyQt5.QtCore',
       attr='PYQT_VERSION_STR',
       incompatible=('PySide2',))
Module('pyqt5gl', modname='PyQt5.QtOpenGL',
       attr=('PyQt5.QtCore', 'PYQT_VERSION_STR'),
       incompatible=('PySide2',))
Module('pyside2', modname='PySide2', incompatible=('PyQt5',))
Module('scipy')
Module('sphinx')
Module('vtk', attr='VTK_VERSION')


class External(Software):
    """Register for external application version detection rules.

    This class holds a register of version detection rules for installed
    external applications. Each instance holds the rule for one application,
    and it is automatically registered at instantiation. The applications used
    by pyFormex are declared in this module, but users can add their own
    just by creating an External instance.

    Parameters
    ----------
    name: str
        The application name as known in pyFormex: this is often the same as
        the executable name, but can be different if the executable
        name is complex. We try to use simple lower case names in pyFormex.
    command: str
        The command to run the application. Usually this includes an option
        to make the application just report its version and then exit.
        The command should be directly executable as-is, without invoking
        a new shell. If a shell is required, it should be made part of the
        command (see e.g. tetgen). Do not use commands that take a long
        time to load and run.
    regex: r-string
        A regular expression that extracts the version from the output of
        the command. If the application does not have or report a version,
        any non-empty string is accepted as a positive detection (for
        example the executable's name in a bin path). The regex string
        should contain one set of grouping parentheses, delimiting the
        part of the output that will be stored as version. If the output
        of the command does not match, an empty string is stored.

    Examples
    --------
    >>> External.register.clear()
    >>> External.detect_all()
    >>> External.print_all()
    """

    register = dict()

    def __init__(self, name, command, regex):
        """Create a registered external executable detection rule"""
        super().__init__(name)
        self.command = command
        self.regex = regex


    def detect(self, fatal=False, quiet=False):
        """Detect the version of the external.

        Parameters
        ----------
        fatal: bool, optional
            If True and the external can not be run, a fatal exception
            is raised. Default is to silently ignore the problem and return
            an empty version string.
        quiet: bool, optional
            If True, the whole operation is done silently. The only
            information about failure will be the returned empty version string.

        Returns
        -------
        str
            The version string of the external, empty if the external can not
            be run.

        Notes
        -----
        As a side effect, the detected version string is stored for later
        reuse. Thus subsequent tests will not try to re-detect.
        """
        pf.debug(f"Check {self.name}\n{self.command}", pf.DEBUG.DETECT)
        P = process.run(self.command)
        pf.debug(f"returncode: {P.returncode}\n"
                 f"stdout:\n{P.stdout}\nstderr:\n{P.stderr}",
                 pf.DEBUG.DETECT)
        version = ''
        # Some programs write their version to stderr, others to stdout
        # So we have to try both
        m = None
        if P.stdout:
            m = re.match(self.regex, P.stdout)
        if m is None and P.stderr:
            m = re.match(self.regex, P.stderr)
        if m:
            version = str(m.group(1))

        super().detect(version, fatal)
        return self.version


External('python', 'python3 --version', r'Python (\S+)')
External('admesh', 'admesh --version', r'ADMesh - version (\S+)')
External('calculix', "ccx -v|tr '\n' ' '", r'[\n]*.*ersion (\S+)')
External('calix', 'calix --version', r'CALIX-(\S+)')
External('calpy', 'calpy3 --version', r'calpy (\S+)')
External('dxfparser', 'pyformex-dxfparser --version', r'dxfparser (\S+)')
External('ffmpeg', 'ffmpeg -version', r'[fF][fF]mpeg version (\S+)')
External('freetype', 'freetype-config --ftversion', r'(\S+)')
External('gts', 'gtsset -h', r'Usage: (gts)')
External('gts-bin', 'gts2stl -h', r'Usage: (gts)')
External('gts-extra', 'gtsinside -h', r'Usage: (gts)')
External('imagemagick', 'import -version', r'Version: ImageMagick (\S+)')
External('instant-meshes', 'instant-meshes -h', r'Syntax: (instant-meshes)')
External('postabq', 'pyformex-postabq -V', r'postabq (\S+).*')
External('recordmydesktop', 'recordmydesktop --version', r'recordMyDesktop v(\S+)')
External('sphinx-build', "sphinx-build --version", r'sphinx-build (\S+)')
External('tetgen', "bash -c 'type -p tetgen'", r'\S+(tetgen)')
External('units', 'units --version', r'GNU Units version (\S+)')
External('zip', 'zip -h', r'.*\nZip (\S+)')


def listLibraries():
    """Return a list with the acceleration libraries"""
    from pyformex import lib
    return [m.__name__ for m in lib.accelerated]


def listShaders():
    """Return a list with the available GPU shader programs.

    Returns
    -------
    list
        A list of the shader versions available.

    Notes
    -----
        Shader programs are stored in the pyformex/glsl directory and consist
        of at least of two files: 'vertex_shader_SHADER.c' and
        'fragment_shader_SHADER.c'. The SHADER part is the version mnemomic
        which can be used in the '--shader SHADER' option of the pyformex
        command.
    """
    files = pf.cfg['shaderdir'].listTree(
        includefile=['vertex_shader_.*[.]c$', 'fragment_shader_.*[.]c$'])
    files = [f.name for f in files]
    vshaders = [f[14:-2] for f in files if f.startswith('v')]
    fshaders = [f[16:-2] for f in files if f.startswith('f')]
    shaders = set(vshaders) & set(fshaders)
    return sorted(shaders)


def detectedSoftware(comp='SME'):
    """Return a dict with detected software.

    Parameters
    ----------
    comp: str
        The components to be detected. The string is composed of the
        characters 'S', M' and 'E', each identifying one of the components:

        - S: detects system software including Python and pyFormex,
        - M: detects Python modules used by pyFormex,
        - E: detects software used by pyFormex as external commands.

     Returns
    -------
    dict
        A dict with one or more of the keys 'System', 'Modules' and 'Externals',
        each having a dict as value:

        - System: contains information about system, pyFormex, Python
        - Modules: the detected Python modules
        - Externals: the detected external programs
    """
    soft = {}
    if 'S' in comp:
        system, host, release, version, arch = os.uname()
        System = {
            'pyFormex_version': pf.__version__.split()[0],
            'pyFormex_installtype': pf.installtype,
            'pyFormex_fullversion': pf.fullVersion(),
            'pyFormex_libraries': ', '.join(listLibraries()),
            'pyFormex_shaders': ', '.join(listShaders()),
            'Python_version': sys.version.split()[0],
            'Python_fullversion': sys.version.replace('\n', ' '),
            'System': system,
            'Host': host,
            'Release': release,
            'Version': version,
            'Arch': arch,
        }
        if pf.GUI:
            System['Qt bindings'] = pf.gui.bindings
        soft['System'] = System
    if 'M' in comp:
        Module.detect_all()
        soft['Modules'] = Module.detected(all=True)
    if 'E' in comp:
        External.detect_all()
        soft['Externals'] = External.detected(all=True)
    return soft


def reportSoftware(soft=None, header=None, sort=False):
    from pyformex import utils
    notfound = '** Not Found **'

    def format_dict(d, sort):
        keys = sorted(d.keys()) if sort else d
        items = [f"  {k} ({d[k] if d[k] else notfound})" for k in keys]
        return '\n'.join(items)

    if soft is None:
        soft = detectedSoftware()
    s = ""
    if header:
        header = str(header)
        s += utils.underlineHeader(header)
    for key, desc, srt in [
            ('System', 'Installed System', False),
            ('Modules', 'Detected Python Modules', sort),
            ('Externals', 'Detected External Programs', sort)
    ]:
        s += f"\n{desc}:\n"
        s += format_dict(soft[key], srt)
        s += '\n'
    return s


comparators = {
    '==': operator.__eq__,
    '!=': operator.__ne__,
    '>': operator.__gt__,
    '>=': operator.__ge__,
    '<': operator.__lt__,
    '<=': operator.__le__,
}

_re_Required = re.compile(r'(?P<cmp>(==|!=|([<>]=?)))? *(?P<require>.*)')


def compareVersion(has, want):
    """Check whether a detected version matches the requirements.

    has is the version string detected.
    want is the required version string, possibly preceded by one
    of the doubly underscored comparison operators: __gt__, etc.
    If no comparison operator is specified, '__eq__' is assumed.

    Note that any tail behind x.y.z version is considered to  be later
    version than x.y.z.

    Returns the result of the comparison: True or False
    Examples:

      >>> compareVersion('2.7','2.4.3')
      False
      >>> compareVersion('2.7','>2.4.3')
      True
      >>> compareVersion('2.7','>= 2.4.3')
      True
      >>> compareVersion('2.7','>= 2.7-rc3')
      False
      >>> compareVersion('2.7-rc4','>= 2.7-rc3')
      True

    """
    if not has:
        return False
    m = _re_Required.match(want)
    if not m:
        return False

    d = m.groupdict()
    want = d['require']
    comp = d['cmp']
    if comp is None:
        comp = '=='
    has = SaneVersion(has)
    want = SaneVersion(want)
    return comparators[comp](has, want)


def checkItem(has, want):
    if compareVersion(has, want):
        return 'OK'
    else:
        return 'FAIL'


def checkDict(has, want):
    """Check that software dict has has the versions required in want"""
    return [(k, has[k], want[k], checkItem(has[k], want[k])) for k in want]


# TODO: only detect the components in requirements
# because detecting everything is slow
def checkSoftware(req, report=False):
    """Check that we have the matching components

    Returns True or False.
    If report=True, also returns a string with a full report.
    """
    from pyformex import utils
    soft = detectedSoftware()
    comp = []
    for k in req:
        comp.extend(checkDict(soft[k], req[k]))
    result = all([s[3] == 'OK' for s in comp])
    fmt = "%30s %15s %15s %10s\n"
    if report:
        s = utils.underlineHeader(fmt % ("Item", "Found", "Required", "OK?"))
        for item in comp:
            s += fmt % item
        s += f"RESULT={'OK' if result else 'FAIL'}"
        return result, s
    else:
        return result


def registerSoftware(req):
    """Register the current values of required software"""
    from pyformex import utils
    soft = detectedSoftware()
    reg = dict()
    for k in req:
        reg[k] = utils.selectDict(soft[k], list(req[k].keys()))
    return reg


def formatDict(d, indent=2, sort_keys=False, mode='json'):
    """Format a possibly nested dict

    >>> d = {'a':0, 'd':{'y':'s', 'x':'t'}, 'b':1}
    >>> print(formatDict(d))
    {
      "a": 0,
      "d": {
        "y": "s",
        "x": "t"
      },
      "b": 1
    }
    >>> print(formatDict(d, mode='python'))
    {'a': 0, 'd': {'y': 's', 'x': 't'}, 'b': 1}
    """
    if mode == 'json':
        import json
        return json.dumps(d, indent=indent, sort_keys=False)
    else:
        return f"{d!r}"


def storeSoftware(soft, fn, mode='json', indent=2):
    """Store the software collection on file.

    The collection is by default stored in JSON format.
    """
    with open(fn, 'w') as fil:
        fil.write(formatDict(soft, indent=indent, mode=mode))
        fil.write('\n')


def readSoftware(fn):
    """Read the software collection from file.

    Default mode is 'python' because it reads json as well as python.
    'legacy' can be used to read old software files, though it is
    recommended to change the files by removing the 'soft = ' at the start.
    """
    with open(fn, 'r') as fil:
        txt = fil.read()
        if txt.startswith('soft'):
            # This is probably a legacy format
            txt = txt.split('=')[1]
        soft = eval(txt)
    return soft


#### execute as pyFormex script for testing ########

if __name__ in ["_draw__", "__script__"]:

    Required = {
        'System': {
            'pyFormex_installtype': 'R',
            'Python_version': '>= 3.7.0',
        },
        'Modules': {
            'pyformex': '>= 2.7',
            'matplotlib': '1.1.1',
            'numpy': '1.16',
        },
        'Externals': {
            'admesh': '>= 0.95',
        },
    }

    soft = detectedSoftware()
    print((reportSoftware(header="Detected Software")))
    print('\n ')
    print((reportSoftware(Required, header="Required Software")))
    print('\n ')

    print('CHECK')
    ok, report = checkSoftware(Required, True)
    print(report)

    reg = registerSoftware(Required)
    print("REGISTER")
    print(formatDict(reg))

    storeSoftware(reg, 'checksoft.json')
    req = readSoftware('checksoft.json')
    print('CHECK REGISTERED')
    print(formatDict(req))

    ok, report = checkSoftware(req, True)
    print(report)

# End
