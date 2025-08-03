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

import typing
from os.path import isabs, join

from scal3.locale_man import tr as _
from scal3.path import pixDir, svgDir
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.option_ui.base import OptionUI
from scal3.ui_gtk.utils import dialog_add_button

if typing.TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.option import Option

__all__ = ["IconChooserOptionUI", "ImageFileChooserOptionUI"]


class FileChooserOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		option: Option[str],
		title: str = "Select File",
		currentFolder: str = "",
	) -> None:
		self.option = option
		# ---
		dialog = gtk.FileChooserDialog(
			title=title,
			action=gtk.FileChooserAction.OPEN,
		)
		dialog_add_button(
			dialog,
			res=gtk.ResponseType.CANCEL,
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
		)
		dialog_add_button(
			dialog,
			res=gtk.ResponseType.OK,
			imageName="dialog-ok.svg",
			label=_("_Choose"),
		)
		w = gtk.FileChooserButton.new_with_dialog(dialog)
		w.set_local_only(True)
		if currentFolder:
			w.set_current_folder(currentFolder)
		# ---
		dialog_add_button(
			dialog,
			res=gtk.ResponseType.NONE,
			imageName="edit-undo.svg",
			label=_("_Revert"),
			onClick=self.onRevertClick,
		)
		# ---
		self._widget = w
		self._fcb = w

	def get(self) -> str:
		return self._fcb.get_filename() or ""

	def set(self, value: str) -> None:
		self._fcb.set_filename(value)

	def onRevertClick(self, _w: gtk.Widget) -> None:
		defaultValue = self.option.default()
		self.option.v = defaultValue
		self.set(defaultValue)


class ImageFileChooserOptionUI(FileChooserOptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		option: Option[str],
		title: str = "Select File",
		currentFolder: str = "",
	) -> None:
		FileChooserOptionUI.__init__(
			self,
			option=option,
			title=title,
			currentFolder=currentFolder,
		)
		self._preview = gtk.Image()
		self._widget.set_preview_widget(self._preview)
		self._widget.set_preview_widget_active(True)
		self._widget.connect("update-preview", self._updatePreview)

	def _updatePreview(self, _w: gtk.Widget) -> None:
		fpath = self._widget.get_preview_filename()
		self._preview.set_from_file(fpath)


class IconChooserOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		option: Option[str],
		label: str = "",
		live: bool = False,
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		from scal3.ui_gtk.mywidgets.icon import IconSelectButton

		self.option = option
		self._onChangeFunc = onChangeFunc
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		if label:
			pack(hbox, gtk.Label(label=label + "  "))
		self.iconSelect = IconSelectButton()
		pack(hbox, self.iconSelect)
		pack(hbox, gtk.Label(), 1, 1)
		self._widget = hbox
		# ---
		if live:
			self.updateWidget()
			self.iconSelect.connect("changed", self.onIconChanged)
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")

	def get(self) -> str:
		return self.iconSelect.get_filename().removeprefix(join(pixDir, ""))

	def set(self, iconPath: str) -> None:
		if not isabs(iconPath):
			if iconPath.endswith(".svg"):
				iconPath = join(svgDir, iconPath)
			else:
				iconPath = join(pixDir, iconPath)
		self.iconSelect.set_filename(iconPath)

	def onIconChanged(self, _w: gtk.Widget, iconPath: str) -> None:
		if not iconPath:
			self.updateWidget()
		self.updateVar()
		if self._onChangeFunc is not None:
			self._onChangeFunc()
