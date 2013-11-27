from os.path import isfile, isdir

from scal2.path import *
from scal2.os_utils import makeDir

from scal2 import core
from scal2.core import osName

comDeskDir = '%s/.config/autostart'%homeDir
comDesk = '%s/%s.desktop'%(comDeskDir, APP_NAME)
#kdeDesk='%s/.kde/Autostart/%s.desktop'%(homeDir, APP_NAME)


def addStartup():
    if osName=='win':
        from scal2.windows import winMakeShortcut
        makeDir(winStartupDir)
        #fname = APP_NAME + ('-qt' if uiName=='qt' else '') + '.pyw'
        fname = core.COMMAND + '.pyw'
        fpath = join(rootDir, fname)
        #open(winStartupFile, 'w').write('execfile(%r, {"__file__":%r})'%(fpath, fpath))
        try:
            winMakeShortcut(fpath, winStartupFile)
        except:
            return False
        else:
            return True
    elif isdir('%s/.config'%homeDir):## osName in ('linux', 'mac') ## maybe Gnome/KDE on Solaris, *BSD, ...
        text = '''[Desktop Entry]
Type=Application
Name=%s %s
Icon=%s
Exec=%s'''%(core.APP_DESC, core.VERSION, APP_NAME, core.COMMAND)## double quotes needed when the exec path has space
        makeDir(comDeskDir)
        try:
            fp = open(comDesk, 'w')
        except:
            core.myRaise(__file__)
            return False
        else:
            fp.write(text)
            return True
    elif osName=='mac':## FIXME
        pass
    return False


def removeStartup():
    if osName=='win':## FIXME
        if isfile(winStartupFile):
            os.remove(winStartupFile)
    elif isfile(comDesk):
        os.remove(comDesk)

def checkStartup():
    if osName=='win':
        return isfile(winStartupFile)
    elif isfile(comDesk):
        return True
    return False



