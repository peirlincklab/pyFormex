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

"""Unit tests for the pyformex.arraytools module

These unit tests are based on the pytest framework.

"""
import pytest
# turns all warnings into errors for this module
pytestmark = pytest.mark.filterwarnings("error")

from . import *
from pyformex.arraytools import *

def test_isInt():
    """Test that argument is an integer number"""
    assert isInt(1)
    assert not isInt(1.1)
    assert isInt(np.arange(1)[0])
    assert not isInt(np.ones((1,))[0])
    assert not isInt(np.array(1))
    assert not isInt([1])

def test_isFloat():
    """Test that argument is a float number"""
    assert isFloat(1) is False
    assert isFloat(1.1) is True
    assert isFloat(np.arange(1)[0]) is False
    assert isFloat(np.ones((1,))[0]) is True

def test_isNum():
    """Test that argument is a number"""
    assert isNum(1) is True
    assert isNum(1.1) is True
    assert isNum('a') is False
    assert isNum([0,1]) is False

def test_stringar():
    assert stringar("Reshaped arange(4) = ",np.arange(4).reshape(2,2)) == "Reshaped arange(4) = [[0 1]\n                      [2 3]]"

def test_printar(capsys):
    printar("Indented array: ",np.arange(4).reshape(2,2))
    stdout, stderr = capsys.readouterr()
    assert stdout == 'Indented array: [[0 1]\n                 [2 3]]\n'

def test_powers():
    assert powers(2,5) == [ 1,2,4,8,16,32 ]
    assert powers(2.0,4) == [1.0, 2.0, 4.0, 8.0, 16.0]

def test_cumsum0():
    assert (cumsum0([2,4,3]) == [0, 2, 6, 9]).all()

def test_sind():
    assert np.isclose(sind(30), 0.5)
    assert np.isclose(sind(30,DEG), 0.5)
    assert np.isclose(sind(pi/6,RAD), 0.5)

def test_cosd():
    assert np.isclose(cosd(60), 0.5)
    assert np.isclose(cosd(60,DEG), 0.5)
    assert np.isclose(cosd(pi/3,RAD), 0.5)

def test_tand():
    assert np.isclose(tand(45), 1.)
    assert np.isclose(tand(45,DEG), 1.)
    assert np.isclose(tand(pi/4,RAD), 1.)

def test_arcsind():
    assert np.isclose(arcsind(0.5), 30)
    assert np.isclose(arcsind(0.5,DEG), 30)
    assert np.isclose(arcsind(0.5,RAD), pi/6)

def test_arccosd():
    assert np.isclose(arccosd(0.5), 60)
    assert np.isclose(arccosd(0.5,DEG), 60)
    assert np.isclose(arccosd(0.5,RAD), pi/3)

def test_arctand():
    assert np.isclose(arctand(1.), 45)
    assert np.isclose(arctand(1.,DEG), 45)
    assert np.isclose(arctand(1.,RAD), pi/4)

def test_arctand2():
    assert np.isclose(arctand2(0.5,sqrt(3)/2), 30)
    assert np.isclose(arctand2(0.5,sqrt(3)/2,DEG), 30)
    assert np.isclose(arctand2(0.5,sqrt(3)/2,RAD), pi/6)

@pytest.mark.parametrize('number, output', [
    (1.3, 1),
    (35679.23, 5),
    (0.4, 0),
    (0.00045676, -3),
    ])
def test_niceLogSize(number,output):
    assert niceLogSize(number) == output

@pytest.mark.parametrize('number, nice', [
    (0.0837, 0.09),
    (0.867, 0.9),
    (8.5, 9.0),
    (83.7, 90.0),
    (93.7, 100.0),
    ])
def test_niceNumber(number,nice):
    assert niceNumber(number) == nice

@pytest.mark.parametrize('number, round, nice', [
    (0.83, np.ceil, 0.9),
    (0.85, np.ceil, 0.9),
    (0.85, np.floor, 0.8),
    (0.85, np.round, 0.8),
    (0.95, np.round, 1.0),
    ])
def test_niceNumber_round(number,round,nice):
    assert niceNumber(number,round) == nice

