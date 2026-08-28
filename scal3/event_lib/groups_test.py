from __future__ import annotations

import io
from typing import TYPE_CHECKING, cast

import pytest

from scal3 import event_lib
from scal3.cal_types import GREGORIAN, to_jd
from scal3.event_lib.group import EventGroup
from scal3.event_lib.groups_import import ImportMode
from scal3.event_lib.handler import Handler
from scal3.event_lib.large_scale import LargeScaleGroup
from scal3.event_lib.task import TaskList
from scal3.event_lib.university import UniversityTerm
from scal3.event_lib.vcs import VcsCommitEventGroup, VcsTagEventGroup

if TYPE_CHECKING:
	from scal3.event_lib.event_container import EventContainer
	from scal3.event_lib.pytypes import EventGroupType, EventType
	from scal3.filesystem import FileSystem


def jd(year: int, month: int, day: int) -> int:
	"""Return the Gregorian Julian day for the given date."""
	return to_jd(year, month, day, GREGORIAN)


def createGroup(fs: FileSystem, groupType: str) -> EventGroupType:
	"""Create a fresh group of the given type on the test filesystem."""
	group = event_lib.classes.group.byName[groupType]()
	group.fs = fs
	return group


def addEvent(group: EventGroupType, eventType: str) -> EventType:
	"""Create, append and save an event of the given type in the group."""
	event = group.create(eventType)
	event.setId()
	assert event.id is not None
	group.append(event)
	event.save()
	group.save()
	return event


def assertGroupPersisted(
	group: EventGroupType,
	groupType: str,
	title: str,
) -> None:
	"""Check the group attributes set by setDict and the save/load roundtrip."""
	assert group.name == groupType
	assert group.title == title
	assert group.enable is True
	group.save()
	assert group.id is not None
	assert group.fs.isfile(group.file)

	groupCls = event_lib.classes.group.byName[groupType]
	reloaded = groupCls.load(group.id, group.fs)
	assert reloaded is not None
	assert reloaded.name == groupType
	assert reloaded.title == title


def assertGroupExport(group: EventGroupType, title: str) -> None:
	"""Check exportData and exportToIcsFp produce usable output."""
	data = group.exportData()
	assert data["title"] == title
	assert data["events"] is not None

	fp = io.StringIO()
	group.exportToIcsFp(fp)
	assert isinstance(fp.getvalue(), str)


def test_legacy_group_set_defaults_override() -> None:
	"""Existing group subclasses can still override the public defaults hook."""

	class LegacyGroup(EventGroup):
		params = EventGroup.params + ["legacyDefault"]

		def setDefaults(self) -> None:
			"""Initialize a persisted plugin field through the legacy hook."""
			super().setDefaults()
			self.legacyDefault = "initialized"

	group = LegacyGroup()
	assert group.legacyDefault == "initialized"
	assert group.getDict()["legacyDefault"] == "initialized"


def test_legacy_group_mutation_hooks(fs: FileSystem) -> None:
	"""Container operations retain public pre/post-add and clear dispatch."""

	class LegacyGroup(EventGroup):
		def __init__(self) -> None:
			self.preAddCalled = False
			self.postAddCalled = False
			self.clearCalled = False
			super().__init__()

		def preAdd(self, event: EventType) -> None:
			"""Record validation through the legacy public hook."""
			self.preAddCalled = True
			super().preAdd(event)

		def postAdd(self, event: EventType) -> None:
			"""Record finalization through the legacy public hook."""
			self.postAddCalled = True
			super().postAdd(event)

		def clear(self) -> None:
			"""Record occurrence clearing through the legacy public hook."""
			self.clearCalled = True
			super().clear()

	group = LegacyGroup()
	group.fs = fs
	event = group.create("custom")
	event.setId()
	group.append(event)
	assert group.preAddCalled
	assert group.postAddCalled
	assert event.parent is group

	group.updateOccurrence()
	assert group.clearCalled


