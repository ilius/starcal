from scal2.locale_man import tr as _

import gtk

from scal2.ui_gtk.event.groups.vcsBase import VcsBaseGroupWidget


class GroupWidget(VcsBaseGroupWidget):
    def __init__(self, group):
        VcsBaseGroupWidget.__init__(self, group)
        ####
        hbox = gtk.HBox()
        label = gtk.Label(_('Tag Description'))
        label.set_alignment(0, 0.5)
        self.sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        ##
        self.statCheck = gtk.CheckButton(_('Stat'))
        hbox.pack_start(self.statCheck, 0, 0)
        ##
        self.pack_start(hbox, 0, 0)
    def updateWidget(self):
        VcsBaseGroupWidget.updateWidget(self)
        self.statCheck.set_active(self.group.showStat)
    def updateVars(self):
        VcsBaseGroupWidget.updateVars(self)
        self.group.showStat = self.statCheck.get_active()






