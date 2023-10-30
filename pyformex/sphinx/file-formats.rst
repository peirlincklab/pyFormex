..

..
  SPDX-FileCopyrightText: © 2007-2023 Benedict Verhegghe <bverheg@gmail.com>
  SPDX-License-Identifier: GPL-3.0-or-later

  This file is part of pyFormex 3.3  (Sun Mar 26 20:16:15 CEST 2023)
  pyFormex is a tool for generating, manipulating and transforming 3D
  geometrical models by sequences of mathematical operations.
  Home page: https://pyformex.org
  Project page: https://savannah.nongnu.org/projects/pyformex/
  Development: https://gitlab.com/bverheg/pyformex
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


.. include:: defines.inc
.. include:: links.inc


.. _cha:fileformats:

*********************
pyFormex file formats
*********************

:Date: |today|
:Version: |version|
:Author: Benedict Verhegghe <bverheg@gmail.com>

.. topic:: Abstract

  This document describes the native file formats used by pyFormex:
  the :ref:`pzf_file_format`, the :ref:`pyf_file_format` and the
  :ref:`pgf_file_format`.


Introduction
============
pyFormex can export geometrical data to many well-known file formats. However,
objects in pyFormex often contain a lot more information, which can not be saved
in these formats. For storing complete object information on a persistent medium
pyFormex has three native file formats:
the :ref:`pzf_file_format`, the :ref:`pyf_file_format` and
the :ref:`pgf_file_format`.

The PZF format is the most versatile: it can store any pyFormex
:class:`~geometry.Geometry` object and most other data in an open, versatile and
efficient format: that of a ZIP archive. It allows partial read, append,
edit and remove operations. It is the most recent of the
three pyFormex formats and is the prefered way to store your data
for reuse in pyFormex or plain Python.

The PYF format can store any data supported by the Python pickle
protocol (which means almost everything). It is fast and compact, but
is bound to the implementation of classes in pyFormex. Reading back
with a very different version of pyFormex may require extra work.
Therefore it is mostly recommended for short term storage.

The PGF format can only store :class:`~geometry.Geometry` objects. The format
is stable and well-defined and has a binary and ascii version.
Since the introduction of the PZF format, there is no longer
any advantage of using this format, except maybe that it is easier
to write a reader in other programming languages but Python.
There will likely be no further developments of the format,
but it will continue to be supported.

The following table gives an overview of the different capabilities of the
three formats.

+----------------------------------------------------+---------+-------+-------+
|       Overview of capabilities                     |  PZF    |  PYF  |  PGF  |
+====================================================+=========+=======+=======+
| Can save Geometry objects		             | yes     | yes   | yes   |
+----------------------------------------------------+---------+-------+-------+
| Can save Geometry object's Attributes              | yes     | yes   | [1]_  |
+----------------------------------------------------+---------+-------+-------+
| Can save Geometry object's Fields                  | yes     | yes   | yes   |
+----------------------------------------------------+---------+-------+-------+
| Can save other objects                             | [2]_    | yes   | no    |
+----------------------------------------------------+---------+-------+-------+
| Can save Canvas layout and Camera                  | yes     | [3]_  | no    |
+----------------------------------------------------+---------+-------+-------+
| Can load Geometry objects		             | yes     | yes   | yes   |
+----------------------------------------------------+---------+-------+-------+
| Can load Geometry object's Attributes              | yes     | yes   | yes   |
+----------------------------------------------------+---------+-------+-------+
| Can load Geometry object's Fields                  | yes     | yes   | yes   |
+----------------------------------------------------+---------+-------+-------+
| Can load other objects                             | yes     | yes   | no    |
+----------------------------------------------------+---------+-------+-------+
| Can restore Canvas layout and Camera               | yes     | [3]_  | no    |
+----------------------------------------------------+---------+-------+-------+
| Supports storing multiple objects                  | yes     | yes   | yes   |
+----------------------------------------------------+---------+-------+-------+
| Supports adding objects to the file                | yes     | no    | no    |
+----------------------------------------------------+---------+-------+-------+
| Supports removing objects from the file            | yes     | no    | no    |
+----------------------------------------------------+---------+-------+-------+
| Supports listing contents without loading          | yes     | no    | no    |
+----------------------------------------------------+---------+-------+-------+
| Backwards compatible (load, not save, old versions)| yes     | [4]_  | yes   |
+----------------------------------------------------+---------+-------+-------+
| Compatibility guaranteed on pyFormex upgrades      | yes     | [4]_  | yes   |
+----------------------------------------------------+---------+-------+-------+
| Compatibility guaranteed on Python upgrades        | yes     | [4]_  | yes   |
+----------------------------------------------------+---------+-------+-------+
| Supports loading in Python (outside of pyFormex)   | [5]_    | no    | [6]_  |
+----------------------------------------------------+---------+-------+-------+
| Supports loading outside of Python                 | [7]_    | no    | [8]_  |
+----------------------------------------------------+---------+-------+-------+

