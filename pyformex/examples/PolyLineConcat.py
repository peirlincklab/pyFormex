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
"""PolyLineConcat

Example showing the use of the PolyLine concatenate method.

#. The example first creates a list of three PolyLines (identical, but with
   an offset in x-direction. (Top row)
#. The three PolyLines are simply concatenated to a single PolyLine.
   (Second row)
#. The middle of the three PolyLines is reversed (so that it starts at top
   right and ends at bottom left) and the three are concatenated again.
   (Third row)
#. The same three Polylines are concatenated with the `smart=True`
   parameter. Notice how the concatenation has selected the closest point
   for the concatenation. (Last row)
"""


_level = 'beginner'
_topics = ['geometry', 'curve']
_techniques = ['polyline', 'concatenate']

from pyformex.gui.draw import *

def run():
    resetAll()
    clear()

    # 1.
    # Create a PolyLine
    C = Formex('l:15').toCurve()
    # Create a list of three polylines with x-offset
    CL = List([C.trl(0, i*3.) for i in range(3)])
    draw(CL)

    # 2.
    # Use a short name for the PolyLine.concatenate method
    catcrv = C.concatenate
    # Concatenate the PolyLines to a single one
    CL1 = catcrv(CL).trl(1, -2)
    draw(CL1)

    # 3.
    # Reverse the middle curve
    CL[1] = CL[1].reverse()
    # Concatenate again
    CL2 = catcrv(CL).trl(1, -4)
    draw(CL2)

    # 4.
    # Concatenate with `smart=True`
    CL3 = catcrv(CL, smart=True).trl(1, -6)
    draw(CL3)




if __name__ == '__draw__':
    run()
# End
