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

"""FePlast

This example shows how to create a Finite Element model of a rectangular
steel plate, how to add material properties, boundary conditions and loads,
and how to export the resulting model as an input file for Abaqus(tm) or
Calculix.
"""
_level = 'advanced'
_topics = ['FEA']
_techniques = ['properties', 'export', 'extrude']
_name = 'FePlast'
_data = _name + '_data'

from pyformex.gui.draw import *

from pyformex.plugins.fe import FEModel
from pyformex.plugins.properties import *
from pyformex.plugins.fe_abq import Step, Output, Result, AbqData
from pyformex.plugins import ccxdat
from pyformex.plugins import postproc_menu
from pyformex.mesh import *


def run():
    reset()
    clear()

    processor = 'abq'   # set to 'ccx' for calculix

    # Create a thin rectangular plate.
    # Because it is thin, we use a 2D model (in the xy plane.
    # We actually only model 1/4 of the plate'
    # The full plate could be found from mirroring wrt x and y axes.
    L = 400.  # length of the plate (mm)
    B = 100.  # width of the plate (mm)
    th = 10.  # thickness of the plate (mm)
    L2, B2 = L/2, B/2  # dimensions of the quarter plate
    nl, nb = 16, 10     # number of elements along length, width
    D = 20.
    r = D/2
    e0 = 0.3


    if not 'FePlast_diag' in pf.PF:
        print("Initializing")
        pf.PF['FePlast_diag'] = dict(
            geometry = None,
            material = None,
            eltype = None,
            interpolation = None,
            format = None,
            run = False,
            )


    # User input
    res = askItems(caption=_name, store=_data, items=[
        _I('geometry', choices=['Plain rectangle', 'Rectangle with hole'], text='Plate geometry'),
        _I('material', choices=['Elastic', 'Plastic'], text='Material model'),
        _I('eltype', choices=['quad4', 'quad8', 'hex8', 'hex20'], text='Element type'),
        _I('interpolation', choices=['Linear', 'Quadratic'], text='Degree of interpolation'),
        _I('format', choices=['CalculiX', 'Abaqus'], text='FEA input format'),
        _I('run', False, text='Run simulation'),
        ])

    if not res:
        return

    pf.PF['FePlast_diag'] = res


    # Create geometry
    if res['geometry'] == 'Plain rectangle':
        plate = rectangle(L2, B2, nl, nb)
    else:
        plate = rectangleWithHole(L2, B2, r, (nl,e0), nb)


    if res['eltype'].startswith('hex'):
        plate = plate.extrude(1, dir=2, length=1.0)

    plate = plate.convert(res['eltype'])

    draw(plate)

    # model is completely shown, keep camera bbox fixed
    setDrawOptions({'bbox': 'last', 'marksize': 8})

    # Assemble the FEmodel (this may renumber the nodes!)
    FEM = FEModel(meshes=[plate])

    # Create an empty property database
    PDB = PropertyDB()

    # Define the material data: here we use an elasto-plastic model
    # for the steel
    steel = {
        'name': 'steel',
        'young_modulus': 207000e-6,
        'poisson_ratio': 0.3,
        'density': 7.85e-9,
        }

    if res['material'] == 'Plastic':
        steel.update(
            {'plastic': [
                (305.45,       0.),
                (306.52, 0.003507),
                (308.05, 0.008462),
                (310.96,  0.01784),
                (316.2, 0.018275),
                (367.5, 0.047015),
                (412.5, 0.093317),
                (448.11, 0.154839),
                (459.6, 0.180101),
                (494., 0.259978),
                (506.25, 0.297659),
                (497., 0.334071),
                (482.8, 0.348325),
                (422.5, 0.366015),
                (399.58,   0.3717),
                (1.,  0.37363),
                ]
             })

    # Define the thin steel plate section
    steel_plate = {
        'name': 'steel_plate',
        'sectiontype': 'solid',
        'thickness': th,
        'material': 'steel',   # Reference to the material name above
        }

    # Give the elements their properties: this is simple here because
    # all elements have the same properties. The element type is
    # for an Abaqus plain stress quadrilateral element with 4 nodes.
    PDB.elemProp(name='Plate', eltype='CPS4',
                 section=ElemSection(section=steel_plate, material=steel))

    # Set the boundary conditions
    # The xz and yz planes should be defined as symmetry planes.
    # First, we find the node numbers along the x, y axes:
    elsize = min(L2/nl, B2/nb)  # smallest size of elements
    tol = 0.001*elsize         # a tolerance to avoid roundoff errors
    nyz = FEM.coords.test(dir=0, max=tol)  # test for points in the yz plane
    nxz = FEM.coords.test(dir=1, max=tol)  # test for points in the xz plane
    nyz = np.where(nyz)[0]  # the node numbers passing the above test
    nxz = np.where(nxz)[0]
    draw(FEM.coords[nyz], color=cyan)
    draw(FEM.coords[nxz], color=green)

    # Define the boundary conditions
    # For Abaqus, we could define it like follows
    #PDB.nodeProp(tag='init',set=nyz,name='YZ_plane',bound='XSYMM')
    #PDB.nodeProp(tag='init',set=nxz,name='XZ_plane',bound='YSYMM')
    # But as Calculix does not have the XSYMM/YSYMM possibilities
    # we define the conditions explicitely
    PDB.nodeProp(tag='init', set=nyz, name='YZ_plane', bound=[1, 0, 0, 0, 0, 0])
    PDB.nodeProp(tag='init', set=nxz, name='XZ_plane', bound=[0, 1, 0, 0, 0, 0])

    # The plate is loaded by a uniform tensile stress in the x-direction
    # First we detect the border
    brd, ind = FEM.meshes()[0].getBorder(return_indices=True)
    BRD = Mesh(FEM.coords, brd).compact()
    draw(BRD, color=red, linewidth=2)
    xmax = BRD.bbox()[1][0]   # the maximum x coordinate
    loaded = BRD.test(dir=0, min=xmax-tol)
    # The loaded border elements
    loaded = np.where(loaded)[0]
    draw(BRD.select(loaded), color=blue, linewidth=4)
    # sort the load elements by the local loaded edge number
    lind = ind[loaded]
    samefacerows = at.collectRowsByColumnValue(ind[loaded], 1)
    sortedelems = dict((k,ind[loaded][samefacerows[k],0]) for k in samefacerows)
    # Define the load
    # Apply 4 load steps:
    # 1: small load (10 MPa)
    # 2: higher load, but still elastic (100 MPa)
    # 3: slightly exceeding yield stress (320 MPa)
    # 4: high plastic deformation (400MPa)
    loads = [10., 100., 320., 400.]  # tensile load in MPa
    steps = ['step%s'%(i+1) for i in range(len(loads))]   # step names
    for face in sortedelems:
        abqface = face+1  # BEWARE: Abaqus numbers start with 1
        for step, load in zip(steps, loads):
            PDB.elemProp(
                tag=step, set=sortedelems[face], name='Loaded-%s'%face,
                dload=ElemLoad('P%s'%(abqface), -load))

    # Print the property database
    PDB.print()

    # Create requests for output to the .fil file.
    # - the displacements in all nodes
    # - the stress components in all elements
    # - the stresses averaged at the nodes
    # - the principal stresses and stress invariants in the elements of part B.
    # (add output='PRINT' to get the results printed in the .dat file)
    if res['format'] == 'Abaqus':
        result = [
            Result(kind='NODE', keys=['U']),
            Result(kind='ELEMENT', keys=['S'], set='Plate'),
            Result(kind='ELEMENT', keys=['S'], pos='AVERAGED AT NODES', set='Plate'),
            Result(kind='ELEMENT', keys=['SP', 'SINV'], set='Plate'),
            ]
    else:
        result = [
            Result(kind='NODE', keys=['U'], output='PRINT'),
            Result(kind='ELEMENT', keys=['S'], output='PRINT'),
            ]

    # Define the simulation steps
    # The tags refer to the property database
    simsteps = [Step('STATIC', time=[1., 1., 0.01, 1.], tags=[step]) for step in steps]

    data = AbqData(FEM, prop=PDB, steps=simsteps, res=result, initial=['init'])

    tmpdir = pf.cfg['workdir']
    if not tmpdir.is_writable_dir():
        tmpdir = pf.cfg['tmpdir']
    fn = askNewFilename(tmpdir / 'feplast1.inp', filter='inp')

    if fn:
        cmd = None
        if res['run']:
            cmd = {'CalculiX': 'ccx', 'Abaqus': 'abaqus'}[res['format']]
            if not utils.External.has(res['format'].lower()):
                ans = pf.warning(
                    "I did not find the command '%s' on your system.\n"
                    "If you continue, I can prepare the model and write "
                    "the input file,but not run the simulation" % cmd,
                    actions=['Cancel', 'Continue'])
                if ans == 'Continue':
                    cmd = None
                else:
                    return

        data.write(jobname=fn, group_by_group=True)

        if cmd:
            chdir(fn)
            job = fn.stem
            if cmd == 'ccx':
                cmd = "ccx -i %s" % job
            elif cmd == 'abaqus':
                cmd == "abaqus job=%s" % job
            P = utils.command("ccx -i %s" % job)
            print(P.stdout)

            if ack('Create the result database?'):
                DB = ccxdat.createResultDB(FEM)
                ngp = 8
                fn = fn.with_suffix('.dat')
                ccxdat.readResults(fn, DB, DB.nnodes, DB.nelems, ngp)
                DB.printSteps()
                name = 'FeResult-%s'%job
                export({name: DB})
                postproc_menu.setDB(DB)
                if showInfo(f"""\
The results have been exported as {name}
You can now use the postproc menu to display results""", actions=['Cancel', 'OK']) == 'OK':
                    postproc_menu.selection.set(name)
                    postproc_menu.selectDB(DB)
                    postproc_menu.open_dialog()


if __name__ == '__draw__':
    smoothwire()
    run()

# End
