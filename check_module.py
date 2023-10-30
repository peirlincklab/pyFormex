#!/usr/bin/env python3

"""check_module.py

Check if a module can be imported in Python3.

Usage: check_module.py [OPTIONS] ARG, ...

Checks for each argument if the name can be imported as a module.
If so, prints the modulen name and package from where the module is loaded.
If not, prints a FAIL message.

OPTIONS
-------
-s : also show the modules from the standard Python library
-f : also show the modules that fail to load
-p : also print the package name

Example: to print a list of all non-pyFormex modules used in pyFormex,
one can use the following command (in the top directory of the source):
  ./create_import_list | xargs ./check_module.py -s
"""

import os, sys
show_std = False
show_fail = False
show_pkg = False


def check_module_import(modname):
    """Print the file from which a named module would be imported"""
    try:
        mod = __import__(modname)
    except:
        if show_fail:
            print(f"{modname}: FAIL")
        return

    pname = mod.__package__
    if pname or show_std:
        if show_pkg:
            if pname:
                print(f"{modname}: from package {pname}")
            else:
                print(f"{modname}: from Python standard library")
        else:
            print(modname)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith('-'):
                for c in arg[1:]:
                    if c == 's':
                        show_std = True
                    elif c == 'f':
                        show_fail = True
                    elif c == 'p':
                        show_pkg = True
                continue
            check_module_import(arg)
    else:
        print(__doc__)

# End
