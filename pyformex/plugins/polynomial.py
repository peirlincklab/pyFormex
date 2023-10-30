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
#

"""Polynomials

This module defines the class Polynomial, representing a polynomial
in n variables.
"""

import numpy as np
from pyformex import arraytools as at

class Polynomial():
    """A polynomial in `n` dimensions.

    An n-dimensional polynomial is the sum of `nterms` terms, where each
    term is the product of a coefficient (a float constant) and a monomial
    in the `n` variables. A monomial is the product of each of the variables
    raised to a specific exponent. For example, in a 2-dim space, a
    polynomial in (x,y) could be::

        2 + 3 * x - x * y - y**2

    This contains four terms. We store the monomials as an int array with
    shape (nterms, ndim) specifying for each term the exponents of each of
    the variables in the monomial. For the above example this becomes:
    [(0,0), (1,0), (1,1), 0,1)]. The `nterms` coefficients are stored
    as floats: [2.0, 3.0, -1.0, -1.0].

    Parameters
    ----------
    exp: :term:`array_like`
        An int array of shape (nterms,ndim) with the exponents of each of
        the ndim variables in each of the nterms terms of the polynomial.
    coeff: :term:`array_like`
        A float array with the coefficients of the terms.
        If not specified, all coefficients are set to 1.
    symbol:str, optional
        A string of length at least `ndim` with the symbols to be used
        for each of the `ndim` independent variables. The default
        is set for a 3-d polynomial.

    Examples
    --------
    >>> p = Polynomial([(0,0),(1,0),(1,1),(0,2)],(2,3,-1,-1))
    >>> p.exp
    array([[0, 0],
           [1, 0],
           [1, 1],
           [0, 2]])
    >>> p.coeff
    array([ 2.,  3., -1., -1.])
    >>> print(p.atoms())
    ['1', 'x', 'x*y', 'y**2']
    >>> print(p)
    2.0 +3.0*x -1.0*x*y -1.0*y**2
    >>> print(repr(p))
    Polynomial([[0, 0], [1, 0], [1, 1], [0, 2]], [2.0, 3.0, -1.0, -1.0], 'xyz')
    >>> print(Polynomial([(2,0), (1,1), (0,2)], (1,2,1), 'ab'))
    a**2 +2.0*a*b +b**2
    """

    def __init__(self, exp, coeff=None, symbol='xyz'):
        """Create an n-d polynomial"""
        self.exp = at.checkArray(exp, kind='i', ndim=2)
        if coeff is None:
            self.coeff = np.ones(self.nterms)
        else:
            self.coeff = at.checkArray(coeff, (self.nterms,), 'f', 'i')
        if len(symbol) < self.ndim:
            raise ValueError(
                f"Insufficient symbols for {self.ndim}-dim Polynimial")
        self.symbol = symbol


    @property
    def nterms(self):
        return self.exp.shape[0]


    @property
    def ndim(self):
        return self.exp.shape[1]


    def degrees(self):
        """Return the degree of the polynomial in each of the dimensions.

        The degree is the maximal exponent for each of the dimensions.
        """
        return self.exp.max(axis=0)


    def degree(self):
        """Return the total degree of the polynomial.

        The degree is the sum of the degrees for all dimensions.
        """
        return self.degrees().sum()


    def atoms(self):
        """Return a human representation of the monomials

        Returns
        -------
        list of str
            A list of the monomials in the Polynomial

        Examples
        --------
        >>> Polynomial([(0,0),(1,0),(1,1),(0,2)]).atoms()
        ['1', 'x', 'x*y', 'y**2']
        """
        return [monomial(e, self.symbol) for e in self.exp]


    def human(self):
        """Return a human representation

        Returns
        -------
        str:
            A string representation of the Polynomial

        Examples
        --------
        >>> Polynomial([(0,0),(1,0),(1,1),(0,2)]).human()
        '1 +x +x*y +y**2'
        """
        mon = self.atoms()
        mon = [str(c)+'*'+m if c != 1 else m for c, m in zip(self.coeff, mon)]
        return ' +'.join(mon).replace('*1', '').replace('+-', '-')

    __str__ = human

    def __repr__(self):
        return (f"Polynomial({self.exp.tolist()}, {self.coeff.tolist()}, "
                f"{self.symbol!r})")


    def evalAtoms(self, x):
        """Evaluate the monomials at the given points

        Parameters
        ----------
        x: :term:`array_like`
            An (npoints,ndim) array of points where the polynomial is to
            be evaluated.

        Returns
        -------
        array
            The (npoints,nterms) array of values of the `nterms` monomials
            at the `npoints` points.

        Examples
        --------
        >>> p = Polynomial([(0,0),(1,0),(1,1),(0,2)],(2,3,-1,-1))
        >>> p.evalAtoms([[1,2],[3,0],[2,1]])
        array([[1., 1., 2., 4.],
               [1., 3., 0., 0.],
               [1., 2., 2., 1.]])
        """
        x = at.checkArray(x, (-1, self.ndim), 'f', 'i')
        g = dict([(self.symbol[i], x[:, i]) for i in range(self.ndim)])
        atoms = self.atoms()
        aa = np.zeros((len(x), len(atoms)), at.Float)
        for k, a in enumerate(atoms):
            aa[:, k] = eval(a, g)
        return aa


    def eval(self, x):
        """Evaluate the polynomial at the given points

        Parameters
        ----------
        x: :term:`array_like`
            An (npoints,ndim) array of points where the polynomial is to
            be evaluated.

        Returns
        -------
        array
            The value of the polynomial at the `npoints` points.

        Examples
        --------
        >>> p = Polynomial([(0,0),(1,0),(1,1),(0,2)],(2,3,-1,-1))
        >>> print(p.eval([[1,2],[3,0],[2,1]]))
        [-1. 11.  5.]
        """
        terms = self.evalAtoms(x)
        return (self.coeff*terms).sum(axis=-1)


