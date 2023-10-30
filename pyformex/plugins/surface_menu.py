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

"""surface_menu.py

Surface operations plugin menu for pyFormex.
"""

import pyformex as pf
from pyformex.gui import menu
from pyformex.plugins import plot2d
from pyformex.plugins import fe_abq
from pyformex.arraytools import niceLogSize
from pyformex.trisurface import TriSurface, fillBorder
from pyformex.plugins.tools import Plane
from pyformex.plugins import geometry_menu as gm
from pyformex.gui import draw as gs
from pyformex.gui.draw import *

_name_ = 'surface_menu_'

##################### selection and annotations ##########################

selection = pf.GS

##################### surface operations ##########################


def fixNormals(method):
    """Fix the normals of the selected surfaces."""
    SL = selection.check()
    if SL:
        SL = [S.fixNormals(method=method) for S in SL]
        export2(selection.names, SL)
        selection.draw()


def reverseNormals():
    """Reverse the normals of the selected surfaces."""
    SL = selection.check()
    if SL:
        SL = [S.reverse() for S in SL]
        export2(selection.names, SL)
        selection.draw()


def removeNonManifold():
    """Remove the nonmanifold edges."""
    SL = selection.check()
    if SL:
        SL = [S.removeNonManifold() for S in SL]
        export2(selection.names, SL)
        selection.draw()


def createPointsOnSurface():
    """Interactively create points on the selected TriSurface.

    """
    from . import tools_menu
    S = selection.check(single=True)
    if S:
        P = tools_menu.createPoints2D(surface=S)
        if P is not None:
            pname = utils.autoName('coords').peek()
            res = askItems([
                _I('name', pname, text='Name for storing the object'),
                ])
            if res:
                name = res['name']
                if name == pname:
                    next(utils.autoName('coords'))
                export({name: P})
            return P

#
# Operations with surface type, border, ...
#
def showBorder():
    S = selection.check(single=True)
    if S:
        border = S.border()
        if border:
            print("The border consists of %s parts" % len(border))
            print("The sorted border edges are: ")
            print('\n'.join([" %s: %s" % (i, b.elems) for i, b in enumerate(border)]))
            coloredB = [b.compact().setProp(i+1) for i, b in enumerate(border)]
            draw(coloredB, linewidth=3)
            for i, b in enumerate(coloredB):
                c = np.roll(pf.canvas.settings.colormap, i+1, axis=0)
                drawText(str(i), b.center(), color=c, size=18)  # ontop=True)
            export({'border': coloredB})
        else:
            warning("The surface %s does not have a border" % selection[0])
            forget('border')
    return S


def fillBorders():
    _data_ = _name_+'fillBorders_data'
    S = showBorder()
    try:
        B = named('border')
    except Exception:
        return
    print("Got Border")
    clear()
    draw(B)
    if B:
        props = [b.prop[0] for b in B]
        dia = Dialog([
            _I('Fill which borders', itemtype='radio', choices=['All', 'One']),
            _I('Filling method', itemtype='radio', choices=['radial', 'border']),
            _I('merge', False, text='Merge fills into current surface'),
            ])
        if _data_ in pf.PF:
            dia.updateData(pf.PF[_data_])
        res = dia.getResults()
        if res:
            pf.PF[_data_] = res

            if res['Fill which borders'] == 'One':
                B = B[:1]
            fills = [fillBorder(b, method=res['Filling method']).setProp(i+1) for i, b in enumerate(B)]
            if res['merge']:
                name = selection.names[0]
                S = named(name)
                for f in fills:
                    S += f
                export({name: S})
                selection.draw()
            else:
                draw(fills)
                export(dict([('fill-%s'%i, f) for i, f in enumerate(fills)]))


def deleteTriangles():
    S = selection.check(single=True)
    if S:
        picked = pick('element')
        #print picked
        if picked:
            picked = picked[0]
            #print picked
            if len(picked) > 0:
                #print S.nelems()
                S = S.cclip(picked)
                #print "DELETE",type(S)
                name = selection.names[0]
                #print name
                #print S.nelems()
                export({name: S})
                selection.draw()


# Selectable values for display/histogram
# key is a description of a result
# value is a tuple of:
#  - function to calculate the values
#  - domain to display: True to display on edges, False to display on elements

