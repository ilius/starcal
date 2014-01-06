from scal2 import core
from scal2.locale_man import tr as _

from scal2.locale_man import tr as _
from scal2.ui_gtk.event.groups.vcsEpochBase import VcsEpochBaseGroupWidget as BaseGroupWidget


class GroupWidget(BaseGroupWidget):
    def __init__(self, group):
        BaseGroupWidget.__init__(self, group)
        ####
        hbox = gtk.HBox()
        label = gtk.Label(_('Tag Description'))
        label.set_alignment(0, 0.5)
        self.sizeGroup.add_widget(label)
        pack(hbox, label)
        ##
        self.statCheck = gtk.CheckButton(_('Stat'))
        pack(hbox, self.statCheck)
        ##
        pack(self, hbox)
    def updateWidget(self):
        BaseGroupWidget.updateWidget(self)
        self.statCheck.set_active(self.group.showStat)
    def updateVars(self):
        BaseGroupWidget.updateVars(self)
        self.group.showStat = self.statCheck.get_active()