def test_dotpr():
    A = [[1.0, 1.0], [1.0,-1.0], [0.0, 5.0]]
    B = [[5.0, 3.0], [2.0, 3.0], [1.33,2.0]]
    assert (dotpr(A,B) == np.array([ 8., -1., 10.])).all()
    assert (dotpr(A,B,0) == np.array([ 7., 10.])).all()

def test_length():
    A = [[1.0, 1.0], [1.0,-1.0], [0.0, 5.0]]
    assert np.allclose(length(A), [1.41, 1.41, 5. ], atol=0.01)
    assert np.allclose(length(A,0), [1.41, 5.2 ], atol=0.01)

def test_normalize():
    A = [[3.0, 3.0], [4.0,-3.0], [0.0, 0.0]]
#    with pytest.warns(RuntimeWarning):
#        eq(normalize(A), [[0.71, 0.71],[0.8, -0.6], [nan,nan]])
    assert eq(normalize(A), [[0.71, 0.71],[0.8, -0.6], [nan,nan]])
    assert eq(normalize(A,ignore_zeros=True), [[0.71, 0.71], [0.8, -0.6], [0., 0.]])
    assert eq(normalize(A,on_zeros='i'), [[0.71, 0.71], [0.8, -0.6], [0., 0.]])
    with pytest.raises(ValueError):
        eq(normalize(A,on_zeros='e'), [[0.71, 0.71], [0.8, -0.6], [0., 0.]])
    assert eq(normalize(A,0), [[0.6, 0.71], [0.8, -0.71], [0., 0.]])


def test_projection():
    A = [[2.,0.],[1.,1.],[0.,1.]]
    assert eq(projection(A,[1.,0.]), [2., 1., 0.])
    assert eq(projection(A,[1.,1.]), [1.41, 1.41, 0.71])

def test_parallel():
    A = [[2.,0.],[1.,1.],[0.,1.]]
    assert eq(parallel(A,[1.,0.]), [[2., 0.], [1., 0.], [0., 0.]])
    assert eq(parallel(A,A), [[2., 0.], [1., 1.], [0., 1.]])

def test_orthog():
    A = [[2.,0.],[1.,1.],[0.,1.]]
    assert eq(orthog(A,[1.,0.]), [[0., 0.], [0., 1.], [0., 1.]])
    assert eq(orthog(A,A), [[0., 0.], [0., 0.], [0., 0.]])

@pytest.mark.parametrize('ord, res', [
    (None, 5.0),
    (2, 5.0),
    (1, 8.6),
    (inf, 3.2),
    (-inf, 2.4),
    (3, 4.19),
    (1.5, 5.98),
    (0.5, 25.71),
])
def test_norm(ord,res):
    assert eq(np.linalg.norm([2.4,-3.0,3.2],ord), res)

def test_inside():
    assert inside([0.5,0.5,2.9],[0.,0.,0.],[1.,2.,3.])
    assert not inside([0.5,0.5,3.1],[0.,0.,0.],[1.,2.,3.])

def test_unitVector():
    assert eq(unitVector(1), [ 0.,  1.,  0.])
    assert eq(unitVector([0.,3.,4.]), [ 0. ,  0.6,  0.8])
    with pytest.raises(ValueError):
        unitVector(3)
        unitVector([1.,2.])
        unitVector([0.,0.,0.])

def test_rotationMatrix():
    pass

def test_rotMat():
    pass

def test_trfMatrix():
    pass

def test_rotMatrix():
    pass

def test_rotationAnglesFromMatrix():
    pass

def test_vectorRotation():
    pass

# def test_addAxis():
#     A = [[1,2,3],[4,5,6]]
#     assert (addAxis(A,1) == [[[1,2,3]],[[4,5,6]]]).all()
#     assert addAxis(A,0).shape == (1,2,3)
#     assert addAxis(A,1).shape == (2,1,3)
#     assert addAxis(A,2).shape == (2,3,1)
#     assert addAxis(A,-1,warn=False).shape == (2,3,1)
#     assert addAxis(A,-2,warn=False).shape == (2,1,3)
#     assert addAxis(A,-3,warn=False).shape == (1,2,3)

