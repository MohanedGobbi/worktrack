# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Backend stays Django 5/6 + Django REST Framework (binding). Front end: delegated to the designer by the user ("use whatever you need, keep Django as backend").
Chosen: server-rendered Django templates with no Node build step. Three.js, GSAP and Lenis are loaded as ES modules from `static/vendor/` through an import map. Why: npm is not usable on the dev machine, customer installs are cPanel/Passenger hosts without Node, and the app pages already depend on server-rendered markup, element ids and `data-*` hooks.

## Users

Two daily audiences, both inside one customer organisation:

- **Workers**: staff who receive tasks, do the work, upload submissions and check their own performance score.
- **Managers**: people who create modules and tasks, assign workers, review and rate submissions, and read team analytics.
- **Super admins**: configure users, roles, branding, translations, hosts and site settings. Fewer people, less frequent.

Mostly used on office desktops through the working day. A phone layout is required (checking tasks, replying to messages, submitting on the go).
Arabic-first organisations; English also supported.

## Product Purpose

WorkTrack Pro runs an organisation's task workflow end to end: work is grouped into modules, tasks are assigned, workers submit versioned results, managers review them, and each person's KPI score is computed automatically from completion, punctuality, quality and productivity. Internal messaging, correspondence, attendance and notifications sit in the same place so the team does not juggle tools.

Success: a worker opens the platform and knows immediately what is due; a manager sees who is behind and can act in a few clicks.

## Positioning

A white-label, self-hosted workforce and task platform. Each customer installs their own instance with their own name and logo; the scoring formula and the review loop are built in rather than bolted on.

## Operating Context

- Deployed per customer on their own host (often cPanel/Passenger under a subpath such as `/cnrst`), SQLite locally, MySQL or PostgreSQL in production.
- Workflows: module → tasks (list, kanban, calendar) → submission with versions → manager review and rating → KPI.
- Also: administrative correspondence (letters with attachments, acknowledgements, PDF), group and direct chat with voice messages and polls, attendance, in-app and email notifications, audit log, translation manager.
- Roles: `super_admin`, `manager`, `worker`. Sidebar items are filtered per role (`SidebarVisibilityRule`), plus custom privilege profiles (`SystemProfile`).

## Capabilities and Constraints

- **White-label is a hard requirement.** Product name (EN and AR) and logo must come from `core.SiteConfiguration` (`app_name`, `app_name_ar`, `logo`) and be swappable per customer without touching templates or CSS. No customer name, logo or brand colour may be hard-coded.
- Bilingual Arabic / English with full RTL and LTR. Default language comes from `SiteSettings.default_language` (default `ar`). Strings are translated at render time by `DynamicTranslationMiddleware` plus the `TranslationItem` table, and client-side by `static/js/i18n.js`.
- The redesign changes presentation only. Routes, view logic, form field names, element ids and `data-*` hooks used by existing JavaScript, and API calls must keep working.
- Cookies are namespaced for subpath deploys (`cnrst_sessionid`, `cnrst_csrftoken`); fetch calls use `credentials: 'same-origin'`.
- Known defect: `static/js/i18n.js` requests `/translations/api/map/`, which no route serves (404).

## Brand Commitments

- **WorkTrack Pro is a ROWD product** (ROWD / روْد, ROWD Tech: "an engineering and technology company building intelligent industrial and digital systems"). Confirmed by the user 2026-11-06.
- **Two layers of identity, kept separate:**
  - *Theme layer (swappable per customer):* product name (EN/AR), customer logo, colours, fonts, imagery. Changing the design or rebranding for a customer touches only this layer.
  - *Vendor credit (fixed):* the ROWD mark and a "by ROWD Tech" credit stay on every install, whatever the theme. It is the only thing that survives a redesign.
- **Default theme = the ROWD brand system** (`D:\rowd tech stuff\rowed brand guidline.pdf`, logo files in `D:\rowd tech stuff\brand-assets\`): Rowd Blue `#0033A0` leads; Signal Blue `#2D6BFF`, Cyan Pulse `#19BEDC`, Steel `#5B6473`; neutrals `#FFFFFF #EEF1F6 #9AA4B4 #2A3242 #131925`. Latin display Montserrat Alternates 400–800, technical/data IBM Plex Mono. The stadium "module" shape (three stacked, offset modules) is the brand's graphic atom. Motion: restrained and precise, ease-out 200–300 ms, no bounce. Voice: precise, confident, human; evidence over hype. The ROWD mark is never recoloured, distorted or given effects; minimum 24 px symbol, 120 px full lockup.
- **Arabic type:** Thmanyah Sans (UI and body) and Thmanyah Serif Display (headings), self-hosted, the same files used in the user's نبض اليوم project. Replaces the guideline's Vesterbro Arabic, which is not licensed here.
- Default product name **WorkTrack Pro** (Arabic: وورك تراك برو). The old `media/logo.png` arrow mark is the previous default and may be replaced.
- The previous CNDP crimson design, the green "editorial" design spec and the old agent system prompt were retired by the user on 2026-11-06. They are not references.

## Evidence on Hand

- Real feature set and data model in the Django apps; a local SQLite database with demo data (`db.sqlite3`) and demo users (see `docs/guides/USER_CREDENTIALS_REFERENCE.md`).
- No customer testimonials, logos, statistics or case studies exist. Do not invent any.

## Product Principles

1. **The daily screens are tools.** Spectacle (3D, scroll motion) belongs on the public landing and sign-in pages. Screens people use all day stay calm, fast and obvious.
2. **One product, any customer.** Every visual decision must survive a different name, logo and accent colour.
3. **What is due comes first.** Every role's home answers "what needs me now" before anything else.
4. **Arabic is not a translation.** RTL layouts, Arabic type and Arabic copy are designed first-class, not mirrored afterwards.
5. **Never break the workflow.** Presentation changes may not change behaviour.

## Accessibility & Inclusion

- Motion-heavy and 3D content must respect `prefers-reduced-motion` and must never block sign-in or navigation.
- Daily screens must work on mid-range office PCs and phones; 3D must not load on working screens.
