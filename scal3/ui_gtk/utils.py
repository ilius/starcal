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

from time import time as now
import os
from os.path import join, isabs
from subprocess import Popen

from scal3.utils import myRaise
from scal3.utils import toBytes, toStr
from scal3.json_utils import *
from scal3.path import pixDir, rootDir
from scal3.cal_types import calTypes
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from gi.repository.GObject import timeout_add
from gi.repository import GdkPixbuf

from scal3.ui_gtk import *


def hideList(widgets):
	for w in widgets:
		w.hide()


def showList(widgets):
	for w in widgets:
		w.show()


def set_tooltip(widget, text):
	widget.set_tooltip_text(text)


def buffer_get_text(b):
	return b.get_text(
		b.get_start_iter(),
		b.get_end_iter(),
		True,
	)


def setClipboard(text, clipboard=None):
	if not clipboard:
		clipboard = gtk.Clipboard.get(gdk.SELECTION_CLIPBOARD)
	clipboard.set_text(
		toStr(text),
		len(toBytes(text)),
	)
	#clipboard.store() ## ?????? No need!


def imageFromFile(path):## the file must exist
	if not isabs(path):
		path = join(pixDir, path)
	im = gtk.Image()
	try:
		im.set_from_file(path)
	except:
		myRaise()
	return im


def pixbufFromFile(path):## the file may not exist
	if not path:
		return None
	if not isabs(path):
		path = join(pixDir, path)
	try:
		return GdkPixbuf.Pixbuf.new_from_file(path)
	except:
		myRaise()
		return None


def toolButtonFromStock(stock, size):
	tb = gtk.ToolButton()
	tb.set_icon_widget(gtk.Image.new_from_stock(stock, size))
	return tb


def toolButtonFromFile(fname):
	tb = gtk.ToolButton()
	tb.set_icon_widget(imageFromFile(fname))
	return tb


def labelStockMenuItem(label, stock=None, func=None, *args):
	item = ImageMenuItem(_(label))
	item.set_use_underline(True)
	if stock:
		item.set_image(gtk.Image.new_from_stock(stock, gtk.IconSize.MENU))
	if func:
		item.connect('activate', func, *args)
	return item


def labelImageMenuItem(label, image, func=None, *args):
	item = ImageMenuItem(_(label))
	item.set_use_underline(True)
	item.set_image(imageFromFile(image))
	if func:
		item.connect('activate', func, *args)
	return item


def labelMenuItem(label, func=None, *args):
	item = MenuItem(_(label))
	if func:
		item.connect('activate', func, *args)
	return item


def getStyleColor(widget, state=gtk.StateType.NORMAL):
	return widget.get_style_context().get_color(state)


def modify_bg_all(widget, state, gcolor):
	print(widget.__class__.__name__)
	widget.modify_bg(state, gcolor)
	try:
		children = widget.get_children()
	except AttributeError:
		pass
	else:
		for child in children:
			modify_bg_all(child, state, gcolor)


def rectangleContainsPoint(r, x, y):
	return (
		r.x <= x < r.x + r.width and
		r.y <= y < r.y + r.height
	)


def dialog_add_button(dialog, stock, label, resId, onClicked=None, tooltip=''):
	b = dialog.add_button(stock, resId)
	if ui.autoLocale:
		if label:
			b.set_label(label)
		b.set_image(gtk.Image.new_from_stock(stock, gtk.IconSize.BUTTON))
	if onClicked:
		b.connect('clicked', onClicked)
	if tooltip:
		set_tooltip(b, tooltip)
	return b


def confirm(msg, parent=None):
	win = gtk.MessageDialog(
		parent=parent,
		flags=0,
		type=gtk.MessageType.INFO,
		buttons=gtk.ButtonsType.NONE,
		message_format=msg,
	)
	dialog_add_button(
		win,
		gtk.STOCK_CANCEL,
		_('_Cancel'),
		gtk.ResponseType.CANCEL,
	)
	dialog_add_button(
		win,
		gtk.STOCK_OK,
		_('_OK'),
		gtk.ResponseType.OK,
	)
	ok = win.run() == gtk.ResponseType.OK
	win.destroy()
	return ok


def showMsg(msg, parent, msg_type):
	win = gtk.MessageDialog(
		parent=parent,
		flags=0,
		type=msg_type,
		buttons=gtk.ButtonsType.NONE,
		message_format=msg,
	)
	dialog_add_button(
		win,
		gtk.STOCK_CLOSE,
		_('_Close'),
		gtk.ResponseType.OK,
	)
	win.run()
	win.destroy()


def showError(msg, parent=None):
	showMsg(msg, parent, gtk.MessageType.ERROR)


def showInfo(msg, parent=None):
	showMsg(msg, parent, gtk.MessageType.INFO)


def openWindow(win):
	win.set_keep_above(ui.winKeepAbove)
	win.present()


def get_menu_width(menu):
	'''
	#print(menu.has_screen())
	#menu.show_all()
	#menu.realize()
	print(
		menu.get_border_width(),
		max_item_width,
		menu.get_allocation().width,
		menu.size_request().width,
		menu.get_size_request()[0],
		menu.get_preferred_width(),
		#menu.do_get_preferred_width(),
		menu.get_preferred_size()[0].width,
		menu.get_preferred_size()[1].width,
		)
	'''
	w = menu.get_allocation().width
	if w > 1:
		#print(w-max(item.size_request().width for item in menu.get_children()))
		return w
	items = menu.get_children()
	if items:
		mw = max(item.size_request().width for item in items)
		return mw + 56 ## FIXME
	return 0


def get_pixbuf_hash(pbuf):
    import hashlib
    md5 = hashlib.md5()

    def save_func(chunkBytes, size, unknown):
        # len(chunkBytes) == size
        md5.update(chunkBytes)
        return True

    pbuf.save_to_callbackv(
        save_func,
        None,  # user_data
        'bmp',  # type, name of file format
        [],  # option_keys
        [],  # option_values
    )
    return md5.hexdigest()


def window_set_size_aspect(win, min_aspect, max_aspect=None):
    if max_aspect is None:
        max_aspect = min_aspect
    geom = gdk.Geometry()
    geom.min_aspect = min_aspect
    geom.max_aspect = max_aspect
    win.set_geometry_hints(
        None,  # widget, ignored since Gtk 3.20
        geom,  # geometry
        gdk.WindowHints.ASPECT,  # geom_mask
    )
    win.resize(1, 1)


class IdComboBox(gtk.ComboBox):
	def set_active(self, _id):
		ls = self.get_model()
		for i in range(len(ls)):
			if ls[i][0] == _id:
				gtk.ComboBox.set_active(self, i)
				return

	def get_active(self):
		i = gtk.ComboBox.get_active(self)
		if i is None:
			return
		try:
			return self.get_model()[i][0]
		except IndexError:
			return


class CopyLabelMenuItem(MenuItem):
	def __init__(self, label):
		MenuItem.__init__(self)
		self.set_label(label)
		self.connect('activate', self.on_activate)

	def on_activate(self, item):
		setClipboard(self.get_property('label'))


if __name__ == '__main__':
	diolog = gtk.Dialog(parent=None)
	w = TimeZoneComboBoxEntry()
	pack(diolog.vbox, w)
	diolog.vbox.show_all()
	diolog.run()
