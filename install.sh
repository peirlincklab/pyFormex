#!/bin/bash
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

#
# This script installs pyFormex. Run ./install.sh --help for usage.
#

#TODO: implement the desktop target
#  desktop: install a desktop link to start pyFormex from the GUI menu

usage() {
    cat<<EOF

Usage: $(basename $0) OPTIONS TARGET...

Install pyFormex from source (either a git source or a tar.gz release).

Targets:

  build: build the binary version but do not install it
  install: install the previously build binary version
  all: do all (build + install)


Options:

  -n, --dry-run : show what commands would be run, but do not actually
     execute them.

  -s, --single-version : install a single pyFormex version, overwriting
     a previously installed (possibly other) version of pyFormex.
     The default is to install multiple versions with their own executable
     named pyformex-VERSION (see also --default).
     Note that the multi-version method is only available as of
     pyFormex 2.7.

  -d, --make-default : make the installed version the default
     pyformex version. This symlinks the \$BINDIR/pyformex-VERSION
     executable to \$BINDIR/pyformex.
     Ignored when --single-version is specified.

  -p, --prefix=PREFIX : the path prefix to be used for the install.
     All files will be installed in a single directory
     $PREFIX/lib/pyformex/pyformex-VERSION.
     The default prefix is /usr/local if the install.sh script is run by the
     root user, or \$HOME/.local for other users.

  -b, --bindir=BINDIR : the path where to link the executable script.
     This should normally be a directory that is in your PATH variable.
     The default is \$PREFIX/bin for the root user, and \$HOME/bin
     for other users.

  -e, --egg: Use egg as the bdist format. Default is to use a wheel.

  -h, --help : display this help page and exit.

EOF
}

#
# Define constants and default values for variables
#
RELEASE=3.4.dev0
PYFVER=pyformex-$RELEASE
PYTHON=python3
ECHO=
SINGLE=
DEFAULT=
PREFIX="$VIRTUAL_ENV"
SCHEME=
BINDIR=
BDIST=whl
BDISTCMD=bdist_wheel
USER="$(id -un)"

#
# helper functions
#

# Return 'true' if $1 is defined, else false
is_defined() {
    if [ -z "$1" ]; then
	echo false
    else
	echo true
    fi
}

#
# functions defining the actions
#

do_build() {
    $ECHO ${PYTHON} setup.py build
    $ECHO make -C pyformex/extra build
    $ECHO ${PYTHON} setup.py $BDISTCMD
}

do_install() {
    EXECUTABLE=$BINDIR/$PYFVER
    [ -n "$SINGLE" ] && EXECUTABLE=$BINDIR/pyformex
    echo "Installing in $INSTALLDIR and $BINDIR"
    $ECHO install -d $INSTALLDIR $BINDIR
    $ECHO unzip -o dist/$PYFVER*.$BDIST $PYFVER'/*' -d $INSTALLDIR
    $ECHO ln -sfn $INSTALLDIR/$PYFVER/pyformex/pyformex $EXECUTABLE
    [ -n "$DEFAULT" ] && $ECHO ln -sfn $PYFVER $BINDIR/pyformex
    make -C pyformex/extra install prefix=$PREFIX
}

do_clean() {
    $ECHO rm -rf build
}

do_desktop() {
    $ECHO install pyformex/icons/pyformex-64x64.png ${PREFIX}/share/icons/hicolor/64x64/apps/
    $ECHO install pyformex.desktop ${PREFIX}/share/applications/
}

################################
# Process command line arguments
#
# Execute getopt
ARGS=$(getopt -o "nsdep:b:h" -l "dry-run,single-version,make-default,egg,prefix:,bindir:,help" -n "$(basename $0)" -- "$@")

#Bad arguments
[ $? -eq 0 ] || { usage; exit 1; }

eval set -- $ARGS

while [ "$1" != "--" ]; do
    case "$1" in
	-n|--dry-run)
	    ECHO=echo ;;
	-s|--single)
	    SINGLE=1 ;;
	-d|--default)
	    DEFAULT=1 ;;
	-e|--egg)
	    BDIST=egg; BDISTCMD=bdist_egg ;;
	-p|--prefix)
	    PREFIX="$2"; shift ;;
	-b|--bindir)
	    BINDIR="$2"; shift ;;
	-h|--help)
	    usage; exit;;
	*) echo "Unknown option: $1" >&2; exit 1 ;;
   esac
   shift  # delete "$1"
done
shift  # delete the "--"

# Fill in defaults for missing required values
[ -n "$PREFIX" ] || {
    if [ "$USER" = "root" ]; then
	PREFIX=/usr/local
	SCHEME="'posix_prefix'"
    else
	PREFIX=$HOME/.local
	SCHEME="'posix_user'"
    fi
}
[ -n "$BINDIR" ] || BINDIR=$PREFIX/bin

INSTALLDIR=$($PYTHON -c "import sysconfig; print(sysconfig.get_paths($SCHEME)['platlib']);")

cat <<EOF

Installing pyFormex with the following options:

user: $USER
dry-run: $(is_defined $ECHO)
single version: $(is_defined $SINGLE)
make-default: $(is_defined $DEFAULT)
prefix: $PREFIX
bindir: $BINDIR
installdir: $INSTALLDIR
bdist format: $BDIST

EOF

# Check that we have targets
[ -z "$@" ] && {
    echo "** Nothing to be done: use -h for help"
    exit
}

# Execute the commands
for cmd in "$@"; do
    echo "** $cmd"
    case $cmd in
	build | install ) do_$cmd ;;
	all )
	    do_build
	    do_install
	    ;;
	* ) echo "No such command: $cmd"
	    exit 1
	    ;;
    esac
done


# End
