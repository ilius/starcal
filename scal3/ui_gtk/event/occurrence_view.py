#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from scal3 import logger
log = logger.get()

from typing import Dict, Any, Tuple, Optional

from scal3.utils import toStr
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import event_lib
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.font_utils import gfontEncode
from scal3.ui_gtk.utils import (
	imageFromFile,
	pixbufFromFile,
	setClipboard,
	buffer_get_text,
)
from scal3.ui_gtk.menuitems import (
	ImageMenuItem,
)
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.customize import CustomizableCalObj

@registerSignals
class DayOccurrenceView(gtk.TextView, CustomizableCalObj):
	_name = "eventDayView"
	desc = _("Events of Day")
	itemListCustomizable = False

	def __init__(
		self,
		eventSepParam: str = "",
		justificationParam: str = "",
		fontParams: Optional[Tuple[str, str]] = None,
		timeFontParams: Optional[Tuple[str, str]] = None,
		styleClass: str = "",
		wrapMode: pango.WrapMode = pango.WrapMode.WORD_CHAR,
	):
		gtk.TextView.__init__(self)
		self.set_editable(False)
		self.set_cursor_visible(False)
		self.set_wrap_mode(wrapMode)
		###
		self.styleClass = styleClass
		if styleClass:
			self.get_style_context().add_class(styleClass)
		###
		self.connect("button-press-event", self.onButtonPress)
		###
		self.textbuff = self.get_buffer()
		# Gtk.ScrolledWindow.add_with_viewport is Deprecated since version 3.8:
		# Gtk.Container.add() will automatically add a Gtk.Viewport if the
		# child doesn't implement Gtk.Scrollable.
		self.initVars()
		self.wrapMode = wrapMode
		self.showDesc = True
		###
		self.eventSepParam = eventSepParam
		self.justificationParam = justificationParam
		self.fontParams = fontParams
		self.timeFontParams = timeFontParams
		###
		if fontParams:
			if not styleClass:
				raise ValueError(f"fontParams={fontParams}, styleClass={styleClass}")
			ud.windowList.addCSSFunc(self.getCSS)
		###
		self.occurOffsets = []
		self.eventMenuItemLabelMaxLen = 25
		self.updateJustification()
		###
		self.timeTag = gtk.TextTag.new("time")
		self.textbuff.get_tag_table().add(self.timeTag)
		self.updateTimeFont()

	def updateTimeFont(self):
		font = list(ui.getFont())
		font[1] = True  # bold by default
		if self.timeFontParams:
			enableParam, fontParam = self.timeFontParams
			if getattr(ui, enableParam):
				font = getattr(ui, fontParam)
		self.timeTag.set_property("font", gfontEncode(font))

	def getEventSep(self):
		if self.eventSepParam:
			return getattr(ui, self.eventSepParam)
		return "\n\n"

	def updateJustification(self):
		if not self.justificationParam:
			return
		value = getattr(ui, self.justificationParam)
		self.set_justification(ud.justificationByName[value])

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.pref_utils import (
			TextPrefItem,
			JustificationPrefItem,
			CheckFontPrefItem,
			CheckPrefItem,
			FontPrefItem,
		)
		if self.optionsWidget:
			return self.optionsWidget
		optionsWidget = VBox(spacing=10)
		###
		if self.justificationParam:
			prefItem = JustificationPrefItem(
				ui,
				self.justificationParam,
				label=_("Text Alignment"),
				onChangeFunc=self.updateJustification,
			)
			pack(optionsWidget, prefItem.getWidget())
		###
		if self.fontParams:
			enableParam, fontParam = self.fontParams
			prefItem = CheckFontPrefItem(
				CheckPrefItem(ui, enableParam, label=_("Font")),
				FontPrefItem(ui, fontParam),
				live=True,
				onChangeFunc=ud.windowList.updateCSS,
			)
			pack(optionsWidget, prefItem.getWidget())
		if self.timeFontParams:
			enableParam, fontParam = self.timeFontParams
			prefItem = CheckFontPrefItem(
				CheckPrefItem(ui, enableParam, label=_("Time Font")),
				FontPrefItem(ui, fontParam),
				live=True,
				onChangeFunc=self.updateTimeFont,
			)
			pack(optionsWidget, prefItem.getWidget())
		###
		if self.eventSepParam:
			prefItem = TextPrefItem(
				ui,
				self.eventSepParam,
				label=_("Event Text Separator"),
				live=True,
				onChangeFunc=self.onEventSepChange,
			)
			pack(optionsWidget, prefItem.getWidget())
		###
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	def getCSS(self) -> str:
		from scal3.ui_gtk.utils import cssTextStyle
		enableParam, fontParam = self.fontParams
		if not getattr(ui, enableParam):
			return ""
		font = getattr(ui, fontParam)
		if not font:
			return ""
		return "." + self.styleClass + " " + cssTextStyle(font=font)

	def onEventSepChange(self):
		self.onDateChange(toParent=False)

	def get_cursor_position(self):
		return self.get_property("cursor-position")

	def has_selection(self):
		buf = self.get_buffer()
		try:
			start_iter, end_iter = buf.get_selection_bounds()
		except ValueError:
			return False
		else:
			return True

	def get_text(self):
		return buffer_get_text(self.get_buffer())

	def copy(self, item):
		buf = self.get_buffer()
		start_iter, end_iter = buf.get_selection_bounds()
		setClipboard(toStr(buf.get_text(start_iter, end_iter, True)))

	def copyAll(self, item):
		return setClipboard(toStr(self.get_text()))

	def findEventByY(self, y: int):
		lineIter, lineTop = self.get_line_at_y(y)
		lineOffset = lineIter.get_offset()
		# lineIter = self.textbuff.get_iter_at_line(lineNum)
		for lastEndOffset, occurData in reversed(self.occurOffsets):
			if lineOffset >= lastEndOffset:
				return occurData
		return None

	def trimEventMenuItemLabel(self, s: str):
		maxLen = self.eventMenuItemLabelMaxLen
		if len(s) > maxLen - 3:
			s = s[:maxLen - 3].rstrip(" ") + "..."
		return s

	def onButtonPress(self, widget, gevent):
		log.debug("DayOccurrenceView: onButtonPress: button={gevent.button}")
		if gevent.button != 3:
			return False
		menu = Menu()
		####
		occurData = self.findEventByY(gevent.y)
		if occurData is not None:
			self.addEventMenuItems(menu, occurData)
		####
		menu.add(ImageMenuItem(
			_("Copy _All"),
			imageName="edit-copy.svg",
			func=self.copyAll,
		))
		####
		itemCopy = ImageMenuItem(
			_("_Copy"),
			imageName="edit-copy.svg",
			func=self.copy,
		)
		if not self.has_selection():
			itemCopy.set_sensitive(False)
		menu.add(itemCopy)
		####
		self.addExtraMenuItems(menu)
		####
		menu.show_all()
		self.tmpMenu = menu
		menu.popup(
			None,
			None,
			None,
			None,
			3,
			gevent.time,
		)
		ui.updateFocusTime()
		return True

	def addText(self, text):
		endIter = self.textbuff.get_bounds()[1]

		text = text.replace("&", "&amp;")
		# Gtk-WARNING **: HH:MM:SS.sss: Invalid markup string: Error on line N:
		# Entity did not end with a semicolon; most likely you used an
		# ampersand character without intending to start an entity —
		# escape ampersand as &amp;

		b_text = text.encode("utf-8")
		self.textbuff.insert_markup(endIter, text, len(b_text))

	def addIcon(self, icon):
		"""
		insert_pixbuf is replaced with insert_texture in gtk 3.93.0

		commit 0b39631464bf2300d25bb9e112089c556dc08f42
		Author: Matthias Clasen <mclasen@redhat.com>
		Date:   Thu Nov 30 07:52:13 2017

			textview: Replace pixbufs by textures

			This affects a few apis, such as gtk_text_iter_get_pixbuf,
			gtk_text_buffer_insert_pixbuf and GtkTextBuffer::insert-pixbuf,
			which have all been replaced by texture equivalents.

			Update all callers.
		"""

		endIter = self.textbuff.get_bounds()[1]
		pixbuf = pixbufFromFile(
			icon,
			size=ui.rightPanelEventIconSize,
		)
		self.textbuff.insert_pixbuf(endIter, pixbuf)

	def addTime(self, timeStr):
		endIter = self.textbuff.get_bounds()[1]
		self.textbuff.insert_with_tags(endIter, timeStr, self.timeTag)

	def onDateChange(self, *a, **kw):
		CustomizableCalObj.onDateChange(self, *a, **kw)
		cell = ui.cell
		self.textbuff.set_text("")
		occurOffsets = []
		eventSep = self.getEventSep()
		for index, occurData in enumerate(cell.getEventsData()):
			lastEndOffset = self.textbuff.get_end_iter().get_offset()
			occurOffsets.append((lastEndOffset, occurData))
			if not occurData["show"][0]:
				continue
			if index > 0:
				self.addText(eventSep)
			# occurData["time"], occurData["text"], occurData["icon"]
			if occurData["icon"]:
				self.addIcon(occurData["icon"])
				self.addText(" ")
			if occurData["time"]:
				self.addTime(occurData["time"])
				self.addText(" ")
			text = (
				"".join(occurData["text"]) if self.showDesc
				else occurData["text"][0]
			)
			self.addText(text)
		self.occurOffsets = occurOffsets

	def moveEventToGroupFromMenu(self, item, event, prev_group, newGroup):
		prev_group.remove(event)
		prev_group.save()
		ui.eventUpdateQueue.put("r", prev_group, self)
		###
		newGroup.append(event)
		newGroup.save()
		###
		ui.eventUpdateQueue.put("v", event, self)
		###
		self.onConfigChange()

	def copyOccurToGroupFromMenu(
		self,
		item,
		newGroup,
		newEventType,
		event,
		occurData,
	):
		newEvent = newGroup.create(newEventType)
		newEvent.copyFrom(event)
		startEpoch, endEpoch = occurData["time_epoch"]
		newEvent.setStartEpoch(startEpoch)
		newEvent.setEnd("epoch", endEpoch)
		newEvent.afterModify()
		newEvent.save()
		###
		newGroup.append(newEvent)
		newGroup.save()
		ui.eventUpdateQueue.put("+", newEvent, self)
		###
		self.onConfigChange()

	def copyEventText(self, item, event):
		setClipboard(event.getText())

	def addWriteEventMenuItems(
		self,
		menu, occurData: Dict[str, Any],
		event: "Event",
		group: "EventGroup",
	):
		from scal3.ui_gtk.event.utils import menuItemFromEventGroup
		label = _("Edit") + ": " + self.trimEventMenuItemLabel(event.summary)
		winTitle = _("Edit") + ": " + event.summary
		menu.add(ImageMenuItem(
			label,
			imageName="document-edit.svg",
			func=self.onEditEventClick,
			args=(
				winTitle,
				event,
				group.id,
			),
		))
		###
		moveToItem = ImageMenuItem(
			_("Move to {title}").format(title="..."),
		)
		moveToMenu = Menu()
		disabledGroupsMenu = Menu()
		for newGroup in ui.eventGroups:
			if newGroup.id == group.id:
				continue
			if event.name not in newGroup.acceptsEventTypes:
				continue
			newGroupItem = menuItemFromEventGroup(newGroup)
			newGroupItem.connect(
				"activate",
				self.moveEventToGroupFromMenu,
				event,
				group,
				newGroup,
			)
			if newGroup.enable:
				moveToMenu.add(newGroupItem)
			else:
				disabledGroupsMenu.add(newGroupItem)

		###
		disabledGroupsItem = ImageMenuItem(label=_("Disabled"))
		disabledGroupsItem.set_submenu(disabledGroupsMenu)
		moveToMenu.add(disabledGroupsItem)
		###
		moveToItem.set_submenu(moveToMenu)
		menu.add(moveToItem)
		###
		if not event.isSingleOccur:
			newEventType = "allDayTask" if occurData["is_allday"] else "task"
			newEventTypeDesc = event_lib.classes.event.byName[newEventType].desc
			copyOccurItem = ImageMenuItem(
				label=_("Copy as {eventType} to...").format(
					eventType=newEventTypeDesc,
				),
			)
			copyOccurMenu = Menu()
			for newGroup in ui.eventGroups:
				if not newGroup.enable:
					continue
				if newEventType in newGroup.acceptsEventTypes:
					newGroupItem = menuItemFromEventGroup(newGroup)
					newGroupItem.connect(
						"activate",
						self.copyOccurToGroupFromMenu,
						newGroup,
						newEventType,
						event,
						occurData,
					)
					copyOccurMenu.add(newGroupItem)
			copyOccurItem.set_submenu(copyOccurMenu)
			menu.add(copyOccurItem)
			###
			menu.add(gtk.SeparatorMenuItem())
		###
		menu.add(ImageMenuItem(
			_("Move to {title}").format(title=ui.eventTrash.title),
			imageName=ui.eventTrash.getIconRel(),
			func=self.moveEventToTrash,
			args=(
				event,
				group.id,
			),
		))

	def addEventMenuItems(self, menu, occurData: Dict[str, Any]):
		if event_lib.allReadOnly:
			return
		####
		groupId, eventId = occurData["ids"]
		event = ui.getEvent(groupId, eventId)
		group = ui.eventGroups[groupId]
		####
		menu.add(ImageMenuItem(
			_("Copy Event Text"),
			imageName="edit-copy.svg",
			func=self.copyEventText,
			args=(event,),
		))
		####
		if not event.readOnly:
			menu.add(gtk.SeparatorMenuItem())
			self.addWriteEventMenuItems(menu, occurData, event, group)
			menu.add(gtk.SeparatorMenuItem())

	def onEditEventClick(self, item, winTitle, event, groupId):
		from scal3.ui_gtk.event.editor import EventEditorDialog
		event = EventEditorDialog(
			event,
			title=winTitle,
			transient_for=self.get_toplevel(),
		).run()
		if event is None:
			return
		ui.eventUpdateQueue.put("e", event, self)
		self.onConfigChange()

	def moveEventToTrash(self, item, event, groupId):
		from scal3.ui_gtk.event.utils import confirmEventTrash
		if not confirmEventTrash(event, transient_for=ui.mainWin):
			return
		ui.moveEventToTrash(ui.eventGroups[groupId], event, self)
		self.onConfigChange()

	def addExtraMenuItems(self, menu):
		pass


