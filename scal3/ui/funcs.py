from __future__ import annotations

from typing import TYPE_CHECKING

from scal3 import logger

if TYPE_CHECKING:
	from scal3.pytypes import CellCacheType

__all__ = ["checkEnabledNamesItems", "getHolidaysJdList"]

log = logger.get()


def checkEnabledNamesItems(
	items: list[tuple[str, bool]],
	itemsDefault: list[tuple[str, bool]],
) -> list[tuple[str, bool]]:
	# cleaning and updating items
	names = {name for (name, i) in items}
	defaultNames = {name for (name, i) in itemsDefault}
	# -----
	# removing items that are no longer supported
	items, itemsTmp = [], items
	for name, enable in itemsTmp:
		if name in defaultNames:
			items.append((name, enable))
	# -----
	# adding items newly added in this version, this is for user"s convenience
	newNames = defaultNames.difference(names)
	log.debug(f"items: {newNames = }")
	# --
	for name in newNames:
		items.append((name, False))  # FIXME
	return items


def getHolidaysJdList(
	cells: CellCacheType,
	startJd: int,
	endJd: int,
) -> list[int]:
	jdList = []
	for jd in range(startJd, endJd):
		tmpCell = cells.getTmpCell(jd)
		if tmpCell.holiday:
			jdList.append(jd)
	return jdList
