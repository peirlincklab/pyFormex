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

"""Error and Warning Messages

"""

# flake8: noqa

import pyformex as pf

_message_data = None


def getMessage(msg):
    """Return the real message corresponding with the specified mnemonic.

    If no matching message was defined, the original is returned.
    """
    msg = str(msg)  # allows for msg being a Warning
    msg = globals().get(msg, msg)
    if _message_data is not None:
        msg = msg % _message_data
    return msg

camera_save = "The old format of saving the camera/canvas is deprecated. Use the menus or gui.draw.saveCamera and gui.draw.saveCanvas to save the camera/canvas in the new PZF format. The old format can still be loaded with gui.draw.loadCamera or gui.draw.loadCanvas, but it is recommended to immediately save it again in the new format."
warn_Connectivity_inverse = "The default behavior of Connectivity.inverse has changed. It now returns a Varray by default. To get the old return value (a -1 padded array), you can either add the 'expand=True' parameter or (preferably) explicitely convert the returned Varray:  conn.inverse().toArray()."
warn_coords_match_changed = "The Coords.match function has changed. The argument 'clean' has been removed. The behavior with clean=True can be obtained with the hasMatch method"
warn_curve_approx = "Curve.approx has been changed. It is now an alias for Curve.approximate. To get the same results as with the old ndiv parameter, you can still specify ndiv as a keyword parameter. The old parameter ntot should be replaced with nseg."
warn_curve_approximate = "Curve.approximate now defaults to equidistant=False"
dialog_store_save = "The 'store' facility of a Dialog is now read/write by default: accepted values are written back to the store. This provides for automatic persistence of data between invocations. If you do want this behavior and prefer a read-only store, add the 'save=False' parameter"
warn_drawImage_changed = "The `drawImage` function has changed: it now draws an image in 2D on the canvas. Use `drawImage3D` to get the old behavior of drawing a 3D grid colored like the image."
warn_dualMesh = "TriSurface.dualMesh has changed. It now only returns the Mesh. The nodal areas can be computed easily afterwards with arraytools.binsum(M.areas(), M.prop)"
warn_dxf_export = "Objects of type '%s' can not be exported to DXF file"
warn_dxf_noparser = """..

No dxfparser
------------
I can not import .DXF format on your machine, because I can not find the required external program *dxfparser*.

*dxfparser* comes with pyFormex, so this probably means that it just was not (properly) installed. The pyFormex install manual describes how to do it.
"""

if pf.installtype == 'G':
    warn_dxf_noparser += """
If you are running pyFormex from Git sources and you can have root access, you can go to the directory `...pyformex/extra/dxfparser/` and follow the instructions there, or you can just try the **Install externals** menu option of the **Help** menu.
"""
    warn_exit_all = "exit(all=True) is no longer supported."

warn_fe_abq_write_load = "The output of load properties by the fe_abq interface has been changed: OP=MOD is now the default. This is in line with the Abaqus default and with the output of boundary condition proiperties."
warn_fe_abq_write_section = "The output of materials and section properties by the fe_abq interface has been drastically changed. There are added, removed and changed features. Please check your output carefully, consult the docstrings in the fe_abq functions if needed, and report any malfunctioning."
fixnormals_default = "The default method of fixNormals has been changed from 'admesh' to 'internal'. This method does not include fuse/compact and guarantees that the node/element numbering is retained. You may want to do a fuse/compact prior to calling fixNormals. The 'admesh' method impies it."
warn_flat_removed = "The 'flat=True' parameter of the draw function has been replaced with 'nolight=True'."
warn_formex_eltype = "Formex eltype currently needs to be a string!"
warn_inertia_changed = "The Coords.inertia method has changed: it now returns an inertia.Inertia class instance, with attributes mass, ctr, tensor, and method principal() returning (Iprin,Iaxes)."
warn_inputcombo_onselect = "InputCombo: the use of onselect is deprecated. Use 'func' instead. It receives the InputItem as parameter."
warn_Interaction_changed = "Class fe_abq.Interaction has been changed, only allowed parameters are name, friction, surfacebehavior, surfaceinteraction, extra (see doc)."

warn_mesh_extrude = "Mesh.extrude parameters have changed. The signature is now  extrude(div,dir,length) where length is the total extrusion length."
warn_mesh_connect = "Mesh.connect does no longer automatically compact the Meshes. You may have to use the Mesh.compact method to do so."
mesh_connectedTo = "Mesh.connectedTo has changed! It now returns a list of element numbers instead of a Mesh. Use the select method on the result to extract the corresponding Mesh: Mesh.select(Mesh.connectedTo(...)."
mesh_eltype = "Mesh.setEltype and Mesh.elType are deprecated. You can directly get and set the Mesh.eltype attribute."
warn_mesh_partitionbyangle = "The partitioning may be incorrect due to nonplanar 'quad4' elements"
mesh_reduce_degenerate = "Mesh.reduceDegenerate has changed. It is now an alias for Mesh.splitDegenerate. See the docs."
warn_mesh_reflect = "The Mesh.reflect will now by default reverse the elements after the reflection, since that is what the user will want in most cases. The extra reversal can be skipped by specifying 'reverse=False' in the argument list of the `reflect` operation."

