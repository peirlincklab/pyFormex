#!/usr/bin/env python3
##
##  This file is part of pyFormex 0.8.6  (Mon Jan 16 21:15:46 CET 2012)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2011 (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
##  Distributed under the GNU General Public License version 3 or later.
##
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
#
"""manifest_check.py

Check that the files in MANIFEST are valid for distribution.
This is done separately from the MANIFEST creator, because manifest.py
is also included in the distribution, while this scipt is not.
"""
import os, sys

def gitRepo(path='.'):
    import git
    return git.Repo(path)


def gitFileStatus(repo,files=None):
    status = {}
    st = repo.git.status(porcelain=True)
    for line in st.split('\n'):
        st = line[:2]
        fn = line[3:]
        if files is not None and fn not in files:
            st = 'ND'
        if st not in status:
            status[st] = []
        status[st].append(fn)
    return status

def get_manifest_files():
    return [ f.strip('\n') for f in open('MANIFEST').readlines() if not f.startswith('#')]


def printfiles(files):
    print('  '+'\n  '.join(files))


def filterFileStatus(status,files):
    for st in status:
        status[st] = [ f for f in status[st] if f in files ]
    return status


def checkFileStatus(repo, files):
    """Check the status of files in the repo

    Returns True if any file has a check status
    """
    status = gitFileStatus(repo)
    status = filterFileStatus(status, files)
    check = {
        ' M': 'Modified files',
        '??': 'Untracked files',
        'ND': 'Undistributed files',
        'NF': 'Unfound files',
        }
    for st in check:
        if st in status and status[st]:
            print('\n'+check[st]+':')
            printfiles(status[st])
    return any(status.values())


if __name__ == '__main__':

    allowed_branches = ['benedict']

    print("="*70)

    # get the repo
    repo = gitRepo()
    try:
        branch = repo.active_branch
        if repo.active_branch.name not in allowed_branches:
            raise ValueError(f"You can only do this on branches {allowed_branches}")
        print(f"Checking branch {branch}")
    except Exception as e:
        print(e)
        sys.exit()

    # get the manifest file list
    files = get_manifest_files()
    print("Checking %s manifest files" % len(files))

    while checkFileStatus(repo, files):
        print("-"*70)
        print("!!! YOU SHOULD FIX THE ABOVE PROBLEM(S) FIRST !!!")
        if os.environ.get('CICD', '') == '1':
            ans = 'q'
        else:
            ans = input(" a: amend last commit; c: create new commit; s: stash; q: quit : ")
        if ans == 'a':
            print("Amending last commit")
            repo.git.commit(all=True, amend=True, no_edit=True)
        elif ans == 'c':
            print("Creating new commit")
        elif ans == 's':
            print("Stashing changes")
        else:
            print("Exiting")
            sys.exit(1)
    print("="*70)


# End
