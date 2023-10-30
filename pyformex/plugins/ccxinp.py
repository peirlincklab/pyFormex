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
"""Interface with Abaqus/Calculix FE input files (.inp).

Attributes
----------
skip_unknown_eltype: bool
    If True, element blocks with an unrecognized element type are skipped.
    If False (default), an exception will be raised.

"""
import re
import numpy as np
from pyformex import Path
from pyformex import arraytools as at

_re_eltypeB = re.compile(r"^(?P<type>B)(?P<ndim>[23])(?P<degree>\d)?(?P<mod>(OS)?H*)$")
_re_eltype = re.compile(r"^(?P<type>[A-Z]+)(?P<ndim>[23]D)?(?P<nplex>\d+)?(?P<mod>[HIMRSW]*)$")

#
# List of known Abaqus/Calculix element type
#
#

abq_elems = [
    'B21', 'B21H', 'B22', 'B22H', 'B23', 'B23H',
    'B31', 'B31H', 'B32', 'B32H', 'B33', 'B33H',
    'C3D4', 'C3D4H',
    'C3D6', 'C3D6H',
    'C3D8', 'C3D8I', 'C3D8H', 'C3D8R', 'C3D8RH', 'C3D10',
    'C3D10H', 'C3D10M', 'C3D10MH',
    'C3D15', 'C3D15H',
    'C3D20', 'C3D20H', 'C3D20R', 'C3D20RH',
    'CAX6', 'CAX8', 'CAX8R',
    'CONN2D2', 'CONN3D2',
    'CPE3', 'CPE3H',
    'CPE4', 'CPE4H', 'CPE4I', 'CPE4IH', 'CPE4R', 'CPE4RH',
    'CPE6', 'CPE6H', 'CPE6M', 'CPE6MH',
    'CPE8', 'CPE8H', 'CPE8R', 'CPE8RH',
    'CPEG3', 'CPEG3H',
    'CPEG4', 'CPEG4H', 'CPEG4I', 'CPEG4IH', 'CPEG4R', 'CPEG4RH',
    'CPEG6', 'CPEG6H', 'CPEG6M', 'CPEG6MH',
    'CPEG8', 'CPEG8H', 'CPEG8R', 'CPEG8RH',
    'CPS3',
    'CPS4', 'CPS4I', 'CPS4R',
    'CPS6', 'CPS6M',
    'CPS8', 'CPS8R', 'CPS8M',
    'DASHPOTA',
    'FRAME2D', 'FRAME3D',
    'M3D3',
    'M3D4', 'M3D4R',
    'M3D6', 'M3D8',
    'M3D8R',
    'M3D9', 'M3D9R',
    'MASS',
    'S3', 'S3R', 'S3RS',
    'S4', 'S4R', 'S4RS', 'S4RSW', 'S4R5',
    'S8R', 'S8R5',
    'S9R5',
    'SPRINGA',
    'STRI3', 'STRI65',
    'SC8R',
    'SFM3D3',
    'SFM3D4', 'SFM3D4R',
    'SFM3D6',
    'SFM3D8', 'SFM3D8R',
    'T2D2', 'T2D2H', 'T2D3', 'T2D3H',
    'T3D2', 'T3D2H', 'T3D3', 'T3D3H',
    'R2D2', 'RB2D2', 'RB3D2', 'R3D3', 'R3D4',
    'RAX2',
]

ccx_elems = [
    'B31', 'B32', 'B32R',
    'C3D6', 'C3D8', 'C3D8I', 'C3D10', 'C3D15', 'C3D20', 'C3D20R',
    'CAX6', 'CAX8', 'CAX8R',
    'CPE4', 'CPE8', 'CPE8R', 'CPS4', 'CPS8', 'CPS8R',
    'D',
    'DASHPOTA',
    'DCOUP3D',
    'F3D8', 'F3D8R',
    'GAPUNI',
    'M3D3', 'M3D4', 'M3D8',
    'MASS',
    'S4', 'S6', 'S8', 'S8R',
    'SPRING1', 'SPRING2', 'SPRINGA',
    'T2D2',
    'T3D2',
    'T3D3',
    'U1',
]

