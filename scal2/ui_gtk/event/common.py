import os, shutil
from os.path import join, split

from scal2.utils import toStr
from scal2.time_utils import durationUnitsAbs, durationUnitValues
from scal2 import core
from scal2.locale_man import tr as _
from scal2.core import pixDir, myRaise

from scal2 import event_man
from scal2 import ui

import gtk
from gtk import gdk

#print 'Testing translator', __file__, _('_About')## OK

buffer_get_text = lambda b: b.get_text(b.get_start_iter(), b.get_end_iter())

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


class IconSelectButton(gtk.Button):
    def __init__(self, filename=''):
        gtk.Button.__init__(self)
        self.image = gtk.Image()
        self.add(self.image)
        self.dialog = gtk.FileChooserDialog(
            title=_('Select Icon File'),
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
        )
        okB = self.dialog.add_button(gtk.STOCK_OK, 0)
        cancelB = self.dialog.add_button(gtk.STOCK_CANCEL, 1)
        ###
        menu = gtk.Menu()
        self.menu = menu
        for item in ui.eventTags:
            icon = item.icon
            if icon:
                menuItem = gtk.ImageMenuItem(item.desc)
                menuItem.set_image(gtk.image_new_from_file(icon))
                menuItem.connect('activate', self.menuItemActivate, icon)
                menu.add(menuItem)
        menu.show_all()
        ###
        self.dialog.connect('file-activated', self.fileActivated)
        self.dialog.connect('response', self.dialogResponse)
        #self.connect('clicked', lambda button: button.dialog.run())
        self.connect('button-press-event', self.buttonPressEvent)
        ###
        self.set_filename(filename)
    def buttonPressEvent(self, widget, event):
        b = event.button
        if b==1:
            self.dialog.run()
        elif b==3:
            self.menu.popup(None, None, None, b, event.time)
    menuItemActivate = lambda self, widget, icon: self.set_filename(icon)
    def dialogResponse(self, dialog, response=0):
        if response==0:
            self.image.set_from_file(dialog.get_filename())
        self.dialog.hide()
    def fileActivated(self, dialog):
        self.filename = dialog.get_filename()
        self.image.set_from_file(self.filename)
        self.dialog.hide()
    get_filename = lambda self: self.filename
    def set_filename(self, filename):
        self.dialog.set_filename(filename)
        self.filename = filename
        if not filename:
            self.image.set_from_file(join(pixDir, 'empty.png'))
        else:
            self.image.set_from_file(filename)

