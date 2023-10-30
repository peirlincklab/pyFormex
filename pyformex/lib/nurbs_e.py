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
"""Python equivalents of the functions in lib.nurbs_c

The functions in this module should be exact emulations of the
external functions in the compiled library. Currently however this
module only contains a few of the functions in lib.nurbs_c, making
nurbs functionality in pyFormex currently only available when using
the compiled lib.
"""


# There should be no other imports here but numpy
import numpy as np

# And Set the version from pyformexld be defined
import pyformex
__version__ = pyformex.__version__
_accelerated = False

# Since binomial is already defined in curve, we can just import it here.
from pyformex.curve import binomial   #  this is math.comb


def length(A):
    """Return the length of an ndim vector."""
    return np.linalg.norm(A)


def bernstein(i, n, u):
    """Compute the value of the Bernstein polynomial B(i,n) at u.

    Parameters
    ----------
    i: int
        The index of the polynomial
    n: int
        The degree of the polynomial
    u: float
        The parametric value where the polynomial is evaluated

    Returns
    -------
    float
        The value of the i-th Bernstein polynomials of degree n at parameter
        value u.

    >>> bernstein(2, 5, 0.4)
    0.3456
    """
    # THIS IS NOT OPTIMIZED !
    return allBernstein(n, u)[i]


def allBernstein(n, u):
    """Compute the value of all n-th degree Bernstein polynomials.

    Parameters:

    - `n`: int, degree of the polynomials
    - `u`: float, parametric value where the polynomials are evaluated

    Returns: an (n+1,) shaped float array with the value of all n-th
    degree Bernstein polynomials B(i,n) at parameter value u.

    Algorithm A1.3 from 'The NURBS Book' p20.
    """
    # THIS IS NOT OPTIMIZED FOR PYTHON.
    B = np.zeros(n+1)
    B[0] = 1.0
    u1 = 1.0-u
    for j in range(1, n+1):
        saved = 0.0
        for k in range(j):
            temp = B[k]
            B[k] = saved + u1*temp
            saved = u * temp
        B[j] = saved
    return B


def find_span(U, u, p, n):
    """Find the knot span index of the parametric point u.

    Parameters
    ----------
    U: float array (m+1,)
        The non-descending knot sequence: U[0] .. U[m]
    u: float
        The parametric value U[0] <= u <= U[m] for which to find the span
    p: int
        The degree of the B-spline basis functions
    n: int
        The number of control points - 1 = m - p - 1

    Returns
    -------
    int
       The index of the knot span.

    Notes
    -----
    Algorithm A2.1 from 'The NURBS Book' p.68.
    """
    if u == U[n+1]:  # special case
        return(n)

    # do binary search
    low = p
    high = n + 1
    mid = (low + high) // 2
    cnt = 0
    while u < U[mid] or u >= U[mid+1]:
        if u < U[mid]:
            high = mid
        else:
            low = mid
        mid = (low + high) // 2
        cnt += 1
        if cnt > 20:
            break
    return mid


def basis_funs(U, u, p, i):
    """Compute the nonvanishing B-spline basis functions for index span i.

    Parameters
    ----------
    U: float array (m+1,)
        The knot sequence: U[0] .. U[m], non-descending.
    u: float
        The parametric value U[0] <= u <= U[m] where to compute the functions.
    p: int
        Degree of the B-spline basis functions
    i: int
        Index of the knot span for value u (from find_span())

    Returns
    -------
    float array (p+1)
        The (p+1) values of nonzero basis functions at u.

    Notes
    -----
    Algorithm A2.2 from 'The NURBS Book' p.70.
    """
    N = np.empty((p+1,))  # return array
    left = np.empty((p+1,))  # workspace
    right = np.empty((p+1,))  # workspace

    N[0] = 1.0
    for j in range(1, p+1):
        left[j]  = u - U[i+1-j]
        right[j] = U[i+j] - u
        saved = 0.0
        for r in range(j):
            temp = N[r] / (right[r+1] + left[j-r])
            N[r] = saved + right[r+1] * temp
            saved = left[j-r] * temp
        N[j] = saved
    return N


