from scal2.locale_man import tr as _
from scal2.utils import myRaise
from scal2.paths import pixDir

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

def myUrlShow(link):
    try:
        Popen(['xdg-open', link])
    except:
        myRaise()
        if not link.startswith('http'):
            return
        try:
            import webbrowser
        except ImportError:
            try:
                import gnomevfs
            except ImportError:
                for path in ('/usr/bin/gnome-www-browser', '/usr/bin/firefox', '/usr/bin/iceweasel', '/usr/bin/konqueror'):
                    if isfile(path):
                        Popen([path, link])
                        return
            else:
                gnomevfs.url_show(url)
        else:
            webbrowser.open(url)

def set_tooltip(widget, text):
    try:
        widget.set_tooltip_text(text)## PyGTK 2.12 or above
    except AttributeError:
        try:
            widget.set_tooltip(gtk.Tooltips(), text)
        except:
            myRaise(__file__)


#if hasattr(gtk, 'image_new_from_file'):
#    imageFromFile = gtk.image_new_from_file
def imageFromFile(path):## the file must exist
    if os.sep=='/' and not path.startswith('/'):
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
    item.set_image(imageFromFile('%s%s%s'%(pixDir, os.sep, image)))
    if func:
        item.connect('activate', func, *args)
    return item

