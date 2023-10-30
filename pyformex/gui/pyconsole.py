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
"""Interactive Python console in a Qt widget.

This module provides the PyConsole class: an interactive Python interpreter
embedded in a Qt widget.
PyConsole was created for the pyFormex GUI, but can be used independently
in any Python Qt application. It can even be run as a standalone application.
PyConsole works with either PyQt5 or PySide2.

Features:

- accepts multiline statements
- accepts continuation lines (ending in backslash)
- keeps a command history with recall and save
- colored output
- indentation adjustement on multiple of 4 columns
- built-in help function
- built-in completer functionality
- can be executed as a standalone program (see below)
- easy to add more functionality

Special Keys:

- RETURN: move input to output and execute if statement complete
- LEFT: go left
- RIGHT: go right
- CTRL-LEFT: go to beginning of line
- CTRL-END: go to end of line
- UP: go up in history
- DOWN: go down in history
- CTRL-UP: go to first line in history
- CTRl-DOWN: go to last line in history
- TAB: if cursor is at start or after a space: increase indent to next
  multiple of 4; else: start completion of the text before the cursor
- BACKTAB (SHIFT-TAB): if cursor is after a space: reduce indent to previous
  multiple of 4

Completion:

If TAB is pressed when the cursor is after a non-space, the built-in completer
is started. It first looks up the possible completions for the text before
the cursor. If None is found, it does nothing. If just one is found, it is
immediately filled in. Another TAB press will remove it again. If multiple
completions were found, it prints the list of possible completions on the
output. Hitting TAB again will fill in the first completion, and repeatedly
pressing TAB cycles through the whole list of completions until the last
possiblility is removed again. Pressing any other key but TAB during the
completion process will accept the currently filled in completion. Note that
any text following the cursor also keeps in place following the completion.

To run the console as a standalone program, use the following command::

    python3 pyconsole.py

You can specify the window geometry in X11 style::

    python pyconsole.py --qwindowgeometry 800x600-0+0

This command will create a window of 800 by 600 pixels in the upper right corner
of the screen.
"""
import sys
import code
import rlcompleter

if 'pyformex' in sys.modules:
    from pyformex.gui import QtCore, QtGui, QtWidgets, Signal#, Slot
else:
    try:
        from PySide2 import QtCore, QtGui, QtWidgets
        from PySide2.QtCore import Signal, Slot
    except ModuleNotFoundError:
        try:
            from PyQt5 import QtCore, QtGui, QtWidgets
            from PyQt5.QtCore import pyqtSignal as Signal
            # from PyQt5.QtCore import pyqtSlot as Slot
        except ModuleNotFoundError:
            print("You need PySide2 or PyQt5 to run this")



