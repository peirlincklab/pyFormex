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
"""Framework for multi-processing in pyFormex

This module contains some functions to perform multiprocessing
in pyFormex in a unified way.

"""
import multiprocessing as mp
import numpy as np

from pyformex.arraytools import splitar

cpu_count = mp.cpu_count

def splitArgs(args, mask=None, nproc=-1, close=False):
    """Split data blocks over multiple processors.

    Parameters
    ----------
    args: list or tuple of :term:`array_like`
        A sequence of data blocks that may need to be split for parallel
        processing over multiple processors. Splitting is done along the
        first dimension, which should therefore be the same for all arrays
        in the sequence that need to be split.
    mask: list or tuple of bool
        If provided, this flags the items in ``args`` that should be split.
        The list should have the same length as ``args``.
        If not provided, all array type items in ``args`` will be split.
    nproc: int
        Intended number of processors. If negative (default), it is set equal
        to the number of processors detected on the host machine.
    close: bool
        If True, the elements where the arrays are split are included in both
        blocks delimited by the element. Thus splitting an array [1, 2, 3]
        in two results in [1, 2] and [2, 3], while the default split would
        be [1, 2] and [3].

    Returns
    -------
    list of tuples.
        The list contains ``nproc`` tuples and each tuple contains the same
        number of items as the input ``args`` and in the same order, whereby
        the (nonmasked) arrays are replaced by a slice of the array along
        its first axis, and the masked and non-array items are replicated
        as is.

    See Also
    --------
    arraytools.splitar: the low level function used to do the splitting

    Examples
    --------
    >>> splitArgs([np.arange(5),'abcde'],nproc=3)
    [(array([0, 1]), 'abcde'), (array([2]), 'abcde'), (array([3, 4]), 'abcde')]
    >>> for i in splitArgs([np.eye(5),'=>',np.arange(5)],nproc=3):
    ...     print("%s %s %s" % i)
    [[1. 0. 0. 0. 0.]
     [0. 1. 0. 0. 0.]] => [0 1]
    [[0. 0. 1. 0. 0.]] => [2]
    [[0. 0. 0. 1. 0.]
     [0. 0. 0. 0. 1.]] => [3 4]
    >>> for i in splitArgs([np.eye(5),'=>',np.arange(5)],mask=[1,0,0],nproc=3):
    ...     print("%s %s %s" % i)
    [[1. 0. 0. 0. 0.]
     [0. 1. 0. 0. 0.]] => [0 1 2 3 4]
    [[0. 0. 1. 0. 0.]] => [0 1 2 3 4]
    [[0. 0. 0. 1. 0.]
     [0. 0. 0. 0. 1.]] => [0 1 2 3 4]

    """
    if nproc < 0:
        nproc = mp.cpu_count()
    if mask is None:
        mask = [isinstance(a, np.ndarray) for a in args]
    split = [
        splitar(a, nproc, close=close) if m else [a] * nproc
        for a, m in zip(args, mask)
    ]
    return list(zip(*split))


def dofunc(arg):
    """Helper function for the multitask function.

    Parameters
    ----------
    arg: tuple
        The first item of the tuple is a callable. The remaining
        items are its arguments.

    Returns
    -------
    object
        The value of the callable when passed the remaining items as
        arguments.

    Examples
    --------
    >>> dofunc((max,(2, 5, 3)))
    5

    """
    func, args = arg
    return func(*args)


def multitask(tasks, nproc=-1):
    """Perform tasks in parallel.

    Runs a number of tasks in parallel over a number of subprocesses.

    Parameters
    ----------
    tasks: list of tuples
        Each task in the list is a tuple where the first item is a callable
        and the other items are the arguments to be passed to the callable.
    nproc: int
        The number of subprocesses to be started. This may be
        different from the number of tasks to run: processes finishing a
        task will pick up a next one. There is no benefit in starting more
        processes than the number of tasks or the number of processing units
        available. The default will set ``nproc`` to the minimum of these two
        values.

    Examples
    --------
    >>> task1 = (int.__add__, (2, 3))
    >>> task2 = (int.__mul__, (2, 3))
    >>> multitask((task1, task2))
    [5, 6]
    >>> from pyformex import process
    >>> tasks = [(process.run, ('ls -d .',)), (process.run, ('uname',))]
    >>> for res in multitask(tasks): print(res.stdout)
    .
    Linux
    """
    if nproc < 0:
        nproc = min(len(tasks), mp.cpu_count())
    with mp.Pool(nproc) as pool:
        res = pool.map_async(dofunc, tasks)
        pool.close()
        pool.join()
        return res.get(timeout=10)

# End
