# Ovulation & Menstrual Cycle Calendar — Implementation Proposal

**Status:** Implemented (v1)
**Target:** StarCal (`scal3/`, Python/GTK)
**Scope:** New event type(s) + group to track menstrual cycles, predict ovulation /
fertile window, estimate the per-day likelihood of pregnancy given intercourse, support
manual correction, and record daily observations by either partner.

> **Implementation status (v1):** core model, editors, three SVG phase icons
> (`svg/event/menstruation.svg`, `svg/event/fertile.svg`, `svg/event/ovulation.svg`),
> tests (`scal3/event_lib/menstrual_test.py`) and a sample-data generator
> (`tools/generate_menstrual_sample.py`) are implemented. Cells are marked with phase
> icons (event icons) instead of background colors. Per-day pregnancy likelihood is
> computed by `MenstrualCycleGroup.probabilityOnDate()` and surfaced in the derived
> fertile/ovulation event summaries. See §4 for the final file layout.

______________________________________________________________________

## 1. Summary

StarCal currently has no health/cycle tracking. This proposal adds a **menstrual cycle
group and events** to `scal3/event_lib/` following the existing event patterns
(`DailyNoteEvent`, `YearlyEvent`, `LargeScaleGroup`), plus a **cell-rendering hook** in
the same style as the existing pray-times plugin (`plugins/pray_times_files/`) so that
each calendar day can show cycle-phase and pregnancy-likelihood information that
occurrence sets alone cannot carry.

The feature answers three questions:

1. **When are periods?** — recorded period-start dates, extrapolated forward using an
   estimated cycle length.
1. **When is the fertile window / ovulation day?** — derived from the predicted next
   period minus the (fairly constant) luteal phase.
1. **What is the likelihood of pregnancy from intercourse on a given day?** — the
   day-specific conception probabilities from the landmark Wilcox 1995 study, relative
   to the estimated ovulation day.

Everything is a prediction and must be **manually adjustable**; observations (flow,
mucus, BBT, OPK, symptoms, intercourse) can be logged by the woman **or her partner**.

> **Medical disclaimer (to be shown in the UI and docs):** This is an informational
> calendar feature, not a medical device. Predictions are estimates and are not
> reliable for contraception or conception planning. Always consult a qualified
> healthcare provider.

______________________________________________________________________

## 2. Domain research (summary of sources)

Sources consulted (full list in §8): Johns Hopkins, Planned Parenthood (via
scienceinsights.org), calculator.net, miniwebtool, medplore, the Wilcox 1995 NEJM study
and the Dunson 1999 Human Reproduction follow-up.

### 2.1 Calendar ("rhythm") method

- The cycle runs **day 1 = first day of bleeding** until the day before the next period
  starts. Normal range ≈ 21–35 days; average ≈ 28 days.
- The **luteal phase** (ovulation → next period) is the stable part: ≈ **12–14 days
  (range 10–17)**, largely constant per woman. The follicular phase (period →
  ovulation) is the variable part.
- Therefore **estimated ovulation day ≈ (predicted next period) − luteal phase**
  (equivalently `cycleLength − lutealPhase` days after period start; for a 28-day cycle
  with 14-day luteal phase → day 14).
- Track at least 6 cycles for a reliable average; the calendar method is only
  meaningful for reasonably regular cycles.

### 2.2 Fertile window

- Sperm survive up to ~5 days; the egg is fertilizable only ~12–24 h. Conception
  occurs almost exclusively during a **6-day window ending on ovulation day**
  (5 days before + ovulation day) [Wilcox 1995]. Some sources also include the day
  after ovulation (7 days total).
- Peak fertility = **the 2–3 days before ovulation and ovulation day**.

### 2.3 Day-specific probability of conception (Wilcox 1995, NEJM 333(23):1517–21)

Study of 221 women; day-specific probabilities relative to the estimated ovulation day
(day 0). These are **per-cycle probabilities of pregnancy given intercourse on that one
day** (single day of intercourse):

| Day rel. to ovulation | Probability of conception |
|---|---|
| −5 | ~10 % |
| −4 | ~16 % |
| −3 | ~14 % |
| −2 | ~27 % |
| −1 | ~31 % |
| 0 (ovulation) | **~33 %** (peak) |
| +1 | 0–8 % (rapid drop) |
| ≤ −6 or ≥ +2 | ≈ 0 |

Model facts used in the proposal:

- The model estimates these from ~625 cycles; probabilities 0.10–0.33 across the six
  days.
- **Cycle viability** (the chance a cycle can conceive at all) was ~0.37; daily
  intercourse during the window gives ~0.37 per cycle; every-other-day ~0.33; the
  numbers are usually presented as relative likelihoods without multiplying by
  viability, which is the convention this proposal follows (and makes adjustable).
