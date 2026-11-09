# Handoff: WorkTrack Pro UI rework

Last updated: 2026-11-08 (after Sprint 3, cleanup and first push). Read this first, then `PRODUCT.md` (product truth) and `DESIGN.md` (the design system).

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

### Sprint 1: sale blockers — DONE 2026-11-07 (see "Sprint 1 results" below)
1. **Server-side cleaning of user text.** Message content is stored raw; the messenger now sanitizes on screen, but the server should too (messages, task comments, submission notes and feedback, todo text, correspondence). Then grep every template and script for user data inserted with `innerHTML` / `|safe` and fix what is found.
2. **Production readiness:** fix the 2 failing tests (`tests.test_creation_fix`: static manifest during tests, and `task_create` crashing on a non-numeric `estimated_hours`); check `DEBUG`, `ALLOWED_HOSTS`, `collectstatic` with the manifest storage, secret key from `.env`.
3. **Translation table:** owner decision pending. Proposal: delete the 3,185 machine rows (`TranslationItem` with key starting `auto.`); template pairs already carry both languages.
4. **Site Settings rebuild** around the theme model: product name EN/AR, logo, brand / accent / on-brand colours (plus preview), contact and footer details, default language. Replace the old ~40-colour editor. This is what makes the product white-label.
5. **"New institution" management command:** name, logo, colours, default language, roles, departments, first admin user.

### Sprint 1 results
- **Cleaning on save:** `core/sanitize.py` (`clean_text`, `clean_rich`, `script_json`) + `core/signals.py` (`CLEAN_FIELDS`: one map of model → fields, connected in `CoreConfig.ready`). Messages keep the messenger allowlist (b, strong, i, em, br, safe links); everything else listed is plain text. `QuerySet.update()` bypasses it. `manage.py clean_user_text [--apply]` cleans rows saved before (0 rows in the dev DB).
- **Sinks fixed:** emails no longer compile user text as template code (it was server-side template injection); JSON islands use `script_json`; shell search/toast/confirm are text-only (`window.wtEsc` is defined in `<head>` for page scripts); plus the per-page fixes listed in commit `fb06306`. Rule for new code: build HTML with `wtEsc()`/`esc()` or `textContent`, and put institution or user text that sits in `lang-en`/`lang-ar` pairs under `translate="no"` (the translation middleware rewrites matching pairs).
- **Production:** `DEBUG` defaults to False; the server refuses to start without `SECRET_KEY` unless `DEBUG=True` or testing. Local `.env` holds `DEBUG=True` (gitignored). `.env.example` lists every install setting. `collectstatic` works with the manifest storage (tests and DEBUG use plain storage). `ALLOWED_HOSTS` stays `*` by default because hosts are checked by `DynamicHostMiddleware`. On Windows run collectstatic with `PYTHONIOENCODING=utf-8`.
- **Tests:** 73 pass, 1 skipped (sidebar module paging: the feature is not in any template; `base.html` still has its dead JS). Messenger unread count had a real bug on coarse clocks (first message counted as read), fixed in `Message.save`.
- **Translation table:** not touched (owner decision: delete `auto.` rows in Sprint 4). Also found: a row maps "العربية" to `missing_arabic` in English mode; delete it in that cleanup.
- **Site Settings** (`/admin-dashboard/site-settings/`): rebuilt on wt parts. Identity (name EN/AR, logo, banner), Colours ("ROWD default" or "Your colours": brand, accent, text on brand, with swatches and a contrast check), Contact & footer (email, phone, website, address EN/AR, footer line EN/AR, shown on every page through `includes/wt_site_footer.html`), Language & access. Live preview of the shell on the end side. Model fields added in migration 0026 (`on_brand_color` replaces the use of `button_text_color`). The ~40 legacy colour columns remain in the DB but are no longer edited; old pages that still read them keep their current values.
- **`manage.py new_institution`**: `--config file.json` and/or flags; see `docs/institution.example.json`. One transaction, `--dry-run`, safe to re-run, prints a generated admin password once.
- **Independent review** (one for the sprint) found 10 issues; all fixed in the last Sprint 1 commit: `clean_rich` crashed on nested `<svg>/<template>` content; `clean_text` ate text like `x<y` (now only well-formed tags are removed, a stray `<` stays as text); `.env` values for `CSRF_TRUSTED_ORIGINS`/`SECURE_COOKIES` were ignored (read with `os.getenv`); `new_institution --dry-run` wrote the logo file and a given password was silently ignored for an existing admin (now warned; `WT_ADMIN_PASSWORD` env var supported); stored email templates had the first message frozen in (migration `notifications.0005`); global map popups and dashboard calendar titles were unescaped; conversation previews now strip tags; an invalid Site Settings POST showed unsaved values in the shell.
- **Known gap found:** page banners always use white text, so a very light brand colour makes banner text hard to read (the preview shows it). Consider deriving banner text from `--wt-on-brand` when doing the Signal Blue work.

