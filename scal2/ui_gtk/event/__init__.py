__all__ = [
    'rules',
    'notifiers',
    'occurrenceViews',
]

############################################

from scal2.utils import myRaise
from scal2 import event_lib


modPrefix = 'scal2.ui_gtk.event'


def makeWidget(obj):## obj is an instance of Event, EventRule, EventNotifier or EventGroup
    cls = obj.__class__
    try:
        WidgetClass = cls.WidgetClass
    except AttributeError:
        try:
            module = __import__(
                '.'.join([
                    modPrefix,
                    cls.tname,
                    cls.name,
                ]),
                fromlist=['WidgetClass'],
            )
            WidgetClass = cls.WidgetClass = module.WidgetClass
        except:
            myRaise()
            return
    widget = WidgetClass(obj)
    try:
        widget.show_all()
    except AttributeError:
        widget.show()
    widget.updateWidget()## FIXME
    return widget 


### Load accounts, groups and trash? FIXME


import scal2.ui_gtk.event.import_customday ## opens a dialog if neccessery