def basis_derivs(U, u, p, i, n):
    """Compute the nonvanishing B-spline basis functions and derivatives.

    Parameters
    ----------
    U: float array (m+1,)
        The knot sequence: U[0] .. U[m], non-descending.
    u: float
        The parametric value U[0] <= u <= U[m] where to compute the functions.
    p: int
        Degree of the B-spline basis functions
    i: int
        Index of the knot span for value u (from find_span())
    n: int
        Number of derivatives to compute (n <= p)

    Returns
    -------
    float array (n+1, p+1)
        The (n+1, p+1) values of the nonzero basis functions and their first n
        derivatives at u

    Notes
    -----
    Algorithm A2.3 from 'The NURBS Book' p.72.
    """
    dN = np.empty((n+1, p+1))  # return array
    # workspaces
    ndu = np.empty((p+1, p+1))
    a = np.empty((2*(p+1),))
    left = np.empty((p+1,))
    right = np.empty((p+1,))

    ndu[0][0] = 1.0
    for j in range(1, p+1):
        left[j] = u - U[i+1-j]
        right[j] = U[i+j]-u
        saved = 0.0
        for r in range(j):
            # Lower triangle
            ndu[j][r] = right[r+1] + left[j-r]
            temp = ndu[r][j-1]/ndu[j][r]
            # Upper Triangle
            ndu[r][j] = saved + right[r+1]*temp
            saved = left[j-r]*temp
        ndu[j][j] = saved
    # Load the basis functions
    dN[0] = ndu[:,p]

    # Compute the derivatives (Eq. 2.9)
    for r in range(p+1):   # Loop over function index
        s1, s2 = 0, p+1     # Alternate rows in array a
        a[0] = 1.0
        # Loop to compute kth derivative
        for k in range(1, n+1):
            der = 0.0
            rk = r-k;  pk = p-k
            if r >= k:
                a[s2] = a[s1] / ndu[pk+1][rk]
                der = a[s2] * ndu[rk][pk]
            if rk >= -1:
                j1 = 1
            else:
                j1 = -rk
            if r-1 <= pk:
                j2 = k-1
            else:
                j2 = p-r
            for j in range(j1, j2+1):
                a[s2+j] = (a[s1+j] - a[s1+j-1]) / ndu[pk+1][rk+j]
                der += a[s2+j] * ndu[rk+j][pk]
            if r <= pk:
                a[s2+k] = -a[s1+k-1] / ndu[pk+1][r]
                der += a[s2+k] * ndu[r][pk]
            dN[k,r] = der
            s1, s2 = s2, s1  # Switch rows

    # Multiply by the correct factors
    r = p
    for k in range(1, n+1):
        dN[k] *= r
        r *= (p-k)
    return dN


# TODO: def basisFuns
# TODO: def basisDerivs ipv basis_derivs
# TODO: def curvePoints
# TODO: def curveDerivs
# TODO: def curveDecompose
# TODO: def curveKnotRefine
# TODO: def curveKnotRemove

def curveDegreeElevate(Pw, U, t):
    """Elevate the degree of the Nurbs curve.

    Parameters:

    - `Pw`: float array (nk,nd): nk=n+1 control points
    - `U`: int array(nu): nu=m+1 knot values
    - `t`: int: how much to elevate the degree

    Returns a tuple:

    - `Qw`: nh+1 new control points
    - `Uh`: mh+1 new knot values
    - `nh`: highest control point index
    - `mh`: highest knot index

    This is based on algorithm A5.9 from 'The NURBS Book' pg206.

    """
    nk, nd = Pw.shape
    n = nk-1
    m = U.shape[0]-1
    p = m-n-1
    # Workspace for return arrays
    Uh = np.zeros((U.shape[0]*(t+1)))
    Qw = np.zeros((Pw.shape[0]*(t+1), nd))
    # Workspaces
    bezalfs = np.zeros((p+t+1, p+1))
    bpts = np.zeros((p+1, nd))
    ebpts = np.zeros((p+t+1, nd))
    Nextbpts = np.zeros((p-1, nd))
    alfs = np.zeros((p-1,))

    ph = p+t
    ph2 = ph//2

    # Compute Bezier degree elevation coefficients
    bezalfs[0, 0] = bezalfs[ph, p] = 1.0
    for i in range(1, ph2+1):
        inv = 1.0 / binomial(ph, i)
        mpi = min(p, i)
        for j in range(max(0, i-t), mpi+1):
            bezalfs[i, j] = inv * binomial(p, j) * binomial(t, i-j)
    for i in range(ph2+1, ph):
        mpi = min(p, i)
        for j in range(max(0, i-t), mpi+1):
            bezalfs[i, j] = bezalfs[ph-i, p-j]