SelectableStatsValues = {
    'Quality': (TriSurface.quality, False),
    'Aspect ratio': (TriSurface.aspectRatio, False),
    'Facet Area': (TriSurface.areas, False),
    'Facet Perimeter': (TriSurface.perimeters, False),
    'Smallest altitude': (TriSurface.smallestAltitude, False),
    'Longest edge': (TriSurface.longestEdge, False),
    'Shortest edge': (TriSurface.shortestEdge, False),
    'Number of node adjacent elements': (TriSurface.nNodeAdjacent, False),
    'Number of edge adjacent elements': (TriSurface.nEdgeAdjacent, False),
    'Edge angle': (TriSurface.edgeAngles, True),
    'Number of connected elements': (TriSurface.nEdgeConnected, True),
    'Curvature': (TriSurface.curvature, False),
}

# Drawable options for curvature.
CurvatureValues = [
    'Shape index S',
    'Curvedness C',
    'Gaussian curvature K',
    'Mean curvature H',
    'First principal curvature k1',
    'Second principal curvature k2',
    'First principal direction d1',
    'Second principal direction d2',
]


def showHistogram(key, val, cumulative):
    y, x = plot2d.createHistogram(val, cumulative=cumulative)
    plot2d.showHistogram(x, y, key)


_stat_dia = None

def showStatistics(key=None, domain=True, dist=False, cumdist=False, clip=None, vmin=None, vmax=None, percentile=False):
    """Show the values corresponding with key in the specified mode.

    key is one of the keys of SelectableStatsValues
    mode is one of ['On Domain','Histogram','Cumulative Histogram']
    """
    S = selection.check(single=True)
    if S:
        func, onEdges = SelectableStatsValues[key]
        kargs = {}
        if key == 'Curvature':
            kargs['neigh'] = _stat_dia.results['neigh']
        val = func(S, **kargs)
        as_vectors = False
        if key == 'Curvature':
            key = _stat_dia.results['curval']
            ind = key.split()[-1]
            if ind in ['d1', 'd2']:
                val = val['d1'], val['d2']
                as_vectors=True
            else:
                val = val[ind]
                val = val[S.elems]

        # !! THIS SHOULD BE IMPLEMENTED AS A GENERAL VALUE CLIPPER
        # !! e.g popping up when clicking the legend
        # !! and the values should be changeable

        if clip:
            clip = clip.lower()
            if percentile:
                try:
                    from scipy.stats.stats import scoreatpercentile
                except Exception:
                    warning("""..

**The **percentile** clipping option is not available.
Most likely because 'python-scipy' is not installed on your system.""")
                    return

                Q1 = scoreatpercentile(val, vmin)
                Q3 = scoreatpercentile(val, vmax)
                factor = 3
                if vmin:
                    vmin = Q1-factor*(Q3-Q1)
                if vmax:
                    vmax = Q3+factor*(Q3-Q1)

            if clip == 'top':
                val = val.clip(max=vmax)
            elif clip == 'bottom':
                val = val.clip(min=vmin)
            else:
                val = val.clip(vmin, vmax)

        if domain:
            clear()
            if as_vectors:
                # TODO: this can become a drawTensor function
                siz =0.5*S.edgeLengths().mean()
                drawVectors(S.coords, val[0], size=siz, color=red)
                drawVectors(S.coords, val[1], size=siz, color=darkgreen)
                lights(True)
                draw(S, mode='smooth')
            else:
                lights(False)
                showSurfaceValue(S, key, val, onEdges)
        if dist:
            showHistogram(key, val, cumulative=False)
        if cumdist:
            showHistogram(key, val, cumulative=True)


def _show_stats(domain, dist):
    if not _stat_dia.validate():
        return
    res = _stat_dia.results
    key = res['Value']
    if dist and res['Cumulative Distribution']:
        cumdist = True
        dist = False
    else:
        cumdist = False
    clip = res['clip']
    if clip == 'None':
        clip = None
    percentile = res['Clip Mode'] != 'Range'
    minval = res['Bottom']
    maxval = res['Top']
    showStatistics(key, domain, dist, cumdist, clip=clip, vmin=minval, vmax=maxval, percentile=percentile)

def _show_domain():
    _show_stats(True, False)
def _show_dist():
    _show_stats(False, True)

def _close_stats_dia():
    global _stat_dia
    # close any created 2d plots
    plot2d.closeAllPlots()
    # close the dialog
    if _stat_dia:
        try:
            _stat_dia.close()
            # this may fail if fialog closed by window manager
        except Exception:
            pass
        _stat_dia = None


