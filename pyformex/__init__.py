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

"""pyFormex core module initialization.

This module initializes the pyFormex global variables and
defines a few essential functions.
It is the very first thing that is loaded when starting pyFormex.
"""
import datetime
start_time = datetime.datetime.now()

import os, sys
#import importlib
import logging
import logging.config
#from getpass import getuser

__prog__ = "pyformex"
__version__ = "3.4.dev0"
__revision__ = __version__
__branch__ = "master"
Copyright = 'Copyright (C) 2004-2023 Benedict Verhegghe'
Url = 'http://pyformex.org'
Description = ("pyFormex is a tool for generating, manipulating and "
               "transforming large geometrical models of 3D structures "
               "by sequences of mathematical transformations.")


def Version():
    """Return a string with the pyFormex name and version"""
    return f"pyFormex {__version__}"


def fullVersion():
    """Return a string with the pyFormex name, version and revision"""
    if __revision__ == __version__:
        return Version()
    else:
        return f"{Version()} ({__revision__}) DEVELOPMENT VERSION"


startup_warnings = []
started = False

# Fatal errors
class FatalError(Exception):
    """Raised on fatal or grave errors"""
    def __init__(self, msg):
        from inspect import cleandoc as dedent
        s = '\n' + '#' * 72
        s = '\n##  '.join([s] + dedent(msg).split('\n')) + s
        Exception.__init__(self, s)


class RequirementsError(FatalError):
    """Raised on missing or invalid requirements"""
    pass

class ImplementationError(FatalError):
    """Raised on clear implementation errors"""
    pass


#########  Check Python version #############

# intended Python version
# We only support 3.8+ because we use self documenting f-strings
_minimal_version = 0x03080000
_target_version = 0x03090000
_numpy_version = '>=1.16'

def major(v):
    """Return the major component of version"""
    return v >> 24


def minor(v):
    """Return the minor component of version"""
    return (v & 0x00FF0000) >> 16


def human_version(v):
    """Return the human readable string for version"""
    return f"{major(v)}.{minor(v)}"


if sys.hexversion < _minimal_version:
    # Older than minimal
    y = human_version(sys.hexversion)
    m = human_version(_minimal_version)
    raise RequirementsError(f"""
Your Python version is {y}, but pyFormex requires Python >= {m}.
We advice you to upgrade your Python version.
""")

if sys.hexversion & 0xFFFF0000 > _target_version:
    # Major,minor newer than target:
    y = human_version(sys.hexversion)
    t = human_version(_target_version)
    startup_warnings.append(f"""
Your Python version is {y}, but pyFormex has only been tested
with Python <= {t}. We expect pyFormex to run correctly with
your Python version, but if you encounter problems, please
contact the developers at http://pyformex.org.
""")

###################################################################
## Load Path class
##################

from pyformex.path import Path  # noqa: E402

# Placeholder for excutable, if pyformex: filled in by startup.py
executable = Path(sys.executable)

#### Detect install type ########

# Install type.
# This can have the following values:
#     'G' : unreleased version running from GIT sources: no installation
#           required. This is set if the directory containing the
#           pyformex start script is a git repository.
#     'U' : normal (source) Release, i.e. tarball installed as user.
#           Installation is done with 'python setup.py install'
#           in the unpacked source.
#           The builtin pyFormex removal is activated.
#     'R' : normal (source) Release, i.e. tarball (default). Installation
#           is done with 'python setup.py install' in the unpacked source.
#           The builtin pyFormex removal is activated.
#     'D' : Distribution package of a released version, official or not
#           (e.g. Debian package). The distribution package tools should
#           be used to install/uninstall. The builtin pyFormex removal is
#           deactivated.
#
installtype = 'R'

pyformexdir = Path(__file__).parent
if (pyformexdir.parent / '.git').exists():
    installtype = 'G'
if installtype == 'R':
    if os.getuid() != 0 and (pyformexdir / 'doc').is_writable_dir():
        installtype = 'U'