#    print("bezalfs:",bezalfs)

    mh = ph
    kind = ph+1
    r = -1
    a = p
    b = p+1
    cind = 1
    ua = U[0]
    Qw[0] = Pw[0]
    for i in range(ph+1):
        Uh[i] = ua
    # Initialize first Bezier segment
    for i in range(p+1):
        bpts[i] = Pw[i]
#    print("bpts =\n%s" % bpts[:p+1])

    # Big loop thru knot vector
    while b < m:
#        print("Big loop b = %s < m = %s" % (b,m))
        i = b
        while b < m and U[b] == U[b+1]:
            b += 1;
        mul = b-i+1
        mh += mul+t
        ub = U[b]
        oldr = r
        r = p-mul

        # Insert knot ub r times
        lbz = (oldr+2)//2 if oldr > 0 else 1
        rbz = ph-(r+1)//2 if r > 0 else ph

        if r > 0:
            # Insert knot to get Bezier segment
            numer = ub-ua
            for k in range(p, mul, -1):
                alfs[k-mul-1] = numer / (U[a+k] - ua)
#            print("alfs = %s" % alfs[:p])
            for j in range(1, r+1):
                save = r-j
                s = mul+j
                for k in range(p, s-1, -1):
                    bpts[k] = alfs[k-s]*bpts[k] + (1.0-alfs[k-s])*bpts[k-1]
                Nextbpts[save] = bpts[p]
#                print("Nextbpts %s = %s" %(save,Nextbpts[save]))
#            print("bpts =\n%s" % bpts[:p+1])

        # Degree elevate Bezier
        for i in range(lbz, ph+1):
            # Only points lbz..ph are used below
            ebpts[i] = 0.0
            mpi = min(p, i)
            for j in range(max(0, i-t), mpi+1):
                ebpts[i] += bezalfs[i, j]*bpts[j]
#        print("ebpts =\n%s" % ebpts[lbz:ph+1])

        if oldr > 1:
            # Must remove knot U[a] oldr times
            first = kind-2
            last = kind
            den = ub-ua
            bet = (ub-Uh[kind-1]/den)
            for tr in range(1, oldr):
                # Knot removal loop
                i = first
                j = last
                kj = j-kind+1
                while j-i > tr:
                    # Compute new control points
                    if i < cind:
                        alf = (ub-Uh[i]) / (ua-Uh[i])
                        Qw[i] = alf*Qw[i] + (1.0-alf)*Qw[i-1]
                    if j >= lbz:
                        if j-tr <= kind-ph+oldr:
                            gam = (ub-Uh[j-tr]) / den
                            ebpts[kj] = gam*ebpts[kj] + (1.0-gam)*ebpts[kj+1]
                        else:
                            ebpts[kj] = bet*ebpts[kj] + (1.0-bet)*ebpts[kj+1]
                    i += 1
                    j -= 1
                    kj -= 1
                first -= 1
                last +=1

        if a != p:
            # Load the knot ua
            for i in range(ph-oldr):
                Uh[kind] = ua
                kind += 1

        for j in range(lbz, rbz+1):
            # Load control points into Qw
            Qw[cind] = ebpts[j]
            cind += 1
#        print(Qw[:cind])

#        print("Now b=%s, m=%s" % (b,m))
        if b < m:
            # Set up for next passcthru loop
            for j in range(r):
                bpts[j] = Nextbpts[j]
            for j in range(r, p+1):
                bpts[j] = Pw[b-p+j]
            a = b
            b += 1
            ua = ub
        else:
            # End knot
            for i in range(ph+1):
                Uh[kind+i] = ub

    nh = mh - ph - 1
    Uh = Uh[:mh+1]
    Qw = Qw[:nh+1]

    return np.array(Pw), np.array(Uh), nh, mh


