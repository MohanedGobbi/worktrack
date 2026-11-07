# Handoff: WorkTrack Pro UI rework

Last updated: 2026-11-07. Read this first, then `PRODUCT.md` (product truth) and `DESIGN.md` (the design system).

---

## 0. Release plan (start here)

Goal: an installable, sellable v1 as fast as possible, spending tokens only where they change the product. Agreed with the owner on 2026-11-07. Work one sprint per conversation: open a new session, say "Read HANDOFF.md, do Sprint N", and update this section when a sprint ends.

### Working rules (to save tokens)
- **One sprint per session.** Long conversations are the main cost; start fresh and rely on this file.
- **No layout questions** except for pages people use all day. Everything else uses the established parts (`wt-home-head`, `wt-panel`, `wt-filters`, `wt-tl-*` list rows, `wt-td-*` detail layout, `wt-tf-*` forms; see DESIGN.md and §5).
- **Verify in batches:** `manage.py check`, the smoke test (§4) and the tests after each page; one visual pass (EN + AR, 1440 + 390) at the end of the sprint, not per page. Screenshots only when something looks broken.
- **One independent review per sprint**, not per page.
- **Mechanical restyles may go to a cheaper model**; keep security, Site Settings and anything touching data with the strongest model.
- Commit after each page; push only when the owner asks.

### Sprint 1: sale blockers
1. **Server-side cleaning of user text.** Message content is stored raw; the messenger now sanitizes on screen, but the server should too (messages, task comments, submission notes and feedback, todo text, correspondence). Then grep every template and script for user data inserted with `innerHTML` / `|safe` and fix what is found.
2. **Production readiness:** fix the 2 failing tests (`tests.test_creation_fix`: static manifest during tests, and `task_create` crashing on a non-numeric `estimated_hours`); check `DEBUG`, `ALLOWED_HOSTS`, `collectstatic` with the manifest storage, secret key from `.env`.
3. **Translation table:** owner decision pending. Proposal: delete the 3,185 machine rows (`TranslationItem` with key starting `auto.`); template pairs already carry both languages.
4. **Site Settings rebuild** around the theme model: product name EN/AR, logo, brand / accent / on-brand colours (plus preview), contact and footer details, default language. Replace the old ~40-colour editor. This is what makes the product white-label.
5. **"New institution" management command:** name, logo, colours, default language, roles, departments, first admin user.

### Sprint 2: finish Phase 1
`notifications`, `profile`, `worker_performance`, built from the existing parts, no layout questions.

### Sprint 3: triage the ~37 remaining pages (owner picks the hide list first)
- **Rebuild (about 8, daily manager use):** `manager_portal`, `kpi_dashboard` + `manager_analytics` (consider merging), correspondence list / detail / form, `attendance/*`, `admin_users` + `create_user`.
- **Restyle with shared CSS only (about 15):** archives, `global_map`, template dashboard / form / builder, `translation_manager`, `host_management`, `audit_logs`, `offline_map_manager`, `version_data_archive`, groups, `todo_management`, `organizational_intelligence`, `roadmap`, `messaging/config`, `messaging/inspect_user`. Use one "legacy bridge" block in `app.css` that maps their old classes onto tokens, rather than rewriting their HTML.
- **Hide for v1:** whatever the owner does not need yet. Hide through sidebar visibility (data, `SidebarVisibilityRule`), not by deleting code.
- Also: the home dashboard's module toolbar row and table view (still legacy).

### Sprint 4: release
- One independent review over everything rebuilt since the worker home (tasks, submissions, module page, messenger, Sprint 2 and 3 pages); fix what it finds.
- Install checklist for cPanel/Passenger (subpath, cookies, static, media, backups, first admin) and a demo-data seed so the product demos well.
- Tag `v1.0`.

### After launch (not before)
Glossary / terminology table, editable landing and sign-in copy, the University of Ghardaia theme and content, a full messenger rebuild on `wt-*` parts (it still uses the local Tailwind file), brand-derived Signal Blue.

### Decisions waiting on the owner
- The list of pages / features to hide for v1.
- Yes / no on deleting the machine-made translation rows.

---

## 1. What this project is

