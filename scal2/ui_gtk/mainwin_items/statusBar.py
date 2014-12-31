from scal2.cal_types import calTypes
from scal2 import core
from scal2.locale_man import tr as _
from scal2.locale_man import rtl
from scal2 import ui

from scal2.ui_gtk import *
from scal2.ui_gtk.mywidgets.datelabel import DateLabel
from scal2.ui_gtk.decorators import *
from scal2.ui_gtk import gtk_ud as ud
from scal2.ui_gtk.customize import CustomizableCalObj

@registerSignals
class CalObj(gtk.HBox, CustomizableCalObj):
    _name = 'statusBar'
    desc = _('Status Bar')
    def __init__(self):
        gtk.HBox.__init__(self)
        self.initVars()
        self.labelBox = gtk.HBox()
        pack(self, self.labelBox, 1, 1)
        sbar = gtk.Statusbar()
        if rtl:
            self.set_direction(gtk.TEXT_DIR_LTR)
            sbar.set_direction(gtk.TEXT_DIR_LTR)
            self.labelBox.set_direction(gtk.TEXT_DIR_LTR)
        sbar.set_property('width-request', 18)
        sbar.connect('button-press-event', self.sbarButtonPress)
        sbar.show()
        pack(self, sbar)
    sbarButtonPress = lambda self, widget, gevent: ui.mainWin.startResize(widget, gevent)
    def onConfigChange(self, *a, **kw):
        CustomizableCalObj.onConfigChange(self, *a, **kw)
        ###
        for label in self.labelBox.get_children():
            label.destroy()
        ###
        for mode in calTypes.active:
            label = DateLabel(None)
            label.mode = mode
            pack(self.labelBox, label, 1)
        self.show_all()
        ###
        self.onDateChange()
    def onDateChange(self, *a, **kw):
        CustomizableCalObj.onDateChange(self, *a, **kw)
        for i, label in enumerate(self.labelBox.get_children()):
            text = ui.cell.format(ud.dateFormatBin, label.mode)
            if i==0:
                text = '<b>%s</b>'%text
            label.set_label(text)