### Sprint 2: finish Phase 1 — DONE 2026-11-08
`notifications`, `profile`, `worker_performance`, built from the existing parts, no layout questions.
- **Notifications** (`/notifications/`): filter bar, day groups (Today / Yesterday / Earlier this week / Older), each row links to its task, submission or correspondence (`_notification_url`), mark read / delete in place. Types and their EN/AR labels and icons: `WT_NOTIF_TYPES` in `core/template_views.py`.
- **Profile** (`/profile/`): identity card + details, password (Django validators, stays signed in), email switches, recent sign-ins. Field errors travel in the session (`pf_errors`) back to the section. Theme/language "preferences" removed (no dark theme; language comes from the switcher).
- **My score** (`/performance/`): KPI engine score for the current month with the install's weights, six calendar months of CSS bars, facts, recent reviews. Managers may pick people from `get_teammates()` only. Linked as "My score" from the worker home and profile, and from manager analytics with `?user_id=`.
- **Still English-only data:** notification titles and messages are written in English by the code that creates them (signals and views). Make them bilingual when the glossary work happens.


### Sprint 3: remaining pages — DONE 2026-11-08 (see "Sprint 3 results" below; follow the owner decisions)
- **Rebuild (about 8, daily manager use):** `manager_portal`, `kpi_dashboard` + `manager_analytics` (consider merging), correspondence list / detail / form, `attendance/*`, `admin_users` + `create_user`.
- **Restyle with shared CSS only (about 15):** archives, `global_map`, template dashboard / form / builder, `translation_manager`, `host_management`, `audit_logs`, `offline_map_manager`, `version_data_archive`, groups, `todo_management`, `organizational_intelligence`, `roadmap`, `messaging/config`, `messaging/inspect_user`. Use one "legacy bridge" block in `app.css` that maps their old classes onto tokens, rather than rewriting their HTML.
- **Hide for v1:** whatever the owner does not need yet. Hide through sidebar visibility (data, `SidebarVisibilityRule`), not by deleting code.
- Also: the home dashboard's module toolbar row and table view (still legacy).

