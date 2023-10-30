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
"""Local http server and html file viewer

This module provides functionality to view a local html file in the
browser using the 'http:' transport mechanism instead of 'file:'.
It was created to allow viewing WebGL models from a local directory.
"""
import os

import pyformex as pf
from pyformex import utils
from pyformex.path import Path


class HttpServer:
    """A specialized http server to serve local files.

    This server is intended to serve local files to a browser.
    It is meant as a replacement for the 'file:' transport mechanism.
    For security reasons modern browsers often do not allow to include
    files (especially script types) from another origin. With the file:
    protocol any other file, even in the same directory, may be considered
    as a foreign origin. A CORS error is raised in such cases.

    The solution is to use a local http server and access the files over
    'http:' protocol. The HttpServer is very lightweight class which can
    serve a directory and all its files and subdirectories to the local
    machine. It is not intended to be exposed directly to the network.
    It uses the :class:`http.server` from the Python standard library.

    Parameters
    ----------
    path: :term:`path_like`
        The path of the local directory to be served. The user should have
        read access to this directory.
    port: int | None
        The TCP port on which the server will be listening. This should be
        an unused port number in the high rang (>= 1024). If not provided,
        a random free port number will be used.


    Every successfully created HttpServer is registered by adding it to the
    list HttpServer._servers. When pyFormex exits, all these servers will be
    topped. The user can stop a server at any time though. If you want a
    server to continue after pyFormex exits, remove it from the list. The
    following attributes of the HttpServer provide useful information:

    path: :class:`Path`
        The path of the directory with accessible files.
    port: int:
        The port number on which the server is listening.
        In your browser, use ``http://localhost:PORT/SOMEFILE`` to
        view the contents of SOMEFILE.
    P: :class:`subprocess.Popen`
        The Popen instance of the running server.
        Its attribute P.pid gives the process id of the server.

    """
    _servers = []  # registers the instances

    def __init__(self, path, port=None):
        """Initialize the HttpServer"""
        path = Path(path)
        if not path.is_dir():
            raise ValueError("path should be a directory")
        os.chdir(path)
        if port is None:
            port = get_free_socket()
        P = utils.system(f'python3 -m http.server {port}', wait=False)
        if P.poll() is None:
            # The server is running
            print(f"Created new HttpServer serving {path}")
            print(f"  running as pid {P.pid} on port {port}")
            HttpServer._servers.append(self)
        else:
            print(f"Failed creating HttpServer for {os.getcwd()}")
        self.path = path
        self.port = port
        self.P = P


    def stop(self):
        """Stop a HttpServer"""
        print(f"Stopping HttpServer pid {self.P.pid} on port {self.port}")
        P = self.P
        print(P, P.pid)
        P.terminate()
        try:
            print("waiting")
            P.wait(timeout=5)
        except TimeoutExpired:
            P.kill()
            try:
                P.wait(timeout=5)
            except TimeoutExpired:
                pass
        HttpServer._servers.remove(self)
        return P


    @classmethod
    def stop_all(cls):
        """Stop all running servers"""
        while len(cls._servers) > 0:
            cls._servers[0].stop()


    def connect(self, url='', browser=None):
        """Show an url in the browser.

        Parameters
        ----------
        url: :term:`path_like`
            The path of the file to be shown in the browser. The path
            is relative to the served directory path.
            An empty string or a single '/' will serve the directory
            itself, showing the contents of the directory.
        browser: str
            The name of the browser command. If not provided, the value
            from the settings is used. It can be configured in the
            Settings menu.
        """
        if self.P.poll() is None:
            utils.system(f"{pf.cfg['browser']} localhost:{self.port}/{url}",
                         wait=False)
            print(f"HttpServer on port {self.port} showing url {url}")
        else:
            utils.warn("The HttpServer has stopped")


def get_free_socket():
    """Find and return a random free port number.

    A random free port number in the upper range 1024-65535 is found.
    The port is immediately bound with the reuse option set.
    This avoids a race condition (where another process could bind to
    the port before we had the change to do so) while still keeping
    the port bindable for our purpose.
    """
    import socket
    sock = socket.socket()
    sock.bind(('', 0))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return sock.getsockname()[1]


def showHtml(path):
    """Show a local .html file in the browser.

    Creates a local web server (:class:`HttpServer`) to serve an html file
    over the http: protocol to a browser on the local machine.
    The browser command is configurable in the settings.

    This is a convenient wrapper function if you have a single file to
    show. If you need to show multiple files from the same directory, you
    may want to create a single :class:`HttpServer` for the directory and\           use multiple calls to its :meth:`~HttpServer.connect` method.

    Parameters
    ----------
    path: :term:`path_like`
        The path of the file to be displayed. This should normally be a
        file with suffix ``.html``.
    """
    path = Path(path)
    if path.is_dir():
        name = ''
    else:
        name = path.name
        path = path.parent
    HttpServer(path).connect(name)


if not pf.sphinx:
    # Make sure we stop all servers on exit
    pf.onExit(HttpServer.stop_all)


# End
