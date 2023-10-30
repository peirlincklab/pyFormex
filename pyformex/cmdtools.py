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

"""pyFormex command line tools

This module contains some command line tools that are run through the
pyformex command, but do not start a full pyFormex program: just execute
some small task and exit.

Furthermore it contains some functions for handling the user preferences.
"""
import os
import warnings

import pyformex as pf
from pyformex import Path
from pyformex import utils
from pyformex import software

# Note: This module and all of the above should NOT import numpy


class UninstallError(pf.FatalError):
    """Raised on invalid remove request"""
    pass


def remove_pyFormex(pyformexdir, executable):
    """Remove the pyFormex installation.

    This will remove a pyFormex installation that was done using
    the 'python setup.py install' command from a source distribution
    in 'tar'gz' format.
    The procedure is interactive and will ask for confirmation.

    Parameters
    ----------
    pyformexdir: Path
        Absolute Path to the pyFormex installation directory.
    executable: Path
        Path to the pyformex executable.

    Notes
    -----
    This implements the `pyformex --remove` functionality.
    """
    if not executable.stem == 'pyformex':
        raise UninstallError("""
The --remove option can only be used from the pyformex command.
Use the command: pyformex --remove.
""")

    if os.getcwd() == pyformexdir.parent:
        raise UninstallError(f"""
pyFormex was loaded from: {pyformexdir}
Your current working directory is: {os.getcwd()}
The --remove option can not be used from inside the pyformex
package directory. Go to another working directory first.
""")

    if pf.installtype == 'D':
        raise UninstallError("""
It looks like this version of pyFormex was installed from a
distribution .deb package. You should use your distribution's
package tools to remove this pyFormex installation.
""")

    if pf.installtype == 'G':
        raise UninstallError(f"""
It looks like you are running pyFormex directly from a source
tree at {pyformexdir}.
I will not remove it. If you have enough privileges, you can
just remove the whole source tree from the file system.
""")

    if not pyformexdir.is_absolute():
        raise UninstallError("""
The pyFormex installation path is not an absolute path.
Probably you are executing this command from inside a pyFormex
source directory. The 'pyformex --remove' command should be
executed from outside the source.
""")

    # If we get here, this is likely an install from tarball release
    # Remove the installation
    installdir = pyformexdir.parent
    pyfver = f"{pf.__prog__}-{pf.__version__}"

    if installdir.name != pyfver:
        print("INSTALLDIR = {installdir}")
        print("VERSION = {pyfver}")
        print("Version doesn't match installdir")
        return

    if pf.installtype == 'U':
        # installed in user space
        homedir = Path.home()
        bindir = homedir / 'bin'
    elif pf.installtype == 'R':
        # installed in root space
        homedir = Path.home()
        bindir = Path('/usr/local/bin')
    else:
        raise pf.ImplementationError("This should not happen")
    otherfiles = []
    script = bindir / pyfver
    if script.exists():
        otherfiles.append(script)
    script1 = bindir / 'pyformex'
    is_default = script1.exists() and script1.resolve() == script.resolve()
    if is_default:
        otherfiles.append(script1)

    print('#'*72)
    print(f"""\
Beware: this procedure will:
- remove the complete pyFormex installation from:
  {installdir}
- remove the pyFormex executable located at {script}\
""")
    if is_default:
        print(f"- remove the default pyFormex executable {script1}")
    print('#'*72)

    print("""\
You should use this only if pyFormex was installed from source with
the command ./install.sh. You need proper permissions to actually
delete the files. After successful removal, you will not be able
to run this pyFormex again, unless you re-install it.\
""")
    if is_default:
        print("""\
If you have another pyFormex version installed (with install.sh),
you can make that the default by running:
pyformex-VERSION --make_default\
""")
    s = input(f"Are you sure you want to remove {pyfver}? yes/NO: ")
    if s == 'yes':
        print(f"Removing pyformex tree: {installdir}")
        installdir.removeTree()

        for f in otherfiles:
            print(f"Removing {f}")
            try:
                Path(f).unlink()
            except Exception:
                print(f"Could not remove {f}")

        print("\nBye, bye! I won't be back until you reinstall me!")
    elif s.startswith('y') or s.startswith('Y'):
        print("You need to type exactly 'yes' to remove me.")
    else:
        print("Thanks for letting me stay this time.")


def list_modules(pkgs=['all']):
    """Return the list of pure Python modules in a pyFormex subpackage.

    Parameters
    ----------
    pkgs: list of str
        A list of pyFormex subpackage names. The subpackage name is a
        subdirectory of the main pyformex package directory.
        Two special package names are recognized:

        - 'core': returns the modules in the top level pyformex package
        - 'all': returns all pyFormex modules

        An empty list is interpreted as ['all'].

    Returns
    -------
    list of str
        A list of all modules in the specified packages.

    Notes
    -----
    This implements the ``pyformex --listmodules`` functionality.

    """
    modules = []
    if pkgs == []:
        pkgs = ['all']
    for subpkg in pkgs:
        modules.extend(utils.moduleList(subpkg))
    return modules


