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
"""A simple Database class

"""
import json

import pyformex as pf
from pyformex.mydict import Dict


class Record(Dict):
    def __init__(self, data=None):
        super().__init__(default_factory=Dict.returnNone, **data)


class Database(dict):
    """A class for storing data in a database-like structure.

    The Database is a Dict where each key is a unique identifier string
    and each value is a record. A record is itself a Dict , where each
    key is a string (the field name) and the value can be anything.

    Parameters
    ----------
    default_factory: callable, optional
        If provided, missing keys will be looked up by a call to the
        default_factory.
    data: dict | list | str, optional
        The Database can be initialized from a dict, a list of records or
        a file in a proper format.

        If a dict, the Database will be directly initialized from it.

        If a list, each record should have at least a key named 'name',
        holding the string identifying the record. This value should be unique
        in the list (or records will be overwritten). The 'name' value will be
        use as a key to store the record in the Database.

        If a string, it is the name of a Database file in one of the
        supported formats, from where it will be read. See :meth:`read`.

        If not provided, an empty database is constructed.
    key: str, optional
        The field name to be used as a key, if list type data are specified.

    Examples
    --------
    >>> rec1 = {'id': 'john', 'first_name': 'John', 'last_name': 'Doe'}
    >>> rec2 = {'id': 'jane', 'first_name': 'Jane', 'last_name': 'Roe'}
    >>> db = Database(data=[rec1, rec2])
    >>> print(db)
    {
        "john": {
            "id": "john",
            "first_name": "John",
            "last_name": "Doe"
        },
        "jane": {
            "id": "jane",
            "first_name": "Jane",
            "last_name": "Roe"
        }
    }
    >>> db.write('test.json')
    >>> db1 = Database(data='test.json')
    >>> print(db1)
    {
        "john": {
            "id": "john",
            "first_name": "John",
            "last_name": "Doe"
        },
        "jane": {
            "id": "jane",
            "first_name": "Jane",
            "last_name": "Roe"
        }
    }
    >>> print(type(db1['john']))
    <class 'pyformex.database.Record'>

    """
    format = 'pyfdb 1.0'

    def __init__(self, *, data=None, key='id', record=Record):
        """Initialize a database"""
        super().__init__()
        self._key = key
        self._record = record
        if data is not None:
            if isinstance(data, str):
                self.read(data)
            else:
                self.add(data)

    def add(self, data, key=None):
        """Add a list of records to the database.

        Parameters
        ----------
        data: list
            A list of records. Each record should be a dict and have at least
            a field name  equal to the value specified for ``key``.
        key: str, optional
            The field name in the records to be used as the key to store the
            records in the Database.
        """
        if key is None:
            key = self._key
        self.update([(r[key], self._record(r)) for r in data])

    def write(self, filename):
        """Export the Database to a file.

        The file is written in .json format and contains a dict
        with two keys: 'key' and 'records'. The key is a
        """
        contents = list(self.values())
        contents.insert(0, {
            'format': Database.format,
            'creator': pf.fullVersion(),
            'key': self._key,
            'nrecs': len(contents),
        })
        with open(filename, 'w+') as fil:
            json.dump(contents, fil, indent=2)
            fil.write('\n')

    def read(self, filename):
        """Import all records from a Database file.

        Parameters
        ----------
        filename: :term:`path_like`
            The file holding the Database. The file should be in
            .json format as written by :meth:`write`.

        Examples
        --------
        >>> db = Database()
        >>> db.read(pf.cfg['prop/matdb'])
        >>> print(db)
        {
            "steel": {
                "name": "steel",
                "young_modulus": 207000.0,
                "poisson_ratio": 0.3,
                "density": 7.85e-09
            },
        ...
        """
        with open(filename, 'r') as fil:
            contents = json.load(fil)
            header = contents.pop(0)
            if header.get('format', None) != Database.format:
                raise ValueError(
                    f"{filename} is not a pyFormex Database file")
            self.add(contents, key=header['key'])


    def __str__(self):
        return json.dumps(self, indent=4)

# End
