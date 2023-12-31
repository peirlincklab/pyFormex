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

"""OpenGL camera handling

Part of the Python OpenGL framework for pyFormex
"""
import numpy as np

from pyformex import arraytools as at
from pyformex import utils
from pyformex.coords import Coords
from pyformex.coordsys import CoordSys
from pyformex.plugins.nurbs import Coords4

from .matrix import Matrix4
from . import gl

#
# Normalize and denormalize should probably be moved to arraytools.
#

def normalize(x, w):
    """Normalize coordinates inside a window.

    Parameters
    ----------
    x: :term:`array_like`
        An (np,nc) array with coordinates.
    w: :term:`array_like`
        A (2,nc) array with minimal coordinates and width of the window
        that will be mapped on the range -1..1.

    Returns
    -------
    array:
        The (np, nc) normalized coordinates. The input values are linearly
        remapped thus that w[0] maps onto [-1]*nc and w[0]+w[1] maps onto
        [+1]*nc.

    See Also
    --------
    denormalize: the inverse transformation

    Examples
    --------
    >>> normalize([(2,4), (4,7), (6,10)], [(2,4), (4,6)])
    array([[-1., -1.],
           [ 0.,  0.],
           [ 1.,  1.]])
    """
    x = at.checkArray(x, (-1, -1), 'f', 'i')
    np, nc = x.shape
    w = at.checkArray(w, (2, nc), 'f', 'i')
    return (x-w[0]) * 2 / w[1] - 1


def denormalize(x, w):
    """Map normalized coordinates to fit a window

    Parameters
    ----------
    x: :term:`array_like`
        An (np,nc) array with normalized coordinates.
    w: :term:`array_like`
        A (2,nc) array with minimal coordinates and width of the window
        that will be mapped on the range -1..1.

    Returns
    -------
    array:
        The (np, nc) normalized coordinates. The input values are linearly
        remapped thus that values -1 become w[0] and values +1 become
        w[0]+w[1].

    See Also
    --------
    normalize: the inverse transformation

    Examples
    --------
    >>> denormalize([(-1,-1), (0,0), (1,1)], [(2,4), (4,6)])
    array([[ 2.,  4.],
           [ 4.,  7.],
           [ 6., 10.]])
    """
    x = at.checkArray(x, (-1, -1), 'f', 'i')
    np, nc = x.shape
    w = at.checkArray(w, (2, nc), 'f', 'i')
    return w[0] + (1+x) * w[1] / 2


def perspective_matrix(left, right, bottom, top, near, far):
    """Create a perspective Projection matrix.

    """
    m = Matrix4()
    m[0, 0] = 2 * near / (right-left)
    m[1, 1] = 2 * near / (top-bottom)
    m[2, 0] = (right+left) / (right-left)
    m[2, 1] = (top+bottom) / (top-bottom)
    m[2, 2] = - (far+near) / (far-near)
    m[2, 3] = -1.
    m[3, 2] = -2 * near * far / (far-near)
    m[3, 3] = 0.
    return m


def orthogonal_matrix(left, right, bottom, top, near, far):
    """Create an orthogonal Projection matrix.

    """
    m = Matrix4()
    m[0, 0] = 2 / (right-left)
    m[1, 1] = 2 / (top-bottom)
    m[2, 2] = -2 / (far-near)
    m[3, 0] = - (right+left) / (right-left)
    m[3, 1] = - (top+bottom) / (top-bottom)
    m[3, 2] = - (far+near) / (far-near)
    return m


def pick_matrix(x, y, w, h, viewport):
    """Create a pick Projection matrix

    """
    m = Matrix4()
    m[0, 0] = viewport[2] / w;
    m[1, 1] = viewport[3] / h;
    m[3, 0] = (viewport[2] + 2.0 * (viewport[0] - x)) / w;
    m[3, 1] = (viewport[3] + 2.0 * (viewport[1] - y)) / h;
    return m