def showStatisticsDialog():
    global _stat_dia
    if _stat_dia:
        _close_stats_dia()

    dispmodes = ['On Domain', 'Histogram', 'Cumulative Histogram']
    keys = list(SelectableStatsValues.keys())
    _stat_dia = gs.Dialog(
        caption='Surface Statistics', items=[
            _C('', [
                _I('Value', itemtype='vradio', choices=keys),
                _I('neigh', text='Curvature Neighbourhood', value=1),
                _I('curval', text='Curvature Value', itemtype='vradio', choices=CurvatureValues),
            ]),
            _C('', [
                _I('clip', itemtype='hradio', choices=['None', 'Top', 'Bottom', 'Both']),
                _I('Clip Mode', itemtype='hradio', choices=['Range', 'Percentile']),
                _G('Clip Values', check=True, items=[
                    _I('Top', 1.0),
                    _I('Bottom', 0.0),
                ]),
                _I('Cumulative Distribution', False),
            ]),
        ],
        actions=[
            ('Close', _close_stats_dia),
            ('Distribution', _show_dist),
            ('Show on domain', _show_domain)],
        default='Show on domain'
        )
    _stat_dia.show()


def showSurfaceValue(S, txt, val, onEdges):
    """Display a scalar value on the surface or its edges"""
    from pyformex.field import Field
    if onEdges:
        M = Mesh(S.coords, S.edges)
    else:
        M = S
    fld = Field(M, 'elemc', val)
    drawField(fld)
    #drawText(txt, (10, 240), size=18)


def partitionByAngle():
    S = selection.check(single=True)
    if S:
        res  = askItems([_I('angle', 60.),
                         _I('firstprop', 1),
                         _I('sort by', choices=['number', 'area', 'none']),
                         ])
        pf.app.processEvents()
        if res:
            selection.remember()
            with Timer() as t:
                p = S.partitionByAngle(angle=res['angle'], sort=res['sort by'])
                S = S.setProp(p + res['firstprop'])
            nprops = len(S.propSet())
            print(f"Partitioned in {nprops} parts ({t.mem:.6f} sec.)")
            for p in S.propSet():
                print(" p: %s; n: %s" % (p, (S.prop==p).sum()))
            selection.draw()


def showFeatureEdges():
    S = selection.check(single=True)
    if S:
        selection.draw()
        res  = askItems([
            _I('angle', 60.),
            _I('minangle', -60.),
            _I('ontop', False),
            ])
        pf.app.processEvents()
        if res:
            ontop = res.pop('ontop')
            p = S.featureEdges(**res)
            M = Mesh(S.coords, S.edges[p])
            draw(M, color='red', linewidth=3, bbox='last', nolight=True, ontop=ontop)


#############################################################################
# Transformation of the vertex coordinates (based on Coords)


def clipSelection():
    """Clip the selection.

    The coords list is not changed.
    """
    FL = selection.check()
    if FL:
        res = askItems([_I('axis', 0),
                        _I('begin', 0.0),
                        _I('end', 1.0),
                        _I('nodes', 'all', choices=['all', 'any', 'none']),
                        ], caption='Clipping Parameters')
        if res:
            bb = bbox(FL)
            axis = res['axis']
            xmi = bb[0][axis]
            xma = bb[1][axis]
            dx = xma-xmi
            xc1 = xmi + float(res['begin']) * dx
            xc2 = xmi + float(res['end']) * dx
            selection.changeValues([F.clip(F.test(nodes=res['nodes'], dir=axis, min=xc1, max=xc2)) for F in FL])
            selection.drawChanges()


def clipAtPlane():
    """Clip the selection with a plane."""
    FL = selection.check()
    if not FL:
        return

    dsize = bbox(FL).dsize()
    esize = 10 ** (niceLogSize(dsize)-5)

    res = askItems([_I('Point', [0.0, 0.0, 0.0], itemtype='point'),
                    _I('Normal', [1.0, 0.0, 0.0], itemtype='point'),
                    _I('Keep side', itemtype='radio', choices=['positive', 'negative']),
                    _I('Nodes', itemtype='radio', choices=['all', 'any', 'none']),
                    _I('Tolerance', esize),
                    _I('Property', 1),
                    ], caption = 'Define the clipping plane')
    if res:
        P = res['Point']
        N = res['Normal']
        side = res['Keep side']
        nodes = res['Nodes']
        atol = res['Tolerance']
        prop = res['Property']
        selection.remember(True)
        if side == 'positive':
            func = TriSurface.clip
        else:
            func = TriSurface.cclip
        FL = [func(F, F.test(nodes=nodes, dir=N, min=P, atol=atol)) for F in FL]
        FL = [F.setProp(prop) for F in FL]
        export(dict([('%s/clip' % n, F) for n, F in zip(selection, FL)]))
        selection.set(['%s/clip' % n for n in selection])
        selection.draw()


