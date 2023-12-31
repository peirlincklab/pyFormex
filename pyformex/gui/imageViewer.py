#!/usr/bin/env python3
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
"""A general image viewer

Part of this code was borrowed from the TrollTech Qt examples.
"""

caption = "pyFormex Image Viewer"

import os, sys
from PySide2 import QtCore, QtGui, QtWidgets


def tr(s):
    return QtCore.QCoreApplication.translate('ImageViewer', s)


class ImageViewer(QtWidgets.QMainWindow):
    """pyFormex image viewer

    The pyFormex image viewer was shaped after the Image Viewer from the
    TrollTech Qt documentation.

    It can be use as stand alone application, as well as from inside
    pyFormex. The viewer allows browsing through directories, selecting
    an image to be displayed. The image can be resized to fit a window.

    Parameters:

    - `parent`: The parent Qt widget (the Qt app in the stand alone case).
    - `path`: string: the full path to the image to be initially displayed.
    """

    def __init__(self, parent=None, path=None):
        QtWidgets.QMainWindow.__init__(self)

        self.parent = parent
        self.filename = path
        self.image = QtWidgets.QLabel()
        self.image.setBackgroundRole(QtGui.QPalette.Base)
        self.image.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        #self.image.setScaledContents(True)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setBackgroundRole(QtGui.QPalette.Dark)
        self.scroll.setWidget(self.image)
        self.scroll.setWidgetResizable(True)
        self.setCentralWidget(self.scroll)

        self.createActions()
        self.createMenus()

        self.setWindowTitle(tr(caption))
        self.resize(500, 400)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

        if path:
            self.openfile(path)


    def openfile(self, filename=None):
        if not filename:
            filename = self.filename
            if filename is None:
                filename = QtCore.QDir.currentPath()
            filename = QtWidgets.QFileDialog.getOpenFileName(self, tr("Open File"), filename)[0]
            if not filename:
                return

        image = QtGui.QImage(filename)
        if image.isNull():
            QtWidgets.QMessageBox.information(self, tr(caption), tr("Cannot load {}".format(filename)))
            return

        print("Size %sx%s" % (image.width(),image.height()))
        self.filename = str(filename)
        self.image.setPixmap(QtGui.QPixmap.fromImage(image))
        self.scaleFactor = 1.0

        self.printAct.setEnabled(True)
        self.fitToWindowAct.setEnabled(True)
        self.updateActions()

        ## if not self.fitToWindowAct.isChecked():
        self.image.adjustSize()
        self.normalSize()


    def print_(self):
        if not self.image.pixmap():
            return

        self.printer = QtGui.QPrinter()
        dialog = QtWidgets.QPrintDialog(self.printer, self)
        if dialog.exec_():
            painter = QtGui.QPainter(self.printer)
            rect = painter.viewport()
            size = self.image.pixmap().size()
            size.scale(rect.size(), QtCore.Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(self.image.pixmap().rect())
            painter.drawPixmap(0, 0, self.image.pixmap())


    def zoomIn(self):
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.8)

    def normalSize(self):
        self.image.resize(self.image.pixmap().size())
        #self.image.adjustSize()
        self.scaleFactor = 1.0

    def fitToWindow(self):
        fitToWindow = self.fitToWindowAct.isChecked()
        self.scroll.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()
        self.updateActions()

    def fitToImage(self):
        self.normalSize()
        self.scroll.resize(self.image.size())


    def about(self):
        QtWidgets.QMessageBox.about(self, tr("About pyFormex Image Viewer"), tr("""
<p>The <b>pyFormex Image Viewer</b> was shaped after the
<b>Image Viewer</b> from the TrollTech Qt documentation.</p>
<p>The example shows how to combine QLabel
and QScrollArea to display an image. QLabel is typically used
for displaying a text,but it can also display an image.
QScrollArea provides a scrolling view around another widget.
If the child widget exceeds the size of the frame,QScrollArea
automatically provides scroll bars. </p>
<p>The example
demonstrates how QLabel's ability to scale its contents
(QLabel.scaledContents),and QScrollArea's ability to
automatically resize its contents
(QScrollArea.widgetResizable),can be used to implement
zooming and scaling features. </p>
<p>In addition the example
shows how to use QPainter to print an image.</p>
"""))


    def createActions(self):
        self.openAct = QtWidgets.QAction(tr("&Open..."), self)
        self.openAct.setShortcut(tr("Ctrl+O"))
        self.openAct.triggered.connect(self.openfile)

        self.printAct = QtWidgets.QAction(tr("&Print..."), self)
        self.printAct.setShortcut(tr("Ctrl+P"))
        self.printAct.setEnabled(False)
        self.printAct.triggered.connect(self.print_)


        self.zoomInAct = QtWidgets.QAction(tr("Zoom &In (25%)"), self)
        self.zoomInAct.setShortcut(tr("Ctrl++"))
        self.zoomInAct.setEnabled(False)
        self.zoomInAct.triggered.connect(self.zoomIn)

        self.zoomOutAct = QtWidgets.QAction(tr("Zoom &Out (25%)"), self)
        self.zoomOutAct.setShortcut(tr("Ctrl+-"))
        self.zoomOutAct.setEnabled(False)
        self.zoomOutAct.triggered.connect(self.zoomOut)

        self.normalSizeAct = QtWidgets.QAction(tr("&Normal Size"), self)
        self.normalSizeAct.setShortcut(tr("Ctrl+S"))
        self.normalSizeAct.setEnabled(False)
        self.normalSizeAct.triggered.connect(self.normalSize)

        self.fitToImageAct = QtWidgets.QAction(tr("Fit &Window to Image"), self)
        self.fitToImageAct.setShortcut(tr("Ctrl+W"))
        self.fitToImageAct.setEnabled(False)
        #self.fitToImageAct.setCheckable(True)
        self.fitToImageAct.triggered.connect(self.fitToImage)

        self.fitToWindowAct = QtWidgets.QAction(tr("&Fit Image to Window"), self)
        self.fitToWindowAct.setShortcut(tr("Ctrl+F"))
        self.fitToWindowAct.setEnabled(False)
        self.fitToWindowAct.setCheckable(True)
        self.fitToWindowAct.triggered.connect(self.fitToWindow)

        self.aboutAct = QtWidgets.QAction(tr("&About"), self)
        self.aboutAct.triggered.connect(self.about)

        if isinstance(self.parent, QtWidgets.QApplication):

            self.exitAct = QtWidgets.QAction(tr("E&xit"), self)
            self.exitAct.setShortcut(tr("Ctrl+Q"))
            self.exitAct.triggered.connect(self.close)

            self.aboutQtAct = QtWidgets.QAction(tr("About &Qt"), self)
            self.aboutQtAct.triggered.connect(self.parent.aboutQt)

        elif isinstance(self.parent, QtWidgets.QDialog):

            self.acceptAct = QtWidgets.QAction(tr("&Accept"), self)
            self.acceptAct.setShortcut(tr("Ctrl+A"))
            self.acceptAct.triggered.connect(self.parent.accept)

            self.rejectAct = QtWidgets.QAction(tr("&Reject"), self)
            self.rejectAct.setShortcut(tr("Ctrl+Q"))
            self.rejectAct.triggered.connect(self.parent.reject)


    def createMenus(self):
        self.fileMenu = QtWidgets.QMenu(tr("&File"), self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator()

        self.viewMenu = QtWidgets.QMenu(tr("&View"), self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fitToImageAct)
        self.viewMenu.addAction(self.fitToWindowAct)

        self.helpMenu = QtWidgets.QMenu(tr("&Help"), self)
        self.helpMenu.addAction(self.aboutAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.helpMenu)

        if isinstance(self.parent, QtWidgets.QApplication):
            self.fileMenu.addAction(self.exitAct)
            self.helpMenu.addAction(self.aboutQtAct)
        elif isinstance(self.parent, QtWidgets.QDialog):
            self.fileMenu.addAction(self.acceptAct)
            self.fileMenu.addAction(self.rejectAct)


    def updateActions(self):
        self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.fitToImageAct.setEnabled(not self.fitToWindowAct.isChecked())


    def scaleImage(self, factor):
        if not self.image.pixmap():
            return
        self.scaleFactor *= factor
        self.image.resize(self.scaleFactor * self.image.pixmap().size())

        self.adjustScrollBar(self.scroll.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scroll.verticalScrollBar(), factor)

        self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)


    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value() + ((factor - 1) * scrollBar.pageStep()/2)))


def main():
    import sys
    global app
    app = QtWidgets.QApplication(sys.argv)
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = None
    viewer = ImageViewer(app, path)
    viewer.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