@registerSignals
class LimitedHeightDayOccurrenceView(gtk.ScrolledWindow, CustomizableCalObj):
	itemListCustomizable = False
	optionsPageSpacing = 20
	_name = DayOccurrenceView._name
	desc = DayOccurrenceView.desc

	def __init__(self, **kwargs):
		gtk.ScrolledWindow.__init__(self)
		self.set_policy(gtk.PolicyType.NEVER, gtk.PolicyType.AUTOMATIC)
		###
		self.initVars()
		###
		item = DayOccurrenceView(**kwargs)
		item.show()
		self._item = item
		self.add(item)
		self.appendItem(item)

	def onDateChange(self, *a, **kw):
		CustomizableCalObj.onDateChange(self, *a, **kw)
		self.showHide()

	def showHide(self):
		self.set_visible(self.enable and bool(ui.cell.getEventsData()))

	def do_get_preferred_height(self):
		height = ui.eventViewMaxHeight
		return height, height

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.pref_utils import SpinPrefItem
		if self.optionsWidget:
			return self.optionsWidget
		optionsWidget = self._item.getOptionsWidget()
		###
		prefItem = SpinPrefItem(
			ui,
			"eventViewMaxHeight",
			1, 9999,
			digits=1, step=1,
			label=_("Maximum Height"),
			live=True,
			onChangeFunc=self.onMaximumHeightChange,
		)
		pack(optionsWidget, prefItem.getWidget())
		###
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	def onMaximumHeightChange(self):
		self.queue_resize()
		ui.mainWin.autoResize()


