import pytz

from scal2.locale_man import tr as _

from scal2.ui_gtk import *
from scal2.ui_gtk.utils import CalTypeCombo, dialog_add_button, TimeZoneComboBoxEntry
from scal2.ui_gtk.mywidgets import TextFrame
from scal2.ui_gtk.mywidgets.icon import IconSelectButton

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
        pack(hbox, gtk.Label(_('Sort events of group "%s"')%group.title))
        pack(hbox, gtk.Label(''), 1, 1)
        pack(self.vbox, hbox)
        ###
        hbox = gtk.HBox()
        pack(hbox, gtk.Label(_('Based on')+' '))
        self.sortByNames = []
        self.sortByCombo = gtk.combo_box_new_text()
        sortByDefault, sortBys = group.getSortBys()
        for item in sortBys:
            self.sortByNames.append(item[0])
            self.sortByCombo.append_text(item[1])
        self.sortByCombo.set_active(self.sortByNames.index(sortByDefault))## FIXME
        pack(hbox, self.sortByCombo)
        self.reverseCheck = gtk.CheckButton(_('Descending'))
        pack(hbox, self.reverseCheck)
        pack(hbox, gtk.Label(''), 1, 1)
        pack(self.vbox, hbox)
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
        pack(hbox, label)
        pack(hbox, gtk.Label(''), 1, 1)
        pack(self.vbox, hbox)
        ###
        hbox = gtk.HBox()
        pack(hbox, gtk.Label(_('Calendar Type')+':'))
        combo = CalTypeCombo()
        combo.set_active(group.mode)
        pack(hbox, combo)
        pack(hbox, gtk.Label(''), 1, 1)
        self.modeCombo = combo
        pack(self.vbox, hbox)
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
                print(failedSummaryList)
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
        pack(self.vbox, label)
        ####
        hbox = gtk.HBox()
        self.iconRadio = gtk.RadioButton(label=_('Icon'))
        pack(hbox, self.iconRadio, 1, 1)
        self.summaryRadio = gtk.RadioButton(label=_('Summary'), group=self.iconRadio)
        pack(hbox, self.summaryRadio, 1, 1)
        self.descriptionRadio = gtk.RadioButton(label=_('Description'), group=self.iconRadio)
        pack(hbox, self.descriptionRadio, 1, 1)
        self.timeZoneRadio = gtk.RadioButton(label=_('Time Zone'), group=self.iconRadio)
        pack(hbox, self.timeZoneRadio, 1, 1)
        pack(self.vbox, hbox)
        ###
        self.iconRadio.connect('clicked', self.firstRadioChanged)
        self.summaryRadio.connect('clicked', self.firstRadioChanged)
        self.descriptionRadio.connect('clicked', self.firstRadioChanged)
        self.timeZoneRadio.connect('clicked', self.firstRadioChanged)
        ####
        hbox = gtk.HBox()
        self.iconChangeCombo = gtk.combo_box_new_text()
        self.iconChangeCombo.append_text('----')
        self.iconChangeCombo.append_text(_('Change'))
        self.iconChangeCombo.append_text(_('Change if empty'))
        pack(hbox, self.iconChangeCombo)
        pack(hbox, gtk.Label('  '))
        self.iconSelect = IconSelectButton()
        self.iconSelect.set_filename(group.icon)
        pack(hbox, self.iconSelect)
        pack(hbox, gtk.Label(''), 1, 1)
        pack(self.vbox, hbox)
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
        pack(hbox, self.textChangeCombo)
        pack(hbox, gtk.Label(''), 1, 1)
        ## CheckButton(_('Regexp'))
        pack(self.textVbox, hbox)
        ###
        self.textInput1 = TextFrame()
        pack(self.textVbox, self.textInput1, 1, 1)
        ###
        hbox = gtk.HBox()
        pack(hbox, gtk.Label(_('with')))
        pack(hbox, gtk.Label(''), 1, 1)
        pack(self.textVbox, hbox, 1, 1)
        self.withHbox = hbox
        ###
        self.textInput2 = TextFrame()
        pack(self.textVbox, self.textInput2, 1, 1)
        ####
        pack(self.vbox, self.textVbox, 1, 1)
        ####
        hbox = gtk.HBox()
        self.timeZoneChangeCombo = gtk.combo_box_new_text()
        self.timeZoneChangeCombo.append_text('----')
        self.timeZoneChangeCombo.append_text(_('Change'))
        pack(hbox, self.timeZoneChangeCombo)
        pack(hbox, gtk.Label('  '))
        self.timeZoneInput = TimeZoneComboBoxEntry()
        pack(hbox, self.timeZoneInput)
        pack(hbox, gtk.Label(''), 1, 1)
        pack(self.vbox, hbox, 1, 1)
        self.timeZoneHbox = hbox
        ####
        self.vbox.show_all()
        self.iconRadio.set_active(True)
        self.iconChangeCombo.set_active(0)
        self.textChangeCombo.set_active(0)
        self.firstRadioChanged()
    def firstRadioChanged(self, w=None):
        if self.iconRadio.get_active():
            self.iconHbox.show()
            self.textVbox.hide()
            self.timeZoneHbox.hide()
        elif self.timeZoneRadio.get_active():
            self.iconHbox.hide()
            self.textVbox.hide()
            self.timeZoneHbox.show()
        elif self.summaryRadio.get_active() or self.descriptionRadio.get_active():
            self.iconHbox.hide()
            self.textChangeComboChanged()
            self.timeZoneHbox.hide()
    def textChangeComboChanged(self, w=None):
        self.textVbox.show_all()
        chType = self.textChangeCombo.get_active()
        if chType==0:
            self.textInput1.hide()
            self.withHbox.hide()
            self.textInput2.hide()
        elif chType in (1, 2):
            self.withHbox.hide()
            self.textInput2.hide()
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
        elif self.timeZoneRadio.get_active():
            chType = self.timeZoneChangeCombo.get_active()
            timeZone = self.timeZoneInput.get_text()
            if chType!=0:
                try:
                    pytz.timezone(timeZone)
                except:
                    myRaise('Invalid Time Zone "%s"'%timeZone)
                else:
                    for event in group:
                        if chType==1:
                            event.timeZone = timeZone
                            event.save()
        else:
            chType = self.textChangeCombo.get_active()
            if chType!=0:
                text1 = self.textInput1.get_text()
                text2 = self.textInput2.get_text()
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

                            

