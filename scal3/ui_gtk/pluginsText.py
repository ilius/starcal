#!/usr/bin/env python3

from scal3 import logger
log = logger.get()

from typing import Tuple

from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.expander import ExpanderFrame
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.customize import CustomizableCalObj


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
		from scal3.ui_gtk.mywidgets.text_widgets import ReadOnlyTextView
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
		self.textview = ReadOnlyTextView()
		self.textview.set_wrap_mode(gtk.WrapMode.WORD)
		self.textbuff = self.textview.get_buffer()
		###
		self.insideExpanderParam = insideExpanderParam
		self.justificationParam = justificationParam
		self.fontParams = fontParams
		###
		if fontParams:
			if not styleClass:
				raise ValueError(f"fontParams={fontParams}, styleClass={styleClass}")
			ud.windowList.addCSSFunc(self.getCSS)
		###
		if justificationParam:
			self.updateJustification()
		else:
			self.textview.set_justification(gtk.Justification.CENTER)
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