@utils.pzf_register
class Camera():
    """A camera for 3D model rendering.

    The Camera class holds all the camera parameters related to the
    rendering of a 3D scene onto a 2D canvas. These includes parameters
    related to camera position and orientation, as well as lens related
    parameters (opening angle, front and back clipping planes).
    The class provides the required matrices to transform the 3D world
    coordinates to 2D canvas coordinates, as well as a wealth of methods
    to change the camera settings in a convenient way so as to simulate
    smooth camera manipulation.

    The basic theory of camera handling and 3D rendering can be found in
    a lot of places on the internet, especially in OpenGL related places.
    However, while the pyFormex rendering engine is based on OpenGL,
    the way it stores and handles the camera parameters is more sophisticated
    than what is usually found in popular tutorials on OpenGL rendering.
    Therefore we give here a extensive description of how the pyFormex
    camera handling and 3D to 2D coordinate transformation works.

    .. note: The remainder below is obsolete and needs to be rewritten.

    Camera position and orientation:

        The camera viewing line is defined by two points: the position of
        the camera and the center of the scene the camera is looking at.
        We use the center of the scene as the origin of a local coordinate
        system to define the camera position. For convenience, this could be
        stored in spherical coordinates, as a distance value and two angles:
        longitude and latitude. Furthermore, the camera can also rotate around
        its viewing line. We can define this by a third angle, the twist.
        From these four values, the needed translation vector and rotation
        matrix for the scene rendering may be calculated.

        Inversely however, we can not compute a unique set of angles from
        a given rotation matrix (this is known as 'gimball lock').
        As a result, continuous (smooth) camera rotation by e.g. mouse control
        requires that the camera orientation be stored as the full rotation
        matrix, rather than as three angles. Therefore we store the camera
        position and orientation as follows:

        - `ctr`: `[ x,y,z ]` : the reference point of the camera:
          this is always a point on the viewing axis. Usually, it is set to
          the center of the scene you are looking at.
        - `dist`: distance of the camera to the reference point.
        - `rot`: a 3x3 rotation matrix, rotating the global coordinate system
          thus that the z-direction is oriented from center to camera.

        These values have influence on the Modelview matrix.

    Camera lens settings:

        The lens parameters define the volume that is seen by the camera.
        It is described by the following parameters:

        - `fovy`: the vertical lens opening angle (Field Of View Y),
        - `aspect`: the aspect ratio (width/height) of the lens. The product
          `fovy * aspect` is the horizontal field of view.
        - `near, far`: the position of the front and back clipping planes.
          They are given as distances from the camera and should both be
          strictly positive. Anything that is closer to the camera than
          the `near` plane or further away than the `far` plane, will not be
          shown on the canvas.

        Camera methods that change these values will not directly change
        the Modelview matrix. The :meth:`loadModelview` method has to be called
        explicitely to make the settings active.

        These values have influence on the Projection matrix.

    Methods that change the camera position, orientation or lens parameters
    will not directly change the related Modelview or Projection matrix.
    They will just flag a change in the camera settings. The changes are
    only activated by a call to the :meth:`loadModelview` or
    :meth:`loadProjection` method, which will test the flags to see whether
    the corresponding matrix needs a rebuild.

    The default camera is at distance 1.0 of the center point [0.,0.,0.] and
    looking in the -z direction.
    Near and far clipping planes are by default set to 0.1, resp 10 times
    the camera distance.

    Properties:

    - `modelview`: Matrix4: the OpenGL Modelview transformation matrix
    - `projection`: Matrix4: the OpenGL Projection transformation matrix

    """

    # DEVELOPERS:
    #    The camera class assumes that matrixmode is always Modelview on entry.
    #    For operations in other modes, an explicit switch before the operations
    #    and afterwards back to Modelview should be performed.

# With a traditional camera, there were two ways to zoom in (move the object closer to the viewer):
# - bring the camera closer to the object (Camera.dolly)
# - change the focal distance of the lens (Camera.zoom)
# Likewise, there were two ways to pan left (move the object left as seen by the viewer):
# - move the camera to the right (Camera.truck)
# - rotate the camera to the right (Camera.pan)

# All these function change the perspective of the view.

# With a digital camera, there is another way of doing it. Since the image is captured on a sensor and stored in memory, it can be transformed before showing it to the viewer.
# Thus, we can zoom in by:
# - mapping a smaller image area to the viewport (Camera.zoomArea)
# and we can pan left by
# - moving the viewport to the on the image (Camera.transArea)

# These functions do not change the image, only the part that is shown to the user.

# When I implemented the *Area functions, I found that I found that the digital zoom and pan is precisely what one wants in most cases. I use zoom in/out mostly to enlarge the image or to fit more on the viewport.
# And I pan usually to move (some part of) the image more centrally on the sceen. But I agree that the classical zoom/pan functions may occasionally be more appropriate and should work also.

# For zoom, this the case (these are default settings):
# - zooming with mouse wheel does a digital zoom
# - zooming with the -/+ toolbar buttons does a lens zoom.
# - zooming with the right mouse button pressed does a digital zoom when moving horizontally and a lens zoom when moving vertically (You can actually just change the perspective while keeping the object size, by moving the mouse diagonally right-down or left up).

