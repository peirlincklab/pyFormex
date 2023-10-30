..
  SPDX-FileCopyrightText: © 2007-2021 Benedict Verhegghe <bverheg@gmail.com>
  SPDX-License-Identifier: GPL-3.0-or-later

  This file is part of pyFormex.
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


.. |date| date::

..
  This document is written in ReST. To see a nicely formatted PDF version
  you can compile this document with the rst2pdf command.

.. _`homepage`: http://pyformex.nongnu.org
.. _`install guide`: http://pyformex.nongnu.org/doc/install.html

=============================
HOWTO for pyFormex developers
=============================
:Date: |date|
:Author: benedict.verhegghe@feops.com


pyFormex repositories
=====================
- development: git@gitlab.com:bverheg/pyformex.git
- public: https://gitlab.com/bverheg/pyformex.git
- public mirror: https://git.savannah.gnu.org/cgit/pyformex.git/


Using the pyFormex repository at gitlab.com
===========================================

Anybody can clone the pyFormex repository with the command::

  git clone https://gitlab.com/bverheg/pyformex.git

However, for developers the prefered way to access the repository is
via ssh, because you will not have to authenticate on every push to the
repository::

  git clone git@gitlab.com:bverheg/pyformex.git


How to become a pyFormex developer
----------------------------------

- register on https://gitlab.com
- send `me <mailto:bverheg@gmail.com` a mail to request membership of the
  pyFormex project as developer.

License
-------
pyFormex is distributed under the GNU GPL version 3 or later. This means that all contributions you make to the pyFormex project will be distributed with this license. By becoming a pyFormex group member and by contributing code or text of any kind, you implicitely agree with the distribution under this license.

The only exception we can make is for material on the pyFormex website that is
not distributed with pyFormex. Media (images, movies) and data files may be placed there under other compatible licenses, but you should explicitely state the license and ask the project manager for approval.


Branching policy
----------------
On moving the pyFormex repository to gitlab, there has been a cleanup and
renaming of the existing branches. It is therefore important to make a new
clone of the repository, and not just change the upstream repository in
your .git/config of an old clone.

We now have the following branches:

- 'master': this is where the development of the next release takes place.
  This branch is protected and can only be changed by members with maintainer
  permissions.
- 'R-x.y(.z): these are branches from previous releases, which are used
  to create bug fixes on these releases. These branches are protected as well.
- Other branches can be created by developers at will and are open to all
  developers. Always use lower case only names.

Since the master branch is protected, developers will have to create another
branch to make changes, and push that branch to the repository::

  git co -b my_branch_name
  git push -u origin my_branch_name

Afterwards, a merge request has to be made (the git push command will
present you the URL to do so) and the maintainer has to approve the
merge.

You can keep a long lived branch with your user name to flag that other
developers should not push to it (unless invited to do so).
Or you can create temporary ad-hoc branches for fixing some bug or for
creating a new feature. Such temporary branches can be flagged to be
deleted after the merge.

Prune branches that were delete remotely
----------------------------------------
If you want to locally delete a branch that was removed from the remote repo,
doing::

  git branch -d branch_name

may not be enough. You may still have some reference to the (deleted)
remote branch. It would e.g. turn up if you do::

  gitk --all

To delete this reference, do::

  git remote prune origin


CI/CD pipeline
--------------
Every push to a branch will cause a continuous integration pipeline to be
started. This pipeline will run the automated tests and try to build a
release package. If anything fails, the branch will not be accepted
for merging into master.

In future we will add more procedures to this pipeline, and hopefully one
day we can do fully automated releases. Anyone with interest and/or knowledge
of gitlab CI/CD is welcome to help developing this.

The pipeline currently runs on Debian 10.5, with an option to run the tests
also on Ubuntu 18.04. Other systems may be added later.

Local testing
-------------
Even with the CI/CD testing in place, it is still important to do local
testing BEFORE pushing your branche commits to the repository.
This may avoid a lot of extra work and resource usage.
Thus, before a push always run::

  pyformex --doctest
  pyformex --pytest

The first command should end with something like this::

  Totals: attempted=1939 tests, failed=0 tests, FAILED=0/159 modules

