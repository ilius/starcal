import gobject

import gtk
from gtk import gdk

class IntegratedCalWidget(gtk.Object):
    name = ''
    desc = ''
    items = [] ## FIXME
    def initVars(self, name, desc):
        self._name = name
        self.desc = desc
        self.items = []
        self.enable = True
    def onConfigChange(self, sender=None, emit=True):
        if emit:
            self.emit('config-change')
        for item in self.items:
            if item.enable and item is not sender:
                item.onConfigChange(emit=False)
    def onDateChange(self, sender=None, emit=True):
        if emit:
            self.emit('date-change')
        for item in self.items:
            if item.enable and item is not sender:
                item.onDateChange(emit=False)
    def __getitem__(self, key):
        for item in self.items:
            if item.name == key:
                return item
    def connectItem(self, item):
        item.connect('config-change', self.onConfigChange)
        item.connect('date-change', self.onDateChange)
    def insertItem(self, index, item):
        self.items.insert(index, item)
        self.connectItem(item)
    def appendItem(self, item):
        self.items.append(item)
        self.connectItem(item)
    @classmethod
    def registerSignals(cls):
        gobject.type_register(cls)
        gobject.signal_new('config-change', cls, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
        gobject.signal_new('date-change', cls, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])


class IntegatedWindowList(IntegratedCalWidget):
    def __init__(self):
        gtk.Object.__init__(self)
        self.initVars('windowList', 'Window List')
    def onConfigChange(self, *a, **ka):
        IntegratedCalWidget.onConfigChange(self, *a, **ka)
        self.onDateChange()

#IntegratedCalWidget.registerSignals()
IntegatedWindowList.registerSignals()

windowList = IntegatedWindowList()

