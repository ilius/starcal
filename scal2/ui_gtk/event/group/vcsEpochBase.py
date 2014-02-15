from scal2 import core
from scal2.locale_man import tr as _

from scal2.ui_gtk import *
from scal2.ui_gtk.event.group.vcsBase import VcsBaseGroupWidget


class VcsEpochBaseGroupWidget(VcsBaseGroupWidget):
    def __init__(self, group):
        VcsBaseGroupWidget.__init__(self, group)
        ######
        hbox = gtk.HBox()
        label = gtk.Label(_('Show Seconds'))
        label.set_alignment(0, 0.5)
        self.sizeGroup.add_widget(label)
        pack(hbox, label)
        pack(hbox, label)
        self.showSecondsCheck = gtk.CheckButton('')
        pack(hbox, self.showSecondsCheck)
        pack(self, hbox)
    def updateWidget(self):
        VcsBaseGroupWidget.updateWidget(self)
        self.showSecondsCheck.set_active(self.group.showSeconds)
    def updateVars(self):
        VcsBaseGroupWidget.updateVars(self)
        self.group.showSeconds = self.showSecondsCheck.get_active()

