from scal2.ui_gtk.event.groups.group import GroupWidget as NormalGroupWidget

from scal2.locale_man import tr as _
import gtk

class GroupWidget(NormalGroupWidget):
    def __init__(self, group):
        NormalGroupWidget.__init__(self, group)
        ####
        hbox = gtk.HBox()
        self.showSeperatedYmdInputsCheck = gtk.CheckButton(_('Show Seperated Inputs for Year, Month and Day'))
        hbox.pack_start(self.showSeperatedYmdInputsCheck, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.pack_start(hbox, 0, 0)
    def updateWidget(self):
        NormalGroupWidget.updateWidget(self)
        self.showSeperatedYmdInputsCheck.set_active(self.group.showSeperatedYmdInputs)
    def updateVars(self):
        NormalGroupWidget.updateVars(self)
        self.group.showSeperatedYmdInputs = self.showSeperatedYmdInputsCheck.get_active()



