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

# This is the only pyFormex module that is imported by the main script,
# so this is the place to put startup code

"""pyFormex command line options

This module defines the pyFormex command line options.
It is placed in a separate module so that it has very limited dependencies
and can be loaded very early in the startup procedure.
This allows options to be used to influence the further startup process
and the modules that are imported.
"""

import argparse

import pyformex as pf

###########################################################################
## parsing command line options
###############################

def createParser():
    """Create a parser for the pyFormex command line.

    Returns
    -------
    :class:`argparse.ArgumentParser`
        A parser for the pyFormex command line.
    """
    description = pf.Description + " More info on http://pyformex.org"
    epilog = """
All pyFormex options are available as long options.
pyFormex options and arguments may be preceded with (short) options for the
Python interpreter. --, -h or -c force the start of pyFormex options.
Example: pyformex -v -- -v0 will pass -v to Python and -v0 to pyFormex.
"""
    parser = argparse.ArgumentParser(
        prog=pf.__prog__,
        # usage = "%(prog)s [<options>] [ [ scriptname [scriptargs] ] ...]",
        description=description,
        epilog=epilog,
        # formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=False,  # Because we do not want to exit here on help!
    )

    def MO(*args, show_default=" (default: %(default)s)", **kargs):
        """Add_argument with automatic showing of default in the help.

        Showing the default can be suppressed by adding show_default=''
        """
        if show_default and 'help' in kargs and 'default' in kargs:
            kargs['help'] += show_default
        parser.add_argument(*args, **kargs)

    MO(
        "--verbose", '-v',
        action='store',
        type=int,
        default=2,
        help="Set the verbosity level (0..5).",
    )
    MO(
        "--gui",
        action="store_true",
        default=None,
        help="Start the GUI. This is the default when no FILE "
        "argument is given.",
        show_default=False,
    )
    MO(
        "--nogui",
        action="store_false",
        dest="gui",
        help="Do not start the GUI. This is the default when a FILE "
        "argument is given.",
        show_default=False,
    )
    MO(
        "--script", '-c',
        action="store",
        default=None,
        metavar='SCRIPT',
        help="A pyFormex script to be executed at startup. It is executed "
        "before any specified script files. This is mostly used in --nogui "
        "mode, when the script to be executed is very short.",
    )
    MO(
        "--interactive",
        action="store_true",
        dest="interactive",
        default=False,
        help="Go into interactive mode after processing the command line "
        "parameters. This is implied by the --gui option and defaults to "
        "False with the --nogui option.",
    )
    MO(
        "--uselib",
        action="store_true",
        default=None,
        help="Use the pyFormex C lib if available. This is the default.",
        show_default=False,
    )
    MO(
        "--nouselib",
        action="store_false",
        dest="uselib",
        default=None,
        help="Do not use the pyFormex C-lib.",
        show_default=False,
    )
    MO(
        "--config",
        action="store",
        default=None,
        help="Use file CONFIG for settings. This file is loaded in addition "
        "to the normal configuration files and overwrites their settings. "
        "Any changes will be saved to this file.",
    )
    MO(
        "--nodefaultconfig",
        action="store_true",
        default=False,
        help="Skip the default site and user config files. This option can "
        "only be used in conjunction with the --config option.",
    )
    MO(
        "--geometry",
        action="store",
        default=None,
        help="Set the main window geometry, overriding the user settings. "
        "The value should be in X11 window geometry style: WxH+X+Y.",
    )
    MO(
        "--redirect",
        action="store",
        default='oe',
        help="Override the 'gui/redirect' configuration setting."
        " Value should be one of 'oe', 'o', 'e' or ''.",
        show_default=False,
    )
    MO(
        "--noredirect",
        action="store_const", const='',
        dest="redirect",
        help="Do not redirect standard and error output to the embedded Python"
        " console.",
        show_default=False,
    )
    MO(
        "--debug",
        action="store",
        default=None,
        help="Display debugging information to sys.stdout. The value is "
        "a comma-separated list of (case-insensitive) debug items. "
        "Do 'pyformex --debugitems' to get a list of available items. "
        "The special value 'all' can be used to switch on all debug info.",
    )
    MO(
        "--debuglevel",
        action="store",
        type=int,
        default=0,
        help="Display debugging info to sys.stdout. "
        "The value is an int with the bits of the requested debug levels set. "
        "A value of -1 switches on all debug info. "
        "If this option is used, it overrides the --debug option.",
    )
    MO(
        "--debugitems",
        action="store_true",
        default=False,
        help="Show all available debug items and exit",
        show_default=False,
    )
    MO(
        "--mesa",
        action="store_true",
        default=False,
        help="Force the use of software 3D rendering through the mesa libs. "
        "The default is to use hardware accelerated rendering whenever "
        "possible. This flag can be useful when running pyFormex remotely "
        "on another host. The hardware accelerated version will not work "
        "over remote X.",
    )
    MO(
        "--dri",
        action="store_true",
        default=None,
        help="Use Direct Rendering Infrastructure. "
        "By default, direct rendering will be used if available.",
        show_default=False,
    )
    MO(
        "--nodri",
        action="store_false",
        dest="dri",
        default=None,
        help="Do not use the Direct Rendering Infrastructure. "
        "This may be used to turn off the direc rendering, e.g. to allow "
        "better capturing of images and movies.",
        show_default=False,
    )
    MO(
        "--gl3",
        action="store_true",
        default=False,
        help="Use the new development gl3 engine. "
        "Note: this is for developers only. Most drawing functions will not "
        "work if you use this.",
    )
    MO(
        "--mgl",
        action="store_true",
        default=False,
        help="Use moderngl instead of PyOpenGL. "
        "Note: this is for developers only. Most drawing functions will not "
        "work if you use this.",
    )
    MO(
        "--opengl",
        action="store",
        default='2.0',
        help="Force the use of a specific OpenGL version. "
        "The version should be specified as a string 'a.b'.",
    )
    MO(
        "--shader",
        action="store",
        default='130',
        help="Force the use of an alternate GPU shader for the OpenGL "
        "rendering. If the default selected shader does not work well "
        "for your hardware, you can use this option to try one of the "
        "alternate shaders. See 'pyformex --detect' for a list of the "
        "available shaders.",
    )
    MO(
        "--nomultisample",
        action="store_false",
        dest="multisample",
        default=True,
        help="Switch off the use of multisample buffers in OpenGL.",
    )
    MO(
        "--fixcbo",
        action="store_true",
        default=False,
        help="Switch a bug on some graphics cards.",
    )
    MO(
        "--bindings",
        action="store",
        default=None,
        help="Override the configuration setting for the Qt5 bindings. "
        "Available bindings are 'pyside2' or 'pyqt5'."
        "A value 'any' may be given to let pyFormex find out which "
        "bindings are available and use one of these.",
    )
    MO(
        "--memtrack",
        action="store_true",
        default=False,
        help="Track memory for leaks. This is only for developers.",
    )
    # MO(
    #     "--fastnurbs",
    #     action="store_true",
    #     default=False,
    #     help="Test C library nurbs drawing: only for developers!",
    # )
    MO(
        "--experimental",
        action="store_true",
        default=False,
        help="Allow the pyformex/experimental modules to be loaded. "
        "Beware: use only if you know what you are doing!",
    )
    MO(
        "--nocanvas",
        action="store_false",
        dest="canvas",
        default=True,
        help="Do not add an OpenGL canvas to the GUI "
        "(use for development purposes only!)",
        show_default=False,
    )
    MO(
        "--listfiles",
        action="store_true",
        default=False,
        help="List the pyFormex Python source files and exit.",
        show_default=False,
    )
    MO(
        "--listmodules",
        action="store",
        default=None,
        metavar='PKG',
        nargs='*',
        help="List the Python modules in the specified pyFormex subpackage "
        "and exit. Specify 'core' to just list the modules in the pyFormex "
        "top level. Specify 'all' to list all modules. The default is to "
        "list the modules in core, lib, plugins, gui, opengl.",
        show_default=False,
    )
    MO(
        "--search",
        action="store_true",
        default=False,
        help="Search the pyformex source for a specified pattern and exit. "
        "This can optionally be followed by -- followed by options for the "
        "grep command and/or '-a' to search all files in the extended search "
        "path. The final argument is the pattern to search. '-e' before the "
        "pattern will interprete this as an extended regular expression. '-l' "
        "option only lists the names of the matching files.",
        show_default=False,
    )
    MO(
        "--remove",
        action="store_true",
        default=False,
        help="Remove the pyFormex installation and exit. This option only "
        "works when pyFormex was installed from a tarball release using the "
        "supplied install procedure. If you install from a distribution "
        "package (e.g. Debian), you should use your distribution's package "
        "tools to remove pyFormex. If you run pyFormex directly from the git "
        "source, you should just remove the whole cloned source tree.",
        show_default=False,
    )
    MO(
        "--whereami",
        action="store_true",
        default=False,
        help="Show where the pyformex package is installed and exit.",
        show_default=False,
    )
    MO(
        "--detect",
        action="store_true",
        default=False,
        help="Show detected helper software and exit.",
        show_default=False,
    )
    MO(
        "--doctest",
        action="store",
        default=None,
        metavar='MODULE',
        nargs='*',
        help="Run the docstring tests for the specified pyFormex modules "
        "and exit. MODULE name is specified in Python syntax, relative "
        "to the pyformex package (e.g. coords, curve).",
        show_default=False,
    )
    MO(
        "--pytest",
        action="store",
        default=None,
        metavar='MODULE',
        nargs='*',
        help="Run the pytest tests for the specified pyFormex modules "
        "and exit. MODULE name is specified in Python syntax, relative "
        "to the pyformex package (e.g. coords, curve).",
        show_default=False,
    )
    MO(
        "--docmodule",
        action="store",
        default=None,
        metavar='MODULE',
        nargs='*',
        help="Print the autogenerated documentation for module MODULE "
        "and exit. This is mostly useful during the generation of the "
        "pyFormex reference manual, as the produced result still needs "
        "to be run through the Sphinx documentation generator. MODULE "
        "is the name of a pyFormex module (Python syntax).",
        show_default=False,
    )
    MO(
        "--runall",
        action="store",
        type=int,
        metavar='COUNT',
        help="Automatically run some random examples at startup. Specify "
        "the number of examples, or -1 for all examples (may take a while).",
    )
    MO(
        "--version",
        action='store_true',
        default=False,
        help="Show program's version number and exit",
        show_default=False,
    )
    MO(
        "--usage",
        action='store_true',
        default=False,
        help="Show pyformex command line usage and exit",
        show_default=False,
    )
    MO(
        "--help", '-h',
        action="store_true",
        default=False,
        help="Show this help message and exit",
        show_default=False,
    )
    MO(
        "args",
        action="store",
        nargs='*',
        metavar='FILE/APP [ARGS ... [++]]',
        help="pyFormex script file or app to be executed on startup. "
        "If it is a filename, it should have a .py suffix and the contents "
        "will be executed in script mode. Else, it is an app in Python "
        "pkg.module notation, and it should be located under one of the "
        "application paths specified in the 'appsdirs' configuration "
        "variable. In both cases the arguments following FILE/APP will be "
        "available to the script/app in a global variable ``_argv_``. "
        "A '++' in the ARGS list ends the argument list for the script/app, "
        "and the next argument will again be interpreted as a FILE/APP. "
        "FILE/APP arguments are mostly used in --nogui mode but also work "
        "in GUI mode.",
    )

    return parser


