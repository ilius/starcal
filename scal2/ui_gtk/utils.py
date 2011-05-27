import gtk

def set_tooltip(widget, text):
    try:
        widget.set_tooltip_text(text)## PyGTK 2.12 or above
    except AttributeError:
        try:
            widget.set_tooltip(gtk.Tooltips(), text)
        except:
            myRaise(__file__)


def image_from_file(path):
    im = gtk.Image()
    im.set_from_file(path)
    return im

def stock_arrow_repr(item):
    if isinstance(item, gtk._gtk.ArrowType):
        return 'gtk.%s\n'%item.value_name[4:]
    else:
        return repr(item)

