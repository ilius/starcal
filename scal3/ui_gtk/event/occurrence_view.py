#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.
from __future__ import annotations

from scal3 import logger

log = logger.get()

from typing import TYPE_CHECKING

from scal3 import event_lib, ui
from scal3.event_lib import ev
from scal3.event_lib.events import SingleStartEndEvent
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import Menu, gdk, gtk, pack
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.cal_obj_base import CustomizableCalObj
from scal3.ui_gtk.font_utils import gfontEncode
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk.utils import (
	buffer_get_text,
	pixbufFromFile,
	setClipboard,
)
from scal3.utils import toStr

if TYPE_CHECKING:
	from scal3.event_lib.occur_data import DayOccurData
	from scal3.event_lib.pytypes import EventGroupType, EventType
	from scal3.font import Font
	from scal3.option import Option
	from scal3.ui_gtk.option_ui import OptionUI

__all__ = ["DayOccurrenceView", "LimitedHeightDayOccurrenceView"]


class DayOccurrenceView(CustomizableCalObj):
	objName = "eventDayView"
	desc = _("Events of Day")
	itemListCustomizable = False

	def __init__(
		self,
		eventSepParam: Option[str] | None = None,
		justificationParam: Option[str] | None = None,
		fontEnableParam: Option[bool] | None = None,
		fontParam: Option[Font | None] | None = None,
		timeFontEnableParam: Option[bool] | None = None,
		timeFontParam: Option[Font | None] | None = None,
		styleClass: str = "",
		wrapMode: gtk.WrapMode = gtk.WrapMode.WORD_CHAR,
	) -> None:
		super().__init__()
		self.t = gtk.TextView()
		self.w: gtk.Widget = self.t
		self.t.set_editable(False)
		self.t.set_cursor_visible(False)
		self.t.set_wrap_mode(wrapMode)
		# ---
		self.styleClass = styleClass
		if styleClass:
			self.t.get_style_context().add_class(styleClass)
		# ---
		self.t.connect("button-press-event", self.onButtonPress)
		# ---
		self.textbuff = self.t.get_buffer()
		# Gtk.ScrolledWindow.add_with_viewport is Deprecated since version 3.8:
		# Gtk.Container.add() will automatically add a Gtk.Viewport if the
		# child doesn't implement Gtk.Scrollable.
		self.initVars()
		self.wrapMode = wrapMode
		self.showDesc = True
		# ---
		self.eventSepParam = eventSepParam
		self.justificationParam = justificationParam
		self.fontEnableParam = fontEnableParam
		self.fontParam = fontParam
		self.timeFontEnableParam = timeFontEnableParam
		self.timeFontParam = timeFontParam
		# ---
		if fontParam:
			if not styleClass:
				raise ValueError(f"{fontParam=}, {styleClass=}")
			ud.windowList.addCSSFunc(self.getCSS)
		# ---
		self.occurOffsets: list[tuple[int, DayOccurData]] = []
		self.eventMenuItemLabelMaxLen = 25
		self.updateJustification()
		# ---
		self.timeTag = gtk.TextTag.new("time")
		self.textbuff.get_tag_table().add(self.timeTag)
		self.updateTimeFont()

	def updateTimeFont(self) -> None:
		font = ui.getFont(bold=True)  # bold by default
		if self.timeFontParam:
			assert self.timeFontEnableParam
			if self.timeFontEnableParam.v and self.timeFontParam.v:
				font = self.timeFontParam.v
		self.timeTag.set_property("font", gfontEncode(font))

	def getEventSep(self) -> str:
		if self.eventSepParam:
			return self.eventSepParam.v
		return "\n\n"

	def updateJustification(self) -> None:
		if not self.justificationParam:
			return
		value = self.justificationParam.v
		self.t.set_justification(ud.justificationByName[value])

	def getOptionsWidget(self) -> gtk.Widget | None:
		from scal3.ui_gtk.option_ui import (
			CheckFontOptionUI,
			CheckOptionUI,
			FontOptionUI,
			JustificationOptionUI,
			TextOptionUI,
		)

		if self.optionsWidget:
			return self.optionsWidget
		optionsWidget = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=10)
		option: OptionUI
		# ---
		if self.justificationParam:
			option = JustificationOptionUI(
				option=self.justificationParam,
				label=_("Text Alignment"),
				onChangeFunc=self.updateJustification,
			)
			pack(optionsWidget, option.getWidget())
		# ---
		if self.fontParam:
			assert self.fontEnableParam
			option = CheckFontOptionUI(
				CheckOptionUI(option=self.fontEnableParam, label=_("Font")),
				FontOptionUI(option=self.fontParam),
				live=True,
				onChangeFunc=ud.windowList.updateCSS,
			)
			pack(optionsWidget, option.getWidget())
		if self.timeFontParam:
			assert self.timeFontEnableParam
			option = CheckFontOptionUI(
				CheckOptionUI(self.timeFontEnableParam, label=_("Time Font")),
				FontOptionUI(self.timeFontParam),
				live=True,
				onChangeFunc=self.updateTimeFont,
			)
			pack(optionsWidget, option.getWidget())
		# ---
		if self.eventSepParam:
			option = TextOptionUI(
				option=self.eventSepParam,
				label=_("Event Text Separator"),
				live=True,
				onChangeFunc=self.onEventSepChange,
			)
			pack(optionsWidget, option.getWidget())
		# ---
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	def getCSS(self) -> str:
		from scal3.ui_gtk.utils import cssTextStyle

		if not self.fontParam:
			return ""
		if self.fontEnableParam and not self.fontEnableParam.v:
			return ""
		font = self.fontParam.v
		if not font:
			return ""
		return "." + self.styleClass + " " + cssTextStyle(font=font)

	def onEventSepChange(self) -> None:
		self.broadcastDateChange()

	def has_selection(self) -> bool:
		buf = self.t.get_buffer()
		try:
			buf.get_selection_bounds()
		except ValueError:
			return False
		else:
			return True

	def get_text(self) -> str:
		return buffer_get_text(self.t.get_buffer())

	def copy(self, _w: gtk.Widget) -> None:
		buf = self.t.get_buffer()
		bounds = buf.get_selection_bounds()
		if not bounds:
			return
		start_iter, end_iter = bounds
		setClipboard(toStr(buf.get_text(start_iter, end_iter, True)))

	def copyAll(self, _w: gtk.Widget) -> None:
		setClipboard(toStr(self.get_text()))

	def findEventByY(self, y: int) -> DayOccurData | None:
		lineIter, _lineTop = self.t.get_line_at_y(y)
		lineOffset = lineIter.get_offset()
		# lineIter = self.textbuff.get_iter_at_line(lineNum)
		for lastEndOffset, occurData in reversed(self.occurOffsets):
			if lineOffset >= lastEndOffset:
				return occurData
		return None

	def trimEventMenuItemLabel(self, s: str) -> str:
		maxLen = self.eventMenuItemLabelMaxLen
		if len(s) > maxLen - 3:
			s = s[: maxLen - 3].rstrip(" ") + "..."
		return s

	def onButtonPress(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		# log.debug(f"DayOccurrenceView: onButtonPress: {gevent.button=}")
		if gevent.button != 3:
			return False
		menu = Menu()
		# ----
		occurData = self.findEventByY(int(gevent.y))
		if occurData is not None:
			self.addEventMenuItems(menu, occurData)
		# ----
		menu.add(
			ImageMenuItem(
				_("Copy _All"),
				imageName="edit-copy.svg",
				func=self.copyAll,
			),
		)
		# ----
		itemCopy = ImageMenuItem(
			_("_Copy"),
			imageName="edit-copy.svg",
			func=self.copy,
		)
		if not self.has_selection():
			itemCopy.set_sensitive(False)
		menu.add(itemCopy)
		# ----
		self.addExtraMenuItems(menu)
		# ----
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

	def addText(self, text: str) -> None:
		endIter = self.textbuff.get_bounds()[1]

		text = text.replace("&", "&amp;")
		text = text.replace(">", "&gt;")
		text = text.replace("<", "&lt;")
		# Gtk-WARNING **: HH:MM:SS.sss: Invalid markup string: Error on line N:
		# Entity did not end with a semicolon; most likely you used an
		# ampersand character without intending to start an entity —
		# escape ampersand as &amp;

		b_text = text.encode("utf-8")
		self.textbuff.insert_markup(endIter, text, len(b_text))

	def addIcon(self, icon: str) -> None:
		"""
		insert_pixbuf is replaced with insert_texture in gtk 3.93.0.

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
			size=conf.rightPanelEventIconSize.v,
		)
		assert pixbuf is not None
		self.textbuff.insert_pixbuf(endIter, pixbuf)

	def addTime(self, timeStr: str) -> None:
		endIter = self.textbuff.get_bounds()[1]
		self.textbuff.insert_with_tags(endIter, timeStr, self.timeTag)  # type: ignore[no-untyped-call]

	def onDateChange(self) -> None:
		super().onDateChange()
		cell = ui.cells.current
		self.textbuff.set_text("")
		occurOffsets = []
		eventSep = self.getEventSep()
		for index, occurData in enumerate(cell.getEventsData()):
			lastEndOffset = self.textbuff.get_end_iter().get_offset()
			occurOffsets.append((lastEndOffset, occurData))
			if not occurData.show[0]:
				continue
			if index > 0:
				self.addText(eventSep)
			# occurData.time, occurData.text, occurData.icon
			if occurData.icon:
				self.addIcon(occurData.icon)
				self.addText(" ")
			if occurData.time:
				self.addTime(occurData.time)
				self.addText(" ")
			text = "".join(occurData.text) if self.showDesc else occurData.text[0]
			for line in text.split("\n"):
				self.addText(line + "\n")
		self.occurOffsets = occurOffsets

	def moveEventToGroupFromMenu(
		self,
		_item: gtk.Widget,
		event: EventType,
		prev_group: EventGroupType,
		newGroup: EventGroupType,
	) -> None:
		prev_group.remove(event)
		prev_group.save()
		ui.eventUpdateQueue.put("r", prev_group, self)
		# ---
		newGroup.append(event)
		newGroup.save()
		# ---
		ui.eventUpdateQueue.put("v", event, self)
		# ---
		self.onConfigChange()

	def copyOccurToGroupFromMenu(
		self,
		_item: gtk.Widget,
		newGroup: EventGroupType,
		newEventType: str,
		event: EventType,
		occurData: DayOccurData,
	) -> None:
		newEvent = newGroup.create(newEventType)
		if not isinstance(newEvent, SingleStartEndEvent):
			# FIXME
			log.error(
				f"copyOccurToGroupFromMenu: unsupported event type {newEventType}",
			)
			return

		newEvent.copyFrom(event)
		startEpoch, endEpoch = occurData.time_epoch
		newEvent.setStartEpoch(startEpoch)
		newEvent.setEndEpoch(endEpoch)
		newEvent.afterModify()
		newEvent.save()
		# ---
		newGroup.append(newEvent)
		newGroup.save()
		ui.eventUpdateQueue.put("+", newEvent, self)
		# ---
		self.onConfigChange()

	@staticmethod
	def copyEventText(_item: gtk.Widget, event: EventType) -> None:
		setClipboard(event.getText())

	def addWriteEventMenuItems(
		self,
		menu: gtk.Menu,
		occurData: DayOccurData,
		event: EventType,
		group: EventGroupType,
	) -> None:
		from scal3.ui_gtk.event.utils import menuItemFromEventGroup

		label = _("Edit") + ": " + self.trimEventMenuItemLabel(event.summary)
		winTitle = _("Edit") + ": " + event.summary

		def editEvent(w: gtk.Widget) -> None:
			self.onEditEventClick(w, winTitle, event, group.mustId)

		menu.add(
			ImageMenuItem(
				label,
				imageName="document-edit.svg",
				func=editEvent,
			),
		)
		# ---
		moveToItem = ImageMenuItem(
			_("Move to {title}").format(title="..."),
		)
		moveToMenu = Menu()
		disabledGroupsMenu = Menu()
		for newGroup in ev.groups:
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

		# ---
		disabledGroupsItem = ImageMenuItem(label=_("Disabled"))
		disabledGroupsItem.set_submenu(disabledGroupsMenu)
		moveToMenu.add(disabledGroupsItem)
		# ---
		moveToItem.set_submenu(moveToMenu)
		menu.add(moveToItem)
		# ---
		if not event.isSingleOccur:
			newEventType = "allDayTask" if occurData.is_allday else "task"
			newEventTypeDesc = event_lib.classes.event.byName[newEventType].desc
			copyOccurItem = ImageMenuItem(
				label=_("Copy as {eventType} to...").format(
					eventType=newEventTypeDesc,
				),
			)
			copyOccurMenu = Menu()
			for newGroup in ev.groups:
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
			# ---
			menu.add(gtk.SeparatorMenuItem())
		# ---

		def moveToTrash(w: gtk.Widget) -> None:
			self.moveEventToTrash(w, event, group.mustId)

		menu.add(
			ImageMenuItem(
				_("Move to {title}").format(title=ev.trash.title),
				imageName=ev.trash.getIconRel(),
				func=moveToTrash,
			),
		)

	def addEventMenuItems(self, menu: gtk.Menu, occurData: DayOccurData) -> None:
		if ev.allReadOnly:
			return
		# ----
		groupId, eventId = occurData.ids
		event = ui.getEvent(groupId, eventId)
		group = ev.groups[groupId]
		# ----

		def copyEventText(w: gtk.Widget) -> None:
			self.copyEventText(w, event)

		menu.add(
			ImageMenuItem(
				_("Copy Event Text"),
				imageName="edit-copy.svg",
				func=copyEventText,
			),
		)
		# ----
		if not event.readOnly:
			menu.add(gtk.SeparatorMenuItem())
			self.addWriteEventMenuItems(menu, occurData, event, group)
			menu.add(gtk.SeparatorMenuItem())

	def onEditEventClick(
		self,
		_item: gtk.Widget,
		winTitle: str,
		event: EventType,
		_groupId: int,
	) -> None:
		from scal3.ui_gtk.event.editor import EventEditorDialog

		window = self.w.get_toplevel()
		assert isinstance(window, gtk.Window), f"{window=}"

		eventNew = EventEditorDialog(
			event,
			title=winTitle,
			transient_for=window,
		).run2()
		if eventNew is None:
			return
		ui.eventUpdateQueue.put("e", eventNew, self)
		self.onConfigChange()

	def moveEventToTrash(
		self,
		_item: gtk.Widget,
		event: EventType,
		groupId: int,
	) -> None:
		from scal3.ui_gtk.event.utils import confirmEventTrash

		if not confirmEventTrash(event, transient_for=ui.mainWin.win):
			return
		ui.moveEventToTrash(ev.groups[groupId], event, self)
		self.onConfigChange()

	def addExtraMenuItems(self, menu: gtk.Menu) -> None:
		pass


class LimitedHeightDayOccurrenceView(CustomizableCalObj):
	itemListCustomizable = False
	optionsPageSpacing = 20
	objName = DayOccurrenceView.objName
	desc = DayOccurrenceView.desc

	def __init__(
		self,
		eventSepParam: Option[str] | None = None,
	) -> None:
		super().__init__()
		self.swin = gtk.ScrolledWindow()
		self.w: gtk.Widget = self.swin
		self.swin.set_policy(gtk.PolicyType.NEVER, gtk.PolicyType.AUTOMATIC)
		# ---
		self.initVars()
		# ---
		item = DayOccurrenceView(eventSepParam=eventSepParam)
		item.show()
		self._item = item
		self.swin.add(item.w)
		self.appendItem(item)

	def onDateChange(self) -> None:
		super().onDateChange()
		self.showHide()

	def showHide(self) -> None:
		self.w.set_visible(self.enable and bool(ui.cells.current.getEventsData()))

	def do_get_preferred_height(self) -> tuple[int, int]:  # noqa: PLR6301
		height = conf.eventViewMaxHeight.v
		return height, height

	def getOptionsWidget(self) -> gtk.Widget | None:
		from scal3.ui_gtk.option_ui import IntSpinOptionUI

		if self.optionsWidget:
			return self.optionsWidget
		optionsWidget = self._item.getOptionsWidget()
		# assert optionsWidget is not None
		assert isinstance(optionsWidget, gtk.Box), f"{optionsWidget=}"
		# ---
		option = IntSpinOptionUI(
			option=conf.eventViewMaxHeight,
			bounds=(1, 9999),
			step=1,
			label=_("Maximum Height"),
			live=True,
			onChangeFunc=self.onMaximumHeightChange,
		)
		pack(optionsWidget, option.getWidget())
		# ---
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	def onMaximumHeightChange(self) -> None:
		self.w.queue_resize()
		assert ui.mainWin is not None
		ui.mainWin.autoResize()


#
# class WeekOccurrenceView(gtk.TreeView, CustomizableCalObj):
# 	# def updateData(self):
# 	# 	return self.updateDataByGroups(ev.groups)

# 	def __init__(self, abbreviateWeekDays: bool = False) -> None:
# 		self.initVars()
# 		self.abbreviateWeekDays = abbreviateWeekDays
# 		self.absWeekNumber = core.getAbsWeekNumberFromJd.v(ui.cells.current.jd)  # FIXME
# 		gtk.TreeView.__init__(self)
# 		self.set_headers_visible(False)
# 		self.ls = gtk.ListStore(
# 			GdkPixbuf.Pixbuf,  # icon
# 			str,  # weekDay
# 			str,  # time
# 			str,  # text
# 		)
# 		self.set_model(self.ls)
# 		# ---
# 		cell = gtk.CellRendererPixbuf()
# 		col = gtk.TreeViewColumn(title=_("Icon"), cell_renderer=cell)
# 		col.add_attribute(cell, "pixbuf", 0)
# 		self.append_column(col)
# 		# ---
# 		cell = gtk.CellRendererText()
# 		col = gtk.TreeViewColumn(
# 			title=_("Week Day"),
# 			cell_renderer=cell,
# 			text=1,
# 		)
# 		col.set_resizable(True)
# 		self.append_column(col)
# 		# ---
# 		cell = gtk.CellRendererText()
# 		col = gtk.TreeViewColumn(
# 			title=_("Time"),
# 			cell_renderer=cell,
# 			text=2,
# 		)
# 		col.set_resizable(True)  # FIXME
# 		self.append_column(col)
# 		# ---
# 		cell = gtk.CellRendererText()
# 		col = gtk.TreeViewColumn(
# 			title=_("Description"),
# 			cell_renderer=cell,
# 			text=3,
# 		)
# 		col.set_resizable(True)
# 		self.append_column(col)

# 	def getWeekData(
# 		self,
# 		absWeekNumber: int,
# 	) -> tuple[list[CellType], list[dict]]:
# 		from scal3.ui import eventGroups

# 		cellCache = ui.cells
# 		cell_list = cellCache.getCellGroup("WeekCal", absWeekNumber)
# 		wEventData = cellCache.weekEvents.get(absWeekNumber)
# 		if wEventData is None:
# 			wEventData = event_lib.getWeekOccurrenceData(
# 				absWeekNumber,
# 				eventGroups,
# 				tfmt=conf.eventWeekViewTimeFormat.v,
# 			)
# 			cellCache.weekEvents[absWeekNumber] = wEventData
# 			# log.info(f"weekEvents cache: {len(self.weekEvents)}")
# 		return cell_list, wEventData


# 	def onDateChange(self) -> None:
# 		super().onDateChange()
# 		self.absWeekNumber = ui.cells.current.absWeekNumber
# 		_cells, wEventData = self.getWeekData(self.absWeekNumber)
# 		self.ls.clear()
# 		for item in wEventData:
# 			if not item.show[1]:
# 				continue
# 			self.ls.append(
# 				[
# 					pixbufFromFile(item.icon),
# 					core.getWeekDayAuto(
# 						item.weekDay,
# 						abbreviate=self.abbreviateWeekDays,
# 					),
# 					item.time,
# 					item.text,
# 				],
# 			)


# class MonthOccurrenceView(gtk.TreeView, event_lib.MonthOccurrenceView):
# 	# def updateData(self):
# 	# 	return self.updateDataByGroups(ev.groups)

# 	def __init__(self):
# 		event_lib.MonthOccurrenceView.__init__(self, ui.cells.current.jd)
# 		gtk.TreeView.__init__(self)
# 		self.set_headers_visible(False)
# 		self.ls = gtk.ListStore(
# 			GdkPixbuf.Pixbuf,  # icon
# 			str,  # day
# 			str,  # time
# 			str,  # text
# 		)
# 		self.set_model(self.ls)
# 		# ---
# 		cell = gtk.CellRendererPixbuf()
# 		col = gtk.TreeViewColumn(title="", cell_renderer=cell)
# 		col.add_attribute(cell, "pixbuf", 0)
# 		self.append_column(col)
# 		# ---
# 		cell = gtk.CellRendererText()
# 		col = gtk.TreeViewColumn(title=_("Day"), cell_renderer=cell, text=1)
# 		col.set_resizable(True)
# 		self.append_column(col)
# 		# ---
# 		cell = gtk.CellRendererText()
# 		col = gtk.TreeViewColumn(title=_("Time"), cell_renderer=cell, text=2)
# 		col.set_resizable(True)-- FIXME
# 		self.append_column(col)
# 		# ---
# 		cell = gtk.CellRendererText()
# 		col = gtk.TreeViewColumn(title=_("Description"), cell_renderer=cell, text=3)
# 		col.set_resizable(True)
# 		self.append_column(col)
# 	def updateWidget(self):
# 		self.updateData()
# 		self.ls.clear()-- FIXME
# 		for item in self.data:
# 			if not item.show[2]:
# 				continue
# 			self.ls.append(
# 				pixbufFromFile(item.icon]),
# 				_(item.day),
# 				item.time,
# 				item.text,
# 			)
