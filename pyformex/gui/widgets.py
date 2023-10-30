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
"""Widgets and dialogs for the pyFormex GUI

This module provides widgets and dialogs to easily extend the pyFormex
GUI with user defined interaction. It allows to build quite complex
dialogs with a minimal effort. Like the rest of the pyFormex GUI, it is
based on the Qt toolkit. Using this module however makes creating user
dialogs very simple, even without any knowledge of Qt.
"""
import inspect

import pyformex as pf
from pyformex import utils
from pyformex import arraytools as at
from pyformex import colors
from pyformex import gui
from pyformex.gui import signals
from pyformex.gui import image

from pyformex.path import Path
from pyformex.gui import QtCore, QtGui, QtWidgets, QPixmap, QImage
from pyformex.mydict import Dict

class ValidationError(Exception):
    """Raised in input fields that do not have an acceptable value."""
    pass

# timeout value for all widgets providing timeout feature
#  (currently: Dialog, MessageBox)

input_timeout = -1.0  # default timeout value : -1 means no timeout

def setInputTimeout(timeout):
    global input_timeout
    input_timeout = timeout

# QT List selection mode
selection_mode = {
    None: QtWidgets.QAbstractItemView.NoSelection,
    'single': QtWidgets.QAbstractItemView.SingleSelection,
    'multi': QtWidgets.QAbstractItemView.MultiSelection,
    'contiguous': QtWidgets.QAbstractItemView.ContiguousSelection,
    'extended': QtWidgets.QAbstractItemView.ExtendedSelection,
    'checked': QtWidgets.QAbstractItemView.SingleSelection,
    }

# QT File selection mode
FILE_SELECTION_MODES = [ 'file', 'exist', 'dir', 'any', 'multi' ]
# we only use the first character as key:
FILE_SELECTION_MODE = {
    'f': QtWidgets.QFileDialog.AnyFile,
    'e': QtWidgets.QFileDialog.ExistingFile,
    'd': QtWidgets.QFileDialog.Directory,
    'a': QtWidgets.QFileDialog.AnyFile,
    'm': QtWidgets.QFileDialog.ExistingFiles,
}

# icons
def standardIcon(label):
    """Load a standard Qt icon.

    Parameters
    ----------
    icon: str
        One of 'noicon', 'info', 'warning', 'error', 'question'.
        These are the standard icon strings accpted by
        QtWidgets.QMessageBox.standardIcon.

    Returns
    -------
    QIcon
        A QIcon as used by QtWidgets.QMessageBox, or the input string
        itself if it is not accepted.
    """
    try:
        icon = ['noicon', 'info', 'warning', 'error', 'question'].index(label)
        return QtWidgets.QMessageBox.standardIcon(icon)
    except Exception:
        return label


def pyformexIcon(icon):
    """Load a pyFormex icon.

    Parameters
    ----------
    icon: str
        The basename without extension of one of the image files in
        the pyformex icons directory. Only .xpm and .png image files
        are accepted.

    Returns
    -------
    QIcon
        A QIcon with an image loaded from the pyFormex icons directory.
    """
    return QtGui.QIcon(QPixmap(utils.findIcon(icon)))


def objSize(object):
    """Return the width and height of an object.

    Parameters
    ----------
    object:
        Any object that has width and height methods, for example
        :class:`QWidget` instances.

    Returns
    -------
    w: int
        The width of the object
    h: int
        The height of the object
    """
    return object.width(), object.height()


def maxWinSize():
    """Return the maximum window size.

    The returned size is the maximum size for a window on the screen.
    This may be smaller than the physical screen size: for example,
    it may exclude the space for docking panels.

    Returns
    -------
    w: int
        Maximum window width
    h: int
        Maximum window height
    """
    return objSize(pf.app.desktop().availableGeometry())


def addTimeOut(widget, timeout=None, timeoutfunc=None):
    """Add a timeout to a widget.

    This enables calling a function or a widget method after a specified
    time has elapsed.

    Parameters
    ----------
    widget: QWidget
        The widget to set the timeout function for.
    timeout: float, optional
        The time in seconds to wait before calling the timeout function.
        If None, it will be set to to the global :attr:`widgets.input_timeout`.
    timeoutfunc: callable, optional
        Function to be called after the widget times out.
        If None, and the widget has a `timeout` method, that will be used.

    Notes
    -----
    If timeout is positive, a timer is installed into the widget which
    will call the `timeoutfunc` after `timeout` seconds have elapsed.
    The `timeoutfunc` can be any callable, but usually will emit a signal
    to make the widget accept or reject the input. The timeoutfunc will not
    be called if the widget is destructed before the timer has finished.
    """
    if timeout is None:
        timeout = input_timeout
    if timeoutfunc is None and hasattr(widget, 'timeout'):
        timeoutfunc = widget.timeout

    try:
        timeout = float(timeout)
        if timeout >= 0.0:
            pf.logger.debug("Adding timeout %ss: %s" % (timeout, timeoutfunc))
            timer = QtCore.QTimer()
            timer.timeout.connect(timeoutfunc)
            timer.setSingleShot(True)
            timeout = int(1000*timeout)  # time count in milliseconds
            timer.start(timeout)
            widget.timer = timer  # make sure this timer stays alive
    except Exception:
        raise
        #raise ValueError("Could not start the timeout timer"


def setExpanding(w):
    freePol = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
    w.setSizePolicy(freePol)
    w.adjustSize()

def hspacer():
    return QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                 QtWidgets.QSizePolicy.Minimum)


def fileUrls(files):
    """Transform a list of local file names to urls"""
    return [QtCore.QUrl.fromLocalFile(str(f)) for f in files]

#####################################################################
########### General Input Dialog ####################################
#####################################################################


class InputItem(QtWidgets.QWidget):
    """A single input item in a Dialog.

    This is the base class for all input items in an Dialog.
    An InputItem in the dialog is treated as a unit and refered
    to by a single unique name.

    The InputItem class is rarely used directly. Most of the components
    of an Dialog are subclasses of it, each specialized in
    some form of input data or representation. There is e.g. an
    InputInt class to input an integer number and an InputString
    for the input of a string. The base class groups the functionality
    that is common to the different input widgets. Even the subclasses
    are seldomly used directly by the normal user. Most of the time
    an Dialog is created by just specifying the proper data using
    the helper function _I, _G, _T, _C defined in :mod:`draw`.
    See :doc:`../input-dialogs` for more guidelines.

    The InputItem widget holds a horizontal layout box (QHBoxLayout)
    to group its components. In most cases there are just two components:
    a label with the name of the field, and the actual input field.
    Other components, such as buttons or sliders, may be added. This is
    often done in subclasses.

    The constructor has one required argument: ``name``.
    The remaining are keyword parameters. Some of them are used by all
    subclasses, others are only for some subclass(es). Some of the
    parameters are handled by this base class, others are handled by the
    individual subclass. All InputItem classes use the \\*\\*kargs syntax, so
    accept all option. They just act on the useful ones.

    For reference, we add here the full list of keyword options in use.

    Parameters
    ----------
    name: str
        The name used to identify the item. It should be unique for
        all InputItems in the same Dialog. It is used as a key in
        the dictionary that returns all the input values in the dialog.
        It is also the default label displayed in front of the input
        field if no ``text`` is specified.
    value: data
        The initial value of the field. The data type is dependent
        on the itemtype. In simple cases the data type will
        determine the itemtype if it is not specified: int, float,
        str. Required in most cases, though some itemtypes have a default
        value (see ``choices``).
    itemtype: str
        The type of input field. This will determine the type
        of data to be specified as value, the type of data returned,
        and the subclass of InputItem used to accept the data. For a
        string 'abc' the subclass used is InputAbc.
    text: str | QPixmap
        A text string or icon that is displayed next to the input area,
        instead of the default name.
        Use this field to display a more descriptive text for the user,
        while using a short name for handling the return value.
        Set it to an empty string to suppress the creation of a label.
        This is useful if the input field widget itself already provides
        a label (see InputBool).
    tooltip: str
        A string that will be shown when the user hovers the mouse over the
        InputItem widget. It can be used to give more comprehensive
        explanation to first time users.
    choices: list
        A list of strings which are options to choose from. If specified
        and no itemtype is given, the options are presented as a combo box.
        Alternatively, one can use itemtype 'hradio', 'vradio', or 'push'.
        If choices are given and no value is specified, the default value
        is set to the first item in the choices list. If a value is given
        that does not appear in choices, the value will be added as the
        first option in choices.
    min: data
        The minimum value for the data to be entered. Useful with 'int' and
        'float' types. If specified, you will not be able to return a lower
        value.
    max: data
        The maximum value for the data to be entered. Useful with 'int' and
        'float' types. If specified, you will not be able to return a higher
        value.
    func: callable
        A callable taking an InputItem as parameter.
        If specified, it is called whenever the value of the item is
        changed. Many InputItems support this feature. Some even require it.
        From the passed InputItem, all information about the item and even
        the whole dialog (through its parent attribute) can be accessed.
    data: data
         Any extra data that you want to be stored into the widget.
         These data are not displayed, but can be useful in the functioning of
         the widget (for example as extra information for ``func``).
    enabled: bool
         If False, the InputItem will not be enabled, meaning that the user
         can not enter or change any values there. Disabled fields are usually
         displayed in a greyed-out fashion. Default is True.
    readonly: bool
         If True, the data are read-only and can not be changed by the user.
         Unlike disabled items, they are displayed in a normal fashion.
         Default is False.
    spacer: str
         Only the characters 'l', 'r' and 'c' are relevant.
         If the string contains an 'l', a spacer is inserted before the label.
         If the string contains an 'r', a spacer in inserted after the input
         field. If the string contains a 'c', a spacer in inserted between
         the label and the input filed.
    width: int
         The minimum width in pixels of the input field
    buttons: a list of (label,function) tuples. For each tuple a button
      will be added after the input field. The button displays the text and
      when pressed, the specified function will be executed. The function
      takes no arguments.

    Notes
    -----

    Subclasses should have an ``__init__()`` method which first constructs
    a proper widget for the input field, and stores it in the attribute
    ``self.input``. Then the baseclass should be properly initialized, passing
    it the name and any optional parameters::

      self.input = SomeInputWidget()
      super().__init__(name, **kargs)

    Subclasses should also override the following default methods of
    the InputItem base class:

    - text(): if the subclass calls the superclass __init__() method with
      a value ``text=''``. This method should return the value of the
      displayed text.
    - value(): if the value of the input field is not given by
      ``self.input.text()``, i.e. in most cases. This method should
      return the value of the input field. In many cases this is different
      from the string displayed in the input field. Thus an InputInt
      should return an int. If the currenttly displayed input can not be
      validated, a ValidationError should be raised.
    - setValue(val): always, unless the field is readonly. This method should
      change the value of the input widget to the specified value.

    Subclasses are allowed to NOT have a ``self.input`` attribute, IFF they
    redefine both the value() and the setValue() methods.

    Subclasses can set validators on the input, like::

      self.input.setValidator(QtGui.QIntValidator(self.input))

    Subclasses can define a show() method e.g. to select the data in the
    input field on display of the dialog.
    """

    autoname = utils.autoName('item')

    def __init__(self, name, **kargs):
        """Create a widget with a horizontal box layout"""
        if not hasattr(self,'input'):
            raise ValueError("Subclass should define self.input before"
                             " calling superclass initialization")
        super().__init__()
        self.error = None

        # set the layout
        layout = QtWidgets.QHBoxLayout()
        s = pf.cfg['gui/spacing']
        layout.setContentsMargins(s, s, s, s)
        self.setLayout(layout)

        # Key for return value
        self.key = str(name)

        # Create the label
        if 'text' in kargs and kargs['text'] is not None:
            text = kargs['text']
        else:
            text = self.key
        if text:
            self.label = QtWidgets.QLabel()
            #text = standardIcon(text)
            if isinstance(text, QPixmap):
                self.label.setPixmap(text)
            else:
                self.label.setText(text)
        else:
            self.label = None

        # Insert the label and input widgets, possibly with spacers
        spacer = kargs.get('spacer', '')
        if 'l' in spacer:
             layout.addItem(hspacer())

        if self.label:
            layout.addWidget(self.label)
            if 'c' in spacer:
                layout.addItem(hspacer())

        layout.addWidget(self.input)
        if 'r' in spacer:
             layout.addItem(hspacer())

        # Install callback function
        self.func = None
        if 'func' in kargs and callable(kargs['func']):
            self.func = kargs['func']

        if 'data' in kargs:
            self.data = kargs['data']

        if 'enabled' in kargs:
            self.setEnabled(kargs['enabled'])

        if 'readonly' in kargs:
            try:
                self.input.setReadOnly(kargs['readonly'])
            except Exception:
                print("Can not set readonly: %s,%s" % (name, kargs))

        if 'width' in kargs:
            try:
                self.input.setMinimumWidth(kargs['width'])
            except Exception:
                pass

        if 'tooltip' in kargs:
            self.setToolTip(kargs['tooltip'])

        if 'buttons' in kargs:
            buttons = kargs['buttons']
            if isinstance(buttons, dict):
                self.buttons = ButtonBox(parent=self, **buttons)
            elif isinstance(buttons, list):
                self.buttons = ButtonBox('', actions=buttons, parent=self)
            layout.addWidget(self.buttons)


    def showError(self, show, msg=''):
        if self.error is None:
            if show:
                self.error = QtWidgets.QPushButton()
                icon_name = 'SP_MessageBoxCritical'
                icon = self.style().standardIcon(getattr(QtWidgets.QStyle, icon_name))
                self.error.setIcon(icon)
                self.error.setToolTip(msg)
                pos = self.layout().indexOf(self.input)
                self.layout().insertWidget(pos,self.error)
        else:
            self.error.setToolTip(msg)
            if show:
                self.error.show()
            else:
                self.error.hide()

    def dialog(self):
        """Return the :class:`Dialog` to which this InputItem belongs

        Returns
        -------
        Dialog
            The Dialog this item is part of, or None if the
            InputItem was not constructed as part of a Dialog.
        """
        dia = self
        while dia is not None:
            if isinstance(dia, Dialog):
                break
            dia = dia.parent()
        return dia

    def name(self):
        """Return the name of the InputItem."""
        return self.key

    def text(self):
        """Return the displayed text of the InputItem."""
        if hasattr(self, 'label'):
            return str(self.label.text())
        else:
            return self.key

    def value(self):
        """Return the widget's value."""
        return str(self.input.text())

    def setValue(self, val):
        """Change the widget's value."""
        self.input.setText(str(val))

    def on_value_change(self, **kargs):
        """Call the installed func with self as parameter"""
        if self.func:
            self.func(self)


