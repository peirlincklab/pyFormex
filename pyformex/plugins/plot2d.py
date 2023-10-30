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
"""plot2d.py

Generic 2D plotting functions for pyFormex.
"""

import numpy as np

import pyformex as pf
from pyformex import utils
from pyformex import arraytools as at


plot2d_system = None
plots = []


def init_plot2d_system(plot2d=None):
    global plt, plot2d_system
    if plot2d_system is not None and plot2d == plot2d_system:
        # already initialised
        pass
    else:
        # need initialisation
        plot2d = pf.cfg['plot2d']
        if utils.Module.has(plot2d):
            if plot2d == 'gnuplot':
                import Gnuplot as plt
            elif plot2d == 'qwt':
                # currently not supported
                #from gui.Qwt5.qplt import *
                plot2d = None
            elif plot2d == 'matplotlib':
                import matplotlib.pyplot as plt
        else:
            plot2d = None
            pf.error("I can not draw the plot because I could not load the requested 2d plot library '%s' for your Python version (%s). You need to install one of the supported plot libraries and/or set the appropriate preference in your pyFormex configuration file or via the Settings->Settings Dialog menu item." % (plot2d_system, 3))

    plot2d_system = plot2d
    return plot2d_system


def showStepPlot(x, y, xlabel='', ylabel='', label='', title=None):
    """
    Show a step plot of x,y data.

    """
    if plot2d_system is None and init_plot2d_system() is None:
        return

    if title is None:
        title = 'TriSurface statistics plot: %s' % label
    maxlen = min(len(x), len(y))
    x = x[:maxlen]
    y = y[:maxlen]

    if plot2d_system == 'gnuplot':
        data = plt.Data(x, y, title=label, with_='steps')
        g = plt.Gnuplot(persist=0)
        plots.append(g)
        if xlabel:
            g.xlabel(xlabel)
        if ylabel:
            g.ylabel(ylabel)
        g.title(title)
        g.plot(data)

    elif plot2d_system == 'matplotlib':
        g = plt.figure()  # create new fig
        plots.append(g)
        #plt.close() # close the current figure (if any)
        plt.step(x, y, where='post', label=label)
        if xlabel:
            plt.xlabel(xlabel)
        if ylabel:
            plt.ylabel(ylabel)
        plt.title(title)
        plt.legend()
        plt.show()


def showHistogram(x, y, cumulative=False, xlabel='', ylabel='', label='', title=''):
    """
    Show a histogram of x,y data.

    """
    if cumulative:
        fill = y[-1]
    else:
        fill = y[0]
    y = at.growAxis(y, len(x)-len(y), fill=fill)
    if cumulative:
        ysum = y[-1]
    else:
        ysum = y.sum()
    ylabel = 'occurrences (total=%s)' % ysum
    showStepPlot(x, y, xlabel=xlabel, ylabel=ylabel, label=label, title=title)


def createHistogram(data, cumulative=False, **kargs):
    """
    Create a histogram from data

    """
    y, x = np.histogram(data, **kargs)
    if cumulative:
        y = y.cumsum()
    return y, x


def closeAllPlots():
    while plots:
        p = plots.pop(0)
        if plot2d_system == 'gnuplot':
            p.close()
        elif plot2d_system == 'matplotlib':
            plt.close(p)



if __name__ == '__draw__':

    mi = 0
    ma = 10
    n = 100
    x = np.arange(mi, ma)
    y = np.random.randint(mi, ma, n)
    title = "%s random numbers in range(%s,%s)" % (n, mi, ma)
    showHistogram(x, y, xlabel='values', title=title)

# End
