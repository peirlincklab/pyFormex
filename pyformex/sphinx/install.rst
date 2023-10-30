..

..
  SPDX-FileCopyrightText: © 2007-2023 Benedict Verhegghe <bverheg@gmail.com>
  SPDX-License-Identifier: GPL-3.0-or-later

  This file is part of pyFormex 3.3  (Sun Mar 26 20:16:15 CEST 2023)
  pyFormex is a tool for generating, manipulating and transforming 3D
  geometrical models by sequences of mathematical operations.
  Home page: https://pyformex.org
  Project page: https://savannah.nongnu.org/projects/pyformex/
  Development: https://gitlab.com/bverheg/pyformex
  Distributed under the GNU General Public License version 3 or later.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see http://www.gnu.org/licenses/.


.. include:: defines.inc
.. include:: links.inc


.. _cha:install:

*******************
Installing pyFormex
*******************

.. topic:: Abstract

   This document explains the different ways for obtaining a running
   pyFormex installation. You will learn how to obtain pyFormex, how
   to install it, and how to get it running.

.. warning:: This document is under construction


.. _sec:choose_installation:

Installing pyFormex-2.0
=======================

This installation manual is for the pyFormex 2.0 series. For older
versions see `Installing pyFormex-1.0`_ or `Installing pyFormex-0.9`_.

pyFormex is being developed on GNU/Linux systems and currently only runs on
Linux. On other systems your best option is to run Linux in a virtual machine
or boot your machine from a USB stick with a Linux Live system.

pyFormex is software under continuous development, and many users run
it directly from the latest development sources. This holds a certain
risk however, because the development version may at times become
unstable or incompatible with previous versions and thus break your
applications.  At regular times we therefore create official releases,
which provide a more stable and better documented and supported
version, together with an easy install procedure.

If you can meet the requirements for using an officially packed
release, and you can not use the :ref:`sec:debian-packages`, this is
the recommended way to install pyFormex. All the software packages
needed to compile and run pyFormex can be obtained for free.