def test_legacy_group_insert_hooks(fs: FileSystem) -> None:
	"""Insert also dispatches through the public pre/post-add hooks."""

	class LegacyGroup(EventGroup):
		def __init__(self) -> None:
			self.preAddCalled = False
			self.postAddCalled = False
			super().__init__()

		def preAdd(self, event: EventType) -> None:
			"""Record validation through the legacy public hook."""
			self.preAddCalled = True
			super().preAdd(event)

		def postAdd(self, event: EventType) -> None:
			"""Record finalization through the legacy public hook."""
			self.postAddCalled = True
			super().postAdd(event)

	group = LegacyGroup()
	group.fs = fs
	event = group.create("custom")
	event.setId()
	assert event.id is not None
	group.insert(0, event)
	assert group.preAddCalled
	assert group.postAddCalled
	assert event.parent is group
	assert group.idList == [event.id]

	with pytest.raises(ValueError, match="already contains"):
		group.insert(0, event)


def test_group_type_group(fs: FileSystem) -> None:
	"""Generic group accepts custom events and exports them to ICS."""
	group = createGroup(fs, "group")
	group.setDict(
		{
			"title": "my group",
			"enable": True,
			"calType": "gregorian",
			"showInMCal": True,
		},
	)
	assertGroupPersisted(group, "group", "my group")

	event = addEvent(group, "custom")
	event.setDict(
		{
			"summary": "meeting",
			"calType": "gregorian",
			"rules": [("date", "2030/05/15")],
		},
	)
	event.save()

	assertGroupExport(group, "my group")
	fp = io.StringIO()
	group.exportToIcsFp(fp)
	assert "BEGIN:VEVENT" in fp.getvalue()
	assert "SUMMARY:meeting" in fp.getvalue()


def test_group_type_large_scale(fs: FileSystem) -> None:
	"""LargeScaleGroup carries a scale param and holds large-scale events."""
	group = createGroup(fs, "largeScale")
	group.setDict(
		{
			"title": "eras",
			"enable": True,
			"calType": "gregorian",
			"scale": 1000,
		},
	)
	assertGroupPersisted(group, "largeScale", "eras")
	assert isinstance(group, LargeScaleGroup)
	assert group.scale == 1000

	group.startJd = jd(2020, 1, 1)
	group.endJd = jd(2035, 1, 1)
	event = addEvent(group, "largeScale")
	event.setDict(
		{
			"summary": "era",
			"calType": "gregorian",
			"scale": 1,
			"start": 2025,
			"end": 2,
			"endRel": True,
		},
	)
	event.save()

	assertGroupExport(group, "eras")
	fp = io.StringIO()
	group.exportToIcsFp(fp)
	assert "BEGIN:VEVENT" in fp.getvalue()


def test_group_type_lifetime(fs: FileSystem) -> None:
	"""LifetimeGroup carries the separate-year-input flag."""
	group = createGroup(fs, "lifetime")
	group.setDict(
		{
			"title": "life",
			"enable": True,
			"calType": "gregorian",
			"showSeparateYmdInputs": True,
		},
	)
	assertGroupPersisted(group, "lifetime", "life")

	addEvent(group, "lifetime")
	assertGroupExport(group, "life")


def test_group_type_note_book(fs: FileSystem) -> None:
	"""NoteBook holds daily notes and exports them to ICS."""
	group = createGroup(fs, "noteBook")
	group.setDict(
		{
			"title": "notes",
			"enable": True,
			"calType": "gregorian",
		},
	)
	assertGroupPersisted(group, "noteBook", "notes")

	event = addEvent(group, "dailyNote")
	event.setDict(
		{
			"summary": "note",
			"calType": "gregorian",
			"rules": [("date", "2030/05/15")],
		},
	)
	event.save()

	assertGroupExport(group, "notes")
	fp = io.StringIO()
	group.exportToIcsFp(fp)
	assert "BEGIN:VEVENT" in fp.getvalue()


