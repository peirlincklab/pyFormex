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
"""Display help

"""
import sys

import pyformex as pf
from pyformex import utils
from pyformex import software
from pyformex.path import Path
from pyformex.gui import draw
from pyformex.gui import qtgl
from .Settings import updateSettings


# TODO: this info may be not up to date
# The location of the local docs depends on the type of installation
#
#  'G': build/install under git tree
#         build_dir = pyformexdir / 'doc'
#
#  'URD': as user post-install:
#         build_dir = .local/share/pyformex/doc/html
#
#  'R': pyformex installation from .tar.gz, during install:
#         build in pyformexdir / 'doc', install in /usr/local/share
#
#  'D': debian package during creation
#         build in pyformexdir / 'doc'
#         create pyformex-doc package /usr/share/doc/pyformex/html
#

def checkHtmlDir():
    """Check that we have the html docs available"""
    for htmldir in (
            # paths where the html docs might be
            pf.cfg['htmldir'],
            pf.cfg['docdir'] / 'html',
            Path.home() / '.local' / 'share' / 'pyformex' / 'doc' / 'html',
            Path.home() / '.local' / 'lib' / 'pyformex' / 'doc' / 'html',
    ):
        if (htmldir / 'index.html').exists():
            if pf.cfg['htmldir'] != htmldir:
                pf.cfg['htmldir'] = htmldir  # correct if needed
            return True
    return False


def checkHtmlReqs():
    """Check the requirements for building the html docs"""
    required = {
        'System': {
            'pyFormex_installtype': 'G',
        },
        'Modules': {
            'docutils': '>= 0',
            'sphinx': '>= 1.4',
        },
        'Externals': {
            'sphinx-build': '>= 1.4',
        },
    }
    # CHECK SOFT
    result, s = software.checkSoftware(required, report=True)
    print(s)
    return result


def buildHtmlDocs(builddir=None):
    """Build the html documentation.

    Note: this is only for users building the docs.
    Builds at installation time are done by the Makefile.
    builddir is where the docs are built.
    For 'G' this is pyformex/doc/.
    For 'RD' this is .local/share/pyformex/doc/html.

    """
    # Check requirements
    if not checkHtmlReqs() != 'OK':
        raise ValueError("I could not find some required software")
    # the source should always be here
    sourcedir = pf.cfg['pyformexdir'] / 'sphinx'
    print(f"BUILDDIR {builddir} ({type(builddir)})")
    if builddir is None:
        # set default build dir
        if pf.installtype in 'GU':
            builddir = pf.cfg['docdir']
        else:
            builddir = Path.home() / '.local' / 'share' / 'pyformex' / 'doc'
    print(f"BUILDDIR {builddir} ({type(builddir)})")
    builddir.mkdir(parents=True, exist_ok=True)
    if not builddir.is_writable_dir():
        draw.showError("TODO: !!!!!!")
    if draw.showInfo(f"""..

Building local documentation
----------------------------
I will now build the local documentation in ::

  {builddir}

As this is a lengthy process (especially if you are building
for the first time), I will run it in the background
and notify you when it's ready.
""", actions=['Cancel', 'OK']) == 'OK':
        cmd = f'make -C {sourcedir} html BUILDDIR={builddir}'
        P = draw.runLongTask(cmd)
        print(f"Return with value {P.returncode}")
        updateSettings({'htmldir': builddir}, save=True)
        menu_enabler(pf.GUI.menu)


def searchIndex():
    """Search text in pyFormex refman index.

    Asks a pattern from the user and searches for it the index of the
    local pyFormex documentation. Displays the results in the browser.
    """
    from pyformex.gui.draw import _I
    res = draw.askItems([
        _I('text', '', text='String to search'),
        ])

    if res:
        showLocalURL(f"search.html?q={res['text']}&check_keywords=yes&area=default")


def searchText():
    """Search text in pyFormex source files.

    Asks a pattern from the user and searches for it through all
    the pyFormex source files.
    """
    from pyformex.gui.draw import _I
    res = draw.askItems([
        _I('pattern', '', text='String to grep'),
        _I('options', '', text='Options', tooltip=
           "Some cool options: -a (extended search), -i (ignore case), "
           "-f (literal string), -e (extended regexp)"),
        ])

    if res:
        out = utils.grepSource(relative=False, **res)
        draw.showText(out, mono=True) #, modal=False)


def catchAndDisplay(expression):
    """Catch stdout from a Python expression and display it in a window."""
    save = sys.stdout
    try:
        with utils.TempFile() as f:
            sys.stdout = f
            eval(expression)
            f.seek(0)
            draw.showText(f.read())
    finally:
        sys.stdout = save