- Nearly all pregnancies are attributable to intercourse in the 6-day window ending on
  ovulation day; probabilities on the marginal days were ~0 (CIs up to ~12 %).

### 2.4 Observation methods (for manual correction & cross-checking)

- **Cervical mucus:** dry → sticky → creamy → watery → clear/"raw-egg-white" indicates
  ovulation is near. (Bigelow et al. 2004: mucus quality predicts conception better
  than timing alone.)
- **Basal body temperature (BBT):** sustained ~0.3–0.5 °C rise after ovulation;
  confirms ovulation *after* the fact.
- **Ovulation predictor kits (OPK):** detect the LH surge 12–48 h before ovulation.
- These give the user **evidence to override the calendar estimate** (a core
  requirement, §5.5).

### 2.5 Irregular cycles

If cycle length varies by more than ~5–7 days, calendar-only prediction is unreliable.
The design therefore (a) uses the most recent cycles weighted by recency, (b) exposes
the fertile window computed from cycle extremes when irregularities are present (the
Ogino–Knaus style "earliest possible / latest possible" window), and (c) relies on
manual override + observations.

______________________________________________________________________

## 3. Requirements

- **R1 Periods:** record the first day of each period; display period days (and
  optional predicted period days) on the calendar.
- **R2 Cycle tracking:** maintain an average/estimated cycle length and luteal phase,
  updated as new period starts are recorded; extrapolate future periods.
- **R3 Ovulation & fertile window:** estimate ovulation day and the fertile window for
  each cycle; show them on the calendar.
- **R4 Pregnancy likelihood by sex on a given day:** for any calendar day, compute and
  display the estimated probability that intercourse on that day results in pregnancy,
  based on the day-relative-to-ovulation probabilities in §2.3.
- **R5 Manual adjustment:** the user can override cycle length, luteal phase, period
  length, a predicted period date, and the ovulation day for a cycle; overrides
  propagate to predictions.
- **R6 Observations:** record daily observations — recorded-by (woman / partner), flow
  level, cervical mucus, BBT, OPK result, symptoms/notes, and whether intercourse
  occurred — tied to a date.
- **R7 Predictions vs. records:** recorded data is always visually distinguished from
  predicted data (solid vs. dashed/hatched, different shades).
- **R8 Multiple people:** the feature must support tracking more than one person (e.g.
  partners in the same StarCal install), via one group instance per person.
- **R9 Tests & isolation:** automated tests must follow the `event_lib` rules in
  `CLAUDE.md` (isolated temp `FileSystem` via the `fs` fixture; never call
  `event_lib.init()`).

______________________________________________________________________

## 4. Proposed design in StarCal

### 4.1 Files to add / modify

| File | Kind | Purpose |
|---|---|---|
| `scal3/event_lib/menstrual.py` | **new** | `MenstrualCycleGroup`, `MenstrualPeriodEvent`, `MenstrualFertileEvent`, `MenstrualOvulationEvent`, `MenstrualObservationEvent`, cycle math |
| `scal3/event_lib/__init__.py` | edit | import `menstrual` for side-effect registration |
| `scal3/event_lib/menstrual_test.py` | **new** | tests (§4.7) |
| `scal3/event_lib/README.md` | edit | document the new types |
| `scal3/ui_gtk/event/event/menstrualPeriod.py` | **new** | period event editor widget |
| `scal3/ui_gtk/event/event/menstrualObservation.py` | **new** | observation event editor widget |
| `scal3/ui_gtk/event/event/menstrualFertile.py` | **new** | fertile-window (derived) widget |
| `scal3/ui_gtk/event/event/menstrualOvulation.py` | **new** | ovulation (derived) widget |
| `scal3/ui_gtk/event/group/menstrualCycle.py` | **new** | group editor widget |
| `scal3/ui_gtk/event/__init__.py` | edit | add loader fns + `widgetClassLoaderByName` entries |
| `svg/event/menstruation.svg` | **new** | period phase icon |
| `svg/event/fertile.svg` | **new** | fertile-window phase icon |
| `svg/event/ovulation.svg` | **new** | ovulation phase icon |
| `tools/generate_menstrual_sample.py` | **new** | sample group JSON generator (importable via Event Manager) |
| `locale.d/en.po`, `locale.d/fa.po` | edit | new translatable strings |

### 4.2 Data model (event_lib)

Following the codebase conventions (§1 of `scal3/event_lib/README.md`), all classes
register via `@classes.event.register` / `@classes.group.register`, declare
`params`/`paramsOrder`, `getDict`/`setDict`, `getV4Dict`, `calcEventOccurrenceIn`, and
wrap every user-facing string in `_()`.