# Element types with a single fixed plexitude
# Fill these in for unknown eltypes to make them recognized
fixed_nplex = {
    'MASS': 1,
}

# Default pyFormex element types
# The base key is nplex. the secondary key is the ndim
pyf_eltypes = {
    1: 'point',
    2: 'line2',
    3: 'tri3',
    4: {2: 'quad4', 3: 'tet4'},
    6: {2: '', 3: 'wedge6'},
    8: {2: 'quad8', 3: 'hex8'},
    9: 'quad9',
    10: 'tet10',
    15: '',
    20: 'hex20',
}


def abq_eltype(eltype):
    """Analyze an Abaqus element type and return eltype characteristics.

    Returns a dictionary with:

    - type: the element base type
    - ndim: the dimensionality of the model space
    - nplex: the plexitude (number of nodes)
    - mod: a modifier string
    - pyf: the corresponding pyFormex element type (this can be a dict
      with nplex as key)

    Currently, all these fields are returned as strings. We should probably
    change ndim and nplex to an int.
    """
    if eltype.startswith('B'):
        m = _re_eltypeB.fullmatch(eltype)
    else:
        m = _re_eltype.fullmatch(eltype)
    if m:
        d = m.groupdict()
        if d['type'] == 'B':
            degree = int(d['degree'])
            nplex = 3 if degree == 2 else 2
        elif d['type'] == 'FRAME':
            nplex = 2
        elif d['type'] in ['SPRINGA', 'DASHPOTA']:
            nplex = (1, 2)
            d['pyf'] = {1: 'point', 2: 'line2'}
        else:
            if d['nplex'] is not None:
                nplex = int(d['nplex'])
            else:
                nplex = fixed_nplex.get(d['type'], None)
                if nplex is None:
                    return {}

        if d['type'] in ('B', 'T'):
            d['pyf'] = f'line{nplex}'
        d['nplex'] = nplex
        if 'ndim' not in d or d['ndim'] is None:
            if d['type'][:2] in ['CP', 'CA', 'S']:
                d['ndim'] = '2'
        if d['type'] in ['R'] and d['nplex']==4:
            d['ndim'] = '2'
        try:
            ndim = int(d['ndim'][0])
        except Exception:
            ndim = 3
        d['ndim'] = ndim
        if 'mod' not in d or d['mod'] is None:
            d['mod'] = ''
        d['avail'] = 'A'   # Available in Abaqus
        if 'pyf' not in d:
            eltype = pyf_eltypes.get(d['nplex'], '')
            if isinstance(eltype, dict):
                eltype = eltype[d['ndim']]
            d['pyf'] = eltype
    else:
        d = {}
    return d


known_eltypes = {
    1: {'point': ['SPRINGA', 'DASHPOTA', 'MASS']},
    2: {'line2': ['SPRINGA', 'DASHPOTA', 'CONN', 'FRAME',
                  'T', 'B', 'RB', 'RAX',
                  ]},
    3: {'line3': ['B', ],
        'tri3': ['M', 'CPS', 'CPE', 'CPEG', 'S', 'SFM', 'R', ]},
    4: {'quad4': ['M', 'CPS', 'CPE', 'CPEG', 'S', 'SFM', 'R', ],
        'tet4': ['C', ]},
    6: {'': ['M', 'CPS', 'CPE', 'CPEG', 'SFM', ],
        'wedge6': ['C', ]},
    8: {'quad8': ['M', 'CPS', 'CPE', 'CPEG', 'CAX', 'S', 'SFM', ],
        'hex8': ['C', ]},
    9: {'quad9': ['M', 'S']},
    10: {'tet10': ['C', ]},
    15: {'': ['C', ]},
    20: {'hex20': ['C', ]},
}


def print_catalog(short=False):
    for el in abq_elems:
        d = abq_eltype(el)
        if d:
            if short:
                print(f"Eltype {el} = {d['pyf']}")
            else:
                print(f"Eltype {el} = {d}")
        else:
            print(f"No match: {el}")

#
#  TODO: S?R5 elements are scanned wrongly
#