class InputLabel(InputItem):
    """An unchangeable information field.

    Unlike the other InputItem subclasses, this is actually not an input
    widget and also does not return a value.
    It is mostly used to present information to the user.

    Parameters
    ----------
    name: str
        The name of the field.
    value: str
        The contents to be displayed. This may be plain text, html or
        reStructuredText. The latter is detected if it starts with a
        line containing two dots, followed with an empty line.
        It is converted to html before being displayed.
    """
    def __init__(self, name, value, format='', **kargs):
        """Initialize the input item."""
        if value is None:
            value = ''
        self.input = QtWidgets.QLabel()
        self.input.setText(utils.convertText(value, format)[0])
        super().__init__(name, **kargs)

    def value(self):
        return None


class InputInfo(InputItem):
    """An unchangeable input field.

    It is just like an :class:`InputString`, but the text can not be edited.
    The value should be a simple string without newlines.

    Parameters
    ----------
    name: str
        The name of the field.
    value: str
        The string to be displayed and returned as a value.
    """
    def __init__(self, name, value, **kargs):
        """Initialize the input item."""
        if value is None:
            value = ''
        self.input = QtWidgets.QLineEdit(str(value))
        kargs['readonly'] = True
        super().__init__(name, **kargs)


class InputString(InputItem):
    """An editable string input field.

    Parameters
    ----------
    name: str
        The name of the field.
    value: str | object
        The initial value of the InputItem. This is normally a string type.
        If not, it is converted to a string before displaying, and the
        displayed string will be eval'ed before returning its value.
        This allows e.g for editing compound objects like tuples and lists.
    max: int, optional
        If specified, the displayed string can not be made longer than this
        number of characters.
    """
    def __init__(self, name, value, max=None, **kargs):
        """Initialize the input item."""
        self.input = QtWidgets.QLineEdit(str(value))
        super().__init__(name, **kargs)
        if isinstance(max, int) and max > 0:
            self.input.setMaxLength(max)
        self._is_string_ = isinstance(value, str)
        if self.func:
            self.input.textChanged.connect(self.on_value_change)


    def show(self, *args):
        InputItem.show(self, *args)
        # Select all text on first display.
        self.input.selectAll()

    def value(self):
        """Return the widget's value."""
        s = str(self.input.text())
        if not self._is_string_:
            try:
                s = eval(s)
            except Exception as e:
                raise ValidationError(
                    "Input should be a valid Python expression")
        return s


class InputText(InputItem):
    """A scrollable text input field.

    Shows a multiline text in the input field. Rich text formats (html, rst)
    can be displayed in nice rendering mode.

    Parameters
    ----------
    name: str
        The name of the field.
    value: str
        The text to be displayed. Rich text formats (html, rst) can be
        displayed in nice rendering mode (at the expense of not being editable).
    format: str, optional
        The format of the text: 'plain', 'html' or 'rst'. The default is to use
        autodetection. ReStructuredText is detected if text start with '..'.
        Specify format='plain' to force display in plain text and make rich
        text formats editable.
    ret_format: str, optional
        The format of the return value: 'plain' or 'html'. The default is
        'plain'. 'rst' can not yet be returned.
    """
    def __init__(self, name, value, format='', ret_format='plain', **kargs):
        """Initialize the input item."""
        self._is_string_ = isinstance(value, str)
        self._format = format
        self.input =  QtWidgets.QTextEdit()
        if ret_format == 'markdown' and not hasattr(self.input, 'toMarkdown'):
            # Early Qt versions didn't support markdown
            ret_format = 'plain'
        self._retformat = ret_format
        setExpanding(self.input)
        super().__init__(name, **kargs)
        self.setValue(value)
        if 'font' in kargs:
            try:
                self.setFont(QtGui.QFont(kargs['font']))
            except Exception:
                pass
        if 'size' in kargs:
            self._size = kargs['size']

    def sizeHint(self):
        if hasattr(self, '_size'):
            width, height = self._size
            docsize = self.input.document().size().toSize()
            #print(f"docsize = {docsize}")
            font = self.input.font()
            if width < 0:
                width = max(80 * font.pixelSize(), 50* font.pointSize())
            if height < 0:
                height = docsize.height() + (
                    self.input.height() - self.input.viewport().height())
                height = max(height, 0.75*width)
            size = QtCore.QSize(width, height)
        else:
            size = QtWidgets.QTextEdit.sizeHint(self.input)
        return size

    def show(self, *args):
        InputItem.show(self, *args)
        # Select all text on first display.
        self.input.selectAll()

    def value(self):
        """Return the widget's value."""
        if self._retformat == 'html':
            s = self.input.toHtml()
        elif self._retformat == 'markdown':
            s = self.input.toMarkdown()
        else:
            s = self.input.toPlainText()

    def setValue(self, val):
        """Change the widget's value."""
        text, format = utils.convertText(str(val))
        if format == 'markdown' and hasattr(self.input, 'setMarkdown'):
            self.input.setMarkdown(text)
        elif format == 'html':
            self.input.setHtml(text)
        else:
            self.input.setPlainText(text)
        self.input.adjustSize()


class InputBool(InputItem):
    """A boolean input item.

    Creates a checkbox for the input of a boolean value.

    Parameters
    ----------
    name: str
        The name of the field.
    value: bool
        The initial value. If True, the checkbox is checked upon display.
    func: callable
        Called with then InputBool as parameter whenever the value is changed.
    """

    def __init__(self, name, value, **kargs):
        """Initialize the input item."""
        if 'text' in kargs:
            text = kargs['text']
        else:
            text = str(name)
        kargs['text'] = ''  # Force no label
        self.input = QtWidgets.QCheckBox(text)
        super().__init__(name, **kargs)
        self.setValue(value)
        if 'func' in kargs:
            self.input.stateChanged.connect(self.on_value_change)

    def text(self):
        """Return the displayed text."""
        return str(self.input.text())

    def value(self):
        """Return the widget's value."""
        return self.input.checkState() == QtCore.Qt.Checked

    def setValue(self, val):
        """Change the widget's value."""
        if val:
            self.input.setCheckState(QtCore.Qt.Checked)
        else:
            self.input.setCheckState(QtCore.Qt.Unchecked)


class InputSelect(InputItem):
    """An InputItem to select from a list of choices.

    InputSelect allows the selection of zero, one or more
    items from a list of choices.

    Parameters
    ----------
    name: str
        The name of the field.
    value: list of str
        The initially selected choices. Values that are not in the choices
        list are ignored. Default is an empty list.
    choices: list of str
        The list of possible choices.
    single: bool
        If True, only a single item can be selected. Default False.
    maxh: int
        If -1, the widget has a fixed height that holds all the items in the
        list. This is the default and works well for small lists.
        If 0, the widget will try to show all the items, but gets scrollbars if
        the space is not sufficient. With maxh>0, the widget will show
        exactly this number of items, and provide scrollbars to show the rest.
    check: bool, optional
        Default False. If True, all items have a checkbox and only the checked
        items are returned. This option forces single==False.
    fast_sel: bool, optional
        Default False. If True, two extra buttons are added to the InputItem,
        to select or deseledt all options at once.

    See Also
    --------
    InputCombo: select exactly one value from a list of choices
    """
    def __init__(self, name, value=[], choices=[], sort=False, single=False,
                 check=False, fast_sel=False, maxh=-1, **kargs):
        """Initialize the input item."""
        if not isinstance(choices, (list,tuple)):
            raise ValueError("Choices should be a list or tuple")
        # if len(choices) == 0:
        #     raise ValueError("List of choices should not empty.")
        self._choices_ = [str(s) for s in choices]
        self.input = ListWidget(maxh=maxh)

        if fast_sel:
            but = [('Select All', self.setAll), ('Deselect All', self.setNone)]
            if 'buttons' in kargs and kargs['buttons']:
                kargs['buttons'].extend(but)
            else:
                kargs['buttons'] = but
        super().__init__(name, **kargs)
        self.input.addItems(self._choices_)
        if sort:
            self.input.sortItems()

        mode = 'extended'
        self._check_ = check
        if check:
            mode = None
            single = False
        if single:
            mode = 'single'

        self.input.setSelectionMode(selection_mode[mode])
        self.setValue(value)

        self.input.setSize()
        if maxh > -1:
            # TODO: move this to InputItem
            pos = self.layout().indexOf(self.input)
            self.layout().removeWidget(self.input)
            self.scroll = QtWidgets.QScrollArea()
            if maxh > 0:
                self.scroll.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                          QtWidgets.QSizePolicy.Expanding)
            else:
                self.scroll.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                          QtWidgets.QSizePolicy.Maximum)
            self.scroll.setBackgroundRole(QtGui.QPalette.Dark)
            self.scroll.setWidgetResizable(False)
            self.scroll.setWidget(self.input)
            self.layout().insertWidget(pos, self.scroll)

        self.updateGeometry()

    def setSelected(self, selected, flag=True):
        """Mark the specified items as selected or not."""
        for s in selected:
            for i in self.input.findItems(s, QtCore.Qt.MatchExactly):
                i.setSelected(flag)

    def setChecked(self, selected, flag=True):
        """Mark the specified items as checked or not."""
        if flag:
            qtflag = QtCore.Qt.Checked
        else:
            qtflag = QtCore.Qt.Unchecked

        for s in selected:
            for i in self.input.findItems(s, QtCore.Qt.MatchExactly):
                i.setCheckState(qtflag)

    def getSelected(self):
        return [str(i.text()) for i in self.input.selectedItems()]

    def getChecked(self):
        return [str(i.text()) for i in self.input.allItems()
                if i.checkState()==QtCore.Qt.Checked]

    def value(self):
        """Return the widget's value."""
        if self._check_:
            f = self.getChecked
        else:
            f = self.getSelected
        return f()

    def setValue(self, val):
        """Change the widget's value."""
        if self._check_:
            f = self.setChecked
        else:
            f = self.setSelected
        f(val, True)
        f([i for i in self._choices_ if i != val], False)

    def setAll(self):
        """Mark all items as selected/checked."""
        self.setValue(self._choices_)

    def setNone(self):
        """Mark all items as not selected/checked."""
        self.setValue([])


class InputCombo(InputItem):
    """A combobox InputItem.

    A combobox allows the selection of a single item from a drop down list.

    choices is a list/tuple of possible values.
    If value is not in the choices list, it is prepended.

    The choices are presented to the user as a combobox, which will
    initially be set to the default value.

    Parameters
    ----------
    name: str
        Name of the field.
    value: bool
        The initially selected value. In not specified, the first item
        of choices is used.
    choices: list
        A list of strings which are the options to choose from. If value
        is not in the list, it is prepended.
    func: callable, optional
        A callable taking a single argument. If specified, the
        function will be called with the InputItem as parameter
        whenever the current selection changes.

    Notes
    -----
    For compatibility, 'onselect' is still accepted as alias for 'func',
    but is deprecated.

    See Also
    --------
    InputRadio: alternate single selection widget using radio buttons
    InputPush: alternate single selection widget using push buttons
    InputSelect: selection widget allowing zero, one or more selected items

    """

    def __init__(self, name, value, choices=[], func=None, **kargs):
        """Initialize the input item."""
        try:
            choices = list(choices)
        except Exception:
            raise ValueError(
                "Choices should be a list or tuple, got %s" % type(choices))
        if 'onselect' in kargs:
            utils.warn("warn_inputcombo_onselect")
            func = kargs['onselect']
        if len(choices) == 0:
            raise ValueError("List of choices should not empty.")
        if value is None:
            value = choices[0]
        if value not in choices:
            choices[0:0] = [value]
        self.input = QtWidgets.QComboBox()
        super().__init__(name, func=func, **kargs)
        self._choices_ = []
        self.setChoices(choices)
        if self.func:
            self.input.currentTextChanged.connect(self.on_value_change)
        self.setValue(value)

    def value(self):
        """Return the widget's value."""
        return str(self.input.currentText())

    def setValue(self, val):
        """Change the widget's current value."""
        val = str(val)
        if val in self._choices_:
            self.input.setCurrentIndex(self._choices_.index(val))

    def setChoices(self, choices):
        """Change the widget's choices.

        This also sets the current value to the first in the list.
        """
        # First remove old choices, if any
        while self.input.count() > 0:
            self.input.removeItem(0)
        # Set new ones
        self._choices_ = [str(s) for s in choices]
        self.input.addItems(self._choices_)

    def setIndex(self, i):
        self.input.setCurrentIndex(i)


class InputRadio(InputItem):
    """A radiobuttons InputItem.

    Radio buttons are a set of buttons used to select a value from a list.

    Parameters
    ----------
    name: str
        Name of the field.
    value: bool
        The initially selected value. In not specified, the first item
        of choices is used.
    choices: list
        A list of strings which are the options to choose from. If value
        is not in the list, it is prepended.
    direction: 'h' | 'v'
        The default 'h' displays the radio buttons in a horizontal box.
        Specifying 'v' puts them in a vertical box.

    See Also
    --------
    InputCombo: alternate selection widget using a combo box
    InputPush: alternate selection widget using push buttons
    InputSelect: selection widget allowing zero, one or more selected items
    """

    def __init__(self, name, value, choices=[], direction='h', **kargs):
        """Initialize the input item."""
        try:
            choices = list(choices)
        except Exception:
            raise ValueError(
                "Choices should be a list or tuple, got %s" % type(choices))
        if len(choices) == 0:
            raise ValueError("List of choices should not empty.")
        if value is None:
            value = choices[0]
        elif value not in choices:
            choices[0:0] = [value]
        self.input = QtWidgets.QGroupBox()
        super().__init__(name, **kargs)
        if direction == 'v':
            self.box = QtWidgets.QVBoxLayout()
            self.box.setContentsMargins(0, 10, 0, 10)
        else:
            self.box = QtWidgets.QHBoxLayout()
            self.box.setContentsMargins(10, 0, 10, 0)
        self.rb = []
        self.box.addStretch(1)

        for v in choices:
            rb = QtWidgets.QRadioButton(v)
            self.box.addWidget(rb)
            self.rb.append(rb)

        self.rb[choices.index(value)].setChecked(True)
        self.input.setLayout(self.box)

    def value(self):
        """Return the widget's value."""
        for rb in self.rb:
            if rb.isChecked():
                return str(rb.text())
        return ''

    def setValue(self, val):
        """Change the widget's value."""
        val = str(val)
        for rb in self.rb:
            if rb.text() == val:
                rb.setChecked(True)
                break


