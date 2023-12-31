..    -*- rst -*-
  
..
  This file is part of the pyFormex project.
  pyFormex is a tool for generating, manipulating and transforming 3D
  geometrical models by sequences of mathematical operations.
  Home page: http://pyformex.org
  Project page:  https://savannah.nongnu.org/projects/pyformex/
  Copyright (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
  Distributed under the GNU General Public License version 3 or later.
  
  
  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.
  
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
  
  You should have received a copy of the GNU General Public License
  along with this program.  If not, see http://www.gnu.org/licenses/.
  
  

.. include:: <isonum.txt>
.. include:: ../defines.inc
.. include:: ../links.inc


Operations on surface meshes
============================
  
Approximating geometry
----------------------

A 3D model of a kinked artery was reconstructed from medical CT
scan images and imported into pyFormex as a triangulated surface. 
The arterial wall surface was then approximated by a
sequence of circles with varying diameters and non collinear center
points. The figure below shows part of the triangulated surface
(yellow), a subset of the approximating circles (blue) and the line
connecting the centers of the circles (red). The view is taken from
inside the artery.

.. image:: ../images/tata-0114.jpg
   :align: center


Stent geometry evaluation
-------------------------

The next figures show four stages in the evaluation of the geometry of
a stent device. The first figure is the imported 3D surface,
reconstructed from CT scan images. In pyFormex, the tubular stent is
unrolled to a planar structure (second figure). This is cut with a
plane, producing the circumference, from which the basic cell is taken
which is shown in the third figure. Finally, the fourth figure shows
the resulting circumference of the opening between the stent
material.

.. image:: ../images/cypher_orig.png
   :align: center
.. image:: ../images/cypher_unroll.png
   :align: center
.. image:: ../images/cypher_unroll_cell.png
   :align: center
.. image:: ../images/cypher_unroll_cell2.png
   :align: center



Human skeleton
--------------

.. _VAKHUM: http://www.ulb.ac.be/project/vakhum
.. _GTS: http://gts.sourceforge.net

The individual bones, reconstructed from CT scans, of the lower human
skeleton were obtained from the VAKHUM_ project. The
original STL files were converted to GTS_ format, coarsened, and read
into pyFormex, where they were aligned to recreate the
skeleton. Colors were added to distinct the bones. 

.. image:: ../images/skelet1.png
   :align: center

.. End