# For pan, this is currently broken (I noticed the 'broken' comment in the Camera source, and some commented out functions). I guess the panning with perspective change was never missed so much, as it took quite some years before someone noticed it. And clearly I forgot about it being broken. But if I have some time left, maybe someday I will fix it.
# Maybe we should do like for zoom: connect the toolbar buttons with camera panning (translate or rotate?) and bind them also to moving the mouse with the middle button pressed plus some modifier keys (CTRL+ALT?). Notice however that with transArea, the image nicely follows the mouse movement. That won't be the case with camera panning.


    def __init__(self, focus=(0., 0., 0.), angles=(0., 0., 0.), dist=1.,
                 fovy=45., aspect=4./3., clip=(0.01, 100.), perspective=True,
                 area=(0., 0., 1., 1.),
                 lockedview=False, lockedlens=False, locked=False,
                 keep_aspect=True, tracking=False,
    ):
        """Create a new camera.

        The default camera is positioned at (0.,0.,1.) looking along the -z
        axis in the direction of the point (0.,0.,0.) and with the upvector
        in the direction of the y-axis.
        """
        self.lockedlens = lockedlens or locked
        self.lockedview = lockedview or locked
        self.focus = focus
        self.dist = dist
        self.keep_aspect = True
        self.tracking = False

        self._modelview = Matrix4()
        self._projection = Matrix4()
        self.p = self.v = None
        self.viewChanged = True
        self.lensChanged = True

        self._perspective = perspective
        self.setAngles(angles)
        self.setLens(fovy, aspect)
        self.setClip(*clip)
        self.area = None
        self.setArea(*area, relative=False)


    def settings(self):
        """Dict with all camera settings

        This dict contains all data that allow save and restore
        of the camera to exactly the same settings (on the same
        size of Canvas).
        """
        return {
            'focus': self.focus.tolist(),
            'angles': self.angles,
            'dist': self.dist,
            'fovy': self.fovy,
            'aspect': self.aspect,
            'clip': (self.near, self.far),
            'area': self.area.ravel().tolist(),
            'perspective': self.perspective,
            'lockedview': self.lockedview,
            'lockedlens': self.lockedlens,
            'tracking': self.tracking,
            'keep_aspect': self.keep_aspect,
            }


    @property
    def modelview(self):
        """Return the current modelview matrix.

        This will recompute the modelview matrix if any camera position
        parameters have changed.
        """
        if self.viewChanged:
            self.setModelview()
        return self._modelview

    @modelview.setter
    def modelview(self, value):
        """Set the modelview matrix to the specified matrix.

        value should be a proper modelview matrix
        """
        self._modelview = Matrix4(value)


    @property
    def projection(self):
        """Return the current projection matrix.

        This will recompute the projection matrix if any camera lens
        parameters have changed.
        """
        if self.lensChanged:
            self.setProjection()
        return self._projection


    @projection.setter
    def projection(self, value):
        """Set the projection matrix to the specified matrix.

        value should be a proper projection matrix
        """
        self._projection = Matrix4(value)


    @property
    def viewport(self):
        """Return the camera viewport.

        This property can not be changed directly.
        It should be changed by resizing the parent canvas.
        """
        return gl.gl_viewport()


    @property
    def focus(self):
        """Return the camera reference point (the focus point)."""
        return self._focus

    @focus.setter
    def focus(self, vector):
        """Set the camera reference point (the focus point).

        The focus is the point the camera is looking at. It is a point on
        the camera's optical axis.

        - `vector`: (3,) float array: the global coordinates of the focus.

        """
        if not self.lockedview:
            self._focus = at.checkArray(vector, (3,), 'f')
            self.viewChanged = True


    @property
    def dist(self):
        """Return the camera distance.

        The camera distance is the distance between the camera eye and
        the camera focus point.
        """
        return self._dist


    @dist.setter
    def dist(self, dist):
        """Set the camera distance.

        - `dist`: a strictly positive float value. Invalid values are
        silently ignored.
        """
        if not self.lockedview:
            if dist > 0.0 and dist != np.inf:
                self._dist = dist
                self.viewChanged = True


    @property
    def perspective(self, on=True):
        """Return the perspecive flag.

        If the perspective flag is True, the camera uses a perspective
        projection. If it is False, the camera uses orthogonal projection.
        """
        return self._perspective


    @perspective.setter
    def perspective(self, flag):
        """Set the perspecive flag.

        - `flag`: bool, the value to set the perspective flag to.

        If changed, this forces the recalculation of the projection matrix.
        """
        if not self.lockedlens:
            if flag != self._perspective:
                self._perspective = bool(flag)
                self.lensChanged = True


    @property
    def rot(self):
        """Return the camera rotation matrix."""
        return self.modelview.rot


    @property
    def angles(self):
        """Return the camera angles.

        Returns a tuple (longitude, latitude, twist) in local camera axes.
        """
        R = self.modelview.rot.T
        R = R[[2, 0, 1]]
        R = R[:, [2, 0, 1]]
        a = [at.Float(angle) for angle in at.cardanAngles(R)]
        return (a[2], -a[1], a[0])


    @property
    def upvector(self):
        """Return the camera up vector"""
        return self.modelview.rot[:, 1].reshape((3,))


    @property
    def axis(self):
        """Return a unit vector along the camera axis.

        The camera axis points from the focus towards the camera.
        """
        # this is the same as: at.normalize(self.eye-self.focus)
        return self.modelview.rot[:, 2].reshape((3,))


    def coordsys(self, origin=None):
        """Return a coordinate system bound to the camera axes.

        The z-axis is the camera axis, the y-axis is the camera upvector,
        The x-axis is the vector product y * z.
        If no origin is specified, it is set to the camera.focus.
        """
        if origin is None:
            origin = self.focus
        cz = self.axis
        cy = self.upvector
        cx = np.cross(cy, cz)
        return CoordSys(rot=[cx, cy, cz], trl=origin)


    def setAngles(self, angles, axes=None):
        """Set the rotation angles.

        Parameters
        ----------
        angles: tuple of floats
            A tuple of three angles (long,lat,twist) in degrees.
            A value None is also accepted, but has no effect.

        axes: if specified, any number of rotations can be applied.
        """
        if not self.lockedview:
            if angles is None:
                return
            if isinstance(angles, str):
                raise ValueError("Invalid value for camera angles: %s" % angles)
                #angles = view_angles.get(angles)
            if axes is None:
                axes = ((0., -1., 0.), (1., 0., 0.), (0., 0., -1.))
            self.setModelview(angles=list(zip(angles, axes))[::-1])


    @property
    def eye(self):
        """Return the position of the camera."""
        return self.toWorld([0., 0., 0.])


    @eye.setter
    def eye(self, eye):
        """Set the position of the camera."""
        return self.lookAt(eye=eye)


    def lock(self, view=True, lens=True):
        """Lock/unlock a camera.

        When a camera is locked, its position and lens parameters can not be
        changed.
        This can e.g. be used in multiple viewports layouts to create fixed
        views from different angles.
        """
        if view is not None:
            self.lockedview = bool(view)
        if lens is not None:
            self.lockedlens = bool(lens)
        #print(f"Camera locks: {self.lockedview}, {self.lockedlens}")

    def unlock(self):
        self.lock(False, False)
        #print(f"Camera locks: {self.lockedview}, {self.lockedlens}")

    def lockview(self, onoff=True):
        self.lock(view=True, lens=None)


    def report(self):
        """Return a report of the current camera settings."""
        return """Camera Settings:
  Eye: %s
  Focus: %s
  Distance: %s
  Angles: %s
  Axis: %s
  UpVector: %s
  Rotation Matrix:
  %s
  Field of View y: %s
  Aspect Ratio: %s
  Area: %s, %s
  Near/Far Clip: %s, %s
""" % (self.eye, self.focus, self.dist, self.angles, self.axis, self.upvector, self.rot, self.fovy, self.aspect, self.area[0], self.area[1], self.near, self.far)


    def dolly(self, val):
        """Move the camera eye towards/away from the scene center.

        This has the effect of zooming. A value > 1 zooms out,
        a value < 1 zooms in. The resulting enlargement of the view
        will approximately be 1/val.
        A zero value will move the camera to the center of the scene.
        The front and back clipping planes may need adjustment after
        a dolly operation.
        """
        if not self.lockedview:
            self.dist *= val
            self.viewChanged = True


    # TODO: This is broken!
    def pan(self, val, axis=0):
        """Rotate the camera around axis through its eye.

        The camera is rotated around an axis through the eye point.
        For axes 0 and 1, this will move the focus, creating a panning
        effect. The default axis is parallel to the y-axis, resulting in
        horizontal panning. For vertical panning (axis=1) a convenience
        alias tilt is created.
        For axis = 2 the operation is equivalent to the rotate operation.
        """
        if not self.lockedview:
            if axis==0 or axis ==1:
                pos = self.eye
                self.eye[axis] = (self.eye[axis] + val) % 360
                print(self.report())
                self.focus = diff(pos, sphericalToCartesian(self.eye))
                print(self.report())
            elif axis==2:
                print(self.report())
                self.twist = (self.twist + val) % 360
            self.viewChanged = True


    # TODO: THis depends on the broken pan!
    def tilt(self, val):
        """Rotate the camera up/down around its own horizontal axis.

        The camera is rotated around and perpendicular to the plane of the
        y-axis and the viewing axis. This has the effect of a vertical pan.
        A positive value tilts the camera up, shifting the scene down.
        The value is specified in degrees.
        """
        if not self.lockedview:
            self.pan(val, 1)
            self.viewChanged = True


    def move(self, dx, dy, dz):
        """Move the camera over translation (dx,dy,dz) in global coordinates.

        The focus of the camera is moved over the specified translation
        vector. This has the effect of moving the scene in opposite direction.
        """
        if not self.lockedview:
            #x, y, z = self.ctr
            print(f"MOVING CAMERA OVER {dx}, {dy}, {dz}")
            self.focus += [dx, dy, dz]
            self.viewChanged = True

