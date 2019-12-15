#!/usr/bin/env python3

from scal3 import logger
log = logger.get()

from scal3.locale_man import tr as _

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import (
	dialog_add_button,
	window_set_size_aspect,
)


class GroupSortDialog(gtk.Dialog):
	def __init__(self, group, **kwargs):
		self._group = group
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_("Sort Events"))
		####
		dialog_add_button(
			self,
			imageName="dialog-cancel.svg",
			label=_("_Cancel"),
			res=gtk.ResponseType.CANCEL,
		)
		dialog_add_button(
			self,
			imageName="dialog-ok.svg",
			label=_("_OK"),
			res=gtk.ResponseType.OK,
		)
		##
		self.connect("response", lambda w, e: self.hide())
		####
		hbox = HBox()
		pack(hbox, gtk.Label(
			label=_("Sort events of group \"{groupTitle}\"").format(
				groupTitle=group.title,
			),
		))
		pack(hbox, gtk.Label(), 1, 1)
		pack(self.vbox, hbox)
		###
		hbox = HBox()
		pack(hbox, gtk.Label(label=_("Based on") + " "))
		self.sortByNames = []
		self.sortByCombo = gtk.ComboBoxText()
		sortByDefault, sortBys = group.getSortBys()
		for item in sortBys:
			self.sortByNames.append(item[0])
			self.sortByCombo.append_text(item[1])
		self.sortByCombo.set_active(
			self.sortByNames.index(sortByDefault),
		)  # FIXME
		pack(hbox, self.sortByCombo)
		self.reverseCheck = gtk.CheckButton(label=_("Descending"))
		pack(hbox, self.reverseCheck)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self.vbox, hbox)
		####
		self.vbox.show_all()

	def run(self):
		if gtk.Dialog.run(self) == gtk.ResponseType.OK:
			self._group.sort(
				self.sortByNames[self.sortByCombo.get_active()],
				self.reverseCheck.get_active(),
			)
			self._group.save()
			return True
		self.destroy()


class GroupConvertCalTypeDialog(gtk.Dialog):
	def __init__(self, group, **kwargs):
		from scal3.ui_gtk.mywidgets.cal_type_combo import CalTypeCombo
		self._group = group
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_("Convert Calendar Type"))
		####
		dialog_add_button(
			self,
			imageName="dialog-cancel.svg",
			label=_("_Cancel"),
			res=gtk.ResponseType.CANCEL,
		)
		dialog_add_button(
			self,
			imageName="dialog-ok.svg",
			label=_("_OK"),
			res=gtk.ResponseType.OK,
		)
		##
		self.connect("response", lambda w, e: self.hide())
		####
		hbox = HBox()
		label = gtk.Label(_(
			"This is going to convert calendar types of all events inside "
			"group \"{groupTitle}\" to a specific type. This operation does not work "
			"for Yearly events and also some of Custom events. You have to "
			"edit those events manually to change calendar type."
		).format(groupTitle=group.title))
		label.set_line_wrap(True)
		pack(hbox, label)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self.vbox, hbox)
		###
		hbox = HBox()
		pack(hbox, gtk.Label(label=_("Calendar Type") + ":"))
		combo = CalTypeCombo()
		combo.set_active(group.calType)
		pack(hbox, combo)
		pack(hbox, gtk.Label(), 1, 1)
		self.calTypeCombo = combo
		pack(self.vbox, hbox)
		####
		self.vbox.show_all()
		window_set_size_aspect(self, 1.6)

	def perform(self) -> bool:
		if gtk.Dialog.run(self) == gtk.ResponseType.OK:
			calType = self.calTypeCombo.get_active()
			failedSummaryList = []
			for event in self._group:
				if event.changeCalType(calType):
					event.save()
				else:
					failedSummaryList.append(event.summary)
			if failedSummaryList:## FIXME
				log.error(f"failedSummaryList={failedSummaryList}")
			return True
		self.destroy()
		return False