**WorkTrack Pro** is a Django 5/6 + DRF task and workforce platform: modules → tasks → versioned submissions → manager review → automatic KPI score, plus messenger, correspondence, attendance and notifications. It is bilingual: Arabic first, English, with full RTL.

- **It is a ROWD Tech product.** The default theme follows the ROWD brand guideline (`D:\rowd tech stuff\rowed brand guidline.pdf`).
- **It is white-label.** Each customer install swaps the name, logo and colours. Only the "Built by ROWD" credit is fixed.
- **Backend stays Django.** The front end uses server-rendered templates with no Node build (npm is broken on the dev machine and cPanel hosts have no Node). three.js, GSAP and Lenis load as static ES modules and scripts.

## 2. Where the work stands

| Area | Status |
|---|---|
| Theme system (tokens, fonts, Bootstrap re-skin, white-label inputs) | Done |
| App shell (sidebar, top bar, phone bar and tab bar, toasts, search, confirm dialog, notes drawer) | Done |
| Landing page `/` (3D stack + scroll story, sign-in built in) | Done, reviewed |
| Sign-in, register, 4 password-reset pages, CSRF page | Done |
| Manager/admin home `/dashboard/` ("Roadmap first") | Done, reviewed: **ship** |
| Worker home `/worker-portal/` ("Due list first") | Done, reviewed (see `.impeccable/surfaces/templates-pages-worker_portal-html.md`) |
| Old green/crimson design, old banner images, old CSS files | Removed |
| ~55 other pages | **Theme applied, but old layouts and inline styles remain** |

