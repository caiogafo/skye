---
inclusion: fileMatch
fileMatchPattern: 'tests/**|docs/**|.kiro/specs/**|.kiro/steering/**'
---

# Repository conventions: tests, docs, specs, steering (Skye)

## Steering file names: `NN-topic.md`
The name says where the file applies; the front matter `inclusion` says when it loads; the number is the group and reading order.
Add a file to the right group; do not invent a prefix. Keep the set small: merge before adding.

| Code | Group | `inclusion` | Files |
|---|---|---|---|
| `00` | project rules | `always` | `00-rules` (keep it short: budget in `tests/budget/test_steering.py`) |
| `1x` | high-level view | `manual` | `10-requirements` (Kiro format, EARS), `11-design`, `12-decisions` (decision log and open decisions) |
| `20` | repository areas | `fileMatch` | `20-repo` (this file: `tests/**`, `docs/**`, `.kiro/specs/**`, `.kiro/steering/**`) |
| `30` | component code | `fileMatch` | `30-code` (`models`, `tools`, `gateway`, `auth`) |

## Where things live
| What | Where | Rule |
|---|---|---|
| Requirements (what the system must do) | `10-requirements.md`, Kiro format: user story plus EARS acceptance criteria | the only place; numbered `Requirement N` |
| High-level design (layers, allowed imports, Ports, composition, extension points) | `11-design.md` | the only place for the system-level view |
| Decisions, taken (D1...) and open (O1...) | `12-decisions.md` | a decision is never rewritten: a later one supersedes it |
| Detailed design of one component | `.kiro/specs/<component>/design.md` | refers to the components and sections of `11-design.md` |
| Tasks | `.kiro/specs/<component>/tasks.md` | only here, never in steering |
| User stories of one component | `.kiro/specs/<component>/requirements.md` | repeats the story, cites the requirement numbers |

## Canonical names for specs
- **Spec name = component name**, exactly, lower case: `.kiro/specs/models/`, `.kiro/specs/auth/`. No suffix, no prefix, no `-support`,
  `-engine` or `-runtime`. The 15 names are in Requirement 1; there is no spec with another name. Specs are never archived or deleted.
- **The one exception is `structure`**, the cross-cutting spec. It holds the work that belongs to no single component: the system
  structure, the documentation wiki and the old consolidation work, all inside its own three files and with no subfolder. Its tasks are
  numbered groups (`structure` group 11 is the wiki).