class EventWidget(gtk.VBox):
    def __init__(self, event):
        gtk.VBox.__init__(self)
        self.event = event
        ###########
        hbox = gtk.HBox()
        ###
        hbox.pack_start(gtk.Label(_('Calendar Type')+':'), 0, 0)
        combo = gtk.combo_box_new_text()
        for module in core.modules:
            combo.append_text(_(module.desc))
        combo.set_active(core.primaryMode)
        hbox.pack_start(combo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.modeCombo = combo
        ###
        self.pack_start(hbox, 0, 0)
        ###########
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Summary')), 0, 0)
        self.summuryEntry = gtk.Entry()
        hbox.pack_start(self.summuryEntry, 1, 1)
        self.pack_start(hbox, 0, 0)
        ###########
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Description')), 0, 0)
        textview = gtk.TextView()
        textview.set_wrap_mode(gtk.WRAP_WORD)
        self.descriptionBuff = textview.get_buffer()
        frame = gtk.Frame()
        frame.set_border_width(4)
        frame.add(textview)
        hbox.pack_start(frame, 1, 1)
        self.pack_start(hbox, 0, 0)
        ###########
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Icon')+':'), 0, 0)
        self.iconSelect = IconSelectButton()
        #print join(pixDir, self.defaultIcon)
        hbox.pack_start(self.iconSelect, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.pack_start(hbox, 0, 0)
        ##########
        self.modeCombo.connect('changed', self.modeComboChanged)## right place? before updateWidget? FIXME
    def updateWidget(self):
        self.modeCombo.set_active(self.event.mode)
        self.summuryEntry.set_text(self.event.summary)
        self.descriptionBuff.set_text(self.event.description)
        self.iconSelect.set_filename(self.event.icon)
        try:
            filesBox = self.filesBox
        except AttributeError:
            pass
        else:
            filesBox.updateWidget()
        self.modeComboChanged(self.modeCombo)
    def updateVars(self):
        self.event.mode = self.modeCombo.get_active()
        self.event.summary = self.summuryEntry.get_text()
        self.event.description = buffer_get_text(self.descriptionBuff)
        self.event.icon = self.iconSelect.get_filename()
    def modeComboChanged(self, combo):## FIXME
        pass


class FilesBox(gtk.VBox):
    def __init__(self, event):
        gtk.VBox.__init__(self)
        self.event = event
        self.vbox = gtk.VBox()
        self.pack_start(self.vbox, 0, 0)
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(''), 1, 1)
        addButton = gtk.Button()
        addButton.set_label(_('_Add File'))
        addButton.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON))
        addButton.connect('clicked', self.addClicked)
        hbox.pack_start(addButton, 0, 0)
        self.pack_start(hbox, 0, 0)
        self.show_all()
        self.newFiles = []
    def showFile(self, fname):
        hbox = gtk.HBox()
        hbox.pack_start(gtk.LinkButton(
            self.event.getUrlForFile(fname),
            _('File') + ': ' + fname,
        ), 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        delButton = gtk.Button()
        delButton.set_label(_('_Delete'))
        delButton.set_image(gtk.image_new_from_stock(gtk.STOCK_DELETE, gtk.ICON_SIZE_BUTTON))
        delButton.fname = fname
        delButton.hbox = hbox
        delButton.connect('clicked', self.delClicked)
        hbox.pack_start(delButton, 0, 0)
        self.vbox.pack_start(hbox, 0, 0)
        hbox.show_all()
    def addClicked(self, button):
        fcd = gtk.FileChooserDialog(
            buttons=(
                toStr(_('_OK')), gtk.RESPONSE_OK,
                toStr(_('_Cancel')), gtk.RESPONSE_CANCEL,
            ),
            title=_('Add File'),
        )
        fcd.connect('response', lambda w, e: fcd.hide())
        if fcd.run()==gtk.RESPONSE_OK:
            fpath = fcd.get_filename()
            fname = split(fpath)[-1]
            dstDir = self.event.filesDir
            ## os.makedirs(dstDir, exist_ok=True)## only on new pythons FIXME
            try:
                os.makedirs(dstDir)
            except:
                myRaise()
            shutil.copy(fpath, join(dstDir, fname))
            self.event.files.append(fname)
            self.newFiles.append(fname)
            self.showFile(fname)
    def delClicked(self, button):
        os.remove(join(self.event.filesDir, button.fname))
        try:
            self.event.files.remove(button.fname)
        except:
            pass
        button.hbox.destroy()
    def removeNewFiles(self):
        for fname in self.newFiles:
            os.remove(join(self.event.filesDir, fname))
        self.newFiles = []
    def updateWidget(self):
        for hbox in self.vbox.get_children():
            hbox.destroy()
        for fname in self.event.files:
            self.showFile(fname)

class NotifiersCheckList(gtk.Expander):
    def __init__(self):
        gtk.Expander.__init__(self, _('Notifiers'))
        self.hboxDict = {}
        totalVbox = gtk.VBox()
        for cls in event_man.eventNotifiersClassList:
            notifier = cls(self.event)
            inputWidget = notifier.makeWidget()
            hbox = gtk.HBox()
            cb = gtk.CheckButton(notifier.desc)
            cb.inputWidget = inputWidget
            cb.connect('clicked', lambda check: check.inputWidget.set_sensitive(check.get_active()))
            cb.set_active(False)
            hbox.pack_start(cb, 0, 0)
            hbox.cb = cb
            #hbox.pack_start(gtk.Label(''), 1, 1)
            hbox.pack_start(inputWidget, 1, 1)
            hbox.inputWidget = inputWidget
            self.hboxDict[notifier.name] = hbox
            totalVbox.pack_start(hbox, 0, 0)
        self.add(totalVbox)
    def setNotifiers(self, notifiers):
        for hbox in self.hboxDict.values():
            hbox.cb.set_active(False)
            hbox.inputWidget.set_sensitive(False)
        for notifier in notifiers:
            hbox = self.hboxDict[notifier.name]
            hbox.cb.set_active(True)
            hbox.inputWidget.set_sensitive(True)
            hbox.inputWidget.notifier = notifier
            hbox.inputWidget.updateWidget()
    def getNotifiers(self):
        notifiers = []
        for hbox in self.hboxDict.values():
            if hbox.cb.get_active():
                hbox.inputWidget.updateVars()
                notifiers.append(hbox.inputWidget.notifier)
        return notifiers


class DurationInputBox(gtk.HBox):
    def __init__(self):
        gtk.HBox.__init__(self)
        ##
        spin = gtk.SpinButton()
        spin.set_increments(1, 10)
        spin.set_range(0, 999)
        spin.set_digits(1)
        spin.set_direction(gtk.TEXT_DIR_LTR)
        #spin.set_width_chars
        self.pack_start(spin, 0, 0)
        self.valueSpin = spin
        ##
        combo = gtk.combo_box_new_text()
        for unitValue, unitName in durationUnitsAbs:
            combo.append_text(_(' '+unitName.capitalize()+'s'))
        combo.set_active(2) ## hour FIXME
        self.pack_start(combo, 0, 0)
        self.unitCombo = combo
    def getDuration(self):
        return self.valueSpin.get_value(), durationUnitValues[self.unitCombo.get_active()]
    def setDuration(self, value, unit):
        self.valueSpin.set_value(value)
        self.unitCombo.set_active(durationUnitValues.index(unit))


class GroupComboBox(gtk.ComboBox):
    def __init__(self):
        pass


class EventEditorDialog(gtk.Dialog):
    def __init__(self, event=None, eventType='', group=None, title=None, parent=None):## don't give both event a eventType
        gtk.Dialog.__init__(self, parent=parent)
        #self.set_transient_for(parent)
        if title:
            self.set_title(title)
        #self.connect('delete-event', lambda obj, e: self.destroy())
        #self.resize(800, 600)
        ###
        cancelB = self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        okB = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        if ui.autoLocale:
            cancelB.set_label(_('_Cancel'))
            cancelB.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL,gtk.ICON_SIZE_BUTTON))
            okB.set_label(_('_OK'))
            okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK,gtk.ICON_SIZE_BUTTON))
        self.connect('response', lambda w, e: self.hide())
        #######
        self.event = event
        self.activeEventWidget = None
        #######
        #print 'eventType = %r'%eventType
        if eventType:
            cls = event_man.eventsClassDict[eventType]
            self.event = cls()
            self.event.setDefaultsFromGroup(group)
            if group:## FIXME
                self.event.setDefaultsFromGroup(group)
            self.activeEventWidget = self.event.makeWidget()
        else:
            hbox = gtk.HBox()
            combo = gtk.combo_box_new_text()
            for cls in event_man.eventsClassList:
                combo.append_text(cls.desc)
            hbox.pack_start(gtk.Label(_('Event Type')), 0, 0)
            hbox.pack_start(combo, 0, 0)
            hbox.pack_start(gtk.Label(''), 1, 1)
            hbox.show_all()
            self.vbox.pack_start(hbox, 0, 0)
            ####
            if self.event:
                combo.set_active(event_man.eventsClassNameList.index(self.event.name))
            else:
                combo.set_active(event_man.defaultEventTypeIndex)
                self.event = event_man.eventsClassList[event_man.defaultEventTypeIndex]()
                if group:## FIXME
                    self.event.setDefaultsFromGroup(group)
            self.activeEventWidget = self.event.makeWidget()
            combo.connect('changed', self.eventTypeChanged)
            self.comboEventType = combo
        self.vbox.pack_start(self.activeEventWidget, 0, 0)
        self.vbox.show()
    def dateModeChanged(self, combo):
        pass
    def eventTypeChanged(self, combo):
        if self.activeEventWidget:
            self.activeEventWidget.destroy()
        event = event_man.eventsClassList[combo.get_active()]()
        #event = event_man.eventsClassByDesc[combo.get_active_text()]()## FIXME
        if self.event:
            event.copyFrom(self.event)
            event.setId(self.event.eid)
            del self.event
        self.event = event
        self.activeEventWidget = event.makeWidget()
        self.vbox.pack_start(self.activeEventWidget, 0, 0)
    def run(self):
        if not self.activeEventWidget or not self.event:
            return None
        if gtk.Dialog.run(self)!=gtk.RESPONSE_OK:
            try:
                filesBox = self.activeEventWidget.filesBox
            except AttributeError:
                pass
            else:
                filesBox.removeNewFiles()
            return None
        self.activeEventWidget.updateVars()
        self.event.saveConfig()
        self.destroy()
        return self.event