def BezDegreeReduce(Q, return_errfunc=False):
    """Degree reduce a Bezier curve.

    Parameters
    ----------
    Q: float array (nk, nd)
        The control points of a Bezier curve of degree p = nk-1
    return_errfunc: bool
        If True, also returns a function to evaluate the error along
        the parametric values.

    Returns
    -------
    P: float array (nk-1, nd)
        The control points of a Bezier curve of degree p-1 that is as
        close as possible to the original curve.
    maxerr: float
        An upper bound on the error introduced by the degree reduction.
    errfunc: function
        A callable to evaluate the error as function of the parameter u.
        Only returned if return_errfunc is True.

    Notes
    -----
    Based on The NURBS Book 5.6.
    """
    nk, nd = Q.shape
    p = nk - 1
    r = (p-1) // 2
    alfs = np.arange(p) / p
    P = np.zeros((p, nd))
    P[0] = Q[0]
    for i in range(1, r+1):
        P[i] = (Q[i] - alfs[i]*P[i-1]) / (1.0-alfs[i])
    P[p-1] = Q[p]
    for i in range(p-2, r, -1):
        P[i] = (Q[i+1] - (1-alfs[i+1])*P[i+1]) / alfs[i+1]
    if p % 2 == 1:
        PrR = (Q[r+1] - (1-alfs[r+1])*P[r+1]) / alfs[r+1]
        Err = 0.5 * (1.0-alfs[r]) * length(P[r] - PrR)
        P[r] = 0.5 * (P[r] + PrR)
    else:
        Err = length(Q[r+1]-0.5*(P[r]+P[r+1]))

    # Max error
    # Note that maximum of Bernstein polynom (i,p) is at i/p
    if p % 2 == 0:
        errfunc = lambda u: Err * bernstein(r+1, p, u)
        # Note that maximum of Bernstein polynom (i,p) is at i/p
        maxerr = errfunc((r+1.)/p)
    else:
        errfunc = lambda u: Err * abs(bernstein(r, p, u) - bernstein(r+1, p, u))
        # We guess that maximum is close to middle of r/p and r+1/p
        maxerr = max(errfunc(float(r)/p), errfunc(float(r+1)/p))

    if return_errfunc:
        return P, maxerr, errfunc
    else:
        return P, maxerr


