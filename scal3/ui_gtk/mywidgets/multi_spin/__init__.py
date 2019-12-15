#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/lgpl.txt>.
# Also avalable in /usr/share/common-licenses/LGPL on Debian systems
# or /usr/share/licenses/common/LGPL/license.txt on ArchLinux

from scal3 import logger
log = logger.get()

import sys
import os
from time import localtime
from time import time as now

from scal3.utils import toStr
from scal3.cal_types import to_jd, jd_to
from scal3 import locale_man
from scal3.locale_man import tr as _
from scal3.locale_man import rtl
from scal3.mywidgets.multi_spin import * ## FIXME
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.utils import imageClassButton
from scal3.ui_gtk.drawing import calcTextPixelWidth


class AutoSizeEntry(gtk.Entry):
	def __init__(self, *args, maxChars=0, **kwargs):
		gtk.Entry.__init__(self, *args, **kwargs)
		self.set_width_chars(maxChars)
		###
		self.maxChars = maxChars
		self.maxPixelWidth = 0
		###
		self.connect("changed", self.onChange)

	def do_get_preferred_width(self):
		# must return minimum_size, natural_size
		text = self.get_text()
		text = " " + text + " "
		pixelWidth = calcTextPixelWidth(self, text)
		pixelWidth += 6
		# log.debug(f"{self.__class__.__name__}: text={text}, pixelWidth={pixelWidth}, max={self.maxChars}")
		if pixelWidth < self.maxPixelWidth:
			pixelWidth = self.maxPixelWidth
		else:
			self.maxPixelWidth = pixelWidth
		return pixelWidth, pixelWidth

	def onChange(self, entry):
		self.queue_resize()


