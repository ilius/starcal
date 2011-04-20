from os.path import join

from scal2 import core
from scal2.locale_man import tr as _
from scal2.core import pixDir, numLocale

from scal2 import event_man
from scal2 import ui

import gtk
from gtk import gdk

buffer_get_text = lambda b: b.get_text(b.get_start_iter(), b.get_end_iter())

def hideList(widgets):
    for w in widgets:
        w.hide()
def showList(widgets):
    for w in widgets:
        w.show()
def set_tooltip(widget, text):
    try:
        widget.set_tooltip_text(text)## PyGTK 2.12 or above
    except AttributeError:
        try:
            widget.set_tooltip(gtk.Tooltips(), text)
        except:
            myRaise(__file__)


class IconSelectButton(gtk.Button):
    def __init__(self, filename=''):
        gtk.Button.__init__(self)
        self.image = gtk.Image()
        self.add(self.image)
        self.dialog = gtk.FileChooserDialog(
            title=_('Select Icon File'),
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
        )
        okB = self.dialog.add_button(gtk.STOCK_OK, 0)
        cancelB = self.dialog.add_button(gtk.STOCK_CANCEL, 1)
        ###
        menu = gtk.Menu()
        self.menu = menu
        for item in ui.eventTags:
            icon = item.icon
            if icon:
                menuItem = gtk.ImageMenuItem(item.desc)
                menuItem.set_image(gtk.image_new_from_file(icon))
                menuItem.connect('activate', self.menuItemActivate, icon)
                menu.add(menuItem)
        menu.show_all()
        ###
        self.dialog.connect('file-activated', self.fileActivated)
        self.dialog.connect('response', self.dialogResponse)
        #self.connect('clicked', lambda button: button.dialog.run())
        self.connect('button-press-event', self.buttonPressEvent)
        ###
        self.set_filename(filename)
    def buttonPressEvent(self, widget, event):
        b = event.button
        if b==1:
            self.dialog.run()
        elif b==3:
            self.menu.popup(None, None, None, b, event.time)
    menuItemActivate = lambda self, widget, icon: self.set_filename(icon)
    def dialogResponse(self, dialog, response=0):
        if response==0:
            self.image.set_from_file(dialog.get_filename())
        self.dialog.hide()
    def fileActivated(self, dialog):
        self.filename = dialog.get_filename()
        self.image.set_from_file(self.filename)
        self.dialog.hide()
    get_filename = lambda self: self.filename
    def set_filename(self, filename):
        self.dialog.set_filename(filename)
        self.filename = filename
        if not filename:
            self.image.set_from_file(join(pixDir, 'empty.png'))
        else:
            self.image.set_from_file(filename)



#class EventCategorySelect(gtk.HBox):

class EventTagsAndIconSelect(gtk.HBox):
    def __init__(self):
        gtk.HBox.__init__(self)
        #########
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Category')+':'), 0, 0)
        #####
        ls = gtk.ListStore(gdk.Pixbuf, str)
        combo = gtk.ComboBox(ls)
        ###
        cell = gtk.CellRendererPixbuf()
        combo.pack_start(cell, False)
        combo.add_attribute(cell, 'pixbuf', 0)  
        ###
        cell = gtk.CellRendererText()
        combo.pack_start(cell, True)
        combo.add_attribute(cell, 'text', 1)  
        ###
        ls.append([None, _('Custom')])## first or last FIXME
        for item in ui.eventTags:
            ls.append([
                gdk.pixbuf_new_from_file(item.icon) if item.icon else None,
                item.desc
            ])
        ###
        self.customItemIndex = 0 ## len(ls)-1
        hbox.pack_start(combo, 0, 0)
        self.typeCombo = combo
        self.typeStore = ls
        
        ###
        vbox = gtk.VBox()
        vbox.pack_start(hbox, 0, 0)
        self.pack_start(vbox, 0, 0)
        #########
        iconLabel = gtk.Label(_('Icon'))
        hbox.pack_start(iconLabel, 0, 0)
        self.iconSelect = IconSelectButton()
        hbox.pack_start(self.iconSelect, 0, 0)
        tagsLabel = gtk.Label(_('Tags'))
        hbox.pack_start(tagsLabel, 0, 0)
        hbox3 = gtk.HBox()
        self.tagButtons = []
        for item in ui.eventTags:
            button = gtk.ToggleButton(item.desc)
            button.tagName = item.name
            self.tagButtons.append(button)
            hbox3.pack_start(button, 0, 0)
        self.swin = gtk.ScrolledWindow()
        self.swin.set_policy(gtk.POLICY_ALWAYS, gtk.POLICY_NEVER)## horizontal AUTOMATIC or ALWAYS FIXME
        self.swin.add_with_viewport(hbox3)
        self.pack_start(self.swin, 1, 1)
        self.customTypeWidgets = (iconLabel, self.iconSelect, tagsLabel, self.swin)
        #########
        self.typeCombo.connect('changed', self.typeComboChanged)
        self.connect('scroll-event', self.scrollEvent)
        #########
        self.show_all()
        hideList(self.customTypeWidgets)
    def scrollEvent(self, widget, event):
        self.swin.get_hscrollbar().emit('scroll-event', event)
    def typeComboChanged(self, combo):
        i = combo.get_active()
        if i is None:
            return
        if i == self.customItemIndex:
            showList(self.customTypeWidgets)
        else:
            hideList(self.customTypeWidgets)
    def getData(self):
        active = self.typeCombo.get_active()
        if active in (-1, None):
            icon = ''
            tags = []
        else:
            if active == self.customItemIndex:
                icon = self.iconSelect.get_filename()
                tags = [button.tagName for button in self.tagButtons if button.get_active()]
            else:
                item = ui.eventTags[active]
                icon = item.icon
                tags = [item.name]
        return {
            'icon': icon,
            'tags': tags,
        }


