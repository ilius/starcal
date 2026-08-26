# `scal3/event_lib/` — Usage Documentation

## Overview

`event_lib` is the core event management library for StarCal. It is used by **82+ files** across the codebase including UI controllers, account sync modules, VCS integrations, and CLI tools.

---

## Quick Start

```python
from scal3 import event_lib
from scal3.filesystem import FileSystem

# Initialize (must be called once at startup)
event_lib.init(fs)           # fs: FileSystem

# Access the global handler
ev = event_lib.ev  # Handler instance

# Access the class registry
event_lib.classes.event       # Event class registry
event_lib.classes.group       # Group class registry
event_lib.classes.rule        # Rule class registry
event_lib.classes.notifier    # Notifier class registry
event_lib.classes.account     # Account class registry
```

---

## Common Import Patterns

### 1. Initialization

Called once at application startup (typically in `scal3/ui/__init__.py`):

```python
from scal3 import event_lib
from scal3.filesystem import FileSystem

event_lib.init(fs)           # fs: FileSystem — Creates directories, loads state, scans IDs
event_lib.ev.init(fs)        # fs: FileSystem — Initializes the handler (loads accounts, groups)
```

### 2. Event Types and Class Registry

Lookup event types by name for UI combo boxes and event creation:

```python
from scal3 import event_lib

# Iterate all registered event types
for eventType in event_lib.classes.event.names:  # eventType: str, e.g. "custom", "note", "task"
    ...

# Look up event class by name
event_cls = event_lib.classes.event.byName[eventType]  # -> type[Event]

# Get event description for display
desc = event_lib.classes.event.byName[eventType].desc  # -> str
```

### 3. Group Types

Lookup and create event groups:

```python
from scal3.event_lib.group import EventGroup
from scal3 import event_lib

# Iterate all registered group types
for groupType in event_lib.classes.group.names:  # groupType: str, e.g. "group", "noteBook", "taskList"
    ...

# Look up group class by name
group_cls = event_lib.classes.group.byName[groupType]  # -> type[EventGroup]
```

### 4. Working with Events

```python
from scal3.event_lib.event_base import Event, SingleStartEndEvent
from scal3.filesystem import FileSystem

# Load an event by ID
event = Event.load(eventId, fs=fs)  # eventId: int, fs: FileSystem -> Event | None

# Get event file path
fpath = Event.getFile(eventId)  # eventId: int -> str

# ICS export
event_lib.event_ics.exportEventToIcsFileObj(event, fileobj)  # fileobj: IO[str]

# ICS import (setIcsData)
# Base Event.setIcsData returns False (unsupported).
# Subclasses (NoteEvent, TaskEvent, etc.) override to return True on success.
# Caller checks the bool to show a user-friendly GUI error on failure.
supported = event.setIcsData(ics_data_dict)  # ics_data_dict: dict[str, str] -> bool
```

### 5. Event Rules

Import specific rule classes for UI editors and event construction:

```python
from scal3.event_lib.rules import (
    EventRule,                    # Base rule class
    StartEventRule, EndEventRule, # Date+time boundaries
    DateEventRule,                # Date-based
    DateAndTimeEventRule,         # Date+time based
    DayTimeEventRule,             # Time within day
    DayTimeRangeEventRule,        # Time range within day
    DurationEventRule,            # Duration-based
    CycleLenEventRule,            # Cycle-based recurrence
    WeekDayEventRule,             # Day of week
    WeekMonthEventRule,           # Week within month
    WeekNumberModeEventRule,      # Week numbering mode
    MonthEventRule,               # Month matching
    YearEventRule,                # Year matching
    DayOfMonthEventRule,          # Day of month
    ExDatesEventRule,             # Exclusion dates
)
```

### 6. Occurrence Data

Compute which events occur on a specific day:

```python
from scal3.event_lib.occur_data import DayOccurData, getDayOccurrenceData
from scal3.event_lib.occur import JdOccurSet, IntervalOccurSet, TimeListOccurSet

# Get occurrence data for a day across all groups
dayData = getDayOccurrenceData(jd, groups)  # jd: int, groups: Iterable[EventGroupType] -> list[DayOccurData]

# Work with occurrence sets
occur_set = JdOccurSet({jd1, jd2, jd3})  # set of Julian Day ints
interval = IntervalOccurSet(startJd, endJd)  # startJd, endJd: int
```