class InputPush(InputItem):
    """A push buttons InputItem.

    Use push buttons to select of a value from a list of choices.
    The choices are presented to the user as a box with mutually
    exclusive push buttons. The buttons can display a text, an icon
    or both.

    Parameters
    ----------
    name: str
        Name of the item.
    value: str, optional
        The initially selected value.
        If not specified, it is set to the first item of ``choices``.
    choices: list, optional
        The list of possible values. If ``value`` is specified and not
        contained in ``choices``, it is prepended to it. If not specified,
        it is set to a list containing only the specified ``value``.
    func: callable, optional
        A function that will be called whenever the currently selected value
        is changed.
    icons: list, optional
        List of icon names to display on the buttons. The list should have
        the same length as choices. A None may be used for buttons that do
        not need an icon.
    iconsonly: bool, optional
        If True, only the icons are displayed on the buttons. The default
        False will display both text and icon.
    direction: 'h' | 'v', optional
        By default the buttons are grouped in a horizontal box.
        Specifying 'v' will order the buttons vertically.
    count: int, optional
        The maximum number of buttons to display in the main ordering
        direction.
    small: bool, optional
        If True, small buttons are used instead of the normal ones. This may
        be a good option if you have a lot of choices.
    func: callable
        The function to call when the button is clicked. The function
        receives the input field as argument. From this argument, the field's
        attributes like name, value(), text, can be retrieved.
        The function should return the value to be set, or None if it is to be
        unchanged. If no function is specified, the value can not be changed.

    Raises
    ------
    ValueError: If neither value nor choices are specified.

    See Also
    --------
    InputCombo: alternate selection widget using a combo box
    InputRadio: alternate selection widget using radio buttons
    InputSelect: selection widget allowing zero, one or more selected items

    """
    def __init__(self, name, value=None, choices=[], func=None, icons=None,
                 iconsonly=False, direction='h', count=0,
                 small=False, **kargs):
        """Initialize the input item."""
        value, choices = Dialog.sanitize_value_choices(value, choices)
        self.input = QtWidgets.QWidget()
        # The vertical layouts do not seem to work in a simple QWidget
        #self.input = QtWidgets.QGroupBox()
        #self.input.setFlat(True)
        #self.input.setStyleSheet("QGroupBox { border: 0px;}")
        super().__init__(name, func=func, **kargs)
        if direction[0] == 'v' and count <= 0:
            self.box = QtWidgets.QVBoxLayout()
            self.box.setContentsMargins(0, 10, 0, 10)
        elif direction[0] == 'h' and count <= 0:
            self.box = QtWidgets.QHBoxLayout()
            self.box.setContentsMargins(2, 0, 2, 0)
        else:
            self.box = QtWidgets.QGridLayout()
        self.box.setSpacing(0)

        self.bg = QtWidgets.QButtonGroup()
        self.choices = choices
        for i, v in enumerate(choices):
            if small:
                b = QtWidgets.QToolButton()
            else:
                b = QtWidgets.QPushButton()
                b.setAutoDefault(False)

            if not iconsonly:
                b.setText(v)

            b.setCheckable(True)
            if icons and icons[i]:
                b.setIcon(pyformexIcon(icons[i]))

            if v == value:
                b.setChecked(True)

            if self.func:
                b.clicked.connect(self.on_value_change)

            self.bg.addButton(b, i)

            if count <= 0:
                self.box.addWidget(b)
            else:
                r, c = divmod(i, count)
                self.box.addWidget(b, r, c)

        self.input.setLayout(self.box)

    def setText(self, text, index=0):
        """Change the text on button index."""
        self.bg.button(index).setText(text)

    def setIcon(self, icon, index=0):
        """Change the icon on button index."""
        if isinstance(icon, str):
            icon = pyformexIcon(icon)
        self.bg.button(index).setIcon(icon)

    def checkedId(self):
        """Return the number of the checked button"""
        return self.bg.checkedId()

    def value(self):
        """Return the widget's value."""
        return self.choices[self.bg.checkedId()]

    def setValue(self, val):
        """Change the widget's value."""
        val = str(val)
        for b in self.bg.buttons():
            b.setChecked(b.text() == val)


class InputInt(InputItem):
    """An integer input item.

    A text edit widget allowing to enter an integer number.

    Parameters
    ----------
    name: str
        Name of the item.
    value: int
        The initially value.
    min: int, optional
        If specified, this is the lowest acceptable value.
    max: int, optional
        If specified, this is the highest acceptable value.
    """

    def __init__(self, name, value, **kargs):
        """Initialize the input item."""
        self.input = QtWidgets.QLineEdit(str(value))
        super().__init__(name, **kargs)
        self.validator = QtGui.QIntValidator(self)
        if 'min' in kargs:
            self.validator.setBottom(int(kargs['min']))
        if 'max' in kargs:
            self.validator.setTop(int(kargs['max']))
        self.input.setValidator(self.validator)

    def show(self):
        InputItem.show(self)
        # Select all text on first display
        self.input.selectAll()

    def value(self):
        """Return the widget's value."""
        txt = self.input.text()
        valid = self.validator.validate(txt, 0)
        if valid[0] != QtGui.QValidator.State.Acceptable:
            raise ValidationError(
                f"Input should be an int in the range "
                f"({self.validator.bottom()} to {self.validator.top()})")
        return int(txt)

    def setValue(self, val):
        """Change the widget's value."""
        val = int(val)
        self.input.setText(str(val))


class InputFloat(InputItem):
    """A float input item.

    A text edit widget allowing to enter an integer number.

    Parameters
    ----------
    name: str
        Name of the item.
    value: float
        The initially value.
    min: float, optional
        If specified, this is the lowest acceptable value.
    max: float, optional
        If specifieid, this is the highest acceptable value.
    dec: int, optional
        If specified, the maximum number of decimal digits.
    """
    def __init__(self, name, value, **kargs):
        """Initialize the input item."""
        self.validator = QtGui.QDoubleValidator()
        if 'dec' in kargs:
            dec = int(kargs['dec'])
            self.validator.setDecimals(dec)
            value = round(value, dec)
        if 'min' in kargs:
            min = float(kargs['min'])
            self.validator.setBottom(min)
            if value < min:
                value = min
        if 'max' in kargs:
            max = float(kargs['max'])
            self.validator.setTop(max)
            if value > max:
                value = max
        self.input = QtWidgets.QLineEdit(str(value))
        self.input.setValidator(self.validator)
        super().__init__(name, **kargs)

    def show(self):
        InputItem.show(self)
        # Select all text on first display
        self.input.selectAll()

    def value(self):
        """Return the widget's value."""
        txt = self.input.text()
        valid = self.validator.validate(txt, 0)
        if valid[0] != QtGui.QValidator.State.Acceptable:
            raise ValidationError(
                f"Input should be a float in the range "
                f"({self.validator.bottom()} to {self.validator.top()})")
        return float(txt)

    def setValue(self, val):
        """Change the widget's value."""
        val = float(val)
        self.input.setText(str(val))


