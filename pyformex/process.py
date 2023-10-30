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
"""Executing external commands.

This module provides some functions for executing external commands in
a subprocess. They are based on the standard Python :mod:`subprocess`
module, but provide some practical enhancements.

Contents:

- :class:`DoneProcess` is a class to hold information about a terminated
  process.
- :func:`run` runs a command in a subprocess and waits for it to finish.
  Returns a :class:`DoneProcess` about the outcome.
- :func:`start` starts a subprocess and does not wait for it.
  Returns a :class:`subprocess.Popen` instance that can be used to communicate
  with the process.

This module can be used independently from pyFormex.
"""

import subprocess
import shlex
import os


class DoneProcess(subprocess.CompletedProcess):
    """A class to return the outcome of a subprocess.

    This is a subclass of :class:`subprocess.CompletedProcess` with some
    extra attributes.

    Attributes
    ----------
    args: str or sequence of arguments
        The args that were used to create the subprocess.
    returncode: int
        The exit code of the subprocess. Typical a 0 means it ran
        succesfully. If the subprocess fails to start, the value
        is 127. Other non-zero values can be returned by the child
        process to flag some error condition.
    stdout: str or bytes or None
        The standard output captured from the child process.
    stderr: str or bytes or None
        The error output captured from the child process.
    failed: bool
        True if the child process failed to start, e.g. due to a
        non-existing or non-loadable executable. The returncode
        will be 127 in this case.
    timedout: bool
        True if the child process exited due to a timeout condition.

    """
    def __init__(self, args, returncode, *, failed=False, timedout=False,
                 **kargs):
        super().__init__(args, returncode, **kargs)
        self.failed = failed
        self.timedout = timedout

    def __repr__(self):
        """Textual representation of the DoneProcess

        This only shows the non-default values.
        """
        s = super().__repr__()
        i = s.rfind(')')
        s = [s[:i], s[i:]]
        if self.failed:
            s.insert(-1, f", failed={self.failed!r}")
        if self.timedout:
            s.insert(-1, f", timedout={self.timedout!r}")
        return ''.join(s)


    def __str__(self):
        """User-friendly full textual representation

        Returns
        -------
        str
            An extensive report about the last run command, including
            output and error messages.

        Notes
        -----
        This is mostly useful in interactive work, to find out
        why a command failed.
        """
        s = f"DoneProcess report\nargs: {self.args}\n"
        if self.failed:
            s += "Command failed to run!\n"
        s += f"returncode: {self.returncode}\n"
        for atr in ['stdout', 'stderr']:
            val = getattr(self, atr)
            if val is not None:
                s += f"{atr}:\n{val}"
                if s[-1] != '\n':
                    s += '\n'
        if self.timedout:
            s += f"timedout: {self.timedout}\n"
        return s


