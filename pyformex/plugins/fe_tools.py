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
"""Utility functions for finite elements applications

This module contains some functions, data and classes for assist
finite element modelling.
You need to import this module in your scripts to have access to its
contents.
"""


from pyformex.arraytools import checkArray
import numpy as np


# Note: this could be combined with convertUnits function from
# plugins.units to do things like this:
#
#  mat = IsotropicElasticity(E='21GPa',K='7000kN/cm**2')
#  mat.E('Mpa')  # would give value in MPa
#
class IsotropicElasticity():
    """Material constants for an isotropic linear elastic material.

       Exactly 2 out of the following need to be specified:

       E, G, nu, K, lmbda, mu, D
    """

    def __init__(self, E=None, G=None, nu=None, K=None, lmbda=None, mu=None,
                 D=None):

        # convert None values to float
        E, G, nu, K, lmbda, mu, D = [float(var) if var is not None else None
                                     for var in (E, G, nu, K, lmbda, mu, D)]

        if G is None and mu is not None:
            G = mu

        if K is None and D is not None:
            K = 2./D

        # Set the young modulus E (checked for combinations with K, lamba, G)
        if K is not None:

            if lmbda is not None:
                E = (9.*K*(K-lmbda))/(3.*K-lmbda)

            if G is not None:
                E=(9.*K*G)/(3.*K+G)

            if nu is not None:
                E = 3.*K*(1.-2.*nu)

        if lmbda is not None:

            if G is not None:
                E = (G* (3.*lmbda + 2.*G))/(lmbda + G)

            if nu is not None:
                E = (lmbda*(1.+nu)*(1-2*nu))/nu

        if G is not None:
            if nu is not None:
                E = 2.*G*(1.+nu)

        # After setting the young modulus E computes G
        # only the few checks below are needed
        if lmbda is not None:
            R = (E**2.+9.*lmbda**2.+2.*E*lmbda)**0.5
            G = (E-3.*lmbda+R)/4.

        if nu is not None:
            G = E / (2*(1+nu))

        if K is not None:
            G = (3.*K*E)/(9*K-E)

        self._E, self._G = E, G


    @property
    def E(self):
        return self._E

    @property
    def G(self):
        return self._G

    @property
    def nu(self):
        return self._E / (2*self._G) - 1.0

    @property
    def K(self):
        return self._G * self._E / (3*(3*self._G-self._E))

    @property
    def D(self):
        return 2./self.K

    @property
    def lmbda(self):
        E, G = self._E, self._G
        return G*(E-2*G) / (3*G-E)

    @property
    def mu(self):
        return self._G

    def __str__(self):
        return (f"E={self.E}; G=mu={self.G}; nu={self.nu}; "
                f"K={self.K}; lmbda={self.lmbda}; D={self.D}")


class UniaxialStrain():
    """Uniaxial finite deformation strain measures.

    This class provides a way to store finite deformation strain measures
    and to convert between different strain measure definitions.

    Parameters:

    - `data`: :term:`array_like` float (n,): strain values
    - `type`: one of 'stretch', 'log', 'nominal', 'green', 'almansi'.
      Defines the type of strain measure:

      - 'stretch': stretch (ratio) or extension ratio,
      - 'nominal': nominal or engineering strain,
      - 'log': logarithmic or true strain,
      - 'green': Green strain (values should be >= -0.5),
      - 'almansi': Almansi strain (values should be <= 0.5).

      The default is to interprete the data as nominal strains.

    Internally, the data are stored as stretch values.
    """

    def __init__(self, data, type):
        """Initialize the UniaxialStrain"""

        data = checkArray(data, shape=(-1,), kind='f')
        if type == 'nominal':
            data = data + 1.
        elif type == 'log':
            data = np.exp(data)
        elif type == 'green':
            data = np.sqrt(2*data + 1.)
        elif type == 'almansi':
            data = 1. / np.sqrt(1. - 2*data)
        elif type != 'stretch':
            raise ValueError("Invalid strain type: %s" % type)

        self.data = data


    def stretch(self):
        """Return the strain data as stretch ratios"""
        return self.data

    def log(self):
        """Return the strain data as logarithmic (true) strains"""
        return np.log(self.data)

    def nominal(self):
        """Return the strain data as nominal (engineering) strains"""
        return self.data - 1.

    def green(self):
        """Return the strain data as Green strains"""
        return 0.5 * (self.data * self.data - 1.0)

    def almansi(self):
        """Return the strain data as Almansi strains"""
        return 0.5 * (1. - 1. / (self.data * self.data))