**`MenstrualCycleGroup(EventGroup)`** — one instance per tracked person.

```python
name = "menstrualCycle"
desc = _("Menstrual Cycle")
acceptsEventTypes = ("menstrualPeriod", "menstrualObservation")
params = EventGroup.params + [
	"cycleLength",  # estimated average cycle length, days (e.g. 28)
	"cycleLengthAuto",  # True → recompute from recorded period starts
	"lutealPhase",  # e.g. 14 (constant per woman)
	"periodLength",  # e.g. 5
	"windowMode",  # "fixed" | "oginoKnaus" (irregular)
	"minCycle",
	"maxCycle",  # used in oginoKnaus mode
	"showPeriodPredict",
	"showFertile",
	"showProbability",
	"personName",  # optional label for the tracked person
]
```

The group is the **authority for predictions** (§4.3): it reads its recorded period
starts, computes cycle stats, and answers per-day queries. It is analogous to
`UniversityTerm`, which holds shared state that events and UI read
(`scal3/event_lib/university.py`).

**`MenstrualPeriodEvent(Event)`** — one instance per recorded period start
(anchored on a date; modeled on `DailyNoteEvent`, `note.py`).

```python
name = "menstrualPeriod"
desc = _("Period")
isSingleOccur = True
requiredRules = ["date"]
isAllDay = True
params = Event.params + ["actualCycle", "ovulationOverride"]
# actualCycle     — measured length from previous period start (auto, editable)
# ovulationOverride — user-confirmed ovulation day (optional; overrides estimate)
```

`calcEventOccurrenceIn` returns the **period days** for this occurrence:
`{startJd, startJd+1, …, startJd+periodLength-1}` (period length from the group),
so period days appear as normal all-day event occurrences and pick up the group color.

**`MenstrualObservationEvent(Event)`** — one per day logged by either partner
(modeled on `DailyNoteEvent` + `description`):

```python
name = "menstrualObservation"
desc = _("Cycle Observation")
isSingleOccur = True
requiredRules = ["date"]
isAllDay = True
params = Event.params + [
	"recordedBy",  # _("Woman") | _("Partner")  (R6)
	"flow",  # none | light | medium | heavy
	"mucus",  # dry | sticky | creamy | watery | eggwhite
	"bbt",  # basal body temperature, °C (float or None)
	"opk",  # negative | positive | None
	"sex",  # intercourse occurred today (bool)
	"note",  # symptoms / free text (uses Event.description)
]
```

The `description` field doubles as free-text symptoms, matching how `Event.getTextParts`
renders summary+description. Both event types are `isAllDay = True`, so they respect the
group's time-zone handling like `DailyNoteEvent`/`YearlyEvent`.

### 4.3 Calculation engine (pure functions in `menstrual.py`)

Keep the math as **pure, deterministic, testable** functions (no I/O):

```
computeCycleStats(periodStartJds) -> avgCycle, minCycle, maxCycle
    # length between consecutive period starts; recency-weighted mean for avgCycle;
    # if < 2 starts, fall back to group.cycleLength

predictOvulation(periodStartJd, cycleLength, lutealPhase) -> jd
    # periodStartJd + (cycleLength - lutealPhase)

predictNextPeriod(periodStartJd, cycleLength) -> jd
    # periodStartJd + cycleLength

fertileWindowDays(ovulationJd, mode) -> list[jd]
    # fixed:        ovulation-5 … ovulation  (optionally +1)
    # oginoKnaus:   first = predictedNext - maxCycle + 1  (≈ min window start),
    #               last  = predictedNext - minCycle + 1  (≈ max window end)

dayProbabilityRelativeToOvulation(daysBeforeOvulation) -> float
    # table from §2.3:
    #   -5:0.10  -4:0.16  -3:0.14  -2:0.27  -1:0.31  0:0.33
    #   outside window (≤-6, ≥+1): 0.0  (+1 handled as a user-configurable 0.0-0.08)

probabilityOnDate(jd, group) -> (float, "recorded"|"predicted")
    # 1. find the current cycle: most recent periodStartJd ≤ jd
    # 2. ovulation estimate = recorded ovulationOverride if set (R5),
    #    else predictOvulation(...)
    # 3. return dayProbabilityRelativeToOvulation(jd - ovulationJd)
    #    — note this is a "given intercourse occurred on that day" estimate
```

Calendar days are the unit of granularity; `scal3.cal_types.to_jd/jd_to` handle all
calendar types (the group inherits `EventGroup.calType`).