To install an official pyFormex release, you need a working GNU/Linux
system, root privileges to the system (whether through `su` or `sudo`,
and you need to make sure that the :ref:`sec:dependencies` listed
below are installed first on the system.
Then preceed to :ref:`sec:official-release`.

If you need to install a new GNU/Linux system from scratch, and have
the choice to pick any distribution, we highly recommend `Debian
GNU/Linux`_ or derivatives.  This is because most of the pyFormex
development is done on Debian systems, and below you'll find precise
instructions to `install dependencies on Debian`_.  Also, the Debian software
repositories are amongst the most comprehensive to be found on the
Internet. Furthermore, we often provide :ref:`sec:debian-packages`
as well, making installation really a no-brainer.

Most popular GNU/Linux distributions provide appropriately packed
recent versions of the dependencies, so that you can install them
easily from the pacakge manager of your system. In case a package or
version is not available for your system, you can always install it
from source. We provide the websites where you can find the source
packages.

.. _`sec:dependencies`:

Dependencies
============

Whether you install an official release package of pyFormex, or you run
pyFormex from the development source tree, you need to have the following
installed (and working) on your computer:

`Python`_
  Version 3.6 or higher, 3.7 is recommended. Nearly all
  GNU/Linux distributions come with Python installed. Some may however
  still have Python2.x installed as the default Python. Python2.x is
  however no longer supported by pyFormex, so you may have to install
  the Python3 version. Usually, the Python 3.x executable is named 'python3',
  and pyFormex expects it that way. To check your version, do::

    python3 --version

`NumPy`_
  Version 1.10 or higher, 1.12 recommended. NumPy is the package used for
  efficient numerical array operations in Python and is essential for pyFormex.

`PIL`_
  The Python Imaging Library from the pillow fork, used for loading and
  saving images in lots of formats.

`Qt5`_ or `Qt4`_
  Qt is the widget toolkit on which the pyFormex Graphical User
  Interface (GUI) is built. We recommended Qt5, but the older Qt4 version
  should also still work.

`PySide2`_ or `PyQt5`_
  These are Python bindings for the Qt5 libraries. We recommend Pyside2,
  though it should not be too difficult to make PyQt5 work as well.
  If you opted for the older Qt4 libraries instead, you should use one of
  `PySide`_ (recommended) or `PyQt4`_. In any case, make sure you have the
  bindings for Python3.

`PyOpenGL`_
   Python bindings for OpenGL, used for drawing and manipulating the
   3D-structures.
admesh
   Used to check and fix STL files. We need the binary, not the Python library.
libgts-0.7-5
   A library for operating on triangulated surfaces.

To compile the acceleration library (highly recommended!), you will also
need the appropriate Python and OpenGL header files, GNU make and the GNU
compiler gcc:

- make
- gcc
- python3-dev
- libglu1-mesa-dev

Furthermore, we recommend to install the following for extended functionality:

- python3-gnuplot or python3-matplotlib
- python3-pydicom
- python3-docutils
- python3-scipy
- units
- imagemagick
- tetgen
- libdxflib3

Finally, while pyFormex has interfaces to use some of the functionality of
vtk and vmtk, we can not really advise you to install 'python3-vtk7' or 'vmtk',
unless you really need these packages. The reason is that their list of
dependencies is too long. On my Debian Buster 'python3-vtk7' pulls 76 other
packages, and that is with the '--no-install-recommends' option. And 'vmtk'
pulls in another 92, many of them the same as the vtk ones, but Python2 versions.

.. _`install dependencies on Debian`:

Installing dependencies on Debian and alikes
............................................

On `Debian GNU/Linux`_ systems (and Debian-derivatives like Ubuntu)
you can install all basic prerequisites and recommended packages and
all their dependencies with the following command::

  (sudo) apt install \
    python3 make gcc git \
    python3-numpy python3-scipy python3-pil python3-opengl \
    python3-pyside2.qtcore python3-pyside2.qtgui python3-pyside2.qtwidgets \
    python3-pyside2.qtopengl \
    python3-matplotlib python3-pydicom python3-docutils python3-sphinx \
    python3-dev libglu1-mesa-dev libfreetype6-dev \
    libgts-dev libgts-bin admesh tetgen units libdxflib-dev \
    python3-pytest


.. _`sec:official-release`:

Install an official pyFormex release
====================================

.. _`downloading`:

Download pyFormex
.................

Official pyFormex releases can be downloaded from `Releases`_.
As of the writing of this manual, the latest release is |latest|.

pyFormex is distributed in the form of a .tar.gz (tarball)
archive. See :ref:`installation-short` for how to proceed further
with the downloaded file.

.. _`installation-short`:

Install pyFormex: the short version
...................................

Once you have downloaded the tarball, unpack it with the command ::

   tar xvzf pyformex-VERSION.tar.gz

where you replace ``VERSION`` with the correct version from the downloaded file.
Then go to the created pyformex directory ::

   cd pyformex-VERSION

and execute the following commands::

   make build
   sudo make install

This will build pyFormex and install it under ``/usr/local/``. You need root
privileges for the install step only. The executables
are put in ``/usr/local/bin``. If all goes well, you can safely remove the
source tree and build temporaries ::

  cd ..
  rm -rf pyformex-VERSION

and you may start pyFormex with the command::

  pyformex

If not, or if you want more details about the install procedure, or want to
customize the installation procedure, read on in the next section.


.. _sec:installation-long:

Install pyFormex: the long version
..................................

The `make` commands in :ref:`installation-short` do two things. As can
be seen from the ``Makefile``, `make build` actually executes::

   python3 setup.py build
   make -C pyformex/extra build

The first of these commands builds the Python code of pyFormex and
compiles some acceleration libraries. The second command compiles some
external programs that are located under ``pyformex/extra``.

If something goes wrong with the `make build`, or if you need to do some
customized build/install procedures, you can use these commands separately,
or customize the ``Makefile``.

As you expect, the `make install` command executes the same two commands
as above, with `install` in place of `build`.
The installation procedure installs everything into a single
directory (default under a subdirectory of ``/usr/local/lib/Python3.x/``),
and creates an executable ``pyformex`` in ``/usr/local/bin``.
If you have xdg-utils on your system, the installation procedure will also
install a menu and desktop starter for pyFormex.

If installation succeeded, you can use the command ::

   pyformex --whereami

to find out where pyFormex is installed. If the binary install path
``/usr/local/bin`` is not up front in your PATH settings, you may have
to use the full path name:  ``/usr/local/bin/pyformex``.

You can not run the ``pyformex`` command from inside the unpacked
``pyformex-VERSION`` directory. This will force a failure, because
doing so would use the Python source files in that directory instead
of the built and installed ones.

Next you can run ::

   pyformex --detect

to give you a list of installed and detected software that pyFormex is able to
use as helpers. Check that you have pyFormex_installtype (R) and
pyFormex_libraries (``pyformex.lib.misc_``, ``pyformex.lib.nurbs_``). The gts,
gts-bin and gts-extra packages do not have a version, and just display ':'.

If you have troubles with building the externals, you can build each of
the externals separately. In each of the subdirectories of ``pyformex/extra``
you can do `make build` and `sudo make install`. Actually only the
``pyformex/extra/gts/`` is of high importance. Most users can do without the
other ones.


Uninstall pyFormex
..................
When pyFormex is installed by the procedure above, it can be removed by
executing the command ::

   pyformex --remove

and answering 'yes' to the question. You may want to do this before
installing a new version.


..
   Install the extra packages
   --------------------------
   pyFormex makes use of extra software components to enhance its functionality.
   While they are not required for the core operation of pyFormex, many users may
   want to install them. Some of these extras (admesh, units) can easily be
   installed from your regular distribution repositories.
   Some extra components however either are not available in packaged format, or
   the existing packages do not work together well with pyFormex.
   For these components, the pyFormex distribution contains an adhoc install
   procedure to help our users with the installation. The procedures are located
   in dedicated subdirectories of the pyformex-VERSION/pyformex/extra directory
   of the unpacked release tree. Each subdirectory contains a ``README`` file
   with installation instructions. It the directory contains a ``Makefile``, this
   usually boils down to the usual::

     make
     (sudo) make install

   Else, an install script ``install.sh`` is included and installation can be done
   with by executing it from within the subdirectory, with root privileges and with a single parameter 'all'::

     (sudo) ./install.sh all


..
   - gts: Installs some programs to do operations on triangulated surfaces. You need to have the ``libgts`` and its header files installed.
   - dxfparser: Installs the command ``pyformex-dxfparser``, to preprocesses AutoCAD .DXF files for import into pyFormex. You need to have the ``libdxflib`` and its header files installed.
   - postabq: Installs the command ``pyformex-postabq``, to preprocess Abaqus output files (.fil) for import into pyFormex.
   - gl2ps: Image output to in vector formats (PS, EPS, PDF and SVG). Requires
     a Python interface, provided by our install procedure.
   - calpy: Simple finite element simulation framework. Needed for the ``*_calpy``
     examples. Has to be installed from source, because is has to be compiled
     against the same numpy version as pyFormex itself.



.. _sec:debian-packages:

deb packages
============
Currently we have no .deb packages ready for pyFormex 2.0. When they
become available, this documentation will be updated.


.. _sec:source-tree:

Running pyFormex from sources
=============================
If the officially released pyFormex packages are not suitable for your needs,
and you can not find proper packages for your distribution, you can try
running pyFormex directly from the source in the git repository.
Besides the :ref:`sec:dependencies` for the official release, you will also
need to have git installed.

The source code can be downloaded anonymously from the `Git repository`_.
The command ::

  git clone https://git.savannah.nongnu.org/git/pyformex.git MYDIR

will checkout the source to a local directory ``MYDIR``. Provided you
have all the prerequisites installed, pyFormex can then be run
directly from the checked out source with the command::

  MYDIR/pyformex/pyformex

If you want to use the compiled accelerator library however, you will have to
create it first::

  cd MYDIR
  make lib

Once you have a checked-out source tree, you can easily sync it to the latest
repository version by just issuing the following command from your checkout
directory::

  git pull

.. End
