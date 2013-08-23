from scal2.locale_man import tr as _

import gtk

from scal2.ui_gtk.event.groups.vcsBase import VcsBaseGroupWidget


class VcsEpochBaseGroupWidget(VcsBaseGroupWidget):
    def __init__(self, group):
        VcsBaseGroupWidget.__init__(self, group)
        ######
        hbox = gtk.HBox()
        label = gtk.Label(_('Show Seconds'))
        label.set_alignment(0, 0.5)
        self.sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        hbox.pack_start(label, 0, 0)
        self.showSecondsCheck = gtk.CheckButton('')
        hbox.pack_start(self.showSecondsCheck, 0, 0)
        self.pack_start(hbox, 0, 0)
    def updateWidget(self):
        VcsBaseGroupWidget.updateWidget(self)
        self.showSecondsCheck.set_active(self.group.showSeconds)
    def updateVars(self):
        VcsBaseGroupWidget.updateVars(self)
        self.group.showSeconds = self.showSecondsCheck.get_active()