class InputSlider(InputInt):
    """An integer input item with a slider.

    An InputInt with an added slider to change the value.

    Parameters
    ----------
    name: str
        Name of the item.
    value: int
        The initial value.
    min: int, optional
        The lowest acceptable value. Default 0.
    max: int, optional
        The highest acceptable value. Default 100.
    ticks: int, optional
        The step length between ticks on the slider. Default is
        (max-min)//10.
    func: callable, optional
        Function called whenever the value is changed.
    tracking: bool, optional
        If True (default), func is called repeatedly while the slider is
        being dragged. If False, func is only called when the user releases
        the slider.
    """

    def __init__(self, name, value, **kargs):
        """Initialize the input item."""
        super().__init__(name, value, **kargs)
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)

        vmin = kargs.get('min', 0)
        vmax = kargs.get('max', 100)
        ticks = kargs.get('ticks', (vmax-vmin)//10)
        tracking = kargs.get('tracking', True)

        self.slider.setTickInterval(ticks)
        self.slider.setMinimum(vmin)
        self.slider.setMaximum(vmax)
        self.slider.setValue(value)
        self.slider.setSingleStep(1)
        self.slider.setTracking(tracking)
        self.slider.valueChanged.connect(self.set_value)
        self.layout().addWidget(self.slider, stretch=2)

    def set_value(self, val):
        val = int(val)
        self.input.setText(str(val))
        if self.func:
            self.func(self)


class InputFSlider(InputFloat):
    """A float input item with a slider.

    An InputFloat with an added slider to change the value.

    Parameters
    ----------
    name: str
        Name of the item.
    value: int
        The initial value.
    min: int, optional
        The lowest acceptable value for the slider. Default 0.
    max: int, optional
        The highest acceptable value for the slider. Default 100.
    scale: float, optional
        The scale factor to compute the float value from the
        integer slider value. Default is 1.0.
    ticks: int, optional
        The step length between ticks on the slider. Default is
        (max-min)//10.
    func: callable, optional
        Function called whenever the value is changed.
    tracking: bool, optional
        If True (default), func is called repeatedly while the slider is
        being dragged. If False, func is only called when the user releases
        the slider.
    """

    def __init__(self, name, value, **kargs):
        """Initialize the input item."""
        super().__init__(name, value, **kargs)
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.scale = kargs.get('scale', 1.0)
        vmin = kargs.get('min', 0.) / self.scale
        vmax = kargs.get('max', 100.) / self.scale
        dec = kargs.get('dec', 6)
        ticks = kargs.get('ticks', int(round((vmax-vmin)/10)))
        stretch = kargs.get('stretch', 1)
        tracking = kargs.get('tracking', True)

        self.slider.setTickInterval(ticks)
        self.slider.setMinimum(int(round(vmin)))
        self.slider.setMaximum(int(round(vmax)))
        self.slider.setValue(int(round(value/self.scale)))
        self.slider.setSingleStep(1)
        self.slider.setTracking(tracking)
        self.slider.valueChanged.connect(self.set_value)
        self.layout().addWidget(self.slider, stretch=stretch)


    def set_value(self, val):
        val = float(val)
        value = val*self.scale
        value = round(value, self.validator.decimals())
        #pf.debug("  fslider: %s = %s" % (val, value), pf.DEBUG.GUI)
        self.input.setText(str(value))
        if self.func:
            self.func(self)


class InputTable(InputItem):
    """An input item for tabular data.

    Parameters
    ----------
    name: str
        Name of the item.
    value: :term:`array_like`
        A 2-D array of items, with `nrow` rows and `ncol` columns.

        If it is an NumPy array, InputTable will use the ArrayModel:
        editing the data will directly change the input data array; all
        items are of the same type; the size of the table can not be changed.

        Else a TableModel is used. Rows and columns can be added to or removed
        from the table. Item type can be set per row or per column or for the
        whole table.
    chead: list, optional
        List of column headers
    rhead: list, optional
        List of row headers
    celltype:
    rowtype:
    coltype:
    edit: bool
    resize:
    autowidth:
    **kargs:
        Aditionally, all keyword parameters of the TableModel or ArrayModel
        may be passed
    """

    def __init__(self, name, value, chead=None, rhead=None, celltype=None,
                 rowtype=None, coltype=None, edit=True, resize=None,
                 autowidth=True, **kargs):
        """Initialize the input item."""
        self.input = Table(value, chead=chead, rhead=rhead, celltype=celltype,
                           rowtype=rowtype, coltype=coltype, edit=edit,
                           resize=resize, autowidth=autowidth)
        super().__init__(name, **kargs)
        self.layout().addWidget(self.input)


    def value(self):
        """Return the widget's value."""
        return self.input.value()

    # TODO: need to implement
    ## def setValue(self,val):
    ##     """Change the widget's value."""
    ##     self.input.setText(str(val))


class InputPoint(InputItem):
    """A 2D or 3D point or vector input item.

    An input field holding a :class:`CoordsBox` widget.
    The default gives fields x, y and z. With ndim=2, only x and y.

    Parameters
    ----------
    name: str
        Name of the item.
    value: list of float
        A list of two or three floats that are the initial values of the
        vector components. The dimension of the vector is determined from
        the length.
    """

    def __init__(self, name, value, **kargs):
        """Initialize the input item."""
        self.input = CoordsBox(ndim=len(value))
        super().__init__(name, **kargs)
        self.setValue(value)

    def value(self):
        """Return the widget's value."""
        return self.input.getValues()

    def setValue(self, val):
        """Change the widget's value."""
        self.input.setValues(val)


class InputIVector(InputItem):
    """A vector of int values.

    Parameters
    ----------
    name: str
        Name of the item.
    value: list of int
        The initial values of the integers in the list. The values can
        be changed, but no values can be added or deleted.

    """

    def __init__(self, name, value, **kargs):
        """Initialize the input item."""
        self.ndim = len(value)
        if 'fields' in kargs:
            fields = kargs['fields']
        else:
            fields = [str(i) for i in range(self.ndim)]

        self.input = QtWidgets.QWidget()
        super().__init__(name, **kargs)

        # TODO: allow self.input to be a list
        # TODO: pass min,max to InputInt
        layout = self.layout()
        self.fields = []
        for fld, val in zip(fields, value):
            f = InputInt(fld, val)
            self.fields.append(f)
            layout.addWidget(f)

    def value(self):
        """Return the widget's value."""
        return [f.value() for f in self.fields]

    def setValue(self, val):
        """Change the widget's value."""
        for f, v in zip(self.fields, val):
            f.setValue(v)


class InputButton(InputItem):
    """A button input item.

    The button input field is a button displaying the current value.
    Clicking on the button executes a function responsible for changing
    the value.

    Parameters
    ----------
    name: str
        Name of the item.
    value: str
        Text to display on the button
    func: callable
        A function to be called when the button is clicked. The function
        receives the InputItem as argument. From this argument, the fields
        attributes like name, value, text, can be retrieved.

    """
    # Revived from deprecation
    # @utils.deprecated_by('InputButton', 'InputPush')
    def __init__(self, name, value, **kargs):
        """Initialize the input item."""
        value = str(value)
        self.input = QtWidgets.QPushButton(value)
        super().__init__(name, **kargs)
        self.setValue(value)
        if self.func:
            self.input.clicked.connect(self.on_value_change)


# TODO: This could be subclassed from InputButton
class InputColor(InputItem):
    """A color input item.

    An InputItem specialized in selecting a color.
    The input field is a button displaying the current color.
    Clicking on the button opens a color dialog, and the returned color
    value is set in the button.

    Parameters
    ----------
    name: str
        Name of the item.
    value: :term:`color_like`
        The initial color.
    """
    def __init__(self, name, value, **kargs):
        """Initialize the input item."""
        if value is None:
            value = 'black'
        color = colors.colorName(value)
        self.input = QtWidgets.QPushButton(color)
        super().__init__(name, **kargs)
        self.setValue(color)
        self.input.clicked.connect(self.setColor)

    def setColor(self):
        self.initial = QtGui.QColor(self.input.text())
        dia = QtWidgets.QColorDialog(self.initial, self)
        dia.setOption(QtWidgets.QColorDialog.DontUseNativeDialog, True)
        dia.currentColorChanged.connect(self.set_value)
        dia.rejected.connect(self.reset_value)
        dia.open()

    def reset_value(self):
        self.set_value(self.initial)

    def set_value(self, val):
        color = colors.colorName(val)
        self.setValue(color)
        if self.func:
            self.func(self)

    def setValue(self, value):
        """Change the widget's value."""
        col = QtGui.QColor(value)
        col = colors.RGBcolor(col)
        lc = colors.luminance(col)
        if lc < 0.40:
            tcol = colors.white
        else:
            tcol = colors.black
        tcol = colors.RGBcolor(tcol)
        self.input.setStyleSheet(
            "* { background-color: rgb(%s,%s,%s); color: rgb(%s,%s,%s) }" %
            (tuple(col)+tuple(tcol)))
        self.input.setText(str(value))


class InputFont(InputItem):
    """An input item to select a font.

    An InpuItem specialized in selecting a font.
    The input field is a button displaying the current text font.
    Clicking on the button opens a font dialog, and the returned font name
    is displayed in the button.

    Parameters
    ----------
    name: str
        Name of the item.
    value: str
        The initial font name.
    """
    def __init__(self, name, value, **kargs):
        """Initialize the input item."""
        if value is None:
            value = pf.app.font().toString()
        self.input = QtWidgets.QPushButton(value)
        super().__init__(name, **kargs)
        self.setValue(value)
        self.input.clicked.connect(self.setFont)

    def setFont(self):
        font = selectFont()
        if font:
            self.setValue(font.toString())
            #pf.GUI.setFont(font)


class InputFilename(InputButton):
    """A filename input item.

    An InpuItem specialized in selecting a file.
    The input field is a button displaying the file name.
    Clicking on the button opens a file selection dialog, and the
    returned file name is displayed in the button.

    Parameters
    ----------
    name: str
        Name of the item.
    value: str
        The initial file name.
    filter: str
        The filter for the accepted filenames. See also :class:`InputFile`.
        Default is '\\*'.
    mode: str
        If True, the file selection mode. One of 'file', 'exist', 'dir',
        'any' or 'multi'. Default is False. See :class:`InputFile` for details.
    preview: ImageView, optional
        A widget having a ``showImage`` method. This can be used with image
        files to show a preview of the selected file. In most cases the
        preview widget is inserted in a dialog directly below the
        InputFilename field.

    See Also
    --------
    InputFile: a file selection dialog integrated in the InputItem

    """
    def __init__(self, name, value, filter='*', mode='file', preview=None,
                 **kargs):
        """Initialize the input item."""
        if 'func' not in kargs:
            kargs['func'] = InputFilename.changeFilename
        self._filter = filter
        self._mode = mode
        self._preview = preview
        super().__init__(name, value=value, **kargs)


    def changeFilename(self):
        """Pop up a FileDialog to change the filename"""
        from pyformex.gui.draw import askFilename
        fn = askFilename(self.value(), filter=self._filter,mode=self._mode)
        if fn:
            self.setValue(fn)
            if self._preview:
                self._preview.showImage(fn)


    def value(self):
        """Return the widget's value."""
        return Path(super().value())


class InputFile(InputItem):
    """An input item to select a file.

    A filename input field with an integrated file selection widget
    that allows to interactively select one (or more) file(s) or a
    directory from the file system, even create new directories.

    The returned value is a single :class:`Path` except for the 'multi'
    mode, which returns a (possibly empty) list of Paths.

    Parameters
    ----------
    name: str
        Name of the item.
    value: :term:`path_like`
        The path of the initially shown directory.  It should be an existing
        path on the file system. If a filename is specified,
        that file will be marked as the initial selection.
    filter: str | list of str
        One or more filter(s) to restrict the selectable files in the dialog.
        If multiple filters are given, the user can select which one to use.
        Each string can be one of the following:

        - a string in the format 'DESCRIPTION (PATTERNS)'
          where DESCRIPTION is a text describing the file type
          and PATTERNS is one or more filename matching patterns,
          separated by blanks. Example: 'Image files (\\*.png \\*.jpg)'
        - a key that can be passed to :func:`utils.fileDescriptions`
          to generate such a string. The function contains ready
          made filters for most common file types used in pyFormex.
    mode: str
        Determines what can be selected. One of:

        - 'file': select a file (existing or not). This is the default.
        - 'exist': select an existing file
        - 'dir': select an existing directory (widget allows to create a new)
        - 'any': select a file (existing or not) or a directory
        - 'multi': select multiple existing paths from the same directory
    compr: bool
        If True, the specified filters will be expanded to also include
        compressed files of the specified patterns. Compression algorithms
        include 'gz' and 'bz2'. For example, a filter 'Python files (\\*.py)'
        would be changed to 'Python files (\\*.py \\*.py.gz \\*.py.bz2)'.
    auto_suffix: bool
        If True (default), new file names will automatically be changed
        to have an extension matching the current filter.
        If False, any name is accepted as a new file name.
    sidebar: list
        A list of :term:`path_like` strings to add to the sidebar of the
        filedialog. This is typically used to provide shortcuts to
        some often used directories.

    See Also
    --------
    InputFilename: a filename input field with popup file selection dialog
    """

    def __init__(self, name, value, filter='*', mode='file', compr=False,
                  auto_suffix=True, sidebar=[], **kargs):
        """Initialize the input item."""
        if value is None:
            value = '.'
        path = Path(value)
        filter = utils.fileDescription(filter, compr)
        self.mode = mode[0]
        if self.mode not in 'fedam':
            self.mode = 'f'
        self.auto_suffix = auto_suffix
        qt_mode = FILE_SELECTION_MODE[self.mode]
        w = QtWidgets.QFileDialog(caption='')
        w.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
        if path.is_file():
            w.setDirectory(str(path.parent))
            w.selectFile(str(path))
        else:
            w.setDirectory(str(path))
        if isinstance(filter, str):
            filter = [filter]
        w.setNameFilters(filter)
        w.setFileMode(qt_mode)
        sidebardirs = pf.cfg['gui/sidebardirs']
        if sidebar:
            sidebardirs.extend(sidebar)
        w.setSidebarUrls(fileUrls(sidebardirs))
        # remove the dialog buttons, since the widget is embedded
        for b in w.findChildren(QtWidgets.QPushButton):
           b.close()
        # Capture the widgets done method
        w.done = self.done
        self.input = w
        super().__init__(name, value=value, **kargs)
        # store the dialog for the sake of overloaded self.input.done
        self._dialog = kargs['dialog']


    def done(self, value):
        """Close the dialog when the selector is closed, e.g. on double click"""
        if value:
            self._dialog.accept()
        else:
            self._dialog.reject()


    def value(self):
        """Return the widget's value."""
        val = [Path(r) for r in self.input.selectedFiles()]
        if self.mode == 'm':
            for v in val:
                if not v.exists():
                    raise ValidationError("The paths should exist")
        else:
            if len(val) == 0:
                raise ValidationError("Selection is empty")
            val = val[0]
            if self.mode == 'd':
                if not val.is_dir():
                    raise ValidationError("Select a directory, not a file")
            elif self.mode in 'ef':
                if val.is_dir():
                    raise ValidationError("Select a file, not a directory")
                if self.mode == 'e':
                    if not val.exists():
                        raise ValidationError("The file should exist")
                elif self.mode == 'f' and self.auto_suffix:
                    # force suffix
                    filter = self.input.selectedNameFilter()
                    val = utils.setFiletypeFromFilter(val, filter)

        return val


    def setValue(self, value):
        self.input.selectFile(value)


class InputWidget(InputItem):
    """An input item containing another widget.

    Parameters
    ----------
    name: str
        Name of the item.
    value: widget
        Another widget, often an InputItem. The widget should have at
        least the following methods:

        - value(): returns the value of the accepted data in the widget.
        - setValue(dict): updates the value(s) in the widget with those
          in the passed dict.
    """

    def __init__(self, name, value, **kargs):
        """Initialize the input item."""
        kargs['text'] = ''  # Force no label
        self.input = value
        super().__init__(name, **kargs)

    def text(self):
        """Return the displayed text."""
        return ''

    def value(self):
        """Return the widget's value."""
        return self.input.value()

    def setValue(self, val):
        """Change the widget's value."""
        if val:
            self.input.setValue(val)


class InputGroup(QtWidgets.QGroupBox):
    """A boxed group of InputItems.

    An InputGroup groups multiple InputItems in a box with label.
    It contains it's own InputForm in which the items can be layed out
    instead of in the Dialog's main form.
    The InputGroup is normally created by using the :func:`_G` function
    in the Dialog items argument.

    Parameters
    ----------
    name: str
        Name of the group.
    check: bool, optional
        If True, the group label has a check widget to enable/disable all
        items in the group at once.
    enabled: bool, optional
        If True (default), the group is enabled initially.
    """

    def __init__(self, name, **kargs):
        """Initialize the input item."""
        super().__init__()
        self.key = name
        self.input = self
        self.tab = None
        self.form = InputForm()
        self.setLayout(self.form)
        self.setTitle(kargs.get('text', name))
        if 'check' in kargs:
            self.setCheckable(True)
            self.setChecked(kargs['check'])
        if 'enabled' in kargs:
            self.setEnabled(kargs['enabled'])

    def name(self):
        return self.key

    def value(self):
        """Return the widget's value."""
        if self.isCheckable():
            return self.isChecked()
        else:
            return None

    def setValue(self, val):
        """Change the widget's value."""
        if self.isCheckable():
            self.setChecked(val)


class InputHBox(QtWidgets.QWidget):
    """A column of items in a hbox input form.

    Usually, all InputItems in a Dialog are put vertically in the form.
    Using the :func:`_C` function in the Dialog input, a horizontal box
    is created in the form, which each can be filled with multiple columns
    of InputItems.

    Parameters
    ----------
    name: str
        Name of the hbox.
    """

    def __init__(self, name, hbox, **kargs):
        """Initialize the input item."""
        super().__init__()
        self.key = name
        self.form = InputForm()
        self.setLayout(self.form)
        if 'maxwidth' in kargs:
            self.setMaximumWidth(kargs['maxwidth'])
        spacer = kargs.get('spacer', '')
        if 'l' in spacer:
            hbox.addItem(hspacer())
        hbox.addWidget(self)
        if 'r' in spacer:
            hbox.addItem(hspacer())

    def name(self):
        return self.key


class InputTab(QtWidgets.QWidget):
    """A tab page in an input form.

    An InputTab groups multiple InputItems in a tab page with a label.
    It contains it's own InputForm in which items can be layed out
    instead of in the Dialog's main form. The label has a check box
    to enable/disable the whole set of items as a group.
    The InputTab is normally created by using the :func:`_T` function
    in the Dialog items argument.

    Parameters
    ----------
    name: str
        Name of the tab.
    """

    def __init__(self, name, tab, **kargs):
        """Initialize the input item."""
        super().__init__()
        self.key = name
        self.form = InputForm()
        self.setLayout(self.form)
        tab.addTab(self, kargs.get('text', name))

    def name(self):
        return self.key


def defaultItemType(item):
    """Guess the InputItem type from the value/choices"""
    if 'choices' in item:
        if 'value' in item and isinstance(item['value'], (tuple, list)):
            itemtype = 'select'
        else:
            itemtype = 'combo'
    else:
        itemtype = type(item['value']).__name__
    if itemtype not in InputItems:
        itemtype = 'str'
    return itemtype


def simpleInputItem(name=None, value=None, itemtype=None, **kargs):
    """A convenience function to create an InputItem dictionary"""
    if name is None:
        name = next(InputItem.autoname)
    kargs['name'] = name
    if value is not None:
        kargs['value'] = value
    if itemtype is not None:
        kargs['itemtype'] = itemtype
    return kargs
_I = simpleInputItem


def groupInputItem(name, items=[], **kargs):
    """A convenience function to create an InputItem dictionary"""
    kargs['name'] = name
    kargs['items'] = items
    kargs['itemtype'] = 'group'
    return kargs
_G = groupInputItem

def columnInputItem(name, items=[], **kargs):
    """A convenience function to create an InputItem dictionary"""
    kargs['name'] = name
    kargs['items'] = items
    kargs['itemtype'] = 'hbox'
    return kargs
_C = columnInputItem

def tabInputItem(name, items=[], **kargs):
    """A convenience function to create an InputItem dictionary"""
    kargs['name'] = name
    kargs['items'] = items
    kargs['itemtype'] = 'tab'
    return kargs
_T = tabInputItem


# define a function to have the same enabling name as for InputItem
def enableItem(self, *args):
    try:
        ok = any([src.value() == val for src, val in self.enabled_by])
        self.setEnabled(ok)
    except Exception:
        utils.warn("error_widgets_enableitem")
        pass


InputItem.enableItem = enableItem
QtWidgets.QGroupBox.enableItem = enableItem
QtWidgets.QTabWidget.enableItem = enableItem


class InputForm(QtWidgets.QVBoxLayout):
    """An input form.

    The input form is a layout box in which the InputItems are normally
    layed out vertically. The form can contain hboxes, which create multiple
    columns of vertically layed out items. Furthermore, the form can consist
    of multiple tabs which each can be filled with (columns of ) input items.
    """

    def __init__(self):
        """Initialize the InputForm."""
        super().__init__()
        self.tabs = []      # list of tab widgets in this form
        self.hboxes = []    # list of hbox widgets in this form
        self.last = None    # last added itemtype


class Dialog(QtWidgets.QDialog):
    """A popup window to edit, accept or reject input values.

    The Dialog class presents a unified system for quick and easy
    creation of common dialog types. The provided dialog can become
    quite sophisticated with tabbed pages, groupboxes and custom widgets.
    Both modal and modeless (non-modal) dialogs can be created.

    Parameters
    ----------
    items: list
        A list of items to be put in the dialog form.
        Each item is either an input item, meaning it can return a value
        to the program, or a plain :class:`QtWidgets.QWidget`, which can
        be used in an auxiliary role, but does not return a value.
        Input items are specified as a dict, containing all the required
        keyword arguments to construct one of the :class:`InputItem`
        subclasses. Because these dicts can become quite verbal,
        the :mod:`gui.draw` module contains some shortcut functions that
        help in reducting the required input.
        Each InputItem at least has an attribute 'name' and a method 'value()'.
        The dialog returns its results as a dict where the value() of each
        input item is stored with its name as key. The name can also be used
        as an index in the Dialog to get the corresponding InputItem.
    enablers: list of tuples, optional
        Each item is a tuple of the form (key,value,key1,...) defining a field
        whose value will enable other fields. If the input itemm named key
        has the specified value, the the fields key1,... are enabled.
        Currently, key should be a field of type boolean, [radio],
        combo or group. Also, any input field should only have one enabler,
        or incorrect operation may result.
        Note: this feature is currently scheduled for revision.
    actions: list | dict, optional
        Parameters to define a :class:`ButtonBox` with actions. If a list,
        it must be like the actions parameter of :class:`ButtonBox`.
        If a dict, it must contain the choices, funcs and optionally icons
        parameters of :class:`ButtonBox`.
        The generated buttons are added to the dialog window above (default)
        or below the normal input form. They are generally
        used to perform some overall action on the input dialog, like accepting
        the values or rejecting them, and closing the dialog window, but they can
        be used for anything. Overall actions could also be triggered
        from buttons in the normal dialog form, but it is convenient for the
        user to make them stand off from the normal input form. The following
        default actions will be generated if the button text is supplied without
        a function:

        - 'Cancel': reject (and close) the dialog
        - 'OK': accept the data in the dialog and close it
        - 'Close': close the dialog (possible containing non-validated entries).

        If no actions are specified, a default ButtonBox is created two
        buttons: Cancel and OK, to either reject or accept the input values.
        This is most valuable in modal dialogs, where some button is needed
        to end the modal dialog.
    default: str, optional
        The text of the default action. This should be one of the actions
        defined in the actions parameter. If not specified, it is set to the
        first of the actions. If no actions were defined either, it is set
        to 'OK'.
    message: str, optional
        A text to be displayed in front of the action buttons. It is most
        functional when the action buttons are on top, to show information
        about the input form below.
    caption: str, optional
        The title to be shown in the window decoration. Default is
        'pyFormex-dialog'. Dialog windows remember their position based
        on this caption.
    parent: QWidget, optional
        The parent widget. Setting this will destroy the dialog when the parent
        is destroyed. The default is the pyFormex main window.
    modal: bool, optional
        If True, the dialog is a modal one, meaning all other windows of the
        application are blocked until the user finishes the dialog by
        either accepting or rejecting the data, which will close the window.
        If False, the dialog is modeless and the user can continue working
        with other windows while the dialog stays open. The default is to not
        set any option and expect it to be specified when the dialog is
        shown (see :meth:`show`).
    store: dict | str, optional
        A dict or dict-like object storing the initial and/or the accepted
        values of the input items. The keys in the dict are the item names.
        The behavior of the store is different depending on the value of the
        ``save`` parameter.

        The default behavior of the store is to provide the initial values
        as well as store back the validated results. The values in the store
        will override the values specified in the items. Items do not need to
        have a value specified, if their value is in the store. On input
        validation the data in the store are updated. Missing items are added.
        This behavior will easily create persistence of the input data over
        different invocations of the Dialog. By using a store in the project
        dict (pf.PF), there will even be persistence over different
        executions of the script/app, and if the project is saved to a file
        even over different pyFormex sessions. As an extra convenience, if
        a string is specified instead of a dict, an empty dict will be
        created in pf.PF with that string as key, and that dict will be used
        as store. All items should specify an initial value in that case.

        If you do not want the validated results to be written back to your
        store, add the ``save=False`` parameter. In that case the store
        is read only and values specified in the items will override the
        values in the store.
    save: bool, optional
        If False, makes the store read-only and gives the values in the
        items precedence over those in the store.
        If not provided or True, the store is read-write and will get
        updated with the validated results. The values in the store have
        preecence over those in the items.
    prefix: str, optional
        If specified, the names of the input items will be prefixed with
        this string in the returned dialog results.
    autoprefix: bool, optional
        If True, the names of items inside tabs and group boxes will
        get prefixed with the tab and group names, separated with a '/'.
        The default (False) will just use the specified item name.
    flat: bool, optional
        If True, the results are returned in a single (flat) dictionary,
        with keys being the specified or autoprefixed ones.
        If False, the results will be structured: the value of a tab
        or a group is a dictionary with the results of its fields.
        If not provided, its value is set equal to that of autoprefix.
    scroll: bool, optional
        If True, the input form will be put inside a scroll area, making
        the form scrollable in case it has so many fields that theyt are
        not all visible at once on the screen.
        The default is to no use a scroll area. Some parts of the input form
        may than fall off the screen and the user has to shift the window to
        make them accessible. It is better to limit the form size by putting
        items in multiple columns using hboxes, or in separate pages using
        tabs.
    buttonsattop: bool, optional
        If True, the action buttons are put above the input form. If False,
        they are at the bottom. The default is configured in the user settings.
    size: tuple (int, int)
        Initial size of the window (width, height) in pixels. The default
        is automatically defined by the size policies.

    Attributes
    ----------
    returncode: int
        A code depending on how the Dialog was closed. It is generally one of

        - Dialog.ACCEPTED: if the Dialog was accepted.
        - Dialog.REJECTED: if the Dialog was rejected.
        - Dialog.TIMEOUT: if the Dialog timed out.

        However, action buttons may finish the Dialog with another return
        value by calling ``self.done(returncode)``.
    results: dict
        Contains the resulting values of all input fields.
        With a returncode REJECTED, it is an empty dict.
        With ACCEPTED, all values will be validated.
        With TIMEOUT, it contains None values for those fields
        that were invalid at the time of the timeout. Since the default
        operation modus is to not use a timeout, the user can just test
        the results dict, and if it contains anything, it are valid results.

    Examples
    --------
    See the :doc:`../input-dialogs`.

    """
    # possible values of the returncode/result() after closing a widget
    REJECTED = 0   # Dialog was canceled
    ACCEPTED = 1   # Dialog was accepted
    TIMEOUT = 2    # Dialog timed out
    RESERVED = 3   # Do no use

    default_caption = 'pyFormex-dialog'

    def __init__(self, items, *, enablers=[],
                 actions=None, default=None, message=None,
                 caption=None, parent=None, modal=None, flags=None,
                 store=None, save=None,
                 prefix='', autoprefix=False, flat=None,
                 scroll=False, buttonsattop=pf.cfg['gui/buttonsattop'],
                 size=None, #align_right=False,
    ):
        """Create a dialog window to let the user input some values."""
        if parent is None:
            parent = pf.GUI
        super().__init__(parent)
        if flags:
            self.setWindowFlags(flags)

        self.signals = signals.Signals()

        if caption is None:
            caption = Dialog.default_caption
        else:
            caption = str(caption)
        # Disallow multiple windows with same name
        if parent == pf.GUI:
            d = pf.GUI.dialog(caption)
            if d is None:
                pf.GUI.dialogs.append(self)
            else:
                d.show()
                d.raise_()
                raise ValueError(
                    f"A Dialog with the name '{caption}' already exists."
                    " You can close all dialogs with Actions->Reset GUI.")

        self.setObjectName(caption)
        self.setWindowTitle(caption)
        if modal is not None:
            self.setModal(modal)

        if size:
            w, h = size
            if isinstance(w, float):
                w = int(w*pf.GUI.maxsize[0])
            if isinstance(h, float):
                h = int(h*pf.GUI.maxsize[1])
            self.resize(w, h)

        self.inputarea = QtWidgets.QWidget()
        #self.inputarea.resize(1000,800)
        #self.inputarea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        if scroll:
            self.scroll = QtWidgets.QScrollArea(parent=self)
            # scroll->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOn);
            # scroll->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOn);
            #self.scroll.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            self.scroll.setWidget(self.inputarea)
            self.scroll.setWidgetResizable(True)
        else:
            self.scroll = self.inputarea

        self.form = InputForm()
        self.inputarea.setLayout(self.form)

        # add needed widgets to layout
        self.fields = []
        self.groups = {}
        self.valid = None
        self.results = {}
        self.returncode = None
        self._pos = None
        if isinstance(store, dict) and save is None:
            utils.warn("dialog_store_save", uplevel=2)
        if isinstance(store, str):
            if store not in pf.PF:
                pf.PF[store] = {}
            store = pf.PF[store]
            if not isinstance(store, dict):
                raise ValueError("Invalid store: not a dict")
        self.store = store
        self.save = store is not None and save is not False
        self.autoname = utils.autoName('input')
        self.prefix = prefix
        self.autoprefix = autoprefix
        self.flat = self.autoprefix if flat is None else flat
        self.tab = None  # tabwidget for all the tabs in this form
        self.actions = None # The actions box for this form

        # add the items to the input form
        if pf.cfg['gui/allow_old_dialog_items']:
            # converting old tuple items
            items = [ _I(*i) if isinstance(i, tuple) else i for i in items]
        self.add_items(self.form, self.prefix, items)

        # add the enablers
        init_signals = []
        for en in enablers:
            src = self[en[0]]
            if src:
                val = en[1]
                for t in en[2:]:
                    tgt = self[t]
                    if tgt:
                        try:
                            tgt.enabled_by.append((src, val))
                        except Exception:
                            tgt.enabled_by = [(src, val)]
                        signal = None
                        if isinstance(src, InputBool):
                            signal = src.input.stateChanged[int]
                        elif isinstance(src, InputRadio):
                            utils.warn('warn_radio_enabler')
                            # BV: this does not work
                            #signal = src.input.buttonClicked[int]
                        elif isinstance(src, InputCombo):
                            signal = src.input.currentIndexChanged[int]
                        elif isinstance(src, InputGroup):
                            signal = src.input.clicked[bool]
                        else:
                            raise ValueError(
                                f"Can not enable from a {type(src.input)}"
                                f" input field")

                        if signal:
                            init_signals.append(signal)
                            signal.connect(tgt.enableItem)

        # emit the signal to adjust initial state
        for signal in init_signals:
            signal.emit(0)

        # create the action buttons
        if actions is None:
            actions = [('Cancel',), ('OK',)]
            if default is None:
                default = 'OK'
        if isinstance(actions, dict):
            kargs = dict(name=message, value=default, parent=self, spacer='l')
            kargs.update(**actions)
            self.actions = ButtonBox(**kargs)
        else:
            default_funcs = {
                'ok': self.accept,
                'cancel': self.reject,
                'close': self.close
                }
            for i, a in enumerate(actions):
                if len(a) < 2 or a[1] is None:
                    # Fill in default functions
                    actions[i] = (a[0], default_funcs.get(a[0].lower()))
            self.actions = ButtonBox(
                name=message, value=default, parent=self, spacer='l',
                actions=actions)

        # add a layout to hold the input form and action buttons
        self._layout = QtWidgets.QVBoxLayout(self)
        if self.actions and buttonsattop:
            self._layout.addWidget(self.actions)
        self._layout.addWidget(self.scroll)
        if self.actions and not buttonsattop:
            self._layout.addWidget(self.actions)
        self.setLayout(self._layout);

        # smart placement keeps pos/size for dialogs with same caption
        if pf.cfg['gui/smart_placement']:
            saved_geom = pf.cfg['gui/saved_geom'].get(caption, None)
            if saved_geom:
                # do not set size for windows with default caption:
                # there may be a very wide range os sizes
                if caption != Dialog.default_caption:
                    self.resize(*saved_geom[2:])
                self.move(*saved_geom[:2])


    def fieldNames(self):
        return [f.key for f in self.fields]

    def add_items(self, form, prefix, items):
        """Add input items to a form in the Dialog.

        Parameters
        ----------
        form: InputForm
            The form to which the items will be added.
        prefix: str
            A string to be prepended to all item names.
        items: list of input items
            The items to be put in the form. Each item is normally a dict
            with the keyword parameters to construct an instance of one
            of the InputItem subclasses, InputGroup, InputHbox, InputTab.
            It can however also be a QWidget, allowing highly customizable
            Dialogs.
        """
        for item in items:

            if isinstance(item, dict):
                # always pass the dialog to the children
                item['dialog'] = self
                itemtype = item.get('itemtype', None)

                if itemtype == 'tab':
                    self.add_tab(form, prefix, **item)

                elif itemtype == 'group':
                    # Experimental: allow override prefix
                    # item.setdefault('prefix', prefix)
                    # self.add_group(form, **item)
                    self.add_group(form, prefix, **item)

                elif itemtype == 'hbox':
                    self.add_hbox(form, prefix, **item)

                else:
                    self.add_input(form, prefix, **item)

                form.last = itemtype

            elif isinstance(item, QtWidgets.QWidget):
                # this allows including widgets which are not
                # input fields
                form.addWidget(item)
                form.last = None

            else:
                raise ValueError(
                    f"Invalid input item type ({type(item)})."
                    " Expected a dict or a QWidget.")


    def add_group(self, form, prefix, name, items, **kargs):
        """Add a group of input items.

        Parameters
        ----------
        form: InputForm
            The form in which to add the items.
        prefix: str
            A string to be prepended to all item names.
        name: str
            Name of the group.
        items: list of dict
            A list a keyword parameters for constructing InputItems to be
            put in the group.
        **kargs: keyword arguments
            Extra arguments passed to the InputGroup initialization.
        """
        if 'check' in kargs:
            if self.store is not None and name in self.store:
                # Override value with the one from store
                kargs['check'] = bool(self.store[prefix+name])
        w = InputGroup(prefix+name, **kargs)
        form.addWidget(w)
        if w.isCheckable:
            self.fields.append(w)

        if self.autoprefix:
            prefix += name+'/'
        self.add_items(w.form, prefix, items)


    def add_hbox(self, form, prefix, name, items, newline=False, **kargs):
        """Add a column with input items.

        Parameters
        ----------
        form: InputForm
            The form in which to add the items.
        prefix: str
            A string to be prepended to all item names.
        name: str
            Name of the hbox.
        items: list of dict
            A list a keyword parameters for constructing InputItems to be
            put in the hbox.
        **kargs: keyword arguments
            Extra arguments passed to the InputHbox initialization.
        """
        if form.last == 'hbox' and not newline:
            # Add to previous hbox widget
            hbox = form.hboxes[-1]
        else:
            # Create a new hbox widget
            w = QtWidgets.QWidget()
            hbox = QtWidgets.QHBoxLayout()
            w.setLayout(hbox)
            form.addWidget(w)
            form.hboxes.append(hbox)

        w = InputHBox(prefix+name, hbox, **kargs)
        #w.resize(1000,w.height())
        if self.autoprefix:
            prefix += name+'/'
        self.add_items(w.form, prefix, items)
        w.form.addStretch()  # makes items in hbox align to top


    def add_tab(self, form, prefix, name, items, **kargs):
        """Add a Tab page with input items.

        Parameters
        ----------
        form: InputForm
            The form in which to add the items.
        prefix: str
            A string to be prepended to all item names.
        name: str
            Name of the tab.
        items: list of dict
            A list a keyword parameters for constructing InputItems to be
            put in the tab.
        **kargs: keyword arguments
            Extra arguments passed to the InputTab initialization.
        """
        if form.last == 'tab':
            # Add to previous tab widget
            tab = form.tabs[-1]
        else:
            # Create a new tab widget
            tab = QtWidgets.QTabWidget()
            form.addWidget(tab)
            form.tabs.append(tab)

        w = InputTab(prefix+name, tab, **kargs)
        if self.autoprefix:
            prefix += name+'/'
        self.add_items(w.form, prefix, items)
        w.form.addStretch()  # makes items in tab align to top


    def add_input(self, form, prefix, **item):
        """Add a single input item to the form.

        Parameters
        ----------
        form: InputForm
            The form in which to add the items.
        prefix: str
            A string to be prepended to all item names.
        **item:
            Keyword arguments for the initialization of the InputItem.
        """
        item['name'] = prefix + item.get('name', next(self.autoname))
        if 'value' not in item:
            item['value'] = None
        if self.save or item['value'] is None:
            # If self.save is True, the store gets precendence over the
            # specified value, so we always read the store.
            # Else, we only read the store if no value was specified.
            if self.store is not None:
                try:
                    item['value'] = self.store[item['name']]
                except KeyError:
                    pass

        if 'choices' in item:
            item['value'], item['choices'] = Dialog.sanitize_value_choices(
                item['value'], item['choices'] )

        if not 'itemtype' in item or item['itemtype'] is None:
            item['itemtype'] = defaultItemType(item)

        itemtype = item['itemtype']

        if isinstance(itemtype, str):
            if itemtype.endswith('radio') or itemtype.endswith('push'):
                if itemtype[0] in 'hv':
                    item['direction'] = itemtype[0]
                    item['itemtype'] = itemtype[1:]
                elif 'direction' not in item:
                    # default horizontal
                    item['direction'] = 'h'

            if itemtype == 'slider':
                value = item['value']
                if at.isInt(value):
                    pass
                elif isinstance(value, float):
                    item['itemtype'] = 'fslider'
                else:
                    raise ValueError("Invalid value type for slider: %s" % value)

        item['parent'] = self

        # Create the InputItem
        itemtype = item['itemtype']  # Make sure we have the final value
        if itemtype == 'list':
            utils.warn("""..

- itemtype='list' is deprecated and has been replaced with itemtype='select'
- the old itemtype='select' widget is now obtained with itemtype='combo'
""")
            itemtype = 'select'
        i = InputItems[itemtype] if itemtype in InputItems else InputString
        field = i(**item)
        self.fields.append(field)
        form.addWidget(field)


    @staticmethod
    def sanitize_value_choices(value=None, choices=[]):
        """Sanitize the value and choices parameters

        Make sure that value is one of the choices.

        Parameters
        ----------
        value: str, optional
            The initial selection from the choices. If not provided,
            the first option from choices becomes the value.
        choices: list | tuple
            An iterable with the valid choices. If value is not in choices,
            it will be added at the beginning.

        Returns
        -------
        value: str
            The default selected value
        choices: list
            The list of choices, which is guaranteed to contain value.

        Raises
        ------
        TypeError, if choices is not an iterable,
        ValueError, if choices is empty and no value is given.

        Examples
        --------
        >>> Dialog.sanitize_value_choices('abc', [])
        ('abc', ['abc'])
        >>> Dialog.sanitize_value_choices('abc', ['def'])
        ('abc', ['abc', 'def'])
        >>> Dialog.sanitize_value_choices('abc', ['def', 'abc'])
        ('abc', ['def', 'abc'])
        >>> Dialog.sanitize_value_choices(choices=['def', 'abc'])
        ('def', ['def', 'abc'])
        """
        try:
            choices = list(choices)
        except TypeError:
            raise ValueError(
                f"Choices should be a iterable, got {type(choices)}")
        if len(choices) == 0:
            if value is None:
                raise ValueError(
                    "List of choices should not be empty if no value given.")
            else:
                choices = [value]
        if value is None:
            value = choices[0]
        elif isinstance(value, (list, tuple)):
            for val in value:
                if val not in choices:
                    choices.append(val)
        else:
            # we have a value and choices
            if value not in choices:
                choices.insert(0, value)
        return value, choices


    def __getitem__(self, name):
        """Return the input item with specified name."""
        items = [f for f in self.fields if f.key == name]
        if len(items) > 0:
            return items[0]
        else:
            print(self.fieldNames())
            raise ValueError("No input field named: %s" % name)
            #return self.groups.get(name,None)


    def updateData(self, d):
        """Update a dialog from the data in given dictionary.

        This can be used to programmatorically change the data in an
        already open dialog.

        Parameters
        ----------
        d: dict
            A dictionary where the keys are field names in the dialog.
            The values will be set in the corresponding input items.
            The dict does not need to contain all the dialog fields.
            Keys that are not anmes of input items are silently ignored.
        """
        for f in self.fields:
            if f.key in d:
                f.setValue(d[f.key])


    def show(self, *, modal=False, timeout=None, timeoutfunc=None):
        """Show the dialog.

        Parameters
        ----------
        modal: bool
            If True, the Dialog is shown as a modal one, meaning that the
            user will have to complete (accept or reject) this Dialog before
            he can continue with other windows.
            The default is to show a modeless dialog.
        timeout: int
            Timeout in seconds for the Dialog. If specified and larger that
            zero, the current data will be accepted automatically (if they
            can be validated) after the given period.
            A value 0 will timeout immediately, a negative value will never
            timeout.  There will also be no timeout if the current data contain
            some invalid item.

        """
        # Set the keyboard focus to the first input field
        #self.fields[0].input.setFocus()
        self.status = None

        self.setModal(modal)
        if not modal:
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        #self.adjustSize()
        #self.setMaximumHeight(800)
        #print self.maximumHeight()
        QtWidgets.QDialog.show(self)
        addTimeOut(self, timeout, timeoutfunc)


    def validate(self):
        """Update the dialog's return value from the field values.

        This function is connected to the 'accepted()' signal.
        Modal dialogs should normally not need to call it.
        In non-modal dialogs however, you can call it to update the
        results without having to raise the accepted() signal (which
        would close the dialog).

        Returns
        -------
        bool
            True if all fields got validated. As a side effect, self.results
            will then contain the validated results. If some field failed
            validation, the corresponding result is set to None, and the return
            value is False.
        """
        self.results = {}
        self.valid = True
        for fld in self.fields:
            try:
                val = fld.value()
                if hasattr(fld, 'showError'):
                    fld.showError(False)
            except ValidationError as e:
                val = None
                self.valid = False
                fld.showError(True, msg=str(e))
            self.results[fld.key] = val
        if self.save:
            self.store.update(self.results)
        return self.valid


    # def done(self, returncode):
    #     """Finish the dialog if the results are valid.

    #     This calls :meth:`validate` to check the current input field values.
    #     If all values are valid, they are stored in the results, and the
    #     dialog is closed. If there are invalid values, they are flagged in
    #     the dialog, and the dialog remains open to let the user fix the
    #     problems.
    #     """
    #     if self.validate(): # or accept_invalid?
    #         self.returncode = returncode
    #         self.signals.VALIDATED.emit()
    #     else:
    #         self.returncode = Dialog.REJECTED
    #         self.results = {}


    def accept(self):
        """Accept the dialog if the results are valid.

        This calls :meth:`validate` to check the current input field values.
        If all values are valid, they are stored in the results, and the
        dialog is closed. If there are invalid values, they are flagged in
        the dialog, and the dialog remains open to let the user fix the
        problems.
        """
        if self.validate(): # or accept_invalid?
            self.returncode = Dialog.ACCEPTED
            self.signals.VALIDATED.emit()
        else:
            self.returncode = Dialog.REJECTED
            self.results = {}


    def close(self):
        """Close the Dialog.

        Unregisters the Dialog from the GUI and then closes the Dialog window.
        If smart_placement is configured, the relative geometry of the
        window is stored in the user's settings with the caption as key.
        """
        if pf.cfg['gui/smart_placement']:
            geom = self.x(), self.y(), self.width(), self.height()
            # DEV: !! the Config class does not allow the direct
            # setting of a dict element in subsections of prefcfg:
            # it will be set in refcfg instead !!
            # so we make a copy and set the full dict
            saved_geom = pf.cfg['gui/saved_geom'].copy()
            saved_geom[self.windowTitle()] = geom
            pf.prefcfg['gui/saved_geom'] = saved_geom
        if self in pf.GUI.dialogs:
            pf.GUI.dialogs.remove(self)
        return super().close()


    def timeout(self):
        """Called when the dialog times out.

        This validates and stores the results, and then closes
        the dialog. Unlike :meth:`accept`, the dialog is always closed,
        even if some input fields are not valid. In that case the results
        will contain a value None for the invalid fields.
        """
        # TODO: we should check the default action, and not return results
        # in case it is a 'CANCEL'.
        pf.debug("TIMEOUT", pf.DEBUG.GUI)
        if self.validate():
            self.signals.VALIDATED.emit()
        else:
            self.results ={}
        self.returncode = Dialog.TIMEOUT
        self.close()


    def waitResults(self):
        """Wait for the results from an input dialog.

        Processes the user interaction with the dialog until the user
        either rejects the dialog, or accepts the dialog with valid results.

        The user can accept the dialog by pressing the OK button or the ENTER
        key, and reject the dialog with the CANCEL button or the ESC key.
        On accept, the current input data are validated and if some data is
        invalid, the accept is refused and a marker is displayed on the invalid
        field(s).

        The result() method can be used to find out how the dialog was ended.
        Its value will be one of :attr:`ACCEPTED`, :attr:`REJECTED` or
        :attr:`TIMEOUT`.
        """
        loop = QtCore.QEventLoop()
        self.signals.VALIDATED.connect(loop.quit)
        self.rejected.connect(loop.quit)
        loop.exec_()
        #self.results.returncode = self.returncode
        self.close()
        return self.results


    def getResults(self, **kargs):
        """Show the dialog and wait for the results.

        Parameters: same as for :meth:`show`. This is a convenience function
        calling :meth:`show` with the provided parameters, and the calls
        :meth:`waitResults` and returns the results.
        """
        self.show(**kargs)
        return self.waitResults()


# Create a dict with itemtype <-> InputItem mapping

def getInputItemDict(base=InputItem):
    sub = base.__subclasses__()
    if not sub:
        return {}

    d = dict([(k.__name__[5:].lower(), k) for k in sub])
    for k in sub:
        d.update(getInputItemDict(k))
    return d

InputItems = getInputItemDict()


# some itemtypes are not strings but Python type objects.
# also add some name mismatches
# TODO: all itemtypes should become strings
InputItems.update({
    # None: InputItem,
    'str': InputString,
})
#print(list(InputItems.keys()))


####################################################################
########### Specialized Widgets #####################################
#####################################################################


# def setIcon(button, icon):
#     iconfile = utils.findIcon(icon)
#     print(iconfile)
#     if iconfile.endswith('.gif'):
#         button.movie = QtGui.QMovie(iconfile)
#         button.frameChanged.connect(button.movie,[=]{
#             pushButton->setIcon(movie->currentPixmap());
# });
# movie->start();

#         else:
#       QtGui.QIcon(QPixmap(utils.findIcon(icon)))


class ButtonBox(QtWidgets.QWidget):
    """A horizontal box with action buttons.

    This creates a horizontal box of push buttons, which each execute
    some functionality when pushed.
    The ButtonBox can be created in two ways: using the actions parameter
    with a list of tuples (text, func, icon), or using three parameters
    choices, func, icons, where choices and icons are lists, and func is
    a single function. Thus the following are equivalent::

        ButtonBox(actions=[(text1, func1, icon1), (text2, func2, icon2)])
        ButtonBox(choices=[text1, text2], func=func, icon=[icon1, icon2])

    if the equivalent func would be defined as follows::

        def func(id):
            if id == 0:
                func1()
            elif id == 1:
                func2()

    Parameters
    ----------
    actions: list of tuples, optional
        Each action is a tuple (text, func, icon) or (text, func) or (text,),
        where text is the string to be displayed on the button, func is a
        callable with zero or one positional argument, and icon is an icon
        name to be displayed on the button. If icon is omitted, the button
        only shows text. If func is omitted and text is a recognized standard
        value, a default func is installed (see parent parameter below).
        If func takes a parameter, it is passed the corresponding QPushButton,
        from where all details of the ButtonBox can be retrieved. See the
        `func` parameter.
        If the actions parameter is used, the choices, func and icons
        parameters must not be specified.
    parent: Dialog or :class:`QtWidget.QDialog`, optional
        The parent dialog to which the ButtonBox is added. If specified,
        some default actions are defined for often used button texts:

    value: str, optional
        The text of the default button. The default button is the button
        that will be pressed when the user presses ENTER on the keyboard.
        If not specified, there is no default action.
    choices: list of str, optional
        The list of strings to appear on the buttons.
    func: callable, optional
        A function that will be called whenever any of the button is pushed.
        The function receives the triggering button as parameter. This allows
        the function to operate depending on the button text and to have
        access to the button's parent ButtonBox. See Notes for an example.
    icons: list of icon names, optional
        A list of strings that specify the icons to be placed on the buttons.
        A None by be used for buttons not needing an icon.
    iconsonly: bool, optional
        If True, only icons will be shown on the button, without text.
        The default False shows both text and icon.

    Notes
    -----
    The following shows a ButtonBox with three buttons. The function prints
    the button text, but if the 'close' button is pressed, it also closes the
    ButtonBox::

        def func(b):
            print(b.text())
            if b.text() == 'close':
                 b.parent().close()

        box = ButtonBox(choices=('option1', 'option2', 'close), func=func)
        box.show()

    The equivalent with using the `actions` parameter would be::

        box = ButtonBox(actions=[
            ('option1', func), ('option2', func), ('close', func)])

    Note that

    Since both ButtonBox and InputPush are implemented as a
    :class:`QButtonGroup` with :class:`QPushButton` elements,
    it is tempting to merge the two classes.
    We have not (yet?) done it because in the InputPush the buttons are
    exclusive, and we use that feature to store and return the value of the
    set of buttons. Furthermore, the exclusive button group has other focus
    behavior, unwanted for action buttons (keyboard focus can not be cycled
    through the different buttons). The ButtonBox therefore has non-exclusive
    buttons and can not store a value. We could implement this ourselves
    (remember which button was pushed last) but it is not considered urgent.
    """
    def __init__(self, name='', actions=None, parent=None,
                 value=None, choices=[], func=None, icons=None,
                 iconsonly=False, spacing=2, spacer='l', **kargs):
        """Initialize the input item."""
        from itertools import zip_longest
        super().__init__(parent=parent)
        self.parent = parent
        if actions is not None:
            cfi = zip_longest(*actions)
            choices = next(cfi)
            try:
                self.funcs = list(next(cfi))
            except StopIteration:
                self.funcs = [ None ] * len(choices)
            try:
                icons = next(cfi)
            except StopIteration:
                icons = None
            self.func = self.myFunc
        else:
            self.func = func
            self.funcs = None
            if icons and len(icons) != len(choices):
                raise ValueError("choices and icons should have same length")

        #value, choices = Dialog.sanitize_value_choices(value, choices)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(spacing)
        if 'l' in spacer:
             layout.addItem(hspacer())
        if name:
            lbl = QtWidgets.QLabel()
            if name.startswith(':movie:'):
                moviefile = utils.findIcon(name[7:])
                movie = QtGui.QMovie(moviefile)
                lbl.setMovie(movie)
                movie.start()
            else:
                lbl.setText(name)
            layout.addWidget(lbl)
            if 'l' in spacer:
                layout.addItem(hspacer())
        self.bg = QtWidgets.QButtonGroup()
        for i, v in enumerate(choices):
            b = QtWidgets.QPushButton()
            b.setAutoDefault(v==value)
            if not iconsonly:
                b.setText(v)
            if icons and icons[i]:
                b.setIcon(pyformexIcon(icons[i]))
            if self.funcs and self.funcs[i] is None:
                if v.lower() == 'close':
                    self.funcs[i] = self.close
                else:
                    raise ValueError(f"No func for action {i}: {choices[i]}")
            self.bg.setId(b, i)
            self.bg.addButton(b, i)
            layout.addWidget(b)
        if 'r' in spacer:
             layout.addItem(hspacer())
        self.bg.buttonClicked.connect(self.func)
        self.setLayout(layout)

    def setText(self, text, index=0):
        """Change the text on button index."""
        self.bg.button(index).setText(text)

    def setIcon(self, icon, index=0):
        """Change the icon on button index."""
        if isinstance(icon, str):
            icon = pyformexIcon(icon)
        self.bg.button(index).setIcon(icon)

    def checkedId(self):
        """Return the number of the checked button"""
        return self.bg.checkedId()

    def myFunc(self, but):
        i = self.bg.id(but)
        f = self.funcs[i]
        if callable(f):
            # try:
            #     print(f)
            #     print(inspect.signature(f).parameters)
            #     nargs = len(inspect.signature(f).parameters)
            #     print(nargs)
            # except:
            #     nargs = 0
            # This does not work, because the function may have
            # keyword parameters with defaults. THey should not be
            # counted.
            # if nargs == 0:
            #     f()
            # else:
            #     f(but)
            try:
                f()
            except TypeError:
                try:
                    f(but)
                except:
                    pass


class ListWidget(QtWidgets.QListWidget):
    """A customized QListWidget with ability to compute its required size.

    """
    def __init__(self, maxh=0):
        """Initialize the ListWidget"""
        super().__init__()
        self.maxh = maxh
        self._size = QtWidgets.QListWidget.sizeHint(self)

    def allItems(self):
        return [self.item(i) for i in range(self.count())]

    def reqSize(self):
        w = 0
        h = 10  # margin
        for i in self.allItems():
            r = self.visualItemRect(i)
            h += r.height()
            w = max(w, r.width())
        return w, h

    def setSize(self):
        w, h = self.reqSize()
        pf.debug("Required list size is %s,%s" % (w, h), pf.DEBUG.WIDGET)
        if self.maxh > -1:
            self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            if self.maxh > 0:
                h = min(h, self.maxh)
            w, hs = objSize(QtWidgets.QListWidget.sizeHint(self))
            pf.debug("QListWidget hints size %s,%s" % (w, hs), pf.DEBUG.WIDGET)

        if self.maxh < 0:
            self.setFixedSize(w, h)

        pf.debug("Setting list size to %s,%s" % (w, h), pf.DEBUG.WIDGET)
        self._size = QtCore.QSize(w, h)

    def sizeHint(self):
        if self.maxh > 0:
            w, h = objSize(QtWidgets.QListWidget.sizeHint(self))
            print("QListWidget hints size %s,%s" % (w, h), pf.DEBUG.WIDGET)
            h = max(h, self.maxh)
            return QtCore.QSize(w, h)
        else:
            return self._size


########################### Table widgets ###########################

_EDITROLE = QtCore.Qt.EditRole


class TableModel(QtCore.QAbstractTableModel):
    """A model representing a two-dimensional array of items.

    Parameters
    ----------
    data: :term:`array_like`
        Any tabular data organized in a fixed number of rows and colums.
        This means that an item at row i and column j can be addressed as
        data[i][j]. Thus it can be a list of lists, or a list of tuples or
        a 2D numpy array. The data will always be returned as a list of lists
        though.
        Unless otherwise specified by the use of a `celltype`, `coltype` or
        `rowtype` argument, all items are converted to strings and will be
        returned as strings.
        Item storage order is row by row.
    chead: list of str, optional
        A list of ``ncols`` column headers.
    rhead: list of str, optional
        A list of ``nrows`` row headers.
    celltype: callable, optional
        A function to tranform the editable string of a cell to the cell data.
        If specified, and no ``rowtype`` nor ``coltype`` are specified,
        each edited item will be translated this function before storing it
        in the output table.
        If data is a numpy array, the default is the datatype of the array.
        Else the default is str.
    rowtype: list of nrows callables, optional
        If specified, the items of each row are mapped by the corresponding
        callable. This overrides `celltype` and is only used if `coltype` is
        not specified.
    coltype: list of ncols callables, optional
        If specified, the items of each column are mapped by the corresponding
        callable. This overrides `celltype` and `rowtype`.
    edit: bool, optional
        If True (default), the table is editable. Set to False to make the
        data readonly.
    resize: bool, optional
        If True, the table can be resized: rows and columns can be
        added or removed. If False, the size of the table can not be changed.
        The default value is equal to the value of `edit`.
        If `coltype` is specified, the number of columns can not be changed.
        If `rowtype` is specified, the number of rows can not be changed.

    See Also
    --------
    ArrayModel: a more efficient but not resizeable model for numpy arrays
    """

    def __init__(self, data, chead=None, rhead=None, celltype=None, rowtype=None, coltype=None, edit=True, resize=None):
        """Initialize the TableModel"""
        import numpy as np
        super().__init__()
        self.celltype = self.rowtype = self.coltype = None
        if coltype is not None:
            self.coltype = coltype
        elif rowtype is not None:
            self.rowtype = rowtype
        elif celltype is not None:
            self.celltype = celltype
        else:
            if isinstance(data, np.ndarray):
                self.celltype = data.dtype
            else:
                self.celltype = str
        if self.coltype:
            self._data = [[ct(i) for i, ct in zip(r, self.coltype)] for r in data]
        elif self.rowtype:
            self._data = [[rt(i) for i in r] for r, rt in zip(data, self.rowtype)]
        else:
            self._data = [[self.celltype(i) for i in r] for r in data]
        self.headerdata = {QtCore.Qt.Horizontal: chead, QtCore.Qt.Vertical: rhead}
        self.makeEditable(edit, resize)


    def makeEditable(self, edit=True, resize=None):
        """Make the table editable or not.

        - `edit`: bool: makes the items in the table editable or not.
        - `resize`: bool: makes the table resizable or not. If unspecified,
          it is set equal to the `edit`.
        """
        self._flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if edit:
            self._flags |= QtCore.Qt.ItemIsEditable
        self.edit = edit
        if resize is None:
            self.resize = edit
        else:
            self.resize = resize


    def rowCount(self, parent=None):
        """Return number of rows in the table"""
        return len(self._data)


    def columnCount(self, parent=None):
        """Return number of columns in the table"""
        return len(self._data[0])


    def data(self, index, role):
        """Return the data at the specified index"""
        if index.isValid() and role == QtCore.Qt.DisplayRole:
            r, c = index.row(), index.column()
            return self._data[r][c]
        else:
            return None


    def cellType(self, r, c):
        """Return the type of the item at the specified position"""
        if self.coltype:
            itemtype = self.coltype[c]
        elif self.rowtype:
            itemtype = self.rowtype[r]
        else:
            itemtype = self.celltype
        return itemtype


    def setCellData(self, r, c, value):
        """Set the value of an individual table element.

        This changes the stored data, not the interface.
        """
        itemtype = self.cellType(r, c)
        if self.coltype:
            itemtype = self.coltype[c]
        elif self.rowtype:
            itemtype = self.rowtype[r]
        else:
            itemtype = self.celltype
        self._data[r][c] = itemtype(value)


    def setData(self, index, value, role=_EDITROLE):
        """Set the value of an individual table element."""
        if self.edit and role == QtCore.Qt.EditRole:
            try:
                r, c = [index.row(), index.column()]
                self.setCellData(r, c, value)
                self.dataChanged.emit(index, index)  # not sure if needed
                return True
            except Exception:
                raise ValueError(f"Could not set the value in cell {index}")
        else:
            print("CAN  NOT EDIT")
        return False


    def headerData(self, col, orientation, role):
        """Return the header data for the sepcified row or column"""
        if orientation in self.headerdata and self.headerdata[orientation] and role == QtCore.Qt.DisplayRole:
            return self.headerdata[orientation][col]
        return None


    def insertRows(self, row=None, count=None):
        """Insert row(s) in table"""
        if row is None:
            row = self.rowCount()
        if count is None:
            count = 1
        last = row+count-1
        newdata = [[None] * self.columnCount()] * count
        self.beginInsertRows(QtCore.QModelIndex(), row, last)
        self._data[row:row] = newdata
        self.endInsertRows()
        return True


    def removeRows(self, row=None, count=None):
        """Remove row(s) from table"""
        if row is None:
            row = self.rowCount()
        if count is None:
            count = 1
        last = row+count-1
        self.beginRemoveRows(QtCore.QModelIndex(), row, last)
        self._data[row:row+count] = []
        self.endRemoveRows()
        return True


    def flags(self, index):
        """Return the TableModel flags."""
        return self._flags


# Generic Python types for numpy data types
_generic_nptype = {
    'i': int,
    'f': float,
    's': str,
    }

class ArrayModel(QtCore.QAbstractTableModel):
    """A model representing a two-dimensional numpy array.

    Parameters
    ----------
    data: 2D numpy array
        The input data: a 2D int or float numpy array of shape (nrows, ncols).
    chead: list of str, optional
        A list of ncol column headers. Default will show the column number.
    rhead: list of str, optional
        A list of nrow row headers. Default will show the row number.
    edit: bool, optional
        If True (default), the table is editable. Set to False to make the
        data readonly.

    See Also
    --------
    TableModel: a more general (resizable) 2D table model
    """

    def __init__(self, data, chead=None, rhead=None, edit=True):
        import numpy as np
        super().__init__()
        self._data = np.asarray(data)
        self.generictype = _generic_nptype[self._data.dtype.kind]
        if rhead is None:
            rhead = np.arange(data.shape[0])
        if chead is None:
            chead = np.arange(data.shape[1])
        self.headerdata = {QtCore.Qt.Horizontal: chead, QtCore.Qt.Vertical: rhead}
        self.makeEditable(edit)


    def makeEditable(self, edit=True):
        """Make the table editable or not.

        - `edit`: bool: makes the items in the table editable or not.
         """
        self._flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if edit:
            self._flags |= QtCore.Qt.ItemIsEditable
        self.edit = edit


    def rowCount(self, parent=None):
        """Return number of rows in the table"""
        return self._data.shape[0]


    def columnCount(self, parent=None):
        """Return number of columns in the table"""
        return self._data.shape[1]


    def data(self, index, role):
        if index.isValid() and role == QtCore.Qt.DisplayRole:
            r, c = index.row(), index.column()
            return self.generictype(self._data[r, c])
        else:
            return None


    def cellType(self, r, c):
        """Return the type of the item at the specified position"""
        return self._data.dtype


    def setData(self, index, value, role=_EDITROLE):
        """Set the value of an individual table element."""
        if self.edit and role == QtCore.Qt.EditRole:
            try:
                k = self._data.dtype.kind
                if k == 'f':
                    value, ok = value.toDouble()
                elif k == 'i':
                    #value,ok = value.toInt()
                    #print(type(value))
                    value, ok = int(value), True
                else:
                    ok = False
                if not ok:
                    pf.warning("Expected %s data" % self.generictype)
                    return False
                r, c = [index.row(), index.column()]
                self._data[r, c] = value
                self.dataChanged.emit(index, index)  # not sure if needed
                return True
            except Exception:
                raise ValueError(f"Could not set the value in cell {index}")
        else:
             print("CAN  NOT EDIT")
        return False


    def headerData(self, col, orientation, role):
        """Return the header data for the sepcified row or column"""
        if orientation in self.headerdata and self.headerdata[orientation] and role == QtCore.Qt.DisplayRole:
            return self.headerdata[orientation][col]
        return None


    def flags(self, index):
        """Return the TableModel flags."""
        return self._flags


class Table(QtWidgets.QTableView):
    """A widget to show/edit a two-dimensional array of items.

    Parameters
    ----------
    data: :term:`array_like`
        A 2-D array of items, with ``nrow`` rows and ``ncol`` columns.

        If ``data`` is a numpy array, the Table will use the ArrayModel:
        editing the data will directly change the input data array; all
        items are of the same type; the size of the table can not be changed.

        Else a TableModel is used. Rows and columns can be added to or removed
        from the table. Item type can be set per row or per column or for the
        whole table.
    label: currently unused (intended to display an optional label
        in the upper left corner if both `chead` and `rhead` are specified.
    parent: widget
        The parent widget
    autowidth: bool
        If True (default), columns are resized to the content width.
    chead, rhead, delltype, rowtype, edit, resize: optional
        Parameters passed to the ArrayModel or TableModel.
    """
    def __init__(self, data, *, chead=None, rhead=None, label=None,
                 celltype=None, rowtype=None, coltype=None, edit=True,
                 resize=None, parent=None, autowidth=True):
        """Initialize the Table widget."""
        import numpy as np
        super().__init__(parent)
        if isinstance(data, np.ndarray):
            self.tm = ArrayModel(data, chead, rhead, edit=edit)
        else:
            self.tm = TableModel(data, chead, rhead, celltype, rowtype, coltype,
                                 edit=edit, resize=resize)
        self.setModel(self.tm)
        self.horizontalHeader().setVisible(chead is not None)
        self.verticalHeader().setVisible(rhead is not None)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                           QtWidgets.QSizePolicy.MinimumExpanding)
        #self.connect(tm,dataChanged
        self.autowidth = autowidth
        if self.autowidth:
            self.resizeColumnsToContents()
        self.setCornerButtonEnabled
        self.adjustSize()

    def colWidths(self):
        """Return the width of the columns in the table"""
        return [self.columnWidth(i) for i in range(self.tm.columnCount())]

    def rowHeights(self):
        """Return the height of the rows in the table"""
        return [self.rowHeight(i) for i in range(self.tm.rowCount())]

    def minimumSizeHint(self):
        #self.update()
        #minsize = size = QtWidgets.QTableView.sizeHint(self)
        #print("ORIG SIZE: %s, %s" % (size.width(),size.height()))
        size = self.size()
        #print("ACTUAL SIZE: %s, %s" % (size.width(),size.height()))
        width = sum(self.colWidths())
        height = sum(self.rowHeights())
        #print("NET SIZE: %s, %s" % (width,height))
        width += self.tm.columnCount() * 1 + 1
        height += self.tm.rowCount() * 1 + 1
        #print("SPACED SIZE: %s, %s" % (width,height))
        if self.horizontalHeader().isVisible():
            height += self.horizontalHeader().height()
        if self.verticalHeader().isVisible():
            width += self.verticalHeader().width()
        #print("HEADERED SIZE: %s, %s" % (width,height))
        size = QtCore.QSize(width, height)
        return size

    sizeHint = minimumSizeHint

    def dataChanged(self, ind1, ind2):
        QtWidgets.QTableView.dataChanged(self, ind1, ind2)
        self.update()

    def update(self):
        """Update the table.

        This method should be called to update the widget when the data of
        the table have changed. If autowidth is True, this will also
        adjust the column widths.
        """
        print("UPDATE")
        QtWidgets.QTableView.update(self)
        if self.autowidth:
            print("ADJUSTING COLUMNS")
            self.resizeColumnsToContents()
        self.adjustSize()
        self.updateGeometry()



    def value(self):
        """Return the Table's value."""
        return self.tm._data