### Sprint 3 results
- **v1 hiding is real now.** `core/features.py`: `feature_required('<key>')` wraps the URLs of the hidden pages (they redirect to the dashboard), and links read `sb_rules.<key>`. Keys: `global_map`, `org_intelligence`, `offline_maps`, `roadmap`, `templates`, `todo_management`, `version_archive`, `host_management`, `messenger_admin` (config + inspect), `translations`. Defaults in `SidebarVisibilityRule.initialize_defaults()` and migration `users.0019`; switch back on in Admin console > sidebar visibility (nothing was deleted). `new_institution` has `hide_sidebar` / `show_sidebar`. The dev DB has triplicate rows for `global_map` and `org_intelligence` (older data); the update works on all of them, but `get_or_create` on those keys would raise MultipleObjectsReturned. Clean them before shipping.
- **Uploads are served safely.** `safe_media_serve` (urls.py) sends nosniff and a CSP without scripts for everything under `/media/`, and makes html/svg/xml/js download. Photos go through `core/uploads.py::process_photo` (decode, re-encode, server-made name). Correspondence files are limited to document types and 25 MB (`core/forms.py::check_documents`). Task attachments and messenger files are still accepted without a type check; they are protected by the serve policy only.
- **Users** (`/management/users/`): list + create/edit on `UserAdminForm`. Role decides `is_superuser`/`is_staff`. Guards: only admin cannot be demoted/deactivated/deleted, no self-deactivate. Sign in as is POST-only.
- **Correspondence** (`/correspondence/...`): list, detail (document viewer, acknowledgements), form. Access via `_corr_visible` / `_can_manage_corr`. The legacy "task of type correspondence" records are still mirrored into `Correspondence` by `_sync_legacy_correspondence` on list load (matches by reference or title); retire that once no install has such tasks.
- **Team** (`/analytics/`, name `manager-analytics`): replaces manager portal, team analytics and KPI dashboard (old URLs redirect; their templates are gone). Scores from `kpi.engine.month_scores` (tested equal to the engine). Team = people who report to the manager or share a work group; admin sees everyone.
- **Audit log** (`/management/audit-logs/`): rebuilt; administrators only (managers lost access, it was never linked for them).
- **Restyle-only pages:** archived modules got the standard page head. Groups, group form and attendance already follow the theme and had no overflow in a phone/Arabic sweep, so the planned "legacy bridge" CSS was not needed; the pages still use old classes inside. Their `<title>` is English only.
- **Dashboard:** the module toolbar and list view work and follow the theme; only the search placeholder and the "Uncategorized" label were made bilingual. A full rebuild of that block (about 700 lines of toolbar and drag-and-drop group JS) was not done; do it with the next dashboard pass if the owner wants it.
- **Independent review of Sprint 3** found 9 issues, all fixed except two noted below. The serious one: the old REST route `/api/users/` let anyone register as an administrator and let a worker PATCH their own role (and any user without a department edit/delete others). Now: writes need an administrator, role / active / department are read-only, `register` is gone, the profile API cannot set manager or photo. The tasks API is writable by managers only (a worker could create, edit and delete tasks). Also fixed: mirrored legacy correspondence came back after deletion (`Correspondence.legacy_task`, migration `tasks.0035` links existing mirrors; delete removes the source task); recipient counts for non-admins (subquery counts); duplicate sidebar rules (migration `users.0020`) and a tolerant `users.0019`; impersonation of deactivated accounts and reverting to a demoted admin; the map tile proxy now needs a login; hidden-feature helper endpoints (translations API, host toggle/delete/whitelist) are gated; Team page counts tasks without a module.
  Not fixed: the last-administrator guard is not atomic (two admins removing each other at the same instant could leave none); the submission and KPI-weight REST viewsets are not mounted but were tightened anyway. **Do a whole-API pass in Sprint 4** (list every `urls.py` include and every ViewSet) since the review found this class of problem late.
- Cache versions: `app.css?v=48`.

