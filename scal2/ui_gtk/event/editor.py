from scal2 import core
from scal2.locale_man import tr as _
from scal2 import event_lib

from scal2 import ui

from scal2.ui_gtk import *
from scal2.ui_gtk.utils import dialog_add_button
from scal2.ui_gtk.event import makeWidget

class EventEditorDialog(gtk.Dialog):
    def __init__(self, event, typeChangable=True, title=None, isNew=False, parent=None, useSelectedDate=False):
        gtk.Dialog.__init__(self)
        if parent:
            self.set_parent(parent)
        #self.set_transient_for(None)
        #self.set_type_hint(gdk.WindowTypeHint.NORMAL)
        if title:
            self.set_title(title)
        self.isNew = isNew
        #self.connect('delete-event', lambda obj, e: self.destroy())
        #self.resize(800, 600)
        ###
        dialog_add_button(self, gtk.STOCK_CANCEL, _('_Cancel'), gtk.ResponseType.CANCEL)
        dialog_add_button(self, gtk.STOCK_OK, _('_OK'), gtk.ResponseType.OK)
        ###
        self.connect('response', lambda w, e: self.hide())
        ###
        self.activeWidget = None
        self._group = event.parent
        self.eventTypeOptions = list(self._group.acceptsEventTypes)
        ####
        if not event.name in self.eventTypeOptions:
            self.eventTypeOptions.append(event.name)
        eventTypeIndex = self.eventTypeOptions.index(event.name)
        ####
        self.event = event
        #######
        if isNew:
            event.timeZone = str(core.localTz)
        #######
        hbox = gtk.HBox()
        pack(hbox, gtk.Label(
            _('Group') + ': ' + self._group.title
        ))
        hbox.show_all()
        pack(self.vbox, hbox)
        #######
        hbox = gtk.HBox()
        pack(hbox, gtk.Label(_('Event Type')))
        if typeChangable:
            combo = gtk.ComboBoxText()
            for tmpEventType in self.eventTypeOptions:
                combo.append_text(event_lib.classes.event.byName[tmpEventType].desc)
            pack(hbox, combo)
            ####
            combo.set_active(eventTypeIndex)
            ####
            #self.activeWidget = makeWidget(event)
            combo.connect('changed', self.typeChanged)
            self.comboEventType = combo
        else:
            pack(hbox, gtk.Label(':  '+event.desc))
        pack(hbox, gtk.Label(''), 1, 1)
        hbox.show_all()
        pack(self.vbox, hbox)
        #####
        if useSelectedDate:
            self.event.setJd(ui.cell.jd)
        self.activeWidget = makeWidget(event)
        if self.isNew:
            self.activeWidget.focusSummary()
        pack(self.vbox, self.activeWidget, 1, 1)
        self.vbox.show()
    def typeChanged(self, combo):
        if self.activeWidget:
            self.activeWidget.updateVars()
            self.activeWidget.destroy()
        eventType = self.eventTypeOptions[combo.get_active()]
        if self.isNew:
            self.event = self._group.createEvent(eventType)
        else:
            self.event = self._group.copyEventWithType(self.event, eventType)
        self._group.updateCache(self.event)## needed? FIXME
        self.activeWidget = makeWidget(self.event)
        if self.isNew:
            self.activeWidget.focusSummary()
        pack(self.vbox, self.activeWidget)
        #self.activeWidget.modeComboChanged()## apearantly not needed
    def run(self):
        #if not self.activeWidget:
        #    return None
        if gtk.Dialog.run(self) != gtk.ResponseType.OK:
            try:
                filesBox = self.activeWidget.filesBox
            except AttributeError:
                pass
            else:
                filesBox.removeNewFiles()
            return None
        self.activeWidget.updateVars()
        self.event.afterModify()
        self.event.save()
        event_lib.lastIds.save()
        self.destroy()
        return self.event

def addNewEvent(group, eventType, title, typeChangable=False, **kw):
    event = group.createEvent(eventType)
    if eventType=='custom':## FIXME
        typeChangable = True
    event = EventEditorDialog(
        event,
        typeChangable=typeChangable,
        title=title,
        isNew=True,
        **kw
    ).run()
    if event is None:
        return
    group.append(event)
    group.save()
    return event



