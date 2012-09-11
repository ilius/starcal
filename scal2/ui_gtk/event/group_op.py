from scal2.locale_man import tr as _

import gtk

from scal2.ui_gtk.utils import DateTypeCombo, dialog_add_button, buffer_get_text
from scal2.ui_gtk.event.common import IconSelectButton

class GroupSortDialog(gtk.Dialog):
    def __init__(self, group):
        self._group = group
        gtk.Dialog.__init__(self)
        self.set_title(_('Sort Events'))
        ####
        dialog_add_button(self, gtk.STOCK_CANCEL, _('_Cancel'), gtk.RESPONSE_CANCEL)
        dialog_add_button(self, gtk.STOCK_OK, _('_OK'), gtk.RESPONSE_OK)
        ##
        self.connect('response', lambda w, e: self.hide())
        ####
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Sort events of group "%s"')%group.title), 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        ###
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Based on')+' '), 0, 0)
        self.sortByNames = []
        self.sortByCombo = gtk.combo_box_new_text()
        for item in group.getSortBys():
            self.sortByNames.append(item[0])
            self.sortByCombo.append_text(item[1])
        self.sortByCombo.set_active(self.sortByNames.index(group.sortByDefault))## FIXME
        hbox.pack_start(self.sortByCombo, 0, 0)
        self.reverseCheck = gtk.CheckButton(_('Descending'))
        hbox.pack_start(self.reverseCheck, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        ####
        self.vbox.show_all()
    def run(self):
        if gtk.Dialog.run(self)==gtk.RESPONSE_OK:
            self._group.sort(
                self.sortByNames[self.sortByCombo.get_active()],
                self.reverseCheck.get_active(),
            )
            self._group.save()
            return True
        self.destroy()



class GroupConvertModeDialog(gtk.Dialog):
    def __init__(self, group):
        self._group = group
        gtk.Dialog.__init__(self)
        self.set_title(_('Convert Calendar Type'))
        ####
        dialog_add_button(self, gtk.STOCK_CANCEL, _('_Cancel'), gtk.RESPONSE_CANCEL)
        dialog_add_button(self, gtk.STOCK_OK, _('_OK'), gtk.RESPONSE_OK)
        ##
        self.connect('response', lambda w, e: self.hide())
        ####
        hbox = gtk.HBox()
        label = gtk.Label(_('This is going to convert calendar types of all events inside group \"%s\" to a specific type. This operation does not work for Yearly events and also some of Custom events. You have to edit those events manually to change calendar type.')%group.title)
        label.set_line_wrap(True)
        hbox.pack_start(label, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        ###
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Calendar Type')+':'), 0, 0)
        combo = DateTypeCombo()
        combo.set_active(group.mode)
        hbox.pack_start(combo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.modeCombo = combo
        self.vbox.pack_start(hbox, 0, 0)
        ####
        self.vbox.show_all()
    def run(self):
        if gtk.Dialog.run(self)==gtk.RESPONSE_OK:
            mode = self.modeCombo.get_active()
            failedSummaryList = []
            for event in self._group:
                if event.changeMode(mode):
                    event.save()
                else:
                    failedSummaryList.append(event.summary)
            if failedSummaryList:## FIXME
                print failedSummaryList
        self.destroy()


class GroupBulkEditDialog(gtk.Dialog):
    def __init__(self, group):
        self._group = group
        gtk.Dialog.__init__(self)
        self.set_title(_('Bulk Edit Events'))
        ####
        dialog_add_button(self, gtk.STOCK_CANCEL, _('_Cancel'), gtk.RESPONSE_CANCEL)
        dialog_add_button(self, gtk.STOCK_OK, _('_OK'), gtk.RESPONSE_OK)
        ##
        self.connect('response', lambda w, e: self.hide())
        ####
        label = gtk.Label(_('Here you are going to modify all events inside group "%s" at once. You better make a backup from you events before doing this. Just right click on group and select "Export" (or a full backup: menu File -> Export)')%group.title+'\n\n')
        label.set_line_wrap(True)
        self.vbox.pack_start(label, 0, 0)
        ####
        hbox = gtk.HBox()
        self.iconRadio = gtk.RadioButton(label=_('Icon'))
        hbox.pack_start(self.iconRadio, 1, 1)
        self.summaryRadio = gtk.RadioButton(label=_('Summary'), group=self.iconRadio)
        hbox.pack_start(self.summaryRadio, 1, 1)
        self.descriptionRadio = gtk.RadioButton(label=_('Description'), group=self.iconRadio)
        hbox.pack_start(self.descriptionRadio, 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        ###
        self.iconRadio.connect('clicked', self.firstRadioChanged)
        self.summaryRadio.connect('clicked', self.firstRadioChanged)
        self.descriptionRadio.connect('clicked', self.firstRadioChanged)
        ####
        hbox = gtk.HBox()
        self.iconChangeCombo = gtk.combo_box_new_text()
        self.iconChangeCombo.append_text('----')
        self.iconChangeCombo.append_text(_('Change'))
        self.iconChangeCombo.append_text(_('Change if empty'))
        hbox.pack_start(self.iconChangeCombo, 0, 0)
        hbox.pack_start(gtk.Label('  '), 0, 0)
        self.iconSelect = IconSelectButton()
        self.iconSelect.set_filename(group.icon)
        hbox.pack_start(self.iconSelect, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        self.iconHbox = hbox
        ####
        self.textVbox = gtk.VBox()
        ###
        hbox = gtk.HBox()
        self.textChangeCombo = gtk.combo_box_new_text()
        self.textChangeCombo.append_text('----')
        self.textChangeCombo.append_text(_('Add to beginning'))
        self.textChangeCombo.append_text(_('Add to end'))
        self.textChangeCombo.append_text(_('Replace text'))
        self.textChangeCombo.connect('changed', self.textChangeComboChanged)
        hbox.pack_start(self.textChangeCombo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        ## CheckButton(_('Regexp'))
        self.textVbox.pack_start(hbox, 0, 0)
        ###
        textview = gtk.TextView()
        textview.set_wrap_mode(gtk.WRAP_WORD)
        self.textBuf1 = textview.get_buffer()
        frame = gtk.Frame()
        frame.set_border_width(4)
        frame.add(textview)
        self.textVbox.pack_start(frame, 1, 1)
        self.textWidget1 = frame
        ###
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('with')), 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.textVbox.pack_start(hbox, 1, 1)
        self.withHbox = hbox
        ###
        textview = gtk.TextView()
        textview.set_wrap_mode(gtk.WRAP_WORD)
        self.textBuf2 = textview.get_buffer()
        frame = gtk.Frame()
        frame.set_border_width(4)
        frame.add(textview)
        self.textVbox.pack_start(frame, 1, 1)
        self.textWidget2 = frame
        ####
        self.vbox.pack_start(self.textVbox, 1, 1)
        self.vbox.show_all()
        self.iconRadio.set_active(True)
        self.iconChangeCombo.set_active(0)
        self.textChangeCombo.set_active(0)
        self.firstRadioChanged()
    def firstRadioChanged(self, w=None):
        if self.iconRadio.get_active():
            self.iconHbox.show()
            self.textVbox.hide()
        else:
            self.iconHbox.hide()
            self.textChangeComboChanged()
    def textChangeComboChanged(self, w=None):
        self.textVbox.show_all()
        chType = self.textChangeCombo.get_active()
        if chType==0:
            self.textWidget1.hide()
            self.withHbox.hide()
            self.textWidget2.hide()
        elif chType in (1, 2):
            self.withHbox.hide()
            self.textWidget2.hide()
    def doAction(self):
        group = self._group
        if self.iconRadio.get_active():
            chType = self.iconChangeCombo.get_active()
            if chType!=0:
                icon = self.iconSelect.get_filename()
                for event in group:
                    if not (chType==2 and event.icon):
                        event.icon = icon
                        event.afterModify()
                        event.save()
        else:
            chType = self.textChangeCombo.get_active()
            if chType!=0:
                text1 = buffer_get_text(self.textBuf1)
                text2 = buffer_get_text(self.textBuf2)
                if self.summaryRadio.get_active():
                    for event in group:
                        if chType==1:
                            event.summary = text1 + event.summary
                        elif chType==2:
                            event.summary = event.summary + text1
                        elif chType==3:
                            event.summary = event.summary.replace(text1, text2)
                        event.afterModify()
                        event.save()
                elif self.descriptionRadio.get_active():
                    for event in group:
                        if chType==1:
                            event.description = text1 + event.description
                        elif chType==2:
                            event.description = event.description + text1
                        elif chType==3:
                            event.description = event.description.replace(text1, text2)
                        event.afterModify()
                        event.save()

