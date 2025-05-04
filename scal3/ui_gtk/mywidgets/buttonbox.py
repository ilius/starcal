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

from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk
from scal3.ui_gtk.utils import (
	labelImageButton,
	set_tooltip,
)

__all__ = ["MyHButtonBox"]


class MyHButtonBox(gtk.Box):
	def __init__(self) -> None:
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.set_spacing(15)
		self.set_border_width(15)
		self._homogeneous = True
		self._sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)

	def set_homogeneous(self, homogeneous: bool) -> None:
		self._homogeneous = homogeneous

	def add(self, child) -> None:
		self.pack_start(child, expand=False, fill=False, padding=0)
		if self._homogeneous:
			self._sizeGroup.add_widget(child)

	def add_button(
		self,
		imageName="",
		label="",
		onClick=None,
		tooltip="",
	):
		if imageName:
			b = labelImageButton(
				label=label,
				imageName=imageName,
			)
		else:
			b = gtk.Button()
			b.set_label(label)
		if onClick:
			b.connect("clicked", onClick)
		if tooltip:
			set_tooltip(b, tooltip)
		self.add(b)
		return b

	def add_ok(self, onClick=None):
		return self.add_button(
			imageName="dialog-ok.svg",
			label=_("_Confirm"),
			onClick=onClick,
		)

	def add_cancel(self, onClick=None):
		return self.add_button(
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
			onClick=onClick,
		)
