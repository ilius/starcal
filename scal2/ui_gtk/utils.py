from scal2.utils import myRaise
from subprocess import Popen
from time import time
import gtk


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
        try:
            import webbrowser
            webbrowser.open(url)
        except:
            try:
                import gnomevfs
                gnomevfs.url_show(url)
            except:
                for path in ('/usr/bin/gnome-www-browser', '/usr/bin/firefox', '/usr/bin/iceweasel', '/usr/bin/konqueror'):
                    if isfile(path):
                        Popen([path, link])
                        return

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
def imageFromFile(path):
    im = gtk.Image()
    im.set_from_file(path)
    return im


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

