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
"""Double Layer Flat Space Truss Roof

"""

_level = 'advanced'
_topics = ['FEA']
_techniques = ['dialog', 'animation', 'persistence', 'color']

import time

from pyformex.gui.draw import *
from pyformex.plugins.properties import *


def run():
    try:
        ############################
        # Load the needed calpy modules
        from pyformex.plugins import calpy_itf
        print("Loading calpy")
        import calpy
        calpy.options.optimize = False
        print("Loading calpy.fe_util")
        from calpy import fe_util
        print("Loading calpy.truss3d")
        from calpy import truss3d

        ############################
    except Exception:
        pf.warning("Calpy could not be loaded")
        return

    if not checkWorkdir():
        error("No writable path: I can not execute the simulation.\nCopy the script to a writable path and try running from there.")
        return

    ####
    #Data
    ###################

    dx = 1800  # Modular size [mm]
    ht = 1500  # Deck height [mm]
    nx = 8     # number of bottom deck modules in x direction
    ny = 6     # number of bottom deck modules in y direction

    q = -0.005  # distributed load [N/mm^2]


    #############
    #Creating the model
    ###################

    top = (Formex('l:1').replicm((nx-1, ny)) + Formex('l:2').replicm((nx, ny-1))).scale(dx)
    top.setProp(3)
    bottom = (Formex('l:1').replicm((nx, ny+1)) + Formex('l:2').replicm((nx+1, ny))).scale(dx).translate([-dx/2, -dx/2, -ht])
    bottom.setProp(0)
    T0 = Formex(4*[[[0, 0, 0]]]) 	   # 4 times the corner of the top deck
    T4 = bottom.select([0, 1, nx, nx+1])  # 4 nodes of corner module of bottom deck
    dia = connect([T0, T4]).replicm((nx, ny), (dx, dx))
    dia.setProp(1)

    F = (top+bottom+dia)

    # Show upright
    createView('myview1', (0., -90., 0.))
    clear()
    linewidth(1)
    draw(F, view='myview1')

    ############
    #Creating FE-model
    ###################

    M = F.toMesh()

    ###############
    #Creating elemsets
    ###################
    # Remember: elements in mesh are in the same order as elements in M
    topbar = np.where(M.prop==3)[0]
    bottombar = np.where(M.prop==0)[0]
    diabar = np.where(M.prop==1)[0]

    ###############
    #Creating nodesets
    ###################

    nnod = M.ncoords()
    nlist = np.arange(nnod)
    count = np.zeros(nnod)
    for n in M.elems.flat:
        count[n] += 1
    field = nlist[count==8]
    topedge = nlist[count==7]
    topcorner = nlist[count==6]
    bottomedge = nlist[count==5]
    bottomcorner = nlist[count==3]
    edge = np.concatenate([topedge, topcorner])
    support = np.concatenate([bottomedge, bottomcorner])

    ########################
    #Defining and assigning the properties
    #############################

    Q = 0.5*q*dx*dx

    P = PropertyDB()
    P.nodeProp(field, cload = [0, 0, Q, 0, 0, 0])
    P.nodeProp(edge, cload = [0, 0, Q/2, 0, 0, 0])
    P.nodeProp(support, bound = [1, 1, 1, 0, 0, 0])

    circ20 = ElemSection(section={'name': 'circ20', 'sectiontype': 'Circ', 'radius': 10, 'cross_section': 314.159}, material={'name': 'S500', 'young_modulus': 210000, 'shear_modulus': 81000, 'poisson_ratio': 0.3, 'yield_stress': 500, 'density': 0.000007850})

    props = [ \
         P.elemProp(topbar, section=circ20, eltype='T3D2'), \
         P.elemProp(bottombar, section=circ20, eltype='T3D2'), \
         P.elemProp(diabar, section=circ20, eltype='T3D2'), \
         ]

    # Since all elements have same characteristics, we could just have used:
    #   P.elemProp(section=circ20,elemtype='T3D2')
    # But putting the elems in three sets allows for separate postprocessing


    #########
    #calpy analysis
    ###################

    # boundary conditions
    bcon = np.zeros([nnod, 3], dtype=int)
    bcon[support] = [1, 1, 1]
    fe_util.NumberEquations(bcon)

    #materials
    mats = np.array([[p.young_modulus, p.density, p.cross_section] for p in props])
    matnr = np.zeros_like(F.prop)
    for i, p in enumerate(props):
        matnr[p.set] = i+1
    matnod = np.concatenate([matnr.reshape((-1, 1)), M.elems+1], axis=-1)
    ndof = bcon.max()

    # loads
    nlc=1
    loads = np.zeros((ndof, nlc), at.Float)
    for n in field:
        loads[:, 0] = fe_util.AssembleVector(loads[:, 0], [0.0, 0.0, Q], bcon[n, :])
    for n in edge:
        loads[:, 0] = fe_util.AssembleVector(loads[:, 0], [0.0, 0.0, Q/2], bcon[n, :])

    # Running calpy analysis
    print("Performing analysis: this may take some time")
    if checkWorkdir():
        indir = pf.cfg['workdir']
    else:
        tmpdir = utils.TempDir()
        indir = tmpdir.path
    outfile = indir / Path(__file__).with_suffix('.out')
    print("Output is written to file '%s'" % outfile.resolve())
    stdout_saved = sys.stdout
    try:
        with outfile.open('w') as fil:
            sys.stdout = fil
            print("# File created by pyFormex on %s" % time.ctime())
            print("# Script name: %s" % pf.scriptName)
            displ, frc = truss3d.static(M.coords, bcon, mats, matnod, loads, Echo=True)
            print("# Analysis finished on %s" % time.ctime())
    except:
        return
    finally:
        sys.stdout = stdout_saved


    ################################
    #Using pyFormex as postprocessor
    ################################

    if pf.options.gui:

        from pyformex.plugins.postproc import frameScale
        from pyformex.gui.colorscale import ColorScale
        from pyformex.opengl.decors import ColorLegend


        def showOutput():
            showFile(outfile)


        def showForces():
            # Give the mesh some meaningful colors.
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
            clear()
            linewidth(3)
            draw(M, color=cval)
            drawText('Normal force in the truss members', (300, 50), size=14)
            CLA = ColorLegend(CS, 100, 10, 10, 30, 200, size=14)
            decorate(CLA)


        # Show a deformed plot
        def deformed_plot(dscale=100.):
            """Shows a deformed plot with deformations scaled with a factor scale."""
            # deformed structure
            dnodes = M.coords + dscale * displ[:, :, 0]
            deformed = Mesh(dnodes, M.elems, M.prop)
            FA = draw(deformed, bbox='last', view=None, wait=False)
            TA = drawText('Deformed geometry (scale %.2f)' % dscale, (300, 50), size=24)
            return FA, TA

        def animate_deformed_plot(amplitude, sleeptime=1, count=1):
            """Shows an animation of the deformation plot using nframes."""
            FA = TA = None
            clear()
            while count > 0:
                count -= 1
                for s in amplitude:
                    F, T = deformed_plot(s)
                    undraw([FA, TA])
                    TA, FA = T, F
                    sleep(sleeptime)

        def getOptimscale():
            """Determine an optimal scale for displaying the deformation"""
            siz0 = F.sizes()
            dF = Formex(displ[:, :, 0][M.elems])
            #clear(); draw(dF,color=black)
            siz1 = dF.sizes()
            return at.niceNumber(1./(siz1/siz0).max())


        def showDeformation():
            clear()
            linewidth(1)
            draw(F, color=black)
            linewidth(3)
            deformed_plot(optimscale)
            view('last', True)


        def showAnimatedDeformation():
            """Show animated deformation"""
            nframes = 10
            res = askItems([
                _I('scale', optimscale),
                _I('nframes', nframes),
                _I('form', 'revert', choices=['up', 'updown', 'revert']),
                _I('duration', 5./nframes),
                _I('ncycles', 2),
                ], caption='Animation Parameters')
            if res:
                scale = res['scale']
                nframes = res['nframes']
                form = res['form']
                duration = res['duration']
                ncycles = res['ncycles']
                amp = scale * frameScale(nframes, form)
                animate_deformed_plot(amp, duration, ncycles)


        optimscale = getOptimscale()
        options = ['None', 'Output File', 'Member forces', 'Deformation', 'Animated deformation']
        functions = [None, showOutput, showForces, showDeformation, showAnimatedDeformation]
        cnt = 0
        while True and cnt < 1000:
            cnt += 1
            ans = ask("Which results do you want to see?", options)
            ind = options.index(ans)
            if ind <= 0:
                break
            functions[ind]()
            if widgets.input_timeout > 0:  #timeout
                break

if __name__ == '__draw__':
    run()
# End
