"""pyFormex Script/App Template

Copyright 2022 Benedict Verhegghe (bverheg@gmail.com)
Distributed under the GNU General Public License version 3 or later.

Your source file should start with a docstring like this.
The first line should hold a short description of the file's purpose.
This is followed by a blank line and one or more lines with a more
comprehensive explanation of the script's purpose.

If you want to distribute your script/app, you should insert the
name of the copyright holder and license near the start of this file.
Make sure that you (the copyright holder) have the intention/right to
distribute the software under the specified copyright license (GPL3 or later).

This is a template file to show the general layout of a pyFormex
script or app.

A pyFormex script is just any simple Python source code file with
extension '.py' and is fully read and execution at once.

A pyFormex app can be a '.py' of '.pyc' file, and should define a function
'run()' to be executed by pyFormex. Also, the app should import anything that
it needs.

This template is a common structure that allows the file to be used both as
a script or as an app, with almost identical behavior.

For more details, see the user guide under the `Scripting` section.
"""

# The pyFormex modeling language is defined by everything in
# the gui.draw module (if you use the GUI). For execution without
# the GUI, you should import from pyformex.script instead.
from pyformex.gui.draw import *

# Definitions
def run():
    """Main function.

    This is executed when you run the app.
    """
    print("This is the pyFormex script/app template")

# Code in the outer scope:
# - for an app, this is only executed on loading (module initialization).
# - for a script, this is executed on each run.

print("This is the initialization code of the pyFormex template script/app")

# The following is to make script and app behavior alike
# When executing a script in GUI mode, the global variable __name__ is set
# to '__draw__', thus the run method defined above will be executed.

if __name__ == '__draw__':
    print("Running as a script")
    run()


# End
