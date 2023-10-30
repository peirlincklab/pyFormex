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
"""A general yet simple configuration class.

| (C) 2005, 2021 Benedict Verhegghe
| Distributed under the GNU GPL version 3 or later

Why
   I wrote this simple class because I wanted to use Python
   expressions in my configuration files. This is so much more fun
   than using .INI style config files.  While there are some other
   Python config modules available on the web, I couldn't find one
   that suited my needs and my taste: either they are intended for
   more complex configuration needs than mine, or they do not work
   with the simple Python syntax I expected.

What
   Our Config class is just a normal Python dictionary which can hold
   anything.  Fields can be accessed either as dictionary lookup
   (config['foo']) or as object attributes (config.foo).  The class
   provides a function for reading the dictionary from a flat text
   (multiline string or file). I will always use the word 'file'
   hereafter, because that is what you usually will read the
   configuration from.  Your configuration file can have named
   sections. Sections are stored as other Python dicts inside the top
   Config dictionary. The current version is limited to one level of
   sectioning.
"""

from pyformex.mydict import Dict
from pyformex import Path


def formatDict(d):
    """Format a Config in Python source representation.

    Each (key,value) pair is formatted on a line of the form::

       key = value

    If all the keys are strings containing only characters that are
    allowed in Python variable names, the resulting text is a legal
    Python script to define the items in the dict. It can be stored
    on a file and executed.

    This format is the storage format of the Config class.

    Examples
    --------
    >>> print(formatDict({'str':'abc', 'path':Path(), 'int':4}))
    str = 'abc'
    path = Path('.')
    int = 4
    """
    s = ""
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, (str, bytes)):
                s += f"{k} = {v!r}\n"
            elif isinstance(v, Path):
                s += f"{k} = Path(v!r)\n"
            else:
                s += f"{k} = {v}\n"
    return s


# TODO: Sections should have a read-only feature to avoid updating
#       a default. Suppose a Config C1 has a section 'S',
#       and an Config C2 has C1 as default, then
#       C1['S/K'] = V       will update section S in C1
#       C2['S']['K'] = V    will also update section S in C1  !! UNWANTED
#       C2['S/K'] = V       will update section S in C2

class Section(Dict):
    """A class for storing a section in a :class:`Config`.

    This is an empty class definition. It only exists to give the
    sections another name.
    """
    # TODO: this is work in progress
    # def __setitem__(self, key, val):
    #     """Allows items to be set as self[section/key] = val.

    #     """
    #     raise ValueError("Can not change Section")
    pass


