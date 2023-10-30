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

"""Timer: Measuring elapsed time.

.. note:: Contrary to its use in plain English, we use the word 'timer'
   here for a device that measures the time between two events, not one
   that counts down a given amount of time.

The Timer class provides a convenient way to measure the time between two
events. When developing algorithms for operations on large data models,
accurate and multiple measurements of the time spent in different parts
of the code are a vital accessory. The Timer class aims at making the
process of measuring and reporting as simple is possible for a variety
of uses. The following examples illustrate the most common use cases.

Examples
--------
We use :func:`time.sleep` to provide a dummy code block with some known
execution time.

>>> from time import sleep

The example below shows the three basic steps: create a timer, make
a measurement, report the result. A Timer instance acts as a context
manager, so it can be used in a with statement. The time spent in the
block inside the with clause is then measured.

>>> t = Timer()      # 1. create a Timer
>>> with t:          # 2. measure the time for a code block
...     sleep(0.07)
>>> print(t)         # 3. report the measured time
Timer: 0.07... sec. Acc: 0.07... sec.

Notice that two values are printed out: the first is the measured time,
the second is the accumulated time of all measurements with this timer.
Let's add a second measurement:

>>> sleep(0.05)
>>> with t:
...     sleep(0.06)
>>> print(t)
Timer: 0.06... sec. Acc: 0.13... sec.

Notice that only the time inside the with block is measured.
Printing out the Timer after measurement is so common, that there is
an option to do it automatically. Just set the auto mode on
(this can also be given as an option when creating the Timer).

>>> t.auto = True
>>> with t:
...     sleep(0.03)
Timer: 0.03... sec. Acc: 0.16... sec.

If you do not need the accumulation feature, you can switch it off by
setting acc=None. We create a new Timer t1, with appropriate tag. The
tag is the string printed before the timer values (the default tag is
'Timer'):

>>> with Timer('No accumulation', auto=True, acc=None) as t1:
...     sleep(0.07)
No accumulation: 0.07... sec.
>>> with t1: sleep(0.13)
No accumulation: 0.13... sec.

You can specify the precision of the output (the actual readings
are still done at the highest precision):

>>> t2 = Timer('Precision 2', dec=2, auto=True)
>>> with t2: sleep(0.057)
Precision 2: 0.06 sec. Acc: 0.06 sec.
>>> with t2: sleep(0.093)
Precision 2: 0.09 sec. Acc: 0.15 sec.

When using multiple timers it is often convenient to be able to use a single
variable to keep all Timer instances alive, or to print all the timers at once.
The :class:`Timers` class provides a list of Timer instances to allow that.

>>> timers = Timers(t, t1, t2)
>>> print(timers)
Timer report
  Timer: 0.03... sec. Acc: 0.16... sec.
  No accumulation: 0.13... sec.
  Precision 2: 0.09 sec. Acc: 0.15 sec.
>>> print(len(timers))
3

Plain list methods can be used on the Timers class, but you shouldn't add
anything but Timer instances. The :meth:`get` method retrieves a Timer by its
tag. If multiple timers have the same tag, you can only get the first one.

>>> print(timers.get('No accumulation'))
No accumulation: 0.13... sec.
>>> t3 = Timer('Precision 2')
>>> timers.append(t3)
>>> print(len(timers))
4
>>> timers.get('Precision 2') is t3
False
>>> timers.get('Precision 2') is t2
True
>>> timers.clear()
>>> print(len(timers))
0

Timer context managers can be nested, so one can easily do partial
and overall timings at the same time:

>>> with Timer("Outer block", dec=2, reg=timers):
...    sleep(0.08)
...    with Timer("Inner block", dec=2, reg=timers):
...        sleep(0.12)
...    sleep(0.07)
...    with Timer("Inner block 2", dec=2, reg=timers):
...        sleep(0.17)
...    sleep(0.06)
...
>>> print(timers)
Timer report
  Outer block: 0.50 sec. Acc: 0.50 sec.
  Inner block: 0.12 sec. Acc: 0.12 sec.
  Inner block 2: 0.17 sec. Acc: 0.17 sec.

The output of the above on some machine gave::

    Process time: 0.02... sec. Acc: 0.02... sec.
    Real time: 0.08... sec. Acc: 0.08... sec.

There may be times when the use of a context manager is not useful
or even possible (like when the start and end of measurement are in
different functions). Then you can always use the low level interface.
The measurement is always done with the :meth:`read` method. It measures
and returns the time since the last :meth:`start` or the creation of the
Timer. Here is an example:

>>> t = Timer(dec=2)
>>> sleep(0.03)
>>> v = t.read()
>>> sleep(0.05)
>>> t.start()
>>> sleep(0.07)
>>> v1 = t.read()
>>> print(v, v1)
0.03... 0.07...

The last reading and the accumulated value remain accessible for
further processing or customized reports:

>>> print(t2.mem, t2.acc)
0.09... 0.15...
>>> print(f"'{t2.tag}' timer: last read {t2.mem}"
...       f", accumulated {t2.acc}")
'Precision 2' timer: last read 0.09, accumulated 0.15

You can have a peek at the current value of the timer, without
actually reading it, and thus not chainging the timer's memory:

>>> print(t)
Timer: 0.07 sec. Acc: 0.10 sec.
>>> sleep(0.09)
>>> print(t.value)
0.09...
>>> print(t)
Timer: 0.07 sec. Acc: 0.10 sec.

Measuring process time is easy as well. Just provide another time measuring
function:

>>> timers = Timers(
...     Timer('Real time', auto=True, dec=2, acc=None),
...     Timer('Process time', auto=True, acc=None, timefunc=time.process_time)
... )
>>> with timers:
...     _ = [i*i for i in range(10_000)]  # do something
...     sleep(0.06)
Process time: 0.00... sec.
Real time: 0.06 sec.
"""
import time


