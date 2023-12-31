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
_techniques = ['color']

from pyformex.gui.draw import *
from pyformex.plugins.properties import *
from pyformex.plugins.fe_abq import *
import os

def run():
    ####
    #Data
    ###################

    dx = 1800  # Modular size [mm]
    ht = 900  # Deck height [mm]
    nx = 4     # number of bottom deck modules in x direction
    ny = 5   # number of bottom deck modules in y direction

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
    # Remember: elements in mesh are in the same order as elements in F
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
    edge =  np.concatenate([topedge, topcorner])
    support = np.concatenate([bottomedge, bottomcorner])

    ########################
    #Defining and assigning the properties
    #############################

    Q = 0.5*q*dx*dx

    P = PropertyDB()
    P.nodeProp(set=field, cload = [0, 0, Q, 0, 0, 0])
    P.nodeProp(set=edge, cload = [0, 0, Q/2, 0, 0, 0])
    P.nodeProp(set=support, bound = [1, 1, 1, 0, 0, 0])

    circ20 = ElemSection(section={'name': 'circ20', 'sectiontype': 'Circ', 'radius': 10, 'cross_section': 314.159}, material={'name': 'S500', 'young_modulus': 210000, 'shear_modulus': 81000, 'poisson_ratio': 0.3, 'yield_stress': 500, 'density': 0.000007850})

    # example of how to set the element type by set
    P.elemProp(set=topbar, section=circ20, eltype='T3D2')
    P.elemProp(set=bottombar, section=circ20, eltype='T3D2')

    # alternatively, we can specify the elements by an index value
    # in an array that we will pass in the Abqdata 'eprop' argument
    P.elemProp(prop=1, section=circ20, eltype='T3D2')

    # Since all elements have same characteristics, we could just have used:
    #   P.elemProp(section=circ20,elemtype='T3D2')
    # But putting the elems in three sets allows for separate postprocessing


    # Print node and element property databases
    for p in P.nprop:
        print(p)
    for p in P.eprop:
        print(p)



    #############
    #Writing the inputfile
    ###################

    step = Step(
        out = [Output(type='field')],
        res = [Result(kind='element', keys=['S']),
                Result(kind='node', keys=['U'])
                ]
        )
    model = FEModel(M)

    if not checkWorkdir():
        return

    AbqData(model, P, [step], eprop=F.prop).write('SpaceTruss')

if __name__ == '__draw__':
    run()
# End