def run_pytest(modules):
    """Run the pytests for the specified pyFormex modules.

    Parameters
    ----------
    modules: list of str
        A list of pyFormex modules in dotted Python notation,
        relative to the pyFormex package. If an empty list is supplied,
        all available pytests will be run.

    Notes
    -----
    Test modules are stored under the path `pf.cfg['testdir']`, with the
    same hierarchy as the pyFormex source modules, and are named
    `test_MODULE.py`, where MODULE is the corresponding source module.

    This implements the `pyformex --pytest` functionality.
    """
    try:
        import pytest
    except Exception:
        print("Can not import pytest")
        pass

    #warnings.filterwarnings("always", category=DeprecationWarning)
    #warnings.filterwarnings("always", category=PendingDeprecationWarning)

    testpath = pf.cfg['testdir']
    #print(f"TESTPATH={testpath}")
    args = ['--maxfail=10', '-W', 'always::DeprecationWarning']
    if not modules:
        pytest.main(args + [testpath])
    else:
        print(f"Running pytests for modules {modules}")
        for m in modules:
            path = Path(*m.split('.'))
            path = testpath / path.with_name(f"test_{path.name}.py")
            if path.exists():
                pytest.main(args + [path])
            else:
                print(f"No such test module: {path}")


def run_doctest(modules):
    """Run the doctests for the specified pyFormex modules.

    Parameters
    ----------
    modules: list of str
        A list of pyFormex modules in dotted Python notation,
        relative to the pyFormex package. If an empty list is supplied,
        all doctests in all pyFormex modules will be run.

    Notes
    -----
    Doctests are tests embedded in the docstrings of the Python source.

    To allow consistent output of floats independent of machine precision,
    numpy's floating point print precision is set to two decimals.

    This implements the `pyformex --doctest` functionality.
    """
    import numpy
    numpy.set_printoptions(precision=4, suppress=True)
    from pyformex import arraytools
    numpy.set_string_function(arraytools.array2str)
    pf.doctest = True
    pf.error = print
    # safe_verbosityset verbosity to 0
    # pf.options.verbose = 0
    # This has to be run from parentdir
    save_dir = Path.cwd()
    run_dir = pf.pyformexdir.parent
    # we need a writable workdir
    if save_dir.is_writable_dir():
        work_dir = save_dir
    else:
        work_dir = Path.home() / '.local' / 'pyformex' / 'workdir'
        Path.mkdir(work_dir, parents=True, exist_ok=True)
    os.chdir(run_dir)
    if not modules:
        modules = ['all']
    todo = []
    for mod in modules:
        if mod in ['all'] or mod.endswith('.'):
            todo.extend(utils.moduleList(mod.replace('.', '')))
        else:
            todo.append(mod)

    # Temporary hack moving 'software' module to the end,
    # as it causes failures for some other modules
    m = 'software'
    if m in todo:
        todo.remove(m)
        todo.append(m)

    # Remove modules that we can not test:
    todo = [m for m in todo if 'vtk' not in m]

    # Remove plugins.mesh_io if we do not have meshio
    if not software.Module.has('meshio'):
        m = 'plugins.mesh_io'
        if m in todo:
            todo.remove(m)


    pf.debug(f"Final list of modules to test: {todo}", pf.DEBUG.DOCTEST)
    # Now perform the tests
    FAILED, failed, attempted = 0, 0, 0
    os.chdir(work_dir)
    for m in todo:
        try:
            result = doctest_module(m)
            failed += result.failed
            attempted += result.attempted
        except Exception as e:
            if pf.verbosity(2):
                raise e
            result = f"FAIL\n  Failed because: {e}"
            FAILED += 1

        print(f"Module {m}: {result}")
    os.chdir(save_dir)

    if len(todo) > 1:
        print('-'*60)
        print(f"Totals: attempted={attempted} tests, failed={failed} tests, "
              f"FAILED={FAILED}/{len(todo)} modules")

def doctest_module(module):
    """Run the doctests in a single module's docstrings.

    All the doctests in the docstrings of the specified module will be run.

    Parameters
    ----------
    module: str
        A pyFormex module in dotted path notation. The leading 'pyformex.'
        can be omitted.
    """
    import doctest
    import importlib
    import numpy

    if not module.startswith('pyformex'):
        module = 'pyformex.' + module
    mod = importlib.import_module(module)
    printoptions = getattr(mod, '_numpy_printoptions_', {})
    pf.options.verbose = 0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        # Always activate when running doctests
        warnings.filterwarnings("default", category=DeprecationWarning)
        warnings.filterwarnings("default", category=PendingDeprecationWarning)

        pf.debug(f"Running doctests on {mod}", pf.DEBUG.DOCTEST)
        with numpy.printoptions(**printoptions):
            return doctest.testmod(
                mod, optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)


def migrateUserConfig():
    """Migrate the user preferences in $HOME/.config

    Conversion of old style has been abandoned.
    Currently this does nothing.
    """
    pass


# End
