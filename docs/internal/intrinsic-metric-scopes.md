# Intrinsic Metric Scope Model (Internal)

This document defines the implementation contract for intrinsic metric scopes.
It is intended for developers and maintainers, not end users.

## Problem Statement

Today QRiS requires every analysis to be tied to one or more Data Capture Events (DCEs). Each DCE represents a point in time with associated field data. This works well for event-based metrics like "dam count in 2023 survey" but creates unnecessary friction for metrics that do not depend on time or field data at all.

Examples of time-independent metrics:

- Centerline length through a sample frame
- Valley bottom area
- Gradient from centerline and DEM
- Integrated width (area / length)

These are already defined in the System Protocol (`riverscape_system_protocol.xml`) but today they still require a DCE to calculate. Users want to get these values quickly without the overhead of creating events or assigning protocols.

## High-Level Goal

Let users create a simplified "intrinsic" analysis that only requires a sample frame, centerline, valley bottom / riverscape, and DEM — no events, no protocols, no field data. The same analysis engine and storage model should support both event-based and intrinsic workflows side by side in one project.

## Design Assumptions

1. No database migration for v1. Scope is stored in the existing JSON metadata column (`analyses.metadata`), under `system.scope`. This matches QRiS convention: `system` holds QRiS-controlled values, `metadata` holds user values, `attributes` holds feature data.

2. One analysis class, two UX modes. Both Simple (intrinsic) and Advanced (event-based) analyses use the same `Analysis` model class and the same `metric_values` table. The UX mode is a flag (`system.analysis_mode`) that controls what the UI shows, not a different data model.

3. Intrinsic metrics are input-based, not DCE-layer-based. They reference analysis metadata keys (centerline, valley_bottom, dem) rather than DCE layers. This is already how the system protocol defines them.

4. Phase 1 keeps sample frames required. Intrinsic metrics are still calculated per sample frame feature. Whole-analysis intrinsic metrics (no sample frame) are deferred to Phase 2.

5. Future DB migration is possible. If we later need strong uniqueness enforcement at the database level, we can add scope columns to `metric_values` and backfill from the existing JSON. The JSON shape is designed to make this migration straightforward.

6. Mixed analyses are a deferred feature. An analysis can be either event-based or intrinsic in v1, not both. A user who wants both creates two analyses.

## Metadata Conventions

QRiS uses a three-key top-level metadata structure:

| Key | Purpose | Examples |
|-----|---------|----------|
| `metadata` | User-specified values | custom labels, notes |
| `system` | QRiS-controlled values | `locked`, `scope`, `analysis_mode` |
| `attributes` | Feature-level data | not used for analyses |

Scope lives under `system.scope` because it is QRiS-controlled, not user-editable.

## Goal

Support both:

- Event-based metrics (time aware)
- Intrinsic metrics (time independent)

And both:

- Sample-frame metric values
- Whole-analysis metric values

## Scope Dimensions

Every metric value is identified by two explicit dimensions.

- Temporal scope
  - `event`
  - `intrinsic`
- Spatial scope
  - `sample_frame`
  - `analysis`

## Canonical Identity

Each metric value must be uniquely addressable by:

- `analysis_id`
- `metric_id`
- `temporal_scope_type`
- `temporal_scope_id`
- `spatial_scope_type`
- `spatial_scope_id`

Notes:

- `*_scope_type` is an enum-like text field.
- `*_scope_id` meaning depends on the corresponding `*_scope_type`.
- Do not use null semantics as the identity mechanism.

## Allowed Combinations

These combinations are valid:

- `event` + `sample_frame`
- `event` + `analysis`
- `intrinsic` + `sample_frame`
- `intrinsic` + `analysis`

Phase guidance:

- Phase 1 implementation target: `intrinsic` + `sample_frame`
- Phase 2 implementation target: `intrinsic` + `analysis`

## Scope ID Rules

- If `temporal_scope_type = event`, then `temporal_scope_id` is an `events.id` value.
- If `temporal_scope_type = intrinsic`, then `temporal_scope_id` is a reserved intrinsic scope key.
- If `spatial_scope_type = sample_frame`, then `spatial_scope_id` is a `sample_frame_features.fid` value.
- If `spatial_scope_type = analysis`, then `spatial_scope_id` is a reserved analysis scope key.

Reserved key recommendations:

- `temporal_scope_id = 0` for intrinsic
- `spatial_scope_id = 0` for analysis-wide

## Behavioral Rules

- Intrinsic values are not filtered by selected events unless explicitly requested.
- Event-based charts should not implicitly include intrinsic values.
- Exports must include scope labels so rows are unambiguous.
- Re-running calculations for the same scope identity must upsert, not duplicate.
- All scope reads and writes go through `Analysis` helper methods, never through raw JSON access.
- `DBItem.set_metadata()` normalizes the three standard sections (`metadata`, `system`, `attributes`) so subclasses can safely mutate `self.system_metadata` without worrying about detached dicts.

## Non-Goals

- This document does not prescribe final table or index names.
- This document does not prescribe migration batching strategy.
- This document does not define UI wireframes.

## Acceptance Criteria

The scope model is considered locked when:

- Maintainers approve this contract.
- Migrations and refactors reference this document.
- No implementation introduces conflicting scope semantics.

## Product Decision: Simple Analysis v1

Status: Approved

- Simple Analysis v1 is intrinsic-only.
- Event metrics are deferred to a later phase.

Rationale:

- Keeps the first release easy to learn and teach.
- Reduces risk by avoiding mixed-scope table and chart behavior in v1.
- Allows backend scope model work to proceed without immediate mixed-UI complexity.

v1 UI boundaries:

- Hide event selection in Simple Analysis.
- Show intrinsic and system metrics only.
- Keep advanced event-based workflows in the existing Analysis form.

Deferred items (post-v1):

- Optional mixed-scope comparison views.
- Event metrics visibility inside Simple Analysis.
- Whole-analysis intrinsic metrics.

## Implementation Strategy: JSON-First (v1)

v1 stores scope metadata in `system.scope` inside the analysis JSON metadata column. No database migration is needed for v1.

### JSON shape

```
{
  "system": {
    "scope": {
      "version": 1,
      "temporal": { "type": "event|intrinsic", "id": 0 },
      "spatial": { "type": "sample_frame|analysis", "id": 0 }
    },
    "analysis_mode": "simple_intrinsic"
  }
}
```

### Why JSON-first for v1

- No migration risk for existing projects.
- All scope logic is centralized in `Analysis` helpers in `src/model/analysis.py`.
- Future DB migration can backfill from JSON with no data loss.

### What code implements this

- `src/model/analysis.py`: `get_scope()`, `set_scope()`, `validate_scope()`, `is_simple_intrinsic_mode()`
- `src/model/db_item.py`: `set_metadata()` normalizes `system`/`metadata`/`attributes` sections

### Future migration path (post-v1)

When scope needs strong DB-level uniqueness guarantees, add scope columns to `metric_values` via migration and backfill from JSON.