def cutWithPlane():
    """Cut the selection with a plane."""
    FL = selection.check()
    if not FL:
        return

    dsize = bbox(FL).dsize()
    esize = 10 ** (niceLogSize(dsize)-5)

    res = askItems([_I('Point', [0.0, 0.0, 0.0], itemtype='point'),
                    _I('Normal', [1.0, 0.0, 0.0], itemtype='point'),
                    _I('New props', [1, 2, 2, 3, 4, 5, 6]),
                    _I('Side', 'positive', itemtype='radio', choices=['positive', 'negative', 'both']),
                    _I('Tolerance', esize),
                    ], caption = 'Define the cutting plane')
    if res:
        P = res['Point']
        N = res['Normal']
        p = res['New props']
        side = res['Side']
        atol = res['Tolerance']
        selection.remember(True)
        if side == 'both':
            G = [F.toFormex().cutWithPlane(P, N, side=side, atol=atol, newprops=p) for F in FL]
            G_pos = []
            G_neg  =[]
            for F in G:
                G_pos.append(TriSurface(F[0]))
                G_neg.append(TriSurface(F[1]))
            export(dict([('%s/pos' % n, g) for n, g in zip(selection, G_pos)]))
            export(dict([('%s/neg' % n, g) for n, g in zip(selection, G_neg)]))
            selection.set(['%s/pos' % n for n in selection] + ['%s/neg' % n for n in selection])
            selection.draw()
        else:
            selection.changeValues([F.cutWithPlane(
                P, N, newprops=p, side=side, atol=atol) for F in FL])
            selection.drawChanges()


def cutSelectionByPlanes():
    """Cut the selection with one or more planes, which are already created."""
    S = selection.check(single=True)
    if not S:
        return

    planes = listAll(clas=Plane)
    if len(planes) == 0:
        warning("You have to define some planes first.")
        return

    res1 = selectItems(planes,
                       caption=f"Known objects of type {selection.object_type}",
                       sort=True)
    if res1:
        res2 = askItems([
            _I('Tolerance', 0.),
            _I('Color by', 'side', itemtype='radio',
               choices=['side', 'element type']),
            _I('Side', 'both', itemtype='radio',
               choices=['positive', 'negative', 'both']),
        ], caption = 'Cutting parameters')
        if res2:
            planes = [named(r) for r in res1]
            p = [plane.P for plane in planes]
            n = [plane.n for plane in planes]
            atol = res2['Tolerance']
            color = res2['Color by']
            side = res2['Side']
            if color == 'element type':
                newprops = [1, 2, 2, 3, 4, 5, 6]
            else:
                newprops = None
            if side == 'both':
                Spos, Sneg = S.toFormex().cutWithPlane(p, n, newprops=newprops, side=side, atol=atol)
            elif side == 'positive':
                Spos = S.toFormex().cutWithPlane(p, n, newprops=newprops, side=side, atol=atol)
                Sneg = Formex()
            elif side == 'negative':
                Sneg = S.toFormex().cutWithPlane(p, n, newprops=newprops, side=side, atol=atol)
                Spos = Formex()
            if Spos.nelems() !=0:
                Spos = TriSurface(Spos)
                if color == 'side':
                    Spos.setProp(2)
            else:
                Spos = None
            if Sneg.nelems() != 0:
                Sneg = TriSurface(Sneg)
                if color == 'side':
                    Sneg.setProp(3)
            else:
                Sneg = None
            name = selection.names[0]
            export({name+"/pos": Spos})
            export({name+"/neg": Sneg})
            selection.set([name+"/pos", name+"/neg"]+res1)
            selection.draw()