### Where things stand (2026-11-08)
- Sprints 1, 2 and 3 are done, reviewed and fixed; 126 tests pass. Code is on GitHub: https://github.com/MohanedGobbi/worktrack (branch `main`, first push 2026-11-08). Next: Sprint 4.
- **Cleanup done:** removed the unused 42 MB Tailwind CLI binary and the dead `messenger.html`; `*.zip` is git-ignored. The binary is still in git history (harmless, under GitHub's limit).
- **Share the project:** `git archive --format=zip --prefix=worktrack/ -o worktrack.zip HEAD` gives a code-only zip (no database, uploads, `.env`, `.venv`). The first zip (10.7 MB) predates `run.bat`.
- **Run fast (Windows):** double-click `run.bat` in the project, or the Desktop file `WorkTrack Pro.bat`, which calls it through the ASCII junction `C:\Users\gobbi\worktrack` (a Windows shortcut and cmd cannot take the Arabic folder name; if the project folder moves, recreate the junction: `New-Item -ItemType Junction -Path C:\Users\gobbi\worktrack -Target <project folder>`). It migrates, starts the server on 127.0.0.1:8000 and opens the browser. Needs `.venv` and a `.env` with `DEBUG=True`.
- **University of Ghardaia version:** started on branch `ghardaia` (2026-11-08); see section 2c. Logos and photos received; still waiting for the partner website, English unit names, the real admin account and the staff list.
- **Signal Blue** now follows the brand when custom colours are set (`_wt_theme` computes it). The ROWD preset keeps Signal Blue.
- **Open before launch (carried over):** whole-API pass (every `urls.py` include and ViewSet), atomic last-admin guard, dashboard module toolbar / list view rebuild (works and is themed, not rebuilt), English-only `<title>` on the groups, attendance and archive pages, English-only notification text written by signals, retire the legacy-task correspondence mirror (`_sync_legacy_correspondence`), file type checks for task attachments and messenger files, banner text colour for very light brand colours.

### Banners, language and automatic updates (2026-11-09, on `main`, not committed)
- **Banners readable on any brand colour or photo:** with a banner photo, `--wt-hero-bg` lays a dark brand gradient over it (stronger on the text side, flipped for RTL). The older `dash-hero` / `cmd-hero` / `admin-hero` banners now use on-brand text with a light shadow (`app.css?v=52`).
- **Language pass:** breadcrumb and `<title>` come from one route-name table (`WT_PAGE_NAMES` in `core/context_processors.py`, include `wt_page_title.html`). Badges, pager, aria-labels, placeholders and tooltips are now bilingual on admin, attendance, groups, login-as and messenger. Dates use `j/n/Y`. Note: the `auto.` machine rows still hide some English; deleting them in Sprint 4 will show what remains (rerun a scan of each page in Arabic per role).
- **Automatic updates (Ubuntu/Debian VPS):** tag `vX.Y.Z` → GitHub Actions tests and publishes `worktrack-X.Y.Z.tar.gz` + `SHA256SUMS`; servers pull it nightly and roll back code and database on failure. Admin panel: Site settings → Software updates. Install and operation: `docs/guides/INSTALL_LINUX.md`. Scripts: `deploy/linux/`, release: `python scripts/release.py patch`. Docker test: `docker run --rm -v "$PWD":/src:ro ubuntu:24.04 bash /src/deploy/linux/tests/run_updater_tests.sh` (31 checks).
- **Vendor support account:** `manage.py support_admin --email ...` creates or restores a super admin (password printed once; `--reset-password` for a new one). Re-running it re-activates and re-promotes the account, so anyone with server shell access can always get back in. No password in the code (public repo).
- **Before the install visit:** push a first tag and confirm the release shows both files; create a fine-grained read-only token for the private repo; build the offline package from that release asset (not from `git archive`).

### Sprint 4: release
- One independent review over everything rebuilt since the worker home (tasks, submissions, module page, messenger, Sprint 2 and 3 pages); fix what it finds.
- Install checklist for cPanel/Passenger (subpath, cookies, static, media, backups, first admin via `new_institution`, and `manage.py clean_user_text --apply` once on any install upgraded from before Sprint 1) and a demo-data seed so the product demos well.
- Delete the machine-made translation rows (see owner decisions).
- Tag `v1.0`, then push the tag.

### After launch (not before)
Glossary / terminology table, editable landing and sign-in copy, the University of Ghardaia theme and content, a full messenger rebuild on `wt-*` parts (it still uses the local Tailwind file), brand-derived Signal Blue.

### Owner decisions (2026-11-07)
- **Hide for v1** (sidebar visibility only; keep the code so it can be switched back on): Global Map, Offline Maps, Organizational Intelligence, Roadmap (Gantt page), module templates (dashboard / form / builder), To-do management page, Version & Data Archive, Host management, Messenger config, Inspect user, Translation manager.
- **Rebuild for v1:** dashboard (toolbar + table view), worker home (done), tasks (done), modules (done), submissions (done), correspondence (list / detail / form), messenger (hardened), notifications, profile, my score, team analytics + KPI (one page), manager portal, users + create user, Site Settings.
- **Restyle only:** archived modules, module groups, audit log, attendance.
- **Machine translations:** keep for now; delete the `auto.` `TranslationItem` rows in **Sprint 4**, after a quick scan of the restyle-only pages for labels that need real Arabic.

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
2. **Phase 1, daily work:** (all done after Sprint 2)
   - ~~`worker_portal.html` (the worker home)~~ Done
   - tasks: ~~`tasks_list`, `task_detail`, `task_kanban`, `task_calendar`, `task_form`~~ Done (independent review skipped at the owner's request; run one before calling them finished).
   - ~~submissions: `submissions_list`, `submission_detail`, `submission_form`, `submission_versions`~~ Done (no independent review yet). Review scores are now 0–100, matching `Submission.score` and the KPI engine.
   - ~~`module_dashboard`~~ Done ("Task timeline first"; no independent review yet)
   - ~~`messaging/messenger_page`~~ Hardened in place (not rebuilt): message HTML sanitized, Font Awesome icons, subpath-safe URLs, translation kept off user text. It still uses the local Tailwind file for layout.
   - ~~`notifications`, `profile`, `worker_performance`~~ Done (Sprint 2)
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
- ~~`templates/messaging/messenger.html`~~ removed (dead); the unused 42 MB Tailwind CLI binary was removed from `static/vendor/tailwind/` too.
- **Demo data is thin.** 5 modules, only 1 with dates, no submissions awaiting review. Seed richer data to test the roadmap and "Needs you". (Worker `tester@test.local`, pk 165, now has 8 dated demo tasks covering every worker-home group, one sent back and one waiting for review.)
- **Notes for workers.** The todo endpoints (`corr_todo_*`) were manager-only, so the shell notes drawer never worked for workers. Now `_can_use_todos` lets anyone manage their own general (module-less) notes; module to-dos stay manager-only. Managers can still edit any todo by id (pre-existing, unchanged).
- ~~Server-side cleaning, production settings, Site Settings, new-institution command~~ Done in Sprint 1.
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

## 2c. Plan: the University of Ghardaia version (Faculty of Law and Political Science)

Customer 1. Same codebase, configured by data (see 2b). The faculty structure the owner supplied has 5 groups; it is kept in `institutions/ghardaia/institution.json` on the branch below (22 units as `Department` rows, 7 roles, Arabic default, registration off).

### Branches (how the two versions relate)
- **`main`** is the product (ROWD default theme) and gets every code change, including anything general found while working on a customer (the partner slot, Signal following the brand colours, page titles from Site Settings all landed on `main` first).
- **`ghardaia`** is `main` plus `institutions/ghardaia/` (university logo, faculty building photo, AFAK partner logo, a campus poster, `institution.json`, README) and `run_ghardaia.bat`. No template or code differs. To update it: `git switch ghardaia && git merge main`. Never edit product code on `ghardaia`.
- **Run it:** double-click `run_ghardaia.bat`. It uses its own `db_ghardaia.sqlite3` and `media_ghardaia/` (git-ignored) and serves on http://127.0.0.1:8001/, so the ROWD demo on 8000 is untouched. The first run applies `institution.json` and writes the admin password (`admin@ghardaia.local`) to `ghardaia_setup.log`. Delete those three to start over.
- **Done on the branch (2026-11-08):** steps 1 to 3 below are applied by the config: name, logo, green brand `#116333` (from the logo; accent `#7dc35b`), faculty building as banner, AFAK partner beside the ROWD credit, 22 units, 7 roles, first admin. Checked visually in Arabic: sign-in page and dashboard are green throughout, partner and ROWD credit both in the footer.
- **Next on the branch:** the partner's website (empty in the config), English unit names, the real admin email, work groups (step 4), the bulk user import (step 5), modules (step 6), vocabulary (step 7).

### What the owner still sends (nothing below can be finished without it)
1. **University logo** (PNG with transparent background if possible) and a **photo of the university**.
2. **Partner company logo** plus its name and website (it will appear as "our partner").
3. The **official English names** of the units (only Arabic names exist so far) and the **faculty / university colours** if they differ from the logo.
4. Who is the first administrator (name, email), contact details (email, phone, address, website) and the **domain / hosting** the install will use.
5. The **staff list** (name, email, unit, role) so accounts can be loaded in one go (see step 5).

### Steps, in order
1. **Identity (Site Settings, no code).** Name: `جامعة غرداية - كلية الحقوق والعلوم السياسية` / `University of Ghardaia - Faculty of Law and Political Science`; upload the logo (the shell picks a readable backdrop for light or dark logos); default language Arabic. Colours: pick "Your colours", take brand and accent from the logo, let the contrast check choose the text colour; check the banner and sidebar in the live preview. The university photo goes in as the **banner image** (it sits under a brand overlay) and can also feed the landing page hero later. Set footer and contact details there too.
2. **Partner logo (done 2026-11-08 on `main`: Site Settings > Partner, `includes/wt_partner.html`, `tests/test_partner.py`).** Site Settings has no slot for a partner yet. Add `partner_name`, `partner_url`, `partner_logo` (migration, form fields, preview) and show it as "In partnership with" in the footer, on the landing page and on sign-in, **next to** the ROWD credit and never replacing or restyling it. `templates/includes/rowd_credit.html` and `tests/test_credit.py` must stay untouched; add a test that the credit is still present when a partner logo is set. Keep it theme-level data, not hard-coded.
3. **Structure and roles (data).** Run `new_institution` with the config: it creates the units, the 7 privilege profiles (Dean, Vice-dean, Secretary general, Head of department, Head of service, Staff, IT administrator) and the first admin (replace the placeholder email first). Base roles map as: IT administrator and Secretary general (if they manage users) = `super_admin`; Dean, Vice-deans, department heads, service heads = `manager`; everyone else = `worker`. Privilege profiles refine this; check each profile with the owner.
   - `Department` has no parent, so the group each unit belongs to is written in its description. **Recommended small addition:** an optional `parent` on `Department` (migration, grouping in the user form, the Team page and filters) so the 5 groups hold their units. Do it if the owner wants reports by group.
4. **Work groups (who can see whom).** The platform shows people the teammates they share a **work group** with. Create one group per service or department (members = its staff and head) plus a "Faculty leadership" group (dean, vice-deans, secretary general, heads). A manager's Team page is built from reports (profile manager) and shared groups, so set each person's "Reports to" as well.
5. **Accounts.** Create the first admin, then load staff. There is no bulk import yet: add `manage.py import_users file.csv` (email, first and last name, unit, role, manager email, groups; dry-run, report of rejected rows, one-time passwords printed or mailed, validators on). Until then use Admin console > Users.
6. **Modules (the faculty's workstreams).** Create modules directly (module templates are hidden in v1). Suggested start, one per service or recurring process: registrations and orientation; teaching and assessment (exams, timetables, deliberations); certificates and career path; postgraduate / doctoral follow-up; scientific research and laboratories; cooperation and external relations; scientific council; human resources; budget and finance; maintenance and general means; IT and statistics; library; virtual courtroom; student clubs and associations. Give each a colour and an owner; tasks, submissions and review then follow the normal flow.
7. **Vocabulary.** The product words (module, worker, manager, submission) do not match faculty language. The glossary table is a post-launch item (section "After launch"); for this customer decide with the owner whether it comes first. Interim choices that need no code: use the role names above in the privilege profiles, name modules after services, and review the Arabic strings on the visible pages (the machine translations are removed in Sprint 4; fix labels such as "الوحدة" vs "الملف" in the templates' Arabic side).
8. **Sidebar and features.** Keep the v1 switches. Likely candidates to switch on for them, with the owner: Attendance (human resources service) and Offline Maps / Global Map are not needed. Correspondence is central (circulars, directives, decisions go through it): create the reference-number convention with the secretary general.
9. **Landing and sign-in copy.** Still fixed text. If the owner wants faculty wording, editable landing copy (post-launch item) comes first; otherwise review the Arabic text once.
10. **Install.** Follow the Sprint 4 cPanel/Passenger checklist: `.env` (SECRET_KEY, DEBUG=False, domain, HTTPS cookies), `collectstatic`, migrate, `new_institution`, then a smoke test with one account per role, EN and AR, desktop and phone. Back up `db.sqlite3` and `media/` before every update.

### Acceptance (done when)
- The shell, landing and sign-in show the university name and logo, the university colours and the partner logo; the ROWD credit is intact (`manage.py test tests.test_credit`).
- A dean, a service head and a staff member each sign in and see only what their role and groups allow; correspondence issued by the secretary general reaches the right people and is acknowledged.
- Everything above is in the config and Site Settings, with no template edited for this customer.

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
- **Local `.env`:** must contain `DEBUG=True` for development (production refuses to start without a `SECRET_KEY`). See `.env.example`.
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
- **Line endings in scripted edits.** Python's text mode on Windows writes CRLF, which turned whole LF files into one big diff (fixed in `48935ad`). Use `open(p, encoding='utf-8', newline='')` for reads and writes, or edit with a file-editing tool.
- **Template cache.** With `runserver --noreload`, Django caches templates, so edits don't show until a restart. The launcher now runs with auto-reload.
- **Asset caching.** Bump the `?v=` cache-busters when editing CSS/JS: `app.css?v=48` (in `base.html` and `public/_head.html`), `public.css?v=8`, `site-settings.js?v=3`, `i18n.js?v=3.2`, `stack-scene.js?v=2`.
- **Old page scripts write inline styles.** For example, `dashboard.html` set margins on `.dashboard-main-area`. The shell's sidebar offset is therefore padding on `.wt-shell`, not a margin.
- **Old page CSS uses `!important` widely.** Overrides need higher specificity (`.wt-app ...`) or a rebuilt block.
- **`100vw` includes the scrollbar.** Use `%` widths, or RTL pages get sideways scroll.
- **`repeat(12, 1fr)` grids overflow** when labels are wider than columns. Use `minmax(0, 1fr)`.
- **Translation middleware vs. data hooks.** It rebuilds `lang-en`/`lang-ar` pairs that match a DB row and drops attributes on them. Anything a script needs to find, and any institution or user text, goes under `translate="no"`.
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
