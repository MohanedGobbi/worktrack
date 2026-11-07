---
version: 1
slug: "templates-pages-task_detail-html"
primary_target: "templates/pages/task_detail.html"
related_targets: ["templates/pages/tasks_list.html", "templates/pages/task_kanban.html", "templates/pages/task_calendar.html"]
---

# Surface: task pages (detail, list, board, calendar)

Mode: Operate. Users: workers (their own tasks) and managers / super admins (all visible tasks), daily, desktop first, phone required.

Constraints: inherits DESIGN.md and the parts built for the two homes (`wt-home-head`, `wt-panel`, `wt-chip`, `wt-up-dot`, `wt-up-bar`, `wt-today-list`, `wt-seg`, `wt-pager`, `wt-avatar`). Presentation only: every route, POST target, AJAX endpoint and form field keeps working. Element ids the scripts use are kept. Arabic-first. No second icon set: Font Awesome only.

## Direction contract

THESIS (detail): "Action rail". The task's own content lives in tabs in the main column; a side rail is led by "Your next step", the one thing this person should do on this task (submit, continue draft, read feedback, start a new version, acknowledge, or, for managers, the review summary), followed by progress, team, information and manage. Refuses the old green banner, countdown boxes and 4-step tracker.

LIST: one filter bar, a List / Board / Calendar switch shared by the three views, one results list (module dot, people, due date amber when overdue, status, progress, done toggle), server-side pages.

BOARD: one column per status (Not started, In progress, Submitted, Sent back, Done, Overdue); managers move cards by drag or the card's "Move to" menu.

CALENDAR: FullCalendar themed from tokens; amber only for overdue and sent back; list view on phones.

FORM (detail): "Action rail", chosen by the user on 2026-11-07 from two options (action rail, single reading column) offered through the structured question tool. seed: none (no concept roll; options written by hand). The list, board and calendar follow the established patterns without a separate choice.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict and DESIGN.md.