##    def truck(self,dx,dy,dz):
##        """Move the camera translation vector in local coordinates.

##        This has the effect of moving the scene in opposite direction.
##        Positive coordinates mean:
##          first  coordinate : truck right,
##          second coordinate : pedestal up,
##          third  coordinate : dolly out.
##        """
##        #pos = self.eye
##        ang = self.getAngles()
##        tr = [dx,dy,dz]
##        for i in [1,0,2]:
##            r = rotationMatrix(i,ang[i])
##            tr = multiply(tr, r)
##        self.move(*tr)
##        self.viewChanged = True


    # TODO
    def translate(self, vx, vy, vz, local=True):
        if not self.lockedview:
            print(f"TRANSLATE CAMERA OVER {vx}, {vy}, {vz}")
            if local:
                vx, vy, vz = self.toWorld([vx, vy, vz])
            self.move(-vx, -vy, -vz)


    def setLens(self, fovy=None, aspect=None):
        """Set the field of view of the camera.

        We set the field of view by the vertical opening angle fovy
        and the aspect ratio (width/height) of the viewing volume.
        A parameter that is not specified is left unchanged.
        """
        if fovy:
            self.fovy = min(abs(fovy), 180)
        if aspect:
            self.aspect = abs(aspect)
        self.lensChanged = True


    def resetArea(self):
        """Set maximal camera area.

        Resets the camera window area to its maximum values corresponding
        to the fovy setting, symmetrical about the camera axes.
        """
        self.setArea(0., 0., 1., 1., False)


    def setArea(self, hmin, vmin, hmax, vmax, relative=True, focus=False, center=False, clip=True):
        """Set the viewable area of the camera.

        Note: Use relative=False and clip=False if you want to set the zoom
        exactly as in previously recorded values.
        """
        area = np.array([hmin, vmin, hmax, vmax])
        if clip:
            area = area.clip(0., 1.)
        if area[0] < area[2] and area[1] < area[3]:
            area = area.reshape(2, 2)
            mean = (area[1]+area[0]) * 0.5
            diff = (area[1]-area[0]) * 0.5

            if relative:
                if self.keep_aspect:
                    aspect = diff[0] / diff[1]
                    if aspect > 1.0:
                        diff[1] = diff[0]  # / self.aspect
                        # no aspect factor: this is relative!!!
                    else:
                        diff[0] = diff[1]  # * self.aspect
                if focus:
                    mean = np.zeros(2)
                area[0] = mean-diff
                area[1] = mean+diff
                #print("RELATIVE AREA %s" % (area))
                area = (1.-area) * self.area[0] + area * self.area[1]

            if center:
                # make center of area equal to 0.5,0.5
                mean = (area[1]+area[0]) * 0.5
                area += 0.5-mean

            #print("OLD ZOOM AREA %s (aspect %s)" % (self.area,self.aspect))
            #print("NEW ZOOM AREA %s" % (area))

            self.area = area
            self.lensChanged = True



    def zoomArea(self, val=0.5, area=None):
        """Zoom in/out by shrinking/enlarging the camera view area.

        The zoom factor is relative to the current setting.
        Values smaller than 1.0 zoom in, larger values zoom out.
        """
        if val>0:
            #val = (1.-val) * 0.5
            #self.setArea(val,val,1.-val,1.-val,focus=focus)
            if area is None:
                area = self.area
            #print("ZOOM AREA %s (%s)" % (area.tolist(),val))
            mean = (area[1]+area[0]) * 0.5
            diff = (area[1]-area[0]) * 0.5 * val
            area[0] = mean-diff
            area[1] = mean+diff
            self.area = area
            #print("CAMERA AREA %s" % self.area.tolist())
            self.lensChanged = True


    def transArea(self, dx, dy):
        """Pan by moving the camera area.

        dx and dy are relative movements in fractions of the
        current area size.
        """
        #print("TRANSAREA %s,%s" % (dx,dy))
        area = self.area
        diff = (area[1]-area[0]) * np.array([dx, dy])
        area += diff
        self.area = area
        self.lensChanged = True


    def setClip(self, near, far):
        """Set the near and far clipping planes"""
        if near > 0 and near < far:
            self.near, self.far = near, far
            self.lensChanged = True
        else:
            print("Error: Invalid Near/Far clipping values")


    ## def setClipRel(self,near,far):
    ##     """Set the near and far clipping planes"""
    ##     if near > 0 and near < far:
    ##         self.near,self.far = near,far
    ##         self.lensChanged = True
    ##     else:
    ##         print("Error: Invalid Near/Far clipping values")


    ## def zoom(self,val=0.5):
    ##     """Zoom in/out by shrinking/enlarging the camera view angle.

    ##     The zoom factor is relative to the current setting.
    ##     Use setFovy() to specify an absolute setting.
    ##     """
    ##     if val>0:
    ##         self.fovy *= val
    ##     self.lensChanged = True


    #### global manipulation ###################


    def setTracking(self, onoff=True):
        """Enable/disable coordinate tracking using the camera"""
        if onoff:
            self.tracking = True
            #self.set3Datrices()
        else:
            self.tracking = False


