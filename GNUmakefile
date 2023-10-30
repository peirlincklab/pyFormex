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
# GNUmakefile
#
# This is the makefile for maintenance tasks of pyFormex.
# This file is not distributed with the releases and is not needed
# for installing pyFormex.
#
SHELL:= /bin/bash
include RELEASE

PKGNAME= pyformex

PYFORMEXDIR= pyformex

LIBDIR= ${PYFORMEXDIR}/lib
DOCDIR= ${PYFORMEXDIR}/doc
BINDIR= ${PYFORMEXDIR}/bin
EXTDIR= ${PYFORMEXDIR}/extra
DATADIR= ${PYFORMEXDIR}/data
SPHINXDIR= pyformex/sphinx

SOURCE= ${PYFORMEXDIR}/pyformex \
	$(wildcard ${PYFORMEXDIR}/*.py) \
	$(wildcard ${PYFORMEXDIR}/gui/*.py) \
	$(wildcard ${PYFORMEXDIR}/gui/menus/*.py) \
	$(wildcard ${PYFORMEXDIR}/opengl/*.py) \
	$(wildcard ${PYFORMEXDIR}/plugins/*.py) \
	$(wildcard ${PYFORMEXDIR}/appsdir/*.py) \
	$(wildcard ${PYFORMEXDIR}/scripts/*.py) \
	$(wildcard ${PYFORMEXDIR}/test/*.py) \
	$(wildcard ${LIBDIR}/*.py) \

LIBSOURCE= ${addprefix ${LIBDIR}/, misc_c.c nurbs_c.c clust_c.c}
LIBOBJECTS= $(CSOURCE:.c=.o)
LIBOBJECTS= $(CSOURCE:.c=.so)

BINSOURCE= \
	$(wildcard ${BINDIR}/*.awk) \

EXTSOURCE= \
	$(wildcard ${EXTDIR}/*/README*) \
	$(wildcard ${EXTDIR}/*/Makefile) \
	$(wildcard ${EXTDIR}/*/*.rst) \
	$(wildcard ${EXTDIR}/*/install.sh) \
	$(wildcard ${EXTDIR}/*/*.h) \
	$(wildcard ${EXTDIR}/*/*.c) \
	$(wildcard ${EXTDIR}/*/*.cc) \
	$(wildcard ${EXTDIR}/*/*.py) \
	${addprefix ${EXTDIR}/pygl2ps/, gl2ps.i setup.py} \

EXAMPLES= \
	$(wildcard ${PYFORMEXDIR}/examples/*.py) \
	$(wildcard ${PYFORMEXDIR}/examples/Demos/*.py) \

EXAMPLEDATA= $(wildcard ${DATADIR}/*.db) $(wildcard ${DATADIR}/*/README)