class UniaxialStress():
    """Uniaxial finite deformation stress measures.

    This class provides a way to store finite deformation stress measures
    and to convert between different stress measure definitions.

    Parameters:

    - `data`: :term:`array_like` float (n,): stress values
    - `type`: one of 'cauchy', 'nominal', 'pk2'.
      Defines the type of stress measure:

      - 'cauchy': Cauchy or true stress,
      - 'nominal': nominal, engineering or first Piola-Kirchhoff stress,
      - 'pk2': second Piola-Kirchhoff stress.

      The default is to interprete the data as nominal stresses.

    - `strain`: a :class:`UniaxialStrain` instance of matching size (n,),
      or :term:`array_like` float (n,) with the strain values. In the latter case
      also `straintype` should be specified.
    - `straintype`: if `strain` is specified as a :class:`UniaxialStrain`
      instance, this argument is not used. Else it specifies the strain type
      (see :class:`UniaxialStrain`).

    Internally, the data are stored as Cauchy stress.
    """

    def __init__(self, data, type, strain, straintype=None):
        """Initialize the UniaxialStress"""

        data = checkArray(data, shape=(-1,), kind='f')
        if not isinstance(strain, UniaxialStrain):
            strain = UniaxialStrain(strain, straintype)
        stretch = strain.stretch()
        if type == 'nominal':
            data = data * stretch
        elif type == 'pk2':
            data = data * stretch**2
        elif type != 'cauchy':
            raise ValueError("Invalid stress type: %s" % type)

        self.data = data
        self.strain = strain

    def cauchy(self):
        return self.data

    def nominal(self):
        return self.data / self.strain.stretch()

    def pk2(self):
        return self.data / self.strain.stretch()**2


# maybe move this to the amplitude class?
def smoothAmp(a, n=50):
    """ Compute a single abaqus smooth amplitude.

    Parameters
    ----------
    a: :term:`array_like` (2,2)
        Initial and final (amplitude,time) pairs
    n: int
        Number of intervals for the time variable
    """
    tc = np.linspace(a[0, 0], a[1, 0], n)
    eps = (tc-a[0, 0])/ (a[1, 0]-a[0, 0])
    amp = a[0, 1] + (a[1, 1]-a[0, 1]) * eps**3 * (10.-15.*eps+6.*eps**2.)
    return np.column_stack([tc, amp])


def ampSequence(a, n=100, f=smoothAmp):
    """Compute a final amplitude from a sequence of amplitudes.

    Parameters
    ----------
    a: :term:`array_like` (namp,2)
        Every row is a pair of subsequent (amplitude,time) values
    n: int
        Number of of intervals for the time variable
    f: callable
        Amplitude function
    """
    amp = np.empty((0, 2))
    for i in range(len(a)-1):
        amp = np.concatenate([amp, f(a[i:i+2], n=n)], axis=0)
    return amp


def transverseShear(E, nu, c, type='generalized'):
    """ Compute the shear stiffness for beam and shell element theory

    For homogeneous beams/shells made of a linear, orthotropic elastic material.

    Parameters
    ----------
    E: float (1 or 2)
        Elastic modulus in the one or two directions. If only one given,
        the values in each directions are taken the same.
    nu: float
        Poisson modulus
    c: float
        Characteristic dimension. For beam elements it is the cross-
        sectional area, for shell elements the thickness of the element.
    type: str
        Either 'shell' or one of the allowed beam cross section names as
        defined in abaqus.

    Returns
    -------
    list
        A list of 3 values for the transverse shear.
        For `type` == 'shell':

            - shear stiffness in the 1st direction,
            - shear stiffness in the 2nd direction,
            - coupling term, assumed to be 0.

        In all other cases (beam sections):

            - shear stiffness,
            - shear stiffness,
            - slenderness compensation factor

    See abaqus documentation for meanings and usage.
    """
    k = {
        'arbitrary': 1.0,
        'box': 0.44,
        'circular': 0.89,
        'elbow': 0.85,
        'generalized': 1.0,
        'hexagonal': 0.53,
        'i': 0.44,
        't': 0.44,
        'l': 1.0,
        'meshed': 1.0,
        'nonlinear': 1.0,
        'pipe': 0.53,
        'rectangular': 0.85,
        'thick pipe1': 0.53,
        'thick pipe2': 0.89,
        'trapezoidal': 0.822,
        'shell': 5/6.,
    }

    if np.asarray(E).size == 1:
        E = [E, E]

    sh = []
    for em in E:
        G = IsotropicElasticity(E=em, nu=nu).G
        sh.append(k[type]*c*G)  # Actual transverse shear stiffness

    if type != 'shell':
        # default slenderness compensation factor is only for beam elements
        sh.append(k[type]/(2.*(1.+nu)))
    else:
        sh.append(0.)
    return sh

# End
