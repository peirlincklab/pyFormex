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



.. _sec:scripting:

pyFormex scripting
==================

While the pyFormex GUI provides some means for creating and transforming
geometry, its main purpose and major strength is the powerful scripting
language. It offers you unlimited possibilities to do whatever you want and
to automize the creation of geometry up to an unmatched level.

Currently pyFormex provides two mechanisms to execute user applications: as a
*script*, or as an *app*. The main menu bar of the GUI offers two menus
reflecting this. While there are good reasons (of both historical and technical
nature) for having these two mechanisms, the fist time user will probably
not be interested in studying the precise details of the differences between
the two models. It suffices to know that the script model is well suited for
small, quick applications, e.g. often used to test out some ideas.
As your application grows larger and larger, you will gain more from the *app*
model. Both require that the source file(s) be correctly formatted Python
scripts. By obeing some simple code structuring rules, it is even possible
to write source files that can be executed under either of the two models.
The pyFormex template script as well as the many examples coming with
pyFormex show how to do it.



Scripts
-------

A pyFormex *script* is a simple Python source script in a file (with '.py'
extension), which can be located anywhere on the filesystem. The script is
executed inside pyFormex with an ``exec`` statement. pyFormex provides a
collection of global variables to these scripts: the globals of module
``gui.draw`` if the script is executed with the GUI, or those from the
module ``script`` if pyformex was started with ``--nogui``. Also, the
global variable ``__name__`` is set to either 'draw' or 'script', accordingly.
The automatic inclusion of globals has the advantage that the first time user
has a lot of functionality without having to know what he needs to import.

Every time the script is executed (e.g. using the start or rerun button),
the full source code is read, interpreted, and executed. This means that
changes made to the source file will become directly available. But it also
means that the source file has to be present. You can not run a script from
a compiled (``.pyc``) file.


Apps
----

A pyFormex *app* is a Python module. It is usually provided as a Python
source file (``.py``), but it can also be a compiled (``.pyc``) file.
The app module is loaded with the ``import`` statement. To allow this, the
file should be placed in a directory containing an '__init__.py' file (marking
it as a Python package directory) and the directory should be on the pyFormex
search path for modules (which can be configured from the GUI App menu).

In order to be executable from the GUI, an app module should contain a
function named 'run'.
When the application is started for the first time (in a session), the module
is loaded and its 'run' function is executed. Each following execution will just
execute the 'run' function again.

When loading a module from source code, it gets compiled to byte code
which is saved as a ``.pyc`` file for faster loading next time. The
module is kept in memory until explicitely removed or reloaded
(another ``import`` does not have any effect).  During the loading of
a module, executable code placed in the outer scope of the module is
executed. Since this will only happen on first execution of the app,
the outer level should be seen as initialization code for your
application.

The 'run' function defines what the application needs to
perform. It can be executed over and over by pushing the 'PLAY' button.
Making changes to the app source code will not have any effect, because
the module loaded in memory is not changed.
If you need the module to be reloaded and the initialization code to be rerun
use the 'RERUN' button: this will reload the module and execute 'run'.


How to choose between script or app
-----------------------------------
Both scripts and apps have their pros and cons. We list some of them below


