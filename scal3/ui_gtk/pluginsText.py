from __future__ import annotations

from scal3 import logger
from scal3.ui import conf

log = logger.get()

from typing import TYPE_CHECKING

from scal3 import ui
from scal3.locale_man import tr as _
from scal3.ui_gtk import Menu, gtk, pack
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.cal_obj_base import CustomizableCalObj
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk.mywidgets.expander import ExpanderFrame
from scal3.ui_gtk.utils import (
	buffer_get_text,
	openWindow,
	setClipboard,
)
from scal3.utils import findWordByPos, toStr

if TYPE_CHECKING:
	from scal3.font import Font
	from scal3.option import Option
	from scal3.pytypes import PluginType
	from scal3.ui_gtk import gdk
	from scal3.ui_gtk.option_ui.base import OptionUI

__all__ = ["PluginsTextBox"]


class PluginsTextView(CustomizableCalObj):
	itemListCustomizable = False

	def __init__(self) -> None:
		super().__init__()
		self.t = gtk.TextView()
		self.w: gtk.Widget = self.t
		self.t.set_editable(False)
		self.t.set_cursor_visible(False)
		self.t.connect("button-press-event", self.onButtonPress)
		self.occurOffsets: list[tuple[int, tuple[PluginType, str]]] = []
		self.initVars()

	def copyAll(self, _item: gtk.Widget) -> None:
		setClipboard(toStr(self.get_text()))

	# def cursorIsOnURL(self):
	# 	return False

	def get_text(self) -> str:
		return buffer_get_text(self.t.get_buffer())

	def has_selection(self) -> bool:
		buf = self.t.get_buffer()
		try:
			buf.get_selection_bounds()
		except ValueError:
			return False
		else:
			return True

	def copy(self, _item: gtk.Widget) -> None:
		buf = self.t.get_buffer()
		bounds = buf.get_selection_bounds()
		if not bounds:
			return
		start_iter, end_iter = bounds
		setClipboard(toStr(buf.get_text(start_iter, end_iter, True)))

	@classmethod
	def copyText(cls, _item: gtk.MenuItem, text: str) -> None:
		setClipboard(text)

	def onDateChange(self) -> None:
		super().onDateChange()
		textbuff = self.t.get_buffer()
		textbuff.set_text("")
		occurOffsets = []
		eventSep = "\n"
		text: str
		for index, occurData in enumerate(ui.cells.current.getPluginsData()):
			_plug, text = occurData
			lastEndOffset = textbuff.get_end_iter().get_offset()
			occurOffsets.append((lastEndOffset, occurData))
			if index > 0:
				self.addText(eventSep)
			self.addText(text)
		self.occurOffsets = occurOffsets

	def findPluginByY(self, y: int) -> tuple[PluginType, str] | None:
		lineIter, _lineTop = self.t.get_line_at_y(y)
		lineOffset = lineIter.get_offset()
		# lineIter = self.get_buffer().get_iter_at_line(lineNum)
		for lastEndOffset, occurData in reversed(self.occurOffsets):
			if lineOffset >= lastEndOffset:
				return occurData
		return None

	def addPluginMenuItems(
		self,
		menu: gtk.Menu,
		occurData: tuple[PluginType, str],
	) -> None:
		plug, text = occurData
		# print(f"addPluginMenuItems, title={plug.title}, file={plug.file}")
		# ----

		def copyText(_w: gtk.Widget) -> None:
			setClipboard(text)

		def configure(_w: gtk.Widget) -> None:
			self.onPlugConfClick(plug)

		def about(_w: gtk.Widget) -> None:
			self.onPlugAboutClick(plug)

		menu.add(
			ImageMenuItem(
				_("Copy Event Text"),  # FIXME: "Event" is a bit misleading
				imageName="edit-copy.svg",
				onActivate=copyText,
			),
		)
		# ----
		item = ImageMenuItem(
			_("C_onfigure Plugin"),
			imageName="preferences-system.svg",
			onActivate=configure,
		)
		item.set_sensitive(plug.hasConfig)
		menu.add(item)
		# ----
		item = ImageMenuItem(
			_("_About Plugin"),
			imageName="dialog-information.svg",
			onActivate=about,
		)
		item.set_sensitive(bool(plug.about))
		menu.add(item)
		# ----
		menu.add(gtk.SeparatorMenuItem())

	def addExtraMenuItems(self, menu: gtk.Menu) -> None:
		pass

	def onPlugConfClick(self, plug: PluginType) -> None:
		if not plug.hasConfig:
			return
		plug.open_configure()
		self.broadcastConfigChange()

	def onPlugAboutClick(self, plug: PluginType) -> None:
		from scal3.ui_gtk.about import AboutDialog

		if hasattr(plug, "open_about"):
			plug.open_about()
			return
		if plug.about is None:
			return
		about = AboutDialog(
			# name="",  # FIXME
			title=_("About Plugin"),  # _("About ") + plug.title
			authors=plug.authors,
			comments=plug.about,
		)
		about.set_transient_for(self.w.get_toplevel())  # type: ignore[arg-type]
		about.connect("delete-event", lambda w, _e: w.destroy())
		about.connect("response", lambda w, _e: w.destroy())
		# about.set_resizable(True)
		# about.vbox.show_all()  # OR about.vbox.show_all() ; about.run()
		openWindow(about)  # FIXME

	def addText(self, text: str) -> None:
		textbuff = self.t.get_buffer()
		endIter = textbuff.get_bounds()[1]

		text = text.replace("&", "&amp;")
		text = text.replace(">", "&gt;")
		text = text.replace("<", "&lt;")
		# Gtk-WARNING **: HH:MM:SS.sss: Invalid markup string: Error on line N:
		# Entity did not end with a semicolon; most likely you used an
		# ampersand character without intending to start an entity —
		# escape ampersand as &amp;

		b_text = text.encode("utf-8")
		textbuff.insert_markup(endIter, text, len(b_text))

	def onButtonPress(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		if gevent.button != 3:
			return False
		# ----
		iter_ = None
		buf_x, buf_y = self.t.window_to_buffer_coords(
			gtk.TextWindowType.TEXT,
			int(gevent.x),
			int(gevent.y),
		)
		text = self.get_text()
		word = ""
		if buf_x is not None and buf_y is not None:
			# overText, iter_, trailing = ...
			iter_ = self.t.get_iter_at_position(buf_x, buf_y)[1]
			pos = iter_.get_offset()
			word = findWordByPos(text, pos)[0]
		# ----
		menu = Menu()
		# ----
		occurData = self.findPluginByY(int(gevent.y))
		if occurData is not None:
			self.addPluginMenuItems(menu, occurData)
		# ----
		menu.add(
			ImageMenuItem(
				_("Copy _All"),
				imageName="edit-copy.svg",
				onActivate=self.copyAll,
			),
		)
		# ----
		itemCopy = ImageMenuItem(
			_("_Copy"),
			imageName="edit-copy.svg",
			onActivate=self.copy,
		)
		if not self.has_selection():
			itemCopy.set_sensitive(False)
		menu.add(itemCopy)
		# ----
		if "://" in word:

			def copyWord(_w: gtk.Widget) -> None:
				setClipboard(word)

			menu.add(
				ImageMenuItem(
					_("Copy _URL"),
					imageName="edit-copy.svg",
					onActivate=copyWord,
				),
			)
		# ----
		self.addExtraMenuItems(menu)
		# ---
		menu.show_all()
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


class PluginsTextBox(CustomizableCalObj):
	objName = "pluginsText"
	desc = _("Plugins Text")
	itemListCustomizable = False
	optionsPageSpacing = 20

	def __init__(
		self,
		hideIfEmpty: bool = True,
		tabToNewline: bool = False,
		insideExpanderParam: Option[bool] | None = None,
		justificationParam: Option[str] | None = None,
		fontEnableParam: Option[bool] | None = None,
		fontParam: Option[Font | None] | None = None,
		styleClass: str = "",
	) -> None:
		super().__init__()
		self.box = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		self.w: gtk.Widget = self.box
		self.initVars()
		# ----
		self.styleClass = styleClass
		if styleClass:
			self.w.get_style_context().add_class(styleClass)
		# ----
		self.w.connect("button-press-event", self.onButtonPress)
		# ----
		self.hideIfEmpty = hideIfEmpty
		self.tabToNewline = tabToNewline
		# ----
		self.textview = PluginsTextView()
		self.textview.t.set_wrap_mode(gtk.WrapMode.WORD)
		self.textbuff = self.textview.t.get_buffer()
		# ---
		self.insideExpanderParam = insideExpanderParam
		self.justificationParam = justificationParam
		self.fontEnableParam = fontEnableParam
		self.fontParam = fontParam
		# ---
		if fontEnableParam:
			if not styleClass:
				raise ValueError(f"{fontEnableParam=}, {fontParam=}, {styleClass=}")
			ud.windowList.addCSSFunc(self.getCSS)
		# ---
		if justificationParam:
			self.updateJustification()
		else:
			self.textview.t.set_justification(gtk.Justification.CENTER)
		# ---
		self.appendItem(self.textview)
		# ---
		if insideExpanderParam:
			self.expander = ExpanderFrame(label=self.desc)
			self.expander.connect("activate", self.expanderExpanded)
			self.expanderEnable = insideExpanderParam.v
			if self.expanderEnable:
				self.textview.show()
				self.expander.add(self.textview.w)
				pack(self.box, self.expander)
				self.expander.set_expanded(conf.pluginsTextIsExpanded.v)
			else:
				pack(self.box, self.textview.w, 1, 1)
		else:
			pack(self.box, self.textview.w, 1, 1)

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

	def updateJustification(self) -> None:
		if not self.justificationParam:
			return
		value = self.justificationParam.v
		self.textview.t.set_justification(ud.justificationByName[value])

	@staticmethod
	def onButtonPress(_widget: gtk.Widget, _ge: gdk.EventButton) -> bool:
		# log.debug("PluginsText: onButtonPress")
		# without this, it will switch to begin_move_drag on button-press
		return True

	def getOptionsWidget(self) -> gtk.Widget | None:
		from scal3.ui_gtk.option_ui.check import CheckOptionUI
		from scal3.ui_gtk.option_ui.check_mix import CheckFontOptionUI
		from scal3.ui_gtk.option_ui.font import FontOptionUI
		from scal3.ui_gtk.option_ui.justification import JustificationOptionUI

		if self.optionsWidget:
			return self.optionsWidget
		optionsWidget = gtk.Box(
			orientation=gtk.Orientation.VERTICAL,
			spacing=20,
		)
		option: OptionUI
		# ----
		if self.insideExpanderParam:
			option = CheckOptionUI(
				option=self.insideExpanderParam,
				label=_("Inside Expander"),
				live=True,
				onChangeFunc=self.onInsideExpanderCheckClick,
			)
			pack(optionsWidget, option.getWidget())
		# ----
		if self.justificationParam:
			option = JustificationOptionUI(
				option=self.justificationParam,
				label=_("Text Alignment"),
				onChangeFunc=self.updateJustification,
			)
			pack(optionsWidget, option.getWidget())
		# ----
		if self.fontParam:
			assert self.fontEnableParam
			option = CheckFontOptionUI(
				CheckOptionUI(option=self.fontEnableParam, label=_("Font")),
				FontOptionUI(option=self.fontParam),
				live=True,
				onChangeFunc=ud.windowList.updateCSS,
			)
			pack(optionsWidget, option.getWidget())
		# ----
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	def onInsideExpanderCheckClick(self) -> None:
		assert self.insideExpanderParam is not None
		enable = self.insideExpanderParam.v
		prevEnable = self.expanderEnable
		self.expanderEnable = enable
		if enable:
			if not prevEnable:
				self.box.remove(self.textview.w)
				self.expander.add(self.textview.w)
				pack(self.box, self.expander)
				self.expander.show_all()
		elif prevEnable:
			self.expander.remove(self.textview.w)
			self.box.remove(self.expander)
			pack(self.box, self.textview.w)
			self.textview.show()
		self.broadcastDateChange()

	@staticmethod
	def expanderExpanded(exp: gtk.Expander) -> None:
		conf.pluginsTextIsExpanded.v = not exp.get_expanded()
		ui.saveLiveConf()

	def getWidget(self) -> gtk.Widget:
		return self.expander if self.expanderEnable else self.textview.w

	def setText(self, text: str) -> None:
		if self.tabToNewline:
			text = text.replace("\t", "\n")
		self.textbuff.set_text(text)
		if self.hideIfEmpty:
			if text:
				self.getWidget().show()
			else:
				self.getWidget().hide()

	def onDateChange(self) -> None:
		pluginsText = ui.cells.current.getPluginsText()
		log.debug(f"PluginsText.onDateChange: {pluginsText}")
		super().onDateChange()
		self.setText(pluginsText)