#from pyformex.plugins.nurbs import *
def curveDegreeReduce(Qw, U, tol=1.0):
    """Reduce the degree of the Nurbs curve.

    Parameters
    ----------
    Qw: float array (nc, nd)
        The nc control points of the Nurbs curve
    U: float array (nu)
        The nu knot values of the Nurbs curve

    Returns
    -------
    Pw: float array (nctrl, nd)
        The new control points
    U: float array (nknots)
        The new knot vector
    err: float array (nerr)
        The error vector

    This is algorithm A5.11 from 'The NURBS Book' pg223.
    """
    nc, nd = Qw.shape
    n = nc-1
    m = U.shape[0]-1
    p = m-n-1
    #print("Reduce degree of curve from %s to %s" % (p, p-1))
    # Workspace for return arrays
    Uh = np.zeros((2*m+1,))
    Pw = np.zeros((2*nc+1, nd))
    # Set up workspaces
    bpts = np.zeros((p+1, nd))  # Bezier control points of current segment
    Nextbpts = np.zeros((p-1, nd))  # leftmost control points of next Bezier segment
    rbpts = np.zeros((p, nd))  # degree reduced Bezier control points
    alfs = np.zeros((p-1,))  # knot insertion alphas
    err = np.zeros((m,))  # error vector

    # Initialize some variables
    ph = p-1
    mh = ph
    kind = ph+1
    r = -1
    a = p
    b = p+1
    cind = 1
    mult = p
    m = n+p+1
    Pw[0] = Qw[0]
    Uh[:ph+1] = U[0]  # Compute left end of knot vector
    bpts[:p+1] = Qw[:p+1]  # Initialize first Bezier segment
    # error vector is initialized
    #print("Initial Uh")
    #print(Uh[:ph+1])
     # Loop through the knot vector
    while b < m:
        # Compute knot multiplicity
        i = b
        while b < m and U[b] == U[b+1]:
            b += 1;
        mult = b-i+1
        mh += mult-1
        #print("Big loop b=%s < m=%s (mult=%s, mh=%s, )" % (b, m, mult, mh))
        #print("a=%s;b=%s;u[a]..u[b]=%s" % (a, b, U[a:b+1]))
        #print("Segment bpts\n", bpts)
        oldr = r
        r = p-mult
        lbz = (oldr+2)//2 if oldr > 0 else 1
        #print("oldr=%s; r=%s; lbz=%s" % (oldr, r, lbz))

        # Insert knot U[b] r times
        if r > 0:
            # Insert knot to get Bezier segment
            #print("Insert knot %s %s times" % (U[b], r))
            numer = U[b]-U[a]
            for k in range(p, mult-1, -1):
                alfs[k-mult-1] = numer / (U[a+k] - U[a])
            #print("alfs = %s" % alfs[:p])
            for j in range(1, r+1):
                save = r-j
                s = mult+j
                for k in range(p, s-1, -1):
                    bpts[k] = alfs[k-s]*bpts[k] + (1.0-alfs[k-s])*bpts[k-1]
                Nextbpts[save] = bpts[p]
                #print("Nextbpts %s = %s" %(save, Nextbpts[save]))

        # Degree reduce Bezier segment
        # if debug:
        #     print("Bezier segment degree reduction")
        #     print("bpts =\n", bpts)
        #     drawCtrlPts(bpts, color=magenta, marksize=8)
        rbpts, maxErr = BezDegreeReduce(bpts)
        # if debug:
        #     print(f"Reduced ctrl points: {rbpts.shape}\n", rbpts[:p])
        #     print("Degree reduce error = %s"%maxErr)
        #     drawCtrlPts(rbpts, color=cyan, marksize=8, linewidth=1, scurve=True)
        err[a] += maxErr
        if err[a] > tol:
            raise ValueError("Curve not degree reducible")
            return None  # Curve not degree reducible

        if oldr > 0:
            #print("Remove knot %s %s times" % (U[a], oldr))
            first = kind
            last = kind
            for k in range(oldr):
                i = first
                j = last
                kj = j-kind
                while j-i > k:
                    alfa = (U[a]-Uh[i-1]) / (U[b]-Uh[i-1])
                    beta = (U[a]-Uh[j-k-1]) / (U[b]-Uh[j-k-1])
                    Pw[i-1] = (Pw[i-1] - (1.0-alfa)*Pw[i-2]) / alfa
                    rbpts[kj] = (rbpts[kj] - beta*rbpts[kj+1])/(1.0-beta)
                    i += 1
                    j -= 1
                    kj -= 1

                # Compute knot removal error bounds (Br)
                if j-i < k:
                    Br = length(Pw[i-2] - rbpts[kj+1])
                else:
                    delta = (U[a]-Uh[i-1]) / (U[b]-Uh[i-1])
                    A = delta*rbpts[kj+1] + (1.0-delta)*Pw[i-2]
                    Br = length(Pw[i-1] - A)
                #print("Knot removal error = %s" % Br)
                # Update the error vector
                K = a+oldr-k
                q = (2*p-k+1)//2
                L = K-q
                for ii in range(L, a+1):  # These knot spans were affected
                    err[ii] += Br
                    if err[ii] > tol:
                        raise ValueError("Curve not degree reducible")

                first -= 1
                last += 1

            cind = i-1

        # Load knot vector and control points
        if a != p:
            # Load the knot U[a]
            for i in range(ph-oldr):
                #print("Load the knot ua=%s in Uh[%s]" % (U[a], kind))
                Uh[kind] = U[a]
                kind += 1

        for i in range(lbz, ph+1):
            # Load control points into Pw
            #print("Load control point %s from rbpts %s = %s" % (cind, i, rbpts[i]))
            Pw[cind] = rbpts[i]
            cind += 1
        if b < m:
            # Set up for next pass thru loop
            for i in range(r):
                bpts[i] = Nextbpts[i]
            for i in range(r, p+1):
                bpts[i] = Qw[b-p+i]
            a = b
            b += 1
        else:
            # End knot
            for i in range(ph+1):
                Uh[kind+i] = U[b]

        # if debug:
        #     pause()

    nh = mh - ph - 1
    Uh = Uh[:mh+1]
    Pw = Pw[:nh+1]

    return Pw, Uh, err