### Next, in priority order
1. ~~Set up git~~ Done (branch `main`).
2. **Phase 1, daily work:**
   - ~~`worker_portal.html` (the worker home)~~ Done
   - tasks: ~~`tasks_list`, `task_detail`, `task_kanban`, `task_calendar`, `task_form`~~ Done (independent review skipped at the owner's request; run one before calling them finished).
   - ~~submissions: `submissions_list`, `submission_detail`, `submission_form`, `submission_versions`~~ Done (no independent review yet). Review scores are now 0–100, matching `Submission.score` and the KPI engine.
   - ~~`module_dashboard`~~ Done ("Task timeline first"; no independent review yet)
   - ~~`messaging/messenger_page`~~ Hardened in place (not rebuilt): message HTML sanitized, Font Awesome icons, subpath-safe URLs, translation kept off user text. It still uses the local Tailwind file for layout.
   - `notifications`, `profile`, `worker_performance`
3. **Phase 2, manager tools:**
   - `manager_portal`, `manager_analytics`, `kpi_dashboard`
   - modules: `module_form`, `available_modules`, `archived_modules`
   - groups: `group_management`, `group_form`
   - templates: `template_dashboard`, `template_form`, `template_builder`
   - `todo_management`, `organizational_intelligence`, `roadmap`
   - correspondence: `administrative_correspondence`, `correspondence_detail`, `correspondence_form`
   - `global_map`, `version_data_archive`, `attendance/*`
   - the dashboard's **module toolbar row and table view** (still legacy)
4. **Phase 3, admin:**
   - `admin_dashboard`, `admin_users`, `create_user`, `system_profiles`
   - **`site_settings`**: rebuild around the new theme model (name, logo, brand, accent, on-brand); it still shows the old ~40-colour editor
   - `translation_manager`, `host_management`, `audit_logs`, `offline_map_manager`, `contact_admin`
   - `messaging/config`, `messaging/inspect_user`
5. **Customization (see 2b):** build the glossary, editable landing copy, Site Settings rebuild and a new-institution seed command; then the Ghardaia version.
6. **Per page, as each one is done:** delete its legacy `<style>`/`extra_css` block and inline colours; use the `wt-*` primitives; check EN + AR, desktop + phone; get an independent review.

### Open issues (not yet fixed)
- **Translation table quality.** 3,185 of 3,198 `TranslationItem` rows are machine-generated (`key` starts with `auto.`), and many are wrong (for example "My Performance" → "لي", "Overdue Tasks" → "مهام"). Template-authored bilingual pairs are now protected (see §5), but single-language text still gets these rows. This needs a cleanup or regeneration decision from the owner.
- **Signal Blue is not a brand input.** If a customer sets a non-blue brand colour, links, focus rings, the top 3D slab and the banner glow stay blue.
- **Super Admin role badge is red** (on the admin pages).
- **`templates/messaging/messenger.html`** is not referenced anywhere (probably dead).
- **Demo data is thin.** 5 modules, only 1 with dates, no submissions awaiting review. Seed richer data to test the roadmap and "Needs you". (Worker `tester@test.local`, pk 165, now has 8 dated demo tasks covering every worker-home group, one sent back and one waiting for review.)
- **Notes for workers.** The todo endpoints (`corr_todo_*`) were manager-only, so the shell notes drawer never worked for workers. Now `_can_use_todos` lets anyone manage their own general (module-less) notes; module to-dos stay manager-only. Managers can still edit any todo by id (pre-existing, unchanged).
- **Stale demo passwords.** The accounts in `docs/guides/USER_CREDENTIALS_REFERENCE.md` no longer match the database.

## 2b. Customization requirement (applies to ALL remaining work)

After the base platform is finished, the owner will supply details for a **University of Ghardaia version**, and later versions for **other institutions**. So every page built from now on must be customizable by configuration, not by editing templates.

**Exception: the ROWD Tech credit is permanent.** It must appear on every install, in every institution's version (University of Ghardaia included), on all public pages and in the app shell (sidebar and footer). It is never configurable, hideable, replaceable or themeable: no Site Settings field, no theme variable, no CSS that hides it. It lives in `templates/includes/rowd_credit.html`, is shielded from translation (`translate="no"`), and is guarded by `tests/test_credit.py`. Run `manage.py test tests.test_credit` before shipping any new version. Do not remove the test.

Rules for every page and component:
1. **No institution-specific text, logo, colour, font, image or URL hard-coded in templates, CSS or JS.** Name, logo, colours, language defaults, contact details, footer text and landing copy (everything except the ROWD credit) come from Site Settings / `SiteConfiguration` or a theme file.
2. **Labels and vocabulary are swappable.** Institutions use different words (module / course / project, worker / employee / staff, manager / head of department). Route such terms through one glossary (to be created: a per-install terminology table read by templates) instead of writing them inline.
3. **Roles, departments and sidebar items are data**, not code (already partly true: `SidebarVisibilityRule`, `SystemProfile`, `Department`). Keep it that way.
4. **Landing and sign-in copy is editable** from Site Settings (headline, tagline, feature points), with Arabic and English fields.
5. **Theme = one file + 3 settings.** Rebrand by logo + name + brand/accent colours; a deeper restyle by a new `theme-<name>.css`. Do not add per-customer overrides to `app.css`.
6. **Per-install content lives outside the repo** (uploads, `.env`, Site Settings rows), so one codebase serves every institution.
7. **Check each finished page** with a second test theme (different brand colour, logo and name) before calling it done.

Planned work for this: (a) a terminology/glossary table and template tag; (b) editable landing/sign-in copy and contact/footer fields in Site Settings; (c) rebuilt Site Settings around the new theme model; (d) derive Signal Blue from the brand colour; (e) an install checklist and a "new institution" seed command (name, logo, colours, default language, roles, departments); (f) a University of Ghardaia theme and content pass once the owner provides the details.

## 3. Decisions already made (do not reopen without the owner)
- The old CNDP crimson design, the green "editorial" spec and the old agent system prompt were deliberately deleted.
- ROWD is the default theme. **The theme layer is swappable; the ROWD credit is fixed** (`templates/includes/rowd_credit.html`, shielded from translation with `translate="no"`).
- Arabic font: **Thmanyah** (Sans for UI, Serif Display for public headlines), copied from the owner's نبض اليوم project. Latin: Montserrat Alternates (display), Montserrat (body), IBM Plex Mono (data only).
- **3D only on public pages** (landing, sign-in, register, reset). Working screens stay calm and fast; dashboards get at most subtle touches (satin bar edges, fill animation).
- react-three-fiber and Vanta were deliberately not used (they need React/Node or an old three.js).
- Dashboard layout: the owner picked **"Roadmap first"** on the decision page.
- On bilingual pairs, templates beat machine translations (§5).

## 4. How to run and test

```bash
# from the project folder
.venv/Scripts/python manage.py runserver 127.0.0.1:8000
.venv/Scripts/python manage.py check
```
- **Python environment:** `.venv` uses Python 3.12 with `requirements.txt` installed (Django 6.0.10 resolved from `>=5.0`).
- **Desktop app launcher:** `../.claude/launch.json` defines `worktrack` (port 8000) and `worktrack-8001` (use it when another session already holds 8000). Auto-reload is on; if a page renders with an empty context after many quick edits, restart the server.
- **Database:** SQLite `db.sqlite3`. It holds demo data plus `SiteConfiguration.theme_preset='rowd'`.
- **Signing in for local testing:** the demo passwords are stale (§2). Create a session for an existing user in the shell and set it as the `sessionid` cookie in the browser. **Delete the session afterwards**, because it works as a real login.

```python
# manage.py shell
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY
from users.models import CustomUser
u = CustomUser.objects.filter(role='super_admin', is_active=True).first()
s = SessionStore(); s[SESSION_KEY] = str(u.pk)
s[BACKEND_SESSION_KEY] = 'django.contrib.auth.backends.ModelBackend'
s[HASH_SESSION_KEY] = u.get_session_auth_hash(); s.create(); print(s.session_key)
# afterwards: Session.objects.filter(session_key=...).delete()
```

- **Smoke test** (renders key pages for every role plus the public flows). Run it with `manage.py shell -c "exec(open('smoke.py').read())"`:

```python
from django.test import Client
from django.conf import settings
from users.models import CustomUser
settings.ALLOWED_HOSTS = ['*']
paths = ['/dashboard/', '/tasks/', '/notifications/', '/profile/', '/messaging/', '/manager-portal/',
         '/worker-portal/', '/modules/available/', '/templates/', '/attendance/', '/manager-analytics/',
         '/worker-performance/', '/admin-dashboard/', '/messaging/config/']
bad = []
for role in ('super_admin', 'manager', 'worker'):
    u = CustomUser.objects.filter(role=role, is_active=True).first()
    c = Client(HTTP_HOST='127.0.0.1'); c.force_login(u)
    for p in paths:
        r = c.get(p, follow=True)
        if r.status_code >= 500: bad.append((role, p, r.status_code))
c = Client(HTTP_HOST='127.0.0.1')
for p in ('/', '/login/', '/register/', '/password_reset/', '/password_reset/done/', '/reset/done/', '/reset/x/y/'):
    if c.get(p).status_code >= 400: bad.append(('anon', p))
print('PROBLEMS', bad)
```

## 5. How the new system works (map)

### Theme layer (swap this to re-theme)
- `static/wt/theme-rowd.css`: `@font-face` rules + tokens (`--wt-*`). Re-theme = copy it, then point the `<link>` in `templates/includes/wt_theme.html` at the copy.
- `templates/includes/wt_theme.html`:
  - injects the per-install brand inputs from Site Settings (`--wt-brand`, `--wt-accent`, `--wt-on-brand`, `--wt-brand-rgb`);
  - defines legacy variable aliases (`--color-primary` and others) so old pages follow the theme;
  - defines the page-banner surface `--wt-hero-bg`, which uses an uploaded Site Settings banner under a brand overlay if one exists.
- `core/context_processors.py`:
  - `_wt_theme`: brand inputs from the `rowd` preset, or the admin colours under the `custom` preset;
  - `_logo_tone`: measures the uploaded logo's brightness so it gets a readable backdrop;
  - `_wt_lang`: first-render language and direction, so pages don't flash LTR.
- `core/models.py` + migration `0025_rowd_theme_preset`: `rowd` preset added and made the default.

### Component layer
- `static/wt/app.css`:
  - derived tokens (`color-mix`) and the Bootstrap bridge;
  - the shell, overlays and Bootstrap re-skin;
  - shared primitives: `.wt-panel`, `.wt-panel-head`, `.wt-chip`, `.wt-count-pill`, `.wt-empty`, `.wt-page-head`, `.wt-num` (LTR-isolated numbers);
  - home styles: `.wt-home*`, `.wt-road*`, `.wt-need*`, `.wt-today*`;
  - module cards `.wt-mcard*` and the bulk bar `.wt-bulkbar`.
- `templates/base.html`: the new shell. It keeps every legacy hook: `.neural-sidebar`, `toggleNeuralSidebar`, `openSearch`, `#notif-badge`, `#banner-messenger-badge`, `amazingConfirm`, `showToast`, `#moduleSidebar`, `#lang-switcher`, `.global-path-tracker`, `.dashboard-main-area`.

### Public surfaces
- Templates: `templates/public/` (`landing.html`, `auth_base.html`, `_head.html`, `_header.html`, `_signin_stack.html`) + `templates/auth/*` + `templates/403_csrf.html`.
- Styles: `static/wt/public.css`.
- `static/wt/js/stack-scene.js`: three.js orthographic scene in CSS pixels; 3D modules align to DOM slots `[data-slot]`; scroll choreography; reduced-motion and no-WebGL fallbacks.
- `static/wt/js/public.js`: Lenis + GSAP intro, password reveal, submit loading state.
- Home view `core/template_views.py::home`: landing for visitors (with live KPI weights); a POST still signs in.

### Home (dashboard)
- `templates/includes/wt_home_top.html` (greeting, roadmap, Needs you, Today) is included from `templates/pages/dashboard.html`.
- Data: `core/template_views.py::_wt_home_context` (read-only).
- Roadmap dates are real dates clipped to the current year; undated modules render as ghost rows.

### Translation behaviour (changed)
- `core/middleware/main.py::DynamicTranslationMiddleware`, for template `lang-en` + `lang-ar` pairs:
  - matching uses the **English** side only;
  - machine `auto.` rows are ignored;
  - English casing from the template is kept when the DB differs only by case;
  - elements with `translate="no"` are never rewritten.
- `static/js/i18n.js`:
  - the language switcher is now `.wt-lang` buttons;
  - the Google Cairo font import is removed;
  - it respects `translate="no"`;
  - the DB map fetch (`/translations/api/map/`, never routed) is disabled.

### Design-process artifacts
- `.impeccable/surfaces/*.md`: direction contracts for the landing and the dashboard.
- `.impeccable/review/`: review screenshots.
- `.impeccable/mocks/decision/`: the dashboard layout sketches.

## 6. Gotchas learned the hard way
- **Escaping in scripted edits.** Python string escapes inside shell heredocs turned `\f`, `\b` and `\1` into control bytes twice. That broke `app.css` parsing (everything after the bad rule was ignored) and a middleware regex. Write edit scripts to a file and use `chr(92)` for backslashes, or use a file-editing tool. After any scripted edit, scan for bytes below 0x20.
- **Template cache.** With `runserver --noreload`, Django caches templates, so edits don't show until a restart. The launcher now runs with auto-reload.
- **Asset caching.** Bump the `?v=` cache-busters when editing CSS/JS: `app.css?v=14`, `public.css?v=7`, `i18n.js?v=3.2`, `stack-scene.js?v=2`.
- **Old page scripts write inline styles.** For example, `dashboard.html` set margins on `.dashboard-main-area`. The shell's sidebar offset is therefore padding on `.wt-shell`, not a margin.
- **Old page CSS uses `!important` widely.** Overrides need higher specificity (`.wt-app ...`) or a rebuilt block.
- **`100vw` includes the scrollbar.** Use `%` widths, or RTL pages get sideways scroll.
- **`repeat(12, 1fr)` grids overflow** when labels are wider than columns. Use `minmax(0, 1fr)`.
- **Small browser pane.** The pane can be resized small by the user, which shrinks screenshots. For full-resolution phone captures, emulate 390×330 and stack strips (ffmpeg `vstack`).

## 7. Process used (keep using it)
The **impeccable** design skill drives the work:
1. For big pages, offer 2–3 layout options on its decision page (`concept-seed --scope surface --mode operate`, then `serve-question`).
2. Write the direction contract into `.impeccable/surfaces/`.
3. Build.
4. Verify EN/AR at 1440 and 390.
5. Get an independent finish review (`impeccable-finish-reviewer` agent); fix until the verdict is **ship**.
6. Keep `DESIGN.md` (and `.impeccable/design.json`) in sync.

The owner's stated fail conditions: **too flashy at work, weak Arabic, slow on old PCs.**
