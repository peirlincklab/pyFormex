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
# Makefile for 'gts*' commands used by pyFormex
#
# You need: libgts-dev, libglib2.0-dev, pkg-config
#
############# SET THESE TO SUIT YOUR INSTALLATION ####################

# !! An environment variable DESTDIR can be set to specify a path for
# !! the installation tree. All install paths specified hereafter will
# !! then be relative to that installation path.
# !! An environment variable SU can be set to execute a program with
# !! root privileges. Examples are 'sudo' or 'gksu'.

# root of the installation tree: this is a reasonable default
prefix:= /usr/local
# where to install the executable files
bindir:= $(prefix)/bin
# where to install library files
libdir:= $(prefix)/lib
# where to install the documentation
docdir:= $(prefix)/share/doc
# where to install the manpages
mandir:= $(prefix)/share/man/man1

#####################################################################

PKG:= pyformex-gts

BINDIR:= $(DESTDIR)$(bindir)
LIBDIR:= $(DESTDIR)$(libdir)
DOCDIR:= $(DESTDIR)$(docdir)
MANDIR:= $(DESTDIR)$(mandir)

CC:= gcc $(CPPFLAGS) $(CFLAGS) $(LDFLAGS)
INSTALL:= $(SU) install
INSTALLDIR:= $(INSTALL) -d
INSTALLBIN:= $(INSTALL) -m 0755
INSTALLDATA:= $(INSTALL) -m 0644
RST2MAN:= /usr/share/docutils/scripts/python3/rst2man

SRC= $(wildcard *.c)
PRG= $(addprefix gts, $(SRC:.c=))
MAN= $(addsuffix .1, $(PRG))

# This will detect the flags needed for compilation
FLAGS:= `pkg-config --cflags --libs glib-2.0 gts`

# If pkg-config does not work on your system, you can try these flags
#FLAGS = -pthread -I/usr/include/glib-2.0 -I/usr/lib/x86_64-linux-gnu/glib-2.0/include  -pthread -Wl,--export-dynamic -lgts -lm -lgthread-2.0 -lgmodule-2.0 -lrt -lglib-2.0

# Allow debug build
DEBUG ?= 0
ifeq ($(DEBUG), 1)
    FLAGS:= ${FLAGS} -gdwarf -g3 -DDEBUG
else
    FLAGS:= ${FLAGS} -DNDEBUG
endif

.PHONY: all build install clean

all: install clean

build: $(PRG)

gts%: %.c
	$(CC) $< $(FLAGS) -o $@

install: $(PRG) $(MAN)
	$(INSTALLDIR) $(BINDIR) $(MANDIR)
	$(INSTALLBIN) $(PRG) $(BINDIR)
	$(INSTALLDATA) $(MAN) $(MANDIR)

manpages: $(MAN)

%.1: %.1.rst
	$(RST2MAN) $< > $@

clean:
	rm -f $(PRG) $(MAN)

# End
