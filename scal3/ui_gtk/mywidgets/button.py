from time import time as now
import sys

from scal3 import ui

from gi.repository import GObject
from gi.repository.GObject import timeout_add

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk import gtk_ud as ud


class ConButtonBase:
    def __init__(self):
        self.pressTm = 0
        self.remain = False
        ###
        self.connect('pressed', self.onPress)
        self.connect('released', self.onRelease)
    doTrigger = lambda self: self.emit('con-clicked')
    def onPress(self, widget, event=None):
        self.pressTm = now()
        self.remain = True
        self.doTrigger()
        timeout_add(ui.timeout_initial, self.onPressRemain, self.doTrigger)
    def onPressRemain(self, func):
        if self.remain and now()-self.pressTm>=ui.timeout_repeat/1000.0:
            func()
            timeout_add(ui.timeout_repeat, self.onPressRemain, self.doTrigger)
    def onRelease(self, widget, event=None):
        self.remain = False


@registerSignals
class ConButton(gtk.Button, ConButtonBase):
    signals =[
        ('con-clicked', []),
    ]
    def __init__(self, *args, **kwargs):
        gtk.Button.__init__(self, *args, **kwargs)
        ConButtonBase.__init__(self)




if __name__=='__main__':
    win = gtk.Dialog(parent=None)
    button = ConButton('Press')
    button.connect('con-clicked', lambda obj: sys.stdout.write('%.4f\n'%now()))
    pack(win.vbox, button, 1, 1)
    win.vbox.show_all()
    win.resize(100, 100)
    win.run()