def intersectWithPlane():
    """Intersect the selection with a plane."""
    FL = selection.check()
    if not FL:
        return
    res = askItems([_I('Name suffix', 'intersect'),
                    _I('Point', (0.0, 0.0, 0.0)),
                    _I('Normal', (1.0, 0.0, 0.0)),
                    ], caption = 'Define the cutting plane')
    if res:
        suffix = res['Name suffix']
        P = res['Point']
        N = res['Normal']
        M = [S.intersectionWithPlane(P, N) for S in FL]
        draw(M, color='red')
        export(dict([('%s/%s' % (n, suffix), m) for (n, m) in zip(selection, M)]))


def slicer():
    """Slice the surface to a sequence of cross sections."""
    S = selection.check(single=True)
    if not S:
        return
    res = askItems([_I('Direction', [1., 0., 0.]),
                    _I('# slices', 20),
                    ], caption = 'Define the slicing planes')
    if res:
        axis = res['Direction']
        nslices = res['# slices']
        with busyCursor():
            with Timer("Sliced", auto=True):
                slices = S.slice(dir=axis, nplanes=nslices)
        print([s.nelems() for s in slices])
        draw([s for s in slices if s.nelems() > 0], color='red',
             bbox='last', view=None)
        export({'%s/slices' % selection[0]: slices})


def spliner():
    """Slice the surface to a sequence of cross sections."""
    from pyformex import olist
    from pyformex.curve import BezierSpline
    S = selection.check(single=True)
    if not S:
        return
    res = askItems([_I('Direction', [1., 0., 0.]),
                    _I('# slices', 20),
                    _I('remove_invalid', False),
                    ], caption = 'Define the slicing planes')
    if res:
        axis = res['Direction']
        nslices = res['# slices']
        remove_cruft = res['remove_invalid']
        with busyCursor():
            slices = S.slice(dir=axis, nplanes=nslices)
        print([s.nelems() for s in slices])
        split = [s.splitProp() for s in slices if s.nelems() > 0]
        split = olist.flatten(split)
        hasnan = [isnan(s.coords).any() for s in split]
        print(hasnan)
        print(sum(hasnan))
        #print [s.closed for s in split]
        export({'%s/split' % selection[0]: split})
        draw(split, color='blue', bbox='last', view=None)
        splines = [BezierSpline(s.coords[s.elems[:, 0]], closed=True) for s in split]
        draw(splines, color='red', bbox='last', view=None)
        export({'%s/splines' % selection[0]: splines})


def refine():
    S = selection.check(single=True)
    if S:
        res = askItems([_I('max_edges', -1),
                        _I('min_cost', -1.0),
                        ])
        if res:
            selection.remember()
            if res['max_edges'] <= 0:
                res['max_edges'] = None
            if res['min_cost'] <= 0:
                res['min_cost'] = None
            S=S.refine(**res)
            selection.changeValues([S])
            selection.drawChanges()


###################################################################
########### The following functions are in need of a make-over



def flytru_stl():
    """Fly through the stl model."""
    global ctr
    Fc = Formex(array(ctr).reshape((-1, 1, 3)))
    path = connect([Fc, Fc], bias=[0, 1])
    flyAlong(path)


def create_volume():
    """Generate a volume tetraeder mesh inside a surface."""
    S = selection.check(single=True)
    if S:
        M = S.tetgen(quality=True)
        export({'tetmesh': M})
        selection.set([])
        gm.selection.set(['tetmesh'])
        print("Created and selected tetraeder mesh 'tetmesh'")


def surface2abq():
    S = selection.check(single=True)
    if S:
        types = ["Abaqus INP files (*.inp)"]
        fn = askNewFilename(pf.cfg['workdir'], types)
        if fn:
            print("Exporting surface model to %s" % fn)
            updateGUI()
            fe_abq.exportMesh(fn, S, eltype='S3', header="Abaqus model generated by pyFormex from input file %s" % fn.name)


def volume2abq():
    if PF['volume'] is None:
        return
    types = ["Abaqus INP files (*.inp)"]
    fn = askNewFilename(pf.cfg['workdir'], types)
    if fn:
        print("Exporting volume model to %s" % fn)
        updateGUI()
        mesh = Mesh(PF['volume'])
        fe_abq.exportMesh(fn, mesh, eltype='C3D%d' % elems.shape[1], header="Abaqus model generated by tetgen from surface in STL file %s.stl" % PF['project'])


def show_nodes():
    n = 0
    data = askItems([_I('node number', n),
                     ])
    n = int(data['node number'])
    if n > 0:
        nodes, elems = PF['surface']
        print("Node %s = %s", (n, nodes[n]))