# def polynomial(atoms, x, y=0, z=0):
#     """Build a matrix of functions of coords.

#     - `atoms`: a list of text strings representing a mathematical function of
#       `x`, and possibly of `y` and `z`.
#     - `x`, `y`, `z`: a list of x- (and optionally y-, z-) values at which the
#       `atoms` will be evaluated. The lists should have the same length.

#     Returns a matrix with `nvalues` rows and `natoms` colums.
#     """
#     aa = np.zeros((len(x), len(atoms)), Float)
#     for k, a in enumerate(atoms):
#         aa[:, k] = eval(a)
#     return aa


def factor(sym, exp):
    """Return a string with a variable to some exponent

    Parameters
    ----------
    sum: str
        The name of the variable
    exp: int
        The exponent to which the variable is raised

    Returns
    -------
    str:
        The expression with the variable `sym` raised to the power `exp`.

    Examples
    --------
    >>> factor('x', 3), factor('y', 1), factor('z', 0)
    ('x**3', 'y', '1')
    """
    if exp == 0:
        return '1'
    elif exp == 1:
        return sym
    else:
        return sym+'**'+str(exp)


def monomial(exp, symbol='xyz'):
    """Return the monomial for the given exponents.

    Parameters
    ----------
    exp: tuple of int
        The integer exponents to which to raise the ndim independent variables.
    symbol: str
        A string of at least the same length as `exp`, containing the
        variables to use for each of the ndim independent variables.
        The default is set for a 3-dimensional space.

    Returns
    -------
    str
        A string representation of a monomial created by raising
        the symbols to the corresponding exponent.

    Examples
    --------
    >>> monomial((2,1))
    'x**2*y'
    >>> monomial((0,3,2))
    'y**3*z**2'
    """
    factors = [factor(symbol[i], j) for i, j in enumerate(exp)]
    # Join and sanitize (note we do not have '**1')
    return '*'.join(factors).replace('1*', '').replace('*1', '')

# End