**Clarity on the probability semantics (R4):** the displayed value is the estimated
probability of pregnancy **given intercourse on that specific day**, taken from the
Wilcox day-specific table. Because the table's own model caps the per-cycle chance at
~0.37 (cycle viability), the UI offers a display option to either (a) show the raw
day-specific value (e.g. 27 %) or (b) multiply by an optional viability factor. The
default is (a), matching public calculators. The label text must be explicit, e.g.
`_("~27 % chance of pregnancy if intercourse occurs today")`.

### 4.4 Cell rendering (per-day phase, fertile window, probability)

Occurrence sets (`JdOccurSet`/`IntervalOccurSet`) only say *which* days an event
applies to — they cannot carry a per-day percentage. To show phase, fertile-window
marking, and the daily probability, the feature needs the per-cell hook used by the
pray-times plugin:

- `Cell.__init__` calls `plug.updateCell(self)` for every active plugin
  (`scal3/cell.py:88-95`); plugins annotate via `c.addPluginText(self, text)`
  (`cell.py:102`), and `c.getPluginsText()`/`getPluginsData()` feed the day/plugins
  views (`scal3/ui_gtk/pluginsText.py`, `starcal_funcs.py`).

Proposed renderer (a small plugin under `plugins/menstrual/`, or a core-registered
`updateCell` handler for `MenstrualCycleGroup`):

```python
def updateCell(c):
    for each MenstrualCycleGroup g:
        prob, kind = g.probabilityOnDate(c.jd)  # §4.3
        if prob is None and c.jd not in period days:
            continue
        # phase: "period" | "fertile" | "ovulation" | "safe" | "unknown"
        phase = g.phaseOnDate(c.jd)
        c.addPluginText(self, formatCellText(phase, prob))
        # distinct shading for recorded vs predicted:
        c.setPhaseColor(phase, recorded=kind)
```

Color legend (recorded = solid, predicted = hatched/dashed):
period **red**, fertile window **yellow/amber** (darker on peak days), ovulation day a
distinct marker (e.g. `◉` or bold), safe days default. This satisfies **R7**.

### 4.5 Manual adjustment (R5)

- **Group editor** (`scal3/ui_gtk/event/group/menstrual.py`): cycle length + auto/off,
  luteal phase, period length, window mode, prediction toggles, person name.
- **Period event editor** (`scal3/ui_gtk/event/event/menstrual.py`): the date rule is
  the period-start date; an `actualCycle` spin shows the measured length (editable);
  an "Ovulation day" date picker sets `ovulationOverride` per cycle.
- **Fast log-in:** the day-context menu (or a dedicated action on the group) offers
  "Mark as period start" and "Log observation for this day", reusing the existing
  group actions mechanism (`EventGroup.actions`, wired via `setActionFuncs`).
- **Recalculation triggers:** `afterModify()` hooks recompute cycle stats and
  `updateSummary()` on derived labels (pattern: `UniversityTerm.afterModify()`).
- Any override is stored as a parameter (not a separate event), so predictions remain
  deterministic and reproducible.

### 4.6 Observations by woman or partner (R6)

- One `MenstrualObservationEvent` per day per person; `recordedBy` distinguishes
  woman vs. partner. The partner can therefore log on their own StarCal profile/account
  sharing the same group, or directly when both use the same install (each partner = one
  `MenstrualCycleGroup`, **R8**).
- Observations are plain events, so they sync/export through the existing account/VCS
  machinery, appear in day views via `getEventsData()`, and are editable like any event.
- Observation days can cross-check predictions: e.g. `opk=positive` or
  `mucus=eggwhite` feed a hint ("suggests ovulation may be imminent/occurred") but never
  overwrite the calendar estimate silently — the user confirms via `ovulationOverride`.

### 4.7 Tests (`scal3/event_lib/menstrual_test.py`)

Follow `events_test.py` conventions and the `CLAUDE.md` rules:

- Use the `fs` pytest fixture; `Handler().init(fs)`; never `event_lib.init()`.
- Pure math: `computeCycleStats`, `predictOvulation`, `fertileWindowDays`,
  `dayProbabilityRelativeToOvulation` (table values, edges, irregular mode).
- Event behavior: `createEvent(fs, "menstrualPeriod")` → set date, check
  `calcEventOccurrenceIn` returns `periodLength` days; round-trip `getDictOrdered()`
  /`setDict()` (assertExportRoundtrip); `setJd`/`getJd`; `copyFrom`.
- Group behavior: create group, record 3 period starts, assert predicted period /
  ovulation / fertile window advance by `cycleLength`; override ovulation; toggle
  auto-cycle; verify `probabilityOnDate` for key days (−5 → 0.10, 0 → 0.33, +1 → ~0).