def opengl():
    """Display the OpenGL format description."""
    from pyformex.opengl import gl
    s = utils.formatDict(gl.gl_version()) + '\n'
    s += qtgl.OpenGLFormat(pf.canvas.format())
    draw.showText(s, mono=True)

def detected():
    """Display the detected software components."""
    from pyformex.main import whereami
    draw.showText(whereami() +
                  '\n\n' +
                  software.reportSoftware(header="Detected Software"),
                  mono=True)

def about():
    """Display short information about pyFormex."""
    version = pf.Version()
    draw.showInfo(f"""..

{version}
{'='*len(version)}

A tool for generating, manipulating and transforming 3D geometrical models by sequences of mathematical operations.

{pf.Copyright}

Distributed under the GNU GPL version 3 or later
""")

def developers():
    """Display the list of developers."""
    devs = [
        'Matthieu De Beule',
        'Nic Debusschere',
        'Gianluca De Santis',
        'Bart Desloovere',
        'Wouter Devriendt',
        'Francesco Iannaccone',
        'Peter Mortier',
        'Tim Neels',
        'Tomas Praet',
        'Tran Phuong Toan',
        'Sofie Van Cauter',
        'Benedict Verhegghe',
        'Zhou Wenxuan',
    ]
    utils.shuffle(devs)
    draw.showInfo("The following people have\n"
                  "contributed to pyFormex.\n"
                  "They are listed in random order.\n\n" +
                  '\n'.join(devs) +
                  "\n\nIf you feel that your name was left\n"
                  "out in error, please write to\n"
                  "bverheg@gmail.com\n")


_cookies = [
    "Smoking may be hazardous to your health.",
    "Windows is a virus.",
    "Coincidence does not exist. Perfection does.",
    "It's all in the code.",
    "Python is the universal glue.",
    "Intellectual property is a mental illness.",
    "Programmers are tools for converting caffeine into code.",
    "There are 10 types of people in the world: those who understand binary, and those who don't.",
    "Linux: the choice of a GNU generation",
    "Everything should be made as simple as possible, but not simpler. (A. Einstein)",
    "Perfection [in design] is achieved, not when there is nothing more to add, but when there is nothing left to take away. (Antoine de Saint-Exupéry)",
    "Programming today is a race between software engineers striving to build bigger and better idiot-proof programs, and the universe trying to build bigger and better idiots. So far, the universe is winning. (Rick Cook)",
    "In theory, theory and practice are the same. In practice, they're not. (Yoggi Berra)",
    "Most good programmers do programming not because they expect to get paid or get adulation by the public, but because it is fun to program. (Linus Torvalds)",
    "Always code as if the guy who ends up maintaining your code will be a violent psychopath who knows where you live. (Martin Golding)",
    "If Microsoft had developed Internet, we could not ever see the source code of web pages. HTML might be a compiled language then.",
    "What one programmer can do in one month, two programmers can do in two months.",
    "Windows 9x: n. 32 bit extensions and a graphical shell for a 16 bit patch to an 8 bit operating system originally coded for a 4 bit microprocessor, written by a 2 bit company that can't stand 1 bit of competition. (Cygwin FAQ)",
    "You know, when you have a program that does something really cool, and you wrote it from scratch, and it took a significant part of your life, you grow fond of it. When it's finished, it feels like some kind of amorphous sculpture that you've created. It has an abstract shape in your head that's completely independent of its actual purpose. Elegant, simple, beautiful.\nThen, only a year later, after making dozens of pragmatic alterations to suit the people who use it, not only has your Venus-de-Milo lost both arms, she also has a giraffe's head sticking out of her chest and a cherubic penis that squirts colored water into a plastic bucket. The romance has become so painful that each day you struggle with an overwhelming urge to smash the fucking thing to pieces with a hammer. (Nick Foster)",
    "One of my most productive days was throwing away 1000 lines of code. (Ken Thompson)",
    ]
utils.shuffle(_cookies)

def roll(l):
    l.append(l.pop(0))

def cookie():
    draw.showInfo(_cookies[0], ["OK"])
    roll(_cookies)


# Help showing functions

def showLocalURL(filename):
    """Show a html document in the local html dir.

    Parameters
    ----------
    filename: str
        Path of the file relative to pf.cfg['htmldir']
    """
    path = pf.cfg['htmldir'] / filename
    draw.showURL(f"file:{path}")


def showConfig(which):
    """Show one of the configs: S(ession), U(ser), F(actory)"""
    cfg = {'S': pf.cfg, 'U': pf.prefcfg, 'F': pf.refcfg}[which]
    draw.showText(str(cfg))