#################################################################
##  Operations on modelview matrix  ##


    def setProjection(self):
        """Set the projection matrix.

        This computes and sets the camera's projection matrix, depending
        on the current camera settings. The projection can either be
        an orthogonal or a perspective one.

        The computed matrix is saved as the camera's projection matrix,
        and the lensChanged attribute is set to False.

        The matrix can be retrieved from the projection attribute,
        and can be loaded in the GL context with loadProjection().

        This function does nothing if the camera is locked.
        """
        if self.lockedlens:
            return

        fv = at.tand(self.fovy*0.5)
        if self._perspective:
            fv *= self.near
        else:
            fv *= self.dist
        fh = fv * self.aspect
        x0, x1 = 2*self.area - 1.0
        frustum = (fh*x0[0], fh*x1[0], fv*x0[1], fv*x1[1], self.near, self.far)
        if self._perspective:
            func = perspective_matrix
        else:
            func = orthogonal_matrix
        self.projection = func(*frustum)

        try:
            self.projection_callback(self)
        except Exception:
            pass
        self.lensChanged = False


    def loadProjection(self):
        """Load the Projection matrix.

        If lens parameters of the camera have been changed, the current
        Projection matrix is rebuild.
        Then, the current Projection matrix of the camera is loaded into the
        OpenGL engine.
        """
        gl.gl_loadprojection(self.projection.gl())



    def pickMatrix(self, rect, viewport=None):
        """Return a picking matrix.

        The picking matrix confines the scope of the normalized device
        coordinates to a rectangular subregion of the camera viewport.
        This means that values in the range -1 to +1 are inside the
        rectangle.

        Parameters:

        - `rect`: a tuple of 4 floats (x,y,w,h) defining the picking region
          center (x,y) and size (w,h)
        - `viewport`: a tuple of 4 int values (xmin,ymin,xmax,ymax) defining
          the size of the viewport. This is normally left unspecified and
          set to the camera viewport.
        """
        if viewport is None:
            viewport = self.viewport
        return pick_matrix(rect[0], rect[1], rect[2], rect[3], viewport)


    def eyeToClip(self, x):
        """Transform a vertex from eye to clip coordinates.

        This transforms the vertex using the current Projection matrix.

        It is equivalent with multiplying the homogeneous
        coordinates with the Projection matrix, but is done here
        in an optimized way.
        """
        return self.projection.transform(x)


    def clipToEye(self, x):
        """Transform a vertex from clip to eye coordinates.

        This transforms the vertex using the inverse of the
        current Projection matrix.

        It is equivalent with multiplying the homogeneous
        coordinates with the inverse Projection matrix, but is done
        here in an optimized way.
        """
        return self.projection.invtransform(x)


