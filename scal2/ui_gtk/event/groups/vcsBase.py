from scal2.locale_man import tr as _
from scal2.vcs_modules import vcsModuleNames

import gtk

from scal2.ui_gtk.event.groups.group import GroupWidget as NormalGroupWidget



class VcsBaseGroupWidget(NormalGroupWidget):
    def __init__(self, group):
        NormalGroupWidget.__init__(self, group)
        ######
        hbox = gtk.HBox()
        label = gtk.Label(_('VCS Type'))
        label.set_alignment(0, 0.5)
        self.sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        self.vcsTypeCombo = gtk.combo_box_new_text()
        for name in vcsModuleNames:
            self.vcsTypeCombo.append_text(name)## descriptive name FIXME
        hbox.pack_start(self.vcsTypeCombo, 0, 0)
        self.pack_start(hbox, 0, 0)
        ######
        hbox = gtk.HBox()
        label = gtk.Label(_('Directory'))
        label.set_alignment(0, 0.5)
        self.sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        self.dirEntry = gtk.Entry()
        hbox.pack_start(self.dirEntry, 0, 0)
        ##
        #self.dirBrowse = gtk.Button(_('Browse'))
        self.pack_start(hbox, 0, 0)
    def updateWidget(self):
        NormalGroupWidget.updateWidget(self)
        self.vcsTypeCombo.set_active(vcsModuleNames.index(self.group.vcsType))
        self.dirEntry.set_text(self.group.vcsDir)
    def updateVars(self):
        NormalGroupWidget.updateVars(self)
        self.group.vcsType = vcsModuleNames[self.vcsTypeCombo.get_active()]
        self.group.vcsDir = self.dirEntry.get_text()