class InpModel():
    pass


model = None
system = None
skip_unknown_eltype = False
log = None
part = None
datadir = None


def startPart(name):
    """Start a new part."""
    global part
    print(f"Start part {name}")
    model.parts.append({'name': name})
    part = model.parts[-1]


def readCommand(line):
    """Read a command line, return the command and a dict with options"""
    if line[0] == '*':
        line = line[1:]
    s = line.split(',')
    s = [si.strip() for si in s]
    cmd = s[0]
    opts = {}
    for si in s[1:]:
        kv = si.split('=')
        k = kv[0]
        if len(kv) > 1:
            v = kv[1]
        else:
            v = True
        opts[k] = v
    return cmd, opts


def _do_HEADING(opts, data):
    """Read the nodal data"""
    model.heading = '\n'.join(data)


def _do_PART(opts, data):
    """Set the part name"""
    print(opts)
    startPart(opts['NAME'])


def _do_SYSTEM(opts, data):
    """Read the system data"""
    global system
    if len(data) == 0:
        system = None
        return

    s = data[0].split(',')
    A = [float(v) for v in s[:3]]
    try:
        B = [float(v) for v in s[3:]]
    except Exception:
        B, C = None, None
    if len(data) > 1:
        C = [float(v) for v in data[1].split('')]
    else:
        B[2] = 0.
        C = [-B[1], B[0], 0.]
    t = np.array(A)
    if B is None:
        r = None
    else:
        r = at.rotmat(np.array([A, B, C]))
    system = (t, r)


def _do_NODE(opts, data):
    """Read the nodal data"""
    print(f"NODES: {len(data)}")
    nnodes = len(data)
    print(f"Read {nnodes} nodes")
    ndata = len(data[0].split())
    if isinstance(datadir, Path):
        filename = datadir / f"{part['name']}-NODE.data"
        print(f"Write nodes to {filename}")
        with open(filename, 'w') as f:
            f.write(',\n'.join(data))
    data = ','.join(data)
    x = np.fromstring(data, dtype=np.float32, count=ndata*nnodes,
                      sep=',').reshape(-1, ndata)
    nodid = x[:, 0].astype(np.int32)
    coords = x[:, 1:]

    if system:
        t, r = system
        if r is not None:
            coords = np.dot(coords, r)
        coords += t

    if 'coords' in part:
        part['nodid'] = np.concatenate([part['nodid'], nodid])
        part['coords'] = np.concatenate([part['coords'], coords], axis=0)
    else:
        part['nodid'] = nodid
        part['coords'] = coords
    print(f"#NODES in part: {len(part['coords'])}")


def _do_ELEMENT(opts, data):
    """Read element data"""
    if 'elems' not in part:
        part['elems'] = []
    if 'elid' not in part:
        part['elid'] = []
    sim_type = opts['TYPE']
    print(f"ELEMENT: {sim_type} {len(data)}")
    if sim_type.startswith('B3'):
        nextranodes = 1
    else:
        nextranodes = 0
    d = abq_eltype(sim_type)
    eltype = d.get('pyf', None)
    if not eltype:
        msg = f"Element type '{sim_type}' can not yet be imported"
        if skip_unknown_eltype:
            print(msg)
            log.write(msg)
            return
        else:
            raise ValueError(msg)

    if isinstance(eltype, dict):
        plex = np.asarray([d.count(',') for d in data])
        plexes = np.unique(plex)
        if len(plexes) > 1:
            # We have to split the data
            print(data)
            print(plex)
            raise ValueError(
                'Mixed plexitude SPRINGA/DASHPOTA elements are not yet implemented')
        else:
            nplex = plexes[0]
            split_data = {nplex: (eltype[nplex], data)}
    else:
        nplex = d['nplex']
        split_data = {nplex: (eltype, data)}

    for nplex in split_data:
        eltype, data = split_data[nplex]
        nelems = len(data)
        print(f"Read {nelems} elements of type {sim_type} "
              f"-> {eltype}, plexitude {nplex}")
        ndata = 1 + nplex + nextranodes  # elem number, nodes, extranodes
        ncomma = ndata-1
        if nextranodes > 0:
            # add extranodes for elements missing them
            missing = ncomma - np.asarray([d.count(',') for d in data])
            if (missing > 0).any():
                data = [d if c <= 0 else d + ', -1'*c
                        for c, d in zip(missing, data)]
                print("Added missing extra nodes")
        if isinstance(datadir, Path):
            elemfile = datadir / f"{part['name']}-ELEMENT.data"
            with open(elemfile, 'w') as f:
                f.write(',\n'.join(data))
        e = np.fromstring(','.join(data), dtype=np.int32, count=ndata*nelems,
                          sep=',').reshape(-1, ndata)
        elid = e[:, 0]
        elems = e[:, 1:] if nextranodes <= 0 else e[:, 1:-nextranodes]
        print(f"#ELEMS: {elems.shape} of type {eltype} "
              f"using nodes {elems.min()}..{elems.max()}")
    part['elems'].append((eltype, elems))
    part['elid'].append(elid)
    print(f"Element blocks: {len(part['elems'])}")