#####################################################################
########### Specialized Dialogs #####################################
#####################################################################


def selectFont():
    """Ask the user to select a font.

    Shows the :class:`QFontDialog` widget, offering the user to select
    a font.

    Returns
    -------
    QFont | None
        A font if the user exited the dialog with the :guilabel:`OK`
        button or None if the user clicked :guilabel:`CANCEL`.
    """
    font = pf.GUI.font()
    # This if ok for pyside2! Don't know for pyqt5
    ok, font = QtWidgets.QFontDialog.getFont(
        font, parent=None, title="",
        options=QtWidgets.QFontDialog.DontUseNativeDialog)
    if ok:
        return font
    else:
        return None


# The QtWidgets.QColorDialog can not be instantiated or subclassed.
# The getColor function will create a QColorDialog and return a color
# See the InputColor.setColor method for how to create your own QColorDialog

def getColor(col='black', caption='pyFormex Color Selector'):
    """Create a color selection dialog and return the selected color.

    col is the initial selection.
    If a valid color is selected, its string name is returned, usually as
    a hex #RRGGBB string. If the dialog is canceled, None is returned.
    """
    QCD = QtWidgets.QColorDialog
    col = QCD.getColor(col, title=caption, options=QCD.DontUseNativeDialog)
    if col.isValid():
        return str(col.name())
    else:
        return None

