from scal2.locale_man import tr as _

from scal2.ui_gtk.event.groups.base import BaseGroupWidget
from scal2.ui_gtk.event import common

import gtk

from scal2.ui_gtk.mywidgets.multi_spin_button import IntSpinButton

maxStartEnd = 999999

class GroupWidget(BaseGroupWidget):
    def __init__(self, group):
        BaseGroupWidget.__init__(self, group)
        ######
        sizeGroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        ######
        hbox = gtk.HBox()
        label = gtk.Label(_('Scale'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        self.scaleCombo = common.Scale10PowerComboBox()
        hbox.pack_start(self.scaleCombo, 0, 0)
        self.pack_start(hbox, 0, 0)
        ####
        hbox = gtk.HBox()
        label = gtk.Label(_('Start'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        self.startSpin = IntSpinButton(-maxStartEnd, maxStartEnd)
        hbox.pack_start(self.startSpin, 0, 0)
        self.pack_start(hbox, 0, 0)
        ####
        hbox = gtk.HBox()
        label = gtk.Label(_('End'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        self.endSpin = IntSpinButton(-maxStartEnd, maxStartEnd)
        hbox.pack_start(self.endSpin, 0, 0)
        self.pack_start(hbox, 0, 0)
    def updateWidget(self):
        BaseGroupWidget.updateWidget(self)
        self.scaleCombo.set_value(self.group.scale)
        self.startSpin.set_value(self.group.getStartValue())
        self.endSpin.set_value(self.group.getEndValue())
    def updateVars(self):
        BaseGroupWidget.updateVars(self)
        self.group.scale = self.scaleCombo.get_value()
        self.group.setStartValue(self.startSpin.get_value())
        self.group.setEndValue(self.endSpin.get_value())




