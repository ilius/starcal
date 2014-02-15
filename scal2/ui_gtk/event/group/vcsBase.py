from scal2 import core
from scal2.locale_man import tr as _
from scal2.vcs_modules import vcsModuleNames

from scal2.ui_gtk import *
from scal2.ui_gtk.event.group.group import GroupWidget as NormalGroupWidget



class VcsBaseGroupWidget(NormalGroupWidget):
    def __init__(self, group):
        NormalGroupWidget.__init__(self, group)
        ######
        hbox = gtk.HBox()
        label = gtk.Label(_('VCS Type'))
        label.set_alignment(0, 0.5)
        self.sizeGroup.add_widget(label)
        pack(hbox, label)
        self.vcsTypeCombo = gtk.combo_box_new_text()
        for name in vcsModuleNames:
            self.vcsTypeCombo.append_text(name)## descriptive name FIXME
        pack(hbox, self.vcsTypeCombo)
        pack(self, hbox)
        ######
        hbox = gtk.HBox()
        label = gtk.Label(_('Directory'))
        label.set_alignment(0, 0.5)
        self.sizeGroup.add_widget(label)
        pack(hbox, label)
        self.dirEntry = gtk.Entry()
        pack(hbox, self.dirEntry)
        ##
        #self.dirBrowse = gtk.Button(_('Browse'))
        pack(self, hbox)
    def updateWidget(self):
        NormalGroupWidget.updateWidget(self)
        self.vcsTypeCombo.set_active(vcsModuleNames.index(self.group.vcsType))
        self.dirEntry.set_text(self.group.vcsDir)
    def updateVars(self):
        NormalGroupWidget.updateVars(self)
        self.group.vcsType = vcsModuleNames[self.vcsTypeCombo.get_active()]
        self.group.vcsDir = self.dirEntry.get_text()


