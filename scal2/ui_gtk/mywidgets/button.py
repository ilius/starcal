from time import time
import sys

import gobject
from gobject import timeout_add

import gtk
from gtk import gdk

from scal2.ui_gtk import gtk_ud as ud


class ConButtonBase:
    def __init__(self):
        self.pressTm = 0
        self.remain = False
        ###
        self.connect('pressed', self.onPress)
        self.connect('released', self.onRelease)
    doTrigger = lambda self: self.emit('con-clicked')
    def onPress(self, widget, event=None):
        self.pressTm = time()
        self.remain = True
        self.doTrigger()
        timeout_add(ui.timeout_initial, self.onPressRemain, self.doTrigger)
    def onPressRemain(self, func):
        if self.remain and time()-self.pressTm>=ui.timeout_repeat/1000.0:
            func()
            timeout_add(ui.timeout_repeat, self.onPressRemain, self.doTrigger)
    def onRelease(self, widget, event=None):
        self.remain = False


class ConButton(gtk.Button, ConButtonBase):
    def __init__(self, *args, **kwargs):
        gtk.Button.__init__(self, *args, **kwargs)
        ConButtonBase.__init__(self)



gobject.type_register(ConButton)
gobject.signal_new('con-clicked', ConButton, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])


if __name__=='__main__':
    win = gtk.Dialog()
    button = ConButton('Press')
    button.connect('con-clicked', lambda obj: sys.stdout.write('%.4f\n'%time()))
    win.vbox.pack_start(button, 1, 1)
    win.vbox.show_all()
    win.resize(100, 100)
    win.run()