class Timer:
    """A class for measuring elapsed time.

    The Timer class is a conventient way to measure and report the elapsed
    time during some processing. It uses Python's :func:`time.perf_counter`,
    providing the highest resolution available. It is however not intended
    for doing micro measurements: use Python's :mod:`timeit` module for
    that.

    A Timer instance can be used as a context manager, with automatic
    reading and even reporting the time spent in the context block.
    The Timer value is a floating point value giving a number of seconds
    elapsed since some undefined reference point. By default this is the
    moment of creation of the Timer, but the starting point can be set at
    any time.

    Parameters
    ----------
    tag: str, optional
        A label identifying the Timer. It is shown together with the
        time value when printing the Timer. It is also used as the key
        when registering a Timer.
    timefunc: callable, optional
        A callable returning a float. The difference in value between two calls
        is the measured time in seconds. The default :func:`time.perf_counter`
        measures real time with high precision. Some other useful values:
        :func:`time.time`, :func:`time.monotonic`, :func:`time.process_time`,
        :func:`time.thread_time`.
    dec: int, optional
        The number of decimals that will be shown when printing the Timer.
        The default (6) provides microsecond accuracy, which is more than
        enough for all purposes.
    acc: float | None, optional
        Starting value for the accumulator. When a Timer is read,
        it accumulates the value in its :attr:`acc` attribute. The
        accumulted value is printed out together with the reading.
        A special value None may be provided to switch off the accumulator.
    auto: bool, optional
        If True, switches on auto print mode for the Timer. In auto print mode,
        the value of the Timer is printed out on each :meth:`read` and, when
        using a context manager, on exiting it.
        This is very convenient to quickly do timing of some code block.
        See the examples above.
        If False, the user is responsible for printing out the Timer.
    reg: :class:`Timers`, optional
        If a :class:`Timers` instance is provided, the new :class:`Timer`
        is added to that collection and its value can be printed out together
        with that of the others in the collection.
    """

    def __init__(self, tag='Timer', *, timefunc=time.perf_counter, dec=6,
                 acc=0., auto=False, reg=None):
        """Create and reset the timer."""
        self._tag = str(tag)
        self.dec = int(dec)
        self.auto = bool(auto)
        self._acc = acc if acc is None else float(acc)
        self._mem = 0.
        if isinstance(timefunc(), float):
            self._func = timefunc
        else:
            raise ValueError("timefunc should return a float")
        self.start()
        if isinstance(reg, Timers):
            reg.append(self)

    @property
    def value(self):
        """The current value of the Timer.

        Peeking at the Timer's value does not :meth:`read` the Timer.
        """
        return self._func() - self._started

    @property
    def mem(self):
        """The last read value rounded to the timer's precision.

        Note
        ----
        Use :attr:`_mem` to get the full precision.
        """
        return round(self._mem, self.dec)

    @property
    def acc(self):
        """The accumulator value rounded to the timer's precision.

        Note
        ----
        Use :attr:`_acc` to get the full precision.
        """
        return round(self._acc, self.dec)

    @property
    def tag(self):
        """The timer's tag string"""
        return self._tag

    def newtag(self, newtag):
        """Change the tag string of the Timer.

        Returns
        -------
        self
            The Timer itself, thus this method can be used as a context manager.
        """
        self._tag = str(newtag)
        return self

    def start(self):
        """Start the timer.

        This marks the start for the next :meth:`read` operation.
        """
        self._started = self._func()

    def read(self):
        """Read the timer.

        Read the time since the last :meth:`read` or :meth:`start`, or since the
        creation of the Timer. Store the time in self.mem, and accumulate
        it in self.acc (if not None). Print the Timer if auto mode is on.

        Returns
        -------
        float
            The time in seconds since the last :meth:`read` or :meth:`start`,
            or since the creation of the Timer.
        """
        now = self._func()
        self._mem = now - self._started
        if self._acc is not None:
            self._acc += self._mem
        self._started = now
        if self.auto:
            print(self)
        return self._mem

    def __enter__(self):
        """Enter the context manager"""
        self.start()
        return self

    def __exit__(self, *exc):
        """Exit the context manager"""
        self.read()

    def format(self):
        """Return a string representation of the Timer.

        Returns
        -------
        string
            A string with the Timer's tag, the last read value, and
            the accumulated value if the Timer is an accumulating one.
            This is also the string that will be shown when printing
            a Timer.
        """
        s = f"{self._tag}: {self._mem:.{self.dec}f} sec."
        if self._acc is not None:
            s += f" Acc: {self._acc:.{self.dec}f} sec."
        return s

    __str__ = format


