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
#  Makefile to install 'instant-meshes'

#####################################################################

PRG:= instant-meshes
SRC:= instant-meshes-linux.zip
STUPID_NAME:= Instant\ Meshes
URL:= https://instant-meshes.s3.eu-central-1.amazonaws.com/$(SRC)
DATADIR:= $(HOME)/bin
BINDIR:= $(DATADIR)

.PHONY: all download unpack install clean check

all: download unpack install

download: $(TMPDIR)/$(SRC)

unpack: $(DATADIR)/$(STUPID_NAME)

install: $(BINDIR)/$(PRG)

check:
	instant-meshes -h

$(TMPDIR)/$(SRC):
	wget -P $(TMPDIR) $(URL)

$(DATADIR)/$(STUPID_NAME): $(TMPDIR)/$(SRC)
	mkdir -p $(DATADIR)
	unzip -o $(TMPDIR)/$(SRC) -d $(DATADIR)

$(BINDIR)/$(PRG): $(DATADIR)/$(STUPID_NAME)
	ln -sfn '$<' $@

clean:
	rm -f $(TMPDIR)/$(SRC)

# End