#####################################################################
########### Text Display Widgets ####################################
#####################################################################


class MessageBox(QtWidgets.QMessageBox):
    """A message box is a widget displaying a short text for the user.

    The message box displays a text, an optional icon depending on the level
    and a number of action buttons.

    Parameters
    ----------
    text: str
        the text to be shown. This can be either plain text or html
        or reStructuredText.
    format: str
        The text format: either 'plain', 'html' or 'rest'.
        Any other value will trigger automatic recognition.
        Recognition of plain text and html is automatic.
        A text is autorecognized to be reStructuredText if its first
        line starts with '..' (usually followed by a blank line).
    level: str
        Defines the icon that will be shown together with the text.
        If one of 'question', 'info', 'warning' or 'error', a matching icon
        will be shown to hint the user about the type of message. Any other
        value will suppress the icon.
    actions: list of str
        For each string a pushbutton will be created which can be used
        to exit the dialog and remove the message.
        By default there is a single button labeled 'OK'.

    Notes
    -----
    When the MessageBox is displayed with the :meth:`getResults()` method,
    a modal dialog is created, i.e. the user will have to click a button
    or hit the ESC key before he can continue.

    If you want a modeless dialog, allowing the user to continue while the
    message stays open, use the :meth:`show` method to display it.
    """
    # TODO: This could be replaced with a generic Dialog
    # Beware: the check option is used in warnings
    def __init__(self, text, format='', level='info', actions=['OK'],
                 default=None, timeout=None, modal=None, caption=None,
                 parent=None, check=None):
        if parent is None:
            parent = pf.GUI
        super().__init__(parent)
        if caption is None:
            caption = f"pyFormex {level}"
        self.setWindowTitle(caption)
        if modal is not None:
            self.setModal(modal)
        if default is None:
            default = actions[-1]
        self.updateText(text, format)
        icon = self.getIcon(level)
        if icon:
            self.setIcon(icon)

        for a in actions:
            b = self.addButton(a, QtWidgets.QMessageBox.AcceptRole)
            if a == default:
                self.setDefaultButton(b)

        addTimeOut(self, timeout, self.accept)
        self.checks = []
        if check:
            if not isinstance(check, list):
                check = [check]
            for text in check:
                self.checks.append(self.addCheck(text))

    def getIcon(self, level='noicon'):
        if level == 'info':
            return self.Information
        elif level == 'warning':
            return self.Warning
        elif level == 'error':
            return self.Critical
        elif level == 'question':
            return self.Question


    def addCheck(self, text):
        """Add a check field at the bottom of the layout."""
        grid = self.layout()
        nr = grid.rowCount()
        check = QtWidgets.QCheckBox(text)
        # Always use column 1: the icon is in column 0, the text in column 1
        grid.addWidget(check, nr, 1, 1, -1)
        return check


    def show(self, modal=False):
        self.setModal(modal)
        QtWidgets.QMessageBox.show(self)


    def getResults(self):
        """Display the message box and wait for user to click a button.

        This will show the message box as a modal dialog, so that the
        user has to click a button (or hit the ESC key) before he can continue.
        Returns the text of the button that was clicked or
        an empty string if ESC was hit.
        """
        self.show(modal=True)
        self.exec_()
        b = self.clickedButton()
        if not b:  # b == 0 or b is None
            b = self.defaultButton()
        if b:
            res = str(b.text())
        else:
            res = ''
        if self.checks:
            return res, [c.isChecked() for c in self.checks]
        else:
            return res


    def updateText(self, text, format=''):
        self.setText(utils.convertText(text, format)[0])


