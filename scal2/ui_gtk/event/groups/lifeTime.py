from scal2 import core
from scal2.locale_man import tr as _

from scal2.ui_gtk import *
from scal2.ui_gtk.event.groups.group import GroupWidget as NormalGroupWidget


class GroupWidget(NormalGroupWidget):
    def __init__(self, group):
        NormalGroupWidget.__init__(self, group)
        ####
        hbox = gtk.HBox()
        self.showSeperatedYmdInputsCheck = gtk.CheckButton(_('Show Seperated Inputs for Year, Month and Day'))
        pack(hbox, self.showSeperatedYmdInputsCheck)
        pack(hbox, gtk.Label(''), 1, 1)
        pack(self, hbox)
    def updateWidget(self):
        NormalGroupWidget.updateWidget(self)
        self.showSeperatedYmdInputsCheck.set_active(self.group.showSeperatedYmdInputs)
    def updateVars(self):
        NormalGroupWidget.updateVars(self)
        self.group.showSeperatedYmdInputs = self.showSeperatedYmdInputsCheck.get_active()



