__all__ = [
    'gtk',
    'gdk',
    'pack',
    'TWO_BUTTON_PRESS',
]

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk

def pack(box, child, expand=False, fill=False, padding=0):
    if isinstance(box, gtk.Box):
        box.pack_start(child, expand, fill, padding)
    elif isinstance(box, gtk.CellLayout):
        box.pack_start(child, expand)
    else:
        raise TypeError('pack: unkown type %s'%type(box))

TWO_BUTTON_PRESS = getattr(gdk.EventType, '2BUTTON_PRESS')