# TODO: can be replaced with a normal Dialog and a label item

class TextBox(QtWidgets.QDialog):
    """Display a text and wait for user response.

    Possible choices are 'OK' and 'CANCEL'.
    The function returns True if the OK button was clicked or 'ENTER'
    was pressed, False if the 'CANCEL' button was pressed or ESC was pressed.
    """
    def __init__(self, text, format=None, actions=[('OK',)], modal=None, parent=None, caption=None, mono=False, timeout=None, flags=None):
        if parent is None:
            parent = pf.GUI
        super().__init__(parent)
        if flags is not None:
            self.setWindowFlags(flags)
        if caption is None:
            caption = 'pyFormex-dialog'
        self.setWindowTitle('pyFormex Text Display')
        if modal is not None:
            self.setModal(modal)
        self._t = QtWidgets.QTextEdit()
        self._t.setReadOnly(True)
        self.updateText(text, format)
        self._b = ButtonBox(actions=actions, parent=self)  # ,stretch=[1,1])
        l = QtWidgets.QVBoxLayout()
        l.addWidget(self._t)
        l.addWidget(self._b)
        self.setLayout(l)
        self.resize(800, 400)
        if mono:
            font = QtGui.QFont("DejaVu Sans Mono")
            # font.setStyle(QtGui.QFont.StyleNormal)
            self.setFont(font)

        addTimeOut(self, timeout, self.accept)

    def getResults(self):
        return self.exec_() == Dialog.ACCEPTED

    def updateText(self, text, format=''):
        self._t.setText(utils.convertText(text, format)[0])