+-------------------------------------+---------------------------------------+
|         Script                      |            App                        |
+-------------------------------------+---------------------------------------+
| - Only source code (.py)            | + Source code (.py) or compiled (.pyc)|
+-------------------------------------+---------------------------------------+
| ? Read and compiled on every run    | ? Read and compiled once per session  |
|                                     | or when explicitely requested,        |
|                                     | run many times unchanged              |
+-------------------------------------+---------------------------------------+
| Can only import functionality from  | Direct import from any other app.     |
| a script structured as a module.    |                                       |
+-------------------------------------+---------------------------------------+
| Attributes need to be searched and  | The module can have any attributes    |
| decoded from the soure text         |                                       |
+-------------------------------------+---------------------------------------+
| A script can not execute another    | One app can import and run another    |
+-------------------------------------+---------------------------------------+
| It is impossible to run multiple    | It **might** become possible to run   |
| scripts in parallel.                | multiple applications in parallel,    |
|                                     | e.g. in different viewports.          |
+-------------------------------------+---------------------------------------+
| Global variables of all scripts     | Each app has its own globals          |
| occupy single scope                 |                                       |
+-------------------------------------+---------------------------------------+
| Scripts and plugins are two         | Apps and plugins (menus or not) are   |
| different things.                   | both just normal Python modules.      |
+-------------------------------------+---------------------------------------+
| Exit requires special function      | Exit with the normal return statement |
+-------------------------------------+---------------------------------------+
| Canvas settings are global to all   | Canvas settings **could** be made     |
| scripts                             | local to applications                 |
+-------------------------------------+---------------------------------------+
| Data persistence requires export to | Data persistence between invokations  |
| the pyFormex GUI dict PF and reload | is automatic (for module globals)     |
+-------------------------------------+---------------------------------------+


In favor of *script*:

+-------------------------------------+---------------------------------------+
|         Script                      |            App                        |
+-------------------------------------+---------------------------------------+
| Default set of globals provided     | Everything needs to be imported       |
|                                     | (can be limited to 1 extra line)      |
+-------------------------------------+---------------------------------------+
| Globals of previous scripts are     | Communication between scripts needs   |
| accessible (may be unwanted)        | explicit exports (but is more sound)  |
| (IS THIS STILL TRUE?)               |                                       |
+-------------------------------------+---------------------------------------+
| Users are used to it since longtime | The difference is not large though.   |
+-------------------------------------+---------------------------------------+
| Can be located anywhere.            | Have to be under sys.path (can be     |
|                                     | configured and expanded).             |
+-------------------------------------+---------------------------------------+
| Can easily execute a small piece of | We may have to keep a basic script    |
| Python code, not even in a file, eg | exec functionality next to the app    |
| ToolsMenu: Execute pyFormex command | framework                             |
+-------------------------------------+---------------------------------------+



Problems with apps
------------------

- Apps with syntax errors can not be loaded nor run. Exceptions raised
  during application load are filtered out by default. Setting the
  configuration variable 'raiseapploadexc' to True will make such errors
  be shown.

- Apps creating a permanent (non-blocking, modeless) dialog can currently
  not be rerun (reload and run). We could add such facility if we use
  a default attribute name, e.g. _dialog. Reloading would then close the
  dialog, and running would reopen it.




Environment for scripts/apps
----------------------------
When executing a script or an app, there are a lot of identifiers already
defined. This is what we call the pyFormex core language. Historically,
this included a huge number of definitions in the global namespace, but
the intention is to cut this down in future, so using specific imports is
highly recommended.


Common script/app template
--------------------------
The template below is a common structure that allows this source to be used both
as a script or as an app, and with almost identical behavior.

  .. literalinclude:: static/scripts/template.py
     :linenos:


The script/app source starts by preference with a docstring, consisting of a
short first line, then a blank line and one or more lines explaining the
intention and working of the script/app.


Convert a script to an app
--------------------------
The following steps will convert most pyFormex scripts into an equivalent app:

- Put all the script code (except initial imports) into a function named 'run'.
- Replace all lines::

    exit()

  with::

    return

- Add a line on top to import everyhing from the gui.draw module::

    from gui.draw import *

If you want the app to still be executable as a script, add the following
at the bottom::

  if __name__ == "draw"
      run()

If your app/script should work both with or without the pyFormex GUI,
use this structure::

  import pyformex as pf
  if pf.GUI:
     from gui.draw import *
     < DEFINITIONS FOR GUI VERSION >
  else:
     from gui.script import *
     < DEFINITIONS FOR NONGUI VERSION >

  < COMMON DEFINITIONS FOR BOTH CASES>

Of course, when your definitions become long it may be better to put them in
separate files::

  import pyformex as pf
  if pg.GUI:
     import myapp_gui
  else:
     import myapp_nongui




.. End
