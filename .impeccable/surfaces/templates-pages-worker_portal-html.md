---
version: 1
slug: "templates-pages-worker_portal-html"
primary_target: "templates/pages/worker_portal.html"
related_targets: []
---

# Surface: worker home (`/worker-portal/`, `templates/pages/worker_portal.html`)

Mode: Operate. Users: workers (also opened by managers and super admins), every working day, office desktop first, phone required. Job: know what is due, act on what was sent back, read new circulars, then reach modules and history.

Constraints: inherits the ROWD world in DESIGN.md (no new palette, type or controls). Presentation only: every link, the enroll forms (POST `enroll-module`), table pagers and the explore search keep working; element ids `action-tasks`, `my-modules`, `task-directory`, `submission-history`, `resubmission-required`, `circulars`, `explore-standalone-section`, `exploreSearchInput`, pager containers stay. New read-only context may be added to the view. The page's own localStorage notes drawer duplicated the shell's server-backed notes drawer; it is removed, and any notes left in the browser are offered for a one-click move into the shell notes. Arabic-first.

## Direction contract

THESIS: One "Up next" list of the worker's own open tasks, grouped by when they are due, with each task's time used shown as a thin stadium bar. Refuses the old banner + five identical stat cards + six tabs.

OWN-WORLD: DESIGN.md as built, sharing the manager home's parts: `wt-home-head` greeting, `wt-panel`, `wt-chip`, `wt-today` list, `wt-mcard` module cards. Amber only for overdue and sent-back. Mono only for dates and numbers.

STORY: The worker reads the greeting line (how many tasks due this week, how many overdue), works down Up next (Overdue, This week, Later, Waiting for review), clears anything in "Sent back to you", reads unread circulars, then opens a module or checks history. Modules they can join sit last.

FIRST VIEWPORT: Page head (greeting, date and due counts; My performance and All tasks actions). Two columns: Up next at 1.6fr; side column at 1fr with Sent back, Circulars and My progress.

FORM: "Due list first", chosen by the user on 2026-11-07 from three options (due list, personal timeline, single inbox) offered through the structured question tool. seed: none (no concept roll; options written by hand)

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict and DESIGN.md.