### 7. Groups and Containers

```python
from scal3.event_lib.group import EventGroup
from scal3.event_lib.event_container import EventContainer, DummyEventContainer
from scal3.event_lib.trash import EventTrash
from scal3.event_lib.groups_holder import EventGroupsHolder
from scal3.filesystem import FileSystem

# Load all groups
groups_holder = EventGroupsHolder.load(ident, fs=fs)  # ident: int, fs: FileSystem

# Trash operations
trash = EventTrash.s_load(ident, fs=fs)  # ident: int, fs: FileSystem
trash.append(eventId)  # eventId: int
```

### 8. Account System

```python
from scal3.event_lib import Account, classes
from scal3.event_lib.errors import AccountError

# Register a new account type (via decorator)
@classes.account.register
class MyAccount(Account):
    ...

# Raise account-specific errors
raise AccountError("sync failed")
```

### 9. VCS Integration

```python
from scal3.event_lib.vcs_base import VcsBaseEventGroup, VcsEpochBaseEventGroup
from scal3.event_lib.vcs import (
    VcsCommitEventGroup,
    VcsTagEventGroup,
    VcsDailyStatEventGroup,
)

# Subclass for new VCS backends
@classes.group.register
class MyVcsGroup(VcsBaseEventGroup):
    ...
```

### 10. Notifiers

```python
from scal3.event_lib.notifier_base import EventNotifier
from scal3.event_lib.notifiers import (
    AlarmNotifier,
    FloatingMsgNotifier,
    WindowMsgNotifier,
    CommandNotifier,
)

@classes.notifier.register
class MyNotifier(EventNotifier):
    ...
```

### 11. Specialized Event Types

```python
from scal3.event_lib.note import NoteBook, DailyNoteEvent
from scal3.event_lib.task import TaskList, TaskEvent, AllDayTaskEvent
from scal3.event_lib.yearly import YearlyGroup, YearlyEvent
from scal3.event_lib.weekly import WeeklyEvent
from scal3.event_lib.monthly import MonthlyEvent
from scal3.event_lib.large_scale import LargeScaleGroup, LargeScaleEvent
from scal3.event_lib.lifetime import LifetimeGroup, LifetimeEvent
from scal3.event_lib.university import (
    UniversityTerm,
    UniversityClassEvent,
    UniversityExamEvent,
    WeeklyScheduleItem,
)
```

### 12. Type Annotations

```python
from scal3.event_lib.pytypes import (
    BaseClassType,
    EventType,
    EventGroupType,
    EventContainerType,
    EventRuleType,
    EventNotifierType,
    AccountType,
    OccurSetType,
    RuleContainerType,
    EventGroupType,
    EventSearchConditionDict,
)
```

### 13. Plugin API

Plugins access event_lib through a dynamic API to avoid circular imports:

```python
# In a plugin file (e.g., plugins/pray_times_files/pray_times.py)
event_classes = api.get("event_lib", "classes")
EventRule = api.get("event_lib", "EventRule")
```

The available API symbols are defined in `__init__.py:152-160`:
```python
__plugin_api_get__ = [
    "classes", "defaultGroupTypeIndex", "EventRule",
    "EventNotifier", "Event", "EventGroup", "Account",
]
```

---

## Side-Effect Imports

Some modules are imported solely for their registration side effects:

```python
# Register all event_lib extensions (accounts, VCS modules)
import scal3.event_lib_import_all  # noqa: F401

# The following modules self-register via @decorators at import time:
from . import (
    events,        # Registers CustomEvent
    large_scale,   # Registers LargeScaleEvent/Group
    lifetime,      # Registers LifetimeEvent/Group
    monthly,       # Registers MonthlyEvent
    note,          # Registers NoteBook, DailyNoteEvent
    notifiers,     # Registers AlarmNotifier, etc.
    task,          # Registers TaskList, TaskEvent, AllDayTaskEvent
    university,    # Registers UniversityTerm, UniversityClassEvent, etc.
    vcs,           # Registers VCS event groups
    weekly,        # Registers WeeklyEvent
    yearly,        # Registers YearlyGroup, YearlyEvent
)
```

---

## Consumer Files by Category

