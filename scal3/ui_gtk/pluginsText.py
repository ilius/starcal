#!/usr/bin/env python3

from scal3 import logger
log = logger.get()

from typing import Tuple

from scal3 import core
from scal3.locale_man import tr as _
from scal3.utils import toStr, findWordByPos
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.expander import ExpanderFrame
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.utils import (
	setClipboard,
	buffer_get_text,
	openWindow,
)
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk.customize import CustomizableCalObj


@registerSignals
class PluginsTextView(gtk.TextView, CustomizableCalObj):
	def __init__(self, *args, **kwargs):
		gtk.TextView.__init__(self, *args, **kwargs)
		self.set_editable(False)
		self.set_cursor_visible(False)
		self.connect("button-press-event", self.onButtonPress)
		self.occurOffsets = []
		self.initVars()

	def copyAll(self, item):
		return setClipboard(toStr(self.get_text()))

	def cursorIsOnURL(self):
		return False

	def get_text(self):
		return buffer_get_text(self.get_buffer())

	def get_cursor_position(self):
		return self.get_buffer().get_property("cursor-position")

	def has_selection(self):
		buf = self.get_buffer()
		try:
			start_iter, end_iter = buf.get_selection_bounds()
		except ValueError:
			return False
		else:
			return True

	def copy(self, item):
		buf = self.get_buffer()
		start_iter, end_iter = buf.get_selection_bounds()
		setClipboard(toStr(buf.get_text(start_iter, end_iter, True)))

	def copyWordByIter(self, item, _iter):
		text = self.get_text()
		buf = self.get_buffer()
		pos = _iter.get_offset()
		word = findWordByPos(text, pos)[0]
		setClipboard(word)

	def copyText(self, item, text):
		setClipboard(text)

	def onDateChange(self, *a, **kw):
		CustomizableCalObj.onDateChange(self, *a, **kw)
		cell = ui.cell
		textbuff = self.get_buffer()
		textbuff.set_text("")
		occurOffsets = []
		eventSep = "\n"
		for index, occurData in enumerate(cell.getPluginsData()):
			plug, text = occurData
			lastEndOffset = textbuff.get_end_iter().get_offset()
			occurOffsets.append((lastEndOffset, occurData))
			if index > 0:
				self.addText(eventSep)
			self.addText(text)
		self.occurOffsets = occurOffsets

	def findPluginByY(self, y: int):
		lineIter, lineTop = self.get_line_at_y(y)
		lineOffset = lineIter.get_offset()
		# lineIter = self.get_buffer().get_iter_at_line(lineNum)
		for lastEndOffset, occurData in reversed(self.occurOffsets):
			if lineOffset >= lastEndOffset:
				return occurData
		return None

	def addPluginMenuItems(self, menu, occurData):
		plug, text = occurData
		# print(f"addPluginMenuItems, title={plug.title}, file={plug.file}")
		####
		menu.add(ImageMenuItem(
			_("Copy Event Text"),  # FIXME: "Event" is a bit misleading
			imageName="edit-copy.svg",
			func=self.copyTextFromMenu,
			args=(text,),
		))
		####
		item = ImageMenuItem(
			_("C_onfigure Plugin"),
			imageName="preferences-system.svg",
			func=self.onPlugConfClick,
			args=(plug,),
		)
		item.set_sensitive(plug.hasConfig)
		menu.add(item)
		####
		item = ImageMenuItem(
			_("_About Plugin"),
			imageName="dialog-information.svg",
			func=self.onPlugAboutClick,
			args=(plug,),
		)
		item.set_sensitive(bool(plug.about))
		menu.add(item)
		####
		menu.add(gtk.SeparatorMenuItem())

	def addExtraMenuItems(self, menu):
		pass

	def onPlugConfClick(self, item, plug):
		if not plug.hasConfig:
			return
		plug.open_configure()
		ud.windowList.onConfigChange()

	def onPlugAboutClick(self, item, plug):
		from scal3.ui_gtk.about import AboutDialog
		if hasattr(plug, "open_about"):
			return plug.open_about()
		if plug.about is None:
			return
		about = AboutDialog(
			# name="",  # FIXME
			title=_("About Plugin"),  # _("About ") + plug.title
			authors=plug.authors,
			comments=plug.about,
		)
		about.set_transient_for(self.get_toplevel())
		about.connect("delete-event", lambda w, e: w.destroy())
		about.connect("response", lambda w, e: w.destroy())
		# about.set_resizable(True)
		# about.vbox.show_all()  # OR about.vbox.show_all() ; about.run()
		openWindow(about)  # FIXME

	def copyTextFromMenu(self, item, text):
		setClipboard(text)

	def addText(self, text):
		textbuff = self.get_buffer()
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

	def onButtonPress(self, widget, gevent):
		if gevent.button != 3:
			return False
		####
		_iter = None
		buf_x, buf_y = self.window_to_buffer_coords(
			gtk.TextWindowType.TEXT,
			gevent.x,
			gevent.y,
		)
		if buf_x is not None and buf_y is not None:
			# overText, _iter, trailing = ...
			_iter = self.get_iter_at_position(buf_x, buf_y)[1]
		####
		text = self.get_text()
		buf = self.get_buffer()
		pos = _iter.get_offset()
		word = findWordByPos(text, pos)[0]
		####
		menu = Menu()
		####
		occurData = self.findPluginByY(gevent.y)
		if occurData is not None:
			self.addPluginMenuItems(menu, occurData)
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
		if "://" in word:
			menu.add(ImageMenuItem(
				_("Copy _URL"),
				imageName="edit-copy.svg",
				func=self.copyText,
				args=(word,)
			))
		####
		self.addExtraMenuItems(menu)
		###
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



