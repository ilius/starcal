from scal2.locale_man import tr as _
from scal2.utils import myRaise
from scal2.paths import pixDir

from scal2 import core
from scal2 import ui

import os
from os.path import join
from subprocess import Popen
from time import time
import gtk
from gtk import gdk


def hideList(widgets):
    for w in widgets:
        w.hide()

def showList(widgets):
    for w in widgets:
        w.show()


def set_tooltip(widget, text):
    try:
        widget.set_tooltip_text(text)## PyGTK 2.12 or above
    except AttributeError:
        try:
            widget.set_tooltip(gtk.Tooltips(), text)
        except:
            myRaise(__file__)

buffer_get_text = lambda b: b.get_text(b.get_start_iter(), b.get_end_iter())

def imageFromFile(path):## the file must exist
    if not os.sep in path:
        path = join(pixDir, path)
    im = gtk.Image()
    try:
        im.set_from_file(path)
    except:
        myRaise()
    return im

def pixbufFromFile(path):## the file may not exist
    if not path:
        return None
    if os.sep=='/' and not path.startswith('/'):
        path = join(pixDir, path)
    try:
        return gdk.pixbuf_new_from_file(path)
    except:
        myRaise()
        return None
toolButtonFromStock = lambda stock, size: gtk.ToolButton(gtk.image_new_from_stock(stock, size))

def setupMenuHideOnLeave(menu):
    def menuLeaveNotify(m, e):
        t0 = time()
        if t0-m.lastLeaveNotify < 0.001:
            timeout_add(500, m.hide)
        m.lastLeaveNotify = t0
    menu.lastLeaveNotify = 0
    menu.connect('leave-notify-event', menuLeaveNotify)


def stock_arrow_repr(item):
    if isinstance(item, gtk._gtk.ArrowType):
        return 'gtk.%s\n'%item.value_name[4:]
    else:
        return repr(item)

def labelStockMenuItem(label, stock=None, func=None, *args):
    item = gtk.ImageMenuItem(_(label))
    if stock:
        item.set_image(gtk.image_new_from_stock(stock, gtk.ICON_SIZE_MENU))
    if func:
        item.connect('activate', func, *args)
    return item

def labelImageMenuItem(label, image, func=None, *args):
    item = gtk.ImageMenuItem(_(label))
    item.set_image(imageFromFile(image))
    if func:
        item.connect('activate', func, *args)
    return item

def modify_bg_all(widget, state, gcolor):
    print widget.__class__.__name__
    widget.modify_bg(state, gcolor)
    try:
        children = widget.get_children()
    except AttributeError:
        pass
    else:
        for child in children:
            modify_bg_all(child, state, gcolor)

def combo_model_delete_text(model, path, itr, text_to_del):
    ## Usage: combo.get_model().foreach(combo_model_delete_text, 'The Text')
    if model[path[0]][0]==text_to_del:
        del model[path[0]]
        return

def cellToggled(cell, path=None):
    print 'cellToggled', path
    cell.set_active(not cell.get_active())##????????????????????????
    return True

def comboToggleActivate(combo, *args):
    print combo.get_property('popup-shown')
    if not combo.get_property('popup-shown'):
        combo.popup()
        return True
    return False

def getTreeviewPathStr(path):
    if not path:
        return None
    return '/'.join([str(x) for x in path])

rectangleContainsPoint = lambda r, x, y: r.x <= x < r.x + r.width and r.y <= y < r.y + r.height

def confirm(msg, parent=None):
    win = gtk.MessageDialog(
        parent=parent,
        flags=0,
        type=gtk.MESSAGE_INFO,
        buttons=gtk.BUTTONS_NONE,
        message_format=msg,
    )
    cancelB = win.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
    okB = win.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
    if ui.autoLocale:
        cancelB.set_label(_('_Cancel'))
        cancelB.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL,gtk.ICON_SIZE_BUTTON))
        okB.set_label(_('_OK'))
        okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK,gtk.ICON_SIZE_BUTTON))
    ok = win.run() == gtk.RESPONSE_OK
    win.destroy()
    return ok

def showError(msg, parent=None):
    win = gtk.MessageDialog(
        parent=parent,
        flags=0,
        type=gtk.MESSAGE_ERROR,
        buttons=gtk.BUTTONS_NONE,
        message_format=msg,
    )
    closeB = win.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_OK)
    if ui.autoLocale:
        closeB.set_label(_('_Close'))
        closeB.set_image(gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_BUTTON))
    win.run()
    win.destroy()


class WeekDayComboBox(gtk.ComboBox):
    def __init__(self):
        ls = gtk.ListStore(str)
        gtk.ComboBox.__init__(self, ls)
        self.firstWeekDay = core.firstWeekDay
        ###
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 0)
        ###
        for i in range(7):
            ls.append([core.weekDayName[(i+self.firstWeekDay)%7]])
        self.set_active(0)
    def getValue(self):
        return (self.firstWeekDay + self.get_active())%7
    def setValue(self, value):
        self.set_active((value-self.firstWeekDay)%7)



## Thanks to 'Pier Carteri' <m3tr0@dei.unipd.it> for program Py_Shell.py
class GtkBufferFile:
    ## Implements a file-like object for redirect the stream to the buffer
    def __init__(self, buff, tag):
        self.buffer = buff
        self.tag = tag
    ## Write text into the buffer and apply self.tag
    def write(self, text):
        #text = text.replace('\x00', '')  
        self.buffer.insert_with_tags(self.buffer.get_end_iter(), text, self.tag)
    writelines = lambda self, l: map(self.write, l)
    flush = lambda self: None
    isatty = lambda self: False



        