class WeekOccurrenceView(gtk.TreeView):
	def updateData(self):
		return self.updateDataByGroups(ui.eventGroups)

	def __init__(self, abbreviateWeekDays=False):
		self.abbreviateWeekDays = abbreviateWeekDays
		self.absWeekNumber = core.getAbsWeekNumberFromJd(ui.cell.jd)## FIXME
		gtk.TreeView.__init__(self)
		self.set_headers_visible(False)
		self.ls = gtk.ListStore(
			GdkPixbuf.Pixbuf,  # icon
			str,  # weekDay
			str,  # time
			str,  # text
		)
		self.set_model(self.ls)
		###
		cell = gtk.CellRendererPixbuf()
		col = gtk.TreeViewColumn(title=_("Icon"), cell_renderer=cell)
		col.add_attribute(cell, "pixbuf", 0)
		self.append_column(col)
		###
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(
			title=_("Week Day"),
			cell_renderer=cell,
			text=1,
		)
		col.set_resizable(True)
		self.append_column(col)
		###
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(
			title=_("Time"),
			cell_renderer=cell,
			text=2,
		)
		col.set_resizable(True)## FIXME
		self.append_column(col)
		###
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(
			title=_("Description"),
			cell_renderer=cell,
			text=3,
		)
		col.set_resizable(True)
		self.append_column(col)

	def updateWidget(self):
		cells, wEventData = ui.cellCache.getWeekData(self.absWeekNumber)
		self.ls.clear()
		for item in wEventData:
			if not item["show"][1]:
				continue
			self.ls.append(
				pixbufFromFile(item["icon"]),
				core.getWeekDayAuto(item["weekDay"], abbreviate=self.abbreviateWeekDays),
				item["time"],
				item["text"],
			)


