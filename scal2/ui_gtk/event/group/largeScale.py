from scal2 import core
from scal2.locale_man import tr as _

from scal2.ui_gtk import *
from scal2.ui_gtk.mywidgets.multi_spin_button import IntSpinButton
from scal2.ui_gtk.event.group.base import BaseGroupWidget
from scal2.ui_gtk.event import common


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
        pack(hbox, label)
        self.scaleCombo = common.Scale10PowerComboBox()
        pack(hbox, self.scaleCombo)
        pack(self, hbox)
        ####
        hbox = gtk.HBox()
        label = gtk.Label(_('Start'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        pack(hbox, label)
        self.startSpin = IntSpinButton(-maxStartEnd, maxStartEnd)
        pack(hbox, self.startSpin)
        pack(self, hbox)
        ####
        hbox = gtk.HBox()
        label = gtk.Label(_('End'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        pack(hbox, label)
        self.endSpin = IntSpinButton(-maxStartEnd, maxStartEnd)
        pack(hbox, self.endSpin)
        pack(self, hbox)
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




