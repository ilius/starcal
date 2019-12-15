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

from os.path import join, isabs

from scal3.path import pixDir, svgDir, sourceDir

from scal3.ui_gtk import *

def pixbufFromSvgFile(path: str, size: int):
	if size <= 0:
		raise ValueError(f"invalid size={size} for svg file {path}")
	if not isabs(path):
		path = join(svgDir, path)
	with open(path, "rb") as fp:
		data = fp.read()
	loader = GdkPixbuf.PixbufLoader.new_with_type("svg")
	loader.set_size(size, size)
	try:
		loader.write(data)
	finally:
		loader.close()
	pixbuf = loader.get_pixbuf()
	return pixbuf


def imageFromSvgFile(path: str, size: int):
	return gtk.Image.new_from_pixbuf(pixbufFromSvgFile(path, size))