def trim_border(elems, nodes, nb, visual=False):
    """Removes the triangles with nb or more border edges.

    Returns an array with the remaining elements.
    """
    b = border(elems)
    b = b.sum(axis=1)
    trim = np.where(b>=nb)[0]
    keep = np.where(b<nb)[0]
    nelems = elems.shape[0]
    ntrim = trim.shape[0]
    nkeep = keep.shape[0]
    print("Selected %s of %s elements, leaving %s" % (ntrim, nelems, nkeep))

    if visual and ntrim > 0:
        prop = np.zeros(shape=(F.nelems(),), dtype=int32)
        prop[trim] = 2  # red
        prop[keep] = 1  # yellow
        F = Formex(nodes[elems], prop)
        clear()
        draw(F, view='left')

    return elems[keep]


def trim_surface():
    check_surface()
    res = askItems([_I('Number of trim rounds', 1),
                    _I('Minimum number of border edges', 1),
                    ])
    n = int(res['Number of trim rounds'])
    nb = int(res['Minimum number of border edges'])
    print("Initial number of elements: %s" % elems.shape[0])
    for i in range(n):
        elems = trim_border(elems, nodes, nb)
        print("Number of elements after border removal: %s" % elems.shape[0])


def read_tetgen(surface=True, volume=True):
    """Read a tetgen model from files  fn.node, fn.ele, fn.smesh."""
    ftype = ''
    if surface:
        ftype += ' *.smesh'
    if volume:
        ftype += ' *.ele'
    fn = askFilename(pf.cfg['workdir'], "Tetgen files (%s)" % ftype)
    nodes = elems =surf = None
    if fn:
        chdir(fn)
        project = utils.projectName(fn)
        set_project(project)
        nodes, nodenrs = tetgen.readNodes(project+'.node')
#        print("Read %d nodes" % nodes.shape[0])
        if volume:
            elems, elemnrs, elemattr = tetgen.readElems(project+'.ele')
            print("Read %d tetraeders" % elems.shape[0])
            PF['volume'] = (nodes, elems)
        if surface:
            surf = tetgen.readSurface(project+'.smesh')
            print("Read %d triangles" % surf.shape[0])
            PF['surface'] = (nodes, surf)
    if surface:
        show_surface()
    else:
        show_volume()


def read_tetgen_surface():
    read_tetgen(volume=False)

def read_tetgen_volume():
    read_tetgen(surface=False)


def scale_volume():
    if PF['volume'] is None:
        return
    nodes, elems = PF['volume']
    nodes *= 0.01
    PF['volume'] = (nodes, elems)


def show_volume():
    """Display the volume model."""
    if PF['volume'] is None:
        return
    nodes, elems = PF['volume']
    F = Formex(nodes[elems], eltype='tet4')
    print("BBOX = %s" % F.bbox())
    clear()
    draw(F, color='random')
    PF['vol_model'] = F


###################  Operations using gts library  ########################


def check():
    S = selection.check(single=True)
    if S:
        sta, out = S.check()
        print((sta, out))
        if sta == 3:
            clear()
            draw(S.select(out), color='red')
            draw(S, color='black')


def split():
    S = selection.check(single=True)
    if S:
        print(S.split(base=selection[0], verbose=True))


def coarsen():
    S = selection.check(single=True)
    if S:
        res = askItems([_I('min_edges', -1),
                        _I('max_cost', -1.0),
                        _I('mid_vertex', False),
                        _I('length_cost', False),
                        _I('max_fold', 1.0),
                        _I('volume_weight', 0.5),
                        _I('boundary_weight', 0.5),
                        _I('shape_weight', 0.0),
                        _I('progressive', False),
                        _I('log', False),
                        _I('verbose', False),
                        ])
        if res:
            selection.remember()
            if res['min_edges'] <= 0:
                res['min_edges'] = None
            if res['max_cost'] <= 0:
                res['max_cost'] = None
            S=S.coarsen(**res)
            selection.changeValues([S])
            selection.drawChanges()


