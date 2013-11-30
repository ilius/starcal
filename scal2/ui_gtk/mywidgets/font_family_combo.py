from scal2.locale_man import tr as _
from scal2 import ui

import gtk

from scal2.ui_gtk.font_utils import getFontFamilyList


class FontFamilyCombo(gtk.ComboBox):
    def __init__(self, hasAuto=False):
        ls = gtk.ListStore(str, str)
        gtk.ComboBox.__init__(self, ls)
        ###
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 1)
        ###
        if hasAuto:
            ls.append((None, _('Auto')))
        for fontName in getFontFamilyList(self):
            ls.append((fontName, _(fontName)))## translate font name in GUI? FIXME
        ###
        self.set_active(0)
        if not hasAuto:
            self.set_value(ui.fontDefault[0])
        ###
        #self.set_property('has-entry', 1)
        #self.set_property('entry-text-column', 0)
    def get_value(self):
        i = self.get_active()
        if i is None:
            return None
        return self.get_model()[i][0]
    def set_value(self, fontName):
        ls = self.get_model()
        for i in range(len(ls)):
            if ls[i][0]==fontName:
                self.set_active(i)
                break

if __name__=='__main__':
    d = gtk.Dialog()
    combo = FontFamilyCombo(1)
    d.vbox.pack_start(combo, 1, 1)
    d.vbox.show_all()
    d.run()
    print(combo.get_value())




