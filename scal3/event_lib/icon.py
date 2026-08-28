import abc
import os
from os.path import isabs, join, split
from typing import Any

from scal3.path import pixDir, svgDir

__all__ = ["WithIcon", "iconAbsToRelativelnData"]


class WithIcon(abc.ABC):
	"""Mixin providing icon get/set and absolute/relative path conversion methods."""

	icon: str | None

	def getIcon(self) -> str | None:
		"""Return the absolute icon path, or None if unset."""
		return self.icon

	def getIconRel(self) -> str | None:
		"""Return the icon path relative to the application data directories."""
		icon = self.icon
		if not icon:
			return None
		for direc in (svgDir, pixDir):
			if icon.startswith(direc + os.sep):
				return icon[len(direc) + 1 :]
		return icon

	def _iconRelativeToAbsInObj(self) -> None:
		"""Resolve a relative icon path on this object to an absolute path in place."""
		icon = self.icon
		if icon and not isabs(icon):
			if "/" not in icon:
				icon = join("event", icon)
			if icon.endswith(".png"):
				icon = join(pixDir, icon)
			else:
				icon = join(svgDir, icon)
		self.icon = icon


def iconAbsToRelativelnData(data: dict[str, Any]) -> None:
	"""Convert absolute icon paths in a data dictionary to relative paths in place."""
	icon = data["icon"]
	if icon is None:
		return
	iconDir, iconName = split(icon)
	if iconName == "obituary.png":
		iconName = "green_clover.svg"
	elif iconDir in {
		"event",
		join(svgDir, "event"),
		join(pixDir, "event"),
	}:
		icon = iconName
	data["icon"] = icon