class LineEdit(QtWidgets.QLineEdit):
    """Input line with a history buffer for recalling previous lines.

    Parameters
    ----------
    historysize: int
        Maximum number of lines kept in the history. If <= 0, the history
        size is unlimited.
    """
    newline = Signal(str)  # Signal when return key pressed

    def __init__(self, historysize=0):
        super().__init__()
        self.historymax = historysize
        self.clearhistory()
        self.pending = ''        # pending text not in the history yet
        self.completer = None
        self.completions = []
        self.completertext = ''
        self.completerstate = 0


    def clearhistory(self):
        """Clear history buffer"""
        self.history = []
        self.historyindex = 0   # index of next line to append

    # We need to override event() because we want to catch TAB
    # otherwise, we could just use keyPressEvent
    def event(self, ev):
        """Event handler: handles special keys."""
        Qt = QtCore.Qt
        if ev.type() == QtCore.QEvent.KeyPress:
            # First handle TAB
            if ev.key() == Qt.Key_Tab:
                pos = self.cursorPosition()
                text = self.text()[:pos]
                if text and (text[-1:] != ' ' or self.completions):
                    # Try completion
                    if not self.completions:
                        completions = self.getcompletions(text)
                        if not completions:
                            return True
                        self.completions = completions
                        self.completerstate = 0
                        self.completerpos = pos
                        if len(completions) > 1:
                            print(f"Completions: {completions}")
                            return True
                    if self.hasSelectedText():
                        self.backspace()
                    if self.completerstate < len(self.completions):
                        compl = self.completions[self.completerstate]
                        compl = compl[len(self.completertext):]
                        self.setCursorPosition(self.completerpos)
                        self.insert(compl)
                        self.setSelection(self.completerpos, len(compl))
                        self.completerstate += 1
                    else:
                        self.setCursorPosition(self.completerpos)
                        self.deselect()
                        self.completerstate = 0
                    return True
                else:
                    pass  # to use tab as indent

            self.completions = []
            self.deselect()
            # First handle history navigation keys
            # and keys that do not end it
            if ev.key() == Qt.Key_Up:
                if self.historyindex == len(self.history):
                    self.pending = self.text()
                if ev.modifiers() == Qt.NoModifier:
                    self.recall(self.historyindex - 1)
                elif ev.modifiers() == Qt.ControlModifier:
                    self.recall(0)
                return True

            elif ev.key() == Qt.Key_Down:
                if ev.modifiers() == Qt.NoModifier:
                    if self.historyindex != len(self.history):
                        self.recall(self.historyindex + 1)
                elif ev.modifiers() == Qt.ControlModifier:
                    self.recall(len(self.history) - 1)
                return True

            elif ev.key() == Qt.Key_Tab:
                self.tabindent(True)
                return True

            elif ev.key() == Qt.Key_Backtab:
                 self.tabindent(False)
                 return True

            elif ev.key() == ord('?') and ev.modifiers() & Qt.ControlModifier:
                self.printhistory()
                return True

            # Any other key turns off history navigation
            if ev.key() == Qt.Key_Return:
                self.returnkey()
                return True

        return super().event(ev)  # pass on

    def tabindent(self, forward=True):
        """Add/remove blanks to next/previous multiple of 4 position"""
        text = self.text()
        pos = len(text) - len(text.lstrip())
        self.setCursorPosition(pos)
        if forward:
            add = 4 - (pos % 4)
            self.insert(' ' * add)
        else:
            if pos > 0:
                delete = (pos+3) % 4 + 1
                self.setSelection(pos-delete, delete)
                self.backspace()

    def getcompletions(self, text):
        """Return possible completions of text in context"""
        i = text.rfind(' ')
        self.completertext = text[i+1:]
        completions = []
        state = 0
        while True:
            comp = self.completer.complete(self.completertext, state)
            if comp is None:
                break
            state += 1
            completions.append(comp)
        return completions

    def returnkey(self):
        """Handle return key. Record line and emit newline signal"""
        text = self.text()#.rstrip()
        self.record(text)
        self.newline.emit(text)
        self.pending = ''
        self.setText('')

    def recall(self, index):
        """Select a line from the history list"""
        if index < 0:
            # print("== Top of history ==")
            pass
        elif index < len(self.history):
            self.setText(self.history[index])
            self.historyindex = index
        else:
            self.setText(self.pending)
            self.historyindex = len(self.history)

    def record(self, line):
        """Add line to history buffer"""
        if self.historymax > 0:
            while len(self.history) >= self.historymax:
                self.history.pop(0)
        if len(self.history) == 0 or line != self.history[-1]:
            self.history.append(line)
        self.historyindex = len(self.history)

    def printhistory(self):
        """Print the history to stdout"""
        print("History:")
        for i, line in enumerate(self.history):
            c = '*' if i == self.historyindex else ' '
            print(f"{i:4}:{c} {line}")
        print(f"Pending: {self.pending}")

    def savehistory(self, filename, maxlines=0):
        """Save the history to file"""
        with open(filename, 'w') as fil:
            for line in self.history[-maxlines:]:
                fil.write(line+'\n')

    def loadhistory(self, filename):
        """Load a history file"""
        with open(filename, 'r') as fil:
            hist = [s.strip('\n').strip() for s in fil.readlines()]
            hist = [s for s in hist if s]
            self.history = hist
            if self.historymax > 0:
                self.history = self.history[-self.historymax:]
            self.recall(len(self.history))

