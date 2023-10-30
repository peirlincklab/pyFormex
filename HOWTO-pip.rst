..

How to run pyFormex with a different Python version
---------------------------------------------------

.. warning: pyFormex only supports Python versions >= 3.7.0

In some cases you might want to run pyFormex with another Python
version than the standard Python3 version on your system:

- the standard version is not supported by pyFormex,
- you want to use a Python module requiring another Python version,
- you want to experiment with newer Python versions.

This howto explains how it can easily be done. It comes down
to these three steps:

- install the Python version of your liking,
- install a virtual environment to run the newly installed Python
  and install the required Python modules for that version,
- run pyFormex in the virtual environment

Install another Python version
..............................
There are ample guides available on the internet that show you how to
install another Python version on your system. Here we will give short
instructions for Debian/Ubuntu style systems. We suppose you have sudo
rights, so you can install the new Python version system-wide.

Start with upgrading your system and installing the required dependencies
to compile Python from source::

  sudo apt update && sudo apt upgrade
  sudo apt install build-essential zlib1g-dev libncurses5-dev \
    libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev \
    libsqlite3-dev wget libbz2-dev

Next download the required Python version source tarball. In our case
we'll install version 3.10.0::

  wget https://www.python.org/ftp/python/3.10.0/Python-3.10.0.tgz

If you don't know the version, go to the Python download page and select
the correct one. Unpack the source tarball::

  tar -xf Python-3.10.0.tgz

Go to the unpacked source directory, configure the make::

  cd Python-3.10.0/
  ./configure --enable-optimizations

Compile the source::

  make -j $(nproc)

Finally, install the new Python version (make sure to use 'altinstall'
and not 'install')::

  sudo make altinstall

Check your installation::

  $ python3.10 --version
  Python 3.10.0


Create a virtual environment for the new Python
-----------------------------------------------
In order to not mix up modules for your system default Python
and your new Python, you should create a virtual environment
for the latter. This can be placed in a directory anywhere.
If you intend to use the new Python only with pyFormex, you can
even put it in your main pyFormex source tree. We will make
a single base directory 'venv' that can hold multiple virtual
environments for different Python versions::

  mkdir -p ~/venv

Now create the virtual environment for the Python3.10 version::

  python3.10 -m venv ~/venv/310

Activate the environment (notice the dot in front)::

  . ~/venv/310/bin/activate

Within the virtual environment, the active python command will
be your newly installed Python version::

  $ python --version
  Python 3.10.0

You can now install any required Python modules for the
new Python version using pip. First check the pip version::

  $ pip --version
  pip x.y.z from ... (python 3.10)

To install the pyFormex dependencies with pip, you can run the
script 'pip_install' in your top level pyFormex directory::

  cd ~/pyformex
  ./pip_install

When you're done using the virtual environment, you can deactivate
it with::

  deactivate


Running pyFormex inside a virtual environment
---------------------------------------------

Running pyFormex inside a properly create virtual environment is now
as simple as activating the virtual environment and starting pyFormex::

  . ~/venv/310/bin/activate
  pyformex

.. End
