#!/usr/bin/env python3

"""File list utility

This is a small command line utility that exposes the Path.listTree
function with a command line interface. It was created for testing,
but since it proved useful, it is retained and offered for use.
Just symlink the script to a directory into your bin path, and you
can use it from anywhere::

  ln -s REALPATH/listtree.py ~/.local/bin
"""

import sys, os
filename = os.path.realpath(__file__)
sys.path[0:0] = [os.path.dirname(os.path.dirname(os.path.dirname(filename)))]
from pyformex.path import Path

__version__ = '1.0'
mrk = '=='  # level 0 header marker
mrk1 = '--'  # level 1 header marker

def create_parser():
    import argparse
    parser = argparse.ArgumentParser(
        prog=os.path.basename(__file__),
#        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
List directory contents recursively.
This program walks top down though a directory tree and lists its contents.
There are a whole set of arguments to define what is visited or skipped.
""",
epilog="""\
Examples

list -type Hs
"""
    )
    def MO(*args, show_default=" (default: %(default)s)", **kargs):
        if show_default and 'help' in kargs and 'default' in kargs:
            kargs['help'] += show_default
        parser.add_argument(*args, **kargs)

    MO('-p', "--path", action="store", nargs='+', default='.',
       help="Starting directory path(s) to list the contents of. Each PATH should be an existing directory path.")
    MO("--type", dest='ftypes', action='store', default='HSf',
       help="""
Select the entry types to list. It is a combination of the following
characters: f(file), d(dir), h(hidden), s(symlink) or their upper case
version meaning NOT that type. Thus the default HSf will only list files
that are not hidden and are not symlinks. 'HS' will list both files and dirs.
'' lists everything. Include and exclude patterns are regexes by default,
but with the --glob options are interpreted as glob style expressions.
Thus --ifile 'f.*\..py' is equivalent to --file 'f*.py' --glob.
""")
    MO("--dtype", dest='dtypes', action='store', default='HSd',
       help="Select the directory types to walk through.")
    MO("--includedir", "--idir", metavar='DIR', action="extend", nargs="*",
       default=[], help="Pattern for directories to include.")
    MO("--excludedir", "--edir", metavar='DIR', action="extend", nargs="*",
       help="Pattern for directories to exclude.")
    MO("--includefile", "--ifile", metavar='FILE', action="extend", nargs="*",
       help="Pattern for files to include.")
    MO("--excludefile", "--efile", metavar='FILE', action="extend", nargs="*",
       help="Pattern for files to exclude.")
    MO("--include", action="extend", nargs="*",
       help="Pattern for paths to include.")
    MO("--exclude", action="extend", nargs="*",
       help="Pattern for paths to exclude.")
    MO("--maxdepth", action="store", type=int, default=-1,
       help="Maximum directory depth.")
    MO("--mindepth", action="store", type=int, default=0,
       help="Minimum directory depth.")
    MO("--glob", action="store_true",
       help="Use glob style expressions for patterns instead of regexes.")
    MO("--relative", action="store_true",
       help="Report directories relative to path.")
    MO("--decorate", action="store_true",
       help="Decorate file names.")
    MO("--ignore-errors", action="store_true",
       help="Silently skip non-accessible paths.")
    MO("--delete", action="store_true",
       help="Delete all the visited files. Use with care!")
    MO("--dry-run", action="store_true",
       help="Developement dry run.")
    MO("--version", action='version', version=f"path.py {__version__}",
       help="Show the version and exit.")
    MO('-v', "--verbose", action="store", type=int, default=2,
       help="Set the verbosity level: 0: nothing, 1: file names only, 2: file names, dir names, file count, 3: as 2 plus args")
    return parser

def decorated(p):
    if p.is_symlink():
        return f"{p} -> {os.readlink(p)}"
    elif p.is_dir():
        return f"{p}/"
    else:
        return p

def ignore(e):
    pass

def show(path, verbose, decorate, glob, **kargs):
    gtcnt = 0
    tcnt = 0
    onerror = ignore if kargs.pop('ignore_errors') else print
    delete = kargs.pop('delete')
    if delete and verbose > 1:
        print("!! All listed files are deleted !!")
    for root in path:
        if verbose > 1:
            print(f"{mrk} Root: {root} {mrk}")
        dcnt = 0
        for dirname, files in Path(root).walkTree(**kargs, onerror=onerror):
            if len(files) == 0:
                   continue
            if verbose > 1:
                print(f"{mrk1} dir: {dirname} {mrk1}")
            cnt = len(files)
            if verbose > 0:
                for f in files:
                    print(decorated(f) if decorate else f)
                    if delete and f.is_file():
                        os.unlink(f)
            if verbose > 1:
                print(f"{mrk1} #files: {cnt} {mrk1}")
            tcnt += cnt
            dcnt == 1
        if verbose > 1:
            print(f"{mrk} Total for {root}: {tcnt} files in {dcnt} dirs {mrk}")
        gtcnt += tcnt

    if len(path) > 1:
        if verbose > 1:
            print(f"{mrk} Grand total: {gtcnt} files {mrk}")


def main(args):
    import fnmatch
    parser = create_parser()
    options = parser.parse_args(args)
    if options.verbose > 2:
        print(options)
    if options.glob:
        for attr in ['includedir', 'includefile', 'include',
                     'excludedir', 'excludefile', 'exclude']:
            patterns = getattr(options, attr)
            if patterns:
                for i, pat in enumerate(patterns):
                    patterns[i] = fnmatch.translate(pat)
                if options.verbose > 2:
                    print(f"{attr} --> {patterns}")
    if not options.dry_run:
        del options.dry_run
        show(**options.__dict__)

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    main(args)