# TODO: add a method setcolor


def help(obj=None):
    """Print help anbout any object"""
    if obj is None:
        print(__doc__)
        print("help(object) will print the __doc__ of any object)")
    else:
        print(obj.__doc__)


###########################################################################

class PyConsole(QtWidgets.QWidget):
    """An interactive Python console in a Qt widget.

    PyConsole is a Qt5 widget exposing an interactive Python console.
    It combines a read-only output area and a one line input area. When
    pressing ENTER, it copies the input line to the output area and executes
    the statement if it is complete.

    Parameters
    ----------
    parent: QWidget
        If provided, the PyConsole will be made a child of that widget.
    context: :class:`InteractiveInterpreter` | dict
        The context where the source will be executed. If an interpreter,
        it is used as is. If a dict, a new interpreter will be created with
        the specified dict as its locals.
    historysize: int
        Maximum number of lines in the history buffer. If 0, the history
        buffer is unlimited.
    blockcount: int
        Maximum number of lines in the output buffer. If 0, the output
        buffer is unlimited.
    fontname: str
        Name of the font to be used. It better be a monospace font!
    fontsize: int
        The font size
    """
    encoding = 'utf-8'
    # text colors
    COLOR_DEFAULT = None
    COLOR_INPUT = 'blue'     # command input
    COLOR_OUTPUT = 'black'   # result output
    COLOR_ERROR = 'red'      # error messages
    # input line prompts
    PROMPT_1 = '>>> '    # single line prompt
    PROMPT_2 = '... '    # continuation line prompt

    def __init__(self, parent=None, context=dict(),
                 historysize=0, blockcount=0,
                 font="DejaVu Sans Mono", fontsize=10):
        super().__init__(parent=parent)
        self.buffer = []
        self.errorproxy = ConsoleErrorProxy(self)

        self.content = QtWidgets.QGridLayout(self)
        self.content.setContentsMargins(0, 0, 0, 0)
        self.content.setSpacing(0)

        # Display for output and stderr
        self.outdisplay = QtWidgets.QPlainTextEdit(self)
        self.outdisplay.setMaximumBlockCount(blockcount)
        self.outdisplay.setReadOnly(True)
        self.content.addWidget(self.outdisplay, 0, 0, 1, 2)

        # Display input prompt left of input edit
        self.promptdisp = QtWidgets.QLineEdit(self)
        self.promptdisp.setReadOnly(True)
        self.promptdisp.setFixedWidth(50)
        self.promptdisp.setFrame(False)
        self.content.addWidget(self.promptdisp, 1, 0)

        # Enter commands here
        self.editline = LineEdit(historysize=historysize)
        self.editline.newline.connect(self.push)
        self.editline.setFrame(False)
        self.content.addWidget(self.editline, 1, 1)

        self.lastline = ''   # buffer for last line

        self.setfont(QtGui.QFont(font, fontsize))
        self.setprompt(PyConsole.PROMPT_1)

        # Set context
        self.setcontext(context)

    def setFocus(self):
        self.editline.setFocus()

    def setcontext(self, context):
        """Set context for interpreter"""
        if isinstance(context, code.InteractiveInterpreter):
            self.interpreter = context
        else:
            self.interpreter = code.InteractiveInterpreter(context)
        self.interpreter.locals['help'] = help
        self.editline.completer = rlcompleter.Completer(self.interpreter.locals)

    def resetbuffer(self):
        """Reset the input buffer."""
        self.buffer = []

    def setprompt(self, text: str):
        self.prompt = text
        self.promptdisp.setText(text)

    def clear(self):
        self.outdisplay.clear()

    def clearall(self):
        self.editline.clearhistory()
        self.outdisplay.clear()

    def printhistory(self):
        self.editline.printhistory()

    def savehistory(self, filename):
        """Save history to a file"""
        self.editline.savehistory(filename)

    def saveoutput(self, filename, contents='all'):
        """Save the console output to a file

        Parameters
        ----------
        filename: str
            File name fir the saved output. Existing file will be overwritten.
        contents: str
            One of 'all', 'commands' or 'output'. The first character suffices.
            Determines what to write: all output, only commands, or only the
            output resulting from the commands.

        See also
        --------
        savehistory: save the command history to a file.
        """
        txt = self.outdisplay.toPlainText()
        contents = contents[:1]
        if contents == 'c':
            self.editline.savehistory(filename)
            return
        if contents == 'o':
            txt = '\n'.join([
                line for line in txt.split('\n') if not (
                    line.startswith(PyConsole.PROMPT_1) or
                    line.startswith(PyConsole.PROMPT_2))
            ])
        with open(filename, 'w') as fil:
            fil.write(txt)
            fil.write('\n')

    def push(self, line: str):
        """Execute entered command.  Command may span multiple lines"""
        lines = line.split('\n')
        if self.lastline:
            self.writecolor('\n', PyConsole.COLOR_INPUT)
        for line in lines:
            self.writecolor(self.prompt + line + '\n', PyConsole.COLOR_INPUT)
            self.setprompt(PyConsole.PROMPT_2)
            self.buffer.append(line)
        # Built a command string from lines in the buffer
        source = '\n'.join(self.buffer)
        more = self.interpreter.runsource(source, '<PyConsole>')
        if not more:
            self.setprompt(PyConsole.PROMPT_1)
            self.resetbuffer()

    def setfont(self, font: QtGui.QFont):
        """Set font for input and display widgets.  Should be monospaced"""
        self.outdisplay.setFont(font)
        self.promptdisp.setFont(font)
        self.editline.setFont(font)

    def write(self, line, color=None):
        """Capture stdout and display in outdisplay"""
        if color is None:
            color = PyConsole.COLOR_OUTPUT
        self.writecolor(line, color)

    def writeerror(self, line: str):
        """Capture stderr and display in outdisplay"""
        self.writecolor(line, PyConsole.COLOR_ERROR)

    # This should be the only method to write to the outdisplay
    def writecolor(self, text, color=None):
        """Color can be anything accepted by QColor"""
        if color is not None:
            fmt = self.outdisplay.currentCharFormat()
            if isinstance(color, (tuple, list)):
                color = QtGui.QColor.fromRgbF(*color)
            else:
                color = QtGui.QColor(color)
            fmt.setForeground(QtGui.QBrush(color))
            self.outdisplay.setCurrentCharFormat(fmt)
        lastnewline = text.rfind('\n')
        self.lastline = text[lastnewline+1:]
        self.outdisplay.insertPlainText(text)
        self.movetoend()

    def movetoend(self):
        """Move the output cursor to the end."""
        cursor = self.outdisplay.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.outdisplay.setTextCursor(cursor)
        self.outdisplay.ensureCursorVisible()

    def keyPressEvent(self, ev):
        if ev.key() == 17 and ev.modifiers() & Qt.ControlModifier: # CTRL-Q
            sys.exit()

class ConsoleErrorProxy:
    def __init__(self, console):
        self.console = console
    def write(self, s):
        self.console.writeerror(s)


if __name__ == '__main__':
    import contextlib
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QMainWindow()
    if '--qwindowgeometry' not in sys.argv[1:]:
        window.move(600,0)
        window.resize(800, 600)
    window.setWindowTitle('Python Console')
    _central = QtWidgets.QWidget(window)
    _layout = QtWidgets.QGridLayout(_central)
    console = PyConsole(context=locals())
    _layout.addWidget(console, 0, 0, 1, 1)
    window.setCentralWidget(_central)
    window.show()
    del _layout
    del _central
    console.setFocus()
    console.writecolor("** Welcome to the Python Console **\n"
                       "** (c) 2022 Benedict Verhegghe ** GPLv3 **", 'red')
    with (contextlib.redirect_stdout(console),
          contextlib.redirect_stderr(console.errorproxy)):
        sys.exit(app.exec_())

# End
