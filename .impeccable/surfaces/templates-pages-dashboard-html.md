---
version: 1
slug: "templates-pages-dashboard-html"
primary_target: "templates/pages/dashboard.html"
related_targets: []
---

# Surface: manager / admin home (`/dashboard/`, `templates/pages/dashboard.html`)

Mode: Operate. Users: managers and super admins, every working morning, on office desktops (phone layout required). Job: see what needs them now, then the state of every module over the year, then manage modules.

Constraints: inherits the ROWD world in DESIGN.md (no new palette, type or controls). Presentation only: module workspace (grid/table, groups, bulk actions, drag reorder) keeps its markup hooks and JS. New read-only context may be added to the view. Arabic-first, RTL mirrors the roadmap (time runs right to left). No 3D on this working screen beyond a subtle satin edge on bars.

## Direction contract

THESIS: The year's modules on one roadmap, with what needs the manager pinned to each module's bar. Refuses the category default of a banner of totals over a grid of identical cards.

OWN-WORLD: DESIGN.md as built: light ground, white ruled panels, Rowd Blue fills, cyan today line, amber only for alerts, Montserrat Alternates numerals, IBM Plex Mono months, Thmanyah in Arabic. Signature: each module's bar is a stadium module whose progress fills it, with attention chips riding at its end.

STORY: A manager reads the greeting line (how many submissions wait), sees each module's place in the year and which ones carry reviews or overdue work, clears the "Needs you" list, then manages modules below.

FIRST VIEWPORT: Page head (greeting, date and review count, New module and New task at the end). Full-width Roadmap panel: module name and tasks done per row, months across, today line, progress-filled stadium bars, chips ("3 to review", "2 overdue"). Below, two columns: "Needs you" list (reviews, overdue tasks, to-dos) at 1.6fr and "Today" summary (completion, waiting for review, overdue, team) at 1fr.

FORM: Roadmap first, dealt lead (index 5 of the grounded list), chosen by the user. seed:b7e18f4e842e5a3b

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
