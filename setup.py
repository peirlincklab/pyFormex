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
#
"""Setup script for pyFormex

To change the install location, see the prefix and exec-prefix in setup.cfg.
To uninstall pyFormex: pyformex --remove
"""
import os
import sys
import numpy as np
from setuptools import setup, Extension

# pyFormex release
RELEASE = '3.4.dev0'


def major(v):
    """Return the major component of version"""
    return v >> 24

def minor(v):
    """Return the minor component of version"""
    return (v & 0x00FF0000) >> 16

def human_version(v):
    """Return the human readable string for version"""
    return f"{major(v)}.{minor(v)}"

# Required Python version
REQVERSION = 0x03080000
if sys.hexversion < REQVERSION:
    ver = human_version(sys.hexversion)
    reqver = human_version(REQVERSION)
    raise RuntimeError(f"Your Python version is {ver} "
                       f"but pyFormex requires >= {reqver}")


import setuptools.command.install_lib
_install_lib = setuptools.command.install_lib.install_lib
class install_lib(_install_lib):
    def finalize_options(self):
        print(f"INSTALL_DIR = {self.install_dir}")
        _install_lib.finalize_options(self)
        self.install_dir = os.path.join(self.install_dir,'pyformex-' + RELEASE)
        print(f"INSTALL_DIR = {self.install_dir}")


# define the things to include
import manifest

def print_msgs(msgs):
    """Print status messages"""
    print('*' * 75)
    for msg in msgs:
        print(msg)
    print('*' * 75)


def run_setup(options):

    # The acceleration libraries
    LIB_MODULES = ['misc_c', 'nurbs_c', 'clust_c']

    ext_modules = [Extension(f"pyformex.lib.{m}",
                             [f"pyformex/lib/{m}.c"],
                             include_dirs=[np.get_include()],
                             )
                   for m in LIB_MODULES
                   ]

    kargs = {}
    if options['accel']:
        kargs['ext_modules'] = ext_modules

    #print(kargs)

    with open('Description') as file:
        long_description = file.read()

    # PKG_DATA, relative from pyformex path
    PKG_DATA = [
        'pyformexrc',
        'icons/README',
        'icons/*.xpm',
        'icons/*.gif',
        'icons/pyformex*.png',
        'icons/64x64/*',
        'fonts/*',
        'glsl/*',
        'examples/apps.cat',
        'bin/*',
        'data/*',
        'doc/*',
        'sphinx/**',
        'extra/Makefile',
        'extra/*/*',
        'scripts/*',
        ]

    setup(
        cmdclass={'install_lib': install_lib},
        #use_scm_version=True,
        #setup_requires=['setuptools_scm'],
        name='pyformex',
        version=RELEASE,
        description='Python framework to create, transform, manipulate and render 3D geometry',
        long_description=long_description,
        author='Benedict Verhegghe',
        author_email='bverheg@gmail.com',
        url='http://pyformex.org',
        download_url='http://download.savannah.gnu.org/releases/pyformex/pyformex-%s.tar.gz' % RELEASE,
        license='GNU General Public License v3 or later (GPLv3+)',
        packages=[
            'pyformex',
            'pyformex.gui',
            'pyformex.gui.menus',
            'pyformex.lib',
            'pyformex.opengl',
            'pyformex.plugins',
            'pyformex.appsdir',
            #  'pyformex.scripts',  # this is not a package!
            'pyformex.examples',
            'pyformex.fe',
            'pyformex.freetype',
            'pyformex.freetype.ft_enums',
        ],
        include_package_data=True,
        #package_data={ 'pyformex': PKG_DATA },
        # scripts=['pyformex/pyformex'],
        # entry_points = {
        #     'console_scripts': [
        #         f'pyformex-{RELEASE}=pyformex.main:run'
        #     ],
        # },
        #data_files=manifest.OTHER_DATA,
        classifiers=[
            'Development Status :: 4 - Beta',
            'Development Status :: 5 - Production/Stable',
            'Environment :: Console',
            'Environment :: X11 Applications :: Qt',
            'Intended Audience :: End Users/Desktop',
            'Intended Audience :: Science/Research',
            'Intended Audience :: Education',
            'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
            'Operating System :: POSIX :: Linux',
            'Operating System :: POSIX',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: C',
            'Topic :: Multimedia :: Graphics :: 3D Modeling',
            'Topic :: Multimedia :: Graphics :: 3D Rendering',
            'Topic :: Scientific/Engineering :: Mathematics',
            'Topic :: Scientific/Engineering :: Visualization',
            'Topic :: Scientific/Engineering :: Physics',
        ],
        python_requires=">=3.8",
        install_requires=[
            'numpy',
            'scipy',
            'pyside2',
            'pyopengl',
            'pillow',
            'docutils',
        ],
        **kargs
    )


run_setup(options={'accel': True})

# End