###################### Special Tool Buttons ########################

class DropDownToolButton(QtWidgets.QToolButton):
    """A toolbar button that drops down a menu"""
    def __init__(self, toolbar, title, items, default):
        super().__init__(parent=toolbar)
        #self.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
        self.triggered.connect(self.setDefaultAction)
        # TODO: setting the default in the toolbutton only happens
        #       after executing the function connected to the selected
        #       item. It would be better to set it before by creating
        #       a wrapper function that sets it and then executes the item.
        #       The item's function should then be disconnected.
        from pyformex.gui.menu import Menu
        menu = Menu(title, parent=toolbar, items=items)
        self.setMenu(menu)
        self.setDefaultAction(menu.action(default))
        toolbar.addWidget(self)


class ToggleToolButton:
    """A toolbar button that toggles a state.

    icons: tuple of two icon names (off, on)
    func: function that toggles the external state
    status: function that reports the external state
    checked: initial state
    tooltip:
    toolbar: the toolbar where the button is added
    """
    def __init__(self, toolbar, icons, func, status, checked=False, tooltip=''):
        iconset = QtGui.QIcon()
        for i, state in enumerate((QtGui.QIcon.Off, QtGui.QIcon.On)):
            icon = QPixmap(utils.findIcon(icons[i]))
            iconset.addPixmap(icon, QtGui.QIcon.Normal, state)
        a = toolbar.addAction(iconset, tooltip, func)
        a.setEnabled(True)
        b = toolbar.widgetForAction(a)
        b.setCheckable(True)
        b.setChecked(checked)
        b.setToolTip(tooltip)
        b.clicked.connect(self.update_status)
        self.action = a
        self.button = b
        self.func = func if callable(func) else None
        self.status = status if callable(status) else None
        self.update_status()

    def update_status(self):
        self.button.setChecked(self.status())
        pf.app.processEvents()


############################# Coords box ###########################

# TODO: this should be merged into InputPoint

class CoordsBox(QtWidgets.QWidget):
    """A widget displaying the coordinates of a point.


    """
    def __init__(self, ndim=3, readonly=False, *args):
        super().__init__(*args)
        layout = QtWidgets.QHBoxLayout(self)
        self.validator = QtGui.QDoubleValidator(self)
        self.values = []
        for name in ['x', 'y', 'z'][:ndim]:
            lbl = QtWidgets.QLabel(name)
            val = QtWidgets.QLineEdit('0.0')
            val.setValidator(self.validator)
            val.setReadOnly(readonly)
            layout.addWidget(lbl)
            layout.addWidget(val)
            self.values.append(val)
        self.setLayout(layout)

    def getValues(self):
        """Return the current x,y,z values as a list of floats."""
        return [float(val.text()) for val in self.values]

    def setValues(self, values):
        """Set the three values of the widget."""
        for v, val in zip(self.values, [float(v) for v in values]):
            v.setText(str(val))



############################# ImageView ###########################

# TODO: put this into an InputImage?
# TODO: this should not have a value(). If value() is needed,
#       InputFilename could be used, Or a derived InputImage?

class ImageView(QtWidgets.QLabel):
    """A widget displaying an image.

    """

    def __init__(self, image=None, maxheight=None, parent=None):
        """Create a new ImageView widget."""
        super().__init__(parent)
        self.setBackgroundRole(QtGui.QPalette.Base)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        if maxheight:
            self.setMaximumHeight(maxheight)
        if image is None:
            self.filename = self.image = None
        else:
            self.showImage(image, maxheight=maxheight)


    def showImage(self, image, maxheight=None):
        """Show an image in the viewer.

        Parameters
        ----------
        image:
            Either a filename or an existing QImage instance. If a filename,
            it should be an image file that can be read by the QImage
            constructor.
            Most image formats are understood by QImage. The list of supported
            formats can be obtained with :func:`gui.image.imageFormats` with
            parameters ('qt', 'r').
        """
        if isinstance(image, QImage):
            filename = None
        else:
            filename = image
            image = QImage(filename)
            if image.isNull():
                try:
                    fname = pf.cfg['datadir'] / 'image_not_loaded.png'
                    image = QImage(fname)
                except Exception:
                    raise ValueError("Cannot load image file %s" % filename)
            if maxheight:
                image = image.scaledToHeight(maxheight)
        #print("Size %sx%s" % (image.width(),image.height()))
        self.setPixmap(QPixmap.fromImage(image))
        self.filename = filename
        self.image = image
        self.zoom = 1.0


    def value(self):
        return self.filename


# Deprecated but still accepted
InputDialog = Dialog


# initialize custom colors in color dialog

def setCustomColors(col):
    """Set QColorDialog Custom colors.

    col is a list of max. 16 color values (any values accepted by
    colors.RGBcolor
    """
    custom_colors = col[:16]
    for i, c in enumerate(custom_colors):
        # the QColorDialog has a strange way to display the colors
        # (alternately in the upper and lower row)
        # we convert this to show them from left to right in order
        j = 2*i if i < 8 else 2*(i-8)+1
        col = QtGui.QColor(*colors.RGBcolor(c))
        if pf.cfg['gui/bindings'].lower() == 'pyside2':
            col = col.rgb()
        QtWidgets.QColorDialog.setCustomColor(j, col)

# Set the QColorDialog custom colors to the pyFormex palette
setCustomColors(colors.palette)

# End