def test_group_type_task_list(fs: FileSystem) -> None:
	"""TaskList carries a default duration and holds task events."""
	group = createGroup(fs, "taskList")
	group.setDict(
		{
			"title": "tasks",
			"enable": True,
			"calType": "gregorian",
			"defaultDuration": "1 hour",
		},
	)
	assertGroupPersisted(group, "taskList", "tasks")
	assert isinstance(group, TaskList)
	assert group.defaultDuration == (1.0, 3600)

	addEvent(group, "task")
	assertGroupExport(group, "tasks")


def test_group_type_university_term(fs: FileSystem) -> None:
	"""UniversityTerm carries time bounds, courses and term end date."""
	group = createGroup(fs, "universityTerm")
	group.setDict(
		{
			"title": "term",
			"enable": True,
			"calType": "gregorian",
			"classTimeBounds": ["08:00", "10:00", "12:00"],
			"classesEndDate": "2030/06/15",
		},
	)
	assertGroupPersisted(group, "universityTerm", "term")
	assert isinstance(group, UniversityTerm)
	assert group.classesEndDate == (2030, 6, 15)
	assert len(group.classTimeBounds) == 3

	event = addEvent(group, "universityClass")
	event.setDict(
		{
			"summary": "math",
			"calType": "gregorian",
			"courseId": 1,
			"rules": [
				("start", {"date": "2030/01/01", "time": "09:00:00"}),
				("end", {"date": "2030/06/15", "time": "09:00:00"}),
				("weekNumMode", "any"),
				("weekDay", [1]),
				("dayTimeRange", ("09:00:00", "10:00:00")),
			],
		},
	)
	event.save()

	assertGroupExport(group, "term")


def test_group_type_yearly(fs: FileSystem) -> None:
	"""YearlyGroup carries the showDate flag and holds yearly events."""
	group = createGroup(fs, "yearly")
	group.setDict(
		{
			"title": "anniversaries",
			"enable": True,
			"calType": "gregorian",
			"showDate": True,
		},
	)
	assertGroupPersisted(group, "yearly", "anniversaries")

	event = addEvent(group, "yearly")
	event.setDict(
		{
			"summary": "birthday",
			"calType": "gregorian",
			"rules": [("month", [5]), ("day", [15])],
		},
	)
	event.save()

	assertGroupExport(group, "anniversaries")
	fp = io.StringIO()
	group.exportToIcsFp(fp)
	assert "BEGIN:VEVENT" in fp.getvalue()


def test_group_type_vcs(fs: FileSystem) -> None:
	"""VcsCommitEventGroup carries VCS repo config and display flags."""
	group = createGroup(fs, "vcs")
	group.setDict(
		{
			"title": "repo",
			"enable": True,
			"calType": "gregorian",
			"vcsType": "git",
			"vcsDir": "/tmp/repo",
			"vcsBranch": "main",
			"showAuthor": True,
			"showShortHash": True,
			"showStat": True,
		},
	)
	assertGroupPersisted(group, "vcs", "repo")
	assert isinstance(group, VcsCommitEventGroup)
	assert group.vcsType == "git"
	assert group.vcsBranch == "main"

	assertGroupExport(group, "repo")


def test_group_type_vcs_tag(fs: FileSystem) -> None:
	"""VcsTagEventGroup carries VCS config and a showStat flag."""
	group = createGroup(fs, "vcsTag")
	group.setDict(
		{
			"title": "tags",
			"enable": True,
			"calType": "gregorian",
			"vcsType": "git",
			"vcsDir": "/tmp/repo",
			"vcsBranch": "main",
			"showStat": True,
		},
	)
	assertGroupPersisted(group, "vcsTag", "tags")
	assert isinstance(group, VcsTagEventGroup)
	assert group.showStat is True

	assertGroupExport(group, "tags")


def test_group_type_vcs_daily_stat(fs: FileSystem) -> None:
	"""VcsDailyStatEventGroup carries VCS repo config."""
	group = createGroup(fs, "vcsDailyStat")
	group.setDict(
		{
			"title": "stat",
			"enable": True,
			"calType": "gregorian",
			"vcsType": "git",
			"vcsDir": "/tmp/repo",
			"vcsBranch": "main",
		},
	)
	assertGroupPersisted(group, "vcsDailyStat", "stat")

	assertGroupExport(group, "stat")


