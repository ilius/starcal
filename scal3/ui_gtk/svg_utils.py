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

from os.path import isabs, join

from scal3.path import svgDir
from scal3.ui_gtk import GdkPixbuf, GLibError, gtk

__all__ = ["pixbufFromSvgFile"]


def pixbufFromSvgFile(path: str, size: int) -> GdkPixbuf.Pixbuf:
	if size <= 0:
		raise ValueError(f"invalid {size=} for svg file {path}")
	if not isabs(path):
		path = join(svgDir, path)
	with open(path, "rb") as fp:
		data = fp.read()
	loader = GdkPixbuf.PixbufLoader.new_with_type("svg")
	loader.set_size(size, size)
	try:
		loader.write(data)
	finally:
		try:
			loader.close()
		except GLibError:
			log.exception("")
	return loader.get_pixbuf()


def imageFromSvgFile(path: str, size: int) -> gtk.Image:
	return gtk.Image.new_from_pixbuf(pixbufFromSvgFile(path, size))
