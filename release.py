#!/usr/bin/env python3

"""Manipulate the RELEASE file

This script can be used to change the VERSION or RELEASE number
in the RELEASE file, and to print the RELEASE file

VERSION is an official release number of the form x.y (or x.y.z for
bugfix releases). RELEASE is the complete version string starting with
VERSION and always having a tail during development. Only
at the moment of creating a release is the tail removed.

Some available commands (to be executed from the parent dir::

    python3 release.py bumprelease store   # increase the tail version component
    python3 release.py setversion store    # set the VERSION/RELEASE for release
    python3 release.py bumpversion bumprelease store
                                    # increase the VERSION/RELEASE after release
    python3 release.py print        # show the current version
    python3 release.py test [-v]    # run the doctests of this script

Use print instead of store to do a dry run.

The first commands are usually executed from the GNUMakefile
using on of the commands::

    make bumprelease
    make bumpversion

"""

import sys
import re
from pathlib import Path

commands = ['bumprelease', 'bumpversion', 'setversion', 'store',
            'print', 'test']


def bumpversion(version,default=None):
    """Bump the end digits part in version

    Increases the ending digits of the version string.

    version: a string supposedly ending in digits
    default: a tail to add to version if it does not end in digits

    Examples
    --------
    >>> bumpversion('1.0.6','')
    '1.0.7'
    >>> bumpversion('1.0.','')
    '1.0.0'
    >>> bumpversion('X.Y.dev3')
    'X.Y.dev4'
    >>> bumpversion('X.Y','.dev')
    'X.Y.dev0'
    """
    m = re.match(r'^(.*)(\d+)$',version)
    if m:
        ver = int(m.group(2)) + 1
        return f"{m.group(1)}{ver}"
    else:
        return f"{version}{default}0"

txt = None

def main(cmd):
    """The main command processor

    Each argument is a cmd that is executed here.
    """
    global txt
    if cmd == 'test':
        import doctest
        doctest.testmod()
        sys.exit(1)

    P = Path(__file__).parent / 'RELEASE'
    if cmd == "store":
        if txt is not None:
            P.write_text(txt)
        return
    elif txt is None:
        txt = P.read_text()

    if cmd == 'print':
        print(txt)
        return

    # Commands operating on txt
    txt = txt.split('\n')
    if cmd == 'bumprelease':
        key = 'RELEASE'
        default = '.dev'
    elif cmd == 'setversion':
        key = 'RELEASE'
    elif cmd == 'bumpversion':
        key = 'VERSION'
        default = ''

    for i, line in enumerate(txt):
        m = re.match(r'^([A-Z]+)=(\S*)$',line)
        if m:
            #print(f"match in line {i}: {line}")
            if m.group(1) == key:
                #print(f"change line {i}: {line}")
                if cmd == 'setversion':
                    version = '${VERSION}'
                else:
                    version = bumpversion(m.group(2),default)
                #print(f"new version is {version}")
                txt[i] = f"{key}={version}"

    txt = '\n'.join(txt)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg in commands:
                main(arg)
            else:
                print(f"invalid argument: {arg}")
                sys.exit(1)
    else:
        print("No argument specified. Need one of:")
        print(commands)
        sys.exit(1)

# End
