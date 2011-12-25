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

def isRunning():
    (output, error) = Popen('ps aux | grep unity-panel-service | grep -v grep', stdout=PIPE, shell=True).communicate()
    output = str(output)
    #error = str(error)
    #open('/tmp/starcal2-unity-out', 'w').write(output)
    #open('/tmp/starcal2-unity-error', 'w').write(error)
    #print 'Unity is Running:', bool(output)
    return bool(output)

def needToAdd():
    if isRunning():
        wlist = getWhileList()
        if not (APP_NAME in wlist or 'all' in wlist):
            return True
    return False

def addAndRestart():
    addToWhileList()
    Popen('LANG=en_US.UTF-8 unity', shell=True)

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