########## start the logger ####################
# TODO: this is work in progress
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        'short': {
            'format': "%(asctime)s %(message)s",
        },
        'detail': {
            'format': "%(asctime)s::%(levelname)s::%(name)s::"
            "%(filename)s::%(lineno)d::%(message)s",
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'detail',
        },
        'memory': {
            'class': 'logging.handlers.MemoryHandler',
            'capacity': 100,
            'formatter': 'default',
        },
        # TODO: activate logfile, but we cant use pf.cfg yet!
        # maybe first use memory logger and later switch to file logger
        # 'logfile': {
        #     'level':'DEBUG',
        #     'class':'logging.handlers.RotatingFileHandler',
        #     'filename': pf.cfg['logfile'],
        #     'maxBytes': 1024*1024*5, # 5 MB
        #     'backupCount': 100,
        #     'formatter':'standard',
        # },
    },
    'loggers': {
        'pyformex': {
            'level': 'INFO',
            'handlers': ['memory'],
        }
    },
}

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('pyformex')
logger.info(f"{fullVersion()} start on Python{human_version(sys.hexversion)}")

########## special global flags ##############

# Are we running doctests?
doctest = False
# Are we importing from Sphinx doc generator?
sphinx = 'sphinx' in sys.modules

########## acceleration libraries ##############

libraries = ['misc_c', 'nurbs_c', 'clust_c']

########## Special adjustements for source versions ############

if installtype == 'G':
    # We are running from a source tree (Git)
    import importlib.machinery

    def run_cmd(cmd):
        """Run command"""
        import subprocess
        #print(f"COMMAND: {cmd}")
        P = subprocess.Popen(
            str(cmd), stdout=subprocess.PIPE, shell=True, universal_newlines=True
        )
        out, err = P.communicate()
        if P.returncode:
            print(out)
            print(err)
        return P.returncode, out, err

    # Clean the source tree
    source_clean = pyformexdir / 'source_clean'
    if source_clean.exists():
        try:
            suffix = importlib.machinery.EXTENSION_SUFFIXES[0]
            cmd = f"{source_clean} --keep_modules '*{suffix}'"
            run_cmd(cmd)
        except Exception as e:
            print(str(e))
            print(f"Error while executing {source_clean}\n"
                  "Ignore error and continue")

    # Running from source tree: make sure the compiled libraries are up-to-date
    libdir = pyformexdir / 'lib'

    def checkLibraries():
        # find extension used by compiled library (.so)
        import sysconfig
        ext = sysconfig.get_config_var('EXT_SUFFIX')
        if ext is None:
            ext = '.so'
        msg = ''
        for lib in libraries:
            if lib.startswith('_'):
                src = libdir / lib + '.pyx'
            else:
                src = libdir / lib + '.c'
            obj = libdir / lib + ext
            if not obj.exists() or obj.mtime < src.mtime:
                msg += f"\nThe compiled library '{lib}' is not up to date!"
        return msg

    msg = checkLibraries()
    if msg and not sphinx:
        print(msg)
        print("Rebuilding pyFormex libraries, please wait")
        cmd = f"cd {pyformexdir.parent}; PYTHON={sys.executable} make lib"
        run_cmd(cmd)
        msg = checkLibraries()

    if msg:
        # No success
        msg += f"""

I had a problem rebuilding the libraries in {libdir}.
You should probably exit pyFormex, fix the problem and then restart pyFormex.
"""
    if msg:
        startup_warnings.append(msg)

    # Set the proper revision number when running from git sources

    def set_revision():
        global __revision__
        cmd = f"cd {pyformexdir} && git describe --always"
        sta, out, err = run_cmd(cmd)
        if sta == 0:
            __revision__ = out.split('\n')[0].strip()
        else:
            print("Could not set revision")

    def set_branch():
        global __branch__
        cmd = f"cd {pyformexdir} && git rev-parse --abbrev-ref HEAD"
        sta, out, err = run_cmd(cmd)
        if sta == 0:
            __branch__ = out.split('\n')[0]
        else:
            print("Could not set branch name")

    set_revision()
    set_branch()

logger.info(f"This is {fullVersion()}")
logger.info(f"Installation type {installtype} at {pyformexdir}")

################ Special import mechanisms ##############

def import_lazy(name):
    import importlib.util
    spec = importlib.util.find_spec(name)
    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module

def import_direct(file):
    import importlib.util
    import tokenize
    file_path = tokenize.__file__
    module_name = tokenize.__name__
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

################ pyFormex global variables and functions ###############

# The GUI parts
app_started = False
interactive = False
app = None  # the QApplication
GUI = None  # the GUI QMainWindow
canvas = None  # the OpenGL Drawing widget controlled by the running script
console = None  # alternate Python console

# initialize some global variables used for communication between modules

# the options found on the command line
# this is replaced with the options read from the command line
# but we define it here with an attribute debuglevel, so that we can
# use debug (unintentionally) before the debuglevel is set


