#!/usr/bin/env python3
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
#
##
##  This file is part of pyFormex 1.0.7  (Mon Jun 17 12:20:39 CEST 2019)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2019 (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
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

"""sendmail.py: a simple program to send an email message

(C) 2008 Benedict Verhegghe (benedict.verhegghe@ugent.be)
I wrote this software in my free time, for my joy, not as a commissioned task.
Any copyright claims made by my employer should therefore be considered void.

Distributed under the GNU General Public License, version 3 or later
"""

import os
import smtplib
import socket
import getpass
from email.message import EmailMessage

################### global data ##################################

host = socket.gethostname()
user = getpass.getuser()
mail = os.environ.get('MAIL', "%s@%s" % (user, host))

################### mail access ##################################

def message(sender='', to='', cc='', subject='', text=''):
    """Create an email message

    'to' and 'cc' can be lists of email addresses.
    """
    if isinstance(to, list):
        to = ', '.join(to)
    if isinstance(cc, list):
        cc = ', '.join(cc)
    message = EmailMessage()
    message["From"] = sender
    message["To"] = to
    if cc:
        message["Cc"] = cc
    message["Subject"] = subject
    message.set_payload(text)
    return message


def sendmail(message, sender, to, serverURL='localhost'):
    """Send an email message

    'message' is an email message (e.g. returned by message())
    'sender' is a single mail address
    'to' can be a list of addresses
    """
    mailServer = smtplib.SMTP(serverURL)
    mailServer.sendmail(sender, to, message.as_string())
    mailServer.quit()


##################################################################


def input_message(prompt=True):
    print(
        """
    This is Bene's simple mail program, version 0.00001.
    Enter lines of text, end with CTRL-D (on a blank line).
    Include at least one line starting with 'To:'
    Include exactly one line starting with 'Subj:'
    Optionally include a line starting with 'From:'
    Optionally include one or more lines starting with 'CC:'
    All other lines will be the text of your message.
    """
    )
    to = []
    cc = []
    subj = ''
    msg = ''
    sender = ''
    while True:
        try:
            s = input()
            slower = s[:5].lower()
            if slower.startswith('to:'):
                to.append(s[3:])
            elif slower.startswith('cc:'):
                cc.append(s[3:])
            elif slower.startswith('subj:'):
                subj = s[5:]
            elif slower.startswith('from:'):
                sender = s[5:]
            else:
                msg += s + '\n'

        except EOFError:
            break
    return to, cc, subj, msg, sender


if __name__ == '__main__':

    to, cc, subj, msg, sender = input_message()
    if not sender:
        sender = mail

    if to and subj and msg and sender:
        msg = message(sender, to, cc, subj, msg)
        print("\n\n    Email message:")
        print(msg)
        if input('\n    Shall I send the email now? (y/n)') == 'y':
            sendmail(msg, sender, to)
            print("Mail has been sent!")
        else:
            print("Mail not sent!")
    else:
        print("Message can not be sent because of missing fields!")

# End
