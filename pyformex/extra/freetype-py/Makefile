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

PKG_NAME=freetype-py
PKG_VERSION=0.4.1
PKG_FULLNAME=$(PKG_NAME)-$(PKG_VERSION)
PKG_SOURCE=$(PKG_FULLNAME).tar.gz
PKG_URL=http://freetype-py.googlecode.com/files/$(PKG_SOURCE)
PKG_DIR=$(PKG_FULLNAME)

.PHONY: all download unpack build install clean

all: build

download: $(PKG_SOURCE)

$(PKG_SOURCE):
	wget $(PKG_URL)

unpack: $(PKG_DIR)

$(PKG_DIR): $(PKG_SOURCE)
	tar xvzf $<
	patch -p0 < freetype.patch

build: $(PKG_DIR)
	cd $(PKG_DIR); python setup.py build

install: $(PKG_DIR)
	cd $(PKG_DIR); python setup.py install

clean:
	rm -rf $(PKG_SOURCE) $(PKG_DIR)

# End
