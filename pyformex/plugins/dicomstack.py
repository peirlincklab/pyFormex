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
"""Convert bitmap images into numpy arrays.

This module contains functions to convert bitmap images into numpy
arrays and vice versa. There are functions to read image from file
into arrays, and to save image arrays to files. There is even a class
that reads a full stack of Dicom images into a 3D numpy array.

Some of this code was based on ideas found on the PyQwt mailing list.
"""

import numpy as np


class DicomStack():
    """
    A stack of DICOM images.

    Note
    ----
    This class is only available if you have pydicom installed.


    The DicomStack class stores a collection of DICOM images
    and provides conversion to ndarray.

    The DicomStack is initialized by a list of file names.
    All input files are scanned for DICOM image data and
    non-DICOM files are skipped.
    From the DICOM files, the pixel and slice spacing are read,
    as well as the origin.
    The DICOM files are sorted in order of ascending origin_z value.

    While reading the DICOM files, the following attributes are set:

    - `files`: a list of the valid DICOM files, in order of ascending
      z-value.
    - `pixel_spacing`: a dict with an (x,y) pixel spacing tuple as key
      and a list of indices of the matching images as value.
    - `slice_thickness`: a list of the slice thicknesses of the
      images, in the same order as `files`.
    - `xy_origin`: a dict with an (x,y) position the pixel (0,0) as key
      and a list of indices of the matching images as value.
    - `z_origin`: a list of the z positions of the images,
      in the same order as `files`.
    - `rejected`: list of rejected files.

    """

    class Object():
        """_A dummy object to allow attributes"""
        # pass


    def __init__(self, files, zsort=True, reverse=False):
        """Initialize the DicomStack."""
        # defer import for startup efficiency
        import pydicom

        ok = []
        rejected = []
        for fn in files:
            obj = DicomStack.Object()
            dataset = pydicom.dcmread(fn)
            try:
                obj.fn = fn
                obj.image = dataset.pixel_array
                obj.spacing = dataset.PixelSpacing
                try:
                    obj.spacingz = dataset.SpacingBetweenSlices
                except Exception:
                    obj.spacingz = None
                obj.origin = np.array(dataset.ImagePositionPatient)
                obj.intercept = dataset.RescaleIntercept
                obj.slope = dataset.RescaleSlope
                ok.append(obj)
            except Exception:
                rejected.append(obj)
                raise

        if zsort:
            ok.sort(key=lambda obj: obj.origin[2], reverse=reverse)

        self.ok, self.rejected = ok, rejected



    def nfiles(self):
        """Return the number of accepted files."""
        return len(self.ok)


    def files(self):
        """Return the list of accepted filenames"""
        return [obj.fn for obj in self.ok]


    def rejectedFiles(self):
        """Return the list of rejected filenames"""
        return [obj.fn for obj in self.rejected]


    def pspacing(self):
        """Return the pixel spacing and slice thickness.

        Return the pixel spacing (x,y) and the slice thickness (z)
        in the accepted images.

        Returns: a float array of shape (nfiles,3).
        """
        return np.array([obj.spacing for obj in self.ok])


    def origin(self):
        """Return the origin of all accepted images.

        Return the world position of the pixel (0,0) in all accepted images.

        Returns: a float array of shape (nfiles,3).
        """
        return np.array([obj.origin for obj in self.ok])


    def zvalues(self):
        """Return the zvalue of all accepted images.

        The zvalue is the z value of the origin of the image.

        Returns: a float array of shape (nfiles).
        """
        return np.array([obj.origin[2] for obj in self.ok])


    def zspacing(self):
        """Check for constant slice spacing."""
        zval = self.zvalues()
        zdif = zval[1:] - zval[:-1]
        if np.allclose(zdif, zdif[0]):
            self.spacingz = zdif[0]
        else:
            self.spacingz = None
        return self.spacingz


    def spacing(self):
        """Return uniform spacing parameters, if uniform."""
        pspacing = self.pspacing()
        if np.allclose(pspacing[:, 0], pspacing[0, 0]) and \
           np.allclose(pspacing[:, 1], pspacing[0, 1]):
            self.spacingp = pspacing[0]
            if self.zspacing():
                return np.concatenate([self.spacingp, [self.spacingz]])
        return None


    def image(self, i):
        """Return the image at index i"""
        return self.ok[i].image


    def pixar(self, raw=False):
        """Return the DicomStack as an array

        Returns all images in a single array. This is only successful
        if all accepted images have the same size.
        """
        if raw:
            data = np.dstack([obj.image for obj in self.ok])
        else:
            data = np.dstack([obj.image*obj.slope+obj.intercept
                              for obj in self.ok])
        return data


def dicom2numpy(files):
    """
    Easy conversion of a set of dicom images to a numpy array.

    Parameters
    ----------
    files: list of :term:`path_like`
        List of file names containing the subsequent DICOM images
        in the stack.
        The file names should be in the correct order.

    Returns
    -------
    pixar: int array (nfiles, height, width)
        Pixel array with the nfiles images.
    spacing:

    """
    ds = DicomStack(files)
    return ds.pixar(), ds.spacing()[0]


# End
