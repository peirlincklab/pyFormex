..

..
  This file is part of pyFormex.
  pyFormex is a tool for generating, manipulating and transforming 3D
  geometrical models by sequences of mathematical operations.
  Home page: http://pyformex.org
  Project page:  http://savannah.nongnu.org/projects/pyformex/
  Copyright 2004-2018 (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
  Distributed under the GNU General Public License version 3 or later.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see http://www.gnu.org/licenses/.


.. |date| date::

..
  This document is written in ReST. To see a nicely formatted PDF version
  you can compile this document with the rst2pdf command.

.. _Python: https://www.python.org/
.. _reST: http://docutils.sourceforge.net/rst.html
.. _PEP8: https://www.python.org/dev/peps/pep-0008/
.. _numpydoc: https://developer.lsst.io/python/numpydoc.html
.. _`Numpy documentation guidelines`: http://projects.scipy.org/numpy/wiki/CodingStyleGuidelines
.. _napoleon: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html#example-numpy
.. _`sphinx napoleon guide`: https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
.. _linters: http://books.agiliq.com/projects/essential-python-tools/en/latest/linters.html

===========================
pyFormex coding style guide
===========================
:Date: |date|
:Author: benedict.verhegghe@feops.com

.. warning:: This document is currently under development!

This document describes the coding style to be used in the pyFormex source.
Developers are expected to apply these rules for all code they contribute
to pyFormex. But pyFormex users may be interested to use the same style
recommendations.


Source languages
================
Most of the pyFormex source code is written in the Python_ language.

.. note:: Whenever we mention Python in this document, we mean Python
	  version 3. The older Python version 2 is no longer supported.
	  On many Linux systems however, it is still the default Python.
	  If in doubt, check with the command ``python --version``.
	  Use the command ``python3`` to assure you get the version 3.
	  Actually, pyFormex requires at least version 3.6.


Text messages, docstrings and comments in the Python code should be in
English.

For performance reasons some functionality may be coded in C and loaded
as a C-extension into Python. The C code is put under the ``pyformex/lib``
subdirectory. By preference there is also a Python version available
which can be loaded in case the C-version can not be compiled/loaded
on the target platform.

The shader programs for the OpenGL rendering engine under ``pyformex/lib``,
though looking like C code, are actually GLSL.

Documentation (like this file) is written by preference in reStructuredText
(reST_), which is readable in an editor and can easily be converted to
both PDF and HTML.
Small and/or frozen documents can also be just plain text.


File names
==========
Source file names should only contain alphanumeric characters and the punctuation
symbols '.', '_' and '-'. Alphabetic characters should by preference be lower
case only.

The first character should always be an alphabetic character (except
for the special purpose ``__init__.py`` files).
The examples in ``pyformex/examples`` and the menus in ``pyformex/gui/menus``
should start with an upper case letter. To visually set off parts of the
filename, use by preference the underscore (_). The dot (.) is normally used
to specify a tail referring to the file type. The hyphen ('-') is mostly used
to set off a numeric part. Examples::

    my_first_example.py
    example-1.py
    example-2.py

The same rules hold for directory names, except these should normally not have
a dot suffix.


Style guidelines for Python source
==================================

The definite guide on properly writing Python code is the PEP8_ document
of the Python developers. It is certainly a good idea to go through that
document and to try to follow it as much as possible.

Many tools have been developed to help in checking your code, suggest
improvements, and even to automatically reformat your code to adjust it
to these presciptions. See the `code_checking_tools`_ section. We recommend
to use these tools and check and improve your code before commiting it.
However, as is mentioned in the PEP8 document, a clear, readable and consistent
style is more important than strictly following all the rules.

Below we only mention the rules for pyFormex where they are deemed really
important or where they divert from PEP8. For the rest, it is save to follow
the PEP8.

General guidelines
------------------

- Always start the Python source file with a line containing a comment marker
  '#' in the first column::

    #

  This mark is used for automatically stamping the files with a copyright
  notice.

  The remainder of the line is normally empty, but if the file is intended
  to be an executable, it can contain the specification of the interpreter,
  like this::

    #!/usr/bin/env python3

- Always end your Python source files with a line::

    # End

  This is useful in detecting accidental cutting of the file.
  Make sure that this line has an end-of-line marker. Most editors can be
  configured to do this automatically on saving your file.

- Always use 4 blanks for indenting, never use TABs. Use
  a decent Python-aware editor that allows you to configure this. The
  main author of pyFormex uses ``Emacs`` with ``python-mode.el``.

- For whitespace in expressions and statements, try to follow the rules in
  PEP8_. Do not put a whitespace directly inside delimiters
  or around mathematic operators of the highest precedence.
  But *do* put spaces around the assignment operator ('='), except in argument
  lists. Also put a blank after commas. Thus::

    def hyp(a, b=1):
        cc = a*a + b*b
        return math.sqrt(cc)

- Always start a new line after the colon (``:``) in ``if`` and ``for``
  statements.

- Whenever possible use implicit for loops (comprehensions) instead of
  explicit ones.

- Numpy often provides a choice of using an attribute, a method or a
  function to get to the same result. The preference ordering is:
  attribute > method > function. Examples:

  - use ``A.shape``, not ``numpy.shape(A)``
  - use ``A.reshape(new_shape)``, not ``numpy.reshape(A, new_shape)``


Line length
-----------
Limit the line length to a maximum of 90 characters. PEP8_ recommends 79,
but as pyFormex code tends to use chaining of transformation methods, lines
typically become longer than standard Python. In order to reduce the number
of continuation lines, we opted for a slightly longer mximum line length.

When needing to break a line, remember that Python has automatic line
continuation for code in between parentheses (), brackets [] or braces {}.
Also strings can be broken up and are automatically continuated.
If you need to break some long line that does not contain any of them, the
best solution might be to add a pair of parentheses: a tuple with a single
item is always reduced to the item itself. For example::

    a_long_variable = a_very_long_variable + another_very_long_variable

can be split as follows::

    a_long_variable = (a_very_long_variable
                       + another_very_long_variable)

.. note:: There has been a change in the PEP8_ recommendation concerning
	  line splitting around a binary operator. Until recently, the
	  recommendation was to split the above line after the operator::

	    a_long_variable = (a_very_long_variable +
                               another_very_long_variable)

          Now the consensus is to split before the operator.


String formatting
-----------------

Python has three major methods to convert data to a string. In order of
their historical appearence, these are:

- the '%' operator,
- the string ``format`` method,
- the use of f-strings.

f-strings only appeared in Python 3.6, and we have set the minimum required
Python version to 3.6 precisely to allow the use of f-strings. An f-string
is simple a string with an 'f' before the opening quote, like
``f"this is an f-string"``.

The following examples compares the three methods of formatting some data::

   a = 1.5
   e = 2
   s1 = "%s to the power %s yields %s" % (a, e, a**e)
   s2 = "{} to the power {} yields {}".format(a, e, a**e)
   s3 = f"{a} to the power {e} yields {a**e}"

All three strings get the same value ``"1.5 to the power 2 yields 2.25"``.
The f-string has been shown to be the most efficient. As it is also the
simplest to read and interprete, this should be the preferred way to write
formatting strings. For historical reasons however most of the cases in
pyFormex are still using the % operator. There is no check done (yet) on
the use of it. But new code should by preference use f-strings and you
are invited to convert as much as possible the existing old style.

Docstrings
----------

Readability and maintainability of source code is greatly enhanced by
proper documentation. In Python this is done mainly by the use of
docstrings.

All pyFormex modules should have a docstring at module level. It is to be the
first code after the copyright notice.
The module docstring consists of at least 3 lines: a first line with a short
description, an empty second line, and the third and following lines describing
the module in detail. A trivial example::

    """Dummy module

    This is a dummy module that does nothing at all.
    """

All class definitions should have their own (class level) docstring, again
with minimum three lines as for the module docstring.

Finally, all function and class method definitions should contain a docstring
as well. Here the docstring can be limited to a single short description if
the function has no parameters and no return value, and the working of the
function is simple and obvious.

See more in the `docstring styleguide`_ below.

Imports
-------
Import statements should be put at the top of the code, directly below
the first (module) docstring.

All import statements in the pyFormex Python source should use absolute
imports, starting from the pyformex main package. Every imported module
should be on a line by itself. When importing individual attributes from
a module, these can be put on a single line.

Imports should be ordered as follows:

- first the modules from the Python standard library,
- next the alien packages,
- finally the pyFormex modules.

The pyFormex modules are by preference ordered by subpackage, and
first module imports and finally individual attribute imports.
The subpackages should be in the order lib, gui, opengl, plugins, examples.

.. warning:: Wildcard imports (``from module import *``) should not be used.
  There are still some of them in historical pyFormex code, but they will be
  gradually removed. New code should not use them.

When importing modules with an alias name, try to use the following
standardized aliases: ``np`` for ``numpy``, ``pf`` for ``pyformex``,
``at`` for pyformex.arraytools.

Here's an example of a correct import section::

    # Example of an extensive import list

    import sys
    import os

    import numpy as np

    import pyformex as pf                  # import pyformex package with alias
    from pyformex import plugins           # import a subpackge
    from pyformex import utils             # import module
    from pyformex import arraytools as at  # import module with alias
    from pyformex.coords import Coords     # import attribute


Naming conventions
------------------

- Variables, functions, classes and their methods should be named
  by preference according to the following scheme:

  - classes: ``UpperUpperUpper``
  - functions and methods: ``lowerUpperUpper``
  - variables: ``lowercaseonly``

  Lower case only names can have underscores inserted to visually separate
  the constituant parts: ``lower_case_only``.

  Local names that are not supposed to be used directly by the user
  or application programmer, can have underscores inserted or
  appended.

  Local names may start with an underscore to hide them from the user.
  These names will indeed not be made available by Python's ``import *``
  statements.


Exceptions
----------
When raising an Exception, the error message should be put in parentheses as
an argument to the Exception class::

  raise SomeError('Some error occurred')

In most cases, the builtin ``ValueError`` can be used.

Also, when using a ``try...except...`` clause, the except should include an
Exception class::

  try:
     # some code that may generate a ValueError
  except ValueError:
     # clean up


Executable scripts
------------------

Some Python modules are intended to also be executed as a script,
rather than just being loaded as a module. The scripts may be executed
by the Python interpreter or by the pyFormex script processor::

    python3 some_python_script.py
    pyformex some_pyformex_script.py
    pyformex --gui some_pyformex_gui_script.py

pyFormex gui scripts can also be executed by loading them from the pyFormex GUI.

In such cases, the executable code that is not be be executed when the file is
loaded as a module, is typically collected at the end of the file under and
if-statement like this::

    if __name__ == "__main__":
        # Code to be executed when run from the Python interpreter

Similarly, pyFormex scripts (including all the examples provided with pyFormex)
can test the ``__name__`` variable to find out whether the script is
executed by pyFormex and whether the GUI is opened or not::

  if __name__ == "__script__":
      # Statements to execute when pyFormex is run without the GUI

  if __name__ == "__draw__":
      # Statements to execute when run under the GUI

Obviously, you can also combine these tests if the same code is to work under
different use cases::

    if __name__ in [ '__draw__', '__script__', '__main__' ]:


.. _`docstring styleguide`:

Style guidelines for Python docstrings
======================================

We now use a sphinx extension 'napoleon' in the automatic generation
of the reference manual. This creates a better layout of the result
and allows simpler docstring formats. Two docstring styles can be used:
numpy style and google style. We prefer numpy style (since pyFormex
is heavily numpy based), though google style is also admissible.
See `sphinx napoleon guide`_ for a description.

.. warning:: This section is outdated and needs an update.

- All functions, methods, classes and modules should have a docstring,
  consisting of a single first line with the short description,
  possibly followed by a blank line and an extended description. It
  is recommended to add an extended description for all but the trivial
  components.

- Docstrings should end and start with triple double-quotes (""").

.. Try not to use lines starting with the word 'class' in a
   multiline docstring: it tends to confuse emacs+python-mode.
   NEEDS CONFIRMATION

- Docstrings should not exceed the 80 character total line length.
  Python statements can exceed that length, if the result is more easy
  to read than splitting the line.

- Docstrings should be written with reST_ syntax. This allows us
  to use the docstrings to autmoatically generate the reference
  manual in a nice layout, while the docstrings keep being easily
  readable. Where in doubt, try to follow the `Numpy documentation guidelines`_.

- reStructuredText is very keen to the precise indentation (but as Python
  coders we are already used to that). All text belonging to the same
  logical unit should get the same indentation. And beware espacially for
  the required blank lines to delimit different section. A typical
  example is that of a bullet list::

    Text before the bullet list.

    - Bullet item 1
    - Bullet item 2, somewhat longer and continued
      on the next line.
    - Bullet item 3

    Text below the bullet item


- The extended description should contain a section describing the parameters
  and one describing the return value (if any). These should
  be structured as follows::

    Parameters
    ----------
    par1: type
        Meaning of parameter 1.
    par2: type
        Meaning of parameter 2.

    Returns
    -------
    ret1: type
        Description of return value 1.
    ret2: type
        Description of return value 2.

  If there is only one return value (the common case) you can leave
  out the 'ret1:' and just specify the type.

- The parameters of class constructor methods (``__init__``) should be
  documented in the Class docstring, not in the ``__init__`` method
  itself.

- Special sections (note, warning) can be used to draw special attention of
  the user. Format these as follows (leave a space after '..')::

     Note
     ----
         This is a note.

     Warning
     -------
         Be careful!

- Wherever possible add an example of the use of the function. By preference
  this should be a live example that can be used through the --doctest
  framework. This should be structured as follows::

    Examples
    --------
      >>> F = Formex('3:012934',[1,3])
      >>> print F.coords
      [[[ 0.  0.  0.]
       [ 1.  0.  0.]
       [ 1.  1.  0.]]

      [[ 1.  1.  0.]
       [ 0.  1.  0.]
       [ 0.  0.  0.]]]

  Lines starting with '>>>' should be executable Python (pyFormex) code.
  If the code creates any output, that output should be added exactly as
  generated (but aligned with the '>>>' below the code line.
  When the module is tested with::

    pyformex --doctest MODULENAME

  Python will execute all these code and check that the results match.
  In order to get good quality formatting in both the HTML and PDF versions,
  both the code lines and the output it generates should be kept short.
  You can use intermediate variables in the code to obtain this. For the
  output, you may have to use properly formatted printing of the data or
  subdata. E.g., a ``print F`` above instead of ``print F.coords`` would
  result in a too long line.

  See also the documentation for arraytools.uniqueOrdered for another
  example.

.. note:: For more examples and guidelines, see
	  `Numpy documentation guidelines`_, numpydoc_ and napoleon_.


Style guidelines for reST documents
===================================

- Start reStructuredText with the following two lines (the second being
  an empty line)::

    ..


- End the .rst files with a line::

    .. End


.. _code_checking_tools:

Automatic checking of the Python coding style
=============================================

While the PEP8_ and the above recommendations should be read and kept in mind
when writing code, it is certainly not easy to keep track of all the
guidelines when concentrating on the validity of the code itself.
Therefore the use of external tools that can check code has nearly become a
necessity to keep the coding style intact over time, and to help in
reformating old offending code.

Many tools are available for checking Python code and reporting offenses.
Some even offer automatic reformating. Some tools check PEP8_ recommendations,
others even check for possible coding errors and bad coding practices.
A non-comprehensive list: pycodestyle, pyflakes, mccabe, flake8, pylama,
pylint, pydocstyle. See linters_ for more and some explanation.
Many of these tools overlap and provide similar output, but there are also
differences that warrant using than one tool.
For pyFormex, we have currently chosen to use flake8 and pylint3.
These can easily be installed on Debian/Ubuntu and alikes::

    apt install flake8 pylint3

Flake8 is actually a meta-tool that uses pycodestyle, pyflakes and mccabe
by default::

  $ flake8 --version
  3.6.0 (mccabe: 0.6.1, pycodestyle: 2.4.0, pyflakes: 2.0.0) CPython 3.7.3 on Linux

Pylint (actually pylint3) is a very comprehensive tool that also does a thorough
code analysis, at the price of being much slower. So the recommendation is to
first run flake8, and when that reports no (or very few) remarks, then run
pylint3 to possibly find more issues.

Because the default configurations of these tools are very pedantic,
we have added custom configuration files (``pylintrc``, ``setup.cfg``),
that make them more usable for pyFormex: the maximum line length is
increased to 90 (from 79 in PEP8_), and we ignore some rules that are
offended a lot in pyFormex but that we deem not important enough to
strictly adhere to:

- E225 and E226: missing whitespace around operator. The code checkers want
  whitespace around every binary operator, though PEP8_ suggests to use no
  whitespace around the operator of the highest precedence in a complex
  expression. We follow that, as it improves readability.
- E266: too many leading '#' for block comment: this is offended by the
  copyright notices appearing in all files. We may someday change the notices
  and then reactivate this rule.
- E303: too many blank lines: PEP8_ suggests to use only one blank line between
  class methods, but allows extra blank lines where it improves readability.
  This is often the case in pyFormex, with has many complex and long methods.
  We have historically been using two blank lines between methods, and want to
  keep that.
- W503 line break before binary operator: as a result of the recent change
  in the PEP8_ recommendation for breaking lines around binary operators
  (now breaking before is recommnded, before breaking after was the standard),
  some tools (depending on version) now issue a warning for both breaking
  before and after an operator. We have chosen to follow the new style, and
  so disabled the W503 warning while keeping the W504 (break after).


.. important:: Do not change these configuration files without first
    discussing the need for a change.

.. warning:: There are some tools that do automatic reformating of the Python
	     source (autopep8, black). We do not recommend to use these, as
	     they tend to reformat the typical pyFormex code in a much less
	     readable way.


How to use
----------
Use both of these tools by preference before committing any new code. From
the top level in your local repository::

   flake8 pyformex/...some_source_file
   pylint3 pyformex/...some_source_file

The tools may produce a whole lot of remarks. Not everything should be
fixed before checking in. You certainly should have a look at lines that
could be coding errors. But purely formatting issues should not all be handled
immediately if you are in a hurry to get the code out.

In future however we will likely use these tools to check all code
automatically at commit time, and you will not be allowed to commit
offending code.

Locally disabling code checks
-----------------------------
At times you may find that following some rule may actually hurt readability
and you would like to keep the offending line, without it being flagged in
future. With flake8 this is easy to do: just put a comment ``# noqa`` on the
line, and no checks will be done for that line. Better still is to silence
only the particular rule(s) you are offending. Add the rules to that comment.
The following is a line from ``pyformex/geomtools.py``::

    I = x.inertia()  # noqa: E741

Without that comment, the line would result in an offense::

    E741 ambiguous variable name 'I'

Indeed, PEP8_ recommends not to use the one-character variable names 'I', 'O'
or 'l', because in some fonts these characters can not be discerned from the
numerals '1' or '0'. However, we feel that in many cases using a meaningful
name like 'I' can add to the readability. In the above code it stands for the
inertia tensor. It would be as useful to name an identity matrix 'I'.
And if you write code, you should not be using an editor with such bad/obsolete
fonts anyhow. So we want to accept the 'I' here. But in order to not let these
possibly troublesome names be misused we did not want to ignore the 'E741' rule
globally. Instead, you can ignore it locally as shown above where you find it
useful to keep the offending variable name.


Testing after changes
---------------------

Be sure to always retest the module after the changes you have made::

  pyformex --doctest subpkg.module



Searching the pyFormex sources
==============================
While developing or using pyFormex, it is often desirable to be able to search
the pyFormex sources, e.g.

- to find examples of similar constructs for what you want to do,
- to find the implementation place of some feature you want to change,
- to update all code dependent on a feature you have changed.

The ``pyformex`` command provides the necessary tool to do so::

    pyformex --search -- [OPTIONS] PATTERN

This will actually execute the command::

    grep OPTIONS PATTERN FILES

where ``FILES`` will be replaced with the list of Python source files in the
pyformex directories. The command will list all occasions of ``PATTERN`` in
these files. All normal ``grep`` options (see ``man grep``) can be added, like
'-f' to search for a plain string instead of a regular expression, or '-i'
make the search case insensitive.

If you find the pyformext command above to elaborate, you can just define a
shorter alias. If you put the following line in your ``.bashrc``
file ::

    alias pysea='pyformex --search --'

you will be able to just do ::

    pysea PATTERN



.. End