def parseOptions(args):
    """Parse command line arguments

    The arguments of the pyFormex command line can be splitted in
    options and remaining arguments. This function will split the
    options from the other arguments and store them in the variable
    pf.options for access throughout pyFormex. The remaining arguments
    are stored in pf.options.args

    Parameters
    ----------
    args: list of str
        A list of command line arguments for the pyformex command

    Returns
    -------
    bool
        True if the parsing was successful.
    """
    pf.logger.info("Parse the command line options")
    pf.parser = createParser()

    # Parse the arguments: set options; options.args contains remaining arguments
    pf.options = pf.parser.parse_args(args)

    # Set debug level
    if pf.options.verbose >= 5:
        pf.options.debuglevel = pf.DEBUG.ALL
    if pf.options.debug and not pf.options.debuglevel:
        pf.options.debuglevel = pf.DEBUG.level(pf.options.debug.split(','))
    else:
        pf.options.debuglevel = pf.DEBUG(pf.options.debuglevel)

    # Check for invalid options
    if pf.options.nodefaultconfig and not pf.options.config:
        print("\nInvalid options: --nodefaultconfig but no --config option\n"
              "Do pyformex --help for help on options.\n")
        return False

    pf.debug("Done parsing options")
    pf.debug(f"Options:{pf.options}", pf.DEBUG.ALL)
    return True


# End
