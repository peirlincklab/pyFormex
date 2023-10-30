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
# Makefile for pyFormex reference manual sections
#
# The pyFormex project uses Sphinx for building its documentation.
# This Makefile creates an autodoc Sphinx file from the pyFormex source.
# It works using the py2rst.py script, because the autodoc functions
# of Sphinx are not yet powerful enough.
#

AUTOMODULES= coords formex mesh arraytools script gui.draw colors

COREMODULES= adjacency apps attributes \
    candy cmdtools collection config connectivity coords coordsys curve \
    database elements field fileread filetools filewrite flatkeydb \
    geometry geomfile geomtools globalformat inertia \
    main multi mydict olist options path polygons process project pzffile \
    script simple software \
    timer track trisurface utils varray
# sendmail currently fails

GUIMODULES= $(addprefix gui., \
    appMenu colorscale dialogs drawlock guifunc guimain \
    image menu pyconsole qtcanvas qtgl qtutils signals\
    toolbar viewport views widgets \
    )
OPENGLMODULES= $(addprefix opengl., \
    actors camera canvas canvas_settings decors drawable  \
    matrix objectdialog renderer sanitize scene shader \
    textext texture \
    )
PLUGINMODULES= $(addprefix plugins., \
    bifmesh \
    cameratools ccxdat ccxinp datareader dicomstack dxf \
    fe fe_abq fe_post flavia gts_itf http_server \
    imagearray isopar isosurface lima mesh_io neu_exp nurbs objects \
    partition plot2d polygon polynomial \
    postproc properties section2d sectionize \
    tetgen tools turtle units web webgl \
    )
LIBMODULES= $(addprefix lib., \
    misc_c nurbs_c clust_c misc_e nurbs_e clust \
    )

AUTOREF= $(AUTOMODULES) $(COREMODULES) $(GUIMODULES) $(OPENGLMODULES) $(PLUGINMODULES) $(LIBMODULES)
AUTOSRC= $(addsuffix .rst, ${AUTOREF})

# MANUALREF = lib.misc_c lib.nurbs_c
# MANUALSRC = $(addsuffix .rst, ${MANUALREF})

.PHONY: ref

.SILENT:

# pyFormex root directory
PYFORMEXDIR= ../..

# the pyFormex executable
PYFORMEX= ${PYFORMEXDIR}/pyformex


all: ${AUTOSRC}

clean:
	rm -f ${AUTOSRC}

%.rst: ${PYFORMEXDIR}/%.py
	@echo "====== $* ======="
	${PYFORMEX} --docmodule $*

gui.%.rst: ${PYFORMEXDIR}/gui/%.py
	@echo "====== gui.$* ======="
	${PYFORMEX} --docmodule gui.$*

opengl.%.rst: ${PYFORMEXDIR}/opengl/%.py
	@echo "====== opengl.$* ======="
	${PYFORMEX} --docmodule opengl.$*

plugins.%.rst: ${PYFORMEXDIR}/plugins/%.py
	@echo "====== plugins.$* ======="
	${PYFORMEX} --docmodule plugins.$*

lib.%.rst: ${PYFORMEXDIR}/lib/%.py
	@echo "====== lib.$* ======="
	${PYFORMEX} --docmodule lib.$*

lib.%.rst: ${PYFORMEXDIR}/lib/%.c
	@echo "====== lib.$* ======="
	${PYFORMEX} --docmodule lib.$*

# End