def curveUnclamp(P, U):
    """Unclamp a clamped curve.

    Input: P,U
    Output: P,U

    Note: this changes P and U inplace.

    Based on algorithm A12.1 of The NURBS Book.
    """
    n = P.shape[0] - 1
    m = U.shape[0] - 1
    p = m - n - 1
    # Unclamp at left end
    for i in range(p):
        U[p-i-1] = U[p-i] - (U[n-i+1]-U[n-i])
        if i == p-1:
            break
        k = p-1
        for j in range(i, -1, -1):
            alfa = (U[p]-U[k]) / (U[p+j+1]-U[k])
            P[j] = (P[j] - alfa*P[j+1]) / (1.0-alfa)
            k -= 1
    # Unclamp at right end
    for i in range(p):
        U[n+i+2] = U[n+i+1] + (U[p+i+1]-U[p+i])
        if i == p-1:
            break
        for j in range(i, -1, -1):
            alfa = (U[n+1]-U[n-j]) / (U[n-j+i+2]-U[n-j])
            P[n-j] = (P[n-j] - (1.0-alfa)*P[n-j-1]) / alfa
    return P, U


def curveGlobalInterpolationMatrix(u, p, t0, t1):
    """Compute the global curve interpolation matrix.

    Parameters
    ----------
    u: float array (nc)
        The parameter values at the nc points Q to be interpolated
    p: int
        The degree of the B-spline to construct.
    t0: 0 | 1
        1 if the tangent at the start of the curve is specified
    t1: 0 | 1
        1 if the tangent at the end of the curve is specified

    Returns
    -------
    U: float array (nU)
        The knot sequence, with nU = nu + p + 1, nu = nc + t0 + t1
    A: float array (nu, nu)
        The coefficient matrix for the interpolation. The control points P
        can be found by solving the system of linear equations: A * P = Q.

    See Also
    --------
    :func:`plugins.nurbs.globalInterpolationCurve`: the normal way to use this

    Notes
    -----
    Modified algorithm A9.1 from 'The NURBS Book' p.369.
    """
    nc = u.shape[0]
    nu = nc + t0 + t1
    nU = nu + p + 1
    m = nu + p;
    # Compute the knot vector U by averaging (9.8)
    U = np.zeros(nU)
    U[m-p:] = 1.0
    for j in range(1-t0, nc-p+t1):
        for i in range(j, j+p):
            U[j+p+t0] += u[i]
        U[j+p+t0] /= p
    # Set up coefficient matrix A
    A = np.zeros((nu,nu))
    A[0,0] = A[-1,-1] = 1.0
    if t0:
        A[1,:2] = -1.0, 1.0
    if t1:
        A[-2,-2:] = -1.0, 1.0
    for i in range(1, nc-1):
        s = find_span(U, u[i], p, nu-1)
        A[t0+i, s-p:s+1] = basis_funs(U, u[i], p, s)
    return U, A


# TODO: merge with curveGlobalInterpolationMatrix
# TODO: implement in nurbs_c
def curveGlobalInterpolationMatrix2(Q, D, u, p):
    """Compute the global curve interpolation matrix for all tangents given.

    Parameters
    ----------
    Q: float array (nc)
    D: float array(nc)
    u: float array (nc)
        The parameter values at the nc points Q to be interpolated
    p: 2 | 3
        The degree of the B-spline to construct.

    Returns
    -------
    U: float array (nU)
        The knot sequence, with nU = 2*nc + p + 1
    A: float array (2*nc, 2*nc)
        The coefficient matrix for the interpolation.
        The control points P can be found by solving the system of linear
        equations: A * P = Q.

    See Also
    --------
    :func:`plugins.nurbs.globalInterpolationCurve`: the normal way to use this

    Notes
    -----
    Modified algorithm A9.1 from 'The NURBS Book' p.369.
    """
    nc, nd = Q.shape
    if D.shape != Q.shape or u.shape[0] != nc:
        raise ValueError("Incompatible shapes of Q, D, u")
    n = nc - 1
    nvar = 2*nc
    nU = nvar + p + 1
    m = nvar + p;
    # Knot vector U
    U = np.zeros(nU)
    U[m-p:] = 1.0
    if p == 2:
        U[2:nU-2:2] = u
        U[3:nU-2:2] = (u[:-1] + u[1:]) / 2
    elif p == 3:
        U[4] = u[1] / 2
        U[-5] = (1+u[-2]) / 2
        U[5:nU-5:2] = (2*u[1:-2] + u[2:-1]) / 3
        U[6:nU-4:2] = (u[1:-2] + 2*u[2:-1]) / 3
    else:
        raise ValueError("Degree should be 2 or 3")
    # Coefficient matrix A
    A = np.zeros((nvar,nvar))
    A[0,0] = A[-2,-1] = 1.0
    A[1,:2] = -1.0, 1.0
    A[-1,-2:] = -1.0, 1.0
    for i in range(1, nc-1):
        s = find_span(U, u[i], p, nvar-1)
        fd = basis_derivs(U, u[i], p, s, 1)  # function values and 1st derivs
        A[2*i, s-p:s+1] = fd[0]
        A[2*i+1, s-p:s+1] = fd[1]
    # Right hand sides R
    R = np.empty((nvar, nd))
    R[::2] = Q
    R[1::2] = D
    R[1] *= U[p+1] / 3
    R[-1] *= (1-U[-(p+2)]) / 3
    return U, A, R