def boolean():
    """Boolean operation on two surfaces.

    op is one of
    '+' : union,
    '-' : difference,
    '*' : interesection
    """
    surfs = listAll(clas=TriSurface)
    if len(surfs) == 0:
        warning("You currently have no exported surfaces!")
        return

    ops = ['+ (Union)', '- (Difference)', '* (Intersection)']
    res = askItems([_I('surface 1', choices=surfs),
                    _I('surface 2', choices=surfs),
                    _I('operation', choices=ops),
                    _I('check self intersection', False),
                    _I('verbose', False),
                    ], caption='Boolean Operation')
    if res:
        SA = pf.PF[res['surface 1']]
        SB = pf.PF[res['surface 2']]
        SC = SA.boolean(SB, op=res['operation'].strip()[0],
                        check=res['check self intersection'],
                        verbose=res['verbose'])
        export({'__auto__': SC})
        selection.set('__auto__')
        selection.draw()


def intersection():
    """Intersection curve of two surfaces."""
    surfs = listAll(clas=TriSurface)
    if len(surfs) == 0:
        warning("You currently have no exported surfaces!")
        return

    res = askItems([_I('surface 1', choices=surfs),
                    _I('surface 2', choices=surfs),
                    _I('check self intersection', False),
                    _I('verbose', False),
                    ], caption='Intersection Curve')
    if res:
        SA = pf.PF[res['surface 1']]
        SB = pf.PF[res['surface 2']]
        SC = SA.intersection(SB, check=res['check self intersection'],
                             verbose=res['verbose'])
        export({'__intersection_curve__': SC})
        draw(SC, color=red, linewidth=3)


def voxelize():
    """Voxelize"""
    pass


###################  Operations using instant-meshes  ########################


def remesh():
    """Remesh a TriSurface to a quality Tri3 and/or Quad4 Mesh.

    Shows a Dialog to set the parameters for the remeshing.
    Then creates and shows the new mesh.
    """
    if not selection.check(single=True):
        selection.ask(single=True)

    if not selection.names:
        return

    name = selection.names[0]
    S = named(name)

    # ask parameters
    _name = 'Remesh parameters'
    _data = _name + '_data'
    nseq = utils.NameSequence(name)
    next(nseq)
    newname = next(nseq)
    methods = ['acvd']
    for m in ['instant-meshes']:
        if utils.External.has(m):
            methods.append(m)
    # use instant-meshes as default if available
    method = 'instant-meshes' if 'instant-meshes' in methods else methods[0]
    vertices = S.ncoords()
    faces = S.nelems()
    edglen = S.edgeLengths()
    scale = 0.5*(edglen.min()+edglen.max())
    smooth = 2
    boundaries = not S.isClosedManifold()
    crease = 90
    intrinsic = False
    res = askItems(caption=_name, store=_data, items=[
        _I('name', newname),
        _I('method', method, choices=methods),
        _G('a', text='Parameters for acvd', items=[
            _I('npoints', vertices),
            _I('ndiv', 3),
            ]),
        _G('i', text='Parameters for instant-meshes', items=[
            _I('posy', 6),
            _I('rosy', 6),
            _I('resolution', choices=['vertices', 'faces', 'scale'],
               itemtype='combo', value='vertices'),
            _I('vertices', vertices),
            _I('faces', faces),
            _I('scale', scale),
            _I('smooth', 2),
            _I('boundaries', boundaries),
            _I('intrinsic', intrinsic),
            _I('crease', crease),
            ]),
    ], enablers=[
        ('method', 'acvd', 'a'),
        ('method', 'instant-meshes', 'i'),
        ('resolution', 'vertices', 'vertices'),
        ('resolution', 'faces', 'faces'),
        ('resolution', 'scale', 'scale'),
        ]
    )

    # infile: :term:`path_like`
    #     An .obj file containing a pure tri3 mesh.
    # outfile: :term:`path_like`
    #     The output file with the quad (or quad dominated) Mesh.
    #     It can be a .obj or .ply file. If not provided, it is generated
    #     from the input file with the '.obj' suffix replaced 'with _quad.obj'.
    # threads: int
    #     Number of threads to use in parallel computations.
    # deterministic: bool
    #     If True, prefer (slower) deterministic algorithms.
    # crease: float
    #     Dihedral angle threshold for creases.
    # smooth: int
    #     Number of smoothing & ray tracing reprojection steps (default: 2).
    # dominant: bool
    #     If True, generate a quad dominant mesh instead of a pure quad mesh.
    #     The output may contain some triangles and pentagones as well.
    # intrinsic: bool
    #     If True, use intrinsic mode (extrinsic is the default).
    # boundaries: bool
    #     If True, align the result on the boundaries.
    #     Only applies when the surface is not closed.
    # posy: 3 | 4 | 6
    #     Specifies the position symmetry type.
    # rosy: 2 | 4 | 6
    #     Specifies the orientation symmetry type.

    # Combinations:
    # posy   rosy      result
    #   3      6       quality tri3
    #   4      4       quality quad4

    if res:
        pf.verbose(2, f"Remeshing {name}")
        qname = res['name']
        res.pop('name', None)
        for k in ['scale', 'faces', 'vertices']:
            if k != res['resolution']:
                res.pop(k, None)
        res.pop('resolution', None)
        with Timer('Remeshing') as t:
            mesh = S.remesh(**res)
        if mesh:
            pf.verbose(2, f"Converted {name} to {mesh.elName()} Mesh named {qname} in {t.mem:.6f} sec.")
            pf.verbose(2, mesh)
            export({qname:mesh})
            pf.GUI.selection['geometry'].set([qname])
            pf.GUI.selection['geometry'].draw()
        else:
            pf.verbose(2, "Conversion failed")


