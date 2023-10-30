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

# Makefile for pyFormex documentation

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         =
BUILDDIR      = ../doc
DOCVERSION = 3.0
PUBDIR = ../../www/doc-${DOCVERSION}

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

RSYNC= rsync -v -e ssh

PDF= pyformex-${DOCVERSION}.pdf
THE_PDF= $(BUILDDIR)/latex/pyformex.pdf

.PHONY: default help clean html README pdf linkcheck prereq ref fixfix pub

# where to search for source files
PYFORMEXDIR=../../pyformex
vpath %.py $(addprefix ${PYFORMEXDIR}, / /gui/ /plugins/)

default: html

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  ref        to recreate the refman source files"
	@echo "  html       to make standalone HTML files"
	@echo "  linkcheck  to check all external links for integrity"

clean:
	make -C ref clean
	-rm -rf $(BUILDDIR)/* pyformex.help

html: prereq
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
	make fixfix
	make README
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."

README: $(BUILDDIR)/html/README

$(BUILDDIR)/html/README:
	@echo "This is the html documentation for pyFormex." > $@
	@echo "All files in this directory are automatically" >> $@
	@echo "created by the documentation building process." >> $@


pdf:
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) $(BUILDDIR)/latex
	@echo "Running LaTeX files through pdflatex..."
	$(MAKE) -C $(BUILDDIR)/latex all-pdf
	@echo "pdflatex finished; the PDF files are in $(BUILDDIR)/latex."

linkcheck:
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) $(BUILDDIR)/linkcheck
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in $(BUILDDIR)/linkcheck/output.txt."

# Automatically created input files

prereq: ref pyformex.help

ref:
	make -s -C ref # We should add logging here

pyformex.help: ${PYFORMEXDIR}/pyformex
	${PYFORMEXDIR}/pyformex --help > $@

# Fix a strange bug in building the docs
fixfix:
	cd $(BUILDDIR)/html; \
	rm -rf _modules/pyformex; \
	sed -i '/pyformex.plugins.webgl/d' _modules/index.html

# Copy the html docs to PUBDIR
pub:
	mkdir -p ${PUBDIR}
	${RSYNC} --delete --exclude CVS --exclude '.buildinfo' ${BUILDDIR}/html/ ${PUBDIR} -av

# End
