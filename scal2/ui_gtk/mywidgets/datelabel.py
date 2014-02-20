from scal2 import core
from scal2.locale_man import tr as _

from scal2.ui_gtk import *

class DateLabel(gtk.Label):
    def __init__(self, text=None):
        gtk.Label.__init__(self, text)
        self.set_selectable(True)
        #self.set_cursor_visible(False)## FIXME
        self.set_can_focus(False)
        self.set_use_markup(True)
        self.connect('populate-popup', self.popupPopulate)
        ####
        self.menu = gtk.Menu()
        ##
        itemCopyAll = gtk.ImageMenuItem(_('Copy _All'))
        itemCopyAll.set_image(gtk.image_new_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU))
        itemCopyAll.connect('activate', self.copyAll)
        self.menu.add(itemCopyAll)
        ##
        itemCopy = gtk.ImageMenuItem(_('_Copy'))
        itemCopy.set_image(gtk.image_new_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU))
        itemCopy.connect('activate', self.copy)
        self.itemCopy = itemCopy
        self.menu.add(itemCopy)
        ##
        self.menu.show_all()
    def popupPopulate(self, label, menu):
        self.itemCopy.set_sensitive(self.get_property('cursor-position') > self.get_property('selection-bound'))## FIXME
        self.menu.popup(None, None, None, 3, 0)
        ui.updateFocusTime()
    def copy(self, item):
        start = self.get_property('selection-bound')
        end = self.get_property('cursor-position')
        setClipboard(toUnicode(self.get_text())[start:end])
    copyAll = lambda self, label: setClipboard(self.get_text())

