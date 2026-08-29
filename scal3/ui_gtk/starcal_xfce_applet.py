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

"""
Status-icon backend for the Xfce panel applet.

Instead of showing a tray/status icon, the rendered icon and tooltip are
written to files that the Xfce panel plugin watches, and click events are
received over a Unix socket. See the ``xfce-applet/`` directory for the panel
plugin itself.

The icon is saved the same way the AppIndicator backend does: the dynamic
pixbuf is written to a hash-named PNG file (a new file when it changes) so
the panel plugin reliably picks up updates.
"""

from __future__ import annotations

import os
import shlex
import socket
import sys
import threading
from os.path import join
from typing import TYPE_CHECKING

from gi.repository import GLib

from scal3 import logger
from scal3.cal_types import calTypes
from scal3.path import APP_NAME, confDir
from scal3.ui_gtk.starcal_funcs import copyDate
from scal3.ui_gtk.utils import get_pixbuf_hash

if TYPE_CHECKING:
	from gi.repository import GdkPixbuf

	from scal3.ui_gtk.starcal_types import MainWinType

log = logger.get()

__all__ = ["XfceAppletStatusIcon"]

APPLET_DIR_NAME = "xfce-applet"
ICON_FILE_PREFIX = f"{APP_NAME}-indicator-"
TOOLTIP_FILE_NAME = "tooltip.txt"
SOCKET_FILE_NAME = "applet.sock"
LAUNCH_COMMAND_FILE_NAME = "launch-command"


class XfceAppletStatusIcon:
	imNamePrefix = f"{ICON_FILE_PREFIX}{os.getuid()}-"

	def __init__(self, mainWin: MainWinType) -> None:
		self.mainWin = mainWin
		self.dir = os.environ.get("STARCAL_XFCE_APPLET_DIR") or join(
			confDir,
			APPLET_DIR_NAME,
		)
		os.makedirs(self.dir, exist_ok=True)
		self.imPath: str | None = None
		self._lastTooltip: str | None = None
		self.tooltipPath = join(self.dir, TOOLTIP_FILE_NAME)
		self.sockPath = join(self.dir, SOCKET_FILE_NAME)
		self._server: socket.socket | None = None
		self._thread: threading.Thread | None = None
		self._running = True
		self._writeLaunchCommand()
		self._startServer()

	def _writeLaunchCommand(self) -> None:
		"""
		Remember how this starcal instance was launched so the panel
		applet can start it again when it is not running.
		"""
		if not sys.argv:
			return
		script = os.path.abspath(sys.argv[0])
		if os.access(script, os.X_OK):
			cmd = [script]
		else:
			cmd = [sys.executable, script]
		try:
			with open(
				join(self.dir, LAUNCH_COMMAND_FILE_NAME),
				"w",
				encoding="utf-8",
			) as fp:
				fp.write(shlex.join(cmd) + "\n")
		except Exception:
			log.exception("failed to write xfce applet launch command")

	def _startServer(self) -> None:
		try:
			os.unlink(self.sockPath)
		except FileNotFoundError:
			pass
		server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		try:
			server.bind(self.sockPath)
		except OSError:
			log.exception(f"failed to bind xfce applet socket {self.sockPath}")
			server.close()
			return
		server.listen(4)
		self._server = server
		self._thread = threading.Thread(target=self._serveLoop, daemon=True)
		self._thread.start()

	def _serveLoop(self) -> None:
		server = self._server
		if server is None:
			return
		while self._running:
			try:
				conn, _addr = server.accept()
			except OSError:
				break
			try:
				data = conn.recv(4096)
			finally:
				conn.close()
			if not data:
				continue
			for line in data.decode("utf-8", "replace").splitlines():
				cmd = line.strip()
				if cmd:
					GLib.idle_add(self._handleCommand, cmd)

	def _handleCommand(self, cmd: str) -> None:
		mainWin = self.mainWin
		try:
			if cmd == "left-click":
				mainWin.onStatusIconClick()
			elif cmd == "middle-click":
				copyDate(calTypes.primary)
			elif cmd == "popup":
				mainWin.statusIconPopupAtPointer()
			else:
				log.warning(f"unknown xfce applet command {cmd!r}")
		except Exception:
			log.exception(f"error handling xfce applet command {cmd!r}")

	def _setCurrentIcon(self, fpath: str) -> None:
		old = self.imPath
		self.imPath = fpath
		if old is not None and old != fpath:
			try:
				os.remove(old)
			except OSError:
				pass

	def set_from_file(self, fpath: str) -> None:
		from scal3.ui_gtk import GdkPixbuf

		try:
			pbuf = GdkPixbuf.Pixbuf.new_from_file(fpath)
		except Exception:
			log.exception(f"failed to load xfce applet icon {fpath}")
			return
		if pbuf is None:
			log.error(f"failed to load xfce applet icon {fpath}")
			return
		self.set_from_pixbuf(pbuf)

	def set_from_pixbuf(self, pbuf: GdkPixbuf.Pixbuf) -> None:
		fname = self.imNamePrefix + get_pixbuf_hash(pbuf) + ".png"
		fpath = join(self.dir, fname)
		tmpPath = fpath + ".tmp"
		pbuf.savev(tmpPath, "png", [], [])
		os.replace(tmpPath, fpath)
		self._setCurrentIcon(fpath)

	def set_tooltip_text(self, text: str) -> None:
		if text == self._lastTooltip:
			return
		self._lastTooltip = text
		tmpPath = self.tooltipPath + ".tmp"
		with open(tmpPath, "w", encoding="utf-8") as fp:
			fp.write(text)
		os.replace(tmpPath, self.tooltipPath)

	def is_embedded(self) -> bool:  # noqa: PLR6301
		return True

	def set_visible(self, visible: bool) -> None:
		if not visible:
			self.cleanup()

	def cleanup(self) -> None:
		self._running = False
		if self._server is not None:
			try:
				self._server.close()
			except OSError:
				pass
			self._server = None
			self._thread = None
		try:
			os.unlink(self.sockPath)
		except OSError:
			pass
		try:
			entries = os.listdir(self.dir)
		except OSError:
			return
		for fname in entries:
			if fname.startswith(self.imNamePrefix):
				try:
					os.remove(join(self.dir, fname))
				except OSError:
					pass