class Config(Dict):
    """A configuration class allowing Python expressions in the input.

    The Config class is a subclass of the :class:`Dict` mapping, which
    provides access to items by either dict-style key lookup
    ``config['foo']``, attribute syntax ``config.foo`` or call syntax
    ``config('foo')``. Furthermore, the Dict class allows a default_factory
    function to lookup in another Dict. This allows a chain of Config
    objects: session_prefs -> user_prefs -> factory_defaults.

    The Config class is different from its parent Dict class in two ways:

    - Keys should only be strings that are valid Python variable names,
      except that they can also contain a '/' character.
      The '/' splits up the key in two parts: the first part becomes a
      key in the Config, and its value is a :class:`Section` dict where
      the values are stored with the second part of the key.
      This allows for creating sections in the configuration. Currently
      only one level of sectioning is allowed (keys can only have a single
      '/' character.

    - A Config instance can be initialized or updated with a text in
      Python source style. This provides an easy way to store
      configurations in files with Python style. The Config class also
      provides a way to export its contents to such a Python source text:
      updated configurations can thus be written back to a configuration
      file. See Notes below for details.

    Parameters
    ----------
    data: dict or multiline string, optional
        Data to initialize the Config. If a dict, all keys should follow
        the rules for valid config keys formulated above.
        If a multiline string, it should be an executable Python source
        text, with the limitations and exceptions outlined in the Notes
        below.
    default: :class:`Config` object, optional
        If provided, this object will be used as default lookup for
        missing keys.

    Notes
    -----
    The configuration object can be initialized from a dict or from
    a multiline string. Using a dict is obvious: one only has to obey
    the restriction that keys should be valid Python variable names.

    The format of the multiline config text is described hereafter.
    This is also the format in which config files are written and
    can be loaded.

    All config lines should have the format: key = value, where key is a
    string and value is a Python expression The first '=' character on the
    line is the delimiter between key and value.  Blanks around both the
    key and the value are stripped.  The value is then evaluated as a
    Python expression and stored in a variable with name specified by the
    key. This variable is available for use in subsequent configuration
    lines. It is an error to use a variable before it is defined.  The
    key,value pair is also stored in the Config dictionary, unless the key
    starts with an underscore ('_'): this provides for local variables.

    Lines starting with '#' are comments and are ignored, as are empty
    and blank lines.  Lines ending with '\' are continued on the next
    line.  A line starting with '[' starts a new section. A section is
    nothing more than a Python dictionary inside the Config
    dictionary. The section name is delimited by '['and ']'. All
    subsequent lines will be stored in the section dictionary instead
    of the toplevel dictionary.

    All other lines are executed as Python statements. This allows
    e.g. for importing modules.

    Whole dictionaries can be inserted at once in the Config with the
    update() function.

    All defined variables while reading config files remain available
    for use in the config file statements, even over multiple calls to
    the read() function. Variables inserted with addSection() will not
    be available as individual variables though, but can be accessed as
    ``self['name']``.

    As far as the resulting Config contents is concerned, the following are
    equivalent::

       C.update({'key':'value'})
       C.read("key='value'\\n")

    There is an important difference though: the second line will make a
    variable key (with value 'value') available in subsequent Config read()
    method calls.


    Examples
    --------
    >>> C = Config('''# A simple config example
    ...     aa = 'bb'
    ...     bb = aa
    ...     [cc]
    ...     aa = 'aa'    # yes ! comments are allowed)
    ...     _n = 3       # local: will get stripped
    ...     rng = list(range(_n))
    ...     ''')
    >>> C
    Config({'aa': 'bb', 'bb': 'bb', 'cc': Section({'aa': 'aa', 'rng': [0, 1, 2]})})
    >>> C['aa']
    'bb'
    >>> C['cc']
    Section({'aa': 'aa', 'rng': [0, 1, 2]})
    >>> C['cc/aa']
    'aa'
    >>> C.keys()
    ['aa', 'bb', 'cc', 'cc/aa', 'cc/rng']

    Create a new Config with default lookup in C

    >>> D = Config(default=C)
    >>> D
    Config({})
    >>> D['aa']       # Get from C
    'bb'
    >>> D['cc']       # Get from C
    Section({'aa': 'aa', 'rng': [0, 1, 2]})
    >>> D['cc/aa']            # Get from C
    'aa'
    >>> D.get('cc/aa','zorro')      # but get method does not cascade!
    'zorro'
    >>> D.keys()
    []

    Setting values in D will store them in D while C remains unchanged.

    >>> D['aa'] = 'wel'
    >>> D['dd'] = 'hoe'
    >>> D['cc/aa'] = 'ziedewel'
    >>> D
    Config({'aa': 'wel', 'dd': 'hoe', 'cc': Section({'aa': 'ziedewel'})})
    >>> C
    Config({'aa': 'bb', 'bb': 'bb', 'cc': Section({'aa': 'aa', 'rng': [0, 1, 2]})})
    >>> D['cc/aa']
    'ziedewel'
    >>> D['cc']
    Section({'aa': 'ziedewel'})
    >>> D['cc/rng']
    [0, 1, 2]
    >>> 'bb' in D
    False
    >>> 'cc/aa' in D
    True
    >>> 'cc/ee' in D
    False
    >>> D['cc/bb'] = 'ok'
    >>> D.keys()
    ['aa', 'dd', 'cc', 'cc/aa', 'cc/bb']
    >>> del D['aa']
    >>> del D['cc/aa']
    >>> D.keys()
    ['dd', 'cc', 'cc/bb']
    >>> D.sections()
    ['cc']
    >>> del D['cc']
    >>> D.keys()
    ['dd']

    """

    _filename = None

    def __init__(self, data={}, default=Dict.returnNone):
        """Creates a new Config instance.

        The configuration can be initialized with a dictionary, or
        with a variable that can be passed to the read() function.
        The latter includes the name of a config file, or a multiline string
        holding the contents of a configuration file.
        """
        super().__init__(default_factory=default)
        if isinstance(data, dict):
            self.update(data)
        elif data:
            self.read(data)
        Config._filename = None


    def update(self, data={}, name=None, removeLocals=False):
        """Add a dictionary to the Config object.

        The data, if specified, should be a valid Python dict.
        If no name is specified, the data are added to the top dictionary
        and will become attributes.
        If a name is specified, the data are added to the named attribute,
        which should be a dictionary. If the name does not specify a
        dictionary, an empty one is created, deleting the existing attribute.

        If a name is specified, but no data, the effect is to add a new
        empty dictionary (section) with that name.

        If removeLocals is set, keys starting with '_' are removed from the
        data before updating the dictionary and not
        included in the config. This behaviour can be changed by setting
        removeLocals to false.
        """
        if removeLocals:
            for k in list(data.keys()):
                if k[0] == '_':
                    del data[k]
        if name:
            if name not in self or not isinstance(self[name], dict):
                self[name] = Section()
            self[name].update(data)
        else:
            super().update(data)


    def _read_error(self, lineno, line):
        if self._filename:
            where = f"config file {Config._filename}"
        else:
            where = ''
        raise RuntimeError(f"Error in {where} line {lineno}:\n{line}")


    def load(self, filename, debug=False):
        """Read a configuration from a file in Config format.

        Parameters
        ----------
        filename: :term:`path_like`
            Path of a text file in Config format.

        Returns
        -------
        Config
            Returns the Config self, updated with the settings read from
            the specified file.
        """
        Config._filename = Path(filename)
        with Config._filename.open('r') as fil:
            self.read(fil, debug=debug)
        Config._filename = None
        return self


    def read(self, txt, debug=False):  # noqa: C901
        """Read a configuration from a file or text

        `txt` is a sequence of strings. Any type that allows a loop like
        ``for line in txt:``
        to iterate over its text lines will do. This could be an open file, or
        a multiline text after splitting on '\\n'.

        The function will try to react intelligently if a string is passed as
        argument. If the string contains at least one '\\n', it will be
        interpreted as a multiline string and be splitted on '\\n'.
        Else, the string will be considered and a file with that name will
        be opened. It is an error if the file does not exist or can not be
        opened.

        The function returns self, so that you can write: cfg = Config().
        """
        if isinstance(txt, str) and '\n' in txt:
            # It is a multiline string: config text
            # Convert to list of strings
            Config._filename = None
            txt = txt.split('\n')
        else:
            # It is an open file or list of strings
            pass

        globals().update(self)
        section = None
        contents = {}
        lineno = 0
        continuation = False
        comments = False
        for line in txt:
            lineno += 1
            ls = line.strip()
            if comments:
                comments = ls[-3:] != '"""'
                ls = ''
            else:
                comments = ls[:3] == '"""'

            if comments or len(ls)==0 or ls[0] == '#':
                continue

            if continuation:
                s += ls  # noqa: F821
            else:
                s = ls

            continuation = s[-1] == '\\'
            if s[-1] == '\\':
                s = s[:-1]

            if continuation:
                continue

            if s[0] == '[':
                if contents:
                    self.update(name=section, data=contents, removeLocals=True)
                    contents = {}
                i = s.find(']')
                if i<0:
                    self.read_error(lineno, line)
                section = s[1:i]
                if debug:
                    print(f"Starting new section '{section}'")
                continue
            else:
                if debug:
                    print("READ: "+line)
            i = s.find('=')
            if i >= 0:
                key = s[:i].strip()
                if len(key) == 0:
                    self.read_error(lineno, line)
                contents[key] = eval(s[i+1:].strip())
                globals().update(contents)
            else:
                exec(s)
        if contents:
            self.update(name=section, data=contents, removeLocals=True)
        return self


    def __setitem__(self, key, val):
        """Allows items to be set as self[section/key] = val.

        """
        i = key.rfind('/')
        if i == -1:
            self.update({key: val})
        else:
            self.update({key[i+1:]: val}, key[:i])


    def __getitem__(self, key):
        """Allows items to be addressed as self[key].

        This is equivalent to the Dict lookup, except that items in
        subsections can also be retrieved with a single key of the format
        section/key.
        While this lookup mechanism works for nested subsections, the syntax
        for config files allows for only one level of sections!
        Also beware that because of this functions, no '/' should be used
        inside normal keys and sections names.
        """
        i = key.rfind('/')
        if i == -1:
            return super().__getitem__(key)
        else:
            try:
                d = self[key[:i]]
                if d is None:
                    raise KeyError(key[:i])
                return d[key[i+1:]]
            except KeyError:
                return self.__missing__(key)


    def __delitem__(self, key):
        """Allows items to be deleted with del self[section/key].

        """
        i = key.rfind('/')
        if i == -1:
            if key in self:
                super().__delitem__(key)
        else:
            try:
                del self[key[:i]][key[i+1:]]
            except Exception:
                pass


    def __contains__(self, key):
        """Allows to test for a key or section/key"""
        i = key.rfind('/')
        if i == -1:
            return super().__contains__(key)
        else:
            section = key[:i]
            return (super().__contains__(section) and
                    isinstance(self[section], Section) and
                    key[i+1:] in self[section])



    def __str__(self):
        """Format the Config in a way that can be read back.

        This function is mostly used to format the data for writing it to
        a configuration file. See the write() method.

        The return value is a multiline string with Python statements that can
        be read back through Python to recreate the Config data. Usually
        this is done with the Config.read() method.
        """
        s = ''
        for k, v in self.items():
            if not isinstance(v, Section):
                s += formatDict({k: v})
        for k, v in self.items():
            if isinstance(v, Section):
                s += f"\n[{k}]\n"
                s += formatDict(v)
        return s


    def write(self, filename,
              header="# Config written by pyFormex    -*- PYTHON -*-\n\n",
              trailer="\n# End of config\n"):
        """Write the config to the given file

        The configuration data will be written to the file with the given name
        in a text format that is both readable by humans and by the
        Config.read() method.

        The header and trailer arguments are strings that will be added at
        the start and end of the outputfile. Make sure they are valid
        Python statements (or comments) and that they contain the needed
        line separators, if you want to be able to read it back.
        """
        filename = Path(filename)
        with filename.open('w') as fil:
            fil.write(header)
            fil.write(f"{self}")
            fil.write(trailer)

        return filename


    def keys(self, descend=True):
        """Return the keys in the config.

        Parameters
        ----------
        descend: bool, optional
            If True (default) also reports the keys in Section objects with
            the combined section/item keys. This is the proper use for a
            Config with optional sections.
            If False, no keys in sections are reported, only the section names.
        """
        keys = list(super().keys())
        if descend:
            for k, v in self.items():
                if isinstance(v, Section):
                    keys += [f"{k}/{ki}" for ki in v]

        return keys


    def sections(self):
        """Return the sections"""
        return [k for k in self if isinstance(self[k], Section)]


if __name__ == '__main__':

    import doctest
    print(doctest.testmod())

# End
