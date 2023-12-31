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
"""FontForge

This example demonstrates the use of FontForge library to render text. To be
able to run it, you need to have the FontForge library and its Python bindings
installed. On Debian GNU/Linux you can achieve this by installing the package
'python3-fontforge'.

"""

_level = 'advanced'
_topics = ['curve', 'font']
_techniques = ['bezier', 'borderfill']

import sys

from pyformex.gui.draw import *
from pyformex import curve
from pyformex.trisurface import fillBorder
from pyformex.plugins.polygon import Polygon
from pyformex import geomtools
from pyformex import utils

try:
    import fontforge
    utils.setSaneLocale()


    def intersection(self, other):
        """Find the intersection points of two plane curves"""
        X = np.stack([self.coords, roll(self.coords, -1, axis=0)], axis=1)
        print(X.shape)
        F = self.toMesh().toFormex()
        # create planes // z
        P = other.coords
        N = other.vectors().rotate(90)
        return geomtools.intersectSegmentWithPlane(F, P, N)


    def partitionByContour(self, contour):
        """Partition the surface by splitting it at a contour on the surface.

        """
        #edg = self.edges
        feat = self.featureEdges(angle=angle)
        p = self.maskedEdgeFrontWalk(mask=~feat, frontinc=0)

        if sort == 'number':
            p = sortSubsets(p)
        elif sort == 'area':
            p = sortSubsets(p, self.areas())

        return p


    def glyphCurve(c):
        """Convert a glyph contour to a list of quad bezier curves."""
        points = []
        control = []
        P0 = c[0]
        points.append([P0.x, P0.y])
        for i in (np.arange(len(c))+1) % len(c):
            P = c[i]
            if P0.on_curve and P.on_curve:
                # straight segment
                control.append([0.5*(P0.x+P.x), 0.5*(P0.y+P.y)])
                points.append([P.x, P.y])
                P0 = P
                continue
            elif P0.on_curve and not P.on_curve:
                # undecided
                P1 = P0
                P0 = P
                continue
            elif not P0.on_curve and P.on_curve:
                # a single quadratic segment
                control.append([P0.x, P0.y])
                points.append([P.x, P.y])
                P0 = P
                continue
            else:  # not P0.on_curve and not P.on_curve:
                # two quadratic segments, central point to be interpolated
                PM = fontforge.point()
                PM.x = 0.5*(P0.x+P.x)
                PM.y = 0.5*(P0.y+P.y)
                PM.on_curve = True
                points.append([PM.x, PM.y])
                control.append([P0.x, P0.y])
                P1 = PM
                P0 = P
                continue

        return Coords(points), Coords(control)



    def contourCurve(c):
        """Convert a fontforge contour to a pyFormex curve"""
        points, control = glyphCurve(c)
        Q = at.interleave(points, control)
        return curve.BezierSpline(control=Q, degree=2, closed=True)


    def charContours(fontfile, character):
        font = fontforge.open(fontfile, 5)
        print("FONT INFO: %s" % font)
        #print(dir(font))
        #print(font.gpos_lookups)

        g = font[ord(character)]
        print("GLYPH INFO: %s" % g)
        #print(dir(g))
        #print(g.getPosSub)


        l = g.layers[1]
        print("Number of curves: %s" % len(l))
        ## c = l[0]
        ## print(c)
        ## #print(dir(c))
        ## print(c.closed)
        ## print(c.is_quadratic)
        ## print(c.isClockwise())
        ## print(len(c))
        ## #print(c.reverseDirection())

        ## #if c.isClockwise():
        ## #    c = c.reverseDirection()

        return l


    def connect2curves(c0, c1):
        x0 = c0.coords
        x1 = c1.coords
        i, j, d = geomtools.closestPair(x0, x1)
        x = np.concatenate([roll(x0, -i, axis=0), roll(x1, -j, axis=0)])
        return curve.BezierSpline(control=x, degree=2, closed=True)


    def charCurves(fontfile, character):
        l = charContours(fontfile, character)
        c = [contourCurve(li) for li in l]
        fontname = utils.projectName(fontfile)
        export({'%s-%s'%(fontname, character): c})
        return c


    def drawCurve(curve, color, fill=None, with_border=True, with_points=True):
        if fill is not None:
            border = curve.approx(ndiv=24)
            if with_border:
                draw(border, color=red)
            drawNumbers(border.coords, color=red)
            P = Polygon(border.coords)
            M = P.toMesh()
            clear()
            draw(M)
            #t,x,wl,wt = intersection(P,P)
            #print(x.shape)
            #draw(Formex(x),color=red)
            #return
            if fill == 'polygonfill':
                print("POLYGON")
                surface = fillBorder(border, 'planar')
            else:
                # Test importing voronoi
                try:
                    #from voronoi import voronoi
                    surface = delaunay(border.coords)
                except Exception:
                    #print(sys.path)
                    warning("DELAUNAY fill is not available")
                    surface = []
            draw(surface, color=color)
            #drawNumbers(surface)
        else:
            draw(curve, color=color)
        if with_points:
            drawNumbers(curve.pointsOn())
            drawNumbers(curve.pointsOff(), color=red)


    def drawCurve2(curve, color, fill=None, with_border=True, with_points=True):
        if fill:
            curve = connect2curves(*curve)
            drawCurve(curve, blue, fill)
        else:
            drawCurve(curve[0], color, with_border=with_border, with_points=with_points)
            drawCurve(curve[1], color, with_border=with_border, with_points=with_points)


    def show(fontname, character, fill=None):
        """Show a character from a font"""
        print("Char '%s' from font '%s'" % (character, fontname))
        curve = charCurves(fontname, character)
        size = curve[0].pointsOn().bbox().dsize()
        clear()

        if fill:
            if len(curve) == 1:
                drawCurve(curve[0], blue, fill=fill)
            elif len(curve) == 2:
                drawCurve2(curve, blue, fill=fill)
        else:
            for c in curve:
                drawCurve(c, blue)

        return


    # Initialization

    # List font files on nonstandard places
    my_fonts = [
        pf.cfg['datadir'] / 'blippok.ttf',
    ]
    fonts = []

    def run():

        global fonts

        if not fonts:
            fonts =  [f for f in my_fonts if f.exists()] + utils.listFonts()

        print("There are %s fonts" % len(fonts))
        print("There are %s monospaced fonts" % len(utils.listMonoFonts()))
        print("The default monospaced font is %s" % utils.defaultMonoFont())

        data = dict(
            fontname = fonts[0],
            character = 'S',
            fill = 'None',
            )
        try:
            data.update(pf.PF['_FontForge_data_'])
        except Exception:
            pass
        print("Number of available fonts: %s" % len(fonts))
        if not data['fontname']:
            data['fontname'] = fonts[0]
        print("Current font: %s" % data['fontname'])
        res = askItems(store=data, items=[
            _I('fontname', choices=fonts),
            _I('character', max=1),
            _I('fill', itemtype='radio', choices=['None', 'polygonfill', 'delaunay']),
            ])

        if not res:
            return

        pf.PF['_FontForge_data_'] = res
        if res['fill'] == 'None':
            del res['fill']

        show(**res)



except ImportError:

    def run():

        warning("I could not import fontforge. "
                "To run this example, first make sure that you have "
                "fontforge and the proper Python bindings. "
                "E.g.: on Debian/Ubuntu, install 'python3-fontforge'."
                )

except Exception:
    raise


if __name__ == '__draw__':
    run()


# End