def test_handler_init_creates_default_groups(fs: FileSystem) -> None:
	"""A fresh filesystem gets the default NoteBook/TaskList/Group objects."""
	handler = Handler()
	handler.init(fs)
	assert len(handler.groups) == 3
	titles = [group.title for group in handler.groups]
	assert len(titles) == 3


def test_default_groups_persist_to_disk(fs: FileSystem) -> None:
	"""Default groups are saved as files in the temp filesystem."""
	handler = Handler()
	handler.init(fs)
	assert fs.isfile("event/group_list.json")
	for group in handler.groups:
		assert group.id is not None
		assert fs.isfile(group.file)


# ---------------------------------------------------------------------------
# generic group behavior (cross-type)


def makeGenericGroup(fs: FileSystem) -> EventGroupType:
	"""Create and save a fresh generic group with a custom event in it."""
	group = createGroup(fs, "group")
	group.setDict(
		{
			"title": "generic",
			"enable": True,
			"calType": "gregorian",
		},
	)
	group.save()
	return group


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


def test_group_must_id(fs: FileSystem) -> None:
	"""MustId returns the group id after assignment."""
	group = makeGenericGroup(fs)
	assert group.mustId == group.id


def test_group_set_title_and_random_color(fs: FileSystem) -> None:
	"""SetTitle and setRandomColor update the group."""
	group = makeGenericGroup(fs)
	group.setTitle("renamed")
	assert group.title == "renamed"
	group.setRandomColor()
	assert group.color is not None


def test_group_check_event_to_add(fs: FileSystem) -> None:
	"""CheckEventToAdd honors the accepted event types."""
	handler = Handler()
	handler.init(fs)
	noteBook = handler.groups.byIndex(0)
	assert noteBook.checkEventToAdd(noteBook.create("dailyNote")) is True
	assert noteBook.checkEventToAdd(noteBook.create("custom")) is False

	generic = handler.groups.byIndex(2)
	assert generic.checkEventToAdd(generic.create("custom")) is True


def test_group_show_in_cal(fs: FileSystem) -> None:
	"""ShowInCal reflects the calendar view flags."""
	group = makeGenericGroup(fs)
	assert group.showInCal() is True
	group.showInDCal = group.showInWCal = group.showInMCal = False
	assert group.showInCal() is False


def test_group_get_sort_bys_and_sort(fs: FileSystem) -> None:
	"""GetSortBys lists options and sort reorders the id list."""
	group = makeGenericGroup(fs)
	default, options = group.getSortBys()
	assert isinstance(default, str)
	assert isinstance(options, list)
	assert options

	addCustomEvent(group, "b")
	addCustomEvent(group, "a")
	addCustomEvent(group, "c")
	group.sort("summary")
	summaries = [group.getEvent(eid).summary for eid in group.idList]
	assert summaries == ["a", "b", "c"]
	group.sort("summary", reverse=True)
	summaries = [group.getEvent(eid).summary for eid in group.idList]
	assert summaries == ["c", "b", "a"]


def test_group_move_up_down_insert(fs: FileSystem) -> None:
	"""moveUp/moveDown/insert reorder and extend the id list."""
	group = makeGenericGroup(fs)
	addCustomEvent(group, "a")
	addCustomEvent(group, "b")
	addCustomEvent(group, "c")

	group.moveUp(2)
	assert [group.getEvent(eid).summary for eid in group.idList] == ["a", "c", "b"]
	group.moveDown(0)
	assert [group.getEvent(eid).summary for eid in group.idList] == ["c", "a", "b"]

	extra = group.create("custom")
	extra.setDict({"summary": "z", "calType": "gregorian"})
	extra.setId()
	assert extra.id is not None
	group.insert(1, extra)
	extra.save()
	assert [group.getEvent(eid).summary for eid in group.idList] == ["c", "z", "a", "b"]


