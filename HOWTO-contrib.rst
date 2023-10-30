..

Guidelines about contributing to the pyFormex project
-----------------------------------------------------

pyFormex is a public open source project, distributed under the GPL v3 or
higher. You are welcome to contribute, but should adhere to some basic
rules.

- Only commit things when you are sure tht they can be distributed freely
  under the GPL3. This means things that you wrote yourself, or that you got
  under license that allows you to do this.

- New files should be add to the proper subdirectory (see below). If unsure,
  ask the project leader where it should go.

- Data files should be separated from the source. Large data files should be
  avoided or compressed.

- File names should not contain spaces or weird characters.

- All source files should include a proper copyright notice, or be in a directory
  that explains the copyright of the included files.

- All source files should be documented as to what is the purpose and how
  it should be used.


pyformex directory structure
----------------------------

pyformex
    The core files. These are considered more or less finalized,
    contain the basic tools, will remain available, should not depend on
    GUI or OpenGL.

pyformex/appsdir
    Fully fledged pyFormex applications that are distributed with pyFormex.

pyformex/attic
    Old stuff that is not working or not interesting anymore, but that we
    do not yet want to remove

pyformex/bin
    Executable that are distributed with pyFormex (usually they are scripts,
    things requiring compilation should go in extra)

pyformex/data
    Data files (anything that is not source or executable). Typically here go
    data that are needed by some pyFormex examples/scripts/applications.

pyformex/doc
    Documentation: this currently mainly includes the local html docs.

pyformex/examples
    Official pyFormex example scripts. These are scripts/apps that are
    structured according to specific guidelines and appear in the
    GUI scripts/apps menu.

pyformex/experimental
    Nothing in this directory should be commited nor distributed.

pyformex/extra
    Accompanying software. These are separate packages each in its own
    directory. In most cases they need to be compiled in order to be used.

pyformex/fe
    Finite element related modules

pyformex/fonts
    Font files for use in pyFormex.

pyformex/freetype
    The source for interfacing with freetype libraries (to create
    pyFormex font files).

pyformex/glsl
    OpenGL shader programs

pyformex/gui
    The GUI components (except for the low level OpenGL stuff)

pyformex/icons
    Icons for use in the GUI

pyformex/lib
    pyFormex acceleration library: compiled C-modules and emulated Python
    versions

pyformex/opengl
    The low level OpenGL rendering engine (normally not used directly)

pyformex/plugins
    Source modules that are considered not fully mature yet (ranging from
    almost mature to just started development). This is the typical place
    where one would add new stuff.

pyformex/scripts
    A place for interesting pyFormex scripts that are distributed with pyFormex.
    Comparable with pyformex/appsdir, but for simple scripts.

pyformex/test
    This is where pyFormex test modules are to be placed. This is meant only
    for official and automated testing. The test modules should use the
    pytest framework. Do not put example scripts here!

.. End