@registerSignals
class PluginsTextBox(gtk.Box, CustomizableCalObj):
	_name = "pluginsText"
	desc = _("Plugins Text")
	itemListCustomizable = False
	optionsPageSpacing = 20

	def __init__(
		self,
		hideIfEmpty=True,
		tabToNewline=False,
		insideExpanderParam="",
		justificationParam="",
		fontParams: Tuple[str, str] = None,
		styleClass: str = "",
	):
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.initVars()
		####
		self.styleClass = styleClass
		if styleClass:
			self.get_style_context().add_class(styleClass)
		####
		self.connect("button-press-event", self.onButtonPress)
		####
		self.hideIfEmpty = hideIfEmpty
		self.tabToNewline = tabToNewline
		####
		self.textview = PluginsTextView()
		self.textview.set_wrap_mode(gtk.WrapMode.WORD)
		self.textbuff = self.textview.get_buffer()
		###
		self.insideExpanderParam = insideExpanderParam
		self.justificationParam = justificationParam
		self.fontParams = fontParams
		###
		if fontParams:
			if not styleClass:
				raise ValueError(f"{fontParams=}, {styleClass=}")
			ud.windowList.addCSSFunc(self.getCSS)
		###
		if justificationParam:
			self.updateJustification()
		else:
			self.textview.set_justification(gtk.Justification.CENTER)
		###
		self.appendItem(self.textview)
		###
		if insideExpanderParam:
			self.expander = ExpanderFrame(label=self.desc)
			self.expander.connect("activate", self.expanderExpanded)
			self.expanderEnable = getattr(ui, insideExpanderParam)
			if self.expanderEnable:
				self.textview.show()
				self.expander.add(self.textview)
				pack(self, self.expander)
				self.expander.set_expanded(ui.pluginsTextIsExpanded)
			else:
				pack(self, self.textview, 1, 1)
		else:
			pack(self, self.textview, 1, 1)

	def getCSS(self) -> str:
		from scal3.ui_gtk.utils import cssTextStyle
		enableParam, fontParam = self.fontParams
		if not getattr(ui, enableParam):
			return ""
		font = getattr(ui, fontParam)
		if not font:
			return ""
		return "." + self.styleClass + " " + cssTextStyle(font=font)

	def updateJustification(self):
		if not self.justificationParam:
			return
		value = getattr(ui, self.justificationParam)
		self.textview.set_justification(ud.justificationByName[value])

	def onButtonPress(self, widget, gevent):
		# log.debug("PluginsText: onButtonPress")
		# without this, it will switch to begin_move_drag on button-press
		return True

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.pref_utils import (
			CheckPrefItem,
			JustificationPrefItem,
			FontPrefItem,
			CheckFontPrefItem,
		)
		if self.optionsWidget:
			return self.optionsWidget
		optionsWidget = VBox(spacing=20)
		####
		if self.insideExpanderParam:
			prefItem = CheckPrefItem(
				ui,
				self.insideExpanderParam,
				_("Inside Expander"),
				live=True,
				onChangeFunc=self.onInsideExpanderCheckClick,
			)
			pack(optionsWidget, prefItem.getWidget())
		####
		if self.justificationParam:
			prefItem = JustificationPrefItem(
				ui,
				self.justificationParam,
				label=_("Text Alignment"),
				onChangeFunc=self.updateJustification,
			)
			pack(optionsWidget, prefItem.getWidget())
		####
		if self.fontParams:
			enableParam, fontParam = self.fontParams
			prefItem = CheckFontPrefItem(
				CheckPrefItem(ui, enableParam, label=_("Font")),
				FontPrefItem(ui, fontParam),
				live=True,
				onChangeFunc=ud.windowList.updateCSS,
			)
			pack(optionsWidget, prefItem.getWidget())
		####
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	def onInsideExpanderCheckClick(self):
		enable = getattr(ui, self.insideExpanderParam)
		prevEnable = self.expanderEnable
		self.expanderEnable = enable
		if enable:
			if not prevEnable:
				self.remove(self.textview)
				self.expander.add(self.textview)
				pack(self, self.expander)
				self.expander.show_all()
		else:
			if prevEnable:
				self.expander.remove(self.textview)
				self.remove(self.expander)
				pack(self, self.textview)
				self.textview.show()
		self.onDateChange()

	def expanderExpanded(self, exp):
		ui.pluginsTextIsExpanded = not exp.get_expanded()
		ui.saveLiveConf()

	def getWidget(self):
		return (
			self.expander if self.expanderEnable
			else self.textview
		)

	def setText(self, text):
		if self.tabToNewline:
			text = text.replace("\t", "\n")
		self.textbuff.set_text(text)
		if self.hideIfEmpty:
			if text:
				self.getWidget().show()
			else:
				self.getWidget().hide()


	def onDateChange(self, *a, **kw):
		pluginsText = ui.cell.getPluginsText()
		log.debug(f"PluginsText.onDateChange: {pluginsText}")
		CustomizableCalObj.onDateChange(self, *a, **kw)
		self.setText(pluginsText)
