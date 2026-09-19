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

from scal3.ui_gtk import gtk
from scal3.ui_gtk.timeline.window import TimeLineWindow

__all__ = ["TimeLineWindow"]


if __name__ == "__main__":
	win = TimeLineWindow(None)
	# win.tline.timeWidth = 100 * minYearLenSec  # 2 * 10**17
	# win.tline.timeStart = now() - win.tline.timeWidth  # -10**17
	win.show()
	gtk.main()