class options:
    debuglevel = {}  # Make sure we can use  VAR in pf.options.debuglevel
    verbose = 1     # Make sure we can use
    uselib = False  # initial default to keep sphinx happy


# Important pyFormex globals
PF = {}  # explicitely exported globals
GS = None  # only set in gui mode

scriptName = None
scriptlock = set()
scriptMode = None

# define default of warning and error

def print_err(*args, **kargs):
    """Print to stderr"""
    file = kargs.pop('file', sys.stderr)
    print(*args, **kargs, file=file)

warning = print_err
error = print_err


def _busy(state=True):
    """Flag a busy state to the user"""
    if state:
        print("This may take some time...")


def busy(state=True):
    """Flag a busy state to the user"""
    if GUI:
        GUI.setBusy(state)
    else:
        _busy(state)


on_exit = []  # functions to run on exit

def onExit(func):
    """Register a function to be called on exit from pyFormex"""
    if callable(func):
        on_exit.append(func)
    else:
        raise ValueError("Expected a callable")


######################################################################
###  DEBUG items
################################

from enum import Flag  # noqa: E402

class DEBUG(Flag):
    """A class with debug items.

    This class holds the defined debug items as attributes.
    Each debug topic is a binary value with a single bit set (a power of 2).
    Debug items can be combined with & (AND), | (OR) and ^ (XOR).
    Two extra values are defined: NONE switches off all debugging, ALL
    activates all debug items.
    """
    NONE = 0
    (INFO, WARNING, CONFIG, DETECT, HELP, MEM, SCRIPT, GUI, MENU, DRAW,
     CANVAS, OPENGL, LIB, MOUSE, APPS, IMAGE, PICK, MISC, ABQ, WIDGET, PROJECT,
     WEBGL, MULTI, LEGACY, PLUGIN, UNICODE, FONT, PGF, VTK, DOCTEST,
     ) = [2**i for i in range(30)]
    ALL = -1

    @classmethod
    def item(cls, name):
        """Convert a string to a DEBUG item

        The string is case insensitive.

        Raises
        ------
        ValueError
            If the name is not a DEBUG item.
        """
        try:
            return cls[name.upper()]
        except KeyError:
            raise ValueError(f"No such {cls.__name__} item: {name}")

    @classmethod
    def level(cls, names):
        """Return the combined debug level for a list of debug items

        Raises
        ------
        ValueError
            If any of the names is not a DEBUG item.
        """
        from operator import or_
        from functools import reduce
        return reduce(or_, [cls.item(name) for name in names])


def debugon(topic):
    """Return True if the specified debug topic is on"""
    return topic in options.debuglevel


def debug(s, level=DEBUG.ALL):
    """Print a debug message

    Parameters
    ----------
    s: str
        The message to be printed
    level: DEBUG
        The DEBUG level in which to print this message. Messages of a certain
        level are only printed if the global variable pf.options.debuglevel
        has the specified DEBUG flag set.
    """
    if level in options.debuglevel:
        print(f"{level}: {s}")


def debugt(s, level):
    """Print a debug message with timer"""
    import time
    debug(f"{time.time()}: {s}")


def verbosity(verbose):
    """Check that verbosity is equal or higher than given value"""
    return options.verbose >= verbose


def verbose(verbose, *args, **kargs):
    """Print a message if the verbosity is high enough"""
    if options.verbose >= verbose:
        print(*args, **kargs)


def run(args):
    """Run pyFormex from a Python shell

    Parameters
    ----------
    args: str
        The arguments for pyformex like thy would be entered on the pyformex
        command line in a shell.
    """
    import shlex
    from pyformex import main
    # We do not return a value here: it is only used when pyformex is
    # imported in a Python shell
    main.run(shlex.split(args))


####################################################################
###  Load factory configuration
###############################
from pyformex.config import Config  # noqa: E402
# Create a config instance
cfg = Config()
cfg['pyformexdir'] = pyformexdir
# load the factory defaults
defaults = cfg['pyformexdir'] / 'pyformexrc'
cfg.load(defaults)
# The default user config path (do not change!)
cfg['userprefs'] = cfg['userconfdir'] / 'pyformex.conf'

# Set the current session configurations in pyformex module
prefcfg = None  # the preferenced configuration
refcfg = None  # the reference configuration
preffile = None  # the file where the preferenced configuration will be saved

# End