class GroupEditorDialog(gtk.Dialog):
    def __init__(self, group=None):
        gtk.Dialog.__init__(self)
        self.set_title(_('Edit Group') if group else _('Add New Group'))
        #self.connect('delete-event', lambda obj, e: self.destroy())
        #self.resize(800, 600)
        ###
        cancelB = self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        okB = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        if ui.autoLocale:
            cancelB.set_label(_('_Cancel'))
            cancelB.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL,gtk.ICON_SIZE_BUTTON))
            okB.set_label(_('_OK'))
            okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK,gtk.ICON_SIZE_BUTTON))
        self.connect('response', lambda w, e: self.hide())
        #######
        self._group = group
        self.activeGroupWidget = None
        #######
        hbox = gtk.HBox()
        combo = gtk.combo_box_new_text()
        for cls in event_man.eventGroupsClassList:
            combo.append_text(cls.desc)
        hbox.pack_start(gtk.Label(_('Group Type')), 0, 0)
        hbox.pack_start(combo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        ####
        if self._group:
            self.isNewGroup = False
            combo.set_active(event_man.eventGroupsClassNameList.index(self._group.name))
        else:
            self.isNewGroup = True
            combo.set_active(event_man.defaultGroupTypeIndex)
            self._group = event_man.eventGroupsClassList[event_man.defaultGroupTypeIndex]()
        self.activeGroupWidget = None
        combo.connect('changed', self.groupTypeChanged)
        self.comboGroupType = combo
        self.vbox.show_all()
        self.groupTypeChanged()
    def dateModeChanged(self, combo):
        pass
    def getNewGroupTitle(self, baseTitle):
        usedTitles = [group.title for group in ui.eventGroups]
        if not baseTitle in usedTitles:
            return baseTitle
        i = 1
        while True:
            newTitle = baseTitle + ' ' + _(i)
            if newTitle in usedTitles:
                i += 1
            else:
                return newTitle
    def groupTypeChanged(self, combo=None):
        if self.activeGroupWidget:
            self.activeGroupWidget.updateVars()
            self.activeGroupWidget.destroy()
        cls = event_man.eventGroupsClassList[self.comboGroupType.get_active()]
        group = cls()
        if self._group:
            if self.isNewGroup:
                if group.defaultIcon:
                    self._group.defaultIcon = group.defaultIcon
            group.copyFrom(self._group)
            group.setId(self._group.gid)
            del self._group
        if self.isNewGroup:
            group.title = self.getNewGroupTitle(cls.desc)
        self._group = group
        self.activeGroupWidget = group.makeWidget()
        self.vbox.pack_start(self.activeGroupWidget, 0, 0)
    def run(self):
        if self.activeGroupWidget is None or self._group is None:
            return None
        if gtk.Dialog.run(self)!=gtk.RESPONSE_OK:
            return None
        self.activeGroupWidget.updateVars()
        self._group.saveConfig()
        ui.eventGroups[self._group.gid] = self._group
        self.destroy()
        return self._group

if __name__ == '__main__':
    from pprint import pformat
    if core.rtl:
        gtk.widget_set_default_direction(gtk.TEXT_DIR_RTL)
    dialog = gtk.Window()
    dialog.vbox = gtk.VBox()
    dialog.add(dialog.vbox)
    #widget = ViewEditTagsHbox()
    widget = EventTagsAndIconSelect()
    #widget = TagsListBox('task')
    dialog.vbox.pack_start(widget, 1, 1)
    #dialog.vbox.show_all()
    #dialog.resize(300, 500)
    #dialog.run()
    dialog.show_all()
    gtk.main()
    print pformat(widget.getData())