.. [1] Some simple attributes (e.g. object color) can be stored.
.. [2] Some objects may need some customization.
.. [3] Canvas and Camera can be saved/restored, but requires some scripting.
.. [4] Mostly, but bot fully guaranteed. Some extra scripting may be needed.
.. [5] Yes, it only requires the numpy module. Restoring the data to pyFormex
       objects obviously requires pyFormex.
.. [6] Yes, but requires scripting and understanding of the format.
.. [7] The PZF format writes arrays in numpy's .npy format. There exist packages
       for some languages (I know of C, C++, Mathematica) to read such files.
.. [8] Doable but you have to program it yourself (the author has done it in
       JavaScript).


.. _pzf_file_format:

pyFormex Zip File Format (PZF)
==============================
A pyFormex Zip File (PZF) is actually a ZIP archive, written with the
standard Python :class:`zipfile.ZipFile` class. Clearly, the user can insert
any file in such an archive. But the pyFormex :class:`pzffile.PzfFile` class
provides tools for storing pyFormex objects in such an archive,
and for restoring the pyFormex objects from the stored data.
The API is very general and extensible and allows any pyFormex class
to be saved in PZF format and restored from it. The PZF format can
therefore replace nearly all use cases of both the :ref:`pgf_file_format` and
the :ref:`pyf_file_format`.

.. note:
    This describes version 2.0 of the pyFormex PZF file format.
    The format has minor changes from the (unpublished) 1.0 version.
    The implementation is completely new though and the
    :class:`pzffile.PzfFile` is able to read and convert version 1.0 files.
    It can not write files in the version 1.0 format though.

The PZF format is very robust, is easy to implement and extend, provides
easy ways to upgrade without losing contents, and guarantees openness to
other softwares and portability to other OSes and architectures.
PZF files can be opened with most modern file managers (if they can open
a ZIP archive), allowing the user a view on what's inside,
and even to remove or edit parts of it or to add more contents.
The format offers compression by default, and even password-protection
might be added in future.
It is recommended (but not enforced) to use file names with a suffix
.pzf rather than .zip, to better recognize the specialized PZF format.

Being a ZIP archive, the contents of the PZF file are individual files.
Creating a PZF file is normally done using the :meth:`~pzffile.PzfFile.save`
method of the :class:`pzffile.PzfFile` class::

  PzfFile(filename).save(name1=obj1, name2=obj2, ...)

Only keyword parameters are allowed and thus each object has a name that will
be stored in the PZF file. The object's class is stored as well, to enable
restoring the original objects upon reading the PZF file.

In order for an object to be saveable, it should have a method ``pzf_dict``,
returning a dict with all the object data to be saved. Each item in the
dict will cause a file to be added in the PZF archive.
Full details are given in :ref:`save-api`.

In order for an object of some class to be loadable from a PZF format file,
the class has to be registered with the :mod:`pzffile` module::

  pzffile.register(class, name)

This tells the PzfFile reader that ``class`` should be used for objects with
the specified class name in the PZF file. The :func:`utils.pzf_register`
decorator can conveniently be used to automatically register the class with
its own name (see example below).

Finally, reading is done with::

  d = PzfFile(filename).read()

The returned dict has the object names as keys and the restored objects
as values. Only objects with a registered class name are restored.