DOCSOURCE= \
	$(wildcard ${SPHINXDIR}/*.rst) \
	$(wildcard ${SPHINXDIR}/*.py) \
	$(wildcard ${SPHINXDIR}/*.inc) \
	$(wildcard ${SPHINXDIR}/static/scripts/[A-Z]*.py) \
	${SPHINXDIR}/Makefile \
	${SPHINXDIR}/ref/Makefile

EXECUTABLE= ${PYFORMEXDIR}/pyformex ${PYFORMEXDIR}/sendmail.py \
	${BINDIR}/read_abq_inp.awk \
	pyformex-viewer

OTHERSTAMPABLE= README.rst GNUmakefile install.sh ReleaseNotes \
	manifest.py setup.py \
	${PYFORMEXDIR}/pyformexrc \
	${EXAMPLEDATA} \
	$(wildcard ${DOCDIR}/*.rst)

NONSTAMPABLE= LICENSE

STAMPABLE= ${SOURCE} \
	${EXECUTABLE} ${CSOURCE} ${EXAMPLES} ${DOCSOURCE} ${BINSOURCE} \
	${LIBSOURCE} \
	$(filter-out ${EXTDIR}/pygl2ps/gl2ps_wrap.c,${EXTSOURCE}) \
	${OTHERSTAMPABLE}

STATICSTAMPABLE= History HOWTO-dev.rst \
	pyformex-viewer \
	$(wildcard user/*.rst) \
	website/Makefile $(wildcard website/scripts/*.py)

STATICDIRS= pyformex/data/README pyformex/icons/README \
	pyformex/lib/README \
	pyformex/doc/html/README \
	screenshots/README \
	${SPHINXDIR}/images/README ${SPHINXDIR}/static/scripts/README \
	website/README website/images/README

PYTHON ?= python3
STAMP= stamp
VERSIONSTRING= __version__ = ".*"
NEWVERSIONSTRING= __version__ = "${RELEASE}"

PKGVER= ${PKGNAME}-${RELEASE}
PKG= ${PKGVER}.tar.gz
PKGDOC= ${PKGNAME}-doc-${RELEASE}.tar.gz
PKGLST= ${PKGVER}.lst
PKGDIR= dist
PUBDIR= dist
LATEST= ${PKGNAME}-latest.tar.gz
LATESTDEV= ${PKGNAME}-dev.tar.gz
PUBFILES= ${addprefix ${PUBDIR}/, ${PKG} ${PKG}.sig ${LATEST}}

# our local ftp server
FTPLOCAL= bumps:/var/ftp/pub/pyformex
# ftp server on Savannah
FTPPUB= bverheg@dl.sv.nongnu.org:/releases/pyformex/

.PHONY: manifest dist sdist signdist cleandist pub clean distclean html latexpdf pubdoc minutes website dist.stamped showversion version tag register bumprelease bumpversion setversion stampall stampstatic stampstaticdirs pubrelease html lib lib3

##############################

default:
	@echo Please specify a target

# To delete the files we do not use
#   find . -name '*~' -delete
# because that fails on dirs with no access rights
clean:
	pyformex/bin/listtree.py -p . --includefile '.*~' -v1 --ignore-errors --delete
	make -C pyformex/extra clean

distclean: clean
	find . \( -name '*.so' -or -name '*.pyc' \)


# Create the website
website:
	make -C website html

# Create the website from CI/CD script
website-ci:
	mkdir -p public
	make -C website html SPHINXOPTS="-W -E --keep-going"

showversion:
	${PYTHON} release.py print | grep -E '(VERSION=)|(RELEASE=)'

# Bump the release: use AFTER creating .tar.gz
bumprelease:
	${PYTHON} release.py bumprelease print store
	make version

# Bump the version: use BEFORE creating release
setversion:
	${PYTHON} release.py setversion print store
	make version

# Bump the version: use AFTER creating release
bumpversion:
	${PYTHON} release.py bumpversion bumprelease print store
	make version

# Fix version in the source files after changing RELEASE file
version: ${PYFORMEXDIR}/__init__.py \
         ${PYFORMEXDIR}/pyformexrc \
         ${PYFORMEXDIR}/pyformex \
	 install.sh \
	 setup.py \
         ${SPHINXDIR}/conf.py ${SPHINXDIR}/defines.inc ${SPHINXDIR}/Makefile \
         ${LIBSOURCE} \
         ${PYFORMEXDIR}/plugins/fe_abq.py
	make showversion

${PYFORMEXDIR}/__init__.py: RELEASE
	sed -i \
	    -e 's|${VERSIONSTRING}|${NEWVERSIONSTRING}|' \
	    -e "/^Copyright/s|2004-....|2004-$$(date +%Y)|" \
	    -e "/^_minimal_version =/s|=.*|= ${MINVERSION}|" \
	    -e "/^_target_version =/s|=.*|= ${TGTVERSION}|" \
	    -e "/^_numpy_version =/s|=.*|= ${NUMPYVERSION}|" \
	    $@

${PYFORMEXDIR}/pyformexrc: RELEASE
	sed -i '/^webdoc =/s/doc-.*"/doc-${DOCVERSION}"/' $@

${PYFORMEXDIR}/pyformex: RELEASE
	REQVER=$(shell python3 -c "from pyformex import human_version; print(human_version(${MINVERSION}))"); \
	sed -i "/^REQVER=/s|=.*|=$${REQVER}|" $@

install.sh: RELEASE
	sed -i "s|RELEASE=.*|RELEASE=${RELEASE}|" $@

setup.py: RELEASE
	sed -i \
	    -e "/^RELEASE =/s|=.*|= '${RELEASE}'|" \
	    -e "/^REQVERSION =/s|=.*|= ${MINVERSION}|" \
	    $@

${SPHINXDIR}/Makefile: RELEASE
	sed -i "s|^DOCVERSION =.*|DOCVERSION = ${DOCVERSION}|" $@

${SPHINXDIR}/conf.py: RELEASE
	sed -i "s|^version =.*|version = '${VERSION}'|;s|^release =.*|release = '${RELEASE}'|" $@
	sed -i "/^copyright/s|2004-....|2004-$$(date +%Y)|" $@

${SPHINXDIR}/defines.inc: RELEASE
	sed -i "/|latest|/s|:: .*|:: ${VERSION}|;/|year|/s|:: .*|:: $$(date +%Y)|" $@

${LIBDIR}/%: RELEASE
	sed -i 's|${VERSIONSTRING}|${NEWVERSIONSTRING}|' $@

${PYFORMEXDIR}/plugins/fe_abq.py: RELEASE
	sed -i "/.*Abaqus input file created by/s/x .* (/x ${RELEASE} (/" $@

# Stamp files with the version/release date

#Stamp.stamp: SHELL:=/bin/bash   # setting the shell to bash for this one
Stamp.stamp: Stamp.template RELEASE
	LANG=C; DATE="$$(date)"; ${STAMP} -t$< header="This file is part of pyFormex ${VERSION}  ($$DATE)" copyright="2007-$${DATE: -4}" -s$@

#Stamp.static: SHELL:=/bin/bash   # setting the shell to bash for this one
Stamp.static: Stamp.template
	LANG=C; DATE="$$(date)"; ${STAMP} -t$< header='This file is part of pyFormex.' copyright="2007-$${DATE: -4}" -s$@

#Stamp.staticdir: SHELL:=/bin/bash   # setting the shell to bash for this one
Stamp.staticdir: Stamp.template
	LANG=C; DATE="$$(date)"; ${STAMP} -t$< header='The files in this directory are part of pyFormex.' copyright="2007-$${DATE: -4}" -s$@

printstampable:
	@for f in ${STAMPABLE}; do echo $$f; done

printstampstatic:
	@for f in ${STATICSTAMPABLE}; do echo $$f; done

printstampstaticdir:
	@for f in ${STATICDIRS}; do echo $$f; done

stampall: Stamp.stamp
	${STAMP} -v -p -t$< -i ${STAMPABLE}

stampstatic: Stamp.static
	${STAMP} -t$< -i ${STATICSTAMPABLE}

stampstaticdirs: Stamp.staticdir
	touch ${STATICDIRS}
	${STAMP} -t$< -i ${STATICDIRS}


# Properly format all sources
#autopep8:
#	pyformex --listfiles | xargs autopep8 -i


# Create the distribution
cleandist:
	mkdir -p ${PKGDIR}
	rm -f ${PKGDIR}/${PKG}

dist: cleandist html manifest sdist clean

# with distutils, add --no-defaults !!!
sdist:
	@echo "Creating ${PKGDIR}/${PKG}"
	( ${PYTHON} setup.py sdist --dist-dir ${PKGDIR}; \
	ln -sfn ${PKG} ${PKGDIR}/${LATESTDEV} ) \
	| tee makedist.log

manifest: manpages
	./manifest.py manifest
	git status
	git status --porcelain -b -uno
	${PYTHON} manifest_check.py
	( echo 'prune *'; sed s'/^/include /' MANIFEST ) > MANIFEST.in

pkglist: ${PKGDIR}/${PKGLST}

signdist: ${PKGDIR}/${PKG}.sig

latest: ${PKGDIR}/${LATEST}

# For CI pipeline
ci_build: cleandist manpages lib3 html manifest sdist clean
	./manifest.py manifest
	git status
	git status --porcelain -b -uno
	CICD=1; ${PYTHON} manifest_check.py
	( echo 'prune *'; sed s'/^/include /' MANIFEST ) > MANIFEST.in

ci_install: ${PKGDIR}/${PKG}
	ls ${PKGDIR}
	tar xvzf ${PKGDIR}/${PKG} ;\
	cd ${PKGVER} ;\
	./install.sh build ;\
	./install.sh install

ci_test: /usr/local/bin/pyformex
	cd; pwd; mkdir -p _test; cd _test; pwd ; \
	which pyformex; \
	pyformex --version; \
	pyformex --whereami; \
	pyformex --detect; \
	pyformex --doctest

# Note that 'pyformex --pytest' does not work on installed pyformex
# because the test directory is not distributed

# Also, pyformex --runall 2 --noredirect
# does not work, because we do not have a screen available

# Atoms

${PKGDIR}/${LATEST}: ${PKGDIR}/${PKG}
	ln -sfn ${PKG} ${PKGDIR}/${LATEST}

${PKGDIR}/${LATESTDEV}: ${PKGDIR}/${PKG}
	ln -sfn ${PKG} ${PKGDIR}/${LATESTDEV}

${PKGDIR}/${PKG}: RELEASE MANIFEST
	@echo "Creating ${PKGDIR}/${PKG}"
	( ${PYTHON} setup.py sdist --no-defaults --dist-dir ${PKGDIR} ) \
	| tee makedist.log

${PKGDIR}/${PKG}.sig: ${PKGDIR}/${PKG}
	cd ${PKGDIR}; gpg --detach-sign ${PKG}
	chmod -w ${PKGDIR}/${PKG}
	chmod -w ${PKGDIR}/${PKG}.sig

docdist: # We do not want auto make dis
	rm -rf ${PKGVER}
	tar xf ${PKGDIR}/${PKG} ${PKGVER}/pyformex/doc/html && tar czf ${PKGDIR}/${PKGDOC} ${PKGVER}
	rm -rf ${PKGVER}

${PKGDIR}/${PKGLST}: ${PKGDIR}/${PKG}
	tar tzf $< > $@

# Create all our manpages
manpages:
	make -C pyformex/doc manpages
	make -C pyformex/extra manpages

# Publish the distribution to our ftp server
#

pubtest:
	echo ${PKGDIR} ${PUBDIR}

publocal: ${PUBFILES}
	rsync -ltv ${PUBFILES} ${FTPLOCAL}

# Publish the distribution to Savannah
#

pubn: ${PUBDIR}/${PKG}.sig
	echo "DRY RUN PUBLICATION!!!"
	rsync -ltvn ${PUBFILES} ${FTPPUB}
	rsync -ltvn ${PUBDIR}/doc/* ${FTPPUB}/doc

pub: ${PUBDIR}/${PKG}.sig
	rsync -ltv ${PUBFILES} ${FTPPUB}
	rsync -ltv ${PUBDIR}/doc/* ${FTPPUB}/doc

# Register with the python package index
register:
	${PYTHON} setup.py register

upload:
	${PYTHON} setup.py sdist upload --show-response

# Tag the release in the git repository
tag:
	git tag -s -a release-${RELEASE} -m "This is the ${RELEASE} release of pyFormex"

# Push the release tag to origin
pushtag:
	git push origin release-${RELEASE}

# Tag the release in the git repository
tagint:
	git tag -s -a ${RELEASE} -m "This is the alpha version ${RELEASE} of pyFormex"

# Push the release tag to origin
pushtagint:
	git push origin ${RELEASE}


# Creates statistics
stats:
	make -C stats

# Create the Sphinx documentation
html:
	make -C ${SPHINXDIR} html |& tee htmldoc.log

# package the documentation
#docdist: see above

#latexpdf:
#	make -C ${SPHINXDIR} latexpdf

# Publish the documentation on the website

pubdoc:
	make -C ${SPHINXDIR} pub


# Publish the website
publish:
	./publish

commit:
	cd www; cvs commit; cd ..

# Make the PDF manual available for download

pubpdf:
	make -C ${SPHINXDIR} pubpdf


# Test all modules
# Currently this tests only the core modules
testall:
	cd pyformex; for f in *.py; do pyformex --doctest $${f%.py}; done


# Create the C accelerated libraries in 'G' installtype
lib3:
	rm -f pyformex/lib/_clust.cpp
	${PYTHON} setup.py build_ext
	find build -name '*.so' -exec mv {} pyformex/lib \;
	#rm -rf build

lib: lib3

# End