def test_group_remove(fs: FileSystem) -> None:
	"""Remove excludes an event from the group."""
	group = makeGenericGroup(fs)
	event = addCustomEvent(group, "a")
	index = group.remove(event)
	assert index == 0
	assert len(group.idList) == 0


def test_group_remove_all(fs: FileSystem) -> None:
	"""RemoveAll clears the group and its occurrence data."""
	group = makeGenericGroup(fs)
	addCustomEvent(group, "a")
	addCustomEvent(group, "b")
	assert len(group.idList) == 2
	group.removeAll()
	assert len(group.idList) == 0


def test_group_get_start_epoch(fs: FileSystem) -> None:
	"""GetStartEpoch returns the epoch of the group start date."""
	group = makeGenericGroup(fs)
	group.startJd = jd(2030, 1, 1)
	container = cast("EventContainer", group)
	assert group.getStartEpoch() == container.getEpochFromJd(jd(2030, 1, 1))


def test_group_update_occurrence(fs: FileSystem) -> None:
	"""UpdateOccurrence rebuilds the occurrence tree."""
	group = makeGenericGroup(fs)
	addCustomEvent(group, "a")
	group.updateOccurrence()
	assert group.occur is not None
	assert group.occurCount >= 1


def test_group_deep_copy(fs: FileSystem) -> None:
	"""DeepCopy clones the group and its events."""
	group = makeGenericGroup(fs)
	addCustomEvent(group, "a")
	copy = group.deepCopy()
	assert isinstance(copy, type(group))
	assert len(copy.idList) == len(group.idList)
	assert copy.getEvent(copy.idList[0]).summary == "a"


def test_group_read_only(fs: FileSystem) -> None:
	"""setReadOnly/isReadOnly toggle the per-group read-only flag."""
	group = makeGenericGroup(fs)
	assert group.isReadOnly() is False
	group.setReadOnly(True)
	assert group.isReadOnly() is True
	group.setReadOnly(False)
	assert group.isReadOnly() is False


def test_group_after_sync_get_last_sync(fs: FileSystem) -> None:
	"""AfterSync records the sync time range for the remote ids."""
	group = makeGenericGroup(fs)
	group.remoteIds = (1, "remote-group")
	assert group.getLastSync() is None
	group.afterSync(100)
	lastSync = group.getLastSync()
	assert lastSync is not None
	assert lastSync[0] == 100


def test_group_import_data(fs: FileSystem) -> None:
	"""ImportData re-imports exported data idempotently."""
	group = makeGenericGroup(fs)
	addCustomEvent(group, "a")
	data = group.exportData()
	result = group.importData(data, importMode=ImportMode.SKIP_MODIFIED)
	assert not result.newGroupIds
	assert len(group.idList) == 1


def test_group_get_event_not_found(fs: FileSystem) -> None:
	"""GetEvent with an unknown id raises ValueError."""
	group = makeGenericGroup(fs)
	with pytest.raises(ValueError, match="does not contain"):
		group.getEvent(9999)


def test_group_get_sort_by_value(fs: FileSystem) -> None:
	"""GetSortByValue returns the value used for sorting."""
	group = makeGenericGroup(fs)
	event = addCustomEvent(group, "a")
	eventGroup = cast("EventGroup", group)
	assert eventGroup.getSortByValue(event, "summary") == "a"


def test_group_deep_convert_to(fs: FileSystem) -> None:
	"""DeepConvertTo converts an empty group to another type."""
	group = makeGenericGroup(fs)
	converted = group.deepConvertTo("noteBook")
	assert converted.name == "noteBook"
	converted.setId(group.id)
	assert converted.id == group.id


def test_group_get_dict_roundtrip(fs: FileSystem) -> None:
	"""GetDict output reimports into a fresh group."""
	group = makeGenericGroup(fs)
	data = group.getDict()
	assert data["title"] == "generic"
	assert data["type"] == "group"

	groupCls = event_lib.classes.group.byName["group"]
	fresh = groupCls()
	fresh.fs = fs
	fresh.setDict(data)
	assert fresh.title == "generic"