warn_nurbs_curve = "Nurbs curves of degree > 7 can currently not be drawn! You can create some approximation by evaluating the curve at some points."
warn_nurb_surface = "Nurbs surfaces of degree > 7 can currently not be drawn! You can approximate the surface by a lower order surface."
warn_nurbs_gic = "Your point set appears to contain double points. Currently I cannot handle that. I will skip the doubles and try to go ahead."
warn_old_numpy = "BEWARE: OLD VERSION OF NUMPY!!!! We advise you to upgrade NumPy!"
warn_old_project = """..

Old project format
------------------
This is an old format project file. Unless you need to read this project file from an older pyFormex version, we strongly advise you to convert the project file to the latest format. Otherwise future versions of pyFormex might not be able to read it back.
"""
warn_Output_changed = "The fe_abq.Output class has changed! Both the 'variable' and 'keys' arguments have been replaced by the single argument 'vars'. Its value is either 'PRESELECT' or 'ALL' or a list of output keys. See the docstring for more info."
warn_project_compression = "The contents of the file does not appear to be compressed."
warn_properties_setname = "!! 'setname' is deprecated, please use 'name'"

warn_regular_grid = "The function simple.regularGrid has changed!. The points are now ordered first along the 0-axis, then along the 1-axis, etc... This is to be consistent with other grid numbering schemes in pyFormex. The old numbering scheme (first along the highest axis) can be obtained by passing the 'swapaxes=True' argument to the function."
warn_select_changed = "The select and cselect methods have changed for Mesh type opbjects. The default is now compact=False, as suggested in https://savannah.nongnu.org/bugs/?40662#comment7. If you want to get the result compacted, use clip/cclip instead, or add '.compact()'"
warn_radio_enabler = "A 'radio' type input item can currently not be used as an enabler for other input fields."

trisurface_remesh = "TriSurface.remesh now uses the instant-meshes program. If you don't have it, you can install if from the pyformex/extra/instant directory or from the Help menu"

warn_viewport_linking = "Linking viewports is an experimental feature and is not fully functional yet."

error_widgets_enableitem = "Error in a dialog item enabler. This should not happen! Please file a bug report."
warn_writevtp_notclean = "Mesh is not clean: vtk will alter the nodes. To clean: mesh.fuse().compact().renumber()"
warn_writevtp_duplicates = "Mesh contains duplicate elements. This may give problems in VTK / ParaView.\n Duplicates: %s "
warn_writevtp_shape = "The number of array cells should be equal to the number of elements"
warn_writevtp_shape2 = "The number of array points should be equal to the number of points"

depr_abqdata_outres = "The use of the `res` and `out` arguments in AbqData is deprecated. Set them inside your Steps instead."
depr_bezierspline_deriv = "The 'deriv' parameter of BezierSpline is deprecated. Use 'tangents' instead"
depr_cardinalspline = 'CardinalSpline is deprecated. Use BezierSpline with ``curl=(1.-tension)/3.``'
depr_connectedLineElems = "connectivity.connectedLineElems is deprecated. You should use Connectivity.chained or Connectivity.chain instead. Please read the docstring: the arguments and return values are different!"
depr_connectionSteps1 = "connectionSteps is deprecated and has been removed. Use frontWalk instead. See the FrontWalk example: walk 3 gives an equivalent result, though you might prefer the simpler solution of walk 2."
depr_filemode = "The 'exist' and 'multi' parameters of askFilename are deprecated. Use the 'mode' parameter instead."
depr_mesh_getedges = "The Mesh methods getEdges, getElemEdges, getFacesand  getCells are deprecated. You can directly use the Mesh properties edges, elem_edges, faces (and the new elem_faces) and cells instead. They are computed when first time used and stored for later reuse."
depr_naturalspline = "NaturalSpline is deprecated. For a closed curve or an open curve with endzerocurv=True, BezierSpline gives a good approximation. For an open curve with endzerocurv=False, a NurbsCurve obtained with nurbs.globalInterpolationCurve will do fine."
depr_pathextension = "patchextension is deprecated. Use border().extrude() instead."
PolyLine_distanceOfPoints = "PolyLine.distanceOfPoints is deprecated"
PolyLine_distanceOfPolyline = "PolyLine.distanceOfPolyline is deprecated"
VTK_strips = "There are strips in the VTK object (not yet supported in pyFormex). I will convert it to triangles."

# End