def cubicSplineInterpolation(Q, t0, t1, U):
    """Compute the control points of a cubic spline interpolate.

    Parameters
    ----------
    Q: float array (nc, 3)
        The nc points where the curve should pass through.
    t0: float array (3,)
        The tangent to the curve at the start point Q[0]
    t1: float array (3,)
        The tangent to the curve at the end point Q[nc-1]
    U: float array (nc+6,)
        The clamped knot vector: 3 zeros, the nc parameter values for
        the points, 3 ones.

    Returns
    -------
    float array (nc+2, 3)
        The control points of the curve. With the given knots they
        will create a 3-rd degree NURBS curve that passes through the points Q
        and has derivatives t0 and t1 at its end.

    Based on algorithm A9.2 of 'The Nurbs Book', p. 373
    """
    # Initialize
    n = Q.shape[0] - 1
    P = np.full((n+3, 3), np.nan)
    dd = np.full((n+1,), np.nan)  # workspace
    P[0] = Q[0]
    P[1] = P[0] + U[4] / 3 * t0
    P[n+2] = Q[n]
    P[n+1] = P[n+2] - (1-U[n+2]) / 3 * t1
    abc = basis_funs(U, U[4], 3, 4)
    den = abc[1]
    P[2] =(Q[1] - abc[0]*P[1]) / den
    for i in range(3, n):
        dd[i] = abc[2]/den
        abc = basis_funs(U, U[i+2], 3, i+2)
        den = abc[1] - abc[0]*dd[i]
        P[i] = (Q[i-1] - abc[0]*P[i-1]) / den
    dd[n] = abc[2]/den
    abc = basis_funs(U, U[n+2], 3, n+2)
    den = abc[1] - abc[0]*dd[n]
    P[n] = (Q[n-1] - abc[2]*P[n+1] - abc[0]*P[n-1]) / den
    for i in range(n-1, 1, -1):
        P[i] = P[i] - dd[i+1]*P[i+1]
    return P



if __name__ == '__draw__':
    from pyformex.plugins.nurbs import NurbsCurve
    N = NurbsCurve([
        [6.2, -7.3],
        [4.5, -6.7],
        [4.0, -5.2],
        [4.9, -3.5],
        [7.6, -2.5],
        [10.3, -3.3],
        [11.2, -5.0],
        [10.7, -6.7],
        [9.0, -7.5],
        ], degree=4, knots=
        [0., 0., 0., 0., 0., 1/3., 1/3., 2/3., 2/3., 1., 1., 1., 1., 1.])
    clear()
    def drawNurbs(N, color=black):
        draw(N, color=color)
        draw(N.knotPoints(), color=color, marksize=5)
        X = N.coords.toCoords()
        draw(PolyLine(X), color=color)
        draw(X, color=color)
        drawNumbers(X, color=color)
    drawNurbs(N, color=red)
    P4, U, err = curveDegreeReduce(N.coords, N.knots, 1.0)
    print(P4.shape, len(U), len(err))
    print(f"Maximum error {err}")
    N = NurbsCurve(control=P4, knots=U)
    drawNurbs(N, color=black)

# End