def test_growAxis():
    A = [[1,2,3],[4,5,6]]
    assert (growAxis(A,2) == [[1,2,3,0,0],[4,5,6,0,0]]).all()

def test_reorderAxis():
    A = [[1,2,3],[4,5,6]]
    assert (reorderAxis(A, [2,0,1]) == [[3,1,2],[6,4,5]]).all()
    assert (reorderAxis(A, 'reverse') == [[3,2,1],[6,5,4]]).all()
    R = reorderAxis(A, 'random')
    R.sort(axis=-1)
    assert (R == A).all()


def test_reverseAxis():
    A = np.array([[1,2,3],[4,5,6]])
    assert (reverseAxis(A, 0) == [[4,5,6],[1,2,3]]).all()
    assert (reverseAxis(A, 1) == A[:,::-1]).all()

def test_interleave():
     assert (interleave(np.arange(4), 10*np.arange(3)) == [0,0,1,10,2,20,3]).all()
     A = np.arange(8).reshape(2,4)
     assert (interleave(A,10*A) == \
             [[0,1,2,3],[0,10,20,30],[4,5,6,7],[40,50,60,70]]).all()
     with pytest.raises(ValueError):
         interleave(np.arange(4),np.arange(2))

def test_multiplex():
    A = np.arange(6).reshape(2,3)
    assert eq(multiplex(A,4,0,False), [[[0,1,2],[3,4,5]]]*4)
    assert eq(multiplex(A,4,1,False), [[[0,1,2]]*4,[[3,4,5]]*4])
    assert eq(multiplex(A,4,2,False), [[[0]*4,[1]*4,[2]*4],[[3]*4,[4]*4,[5]*4]])
    assert eq(multiplex(A,4,-1,False), multiplex(A,4,2,False))
    assert eq(multiplex(A,4,-2,False), multiplex(A,4,1,False))
    assert eq(multiplex(A,4,-3,False), multiplex(A,4,0,False))

def test_concat():
    assert eq(concat([np.array([0,1]) ,np.array([]), np.array([2,3])]), [0, 1, 2, 3])

def test_minmax():
    a = np.array([[ [1.,0.,0.], [0.,1.,0.] ], [ [2.,0.,0.], [0.,2.,0.] ] ])
    assert eq(minmax(a,axis=1), \
              [[[0., 0., 0.], [1., 1., 0.]], [[0., 0., 0.], [2., 2., 0.]]])


def test_abat():
    A = np.array([[1.0, 2.0]])
    B = np.array([[1.0,2.0], [3.0,4.0]])
    assert eq(abat(A,B), [27.])

def test_atba():
    A = np.array([[1.0], [2.0]])
    B = np.array([[1.0,2.0], [3.0,4.0]])
    assert eq(atba(A,B), [27.])

def test_stretch():
    assert eq(stretch([1.,2.,3.],min=0,max=1), [0., 0.5, 1.])
    A = np.arange(6).reshape(2,3)
    assert eq(stretch(A,min=20,max=30), [[20, 22, 24], [26, 28, 30]])
    assert eq(stretch(A,min=20,max=30,axis=1), [[20, 25, 30], [20, 25, 30]])
    assert eq(stretch(A,max=30), [[ 0,  6, 12], [18, 24, 30]])
    assert eq(stretch(A,min=2,axis=1), [[2, 4, 5], [2, 4, 5]])
    assert eq(stretch(A.astype(Float),min=2,axis=1), [[2.,3.5,5.],[ 2.,3.5,5.]])

def test_horner():
    R = horner([[1.,1.,1.],[1.,2.,3.]],[0.5,1.0])
    assert eq(R, [[1.5, 2., 2.5], [2., 3., 4.]])

def test_solveMany():
    A1 = np.array([[[2.]], [[3.]]])
    B1 = np.array([[[2., 8.]], [[6., 27.]]])
    assert eq(solveMany(A1,B1), [[[1.,4.]], [[2.,9.]]])
    A1 = [[2.]]
    B1 = [[2., 8.]]
    X1 = [[1., 4.]]
    A2 = [[3.]]
    B2 = [[6., 27.]]
    X2 = [[2., 9.]]
    A = np.stack([A1,A2],axis=0)
    B = np.stack([B1,B2],axis=0)
    X = np.stack([X1,X2],axis=0)
    assert eq(solveMany(A,B), X)
    # TODO: examples with ndof = 2,3,4

