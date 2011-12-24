# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

import os

def makeDir(direc):
    if not isdir(direc):
        os.makedirs(direc)

def getUsersData():
    data = []
    for line in open('/etc/passwd').readlines():
        parts = line.strip().split(':')
        data.append({
            'login': parts[0],
            'uid': parts[2],
            'gid': parts[3],
            'read_name': parts[4],
            'home_dir': parts[5],
            'shell': parts[6],
        })
    return data


def kill(pid, signal=0):
    '''
        sends a signal to a process
        returns True if the pid is dead
        with no signal argument, sends no signal
    '''
    #if 'ps --no-headers' returns no lines, the pid is dead
    from os import kill
    try:
        return kill(pid, signal)
    except OSError, e:
        #process is dead
        if e.errno == 3:
            return True
        #no permissions
        elif e.errno == 1:
            return False
        else:
            raise e

def dead(pid):
    if kill(pid):
        return True

    #maybe the pid is a zombie that needs us to wait for it
    from os import waitpid, WNOHANG
    try:
        dead = waitpid(pid, WNOHANG)[0]
    except OSError, e:
        #pid is not a child
        if e.errno == 10:
            return False
        else:
            raise e
    return dead

#def kill(pid, sig=0): pass #DEBUG: test hang condition


def goodkill(pid, interval=1, hung=20):
    'let process die gracefully, gradually send harsher signals if necessary'
    from signal import SIGTERM, SIGINT, SIGHUP, SIGKILL
    from time import sleep

    for signal in (SIGTERM, SIGINT, SIGHUP):
        if kill(pid, signal):
            return
        if dead(pid):
            return
        sleep(interval)

    i = 0
    while True:
        #infinite-loop protection
        if i < hung:
            i += 1
        else:
            raise OSError('Process %s is hung. Giving up kill.'%pid)
        if kill(pid, SIGKILL):
            return
        if dead(pid):
            return
        sleep(interval) 