Check that there are 0 failed tests and 0 FAILED modules. FAILED modules
are modules that failed to be imported under doctest.

The second command ends with something like this::

  ========= 126 passed in 1.00 seconds ===========

There should be no errors reported here.
Warnings are acceptable, but should be investigated
(maybe raise an issue on https://gitlab.com/bverheg/pyformex/-/issues).
They do however not prohibit the pushing and merging into master.


Release numbering
-----------------
From now on primary releases of pyFormex will only have two numbers,
like the last 2.0 release. A third number can be added to create bug
releases on the branch of that release: 2.0.1, 2.0.2, ... .
Release branches are named like 'R-2.0', to easily identify those branches.
For historical reasons there are some branches with 3 numbers and even with
a non-numeric tail, but such version numbers will not be created anymore.



Release a distribution to the general public
--------------------------------------------
This can only be done by a release manager. It still has to be done manually.
Most of this will be entered into the ci/cd pipeline later.

The release is prepared in a private branch and only afterwards merged into
the master. The starting point is a branch that has been through all tests
on at least latest stable Debian and Ubuntu LTS.
Of course the default pipeline should be passed.

We suppose that the VERSION variable in the RELEASE file is the intended
release version and the RELEASE variable has a tail (usually .dev?).
Start by making an official release number::

   make setversion  # Removes the tail
   make lib3        # avoids a library rebuild in the following

- Stamp the files with the version ::

   make stampall

- This step can be skipped: Run the following examples with the
  'pyformex/data' as current workdir
  (you can set it in the GUI Cwd widget). This is needed to update some
  files:

  - FePlast (save as feplast1.inp
  - SpaceTrussRoof_abq
  - WebGL

.. The above could be automated with
   pyformex examples.FePlast ++ examples.SpaceTrussRoof_abq ++ examples.WebGL

- Rebuild the html documentation ::

    make html

- At this point you may try to rebuild the package, install it and checking
  everything before proceeding to the changes that can not be undone. ::

    make dist

  This will check first that all files that would be in the release tarball
  are already checked into the git repository. If not, you are proposed
  the options to either:

  - commit them now with a new commit
  - commit them by amending the last commit
  - stashing them away (the changes will then NOT be in the tarball)
  - quit the procedure (not creating a tarball)

- Create an entry in ReleaseNotes with the most important changes.

- Commit the changes to the branch, push the branch::

    git commit -a -m "Preparing release ..."
    git push

- When the pipeline is passed, merge the branch into master, check out master
  and pull the update::

    git co master
    git pull

- Create a Tag::

    make tag      # requires signing!! and record the created RELEASETAG

- Create the final distribution ::

    make dist
    make signdist
    make latest

- Push the new tag::

    make pushtag

- Push source to Savannah::

   git push public master
   git push public RELEASETAG   # replace RELEASETAG with the one created

- Put the release files on Savannah::

   make pubpdf    # may skip: probably fails
   make pubn
   make pub

- Announce the release on the pyFormex news (Savannah)

  * news
    * submit
    * manage (to approve)

    text: pyFormex Version released....

- Put the HTML documentation on the web site (OBSOLETE) ::

   make pubdoc
   ./publish
   make commit

- Go back to your own (non-master) branch::

    git co <my-branch>

- Bump the RELEASE and VERSION variables in the file RELEASE, then ::

   make bumpversion    # increase version and add a new tail to the RELEASE
   make lib
   git commit -a -m 'Bump release after making official release'
   git push       # push can wait until some other commit is added


Create html documentation
-------------------------
- The documentation is no longer included in the release, but can be build
  on demand (by the user, the installer, or the package builder). The command
  to build the documentation is::

    make html

  for the (prefered) html version and::

    make pdf

  for a pdf version. The latter takes a long time, as it goes through a
  conversion to LaTeX first.

- The documentation can also be built from the Help menu in the pyFormex GUI.

.. ......................................................................

.. warning: The remainder of this document is old and subject to changes.



For new pyFormex developers
===========================


Install required basic tools
----------------------------

You will need a computer running Linux. We advice Debian GNU/Linux, but
other distributions can certainly be used as well. Make sure that you
have internet connection from your Linux system.

- In order to run pyFormex, you need to have some other software packages
  installed on your computer. See the `install guide`_ in the documentation
  for a full list of the prerequisites. On a Debian-like system you can
  install from the top level git tree with:

    ./apt_install_deps


- You certainly need to (learn to) use a decent text editor. pyFormex
  code, documentation, website, tools: everything is based on source text
  files. Since we use a lot of `Python` code, an editor that can nicely
  highlight the Python syntax is recommended. We suggest `emacs` with the
  `python-mode.el` extension (it has a somewhat steep learning curve, but
  this will be rewarded)::

    apt-get install emacs python-mode.el

  Of course, many other editors will qualify as well.

.. note:: We should add a list of other good editors here

- Make sure you have `git` installed. This is the revision control system used
  by pyFormex. And the graphical tool `gitk` may also be helpful.
  To install on Debian GNU/Linux::

    apt-get install git gitk

- Configure git by setting your user name and email address::

    git config --global user.name "John Doe"
    git config --global user.email john.doe@some.where


- We also recommend you to install some aliases as shortcuts for some
  often used commands. For example, add the following section to your
  `~/.gitconfig` file::

    [alias]
	su = status
	st = status -uno
	co = checkout
	ci = commit
	br = branch
	last = log -1 HEAD
	df = diff --ignore-space-change
	find = log --pretty=\"format:%Cgreen%H %Cblue%s\" --name-status --grep


- If you want to work on the documentation (and as a developer you really
  should), then you need `python-sphinx` and `dvipng`::

    apt-get install python-sphinx dvipng

  The installed version of sphinx needs to be patched however. See further
  for how to do this.

- If you want to create source distributions (.tar.gz), you also need::

    apt-get install python-git


Get access to the repositories
------------------------------

While anybody can get read access to the repositories on Savannah,
write access is restricted to pyFormex group members. To authenticate
yourself on Savannah, you need to provide an SSH key. Your SSH key is
a pair of files `id_rsa` and `id_rsa.pub` the directory `.ssh` under
your home directory.

- If you do not have such files, create them first, using the command::

    ssh-keygen

  You can just accept all defaults by clicking 'ENTER'. After that, you
  will have an SSH private,public keypair in your directory `.ssh`.

.. warning:: Never give the private part (`id_rsa`) of your key to anybody
  or do not make it accessible by anybody but yourself!

- The public part (`id_rsa.pub`) should be registered on Savannah
  to get easy developer access to the pyFormex repository.
  Login to Savannah and go to
  *My Account Conf*. Under *Authentication Setup* you can enter your
  public SSH key. Just copy/paste the contents of the file *.ssh/id_rsa.pub*.

.. note::

  If you are connecting from an Ubuntu system, and you find that you still can
  not get access after more than one day, you may try the following:

  - Check the end part of the public SSH key you pasted on Savannah, with the
    help of the scroll bar.
  - If it ends with '/' before "username@host.domain", replace the '/' with '=='.
  - After the update, wait for another day for the server to refresh, then try
    again to access the repository.


Currently, we are also using a developer repository, located on the server
`bumps.ugent.be`. You should also have an ssh account on that server. If
you do not have an account on the bump* servers yet, ask one: mailto:benedict.verhegghe@ugent.be.

Then copy your ssh key to the bumps server::

  ssh-copy-id username@bumps.ugent.be

Note that your username at bumps may be different from that at Savannah

Now you are all set to checkout the pyFormex repository.

Further reading
---------------

This basic guide can not tell you everything you need to know as pyFormex
group member. Depending on your tasks you may at times have to study some
other resources. Hereafter we give a list of the basic tools and software
packages that are needed in developing/documenting/managing/using pyFormex.
For all of these information is widely available on the internet.

.. note:: Maybe add here some good links.


- Python
- Numerical Python (NumPy)
- reStructuredText: http://docutils.sourceforge.net/rst.html
- Sphinx
- OpenGL (PyOpenGL)
- QT4 (PyQt4)
- git: `man git COMMAND` or
  http://www.kernel.org/pub/software/scm/git/docs/ or
  http://git-scm.com/documentation or
  http://gitref.org/index.html or
  http://sitaramc.github.com/gcs/index.html


Using the git repository
------------------------

Read http://sitaramc.github.com/gcs/index.html for definition of some git terms.

Quick overview
..............

- Clone the pyFormex developer repository into a directory `pyformex` (using
  your at the bump* servers)::

    git clone USERNAME@bumps.ugent.be:/srv/git/pyformex.git

  This will create a working directory `pyformex` with a clone of the
  repository (in a hidden subdir `.git`) and a checked out working copy
  of the master branch of the repository. You should be able to run
  pyformex directly from it, just like you previously did with a
  Subversion checkout.

.. note: In case you only want to run/change some version of pyFormex and
   do not want to contribute any changes back to the pyFormex project, you
   can also clone the repository anonymously (see the install manual).

- The .git directory in your repository also contains a config file,
  where you can set configuration items special for this git repository.
  The above mentioned ~/.gitconfig holds for all your git repositories.


- See a status of what has changed (use it often!)::

    git status

  If you have installed the aliases as mentioned above, you can also use the
  short form `git st`. This will give you the status report,without the
  untracked files, which is handy if you tend to collect many files in your git
  directory that should not be in the repository. If you want to see the
  untracked files as well, use `git su` (or `git status`).

- Pull in the changes from the remote repository::

    git pull

  Make sure you have a clean working directory (i.e. no changes) before
  doing that.

- Commit your changes to the remote repository. This is now
  a two-step (or even 3-step) procedure. First you commit the changes to
  your local copy of the repository::

    git commit -a

  You will need to specify a commit message.

  Next you can push your changes up to the remote repository::

    git push


Working with multiple repos
...........................

Once you get sufficiently comfortable with using git, you can also add
the public repository as a remote (using your Savannah username)::

  git remote add public USERNAME@git.sv.gnu.org:/srv/git/pyformex.git

Now the command ::

  git remote -v

will give you something like (replace the user names)::

  origin	bene@bumps.ugent.be:/srv/git/pyformex.git (fetch)
  origin	bene@bumps.ugent.be:/srv/git/pyformex.git (push)
  public	bverheg@git.sv.gnu.org:/srv/git/pyformex.git (fetch)
  public	bverheg@git.sv.gnu.org:/srv/git/pyformex.git (push)

The default remote is 'origin' (the one you initially cloned from).
The 'public' is where you can push changes to make them available to
the general public.

To push your changes to the public repository, you have to specify both the
repository name and branch::

    git push public master

.. warning: Current project policy is that only the project manager pushes
   to the public repository. Other developers should (for now) only push to
   the local remote at bumps.ugent.be.



Switch the master branch
........................

You have a (public) branch NEW, which you want to become the master, while
the current master branch should be kept under the name OLD. We suppose
that both the NEW and master branches are already (updated) in the remote
repository, while OLD is non-existing in the remote.

First make a copy of the current master under the name OLD and save
it to the remote::

  git br OLD
  git push -u origin OLD

The NEW branch has diverted a lot from master, but you still need to
keep the changes from the master branch. So first merge the master
into your NEW branch::

  git co NEW
  git merge --strategy=ours --no-commit master
  git commit          # add information to the template merge message

.. note: If you do not want to provide a commit message, you can do the
   last two commands at once: git merge -s ours master

Finally, got to the master and merge the NEW branch in it::

  git co master
  git merge new


Adding tags
...........

Tags come in two sorts: annotated and lightweight (unannotated).
Always create annotated tags if you intend to push them to the repository.
You can use lightweight tags for your local repository.

All published versions should get a tag. If it is a release, the tag should
be 'release-RELEASE', else just 'RELEASE', where RELEASE is defined in the
RELEASE file.

To show which tags are annotated or not::

  git for-each-ref refs/tags

The tags marked 'tag' are annotated, those marked 'commmit' are not.


Structure of the pyFormex repository
====================================
After you checked out the trunk, you will find the following in the top
directory of your local copy.

:pyformex: This is where all the pyFormex source code (and more) is located.
  Everything that is included in the distributed releases should be located
  under this directory.

:pkg: This directory is where we have the tools for building Debian packages.

:screenshots: This contains some (early) screenshots. It could develop into
  a container for all kinds of promotional material (images, movies, ...)

:sphinx: This is where we build the documentation (not surprisingly, we use
  **Sphinx** for this task). The built documents are copied in `pyformex/doc`
  for inclusion in the release.

:stats: Contains some statistics and tools to gather them.

:user: Contains the minutes of pyFormex user meetings.

:website: Holds the source for the pyFormex website. Since the move to
  Savannah recently, we also use Sphinx to build the website.
  Since the whole html documentation tree is also published as part of
  the website (`<http://www.nongnu.org/pyformex/doc/>`_) we could actually
  integrate the *sphinx* part under *website*. The reasons for keeping them
  apart are:

  - the html documents under *sphinx* are made part of the release (for use
    as local documentation accessible from the pyFormex GUI), but the
    *website* documents are not, and
  - the *sphinx* documents need to be regenerated more often, because of the
    fast development process of pyFormex, while the *website* is more static.

Furthermore the top directory contains a bunch of other files, mostly managing tools. The most important ones will be treated further.



Commit messages
===============

When committing something to a repository, you always need to specify
a commit message. The message should be brief and to the point, but still
complete: describing what was changed and possibly why.

The structure of the commit message should be as follow: a single line
with a short contents, followed by a blank line and then multiple lines
describing all the changes. If you only made a single change,
a single line message is allowed.

If you find yourself writing a very long list of changes, consider
splitting your commit into smaller parts.  Prefixing your comments
with identifiers like Fix or Add is a good way of indicating what type
of change you did.  It also makes it easier to filter the content
later, either visually, by a human reader, or automatically, by a
program.

If you fixed a specific bug or implemented a specific change request,
it is recommended to reference the bug or issue number in the commit
message. Some tools may process this information and generate a link
to the corresponding page in a bug tracking system or automatically
update the issue based on the commit.


Using the *make* command
========================
A lot of the recipes below use the *make* command. There is no place here to give a full description of what this command does (see http://www.gnu.org/software/make/). But for those unfamiliar with the command: *make* creates derived files according to recipes in a file *Makefile*. Usually a target describing what is to be made is specified in the make command (see many examples below). The *-C* option allows to change directory before executing the make. Thus, the command::

  make -C pyformex/lib debug

will excute *make debug* in the directory *pyformex/lib*. We use this a lot to allow most *make* commands be executed from the top level directory.

A final tip: if you add a *-n* option to the make command, make will not actually execute any commands, but rather show what it would execute if the *-n* is left off. A good thing to try if you are unsure.


Create the pyFormex acceleration library
========================================
Most of the pyFormex source code is written in the Python scripting language: this allows for quick development, elegant error recovery and powerful interfacing with other software. The drawback is that it may be slow for loop operations over large data sets. In pyFormex, that problem has largely been solved by using **Numpy**, which handles most such operations by a call to a (fast) compiled C-library.

Some bottlenecks remained however, and therefore we have developed our own compiled C-libraries to further speed up some tasks. While we try to always provide Python equivalents for all the functions in the library, the penalty for using those may be quite high, and we recommend everyone to always try to use the compiled libraries. Therefore, after creating a new local git tree, you should first proceed to compiling these libraries.

Prerequisites for compiling the libraries
-----------------------------------------
These are Debian GNU/Linux package names. They will most likely be available
under the same names on Debian derivatives and Ubuntu and derivatives.

- make
- gcc
- python-dev
- libglu1-mesa-dev


Creating the libraries
----------------------
The source for the libraries are the '.c' files in the `pyformex/lib`
directory of your git tree. You will find there also the equivalent
Python implementations. To compile the liraries, got to ``TOPDIR`` and execute
the command::

  make lib

Note that this command is executed automatically when you run pyFormex directly
from the git sources (see below). This is to ensure that you pick up any changes made to
the library. If compilation of the libraries during startup fails,


Run pyFormex from the checked-out source
========================================
In the toplevel directory, execute the command::

  pyformex/pyformex

and the pyFormex GUI should start. If you want to run this version as your
default pyFormex, it makes sense to create a link in a directory that is in
your *PATH*. On many systems, users have their own *~/bin* directory that is
in the front of the *PATH*. You can check this with::

  echo $PATH

The result may e.g. contain */home/USER/bin*. If not, add the following to your
*.profile* or *.bash_profile*::

  PATH=$HOME/bin:$PATH
  export PATH

and make sure that you create the bin directory if it does not exist.
Then create the link with the following command::

  ln -sfn TOPDIR/pyformex/pyformex ~/bin/pyformex

where ``TOPDIR`` is the absolute path of the top directory (created from the
repository checkout). You can also use a relative path, but this should be
as seen from the ``~/bin`` directory.

After starting a new terminal, you should be able to just enter the command
``pyformex`` to run your git version from anywhere.

When pyformex starts up from the git source, it will first check that the
compiled acceleration libraries are not outdated, and if they are, pyformex
will try to recompile them by invoking the 'make lib' command from the
parent directory. This is to avoid nasty crashes when the implementation of
the library has changed. If this automatic compilation fails, pyformex will
nevertheless continue, using the old compiled libraries or the slower Python
implementation.


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


Style guidelines for source and text files
==========================================

All pyFormex source code should adhere to the recommendations
described in the HOWTO-style.rst document.


Creating pyFormex documentation
===============================

The pyFormex documentation (as well as the website) are created by the
**Sphinx** system from source files written in ReST (ReStructuredText).
Therefore, you need to have Sphinx installed on your system in order to
build the documentation. You will also need `dvipng`.

Install Sphinx and dvipng
-------------------------
On Debian GNU/Linux and derivates, just do ::

    apt-get install dvipng python-sphinx

Writing documentation source files
----------------------------------

pyFormex documentation is written in ReST (ReStructuredText).
The source files are in the ``sphinx`` directory of your git tree
and have an extension ``.rst``.

When you create a new .rst files with the following header::

  ..
  .. include:: defines.inc
  .. include:: links.inc
  ..
  .. _cha:chaptername:

Replace in this header chaptername with the documentation chapter name.

See also the following links for more information:

- guidelines for documenting Python: http://docs.python.org/documenting/index.html
- Sphinx documentation: http://sphinx.pocoo.org/
- ReStructuredText page of the docutils project: http://docutils.sourceforge.net/rst.html

When refering to pyFormex as the name of the software or project,
always use the upper case 'F'. When refering to the command to run
the program, or a directory path name, use all lower case: ``pyformex``.

The source .rst files in the ``sphinx/ref`` directory are automatically
generated with the ``py2rst.py`` script. They will generate the pyFormex
reference manual automatically from the docstrings in the Python
source files of pyFormex. Never add or change any of the .rst files in
``sphinx/ref`` directly. Also, these files should *not* be added into the
git repository.


Adding image files
------------------

- Put original images in the subdirectory ``images``.

- Create images with a transparent or white background.

- Use PNG images whenever possible.

- Create the reasonable size for inclusion on a web page. Use a minimal canvas size and maximal zooming.

- Give related images identical size (set canvas size and use autozoom).

- Make composite images to combine multiple small images in a single large one.
  If you have ``ImageMagick``, the following command create a horizontal
  composition ``result.png``  of three images::

     convert +append image-000.png image-001.png image-003.png result.png


Create the pyFormex manual
--------------------------

The pyFormex documentation is normally generated in HTML format, allowing it
to be published on the website. This is also the format that is included in
the pyFormex distributions. Alternative formats (like PDF) may also be
generated and made available online, but are not distributed with pyFormex.

The ``make`` commands to generate the documentation are normally executed
from the ``sphinx`` directory (though some work from the ``TOPDIR`` as well).

- Create the html documentation ::

   make html

  This will generate the documentation in `sphinx/_build/html`, but
  these files are *not* in the git tree and will not be used in the
  pyFormex **Help** system, nor can they be made available to the public
  directly.
  Check the correctness of the generated files by pointing your
  browser to `sphinx/_build/html/index.html`.

- The make procedure often produces a long list of warnings and errors.
  You may therefore prefer to use the following command instead ::

    make html 2>&1 | tee > build.log

  This will log the stdout and stderr to a file ``build.log``, where you
  can check afterwards what needs to be fixed.

- When the generated documentation seems ok, include the files into
  the pyFormex git tree (under ``pyformex/doc/html``) and thus into
  the **Help** system of pyFormex ::

   make incdoc

  Note: If you created any *new* files, do not forget to ``git add`` them.

- A PDF version of the full manual can be created with ::

   make latexpdf

  This will put the PDF manual in ``sphinx/_build/latex``.

.. warning: I had to install package latexmk lately.

The newly generated documentation is not automatically published on the
pyFormex website. Currently, only the project manager can do that. After you
have made substantial improvements (and checked them in), you should contact
the project manager and ask him to publish the new docs.


Create a distribution
=====================

A distribution (or package) is a full set of all pyFormex files
needed to install and run it on a system, packaged in a single archive
together with an install procedure. This is primarily targeted at normal
users that want a stable system and are not doing development work.

Distribution of pyFormex is done in the form of a 'tarball' (.tar.gz) archive.
You need to have `python-git`, `python-docutils` and `rst2pdf` installed to
create the distribution tarball.
Also, you need to create a subdirectory `dist` in your pyFormex source tree.

Before creating an official distribution, update your tree and commit your
last modifications. Then, in the top directory of your git repo, do ::

  make dist

This will create the package file `pyformex-${VERSION}.tar.gz` in
`dist/`. The version is read from the `RELEASE` file in the top
directory. Do not change the *VERSION* or *RELEASE* settings in this
file by hand: we have `make` commands to do this (see below). Make sure
that the *RELEASE* contains a trailing field (*-aNUMBER*).
This means that it is an (alpha) intermediate, unsupported release.
Official, supported releases do not have the trailer.

Any developer can create intermediate release tarballs and distribute them.
However, *currently only the project manager is allowed
to create and distribute official releases!*

After you have tested that pyFormex installation and operation from the
resulting works fine, you can distribute the package to other users, e.g.
by passing them the package file explicitely (make sure they understand the
alpha status) or by uploading the file to our local file server.
Once the package file has been distributed by any means, you should immediately
bump the version, so that the next created distribution will have a higher number::

  make bumprelease
  git ci -m "Bump release after creating distribution file"

.. note:: There is a (rather small) risk here that two developers might
  independently create a release with the same number.


Things that have to be done by the project manager
==================================================

Extra needed packages:

- cvs, for the pyFormex website at Savannah::

    apt-get install cvs

Make file(s) public
-------------------
This is for interim releases, not for an official release ! See below
for the full procedure to make and publish an official release tarball.

- Make a distribution file (tarball) available on our own FTP server ::

   make publocal

- Make a distribution file available on Savannah FTP server ::

   make pub

- Bump the pyFormex version. While any developer can bump the version,
  it really should only be done after publishing a release (official
  or interim) or when there is another good reason to change the
  version number. Therefore it is included here with the manager's
  tasks. ::

   make bumpversion


Update the website at Savannah
------------------------------
- Checkout the website repo::

    mkdir www
    cd www
    cvs -z3 -d:ext:bverheg@cvs.sv.gnu.org:/web/pyformex co pyformex

  This gives a directory www/pyformex.


Publish the documentation
-------------------------
- Put the html documention on the website ::

   make pubdoc
   ./publish # This should currently be done by the project manager
             # on his laptop!
   # now add the missing files by hand : cvs add FILE
   make commit

- Publish a PDF manual ::

   make pubpdf


Change the pyFormex website
---------------------------

The top tree of the website (everything not under Documentation) has its
source files in the `website` directory. It uses mostly rest and sphinx,
just like the documentation. To create the website::

  cd website
  make html

Look at the result under the _build subdirectory. Some links (notably to
the documentation) will not work from the local files.
If the result is ok, it can be published as follows::

  make pubdoc

This moves the resulting files to the `www` subdirectory, which is a
cvs mirror of the website. Upload the files just as for the documentation::

   cd ..
   ./publish
   make commit


Creating (official) Debian packages
-----------------------------------

.. note: This section needs further clarification

Debian packages are create in the `pkg` subdirectory of the trunk.
The whole process is controlled by the script `_do`. The debian-template
subdirectory contains starting versions of the `debian` files packaging.
They will need to be tuned for the release.

- Install needed software packages for the build process::

    apt-get install debhelper devscripts python-all-dev
    apt-get install libgts-dev libglib2.0-dev libdxflib-dev

  Furthermore you also need to have installed all dependencies for the build,
  as declared in the variables `Build-Depends` and `Build-Depends-Indep` in
  the file `control`.

- Other packages: lintian, libfile-fcntllock-perl

- Go to the `pkg` directory. The `_do` procedure should always be executed
  from here.

- Prepare the package creation. This will set an entry in the debian/changelog
  file. If the package to be created is for a new pyFormex version/release,
  use::

    ./_do prepare

  If the new package is a fix for the previous package of the same pyFormex
  release, use::

    ./_do prepfix

  Then carefully edit the changelog file, respecting all whitespace.

  - Replace UNRELEASED with unstable.
  - Add the reason for the new package next to the *
  - Remove all entries below that have a ~a field in the release.

- Unpack latest release::

    ./_do unpack

  This unpacks the latest source
  distribution (from the `dist/` or `dist/pyformex/` subdirectory) in
  a directory `pyformex-VERSION` and copies the `debian-template` as a
  starting `debian` subdirectory.
- Edit the files in the generated `pyformex-VERSION/debian` subdirectory.
  At least a new entry in the file `changelog` needs to be added.
  Other files that are likely to require changes are `control` and `rules`.

.. note: If errors occur during the build, you will most likely have to fix
   the files in `debian` and then rerun the build. Often a rebuild requires
   a clean first. Beware that this will remove your changes and reinstall
   the original `debian` files. It is therefore adviced to edit the
   files in `debian-template` instead of those in `pyformex-VERSION/debian`.
   Then do a `_do clean unpack`.

- Build the packages::

    ./_do build | tee log

  This will build the python modules,
  the compiled libraries and the extra binaries under a path
  `pyformex-VERSION/debian/tmp` and install the needed files into
  the package directories `pyformex`, `pyformex-lib` and `pyformex-extras`.

  Check that no errors occur during the procedure. A log file is written
  for each package.

- Test installing and running of the packages::

    ./_do install

- If OK, build final (signed)::

    ./_do clean unpack final | tee build.log

- List contents (example) ::

    dpkg --contents pyformex_1.0.4-a3-1_all.deb

- Put on local mini-dinstall repository::

    dput local pyformex_1.0.4-a3-1_amd64.changes

- Completely rework a version::

    rm -rf  *1.0.4-a3*

- Sync our local repo with public on bumps.ugent.be::

    rsync /srv/packages/deb bumps.ugent.be:/srv/packages -av

The following should currently not be used.

- upload to Debian mentors::

    _do upload

- upload to local repository and make available::

    _do uploadlocal
    _do publocal


Test installation on other distributions
----------------------------------------
- Run other distribution from a docker image. Example::

    $ docker run -it ubuntu:18.04

- In the docker image::

    # apt update
    # apt install lsb_release wget
    # wget http://download.savannah.nongnu.org/releases/pyformex/pyformex-2.2.tar.gz
    # tar xvzf pyformex-2.2.tar.gz
    # cd pyformex-2.2
    # bash apt_install_deps

- If this fails with *pyside2* packages not found, try::

    # bash apt_install_deps debian:9

Remove old packages from mini-dinstall repository
-------------------------------------------------
On bumps in /srv/package do

rm all the relevant files from the repo directory:

rm foobar.{tar.gz,deb,dsc,changes}

run mini-dinstall in batch mode:

mini-dinstall -b

re-sign the Release file:

gpg --detatch-sign -o Release.gpg Release



.. End
