from __future__ import annotations

from typing import TYPE_CHECKING

from scal3 import event_lib
from scal3.cal_types import GREGORIAN, to_jd
from scal3.event_lib.handler import Handler

if TYPE_CHECKING:
	from scal3.event_lib.pytypes import EventGroupType, EventType
	from scal3.filesystem import FileSystem


def jd(year: int, month: int, day: int) -> int:
	"""Return the Gregorian Julian day for the given date."""
	return to_jd(year, month, day, GREGORIAN)


def addCustomEvent(group: EventGroupType, summary: str) -> EventType:
	"""Add a saved custom event with a date rule to the group."""
	event = group.create("custom")
	event.setDict(
		{
			"summary": summary,
			"calType": "gregorian",
			"rules": [("date", "2030/05/15")],
		},
	)
	event.setId()
	assert event.id is not None
	group.append(event)
	event.save()
	group.save()
	return event


def makeGenericGroup(fs: FileSystem, title: str = "generic") -> EventGroupType:
	"""Create and save a fresh generic group on the test filesystem."""
	group = event_lib.classes.group.byName["group"]()
	group.fs = fs
	group.setDict(
		{
			"title": title,
			"enable": True,
			"calType": "gregorian",
		},
	)
	group.save()
	return group


def test_archive_group_moves_to_archived_holder(fs: FileSystem) -> None:
	"""Archive moves the group (with its events) to the archived holder, disabled."""
	handler = Handler()
	handler.init(fs)
	group = makeGenericGroup(fs)
	addCustomEvent(group, "a")
	handler.groups.append(group)
	handler.groups.save()
	gid = group.mustId

	assert gid in handler.groups.idList
	assert gid not in handler.archivedGroups.idList
	assert group.enable is True

	handler.groups.archiveGroup(group)

	assert gid not in handler.groups.idList
	assert gid in handler.archivedGroups.idList
	archived = handler.archivedGroups[gid]
	assert archived.enable is False
	assert len(archived) == 1  # events are kept inside the archived group
	assert archived.idList == group.idList


def test_archive_group_persists(fs: FileSystem) -> None:
	"""Archived groups survive a reload and are still treated as disabled."""
	handler = Handler()
	handler.init(fs)
	group = makeGenericGroup(fs)
	addCustomEvent(group, "a")
	handler.groups.append(group)
	handler.groups.save()
	gid = group.mustId
	handler.groups.archiveGroup(group)

	handler2 = Handler()
	handler2.init(fs)
	assert gid in handler2.archivedGroups.idList
	assert gid not in handler2.groups.idList
	archived = handler2.archivedGroups[gid]
	assert archived.enable is False
	assert len(archived) == 1
	assert fs.isfile(group.file)


def test_unarchive_group_back_to_main_holder(fs: FileSystem) -> None:
	"""Unarchive moves the group back, keeping it disabled."""
	handler = Handler()
	handler.init(fs)
	group = makeGenericGroup(fs)
	addCustomEvent(group, "a")
	handler.groups.append(group)
	handler.groups.save()
	gid = group.mustId
	handler.groups.archiveGroup(group)

	archived = handler.archivedGroups[gid]
	handler.groups.unarchiveGroup(archived)

	assert gid not in handler.archivedGroups.idList
	assert gid in handler.groups.idList
	assert handler.groups[gid].enable is False
	assert len(handler.groups[gid]) == 1


def test_recover_orphans_skips_archived_groups(fs: FileSystem) -> None:
	"""RecoverOrphans keeps archived group files and their events in place."""
	handler = Handler()
	handler.init(fs)
	group = makeGenericGroup(fs)
	addCustomEvent(group, "a")
	handler.groups.append(group)
	handler.groups.save()
	gid = group.mustId
	archivedEventId = group.idList[0]
	handler.groups.archiveGroup(group)

	orphan = event_lib.classes.event.byName["custom"]()
	orphan.fs = fs
	orphan.setDict(
		{
			"summary": "orphan",
			"calType": "gregorian",
			"rules": [("date", "2031/01/01")],
		},
	)
	orphan.setId()
	assert orphan.id is not None
	orphan.save()

	newGroup = handler.groups.recoverOrphans()

	# archived group file is not deleted
	assert fs.isfile(group.file)
	assert gid in handler.archivedGroups.idList
	assert newGroup is not None
	# archived group events are not collected as orphans
	assert archivedEventId not in newGroup.idList
	# the truly orphaned event is collected
	assert orphan.id in newGroup.idList


def test_recover_orphans_with_no_archived_holders(fs: FileSystem) -> None:
	"""RecoverOrphans still works when no archived groups exist."""
	handler = Handler()
	handler.init(fs)
	newGroup = handler.groups.recoverOrphans()
	assert newGroup is None