@registerSignals
class MultiSpinButton(gtk.Box):
	signals = [
		("changed", []),
		("activate", []),
		("first-min", []),
		("first-max", []),
	]

	buttonSize = gtk.IconSize.MENU # FIXME

	def set_width_chars(self, w: int):
		self.entry.set_width_chars(w)

	def get_text(self) -> str:
		return self.entry.get_text()

	def set_text(self, text: str) -> None:
		self.entry.set_text(text)

	def set_editable(self, editable: bool) -> None:
		self.entry.set_editable(editable)

	def get_selection_bounds(self):
		return self.entry.get_selection_bounds()

	def get_increments(self) -> "Tuple[int, int]":
		return (self.step_inc, self.page_inc)

	# def set_range(self, _min: int, _max: int):
	# 	self.field.children[0].setRange(_min, _max)
	# 	self.set_text(self.field.getText())

	def __init__(
		self,
		sep=None,
		fields=None,
		arrow_select=True,
		step_inc=1,
		page_inc=10,
	):
		if sep is None:
			raise ValueError("MultiSpinButton: sep is None")
		if fields is None:
			raise ValueError("MultiSpinButton: fields is None")
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		##
		sep = toStr(sep)
		self.field = ContainerField(sep, *fields)
		self.entry = AutoSizeEntry(maxChars=self.field.getMaxWidth())
		##
		self.step_inc = step_inc
		self.page_inc = page_inc
		##
		# 0 = IconSize.INVALID
		# 1 = IconSize.MENU
		# 2 = IconSize.SMALL_TOOLBAR
		# 3 = IconSize.LARGE_TOOLBAR
		# 4 = IconSize.BUTTON
		# 5 = IconSize.DND
		# 6 = IconSize.DIALOG
		###
		# in Gtk's sourc code, icon names are "value-decrease-symbolic" and
		# "value-increase-symbolic" but I can not find these icons
		# (and my Gtk does not either)
		# instead "list-remove-symbolic" and "list-add-symbolic" used in this
		# patch, work perfectly
		# https://gitlab.gnome.org/GNOME/gtk/commit/5fd936beef7a999828e5e3625506ea6708188762
		###
		self.down_button = imageClassButton("list-remove-symbolic", "down", self.buttonSize)
		self.down_button.connect("button-press-event", self.onDownButtonPress)
		self.down_button.connect("button-release-event", self.onButtonRelease)
		###
		self.up_button = imageClassButton("list-add-symbolic", "up", self.buttonSize)
		self.up_button.connect("button-press-event", self.onUpButtonPress)
		self.up_button.connect("button-release-event", self.onButtonRelease)
		###
		pack(self, self.entry, expand=True, fill=True)
		pack(self, self.down_button)
		pack(self, self.up_button)
		####
		# priv->down_button = gtk_button_new ();
		# gtk_container_add (GTK_CONTAINER (priv->down_button),
		# 		gtk_image_new_from_icon_name ("value-decrease-symbolic"));
		# gtk_style_context_add_class (gtk_widget_get_style_context
		#		(priv->down_button), "image-button");
		# gtk_widget_set_can_focus (priv->down_button, FALSE);
		# gtk_style_context_add_class (gtk_widget_get_style_context
		# 		(priv->down_button), "down");
		# gtk_container_add (GTK_CONTAINER (priv->box), priv->down_button);

		# gesture = gtk_gesture_multi_press_new ();
		# gtk_gesture_single_set_button (GTK_GESTURE_SINGLE (gesture), 0);
		# gtk_gesture_single_set_touch_only (GTK_GESTURE_SINGLE (gesture), FALSE);
		# gtk_event_controller_set_propagation_phase (GTK_EVENT_CONTROLLER (gesture),
		# 											GTK_PHASE_CAPTURE);
		# g_signal_connect (gesture, "pressed",
		#		G_CALLBACK (button_pressed_cb), spin_button);
		# g_signal_connect (gesture, "released",
		# 		G_CALLBACK (button_released_cb), spin_button);
		# gtk_widget_add_controller (GTK_WIDGET (priv->down_button),
		# 		GTK_EVENT_CONTROLLER (gesture));
		####
		self.arrow_select = arrow_select
		self.entry.set_editable(True)
		###
		self.digs = locale_man.getDigits()
		###
		####
		self.entry.set_direction(gtk.TextDirection.LTR)
		# log.debug(self.__class__.__name__, "value=", value)
		self.entry.connect("changed", self._entry_changed)
		#self.connect("activate", lambda obj: self.update())
		self.entry.connect("activate", self._entry_activate)
		for widget in (self, self.entry, self.down_button, self.up_button):
			widget.connect("key-press-event", self.onKeyPress)
		self.entry.connect("scroll-event", self._scroll)
		# self.connect("button-press-event", self.onButtonPress) # FIXME
		# self.connect("button-release-event", self.onButtonRelease) # FIXME
		####
		#self.select_region(0, 0)

	def _entry_changed(self, widget):
		self.emit("changed")

	def _entry_activate(self, widget):
		# log.debug("_entry_activate", self.entry.get_text())
		self.update()
		# log.debug(self.entry.get_text())
		self.emit("activate")
		return True

	def get_value(self):
		self.field.setText(self.entry.get_text())
		return self.field.getValue()

	def set_value(self, value):
		pos = self.entry.get_position()
		self.field.setValue(value)
		self.entry.set_text(self.field.getText())
		self.entry.set_position(pos)

	def update(self):
		pos = self.entry.get_position()
		self.field.setText(toStr(self.entry.get_text()))
		self.entry.set_text(self.field.getText())
		self.entry.set_position(pos)

	def insertText(self, s, clearSeceltion=True):
		selection = self.get_selection_bounds()
		if selection and clearSeceltion:
			start, end = selection
			text = toStr(self.entry.get_text())
			text = text[:start] + s + text[end:]
			self.entry.set_text(text)
			self.entry.set_position(start + len(s))
		else:
			pos = self.entry.get_position()
			self.entry.insert_text(s, pos)
			self.entry.set_position(pos + len(s))

	def entry_plus(self, p):
		self.update()
		pos = self.entry.get_position()
		self.field.getFieldAt(
			toStr(self.entry.get_text()),
			self.entry.get_position()
		).plus(p)
		self.entry.set_text(self.field.getText())
		self.entry.set_position(pos)

	def onKeyPress(self, widget, gevent):
		kval = gevent.keyval
		kname = gdk.keyval_name(kval).lower()
		size = len(self.field)
		sep = self.field.sep
		step_inc = self.step_inc
		page_inc = self.page_inc
		if kname in (
			"up",
			"down",
			"page_up",
			"page_down",
			"left",
			"right",
		):
			if not self.entry.get_editable():
				return True
			if kname in ("left", "right"):
				return False
				#if not self.arrow_select:
				#	return False
				#shift = {
				#	"left": -1,
				#	"right": 1
				#}[kname]
				#FIXME
			else:
				p = {
					"up": step_inc,
					"down": -step_inc,
					"page_up": page_inc,
					"page_down": -page_inc,
				}[kname]
				self.entry_plus(p)
			#from scal3.utils import strFindNth
			#if fieldIndex==0:
			#	i1 = 0
			#else:
			#	i1 = strFindNth(text, sep, fieldIndex) + len(sep)
			#i2 = strFindNth(text, sep, fieldIndex+1)
			##self.grab_focus()
			#self.select_region(i1, i2)
			return True
		#elif kname=="return":## Enter
		#	self.update()
		#	##self.emit("activate")
		#	return True
		elif ord("0") <= kval <= ord("9"):
			self.insertText(self.digs[kval - ord("0")])
			return True
		elif "kp_0" <= kname <= "kp_9":
			self.insertText(self.digs[int(kname[-1])])
			return True
		elif kname in (
			"period", "kp_decimal",
		):
			self.insertText(locale_man.getNumSep())
			return True
		else:
			# log.debug(kname, kval)
			return False

	def onDownButtonPress(self, button, gevent):
		self._arrow_press(-self.step_inc)

	def onUpButtonPress(self, button, gevent):
		self._arrow_press(self.step_inc)

	def _scroll(self, widget, gevent):
		d = getScrollValue(gevent)
		if d in ("up", "down"):
			if not self.entry.has_focus():
				self.entry.grab_focus()
			if self.entry.get_editable():
				plus = (1 if d == "up" else -1) * self.step_inc
				self.entry_plus(plus)
		else:
			return False
		return True

	#def _move_cursor(self, obj, step, count, extend_selection):
	#	# force_select
	#	log.debug(f"_move_cursor: count={count}, extend_selection={extend_selection}")

	def _arrow_press(self, plus):
		self.pressTm = now()
		self._remain = True
		timeout_add(ui.timeout_initial, self._arrow_remain, plus)
		self.entry_plus(plus)

	def _arrow_remain(self, plus):
		if (
			self.entry.get_editable()
			and
			self._remain
			and
			now() - self.pressTm >= ui.timeout_repeat / 1000
		):
			self.entry_plus(plus)
			timeout_add(
				ui.timeout_repeat,
				self._arrow_remain,
				plus,
			)

	def onButtonRelease(self, widget, gevent):
		self._remain = False

	"""## ????????????????????????????????
	def _arrow_enter_notify(self, gtkWin):
		if gtkWin!=None:
			log.info("_arrow_enter_notify")
			gtkWin.set_background(gdk.Color(65535, 0, 0))
			gtkWin.show()
	def _arrow_leave_notify(self, gtkWin):
		if gtkWin!=None:
			log.info("_arrow_leave_notify")
			gtkWin.set_background(gdk.Color(65535, 65535, 65535))
	#"""


class SingleSpinButton(MultiSpinButton):
	def __init__(self, field=None, **kwargs):
		if field is None:
			raise ValueError("SingleSpinButton: field is None")
		MultiSpinButton.__init__(
			self,
			sep=" ",
			fields=(field,),
			**kwargs
		)
		# if isinstance(field, NumField):
		# 	gtk.SpinButton.set_range(self, field._min, field._max)

	# def set_range(self, _min, _max): FIXME
	# 	gtk.SpinButton.set_range(self, _min, _max)

	def get_value(self):
		return MultiSpinButton.get_value(self)[0]