def run(args, *, input=None, capture_output=True, timeout=None,
        wait=True, **kargs):
    """Execute a command through the operating system.

    Run an external command in a subprocess, waiting for its termination
    or not. This is similar to Python3's :func:`subprocess.run`, but
    provides the following enhancements:

    - If `shell` is True, and no `executable` is provided, the shell
      will default to the value in the user's SHELL environment variable,
      and if that isn't set, to '/bin/sh'.

    - If a string is passed as `args` and `shell` is False, the string is
      automatically tokenized into an args list.

    - If no stdout nor stderr are specified, the output of the command
      is captured by default.

    - The `encoding` is set to 'utf-8' by default, so that stdout
      and stderr are returned as strings.

    - stdin, stdout and stderr can be file names. They will be replaced
      with the opened files (in mode 'r' for stdin, 'w' for the others).

    - Exceptions are captured by default and can be detected from
      the return value.

    - A `wait` parameter allows the same function to be used to just
      start a subprocess and not wait for its outcome.

    Only the new and changed parameters are described hereafter. Except for
    the first (`args`), all parameters should be specified by keyword.
    For more parameters, see :class:`subprocess.run`.

    Parameters
    ----------
    args: str or list of str.
        If a string is provided, it is the command as it should be entered
        in a shell. If it is a list, args[0] is the executable to run
        and the remainder of args are the arguments to be passed to it.

        If a string is provided and `shell` is False (default), the string is
        split into an args list using :func:`shlex.split`.
    capture_output: bool
        If True (default), both stdout and stderr are captured and available
        from the returned :class:`DoneProcess`. Specifying a value for any of
        `stdout` or `stderr` values will however override the capture_output
        setting.
    shell: bool
        Default is False. If True, the command will be run in a new shell.
        The `args` argument should be a string in this case.
        Note that this uses more resources, may cause a problem in killing the
        subprocess and and may pose a security risk.
        Unless you need some shell functionality (like parameter expansion,
        compound commands, pipes), the advised way to execute a command is
        to use the default False.
    executable: str
        The full path name of the program to be executed.
        This can be used to specify the real executable if the
        program specified in `args` is not in your PATH, or,
        when `shell` is True, if you want to use a shell other than
        the default: the value of the 'SHELL' environment variable,
        and if that is not set, '/bin/sh/'.
    encoding: str
        The encoding for the returned stdout and stderr. The default is
        'utf-8', making the returned values Python3 str types. Specifying
        encoding=None will return bytes. Another encoding may be specified
        if needed.
    input: str
        If provided, passes the provided string as stdin to the started
        process. Only available with wait=True.
    timeout: int
        If provided, this is the maximum number of seconds the process is
        allowed to run. After this time the Process will be killed.
    check: bool
        Default is False.
        If True, an exception will be raised when the command did not
        terminate normally: a non-zero returncode, a timeout condition
        or a failure to start the executable. With the default, these
        conditions are captured and reported in the return value.
    **kargs: keyword arguments
        Any other keyword arguments accepted by :class:`subprocess.Popen`.
        See the Python documentation for :class:`subprocess.Popen` for full info.

    Returns
    -------
    :class:`DoneProcess` | :class:`subprocess.Popen`
        If ``wait`` is True (default), returns a :class:`DoneProcess`
        collecting all relevant info about the finished subprocess.
        See :class:`DoneProcess` for details.

        If ``wait`` is False, returns the created :class:`subprocess.Popen`.
        In this case the user if fully responsible for handling the
        communication with the process, its termination, and the processing
        of its outcome.

    Examples
    --------
    >>> P = run("pwd")
    >>> P.stdout.strip('\\n') == os.getcwd()
    True

    >>> P = run("pwd", stdout=subprocess.PIPE)
    >>> P.stdout.strip('\\n') == os.getcwd()
    True

    >>> P = run("echo 'This is stderr' > /dev/stderr", shell=True)
    >>> P.stderr
    'This is stderr\\n'

    >>> P = run('false')
    >>> P
    DoneProcess(args=['false'], returncode=1, stdout='', stderr='')

    >>> P = run('false', capture_output=False)
    >>> P
    DoneProcess(args=['false'], returncode=1)
    >>> P.stdout is None
    True

    >>> P = run('False')
    >>> P
    DoneProcess(args=['False'], returncode=127, failed=True)

    >>> P = run("sleep 5", timeout=1, capture_output=False)
    >>> P
    DoneProcess(args=['sleep', '5'], returncode=-1, timedout=True)

    >>> print(P)
    DoneProcess report
    args: ['sleep', '5']
    returncode: -1
    timedout: True

    >>> P = run("sleep 10", wait=False)
    >>> P.poll() is None
    True
    """
    if capture_output and 'stdout' not in kargs and 'stderr' not in kargs:
        kargs['stdout'] = subprocess.PIPE
        kargs['stderr'] = subprocess.PIPE
    kargs.setdefault('encoding', 'utf-8')
    for f in ['stdin', 'stdout', 'stderr']:
        if f in kargs and isinstance(kargs[f], str):
            if f[-1] == 'n':
                mode = 'r'
            else:
                mode = 'w'
            kargs[f] = open(kargs[f], mode)
    shell = bool(kargs.get('shell', False))
    if shell and 'executable' not in kargs:
        kargs['executable'] = os.environ.get('SHELL', '/bin/sh')
    if isinstance(args, str) and shell is False:
        # Tokenize the command line
        args = shlex.split(args)

    check = kargs.pop('check', False)

    try:
        P = subprocess.Popen(args, **kargs)
    except Exception as e:
        if check:
            raise e
        return DoneProcess(args, 127, failed=True)

    if not wait:
        return P

    with P:
        try:
            stdout, stderr = P.communicate(input, timeout=timeout)
        except subprocess.TimeoutExpired as e:
            if check:
                raise e
            P.kill()
            stdout, stderr = P.communicate()
            return DoneProcess(args, -1, stdout=stdout, stderr=stderr,
                               timedout=True)
        except Exception as e:
            # Unexpected error
            P.kill()
            raise e
        retcode = P.poll()
        if retcode and check:
            raise subprocess.CalledProcessError(
                retcode, args, output=stdout, stderr=stderr)
    return DoneProcess(args, retcode, stdout=stdout, stderr=stderr)



# deprecated: for ccompatibility
def start(args, **kargs):
    return run(args, wait=False, **kargs)


if __name__ == "__main__":
    print("This is process.py")
    P = run("pwd", shell=True)
    print(P)
    P = run("ls -l", stdout="filelist.txt")
    print(P)
    P = run("sleep 50", timeout=2)
    print(P)

### End