class TagsListBox(gtk.VBox):
    '''
        [x] Only related tags     tt: Show only tags related to this event type
        Sort by:
            Name
            Usage


        Related to this event type (first)
        Most used (first)
        Most used for this event type (first)
    '''
    def __init__(self, eventType=''):## '' == 'custom'
        gtk.VBox.__init__(self)
        ####
        self.eventType = eventType
        ########
        if eventType:
            hbox = gtk.HBox()
            self.relatedCheck = gtk.CheckButton(_('Only related tags'))
            set_tooltip(self.relatedCheck, _('Show only tags related to this event type'))
            self.relatedCheck.set_active(True)
            self.relatedCheck.connect('clicked', self.optionsChanged)
            hbox.pack_start(self.relatedCheck, 0, 0)
            hbox.pack_start(gtk.Label(''), 1, 1)
            self.pack_start(hbox, 0, 0)
        ########
        treev = gtk.TreeView()
        trees = gtk.ListStore(str, bool, str, int, str)## name(hidden), enable, desc, usage(hidden), usage(numLocale)
        treev.set_model(trees)
        ###
        cell = gtk.CellRendererToggle()
        #cell.set_property('activatable', True)
        cell.connect('toggled', self.enableCellToggled)
        col = gtk.TreeViewColumn(_('Enable'), cell)
        col.add_attribute(cell, "active", 1)
        #cell.set_active(False)
        col.set_resizable(True)
        col.set_sort_column_id(1)
        col.set_sort_indicator(True)
        treev.append_column(col)
        ###
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn(_('Name'), cell, text=2)## really desc, not name
        col.set_resizable(True)
        col.set_sort_column_id(2)
        col.set_sort_indicator(True)
        treev.append_column(col)
        ###
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn(_('Usage'), cell, text=4)
        #col.set_resizable(True)
        col.set_sort_column_id(3) ## previous column (hidden and int)
        col.set_sort_indicator(True)
        treev.append_column(col)
        ###
        swin = gtk.ScrolledWindow()
        swin.add(treev)
        swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.pack_start(swin, 1, 1)
        ####
        self.treeview = treev
        self.treestore = trees
        ####
        ui.updateEventTagsUsage()
        #for (i, tagObj) in enumerate(ui.eventTags): tagObj.usage = i*10 ## for testing
        self.optionsChanged()
        self.show_all()
    def optionsChanged(self, widget=None, tags=[]):
        if not tags:
            tags = self.getData()
        tagObjList = ui.eventTags
        if self.eventType:
            if self.relatedCheck.get_active():
                tagObjList = [t for t in tagObjList if self.eventType in t.eventTypes]
        self.treestore.clear()
        for t in tagObjList:
            self.treestore.append((
                t.name,
                t.name in tags, ## True or False
                t.desc,
                t.usage,
                numLocale(t.usage)
            ))
    def enableCellToggled(self, cell, path):
        i = int(path)
        active = not cell.get_active()
        self.treestore[i][1] = active
        cell.set_active(active)
    def getData(self):
        tags = []
        for row in self.treestore:
            if row[1]:
                tags.append(row[0])
        return tags
    def setData(self, tags):
        self.optionsChanged(tags=tags)



class TagEditorDialog(gtk.Dialog):
    def __init__(self, eventType=''):
        gtk.Dialog.__init__(self)
        self.tags = []
        self.tagsBox = TagsListBox(eventType)
        self.vbox.pack_start(self.tagsBox, 1, 1)
        ####
        cancelB = self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        okB = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        #if ui.autoLocale:
        cancelB.set_label(_('_Cancel'))
        cancelB.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_BUTTON))
        okB.set_label(_('_OK'))
        okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK, gtk.ICON_SIZE_BUTTON))
        self.vbox.show_all()
        self.getData = self.tagsBox.getData
        self.setData = self.tagsBox.setData




class ViewEditTagsHbox(gtk.HBox):
    def __init__(self, eventType=''):
        gtk.HBox.__init__(self)
        self.tags = []
        self.pack_start(gtk.Label(_('Tags:  ')), 0, 0)
        self.tagsLabel = gtk.Label('')
        self.pack_start(self.tagsLabel, 1, 1)
        self.dialog = TagEditorDialog(eventType)
        self.dialog.connect('response', self.dialogResponse)
        self.editButton = gtk.Button()
        self.editButton.set_label(_('_Edit'))
        self.editButton.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT, gtk.ICON_SIZE_BUTTON))
        self.editButton.connect('clicked', self.editButtonClicked)
        self.pack_start(self.editButton, 0, 0)
        self.show_all()
    def editButtonClicked(self, widget):
        self.dialog.present()
    def dialogResponse(self, dialog, resp):
        print 'dialogResponse', dialog, resp
        if resp==gtk.RESPONSE_OK:
            self.setData(dialog.getData())
        dialog.hide()
    def setData(self, tags):
        self.tags = tags
        self.dialog.setData(tags)
        sep = _(',') + ' '
        self.tagsLabel.set_label(sep.join([ui.eventTagsDesc[tag] for tag in tags]))
    def getData(self):
        return self.tags


if __name__ == '__main__':
    from pprint import pformat
    if core.rtl:
        gtk.widget_set_default_direction(gtk.TEXT_DIR_RTL)
    dialog = gtk.Dialog()
    widget = ViewEditTagsHbox()
    #widget = EventTagsAndIconSelect()
    #widget = TagsListBox('task')
    dialog.vbox.pack_start(widget, 1, 1)
    dialog.vbox.show()
    #dialog.resize(300, 500)
    dialog.run()
    print pformat(widget.getData())



