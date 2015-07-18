from scal3.locale_man import tr as _

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import confirm
from scal3.ui_gtk.drawing import newColorCheckPixbuf


confirmEventTrash = lambda event, parent=None: confirm(
    _('Press OK if you want to move event "%s" to trash')%event.summary,
    parent=parent,
)


def menuItemFromEventGroup(group):
    item = ImageMenuItem()
    item.set_label(group.title)
    ##
    image = gtk.Image()
    image.set_from_pixbuf(newColorCheckPixbuf(group.color, 20, True))
    item.set_image(image)
    return item


