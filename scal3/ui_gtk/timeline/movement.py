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

from time import perf_counter
from typing import TYPE_CHECKING

from scal3.timeline import conf
from scal3.ui_gtk import main_context_default, source_remove, timeout_add

if TYPE_CHECKING:
	from gi.repository.GLib import Source

	from scal3.ui_gtk.timeline.widget import TimeLine

__all__ = ["MovementHelper"]


class MovementHelper:
	"""Timeline view movement and animation physics."""

	def __init__(self, tline: TimeLine) -> None:
		self.tline = tline
		self.movingLastPress = 0.0
		self.movingV = 0.0
		self.movingF = 0.0
		self.animTimerSource: Source | None = None

	def movingUserEvent(
		self,
		direction: int = 1,
		smallForce: bool = False,
		source: str = "keyboard",
	) -> None:
		"""Source in ("keyboard", "scroll", "button")."""
		if conf.enableAnimation.v:
			tm = perf_counter()
			# dtEvent = tm - self.movingLastPress
			self.movingLastPress = tm
			"""
				We should call a new updateMovingAnim if:
					last key press has bin timeout, OR
					force direction has been change, OR
					its currently still (no speed and no force)
			"""
			if (
				self.movingF * direction < 0 or self.movingF * self.movingV == 0
				# or dtEvent > conf.movingKeyTimeout.v
			):
				if source == "scroll":
					force = conf.movingHandForceMouse.v
					if smallForce:
						force = (force + conf.movingFrictionForce.v) / 2.0
				elif source == "keyboard":
					if smallForce:
						force = conf.movingHandForceKeyboardSmall.v
					else:
						force = conf.movingHandForceKeyboard.v
				elif source == "button":
					force = conf.movingHandForceButton.v
				else:
					raise ValueError(f"invalid {source=}")
				self.movingF = direction * force
				self.movingV += conf.movingInitialVelocity.v * direction
				self.stopAnimTimers()
				self.updateMovingAnim(
					self.movingF,
					tm,
					tm,
					self.movingV,
					self.movingF,
				)
		else:
			self.tline.setTimeStart(
				self.tline.getTimeStart()
				+ direction
				* (
					conf.movingStaticStepMouse.v
					if source == "mouse"
					else conf.movingStaticStepKeyboard.v
				)
				* self.tline.getTimeWidth()
				/ self.tline.getWidgetWidth()
			)

	def stopAnimTimers(self) -> None:
		if self.animTimerSource is None:
			return
		if not self.animTimerSource.is_destroyed():
			source_remove(self.animTimerSource.get_id())
		self.animTimerSource = None
		# .is_destroyed() is checked to get rid of this warning:
		# Warning: Source ID {id} was not found when attempting to remove it

	def startAnimConstantAccel(self, direction: int, force: float) -> None:
		if self.movingV != 0:
			self.stopAnimTimers()
		self.movingF = direction * force
		if self.movingV == 0:
			self.movingV = conf.movingInitialVelocity.v * direction
		tm = perf_counter()
		self.updateMovingAnim(
			self.movingF,  # f1
			tm,  # t0
			tm,  # t1
			self.movingV,  # v0
			force - conf.movingFrictionForce.v,  # a1
			holdForce=True,
		)

	def updateMovingAnim(
		self,
		f1: float,  # force
		t0: float,  # perf_counter time
		t1: float,  # perf_counter time
		v0: float,  # speed
		a1: float,  # acceleration
		holdForce: bool = False,
	) -> None:
		# log.debug(f"updateMovingAnim: {f1=:.1f}, {v0=:.1f}, {a1=:.1f}")
		t2 = perf_counter()
		f = self.movingF
		if not holdForce and f != f1:
			# log.debug("Stopping movement: f != f1")
			return
		v1 = self.movingV
		if f == v1 == 0:
			return
		timeout = (
			conf.movingKeyTimeoutFirst.v
			if t2 - t0 < conf.movingKeyTimeoutFirst.v
			else conf.movingKeyTimeout.v
		)
		if not holdForce and f != 0 and t2 - self.movingLastPress >= timeout:
			# Stopping
			# log.debug("Stopping force")
			f = self.movingF = 0
		if v1 > 0:
			a2 = f - conf.movingFrictionForce.v
		elif v1 < 0:
			a2 = f + conf.movingFrictionForce.v
		else:
			a2 = f
		if a2 != a1:
			return self.updateMovingAnim(
				f,
				t2,
				t2,
				v1,
				a2,
				holdForce=holdForce,
			)
		v2 = v0 + a2 * (t2 - t0)
		if v2 > conf.movingMaxVelocity.v:
			v2 = conf.movingMaxVelocity.v
		elif v2 < -conf.movingMaxVelocity.v:
			v2 = -conf.movingMaxVelocity.v
		if f == 0 and v1 * v2 <= 0:
			# log.debug("Stopping movement: f == 0 and v1 * v2 <= 0")
			self.movingV = 0
			return
		source_id = timeout_add(
			conf.movingUpdateTime.v,
			self.updateMovingAnim,
			f,
			t0,
			t2,
			v0,
			a2,
			holdForce,
		)
		self.animTimerSource = main_context_default().find_source_by_id(source_id)
		self.movingV = v2
		self.tline.setTimeStart(
			self.tline.getTimeStart()
			+ v2 * (t2 - t1) * self.tline.getTimeWidth() / self.tline.getWidgetWidth()
		)
		self.tline.queueDraw()
		return

	def stopMovingAnim(self) -> None:
		# stop moving immudiatly
		self.movingF = 0
		self.movingV = 0

	def arrowButtonReleased(self) -> None:
		self.movingF = 0
		# ^ this will only make it stop slowly (by friction force)
		# if you want it to stop movement, set: self.movingV = 0
		# just like self.stopMovingAnim