Here's an example of a simple class that can be saved to PZF and restored::

  @utils.pzf_register
  class Person:
      def __init__(self, first_name, last_name):
          self.first = first_name
	  self.last = last_name
      def pzf_dict(self):
          return { 'first_name': self.first, 'last_name: self.last }


.. _`save-api`:

API for saving objects to PZF
-----------------------------

pzf_dict
........
An object can be saved to PZF if it has a ``pzf_dict`` method returning a
dict with the object data that should be saved. Each item in the dict causes a
file to be written into the PZF archive. The key becomes part of the filename
and the value is stored inside the file.

The key is often an attribute of the object, though it doesn't have to be.
In most cases it is just the keyword parameter that will be passed to the
object's loader function when reading the PZF file. The default loader
function is the object's __init__ method. That's why in the above example
we made the keys in the pzf_dict match the keyword parameters of the __init__
method. Note that if in the above example we use the same names for object
attributes and __init__ arguments (as is often done), we can simply return the
object's __dict__ as pzf_dict::

  @utils.pzf_register
  class Person:
      def __init__(self, first_name, last_name):
          self.first_name = first_name
	  self.last_name = last_name
      def pzf_dict(self):
          return self.__dict__

This hasn't been made the default because
objects often have a lot of computed attributes that are unneeded or even
unwanted for restoring the object and because
the pzf_dict items should be carefully crafted to allow storage
in the PZF format.

The value of the item should be one of these types:

:class:`numpy.ndarray`
  The value is written with :func:`numpy.lib.format.write_array` to a
  file with suffix .npy. This is the format as created by :func:`numpy.save`.
``str``
  The value is written as text to a file with suffix .txt and utf-8
  encoding.
``dict``
  The dict is converted to a string and then written to a file
  with suffix .txt like str type above. The key is required to hold a conversion
  specifier (see :ref:`convert_dict_to_str`).
``None``
  The value is part of the key (see :ref:`value_in_filename`).
  An empty file is created and the filename doesn't get a suffix.

File names
..........
From the above, it follows that only three types of files are written into
a PZF archive. They are marked by the filename suffix:

``.npy``
  A file containing a single numpy.ndarray in NumPy's .npy format.
``.txt``
  A file containing text in a utf-8 encoding.
``no suffix``
  An empty file: the info is in the file name.

The file name is formed as follows: the object's name and its class name are
joined together with a colon as separator to form a directory entry, and the
key from the pzf_dict with the appropriate suffix appended becomes the file
name. In other words, the full file names in the PZF archive become one of
these::

  name:class/key.npy
  name:class/key.txt
  name:class/key

This file name structure makes it easy to recognize the objects stored in a
PZF and conveniently groups all the files belonging to that object in
a subdirectory.


Valid keys
..........
A key in the pzf_dict must be a str. It cannot start or end with an underscore
and cannot contain double underscores excpet for the specific purposes
described in

- :ref:`value_in_filename`
- :ref:`reserved_key_field`

It should also not contain a colon except for the purposes described in
the following cases, where it is required:

- :ref:`convert_dict_to_str`
- :ref:`value_in_filename`

The part of the key before the (first) double underscore or colon (or the whole
key if it doesn't contain any of them) will be passed as keyword argument to
the loader function when reading a PZF file. We call (that part of) the key
the karg. Obviously, the karg has to be a valid Python identifier.
It is recommended to only use literals, numbers and underscore.

The following karg values are reserved for special purposes:

- attrib: see :ref:`reserved_key_attrib`
- kargs: see :ref:`reserved_key_kargs`
- field: see :ref:`reserved_key_field`

.. _convert_dict_to_str:

Converting dict to string
.........................
Storing a dict on a file involves converting the dict to a string, and then
writing the string to a text file.
The PZF implementation provides a number of dict to str conversion methods,
identified by a single character. The pzf_dict key for a dict value should
specify this method and be of the form::

  karg:M

where M is the character identifying the conversion method and karg is the
keyword that will be pass the decoded dict to the loader function on readback.
Currently the following values for M are available:

- c: use the :class:`pzffile.Config` class
- j: use Python's json module
- r: use Python's repr function
- p: use Python's pprint function
- P: use Python's pickle module

It is important to understand the limitations of each of these methods.
The method should be choosen such that the whole dict can be converted to a
string and restored from it.
Another consideration is whether the resulting file should
be easily editable or not (the P method is clearly not).
If in doubt, use 'r' or 'p'.

One can also use any custom method, by pre-converting the dict to a string
and passing the string as value in the pzf_dict method.
The key doesn't have a ``:M`` part in this case, as the item's value is a str.
For readback, a custom loader function should be provided, taking
the string as input and properly initializing the object from it
(see :ref:`load-api`).

.. _`reserved_key_attrib`:

Reserved key ``attrib*``
........................
pyFormex objects that are instances of a :class:`Geometry` subclass
can have an attribute ``attrib`` that is a dict-like object storing mostly
drawing options (such as color) to be used with the rendering of the object.
The :meth:`Geometry.pzf_dict` method contains this item, and subclasses
using that method inherit it. On readback the attrib dict is not passed as
an keyword parameter to the loader function, but the contained attributes
are set on the loaded objects using the special ``attrib`` method. Therefore,
this key should not be used for any other purpose.

.. _`reserved_key_kargs`:

Reserved key ``kargs*``
.......................
The pzf_dict from the example above has two items, and thus creates two files
in the PZF archive. If we run the following example::

  somebody = Person('John', 'Doe')
  PzfFile('test_api.pzf').save(johndoe=somebody)

the PZF archive will contain two files:

- johndoe:Person/first_name.txt: a text file with contents 'John'
- johndoe:Person/last_name.txt: a text file with contents 'Doe'

With simple attributes like this, the use of two files is clearly overshoot.
However, most of the pyFormex classes contain attributes which are large NumPy
arrays, and the PZF format was specifically created to store those in an
effective way.

Simple attributes like the above can better be collected in a dict
and stored on a single file. On readback, a special loader function could be
used to restore the individual values and argument names from the loaded dict.
To make this process more easy (and to avoid the use of a special loader
function), the reserved key name ``kargs`` can be used. Just collect
all simple attributes in a dict and put that as value in the pzf_dict and
use as key ``kargs:M``,
where M is again one of the methods from :ref:`convert_dict_to_str`.
On readback, the kargs dict will not be passed to
the loader function (with ``kargs`` as keyword argument), but rather all
individual items from the dict will be passed as keyword arguments. See
:ref:`load-api`.

Thus, in the example above we can simply implement the pzf_dict as follows::

  def pzf_dict(self):
      return { 'kargs:c': self.__dict__ }

and the PZF file then has a single file ``johndoe:Person/kargs:c.txt``
with the contents::

  first_name = 'John'
  last_name = 'Doe'

.. _`value_in_filename`:

Encoding value in filename
..........................
Information can also be encoded directly in the file name, instead of
the file contents. It is normally only done when the
following conditions are met:

- the string representation of the value is simple and short,
- only a few object attributes are encoded in filenames,
- it is interesting for the user to see the value from inspecting the
  contents of the PZF archive, without having to open and read a file.

In order to encode a value into the filename, the pzf_dict should pass
an item with value None and a key that contains the encoded value, in
the following format::

    karg:N__value

where N is one of the following characters identifying the stored value
type:

- b: bool
- i: int
- f: float
- s: str

This generates an empty file and the filename has no suffix.

Continuing on the example above, if we can implement the pzf_dict like this::

  def pzf_dict(self):
        return {f'fullname:s__{self.first_name}_{self.last_name}': None}

the PZF archive will contain an empty file named::

  johndoe:Person/fullname:s__John_Doe

In this case, readback will require a special load function accepting
the argument (see :ref:`load-api`)::

  fullname='John_Doe'


.. _reserved_key_field:

Reserved key ``field*``
.......................
pyFormex objects that are instances of a :class:`Geometry` subclass
have an attribute ``fields`` that stores one or more :class:`Field`
instances defined over the geometry. These objects are stored using
the reserved key ``field*``. The key needs two extra parts of information:
the Field type and the Field name. The Field data are a numpy array, and
will be stored in a .npy file. This results in filenames like::

    name:class/field__fieldtype__fieldname.npy``.

There can be any number of such files for the same object.

:class:`Geometry` subclasses do not have to add these field items to the
pzf_dict.
The :meth:`Geometry.pzf_dict` method provides the proper pzf_dict items.
The subclasses can just initialize their pzf_dict from it and add their
specific items.

.. _filename_structure:

Summary of the file name structure
..................................
The filenames below have the following variable parts:

name
  the name of the object
class
  the name of the class of the restored object, which is usually
  (but not necessarily) the class of the object written
attr
  the name of the attribute, which is not necessarily an attribute
  of the object written:
value
  a value directly stored in the filename
M
  a modifier character, specifying the way to store some value in the
  archive

Some attribute names are reserved and are used in a special way on loading:

kargs
  Defines a dict of keyword arguments to be passed to the loader. This is
  convenient when many simple attributes have to be stored. The 'kargs'
  attribute can be combined with normal named attributes, but will overwrite
  those in case of name clashes.
attrib
  Defines a dict of values that will be loaded via the 'attrib' method of
  the object. This usually contains drawing options for a Geometry object.
field
  Defines a single Field value that will be attached to the Geometry object
  using the addField method.


If the value of an attribute is a dict, the attribute name should have
one of the following modifiers to specify what method is used to convert
the dict to a string:

- ':c' use the :class:`pzffile.Config` class,
- ':j' use the json module to,
- ':r' use Python's repr function.
- ':p' use Python's pprint function.

If a value is to be stored inside the file name, the attribute name
should have one of the following modifiers attached:

- ':b' if the value is a boolean,
- ':i' if the value is an int,
- ':f' if the value is a float,
- ':s' if the value is a string.

If an attribute name does not have a modifier attached, then its value
is stored in numpy's .npy format if the value is a numpy.ndarray, or
as utf-8 text in a .txt file if the value os a string. Other values are
invalid.

Object, class or attribute should not start or end with an underscore
or have a double underscore inside. Also, 'class' can not be use as
attribute name, and 'field' and 'attrib' are reserved attribute names
with a specific meaning for pyFormex Geometry classes. Likewise,
object names '_camera' and '_canvas' are reserved.

Here's a list of the valid file name formats and their use:

- ``name:class/attr.npy``: attr is a numpy ndarray stored on .npy file
- ``name:class/attr.txt``: attr is a str stored on .txt file
- ``name:class/attr:M.txt``: attr is a dict stored  on .txt file
- ``name:class/attr:M__value``: attr is stored in filename
- ``name:class/kargs:M.txt``: attr is a dict stored on .txt file
- ``name:class/attrib:M.txt``: attr is an attrib dict stored on .txt file
- ``name:class/field__fieldtype__fieldname.npy``: an object's Field data
  is stored on the .npy file, the filename contains the Field's type and name.

The reserved attribute name 'kargs' is handled differently than other names.
Its purpose is to store multiple attributes on a single file using one of
the dict modifiers. But while an other attribute with a dict value
will be passed as 'attr=dict_value' argument to the object loader,
the 'kargs' attribute will be passed as ``**kargs``, thus making the
contents of the dict individual items.

As an example, the list of files in the 'saveload.pzf' archive in the
pyformex/data folder is::

  __FORMAT__PZF__2.0
  __METADATA
  F:Formex/coords.npy
  F:Formex/prop.npy
  M:Mesh/coords.npy
  M:Mesh/field__node__dist.npy
  M:Mesh/field__node__dist3n.npy
  M:Mesh/field__elemc__dist3c.npy
  M:Mesh/attrib:j.txt
  M:Mesh/elems.npy
  M:Mesh/eltype:s__quad4
  T:TriSurface/coords.npy
  T:TriSurface/attrib:j.txt
  T:TriSurface/elems.npy
  spiral:PolyLine/coords.npy
  spiral:PolyLine/attrib:j.txt
  spiral:PolyLine/closed:b__False
  CS:CoordSys/rot.npy
  CS:CoordSys/trl.npy
  curve:BezierSpline/attrib:j.txt
  curve:BezierSpline/closed:b__True
  curve:BezierSpline/control.npy
  curve:BezierSpline/degree:i__3
  X:Coords/data.npy
  _canvas:MultiCanvas/kargs:p.txt

From this list it is immediately obvious that the file is a PZF version 2.0
archive and that it contains a Formex named 'F', a Mesh named 'M',
a TriSurface 'T', a PolyLine 'spiral', and some more objects
(among which there is one with a reserved object name: '_canvas'.
We can also see that the Mesh 'M' has an element type 'quad4' and
that the BezierSpline 'curve' is closed and of the third degree.
Furthermore, the Mesh object has three Fields defined on it.

This info can not only be got from the :meth:`files` method,
but can also be seen outside of pyFormex by opening the pzf file in
your file manager: the PZF file is a valid ZIP file and most modern
file managers know how to open zuch an archive and list its contents.
Opening the PZF will likely only show the top level::

  __FORMAT__PZF__2.0
  __METADATA
  F:Formex
  M:Mesh
  T:TriSurface
  spiral:PolyLine
  CS:CoordSys
  curve:BezierSpline
  X:Coords
  _canvas:MultiCanvas

and clicking on any of the subdirectories would show its contents.
You can also use the file manager to delete some objects,
extract the archive, rename the objects, edit some text files,
zip some extracted files to a new pzf file. Just be careful to observe
the file naming rules. Using the PzfFile methods is of course more
secure.

Hey, but what are these files that do not obey the above given file
name rules: __FORMAT__PZF__2.0 and __METADATA?
Filenames starting with double underscores are system files and should
not be meddled with by the user. As you can guess, the __FORMAT__PZF__2.0
declares this file to be a PZF version 2.0 format. Likewise, __METADATA
contains some metadata about the archive. You can open it and read it.
It may look like this::

    format = 'PZF'
    version = '2.0'
    creator = 'pyFormex 3.1.dev0'
    datetime = (2022, 2, 13, 13, 41, 18)

The format info is repeated in the __METADATA file. We keep the
__FORMAT... file to recognize the format immediately without the
need to read __METADATA file from the archive.


.. _`load-api`:

API for loading objects from PZF
--------------------------------
Loading objects from a PZF file using :meth:`PzfFile.load`
processes as follows:

- File names are decomposed into object name, class name,
  keyword and possibly extra items such as modifier, value, suffix.
  The subdirectory name defines the object name and class, the filename
  the other items.
  See `filename_structure`_ for the full set of valid filenames.
- If the file name has no suffix, the value is set from the filename
  (see `value_in_filename`_). If the file name has a suffix .npy,
  the file is read into a numpy array using
  :func:`numpy.lib.format.read_array` and this becomes the value.
  If the suffix is .txt, the file is read as text, and if a modifier was used,
  the resulting string is transformed into a dict.
  Either way, we now have a keyword and a value, which are added to the object
  dict.
- The class name should be a registered class for restoring PZF objects. This
  can have been registered by calling the :func:`pzffile.register` function or
  by using the :func:`utils.pzf_register` decorator on a class definition.
  Note that the registered class for some class name does not have to be the
  same class as the object's class on storing the PZF (though it usually is).
  It is thus possibly to load a PZF into other objects than they were stored
  from.
- The registered class is used to create a Python object from the object dict.
  If the class does not have a ``pzf_load`` method, the class is instantiated
  with the object dict as keyword arguments and the object is an instance
  of the registered class. If a class method ``pzf_load`` exists, this method
  is called with the object dict as keyword args, and the resulting object
  is whatever this returns. See `pzf_load`_.
- The created objects are collected in a dict with the object names as keys
  and the resulting dict is returned.

As an example, take the first PZF from `reserved_key_kargs`_, containing
two files:

- johndoe:Person/first_name.txt: a text file with contents 'John'
- johndoe:Person/last_name.txt: a text file with contents 'Doe'

After reading these files, there will be object named ``johndoe`` with class
name ``Person`` and object dict ``{'first_name':'John', 'last_name':'Doe'}``.
The object will be created as::

    Person(first_name='John', last_name='Doe')

.. _`load_reserved_keywords`:

Handling reserved keywords
..........................
The following reserved keywords are not put into the object dict like the
others, but are handled in a special way: kargs, attrib, field.

kargs
    The kargs keyword requires a dict as value. This dict is used to update
    the object dict (after all normal keywords for the object were added).
    Thus the contents of the kargs dict are keyword parameters passed to
    the object creation.
    Thus, in the second example from `reserved_key_kargs`_, the single file
    ``johndoe:Person/kargs:c.txt`` will lead to exactly the same object dict
    as above.

attrib
    The attrib keyword requires a dict as value. This dict is not used in the
    creation of the object. Rather, after the object has been initialized,
    the objects ``attrib`` method will be called with this dict as the keyword
    arguments. Obviously, this requires a class that has an attrib method
    (such as all the Geometry subclasses in pyFormex).

field
    The field keyword requires a field type and field name encoded in the
    file name, and a numpy array as value. All the field values are collected
    and after the object has been created, the corresponding data are applied
    to the object by calling its :meth:`~Geometry.addField` method.

.. _`pzf_load`:

Custom pzf_load
...............
In some cases the ``__init__`` method of the registered object class is not
fit to reconstruct the object from the stored data. Therefore, a special
method `pzf_load` may be defined in the class to process the object dict
and produce whatever result is required. If an object's registered class
has such a method, it will be called with the contents of the object dict
as keyword parameters, and whatever the method returns will be set as the
object.

In the example from `value_in_filename` there was one file with all
information encoded in the filename::

  johndoe:Person/fullname:s__John_Doe

After reading the file, the object dict for johndoe will look like::

  {'fullname': 'John_Doe'}

Obviously, we can not instantiate the Person class with these keyword
parameters. Therefore, we add a custom loader method to the Person class.
The method accepts the object dict as keyword parameters, and transforms
the info into the proper arguments for the class initialization. Note that
this has to be a class method::

    @classmethod
    def pzf_load(clas, fullname):
	first, last = fullname.split('_')
	return clas(first, last)


.. _`pzf_args`:

Positional arguments
....................
In some cases the object class __init__ or pzf_load method may require the use
of positional arguments. This can be achieved by declaring an attribute
``pzf_args`` containing a list of the keywords from the object dict that
should be passed as positional arguments, in the order of that list.

As an example, the TriSurface initialization signature is::

    def __init__(self, *args, prop=None)

It accepts up to 3 positional arguments, covering these cases:

- none creates an empty object,
- 1: convert from a Coords, Formex or Mesh object,
- 2: coords, elems
- 3: coords, edges, faces

Internally the data are stored as (coords, elems), both being numpy arrays.
It also has an optional ``prop`` keyword argument. The PZF storage mirrors
this and stores coords, elems (and optionally prop). When the object is
restored from PZF, we can not pass the coords and elems as keyword arguments:
they should be passed as two positional arguments. This is achieved by
declaring in the TriSurface class::

    pzf_args = ['coords', 'elems']

An alternative would be to use a pzf_load function::

    @classmethod
    def pzf_load(clas, coords, elems, prop=None):
        return TriSurface(coords, elems, prop=prop)

But obviously, in cases like this, using pzf_args is simpler.

.. _`examples`:

Examples
--------
This section presents some cases from important pyFormex classes.
For clarity they are shown here slightly different from the actual
implementation, where many classes inherit part of their pzf_dict
from a parent class.

Coords
......
The Coords class is a subclass of a numpy.ndarray and does not contain
other data, so we only have to store itself. The Coords __init__ method
gets the data in an argument named data. Thus we just need to define
this pzf_dict in the Coords class::

    def pzf_dict(self):
        return {'data': self}

and register the Coords class::

    @utils.pzf_register
    class Coords:
        ...

Formex
......
A Formex has an attribute coords, which is a Coords (and thus an ndarray),
and has an optional second data attribute, prop, which is also an ndarray.
The pzf_dict looks like::

    def pzf_dict(self):
        d = {'coords': self.coords}
	if self.prop:
            d['prop'] = self.prop
	return d

Mesh
....
A Mesh has attributes coords and elems that are ndarrays, an optional prop
like in the Formex class and eltype, which is an ElementType, but can be
specified by the ElementType's name (a string) in the __init__ method.
This name can be simply encoded in the file name.
The pzf_dict then looks like this::

    def pzf_dict(self):
        d = {
            'coords': self.coords,
	    'elems': self.elems,
	    f"{eltype}:s__{self.eltype.name}": None,
	    }
	if self.prop:
            d['prop'] = self.prop
	return d

TriSurface
----------
TriSurface is a subclass of Mesh with a fixed ElementType ('tri3').
Its pzf_dict is therefore the same as that of Mesh, but without the
eltype entry. However, TriSurface.__init__ has a different signature.
It does not have coords, elems arguments, but rather a list of
positional arguments \*args. Therefore it needs a pzf_args as
discussed in `pzf_args`_.

Polygons
--------
Polygons is like a Mesh, but without eltype and the elems attribute
is a Varray, which itself has two ndarray attributes: data and ind.
The pzf_dict becomes::

    def pzf_dict(self):
        d = {
            'coords': self.coords,
            'elems': self.elems.data,
            'ind': self.elems.ind,
	}
	if self.prop:
            d['prop'] = self.prop
        return d

A pzf_load method is required to restore the Varray before passing
it to the Polygons.__init__::

    @classmethod
    def pzf_load(clas, coords, elems, ind, **kargs):
        return clas(coords, Varray(elems, ind), **kargs)

BezierSpline
------------
A BezierSpline stores three attributes: an ndarray coords, an int degree
and a bool closed. The latter two are encoded in the filename. The coords
attribute has to be passed to the control argument when creating a new
BezierSpline::

    def pzf_dict(self):
        return {
	    'control': self.coords,
            f'degree:i__{self.degree}': None,
            f'closed:b__{self.closed}': None,
        }

Camera
------
The Camera class has a method :meth:`Camera.settings` which returns a dict
with all the parameters from which an identical Camera instance may be
restored. All the parameters are simple enough to be restored from a
string version of the dict. So the pzf_dict can be just::

    def pzf_dict(self):
        return { 'kargs:p': self.settings() }

..
 The reserved attribute 'attrib' is used to store the 'attrib' of
 a Geometry class object as a single dict. Note that if this dict
 contains arrays, only the ':r' modifier will work. The Geometry class
 by default writes it with the JSON ':j' scheme, which can not store
 arrays. However, arrays in attrib can easily be avoided by using Field:
 instead of setting 'color=some_large_color_array' in the attributes,
 one can add 'some_large_color_array' as a Field to the object, with
 'some_field_name', and then set an attribute 'color=fld:some_field_name'
 on the object.

.. ==========================================================================

.. _pyf_file_format:

pyFormex Project File Format (PYF)
==================================

A pyFormex project file is just a pickled Python dictionary stored on file,
possibly with compression. Any pyFormex objects can be exported and stored on
the project file. The resulting file is normally not readable for humans and
because all the class definitions of the exported data have to be present,
the file can only be read back by pyFormex itself.

The format of the project file is therefore currently not further documented.
See :doc:`projects` for the use of project files from within pyFormex.




.. _`pgf_file_format`:

pyFormex Geometry File Format (PGF)
===================================
This describes the pyFormex Geometry File Format (PGF) version 1.6 as
drafted on 2013-03-10 and being used in pyFormex 0.9.0.
The version numbering is such that implementations of a later
version are able to read an older version with the same major numbering.
Thus, the 1.6 version can still read version 1.5 files.

The prefered filename extension for pyFormex geometry files is '.pgf',
though this is not a requirement.

General principles
------------------

The PGF format consists of a sequence of records of two types: comment
lines and data blocks. A record always ends with a newline character,
but not all newline characters are record separators: data blocks may
include multiple newlines as part of the data.

Comment records are ascii and start with a '#' character. Comment records
are mostly used to announce the type and amount of data in the following
data block(s). This is done by comment line containing a sequence of
'key=value' statements, separated by semicolons (';').

Data blocks can be either ascii or binary, and are always announced by
specially crafted comment lines preceding them. Note that even binary
data blocks get a newline character at the end, to mark the end of the
record.


Detailed layout
---------------

The pyFormex Geometry File starts with a header comment line identify
the file type and version, and possibly specifying some global variables.
For the version 1.6 format the first line may look like::

  # pyFormex Geometry File (http://pyformex.org) version='1.6'; sep=' '

The version number is used to read back legacy formats in newer versions
of pyFormex. The `sep = ' '` defines the default data separator for
data blocks that do not specify it (see below).


The remainder of the file is a sequence of comment lines announcing
data blocks, followed by those data blocks. The announcement line
provides information about the number, type and size of data blocks
that follow. This makes it possible to write and read the data using
high speed functions (like `numpy.tofile` and `numpy.fromfile`) and without
having to test any contents of the data.
The data block information in the announcement line is provided by a number
of 'key=value' strings separated with a semicolon and optional whitespace.


Object type specific fields
...........................
For each object type that can be stored, there are some required fields
and data blocks. In the examples below, `<int>` stands for an integer number,
`<str>` for a string, and `<bool>` for either `True` or `False`.

- Formex: the announcement provides at least::

    # objtype='Formex'; nelems=<int>; nplex=<int>

  The data block following this line should contain exactly `nelems*nplex*3`
  floating point values: the 3 coordinates of the `nplex` points of the
  `nelems` elements of the Formex.

- Mesh: the announcement contains at least::

    # objtype='Mesh'; ncoords=<int>; nelems=<int>; nplex=<int>

  In this case two data blocks will follow: first `ncoords*3` float values
  with the coordinates of the nodes; then a block with `nelems*nplex`
  integer values: the connectivity table of the mesh.

- Curve:

Optional fields
...............
The announcement line may contain other fields, usually to define extra
attributes for the object:

- `props=<bool>` : If the value is True, another data block with `nelems`
  integer values follows. These are the property numbers of the object.

- `eltype=<str>` : Can also have the special value None. If specified and
  not None, it will be used to set the element type of the object.

- `name=<str>` : Name of the object. If specified, pyFormex will use this
  value as a key when returning the restored object.

- `sep=<str>` : This field defines how the data are stored. If it is not
  defined, the value from the file header is used.

  - An empty string means that the data blocks are written in binary.
    Floating point values are stored as little-endian 4byte floats, while
    integer values are stored as 4 byte integers.

  - Any other string makes the data being written in ascii mode, with the
    specified string used as a separator between any two values. When
    reading a PGF file, extra whitespace and newlines appearing around the
    separator are silently ignored.



Example
-------

The following pyFormex script creates a PGF file containing two objects,
a Formex with one square, and a Mesh with two triangles::

  F = Formex('4:0123')
  M = Formex('3:112.34').setProp(1).toMesh()
  writeGeomFile('test.pgf',[F,M],sep=', ')

The Mesh has property numbers defined on it, the Formex doesn't.
The data are written in ascii mode with ', ' as separator.
Here is the resulting contents of the file 'test.pgf'::

  # pyFormex Geometry File (http://pyformex.org) version='1.6'; sep=', '
  # objtype='Formex'; nelems=1; nplex=4; props=False; eltype=None; sep=', '
  0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 0.0
  # objtype='Mesh'; ncoords=4; nelems=2; nplex=3; props=True; eltype='tri3'; sep=', '
  1.0, 0.0, 0.0, 2.0, 0.0, 0.0, 1.0, 1.0, 0.0, 2.0, 1.0, 0.0
  0, 1, 3, 3, 2, 0
  1, 1

This file contains two objects: a Formex and a Mesh. The Formex has 1 element
of plexitude 4 and no property numbers. Following its announcement is a single
data block with 1x4x3 = 12 coordinate values.
The Mesh contains 2 elements of plexitude 3, has element type 'tri3' and
contains property numbers. Following the announcement are three data blocks:
first the 4*3 nodal coordinates, then the 2*3 = 6 entries in the connectivity
table, and finally 2 property numbers.

.. End
