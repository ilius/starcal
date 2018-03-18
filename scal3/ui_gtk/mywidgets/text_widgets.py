from scal3.utils import toStr
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import labelStockMenuItem, setClipboard, buffer_get_text

class ReadOnlyTextWidget:
    copyAll = lambda self, item: setClipboard(toStr(self.get_text()))
    def has_selection():
        raise NotImplementedError
    def onPopup(self, widget, menu):
        # instead of creating a new menu, we should remove all the current items from current menu
        for item in menu.get_children():
            menu.remove(item)
        ####
        menu.add(labelStockMenuItem(
            'Copy _All',
            gtk.STOCK_COPY,
            self.copyAll,
        ))
        ####
        itemCopy = labelStockMenuItem(
            '_Copy',
            gtk.STOCK_COPY,
            self.copy,
        )
        if not self.has_selection():
            itemCopy.set_sensitive(False)
        menu.add(itemCopy)
        ####
        menu.show_all()
        self.tmpMenu = menu
        ui.updateFocusTime()


class ReadOnlyLabel(gtk.Label, ReadOnlyTextWidget):
    get_cursor_position = lambda self: self.get_property('cursor-position')
    get_selection_bound = lambda self: self.get_property('selection-bound')
    def has_selection(self):
        return self.get_cursor_position() != self.get_selection_bound()
    def copy(self, item):
        bound = self.get_selection_bound()
        cursor = self.get_cursor_position()
        start = min(bound, cursor)
        end = max(bound, cursor)
        setClipboard(toStr(self.get_text())[start:end])
    def __init__(self, *args, **kwargs):
        gtk.Label.__init__(self, *args, **kwargs)
        self.set_selectable(True)## to be selectable, with visible cursor
        self.connect('populate-popup', self.onPopup)



class ReadOnlyTextView(gtk.TextView, ReadOnlyTextWidget):
    get_text = lambda self: buffer_get_text(self.get_buffer())
    get_cursor_position = lambda self: self.get_buffer().get_property('cursor-position')
    def has_selection(self):
        buf = self.get_buffer()
        try:
            start_iter, end_iter = buf.get_selection_bounds()
        except ValueError:
            return False
        else:
            return True
    def copy(self, item):
        buf = self.get_buffer()
        start_iter, end_iter = buf.get_selection_bounds()
        setClipboard(toStr(buf.get_text(start_iter, end_iter, True)))
    def __init__(self, *args, **kwargs):
        gtk.TextView.__init__(self, *args, **kwargs)
        self.set_editable(False)
        self.set_cursor_visible(False)
        self.connect('populate-popup', self.onPopup)