def test_splitrange():
    assert (splitrange(7,3) == [0,2,5,7]).all()
    assert (splitrange(60,4) == [0,15,30,45,60]).all()

def test_splitar():
    X = np.array([[1.,0.,0.],
               [2.,0.,0.],
               [3.,0.,0.],
               [4.,0.,0.],
    ])
    XL = splitar(X,2)
    assert eq(XL[0], np.array([[1.,0.,0.],
                            [2.,0.,0.],
    ])) and eq(XL[1], np.array([[3.,0.,0.],
                             [4.,0.,0.],
    ]))
    XL = splitar(X,2,close=True)
    assert eq(XL[0], np.array([[1.,0.,0.],
                            [2.,0.,0.],
                            [3.,0.,0.],
    ])) and eq(XL[1], np.array([[3.,0.,0.],
                             [4.,0.,0.],
    ]))
    XL = splitar(X,2,axis=-1)
    assert eq(XL[0], np.array([[1.,0.],
                            [2.,0.],
                            [3.,0.],
                            [4.,0.],
    ])) and eq(XL[1], np.array([[0.],[0.],[0.],[0.],
    ]))

def test_checkInt():
    assert checkInt(1) == 1
    assert checkInt(1,min=0,max=1) == 1
    with pytest.raises(ValueError):
        assert checkInt(2,max=1)
        assert checkInt(-1,min=0)
        assert checkInt(1.0)
        assert checkInt([1])

def test_checkFloat():
    assert checkFloat(1.0) == 1.0
    assert checkFloat(1) == 1.0
    assert checkFloat(0.5,min=0.,max=1.) == 0.5
    with pytest.raises(ValueError):
        assert checkFloat(1.1,max=1.)
        assert checkFloat(1.1,min=1.2)
        assert checkFloat([1.])

def test_checkArray():
    pass

def test_checkArray1D():
    pass

def test_checkUniqueNumbers():
    pass

def test_readArray():
    pass

def test_writeArray():
    pass

def test_cubicEquation():
    pass

def test_unniqueOrdered():
    pass

def test_renumberIndex():
    pass

def test_complement():
    pass

def test_inverseUniqueIndex():
    pass

def test_sortSubsets():
    pass

def test_sortByColumns():
    pass

def test_uniqueRows():
    pass

def test_argNearestValue():
    pass

def test_nearestValue():
    pass

def test_inverseIndex():
    pass

def test_findFirst():
    pass

def test_findAll():
    pass

def test_groupArgmin():
    pass

def test_vectorPairAreaNormals():
    pass

def test_vectorPairArea():
    pass

def test_vectorPairNormals():
    pass

def test_vectorTripleProduct():
    pass

def test_vectorPairCosAngle():
    pass

def test_vectorPairAngle():
    pass

def test_det2():
    pass

def test_det3():
    pass

def test_det4():
    pass

def test_percentile():
    pass

def test_multiplicity():
    pass

def test_histogram2():
    pass

def test_movingView():
    pass

def test_movingAverage():
    pass

def test_randomNoise():
    pass

def test_unitDivisor():
    pass

def test_uniformParamValues():
    pass

def test_nodalSum_Avg():
    val = np.array([
        [[ 0.,  0.],
         [ 2., 20.],
         [ 3., 30.],
         [ 1., 10.]],
        [[ 2., 20.],
         [ 4., 40.],
         [ 5., 50.],
         [ 3., 30.]]])
    elems = np.array([
        [0, 2, 3, 1],
        [2, 4, 5, 3]])
    sum,cnt = nodalSum(val,elems)
    assert eq(sum,[[0,0],[1,10],[4,40],[6,60],[4,40],[5,50]])
    assert (cnt == [1, 1, 2, 2, 1, 1]).all()
    avg = nodalAvg(val,elems)
    assert eq(avg,[[0,0],[1,10],[2,20],[3,30],[4,40],[5,50]])

def test_pprint():
    pass

def test_fmtData1d():
    pass

def test_isqrt():
    pass

# End
