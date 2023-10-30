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

"""BeamFreq_calix

This example shows the first natural vibration modes of an elastic beam.
It requires an external program, calix, which can be downloaded from
ftp://bumps.ugent.be/pub/calix/
Make sure you have version 1.5-a8 or higher.

See example BeamFreq for a version that does not require calix.
"""
_level = 'normal'
_topics = ['FEA', 'curve', 'drawing']
_techniques = ['external', 'viewport']

from pyformex.gui.draw import *
from pyformex import curve

def check_calix(version='>= 1.5-a8'):
    """Check that we have the required calix version"""
    ok = utils.External.check('calix', version)
    if not ok:
        showText("""..

Error
-----
An error occurred when I tried to find the program 'calix'.
This probably means that calix is not installed on your system,
or that the installed version is not one I can use for this example.

Calix is a free program and you can install it as follows:

- download calix (%s or higher) from ftp://bumps.ugent.be/pub/calix/
- unpack, compile and install (as root)::

   tar xvzf calix-%s.tar.gz
   cd calix-1.5
   make
   (sudo) make install
""" % (version, version))
    return ok

n = 16
nshow = 4
bcons = ['cantilever', 'simply supported']
bcon = 'cantilever'
keep = False
verbose = False


def geometry():
    global M

    res = askItems([
        _I('n', n, text='number of elements along beam'),
        _I('nshow', nshow, text='number of natural modes to show'),
        _I('bcon', bcon, text='beam boundary conditions', choices=bcons),
        _I('keep', keep, text='keep data and result files'),
        _I('verbose', verbose, text='show intermediate information'),
        ])
    if not res:
        return

    globals().update(res)
    F = simple.line([0., 0., 0.], [0., 1., 0.], n)
    M = F.toMesh()
    return M


def compute():
    global nshow, a, freq
    nnod = M.ncoords()
    nel = M.nelems()
    nmat = 1
    iout = 1

    # init
    s=""";calix script written by pyFormex (example BeamFreq_calix)
start
use program 'frame.cal'
endtext
"""

    # params
    s += " %s %s %s %s\n" % (nnod+1, nel, nmat, iout)
    # nodes
    for i, x in enumerate(M.coords):
        s += "%5d%10.3e%10.3e%10.3e\n" %  ((i+1,)+tuple(x))
    # orientation node
    s += "%5d%10.3e%10.3e%10.3e\n\n" %  (nnod+1, 0.0, 0.0, 1.0)

    # boundary conditions
    s += "%5s    0    1    1    1    1    0%5s    1\n" %  (2, nnod-2)
    s += "%5s    1    1    1    1    1    1\n" % (nnod+1)
    if bcon == 'cantilever':
        # boundary conditions for cantilever
        s += "%5s    1    1    1    1    1    1\n" % (1)
        s += "%5s    0    1    1    1    1    0\n" % (nnod)
    else:
        # boundary conditions for simply supported
        s += "%5s    1    1    1    1    1    0\n" % (1)
        s += "%5s    1    1    1    1    1    0\n" % (nnod)
    s += '\n'
    # material
    s += "      3.d6     1.2d6      1.00     3000.      1.00     70.d4    110.d4\n"
    # elems
    fmt = "%5s"*(M.nplex()+3) + '\n'
    for i, e in enumerate(M.elems+1):
        s += fmt % ((i+1, 1)+tuple(e)+(nnod+1,))

    # action and output in a format we can easily read back
    s += """
exec frame_ev
endtext
intvar name nnod 1
intvar name ndof 7
file open 'test.out' write seq 17
user printf '(i5)' nnod $17
user printf '(i5)' ndof $17
user printf '(5g13.4)' EIG $17
user printf '(5g13.4)' DISPL $17
file close $17
stop
"""
    savedir = Path.cwd()
    with utils.TempDir() as tmpdir:
        chdir(tmpdir)
        print("Using a temporary directory: %s" % tmpdir)

        Path('temp.dta').write_text(s)

        if verbose:
            # show calix input data
            showFile('temp.dta')

        # run calix
        cmd = "calix temp.dta temp.res"
        Path('test.out').remove()

        P = utils.command(cmd)

        if verbose:
            # show calix output
            showText(P.stdout)
            showFile('temp.res')
            showFile('test.out')

        # read results from eigenvalue analysis
        with open('test.out', 'r') as fil:
            nnod, ndof = np.fromfile(fil, sep=' ', count=2, dtype=int)
            eig = np.fromfile(fil, sep=' ', count=4*ndof).reshape(ndof, 4)
            nshow = min(nshow, ndof)
            freq = eig[:nshow, 2]
            basefreq = freq[0]
            print("Frequencies: %s" % freq)
            print("Multipliers: %s" % (freq/freq[0]))

            a = np.fromfile(fil, sep=' ',).reshape(-1, nnod, 6)
            # print a.shape
            # remove the extra node
            a = a[:, :-1, :]

        chdir(savedir)


def drawDeformed(M, u, r):
    xd = M.coords.copy()
    xd[:, 0] += u
    c = curve.NaturalSpline(xd)
    draw(c, color=red)
    draw(c.pointsOn())


def showResults(hscale):
    for i in range(nshow):
        viewport(i)
        clear()
        transparent(False)
        lights(False)
        linewidth(2)
        draw(M)
        ai = a[i]
        u = ai[:, 0]
        imax = np.argmax(abs(u))
        r = ai[:, 5]
        sc = hscale / u[imax]
        u *= sc
        r *= sc
        # print u,r
        drawDeformed(M, u, r)
        fi = freq[i]
        mi = fi/freq[0]
        drawText('%s Hz = %.2f f0' % (fi, mi), (20, 20), size=20)


def run():
    resetAll()
    clear()
    flat()
    if not check_calix():
        return

    M = geometry()
    if M:
        compute()
        layout(nshow, ncols=4)
        showResults(hscale = 0.5)

if __name__ == '__draw__':
    run()
# End
