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

"""FeBol

"""

_level = 'advanced'
_topics = ['FEA']
_techniques = ['properties', 'export']

from pyformex.gui.draw import *

from pyformex.plugins.fe import FEModel
from pyformex.plugins.properties import *
from pyformex.plugins.fe_abq import Step, Output, Result, AbqData


from pyformex import simple


def centralPoint(X):
    """Find the most central point of a Coords"""
    d = X.distanceFromPoint(X.center())
    return np.argmin(d)

def globalNodeNr(M, group, nodid):
    """Return the global node number of a node with group id.

    group is the element group number.
    nodid is the index of the node in the raveled elems definition (i.e.
    if the elements have plexitude nplex, the first element has nodids
    0..nplex-1, the second one has nodids nplex..2*nplex-1, etc.).
    This function then returns the global node number for the with
    give group number and nodid.
    """
    return M.elems[group].ravel()[nodid]

def groupCentralPoint(M, group):
    """Return the node number of the most central point of the given group"""
    # Find the local group center
    nodid = centralPoint(M.coords[M.elems[group]])
    return globalNodeNr(M, group, nodid)


def run():
    reset()
    clear()

    # Property numbers used
    pbol = 1  # Bol
    ptop = 2  # Top plate
    pbot = 3  # Bottom plate

    scale = 15.   # scale (grid unit in mm)

    # Create a solid sphere
    BolSurface = simple.sphere().scale(scale)
    try:
        # tetgen may not be available
        Bol = BolSurface.tetgen(quality=True).setProp(pbol)
    except Exception:
        return
    draw(Bol)
    view('xz')

    # Create top and bottom plates
    plate = simple.rectangle(4, 4).toMesh().centered()
    topplate = plate.setProp(ptop).trl(2, 1.).scale(scale)
    botplate = plate.setProp(pbot).trl(2, -1.).scale(scale)
    draw([topplate, botplate])

    # model is completely drawn, keep fixed bbox
    setDrawOptions({'bbox': 'last', 'marksize': 8})

    # Assemble the model
    FEM = FEModel(meshes=[Bol, topplate, botplate])

    # Create the property database
    PDB = PropertyDB()

    # In this simple example, we do not use a material/section database,
    # but define the data directly
    steel = {
        'name': 'steel',
        'young_modulus': 207000,
        'poisson_ratio': 0.3,
        'density': 7.85e-9,
        'plastic': [
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
            ],
        }
    solid_steel = {
        'name': 'solid_steel',
        'sectiontype': 'solid',
        'material': 'steel',   # Need material reference for Abaqus
        }
    steel_plate = {
        'name': 'solid_steel',
        'sectiontype': 'solid',
        'thickness': 3,
        'material': 'steel',   # Need material reference for Abaqus
        }

    # Set the element properties
    eset = dict([(p, np.where(FEM.prop==p)[0]) for p in [pbol, ptop, pbot]])

    # Bol is elasto/plastic
    PDB.elemProp(set=eset[pbol], name='Bol', eltype='C3D4', section=ElemSection(section=solid_steel, material=steel))

    # Top plate is rigid or elasto-plastic
    topplate_rigid = True
    if topplate_rigid:
        # Rigid bodies need a reference node.
        # We select the most central node, but any node would also work,
        # e.g. pbref = FEM.elems[1][0][0], the very first node in the group
        reftop = groupCentralPoint(FEM, 1)
        print("Top plate refnode: %s" % reftop)
        draw(FEM.coords[reftop], color=green)
        PDB.elemProp(set=eset[ptop], name='TopPlate', eltype='R3D4', section=ElemSection(sectiontype='rigid', refnode=reftop))
    else:
        PDB.elemProp(set=eset[ptop], name='TopPlate', eltype='CPS4', section=ElemSection(section=steel_plate, material=steel))


    # Bottom plate is rigid or elasto-plastic
    refbot = groupCentralPoint(FEM, 2)
    print("Bottom plate refnode: %s" % refbot)
    draw(FEM.coords[refbot], color=blue)
    PDB.elemProp(set=eset[pbot], name='BottomPlate', eltype='R3D4', section=ElemSection(sectiontype='rigid', refnode=refbot))

    # Set the boundary conditions
    # Bottom plate is fixed
    fixed = np.unique(FEM.elems[2])
    PDB.nodeProp(tag='init', set=[refbot], name='Fixed', bound=[1, 1, 1, 1, 1, 1])

    # Set the loading conditions
    # Top plate gets z-displacement of -5 mm
    displ = np.unique(FEM.elems[1])
    PDB.nodeProp(tag='init', set=[reftop], name='Displ', bound=[1, 1, 0, 1, 1, 1])
    PDB.nodeProp(tag='step1', set=[reftop], name='Refnod', displ=[(2, -0.5)])

    ## # Set the loading conditions
    ## # All elements of Plate1 have a pressure loading of 10 MPa
    ## loaded = FEM.elemNrs(1)
    ## PDB.elemProp(tag='step1',set=loaded,name='Loaded',dload=ElemLoad('P',10.0))

    from pyformex.plugins.fe_abq import Interaction
    PDB.Prop(tag='init', generalinteraction=Interaction(name='interaction1', friction=0.1))
    PDB.Prop(tag='init', generalcontact='interaction1')

    print("Element properties")
    for p in PDB.getProp('e'):
        print(p)
    print("Node properties")
    for p in PDB.getProp('n'):
        print(p)
    print("Model properties")
    for p in PDB.getProp(''):
        print(p)

    out = [Output(type='history'),
            Output(type='field'),
            ]

    # Create requests for output to the .fil file.
    # - the displacements in all nodes
    # - the stress components in all elements
    # - the stresses averaged at the nodes
    # - the principal stresses and stress invariants in the elements of part B.
    # (add output='PRINT' to get the results printed in the .dat file)
    res = [Result(kind='NODE', keys=['U']),
            Result(kind='ELEMENT', keys=['S'], set='Bol'),
            Result(kind='ELEMENT', keys=['S'], pos='AVERAGED AT NODES', set='Bol'),
            Result(kind='ELEMENT', keys=['SP', 'SINV'], set='Bol'),
            ]

    # Define steps (default is static)
    step1 = Step('DYNAMIC', time=[1., 1., 0.01, 1.], tags=['step1'])

    data = AbqData(FEM, prop=PDB, steps=[step1], res=res, initial=['init'])

    if ack('Export this model in ABAQUS input format?', default='No'):
        fn = askNewFilename(filter='inp')
        if fn:
            data.write(jobname=fn, group_by_group=True)


if __name__ == '__draw__':
    run()

# End