"""
class MonthOccurrenceView(gtk.TreeView, event_lib.MonthOccurrenceView):
	def updateData(self):
		return self.updateDataByGroups(ui.eventGroups)

	def __init__(self):
		event_lib.MonthOccurrenceView.__init__(self, ui.cell.jd)
		gtk.TreeView.__init__(self)
		self.set_headers_visible(False)
		self.ls = gtk.ListStore(
			GdkPixbuf.Pixbuf,  # icon
			str,  # day
			str,  # time
			str,  # text
		)
		self.set_model(self.ls)
		###
		cell = gtk.CellRendererPixbuf()
		col = gtk.TreeViewColumn(title="", cell_renderer=cell)
		col.add_attribute(cell, "pixbuf", 0)
		self.append_column(col)
		###
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title=_("Day"), cell_renderer=cell, text=1)
		col.set_resizable(True)
		self.append_column(col)
		###
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title=_("Time"), cell_renderer=cell, text=2)
		col.set_resizable(True)## FIXME
		self.append_column(col)
		###
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title=_("Description"), cell_renderer=cell, text=3)
		col.set_resizable(True)
		self.append_column(col)
	def updateWidget(self):
		self.updateData()
		self.ls.clear()## FIXME
		for item in self.data:
			if not item["show"][2]:
				continue
			self.ls.append(
				pixbufFromFile(item["icon"]),
				_(item["day"]),
				item["time"],
				item["text"],
			)
"""
