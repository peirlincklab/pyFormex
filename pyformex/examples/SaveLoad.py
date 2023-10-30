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
"""SaveLoad

Example illustrating the saving to and loading from a file in
the pyFormex zip format (PZF).

"""
_level = 'normal'
_topics = ['save']
_techniques = ['PzfFile', 'field']

from pyformex.gui.draw import *
from pyformex.simple import cylinder
from pyformex.mesh import rectangleWithHole
from pyformex.examples.Spirals import createSpiral

def run():
    clear()
    smoothwire()
    view('xz')

    F = cylinder(3, 4, 12, 2)
    M = rectangleWithHole(10, 10, 3, 6, 3)
    M += M.reflect(0)
    M += M.reflect(1)
    T = TriSurface.read(getcfg('datadir') / 'man.off')
    T = T.scale(4).align('00-', [0., 0., 0.])
    PL = createSpiral(nseg=100, turns=1.8, phi=30., alpha=70., c=0.8)
    PL.attrib(linewidth=3)
    F.setProp('range')
    M.attrib(color='fld:dist3n', lighting=False)
    T.attrib(color='gold', mode='smooth')
    data = at.length(M.coords - [5., 3., 0.])
    M.addField('node', data, 'dist')
    data = abs(M.coords - [5., 3., 0.])
    data /= data.max()
    M.addField('node', data, 'dist3n')
    data = abs(M.centroids() - [5., 3., 0.])
    data /= data.max()
    M.addField('elemc', data, 'dist3c')
    X = Coords('263374').scale(5).rotate(-90., 0).trl([10., 10., 10.])
    X[-1].y -= 5
    C = BezierSpline(X, degree=3, closed=True)
    C.attrib(linewidth=2, color=pyformex_pink)
    draw([F, M, T, PL, C, X])
    CS = CoordSys()
    drawAxes(CS, size=0.5, psize=0.0)

    pause(msg="""..

SaveLoad example
----------------
First we have created some geometry:

F: Formex: a cylinder of rectangular panels colored by its prop='range'
M: Mesh: a square plate with circular hole, colored from a Field being the
   3D-distance from a point (the center of the black zone). This object is
   drawn without lighting (set in the attrib dict).
T: TriSurface: a surface representing a man, colored in gold, standing
   inside the cylinder.

You can now change the camera settings like you wish.
When you hit the PLAY button, we will ask you for a .pzf filename to save the
model to.
""")

    if checkWorkdir():
        indir = pf.cfg['workdir']
    else:
        tmpdir = utils.TempDir()
        indir = tmpdir.path
    fn = askNewFilename(indir / 'saveload.pzf', 'pzf')
    if not fn:
        return

    pzf = PzfFile(fn)
    pzf.save(F=F, M=M, T=T, spiral=PL, CS=CS, curve=C, X=X, _canvas=True)
    clear()
    F = M = T = PL = CS = C = X = None
    print("Archive contents:")
    print(pzf.files())
    pause(msg="""
Now we have saved the whole model in PZF format and
erased it from the screen and from memory.
When you hit the PLAY button, we will reload the model
from the saved file, and display it again.
""")

    d = pzf.load()
    # Set the camera/canvas as stored in the file
    if '_camera' in d:
        pf.canvas.initCamera(d['_camera'])
        pf.canvas.update()
    elif '_canvas' in d:
        pf.GUI.viewports.loadConfig(d['_canvas'])
    print("Loaded %s objects" % len(d))
    drawn = draw(d.values())
    print("Drawn %s objects" % len(drawn))
    print(pzf.objects())
    # currently, CoordSys can not be drawn directly
    drawAxes(d['CS'], size=0.5, psize=0.0)


if __name__ == '__draw__':
    run()

# End
