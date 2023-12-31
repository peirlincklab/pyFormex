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


Postprocessing
==============

The pyFormex rendering machine can be used to render any scalar value
on a given geomatry. Thus pyFormex can also be used as a postprocessor for
numerical simulation codes such as Finite Element Analysis (FEA) or
Computational Fluid Dynamics (CFD).

Distance
--------

This image renders the distance from all points of the
geometry to a single fixed point. The imagewas taken in an alpha version of pyFormex 0.6.1.

.. image:: ../images/postproc.png
   :align: center


FE results
----------

In this image from pyFormex 0.8.1 (alpha) multiple viewports are used
to render some results from FEA simulations. Also shown is the
postprocessing user dialog.


.. image:: ../images/postproc1.png
   :align: center


.. End