def install_external(pkgdir, prgname):
    """Install external software from the pyformex/extra dir"""
    extdir = pf.cfg['pyformexdir'] / 'extra' / pkgdir
    cmd = f"cd {extdir} && make && make install"
    P = utils.command(cmd, shell=True)
    if P.returncode:
        draw.showText(P.stdout + P.stderr)
    else:
        if utils.External.has(prgname, check=True):
            info = f"Succesfully installed {prgname}"
        else:
            info ="You should now restart pyFormex!"
        draw.showInfo(info)
    return P.returncode


# Short aliases for use in items
_L = showLocalURL
_C = showConfig
_F = draw.showFile
_U = draw.showURL
_E = install_external

# constant strings used in items
docdir = pf.cfg['docdir']
savannah = 'http://savannah.nongnu.org/'

def showHelp(action):
    """Function triggered by the help menu items.

    If the action's data is a tuple with a callable as first item,
    call it with the remainder of the tuple as arguments.
    """
    pf.debug(f"SHOWHELP {action.text()}", pf.DEBUG.HELP)
    data = action.data()
    if data and isinstance(data, tuple) and callable(data[0]):
        data[0](*data[1:])

##### extra help items when running from source directory ########

if pf.installtype in 'UG':
    # extra help items for developer version
    devdir = pf.cfg['pyformexdir'] / '..'
    dev_installs = [
        # ('dxfparser', (_E, 'dxfparser', 'pyformex-dxfparser')),  # fails
        ('postabq', (_E, 'postabq', 'pyformex-postabq')),
        ('gtsinside', (_E, 'gts', 'gtsinside')),
        ]
    dev_docs = [
        ('Developer HOWTO', (_F, devdir / "HOWTO-dev.rst")),
        ('pyFormex coding style guide', (_F, devdir / "HOWTO-style.rst")),
        ('Installation of extra software', (_F, devdir / "install-extra.rst")),
        ('Numpy documentation guidelines', (_U, 'https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard')),
        ('re-structured text (reST)', (_U, 'http://docutils.sourceforge.io/rst.html')),
        ]
    dev_docs = [
        ('Developer Guides', dev_docs),
        # TODO: for some reason we need to specify the data=None argument
        # otherwise Qt passes False to the function. Is this new?
        # there may be other places where this fails. Set data=None by default?
        ('Build local documentation', buildHtmlDocs),
        ]

########## The help menu ##########

def menu_enabler(menu):
    """Disable items that are not available"""
    if not checkHtmlDir():
        m = menu['Help']
        first = m.index('Local documentation')
        last = m.index('Search in index')
        for a in m.actions()[first:last+1]:
            a.setEnabled(False)

MenuData = ('Help',[
    ('Online documentation', (_U, pf.cfg['help/webdoc'])),
    ('---', None),
    ('Local documentation', (_L, 'index.html')),
    ('Reference Manual', (_L, 'refman.html')),
    ('Tutorial', (_L, 'tutorial.html')),
    ('Running pyFormex', (_L, 'running.html')),
    ('Module Index', (_L, 'py-modindex.html')),
    ('Index', (_L, 'genindex.html')),
    ('Search in index', searchIndex),
    ('Search in source', searchText),
    ('About Current Application', draw.showDoc),
    ('---', None),
    ('Readme', (_F, docdir / 'README.rst')),
    ('ReleaseNotes', (_F, docdir / 'ReleaseNotes')),
    ('License', (_F, docdir / 'LICENSE')),
    ('Detected Software', detected),
    ('OpenGL Format', opengl),
    ('Settings', [
        ('Session settings', (_C, 'S')),
        ('User settings', (_C, 'U')),
        ('Factory settings', (_C, 'F')),
    ]),
    ('---', None),
    ('Important Links', [
        ('pyFormex', (_U, 'http://pyformex.org')),
        ('pyFormex development', (_U, 'https://gitlab.com/bverheg/pyformex')),
        ('pyFormex issues', (_U, 'https://gitlab.com/bverheg/pyformex/-/issues')),
        ('pyFormex @Savannah', [
            ('project page', (_U, savannah + 'projects/pyformex/')),
            ('support', (_U, savannah + 'support/?func=additem&group=pyformex')),
            ('bugs', (_U, savannah + 'bugs/?func=additem&group=pyformex')),
        ]),
        ('Python', (_U, 'https://python.org')),
        ('NumPy', (_U, 'https://numpy.org/doc/stable/')),
    ]),
    ('Fortune Cookie', cookie),
    ('People', developers),
    ('---', None),
    ('About', about),
    ('---', None),
    ('Install Externals', [
        ('Instant Meshes', (_E, 'instant', 'instant-meshes')),
    ] + dev_installs),
] + dev_docs,
            { 'func': showHelp }
)

# End