def tri2quad_auto(suffix='_quad4'):
    """Autoconvert a set of TriSurfaces to quad4 Meshes

    The outputs are stored with names equal to the input names plus the suffix.
    If a suffix '' is given, the input names are used and the input objects
    will be cleared from memory.
    """
    if not selection.check():
        selection.ask()

    if not selection.names:
        return

    names = selection.names
    objects = [named(n) for n in names]
    if suffix:
        names = [n + suffix for n in names]

    print(f"Converting {names} to quad4")
    meshes = [o.remesh() for o in objects]
    meshes = dict([(n, o) for n, o in zip(names, meshes) if o is not None])
    names = list(meshes.keys())
    print(f"Converted {names} to quad4")
    export(meshes)

    pf.GUI.selection['geometry'].set(names)
    pf.GUI.selection['geometry'].draw()



################### menu #################

def create_menu(before='help'):
    """Create the Surface menu."""
    MenuData = [
        ("&Fix Normals", fixNormals, {'data':'internal'}),
        ("&Fix Normals (admesh)", fixNormals, {'data':'admesh'}),
        ("&Reverse Normals", reverseNormals),
        ("&Remove NonManifold Edges", removeNonManifold),
        ("&Statistics", showStatisticsDialog),
        ("&Refine", refine),
        ('&Remesh', remesh),
        ("&Create Points on Surface", createPointsOnSurface),
        ("&Partition By Angle", partitionByAngle),
        ("&Show Feature Edges", showFeatureEdges),
        ("&Show Border", showBorder),
        ("&Fill Border", fillBorders),
        ("&Delete Triangles", deleteTriangles),
        ("---", None),
        ("&Clip/Cut", [
            ("&Clip", clipSelection),
            ("&Clip At Plane", clipAtPlane),
            ("&Cut With Plane", cutWithPlane),
            ("&Multiple Cut", cutSelectionByPlanes),
            ("&Intersection With Plane", intersectWithPlane),
            ("&Slicer", slicer),
            ("&Spliner", spliner),
        ]),
        ("---", None),
        ('&GTS functions', [
            ('&Check surface', check),
            ('&Split surface', split),
            ("&Coarsen surface", coarsen),
            ("&Refine", refine),
            ("&Boolean operation on two surfaces", boolean),
            ("&Intersection curve of two surfaces", intersection),
            #          ("&Voxelize the volume inside a surface", voxelize),
        ]),
        ('&Instant Meshes', [
            ('&Quality remesh surface to tri3 or quad4 mesh', remesh),
            ('&Auto-convert multiple surfaces to quad4', tri2quad_auto),
        ]),
        #        ("&Show volume model",show_volume),
        # ("&Print Nodal Coordinates",show_nodes),
        # ("&Convert STL file to OFF file",convert_stl_to_off),
        # ("&Sanitize STL file to OFF file",sanitize_stl_to_off),
        #        ("&Trim border",trim_surface),
        ("&Create volume mesh", create_volume),
        #        ("&Read Tetgen Volume",read_tetgen_volume),
        #        ("&Export surface to Abaqus",surface2abq),
        #        ("&Export volume to Abaqus",volume2abq),
        ("---", None),
    ]
    m = menu.Menu('Surface', items=MenuData, parent=pf.GUI.menu, before=before)
    # Enable menus needing optional external software
    m['&GTS functions'].setEnabled(utils.External.has('gts-extra') != '')
    m['&Instant Meshes'].setEnabled(utils.External.has('instant-meshes') != '')
    return m


# End