class Timers(list):
    """A collection of timers

    Timers is a :class:`list` of :class:`Timer` instances. All normal
    list methods are available. Thould take care though to add nothing but
    :class:`Timer` instances to the list.

    The benefits over using a plain :class:`list` is that printing a Timers
    will give a nicely formatted output of the timers and
    that the Timers can be used as a content manager to activate
    all its Timer instances at once. The latter is e.g. convenient to measure
    the same code block with different time functions.

    Parameters
    ----------
    *timers: optional
        A sequence of :class:`Timer` instances.

    """
    def __init__(self, *timers):
        for t in timers:
            if not isinstance(t, Timer):
                raise ValueError("Arguments should be Timer instances")
        super().__init__(timers)

    def get(self, tag):
        """Return the (first) timer in the list with the specified tag

        Parameters
        ----------
        tag: str
            The tag string of a Timer to be found in the Timers list.

        Returns
        -------
        :class:`Timer` | None
            If the tag was found in the list, returns the first matching Timer.
            Else, returns None.
        """
        for t in self:
            if t._tag == tag:
                return t

    def report(self, *tags):
        """Return a full report of all existing or requested Timers.

        Parameters
        ----------
        *tags: sequence, optional
            A sequence of tag strings of the timers that should be included
            in the report. In none provided, all timers are included.

        Returns
        -------
        string
            A string containing the formatted Timer instances. This is also
            the string that will be shown by the print function.
        """
        if tags:
            timers = (t:=self.get(tag) for tag in tags if t is not None)
        else:
            timers = self
        return '\n  '.join(['Timer report'] + [str(t) for t in timers])

    def __str__(self):
        return self.report()

    def __enter__(self):
        """Enter the context manager"""
        for timer in self:
            timer.__enter__()
        return self

    def __exit__(self, *exc):
        """Exit the context manager"""
        for timer in reversed(self):  # TODO: Should we use reversed or not?
            timer.__exit__()


if __name__ == "__main__":

    print(f"Running doctests on {__file__}")
    import doctest
    doctest.testmod(
        optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)


# End