def endCommand(cmd, opts, data):
    global log
    func = f"_do_{cmd}"
    if func in globals():
        globals()[func](opts, data)
    else:
        log.write(f"Don't know how to handle keyword '{cmd}'\n")


#  TODO: Add a abaqus/calculix flavour argument
def readInpFile(fn, tempdir=None):
    """Read an input file (.inp)

    Tries to read a file in Abaqus INP format and returns the recognized
    meshes.

    Parameters
    ----------
    fn: :term:`path_like`
        The filename of the input path.
    tempdir: :term:`path_like`, optional
        The pathname to a directory where intermediary data can be stored.
        If not provided, no intermediary data are stored.

    Warning
    -------
    Element blocks with an unrecognized element type will raise an exception,
    unless :attr:`~plugins.ccxinp.skip_unknown_eltype` is set to True.

    Returns
    -------
    InpModel
        A data class with the following attributes:

        - `heading`: the heading read from the .inp file
        - `parts`: a list with parts. See Notes

    Notes
    -----
    Each part is a dict and can contain the following keys:

    - `name`: string: the part name
    - `coords`: float (nnod,3) array: the nodal coordinates
    - `nodid`: int (nnod,) array: node numbers; default is np.arange(nnod)
    - `elems`: int (nelems,nplex) array: element connectivity
    - `elid`: int (nelems,) array: element numbers; default is np.arange(nelems)

    See Also
    --------
    :func:`fileread.readINP`: read an INP file and return FEModel objects.
    """
    global line, part, log, model, datadir
    fn = Path(fn)
    logname = Path('.') / fn.stem + '_ccxinp.log'
    model = InpModel()
    model.parts = []
    startPart('DEFAULT')
    cmd, opts = '', None
    if tempdir is None:
        datadir = None
    else:
        datadir = Path(tempdir)
        datadir.mkdir(exist_ok=True)


    with open(logname, 'w') as log:
        with open(fn) as fil:
            data_cont = False
            data = []
            for line in fil:
                if len(line) == 0:
                    break
                if line.startswith('**'):
                    # skip comments
                    continue
                line = line.upper()
                if line.startswith('*'):
                    if cmd:
                        endCommand(cmd, opts, data)
                        cmd = ''
                    if line[1] != '*':
                        data = []
                        cmd, opts = readCommand(line[1:])
                        log.write(f"Keyword {cmd}; Options {opts}\n")
                        data_cont = False
                else:
                    line = line.strip()
                    if data_cont:
                        data[-1] += line
                    else:
                        data.append(line)
                    data_cont = line.endswith(',')

    print(f"Number of parts in model: {len(model.parts)}")
    return model


if __name__ in ('__draw__', '__script__'):

    def print_match():
        for eltype in abq_elems:
            if eltype.startswith('B'):
                m = _re_eltypeB.fullmatch(eltype)
            else:
                m = _re_eltype.fullmatch(eltype)
            if m:
                print(f"{eltype}: {m.groupdict()}")
            else:
                print(f"{eltype} NOT RECOGNIZED")

    print_match()
    print_catalog()


# End