- **Files** are exactly `requirements.md`, `design.md`, `tasks.md` (Kiro's three). No other file is a source of truth.
- **Front matter** of each spec file: `component: <name>` and `codename: <word>`; `previous_name: <old folder>` while a renamed spec still
  has that history.
- **Tasks** use Kiro's task syntax, because Kiro's tools validate it: a milestone is a top-level task `- [ ] 1. <title>` (or `- [x] 1. <title>`) and
  its tasks are indented sub-tasks `  - [ ] 1.1 <title>`; an optional task adds `*` after the checkbox (`- [ ]* 1.2 <title>`). Numbers are plain
  (`1.`, `1.1`), never `M1` or a component prefix in the line. The **task ID** used to cite a task from another document is `<component>:<N.k>`
  (for example `models:2.3`).
- **Requirements** are cited as `Requirement N` or `Requirement N.k` (the numbers in `10-requirements.md`); decisions as `D<n>`;
  open decisions as `O<n>`.

## Creating a new spec (read this before writing any spec file)
Load `10-requirements.md` and `11-design.md` first (they are `manual`: open them with `#[[file:.kiro/steering/10-requirements.md]]`
and `#[[file:.kiro/steering/11-design.md]]`). One spec = one component, named like the component.
1. **Requirements.** Write the new requirements into `10-requirements.md`, not into the spec: add `### Requirement N: <title>` after the
   last number, with a user story and EARS acceptance criteria, in the same format as the others. Reuse a requirement that already covers
   the need instead of adding a duplicate; edit an existing one only when the rule itself changes. Never renumber existing requirements.
2. **Spec `requirements.md`.** Kiro format, because Kiro's tools need it: `# Requirements Document`, `## Introduction`, `## Requirements`, then
   `### Requirement N: <title>` blocks numbered 1..n, each with `**User Story:**` and `#### Acceptance Criteria`. Our rule on top of the format:
   every criterion is a pointer and nothing else, in one of three exact forms:
   `THE spec SHALL realize Requirement 9.2 of #[[file:.kiro/steering/10-requirements.md]].` or
   `THE spec SHALL honor decision D13 of #[[file:.kiro/steering/12-decisions.md]].` or the history form used in `structure`.
   A real rule is never written in the spec: if a story needs one that steering does not state, go back to step 1. The number in a spec heading
   is local to the spec; the number in a pointer is the steering one. `tests/budget/test_specs_format.py` fails on any other criterion.
   **How to fetch a requirement:** each steering requirement starts at `### Requirement N: <title>` and its criteria are the numbered list under
   `#### Acceptance Criteria`: `grep -n -A25 "^### Requirement 9:" .kiro/steering/10-requirements.md` reads Requirement 9, and `Requirement 9.2` is its
   second criterion. Keep that heading syntax exactly as Kiro writes it, because tools search for it.
3. **High-level design.** If the new component, or a new Port, an allowed import, an extension point or a layer change, alters the
   system view, update `11-design.md` (tables, diagram) in the same change. Do not describe the component's internals there.
4. **Spec `design.md`.** Write only the detailed design of the component and open it with one line in this form:
   `Builds on: #[[file:.kiro/steering/11-design.md]] (sections: Layers, Allowed imports, Ports, Composition)`. Refer to what already exists in
   steering instead of rewriting it. If the design needs something the steering does not say, **change the steering first, then write the spec**.
5. **Spec `tasks.md`.** Milestones in build order, each task citing the requirement numbers it satisfies. Tasks live only here.
6. **Decision.** If the work records a choice the owner made, add `D<n>` to `12-decisions.md` with the requirements it supports.
7. Approve in order: requirements, design, tasks. Add the component to the progression view `.kiro/specs/README.md`.

## Changing something that exists
Steering is always changed before the spec: first `10-requirements.md` or `11-design.md` (with the decision line), then the specs that cite them.
- A rule changes: edit it in `10-requirements.md` and add a decision line; then add a milestone to the tasks of each component that
  cites that requirement number. Do not create a new spec for it.
- The system view changes (layer, allowed import, Port): edit `11-design.md`, add a decision line, and revisit the `design.md` of the
  components named in the changed section.
- A cross-cutting rule (layers, import matrix, names, codenames, budgets): same, in `10-requirements.md` and `11-design.md`.
- **Prompts** in `.kiro/prompts/` are one-off instructions, never a source of truth. A choice made in a prompt is copied to the
  decision log before the prompt is retired.

## Specs: lifecycle
- A task is done when its checkbox is ticked with evidence (a file or a test). A closed milestone is folded away.
- Specs are never archived or deleted: an old or one-off spec is reorganized in place and keeps its history.
- Spec front matter carries the component codename line. The progression view across components is `.kiro/specs/README.md`.

## Tests
- Run with **uv**: `uv run pytest tests/`; coverage `uv run pytest tests/ --cov=src/skye`.
- Layout: `tests/unit` (fast, isolated, mock externals), `tests/integration` (real implementations where possible), `tests/stress`
  (performance), `tests/differential` (built-in against vendor SDK), `tests/fixtures` (shared).
- `tests/budget` holds the deterministic size, load and structure checks. They run on every pull request via the `budgets` workflow and
  stay offline and deterministic (no network, no install in the fast job). The import matrix is `test_import_matrix.py`; the steering
  decisions are `test_steering.py`.
- Aim for 80%+ coverage on core functionality, critical paths first. Use property-based tests where they fit.

## Docs wiki
`docs/` is a wiki: one section per component, section name equal to the component short name, not a flat folder.
- Each section index has one italic line under the title naming the component codename (one of the four sanctioned places).
- One glossary page maps every codename to its plain name and role, lists the documentation-only watermarks (the `Runnable` Port's
  and the project umbrella watermark) separately, and states the `auth` (authentication) vs `policy` (authorization) contrast.
- Every page has front matter (title, status, last_updated, related pages) and is linked from its section index; `docs/index.md`
  reaches every page. The structure and migration plan are in `structure` (group 11 of its tasks).
