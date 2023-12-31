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
"""X-shaped truss analysis

"""

_level = 'advanced'
_topics = ['FEA']
_techniques = ['color', 'persistence']

import time

from pyformex.gui.draw import *
from pyformex.examples.X_truss import X_truss

############################
# Load the needed calpy modules

from pyformex.plugins import calpy_itf
from calpy.fe_util import *
from calpy.truss3d import *
############################


def run():
    # if not checkWorkdir():
    #     error("No writable path: I can not execute the simulation.\nCopy the script to a writable path and try running from there.")
    #     return

    # ###########################

    reset()
    clear()
    bgcolor(lightgrey)

    # create a truss (Vandepitte, Chapter 1, p.16)
    n = 5
    l = 800.
    h = 800.
    truss = X_truss(n, l, h)

    # draw it
    clear()
    draw(truss.allNodes(), wait=False)
    draw(truss.allBars())

    # assign property numbers
    truss.bot.setProp(0)
    truss.top.setProp(0)
    truss.vert.setProp(2)
    truss.dia1.setProp(1)
    truss.dia2.setProp(1)
    for p in [truss.bot.prop, truss.top.prop]:
        p[0] = p[n-1] = 3

    # define member properties
    materials={'steel': {'E': 207000, 'nu': 0.3}}
    sections={'hor': 50, 'end': 40, 'dia': 40, 'vert': 30}
    properties = {'0': ['steel', 'hor'],
                   '3': ['steel', 'end'],
                   '2': ['steel', 'vert'],
                   '1': ['steel', 'dia']}

    def getmat(key):
        """Return the 'truss material' with key (str or int)."""
        p = properties.get(str(key), [None, None])
        m = materials.get(p[0], {})
        E = m.get('E', 0.)
        rho = m.get('rho', 0.)
        A = sections.get(p[1], 0.)
        return [E, rho, A]


    # create model for structural analysis
    model = truss.allBars()
    coords, elems = model.fuse()
    props = model.prop
    propset = model.propSet()

    clear()
    draw(Formex(reshape(coords, (coords.shape[0], 1, coords.shape[1]))), wait=False)
    draw(model)


    ############################################

    nnod = coords.shape[0]
    nelems = elems.shape[0]
    # boundary conditions
    # we use the knowledge that the elements are in the order
    # bot,top,vert,mid1,mid2
    # remember to add 1 to number starting from 1, as needed by calpy
    nr_fixed_support = elems[0][0]
    nr_moving_support = elems[n-1][1]
    nr_loaded = elems[2][1]  # right node of the 3-d element
    bcon = ReadBoundary(nnod, 3, """
      all  0  0  1
      %d   1  1  1
      %d   0  1  1
    """ % (nr_fixed_support + 1, nr_moving_support + 1))
    NumberEquations(bcon)
    mats=array([getmat(i) for i in range(max(propset)+1)])
    matnod = np.concatenate([reshape(props+1, (nelems, 1)), elems+1], 1)
    ndof=bcon.max()
    nlc=1
    loads=np.zeros((ndof, nlc), at.Float)
    loads[:, 0]=AssembleVector(loads[:, 0], [0.0, -50.0, 0.0], bcon[nr_loaded, :])

    # Running calpy analysis
    print("Performing analysis: this may take some time")
    if checkWorkdir():
        wrkdir = pf.cfg['workdir']
        print(f"Using workdir {wrkdir}")
    else:
        tmpdir = utils.TempDir()
        wrkdir = tmpdir.path
        print(f"Created tempdir {wrkdir}")
    pwdir()
    # USe a filename with same name as script
    outfile = (wrkdir / Path(__file__).name).with_suffix('.out')
    print(f"outfile is {outfile}")
    print("Output is written to file '%s'" % outfile.resolve())
    stdout_saved = sys.stdout
    try:
        with outfile.open('w') as fil:
            sys.stdout = fil
            print("# File created by pyFormex on %s" % time.ctime())
            print("# Script name: %s" % pf.scriptName)
            displ, frc = static(coords, bcon, mats, matnod, loads, Echo=True)
            print("# Analysis finished on %s" % time.ctime())
    except:
        return
    finally:
        sys.stdout = stdout_saved


    ################################
    #Using pyFormex as postprocessor
    ################################

    from pyformex.gui.colorscale import ColorScale
    from pyformex.opengl.decors import ColorLegend

    # Creating a formex for displaying results is fairly easy
    results = Formex(coords[elems], np.arange(nelems))
    # Now try to give the formex some meaningful colors.
    # The frc array returns element forces and has shape
    #  (nelems,nforcevalues,nloadcases)
    # In this case there is only one resultant force per element (the
    # normal force), and only load case; we still need to select the
    # scalar element result values from the array into a onedimensional
    # vector val.
    val = frc[:, 0, 0]
    # create a colorscale
    CS = ColorScale([blue, yellow, red], val.min(), val.max(), 0., 2., 2.)
    cval = np.array([CS.color(v) for v in val])
    #aprint(cval,header=['Red','Green','Blue'])
    clear()
    draw(results, color=cval)

    bgcolor('lightgreen')
    linewidth(3)
    drawText('Normal force in the truss members', (400, 100), size=12)
    CLA = ColorLegend(CS, 256, 10, 20, 30, 200)
    decorate(CLA)

    # and a deformed plot
    dscale = 10000.
    dcoords = coords + dscale * displ[:, :, 0]
    # first load case
    deformed = Formex(dcoords[elems], np.arange(nelems))
    clear()
    pf.canvas.addDecoration(CLA)
    linewidth(1)
    draw(results, color='darkgreen')
    linewidth(3)
    draw(deformed, color=cval)
    drawText('Normal force in the truss members', (400, 100), size=14)
    drawText('Deformed geometry (scale %.2f)' % dscale, (400, 130), size=12)

    if ack("Show the output file?"):
        showFile(outfile)


if __name__ == '__draw__':
    run()

# End
