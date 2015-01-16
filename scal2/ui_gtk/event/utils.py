from scal2.locale_man import tr as _

from scal2.ui_gtk import *
from scal2.ui_gtk.utils import confirm
from scal2.ui_gtk.drawing import newColorCheckPixbuf


confirmEventTrash = lambda event:\
    confirm(_('Press OK if you want to move event "%s" to trash')%event.summary)


def menuItemFromEventGroup(group):
    item = gtk.ImageMenuItem()
    item.set_label(group.title)
    ##
    image = gtk.Image()
    image.set_from_pixbuf(newColorCheckPixbuf(group.color, 20, True))
    item.set_image(image)
    return item