#################################################################
##  Operations on modelview matrix  ##


    def lookAt(self, focus=None, eye=None, up=None):
        """Set the Modelview matrix to look at the specified focus point.

        The Modelview matrix is set with the camera positioned at eye
        and looking at the focus points, while the camera up vector is
        in the plane of the camera axis (focus-eye) and the specified
        up vector.

        If any of the arguments is left unspecified, the current value
        will be used.
        """
        if self.lockedview or self.lockedlens:
            return

        if focus is None:
            focus = self.focus
        else:
            focus = at.checkArray(focus, (3,), 'f')
        if eye is None:
            eye = self.eye
        else:
            eye = at.checkArray(eye, (3,), 'f')
        if up is None:
            up = self.upvector
        else:
            up = at.normalize(at.checkArray(up, (3,), 'f'))
        vector = eye-focus
        self.focus = focus
        self.dist = at.length(vector)
        axis2 = at.normalize(vector)
        axis0 = at.normalize(np.cross(up, axis2))
        axis1 = at.normalize(np.cross(axis2, axis0))
        m = Matrix4()
        m.rotate(np.column_stack([axis0, axis1, axis2]))
        m.translate(-eye)
        self.setModelview(m)


    def rotate(self, val, vx, vy, vz):
        """Rotate the camera around current camera axes."""
        if not self.lockedview:
            rot = self._modelview.rot
            m = Matrix4()
            m.translate([0, 0, -self.dist])
            m.rotate(val % 360, [vx, vy, vz])
            m.rotate(rot)
            m.translate(-self.focus)
            self.setModelview(m)


    def setModelview(self, m=None, angles=None):
        """Set the Modelview matrix.

        The Modelview matrix can be set from one of the following sources:

        - if `mat` is specified, it is a 4x4 matrix with a valuable
          Modelview transformation. It will be set as the current camera
          Modelview matrix.

        - else, if `angles` is specified, it is a sequence of tuples
          (angle, axis) each of which define a rotation of the camera
          around an axis through the focus point.
          The camera Modelview matrix is set from the current camera focus,
          the current camera distance, and the specified angles/axes.
          This option is typically used to change the viewing direction
          of the camera, while keeping the focus point and camera distance.

        - else, if the viewChanged flags is set, the camera Modelview
          matrix is set from the current camera focus, the current camera
          distance, and the current camera rotation matrix.
          This option is typically used after changing the camera focus
          point and/or distance, while keeping the current viewing angles.

        - else, the current Modelview matrix remains unchanged.

        In all cases, if a modelview callback was set, it is called,
        and the viewChanged flag is cleared.
        """
        if self.lockedview:
            return

        if m is None and angles is not None:
            m = Matrix4()
            m.translate([0, 0, -self.dist])
            #print(list(angles))
            for angle, axis in angles:
                m.rotate(angle, axis)
            m.translate(-self.focus)
        elif m is None and self.viewChanged:
            m = Matrix4()
            m.translate([0, 0, -self.dist])
            m.rotate(self._modelview.rot)
            m.translate(-self.focus)

        if m is not None:
            self.modelview = m

        try:
            self.modelview_callback(self)
        except Exception:
            pass
        self.viewChanged = False


    def loadModelview(self):
        """Load the Modelview matrix.

        If camera positioning parameters have been changed, the current
        Modelview matrix is rebuild.
        Then, the current Modelview matrix of the camera is loaded into the
        OpenGL engine.
        """
        gl.gl_loadmodelview(self.modelview.gl())


    def toEye(self, x):
        """Transform a vertex from world to eye coordinates.

        This transforms the vertex using the current Modelview matrix.

        It is equivalent with multiplying the homogeneous
        coordinates with the Modelview matrix, but is done here
        in an optimized way.
        """
        x = at.checkArray(x, (-1, 3), 'f')
        return np.dot(x, self.modelview[:3, :3]) + self.modelview[3, :3]


    def toWorld(self, x):
        """Transform a vertex from eye to world coordinates.

        This transforms the vertex using the inverse of the
        current Modelview matrix.

        It is equivalent with multiplying the homogeneous
        coordinates with the inverse Modelview matrix, but is done
        here in an optimized way.
        """
        x = at.checkArray(x, (3,), 'f') + [0., 0., self.dist]
        return x @ self.rot.T + self.focus