- Observation event: round-trip all params, `recordedBy` values.
- Use `jd(…)` helpers as in `events_test.py`.

### 4.8 i18n

All new desc/labels/strings wrapped in `_()`; add source strings to `locale.d/en.po`
and regenerate `locale.d/fa.po`. Include the medical disclaimer string.

______________________________________________________________________

## 5. Milestones

1. **Core model:** `menstrual.py` group + period event + observation event, pure
   calculation functions, registration import; `menstrual_test.py` (pure math + events).
   — **done**
1. **Editors:** group/event widgets + loader entries; basic create/edit/log workflows.
   — **done**
1. **Cell rendering:** per-day phase color + probability text hook (recorded vs.
   predicted distinction); fast "mark period" / "log observation" actions.
   — **partially done:** phase icons (`menstruation.svg`, `fertile.svg`, `ovulation.svg`) are
   shown via derived events without changing cell color; "mark period"/"log
   observation" quick actions and a dedicated per-day probability plugin hook are
   future work.
1. **Refinements:** oginoKnaus irregular mode, viability-factor display option,
   observation cross-check hints, multi-person UX polish.
   — oginoKnaus mode and the viability factor are done.
1. **Docs & i18n:** update `event_lib/README.md`, release note; compile translations;
   final `ruff format` + `ruff check`.
   — README updated; translation template regeneration is still open.

______________________________________________________________________

## 6. Open questions

- **Where the renderer lives:** a separate plugin (`plugins/menstrual/`) vs. a
  core `updateCell` hook for the group — the plugin keeps core smaller and mirrors
  pray-times; the core hook avoids plugin registration. (Default: plugin.)
- **Probability display:** raw Wilcox day-specific value vs. viability-scaled value;
  both are offered, but which is the default shown in cells vs. the day-info panel?
- **Observation granularity:** one event per day is simple but noisy for 3+
  years; consider batching observations per cycle (a JSON list on a per-cycle object)
  later. Not required for v1.
- **Multi-user sync:** how should two partners' separate groups behave when synced via
  the starcal/google account? Out of scope for v1; note in docs.
- **ICS export:** v1 marks recorded period/observation events (already supported by the
  `DailyNoteEvent`-style `getIcsData`); predicted/fertile days are calendar-internal and
  not exported by default.

______________________________________________________________________

## 7. References

1. Wilcox AJ, Weinberg CR, Baird DD. *Timing of Sexual Intercourse in Relation to
   Ovulation — Effects on the Probability of Conception…* N Engl J Med
   1995;333:1517–21. (Day-specific probabilities 0.10→0.33; 6-day window; cycle
   viability ≈ 0.37.) — https://www.nejm.org/doi/full/10.1056/NEJM199512073332301
1. Dunson DB, Baird DD, Wilcox AJ, Weinberg CR. *Day-specific probabilities of clinical
   pregnancy based on two studies with imperfect measures of ovulation.* Hum Reprod
   1999;14(7):1835–9. (Peak on day −1/−0; 6-day fertile interval.)
1. Johns Hopkins Medicine — *Calculating Your Monthly Fertility Window* (calendar,
   mucus, BBT methods; fertile window ≈ 7 days). —
   https://www.hopkinsmedicine.org/health/wellness-and-prevention/calculating-your-monthly-fertility-window
1. Planned Parenthood formula for variable cycles (via
   https://scienceinsights.org/how-to-calculate-ovulation-and-your-fertile-window/ ).
1. calculator.net — *Ovulation Calculator* (cycle tracking; day 10–18 fertile). —
   https://www.calculator.net/ovulation-calculator.html
1. miniwebtool — *Ovulation / Fertility Calculator* (ovulation = cycle − luteal phase;
   luteal 10–16 d, default 14; window = −5…+1). —
   https://miniwebtool.com/ovulation-calculator/ , https://miniwebtool.com/fertility-calculator/
1. medplore — *Free Ovulation & Fertility Tracker* (feature survey of period-tracker
   apps). — https://medplore.com/health-tools/ovulation-fertility-period-calculator/
1. Bigelow JL, et al. *Mucus observations in the fertile window: a better predictor of
   conception than timing of intercourse.* Hum Reprod 2004;19(4):889–92. (via
   Semantic Scholar).
1. Natural Cycles / NHS references on cycle variation and luteal phase (10–16 d). —
   https://www.naturalcycles.com/uk/cyclematters/period-calculator

*Disclaimer for this document: menstrual-cycle predictions are estimates and are not
suitable as contraception. This document is a software-design proposal, not medical
advice.*
