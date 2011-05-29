#!/usr/bin/python2
import sys
from subprocess import Popen, PIPE

from scal2.core import APP_NAME, getOsDesc
from scal2 import ui

getWhileList = lambda: eval(Popen(['gsettings', 'get', 'com.canonical.Unity.Panel', 'systray-whitelist'], stdout=PIPE).communicate()[0])

setWhileList = lambda ls: Popen(['gsettings', 'set', 'com.canonical.Unity.Panel', 'systray-whitelist', repr(ls)])

def addToWhileList():
    ls = getWhileList()
    if not APP_NAME in ls:
        ls.append(APP_NAME)
        setWhileList(ls)

def removeFromWhileList():
    ls = getWhileList()
    if APP_NAME in ls:
        ls.remove(APP_NAME)
        setWhileList(ls)

def needToAdd():
    if getOsDesc()=='Ubuntu 11.04':
        if APP_NAME not in getWhileList():
            return True
    return False

def addAndRestart():
    addToWhileList()
    Popen(['unity'])
    #ui.restart()

addAndRestartText = "Seems that you are using a Unity desktop and StarCalendar is not allowed to use Tray icon. Press OK to add StarCalendar to Unity's white list and then restart Unity"

if __name__=='__main__':
    if len(sys.argv)>1:
        cmd = sys.argv[1]
        if cmd=='add':
            addToWhileList()
        elif cmd=='rm':
            removeFromWhileList()
        elif cmd=='print':
            print getWhileList()