#################################################################
##  Transform vertices with modelview and projection matrix  ##


    def toWindow(self, x):
        """Convert normalized device coordinates to window coordinates"""
        # This is only correct when glDepthRange(0.0, 1.0)
        # We should not change the depth range
        vp = gl.gl_viewport()
        #print([[vp[0], vp[1], 0], [vp[2], vp[3], 1]])
        return denormalize(x[:, :3], [[vp[0], vp[1], 0], [vp[2], vp[3], 1]])


    def fromWindow(self, x):
        """Convert window coordinates to  normalized device coordinates"""
        # This is only correct when glDepthRange(0.0, 1.0)
        # We should not change the depth range
        vp = gl.gl_viewport()
        x = at.checkArray(x, (-1, 3), 'f')
        return normalize(x[:, :3], [[vp[0], vp[1], 0], [vp[2], vp[3], 1]])


    def toNDC(self, x, rect=None):
        """Convert world coordinates to normalized device coordinates.

        The normalized device coordinates (NDC) have x and y values
        in the range -1 to +1 for points that are falling within the
        visible region of the camera.

        Parameters:

        - `x`: Coords with the world coordinates to be converted
        - `rect`: optional, a tuple of 4 values (x,y,w,h) specifying
          a rectangular subregion of the camera's viewport. The default
          is the full camera viewport.

        The return value is a Coords. The z-coordinate provides
        depth information.
        """
        m = np.dot(self.modelview, self.projection)
        if rect is not None:
            m = np.dot(m, self.pickMatrix(rect))
        x = Coords4(x)
        x = Coords4(np.dot(x, m))
        if self._perspective:
            x = x.toCoords()  # This performs the perspective divide
        else:
            # Orthogonal projection
            # This is not tested yet!!!
            x = Coords(x[..., :3])
        return x


    def toNDC1(self, x, rect=None):
        """This is like toNDC without the perspective divide

        This function is useful to compute the vertex position of a
        3D point as computed by the vertex shader.

        """
        m = np.dot(self.modelview, self.projection)
        if rect is not None:
            m = np.dot(m, self.pickMatrix(rect))
        x = Coords4(x)
        x = Coords4(np.dot(x, m))
        x = Coords(x[..., :3])
        return x


    def project(self, x):
        """Map the world coordinates (x,y,z) to window coordinates."""
        # Modelview transform
        e = Coords4(x).reshape(-1,4) @ self.modelview
        #print("EYE COORDINATES:",e)
        w = -e[:, 2]
        # Projection
        x = e @ self.projection
        #print("CLIP COORDINATES:",x)
        # Perspective division
        if self._perspective:
            ## if (w == 0.0):
            ##     return [np.inf,np.inf,np.inf]
            x = x/w
        #print("NORMALIZED DEVICE COORDINATES:",x)
        # Map to window
        return self.toWindow(x).reshape(-1, 3)


    def unproject(self, x, ndc=False):
        """Map the window coordinates x to object coordinates."""
        m = self.modelview @ self.projection
        #print("M*P",m)
        m1 = np.linalg.inv(m)
        #print("M*P -1",m1)
        x = self.fromWindow(Coords(x).reshape(-1,3))
        #print("NORMALIZED DEVICE COORDINATES:",x)
        X = (Coords4(x) @ m1).toCoords()
        if ndc:
            return X, x
        else:
            return X


    def inside(self, x, rect=None, return_depth=False):
        """Test if points are visible in the camera.

        Parameters
        ----------
        x: :term:`array_like`
            Array (npts, 3) with coordinates of 3D points.
        rect: tuple, optional
            A tuple of 4 values (x,y,w,h) specifying a rectangular subregion
            of the camera's viewport. Default is the full camera viewport.
        return_depth: bool
            If True, also returns the the z-depth of the points.

        Returns
        -------
        inside: bool array
            An array with value 1 (True) for the points that
            are projected inside the rectangular area of the camera.
        depth: float array (npts,)
            The z-depth value of the points. Only returned if
            `return_depth` is True.
        """
        ndc = self.toNDC(x, rect)
        xy = ndc[:, :2]
        inside = (xy >= -1).all(axis=-1) * (xy <= 1).all(axis=-1)
        if return_depth:
            return inside, ndc[:, 2]
        else:
            return inside


    def loadConfig(self, config):
        """Load the camera settings from a dict"""
        from pyformex.gui import toolbar
        self.__init__(**config)
        # Since this might have changed the perspective state
        # of the current camera, updat the gui perspective button
        toolbar.updatePerspectiveButton()


    ###################
    ## PZF interface ##

    def pzf_dict(self):
        return { 'kargs:p': self.settings() }


    ## DEPRECATED ##

    # Deprecated old camera saving format   2023-01
    # TODO: remove after 2023-08
    @utils.deprecated('camera_save')
    def save(self, filename):
        """Save the camera settings to file"""
        from pyformex.pzffile import dict2str
        with open(filename, 'w') as fil:
             fil.write("#Camera settings saved from pyFormex\n" +
                       dict2str(self.settings(), 'c') + "\n#End\n")


    @utils.deprecated('camera_save')
    def load(self, filename):
        """Load the camera settings from file"""
        from pyformex.pzffile import str2dict
        with open(filename, 'r') as fil:
             config = fil.read()
        self.loadConfig(str2dict(config, 'c'))

# End