| Category | Count | Key Files |
|---|---|---|
| **UI (GTK) — Event editors** | 14 | `scal3/ui_gtk/event/event/*.py` |
| **UI (GTK) — Group editors** | 12 | `scal3/ui_gtk/event/group/*.py` |
| **UI (GTK) — Rule editors** | 14 | `scal3/ui_gtk/event/rule/*.py` |
| **UI (GTK) — Notifier widgets** | 3 | `scal3/ui_gtk/event/notifier/*.py` |
| **UI (GTK) — Core** | 12 | `scal3/ui_gtk/starcal*.py`, `scal3/ui_gtk/timeline.py`, etc. |
| **Account modules** | 2 | `scal3/account/starcal.py`, `scal3/account/google.py` |
| **VCS modules** | 3 | `scal3/vcs_modules/*.py` |
| **Core modules** | 8 | `scal3/cell.py`, `scal3/core.py`, `scal3/show_event.py`, etc. |
| **Tools** | 2 | `tools/wikipedia-fa-events/`, `tools/kalzium-elements-discovery.py` |
| **Plugins** | 1 | `plugins/pray_times_files/pray_times.py` |

---

## Module Map

```
event_lib/
├── __init__.py          # Package init, init(), ev Handler, class assertions
├── event_base.py        # Event, SingleStartEndEvent — core event model
├── event_container.py   # EventContainer — base for groups/trash
├── event_ics.py         # ICS format export
├── events.py            # CustomEvent registration
├── group.py             # EventGroup — main event container
├── groups_holder.py     # EventGroupsHolder — manages all groups
├── groups_import.py     # Import mode constants
├── handler.py           # Handler — facade for accounts/groups/trash
├── holders.py           # ObjectsHolderTextModel — generic ordered collection
├── accounts.py          # Account base class
├── accounts_holder.py   # EventAccountsHolder — manages all accounts
├── trash.py             # EventTrash — deleted events container
├── register.py          # Class registry (classes.event, classes.group, etc.)
├── pytypes.py           # Protocol definitions for all types
├── state.py             # Global state (allReadOnly, info, lastIds)
├── common.py            # Utilities (week days, JD, compression)
├── icon.py              # Icon path handling
├── object_base.py       # EventObjTextModel — read-only aware text model
├── objects.py           # HistoryEventObjBinaryModel — history-tracked binary model
├── occur.py             # OccurSet types (JdOccurSet, IntervalOccurSet, TimeListOccurSet)
├── occur_data.py        # DayOccurData, getDayOccurrenceData
├── rule_container.py    # RuleContainer — mixin for objects with rules
├── patch.py             # createPatchListFromGroup — sync patches
├── notifier_base.py     # EventNotifier base
├── notifiers.py         # AlarmNotifier, FloatingMsgNotifier, etc.
├── note.py              # NoteBook, DailyNoteEvent
├── task.py              # TaskList, TaskEvent, AllDayTaskEvent
├── yearly.py            # YearlyGroup, YearlyEvent
├── weekly.py            # WeeklyEvent
├── monthly.py           # MonthlyEvent
├── large_scale.py       # LargeScaleGroup, LargeScaleEvent
├── lifetime.py          # LifetimeGroup, LifetimeEvent
├── university.py        # UniversityTerm, UniversityClassEvent, UniversityExamEvent
├── vcs_base.py          # VcsBaseEventGroup, VcsEpochBaseEventGroup
├── vcs.py               # VcsCommitEventGroup, VcsTagEventGroup, etc.
├── typing_test.py       # Ad-hoc type checking (not a real test)
├── errors.py            # AccountError
├── exceptions.py        # BadEventFile
└── rules/
    ├── __init__.py      # Re-exports all rule classes
    ├── rule_base.py     # EventRule base
    ├── rule_allday.py   # AllDayEventRule, MultiValueAllDayEventRule
    ├── rule_cycle.py    # CycleDaysEventRule, CycleWeeksEventRule, CycleLenEventRule
    ├── rule_date.py     # DateEventRule, ExDatesEventRule
    ├── rule_datetime.py # DateAndTimeEventRule, StartEventRule, EndEventRule
    ├── rule_daytime.py  # DayTimeEventRule, DayTimeRangeEventRule
    ├── rule_duration.py # DurationEventRule
    ├── rule_week.py     # WeekNumberModeEventRule, WeekDayEventRule, WeekMonthEventRule
    └── rule_ymd.py      # YearEventRule, MonthEventRule, DayOfMonthEventRule, Ex* rules
```
