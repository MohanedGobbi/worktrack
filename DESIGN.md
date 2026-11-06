---
name: WorkTrack Pro
description: White-label task, review and KPI platform by ROWD Tech. Arabic-first, full RTL, one swappable theme layer over a fixed vendor credit.
colors:
  rowd-blue: "#0033a0"
  cyan-pulse: "#19bedc"
  on-brand: "#ffffff"
  signal-blue: "#2d6bff"
  steel: "#5b6473"
  ink: "#131925"
  ink-2: "#2a3242"
  muted: "#5b6473"
  faint: "#8a94a6"
  line: "#dce2ec"
  line-soft: "#e8ecf3"
  ground: "#eef1f6"
  surface: "#ffffff"
  surface-2: "#f6f8fb"
  ok: "#0e7c57"
  ok-soft: "#e3f4ed"
  warn: "#a85f00"
  warn-soft: "#fdf1de"
  bad: "#c0283a"
  bad-soft: "#fbe7ea"
typography:
  display:
    fontFamily: "Montserrat Alternates, Thmanyah Sans, Segoe UI, sans-serif"
    fontSize: "clamp(2.25rem, 1.1rem + 4.1vw, 4.9rem)"
    fontWeight: 700
    lineHeight: 1.02
    letterSpacing: "-0.035em"
  display-ar:
    fontFamily: "Thmanyah Serif Display, Thmanyah Sans, serif"
    fontSize: "clamp(2.25rem, 1.1rem + 4.1vw, 4.9rem)"
    fontWeight: 700
    lineHeight: 1.22
    letterSpacing: "0"
  headline:
    fontFamily: "Montserrat Alternates, Thmanyah Sans, Segoe UI, sans-serif"
    fontSize: "clamp(1.9rem, 1.2rem + 2.2vw, 3.2rem)"
    fontWeight: 700
    lineHeight: 1.06
    letterSpacing: "-0.03em"
  title:
    fontFamily: "Montserrat Alternates, Thmanyah Sans, Segoe UI, sans-serif"
    fontSize: "clamp(1.4rem, 1.1rem + 1vw, 1.9rem)"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.015em"
  body:
    fontFamily: "Montserrat, Thmanyah Sans, Segoe UI, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.55
    fontFeature: "\"lnum\" 1"
  body-ar:
    fontFamily: "Thmanyah Sans, Segoe UI, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "Montserrat, Thmanyah Sans, Segoe UI, system-ui, sans-serif"
    fontSize: "0.82rem"
    fontWeight: 600
    lineHeight: 1.3
  data:
    fontFamily: "IBM Plex Mono, ui-monospace, Cascadia Mono, monospace"
    fontSize: "0.86rem"
    fontWeight: 400
    lineHeight: 1.7
  data-label:
    fontFamily: "IBM Plex Mono, ui-monospace, Cascadia Mono, monospace"
    fontSize: "0.7rem"
    fontWeight: 500
    lineHeight: 1.3
    letterSpacing: "0.06em"
rounded:
  sm: "6px"
  input: "8px"
  chip: "10px"
  card: "12px"
  dialog: "16px"
  pill: "999px"
spacing:
  s1: "4px"
  s2: "8px"
  s3: "12px"
  s4: "16px"
  s5: "24px"
  s6: "32px"
  s7: "48px"
  s8: "64px"
components:
  button-primary:
    backgroundColor: "{colors.rowd-blue}"
    textColor: "{colors.on-brand}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "8px 16px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.pill}"
    padding: "8px 16px"
  button-dark:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.surface}"
    rounded: "{rounded.pill}"
    padding: "8px 16px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.input}"
    padding: "8px 12.8px"
    height: "40px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
    padding: "18px"
  nav-item:
    backgroundColor: "{colors.rowd-blue}"
    textColor: "{colors.on-brand}"
    rounded: "{rounded.pill}"
    padding: "8px 12px"
    height: "40px"
  nav-item-active:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.rowd-blue}"
    rounded: "{rounded.pill}"
    padding: "8px 12px"
    height: "40px"
  badge-success:
    backgroundColor: "{colors.ok-soft}"
    textColor: "{colors.ok}"
    rounded: "{rounded.pill}"
    padding: "0.36em 0.6em"
  signin-module:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "8px"
    height: "76px"
---

# Design System: WorkTrack Pro

## Overview

**Creative North Star: "Three Modules, One System"**

The ROWD stadium module (a rounded slab with true semicircular ends) is the unit of work, and everything is built from it. On the public pages a Rowd Blue field holds a stack of three offset modules. The top and bottom ones are satin extruded slabs in WebGL, and the middle one is the white sign-in form. Inside the product the same atom shrinks to a working size: the white pill that marks the active sidebar item, the pill buttons, the three-module watermark on page banners, and the default module cover. A screen should still read as this world with all copy removed: a blue field, offset rounded slabs, and white working surfaces.

The system has two registers. Public pages (landing, sign-in, register, password reset) are where the show happens: full-bleed brand field, large display type, one scroll-scrubbed 3D scene. Working screens are tools. They use a calm blue-grey ground (#eef1f6), white 12px cards, hairline lines, a brand-blue sidebar, and no 3D. Density is office-desktop first, with a full phone layout (brand mobile bar plus a five-item bottom nav).

Identity comes in two layers that must never mix. The **theme layer** (product name in EN and AR, customer logo, colours, fonts, imagery) can be swapped per customer. The **vendor credit** (the ROWD mark plus "Built by / تطوير", linked to rowd.co) is fixed and survives every redesign. Arabic is designed first. RTL mirrors layout, gradients, the banner motif and the 3D stage, and Arabic gets its own faces instead of falling back to Latin ones.

**Key Characteristics:**
- One atom: the stadium module, used at every scale from a 3D slab down to a nav pill.
- Brand inputs are kept to a minimum (brand, accent, on-brand). Every tint, shade, line and shadow is derived with `color-mix(in oklab, ...)`, so any customer colour re-tints the whole product, including the 3D scene.
- Spectacle stays on public pages. Working screens stay calm and fast.
- Pills for actions and navigation, 12px cards, 8px inputs.
- Soft blue-tinted ambient shadows. Nothing glossy, nothing hard-edged except the extruded slab edge of the sign-in module.
- Arabic-first type: Thmanyah Sans for UI, Thmanyah Serif Display for public headlines.

### The two identity layers and how to re-theme

**Theme layer (swappable).**
- `static/wt/theme-rowd.css` holds the typefaces (`@font-face`) and every primitive token (`--wt-*`). It is the only file a full re-theme replaces.
- `templates/includes/wt_theme.html` loads the theme file. It then injects the per-install brand inputs from Site Settings inline (`--wt-brand`, `--wt-accent`, `--wt-on-brand`, `--wt-brand-rgb`), aliases the legacy variable names (`--color-primary`, `--primary-color`, `--banner-primary`, ...), and defines the page-banner surface `--wt-hero-bg`.
- `core/context_processors.py` supplies the inputs. `_wt_theme` reads them from the selected preset (`rowd` by default), or from the admin colour fields when the preset is `custom` (`primary_color`, `accent_color`, `button_text_color`). `_logo_tone` measures the uploaded logo's luminance so a light logo sits directly on the brand field (`wt-logo-chip--on-brand`) and a dark logo sits in a white chip. With no logo, a typographic `wt` monogram stands in. `_wt_lang` sets `lang` and `dir` on the first render so RTL pages never flash LTR.
- `static/wt/app.css` and `static/wt/public.css` are the component layer. They only read tokens and must not hard-code a brand colour, font or radius.

**Vendor credit (fixed).** `templates/includes/rowd_credit.html` renders the credit with the white ROWD mark on brand surfaces (`variant='side'` or `'dark'`) and the navy mark on light ones (`'light'`). It is not part of the theme layer, no theme may restyle or remove it, and the mark is never recoloured, distorted or given effects.

**To rebrand an install (no code):** in Site Settings, set the product name (`app_name`, `app_name_ar`) and upload the logo. Then either keep the `rowd` preset or choose `custom` and set the primary (brand), accent and button-text (on-brand) colours. Everything derived (soft tints, hover shades, focus ring, shadows, sidebar, banners, module covers, the 3D slabs) follows automatically. An uploaded banner image sits under a brand-gradient overlay so white text stays readable.

**To ship a new theme (code):** copy `theme-rowd.css` to `theme-<name>.css` and change the faces, neutrals, signal, status colours, radii, spacing or motion. Then point the single `<link>` in `templates/includes/wt_theme.html` at the new file; that link is the theme switch. Brand, accent and on-brand always come from Site Settings, because they are injected after the theme file, so a theme file's own values for those three are only fallbacks.

## Colors

The palette is one deep corporate blue that owns surfaces, two lighter blues that carry light and data, and a cool blue-tinted neutral scale. Status colours are muted and appear only where status lives.

### Primary
- **Rowd Blue** (`--wt-brand`): the brand field. Used for the sidebar, the mobile bar, public-page backgrounds, primary buttons, checked controls, active tabs, the progress fill, and the base of the page banner. It is overridable per install.
- **On-Brand White** (`--wt-on-brand`): text and icons on Rowd Blue, the active nav pill, and the middle slab of the stack. It is overridable per install for light brand colours.

### Secondary
- **Signal Blue** (`--wt-signal`): links, the focus outline (2px, offset 2px), info states, the top slab of the 3D stack, and the radial light on banners and the public field. It is not overridable from Site Settings.

### Tertiary
- **Cyan Pulse** (`--wt-accent`): data highlights and live counts. Used for sidebar count badges and the notes badge (always with ink text), formula weights, story bullet icons, the bottom slab of the stack, the 3D rim light, and the public-page focus outline. It is overridable per install.

### Neutral
- **Ink** (`--wt-ink`): body text, headings, and dark buttons and tooltips.
- **Ink 2** (`--wt-ink-2`): secondary text, form labels, and the text on light buttons.
- **Steel / Muted** (`--wt-steel`, `--wt-muted`): captions, breadcrumbs, table headers and helper text. Mixed with transparency, it also colours the scrollbars.
- **Faint** (`--wt-faint`): placeholders and breadcrumb separators only.
- **Line** (`--wt-line`) and **Line Soft** (`--wt-line-soft`): hairline borders, dividers and table rules.
- **Ground** (`--wt-ground`): the app page background behind cards.
- **Surface** (`--wt-surface`) and **Surface 2** (`--wt-surface-2`): cards, dialogs, inputs, and recessed fills such as table heads, disabled fields and the notes drawer body.

### Status
- **OK / Warn / Bad** (`--wt-ok`, `--wt-warn`, `--wt-bad`), each with a `-soft` tint. Badges, alerts and toasts use the soft tint as the fill and the strong colour as the text.

### Derived (app.css; never hand-pick these)
`--wt-brand-strong` (brand 80% + black, hover), `--wt-brand-deep` (62% + black, active), `--wt-brand-soft` (7% into surface, hover fills and focused fields), `--wt-brand-tint` (14%, primary badges), `--wt-brand-line` (26%, hover borders), `--wt-on-brand-muted` (72%, secondary text on the sidebar), `--wt-on-brand-faint` (14%, hover fills on brand), `--wt-focus` (signal at 55%, 3px focus halo on fields and buttons).

### Named Rules
**The Two Inputs Rule.** A customer changes brand and accent (plus on-brand), and nothing else needs to change. Any new colour on a component must be a `color-mix` of an existing token, never a new hex.

**The Amber Is Alarm Rule.** Warn amber appears only for alerts, overdue states and impersonation. It is never used as decoration or as a second accent.

**The Cyan Carries Ink Rule.** On Cyan Pulse fills (count badges, the notes badge) the text is Ink, not white.

## Typography

**Display Font:** Montserrat Alternates 500–800 (with Thmanyah Sans, Segoe UI)
**Body Font:** Montserrat 400–700 (with Thmanyah Sans, Segoe UI, system-ui)
**Data Font:** IBM Plex Mono 400–600 (with ui-monospace, Cascadia Mono)
**Arabic UI and body:** Thmanyah Sans 300–900
**Arabic display:** Thmanyah Serif Display 500–900

All faces are self-hosted from `static/wt/fonts/` with `font-display: swap`. Latin faces are split into latin and latin-ext subsets by `unicode-range`.

**Character:** Montserrat Alternates gives the geometric, engineered voice of the ROWD mark. Montserrat keeps body text plain and legible. In Arabic, the Serif Display brings calligraphic weight to public headlines, and Thmanyah Sans keeps the working UI quiet.

### Hierarchy
- **Display**: public hero title only (product name over the stack). Max 17ch. In Arabic it switches to Thmanyah Serif Display 700 with a line height of 1.22, letter spacing 0, max 16ch.
- **Headline**: public story sections, the close section and auth page titles. In Arabic: Serif Display, line height 1.25.
- **Title**: the app page heading (`wt-page-head h1`). Section headings h1–h6 use the display face at 700 with letter spacing -0.015em and line height 1.2, balanced. In Arabic, all app headings switch to Thmanyah Sans with a line height of 1.35.
- **Body**: 15px at line height 1.55 with lining numerals. Public body text runs 1.04rem at line height 1.65, max 46–58ch. Page intros are capped at 70ch.
- **Label**: form labels at 0.82rem 600 in Ink 2. Compact labels on the sign-in module run 0.76rem.
- **Data**: the scoring formula (always LTR, `unicode-bidi: isolate`, `translate="no"`), weight values, timestamps, `kbd` hints and code.
- **Data label**: small uppercase mono labels for table headers (0.7rem, 0.06em), sidebar group labels, dropdown headers and search section headers (0.68rem, 0.08em). In RTL these switch to Thmanyah Sans with no uppercase and no tracking, at 0.78rem.

### Named Rules
**The Mono Means Machine Rule.** IBM Plex Mono is for data: numbers, the formula, times, keys, and the small column and group labels that index data. It never sets a heading, a sentence or a button.

**The Arabic Is Not A Fallback Rule.** Every Latin type rule has an explicit `html[dir="rtl"]` counterpart that swaps the family, sets letter spacing to 0, drops uppercase and opens up the line height (about 1.22–1.45). Never let Arabic inherit negative tracking or uppercase.

**The Tabular Numbers Rule.** Tables, stat values, badges and `.wt-num` use `font-variant-numeric: tabular-nums`.

## Layout

- **App shell:** a fixed inline-start sidebar 264px wide and a sticky top bar 60px high (92% surface with blur, hairline bottom border). Content padding is 24px, with 48px at the bottom. The main container is capped at 1480px. All positioning uses logical properties (`inset-inline-start`, `padding-inline-start`), so RTL mirrors without overrides.
- **Below 992px:** the sidebar becomes an off-canvas drawer (min(86vw, 320px)) over an ink backdrop. A 56px Rowd Blue mobile bar replaces it, the top bar actions hide, and a fixed five-column white bottom nav (52px targets, safe-area padding) appears. The floating notes button hides because notes move into the menu.
- **Spacing:** an 8px rhythm (`--wt-s1`…`--wt-s8`: 4, 8, 12, 16, 24, 32, 48, 64). Page heads sit 24px above content. Card bodies use 18px padding.
- **Public pages:** a full-viewport hero (`100svh`) with three rows (header, centred body, foot with the credit and scroll cue). The sign-in stack is min(880px, 100%) wide. Story steps are each 100svh, with copy at min(440px, 42vw) on the start side, and the 3D stage takes the other side (at 22% of the width, mirrored in RTL). Below 900px the copy sits in a blurred deep-field card at the bottom, with the scene above. The close section is white, a two-column grid (1.3fr / 1fr) capped at 1180px, and collapses to one column.

## Elevation & Depth

Working screens use a hybrid of tonal layering and ambient shadow. The ground (#eef1f6) sits under white surfaces, and recesses use Surface 2. Shadows are always soft and two-part: a small brand-tinted contact shadow plus a larger ink-tinted ambient one. All shadows derive from tokens, so they re-tint with the brand.

### Shadow Vocabulary
- **Rest** (`--wt-shadow-1`): cards, panels, stat cards, the active language segment.
- **Raised** (`--wt-shadow-2`): dropdowns, the floating notes button, public alerts.
- **Overlay** (`--wt-shadow-3`): toasts, dialogs, search, the notes drawer, the mobile drawer.
- **Active nav pill:** `0 2px 10px` brand-deep at 35%. It lifts the white pill off the blue sidebar.
- **Slab edge** (sign-in module only): an inset top highlight, an inset bottom tint, and a 1px plus 6px un-blurred brand-tinted underside, over a 30px/70px ambient drop. It renders the DOM module as the same extruded slab as its WebGL neighbours.

### Depth on public pages
Depth on public pages is real 3D. An orthographic three.js camera is mapped to CSS pixels, so the extruded stadium meshes sit exactly on their DOM slots. Materials are satin (MeshStandard, roughness 0.3, a light emissive lift), lit by a white key light and a cyan rim light, over a radial signal-blue glow on the field.

### Named Rules
**The Flat Tool Rule.** No 3D, WebGL or scroll choreography on working screens. Depth there comes only from the shadow vocabulary above.

**The Tinted Shadow Rule.** Shadows are never neutral grey or black. They mix brand and ink at low opacity.

## Shapes

The stadium (a rounded rectangle with full semicircular ends) is the system's atom.

- **Stadium / pill (999px):** buttons, nav items, the search trigger, the language switch, badges, progress bars, formula weight tracks, and the sign-in module and its fields. When the module stacks into a column on phones it relaxes to 28px, and the fields inside it to 20px.
- **Card (12px):** cards, panels, alerts, dropdowns, toasts, page-level notices.
- **Input (8px):** form controls and pagination.
- **Dialog (16px):** modals, the confirm dialog, global search, and legacy hero banners.
- **Small (6px, 10px):** `kbd` chips (6px), and the logo chip, note cards and search rows (10px).
- **Circles:** avatars, icon buttons and toast icons.

### Where the module appears
1. **The 3D stack** (`static/wt/js/stack-scene.js`): three extruded slabs offset like the mark (top 92% wide shifted toward the start side in Signal Blue, middle white, bottom 56% wide shifted toward the end side in Cyan Pulse). The geometry stretches the straight middle, so the caps stay true semicircles at any length. Without WebGL, CSS pills in the same colours fill the slots.
2. **The sign-in module:** the middle slab is a real white DOM form. On register it grows into a 30px-radius panel.
3. **The active nav pill:** a white stadium on the Rowd Blue sidebar.
4. **The banner motif** (`--wt-hero-motif`): three offset white stadiums at 9%, 15% and 11% opacity, anchored to the end side (mirrored in RTL), over the brand gradient and a signal-blue radial glow.
5. **The default module cover** (`static/wt/img/module-cover.svg` on `img[data-wt-cover]`): three white stadiums (22%, 90% and 40% opacity) on a brand gradient drawn by CSS, so the cover follows any theme colour.

### Named Rule
**The True Cap Rule.** A module's ends are always full semicircles. Never scale a stadium non-uniformly, and never swap it for a rounded rectangle with a small radius when it means "module".

## Components

### Buttons
- **Shape:** stadium (999px). Default size: 600 weight, 0.875rem, 8px by 16px padding. Small: 0.8rem. Large: 0.95rem, 11px by 22px.
- **Primary:** Rowd Blue with On-Brand text. Hover is brand-strong, active is brand-deep.
- **Secondary / light:** white surface, Line border, Ink 2 text. On hover the border turns brand-line and the text turns brand.
- **Dark:** an Ink fill with white text.
- **Outline and status variants:** the status colour at 35% for the border, filled with the soft tint on hover.
- **Focus:** a 3px `--wt-focus` halo. Transitions run 160ms with the brand ease.
- **Public buttons:** 52–56px high, set in the display face at 700 (Thmanyah Sans in Arabic). On hover the gap between label and arrow widens from 12px to 16px. That is the only movement.

### Chips / Badges
- **Style:** stadium, 0.72rem at 600, a soft-tint fill with strong-colour text (primary uses brand-tint with brand text). Neutral badges are Surface 2 with a Line border. Counts on the sidebar are Cyan Pulse with Ink text.

### Cards / Containers
- **Corner style:** 12px. **Background:** Surface on the Ground. **Shadow:** Rest. **Border:** a 1px Line. **Padding:** 18px, with a 14px by 18px header separated by Line Soft.

### Inputs / Fields
- **Style:** at least 40px high, 8px radius, 1px Line border, white fill, 0.9rem text, Faint placeholders, brand caret.
- **Hover:** the border mixes 30% brand into Line. **Focus:** the border turns brand and a 3px focus halo appears.
- **Disabled / read-only:** a Surface 2 fill with Muted text. **Error:** a Bad border with 0.8rem Bad feedback.
- **Sign-in module fields:** labelled fields inside the white stadium, separated by a 1px Line divider. A focused field fills with brand-soft. Password fields have a round reveal button on the end side.

### Navigation
- **Sidebar:** Rowd Blue, On-Brand text. Items are 40px pills at 0.875rem 500. Hover fills with on-brand-faint. Active is the white pill with brand text at 600 and the nav-pill shadow. Group labels are data labels in on-brand-muted. The primary action is a white pill CTA. The footer holds the user, the language switch and the ROWD credit.
- **Top bar:** breadcrumbs (Muted, the current page in Ink at 600, Font Awesome chevrons that flip in RTL), a pill search trigger with a `kbd` hint, and 38px circular icon buttons with a Bad count dot.
- **Mobile:** the Rowd Blue bar plus a white bottom nav. Its active item is brand text on brand-soft in a 14px rounded cell.
- **Language switch:** a segmented pill. The pressed segment is white with brand text, or inverted on brand surfaces.

### Overlays
Toasts appear at the top end, are 380px wide and 12px rounded, with a status icon circle and a 3px progress bar that drains toward the start side. The confirm dialog is 420px with a 16px radius and two pill buttons. Global search is a 640px, 16px-radius box with mono section labels. The notes drawer slides in from the end side (420ms).

### Signature: The Sign-in Stack
On public pages: a blue field, the product name in display type, a one-line tagline, then three modules where the middle one is the working form (email, password, sign in). Remember-me and the secondary links sit below. The ROWD credit and the scroll cue sit at the foot. The form works, and reads correctly, with no JavaScript, no WebGL and reduced motion.

### Motion
- **UI:** ease-out `--wt-ease` (`cubic-bezier(0.22, 1, 0.36, 1)`). Durations are 160ms for hovers and colour, 240ms for overlays, toasts and drawers, and 420ms for the notes drawer slide. No bounce, no overshoot.
- **Public pages only:** one scroll-scrubbed scene (Lenis smooth scroll on the GSAP ticker). The hero stack goes to modules, then the module splits into eight task pills in three lanes, the pills pass review (approved ones turn cyan, with ghost versions behind them), and they lock into score bars sized by this install's real KPI weights before the stack re-forms. The canvas fades out before the white close section. There is one 1.5s expo-out intro in which the outer slabs slide in from opposite sides, the copy and module rise in, and pointer tilt is lerped at 0.06.
- **Auth pages:** the stack with the intro and pointer tilt only, and no scroll story.
- **Reduced motion:** the intro, tilt, idle float, ambient field and smooth scroll are all off. UI animations and transitions drop to 1ms. The static stack still renders.
- **Degradation:** without WebGL the CSS pills show in the slots. On low-power devices (4 or fewer cores, or 4GB or less memory) the renderer uses fewer segments, no antialiasing, pixel ratio 1, and half the ambient field. The scene pauses while the tab is hidden.

## Do's and Don'ts

### Do:
- **Do** read only `--wt-*` tokens in components, and derive any new tint with `color-mix(in oklab, var(--wt-brand) N%, var(--wt-surface))`.
- **Do** use the stadium for anything that is an action, a navigation target or a unit of work, and keep its caps true semicircles.
- **Do** write an `html[dir="rtl"]` counterpart for every Latin type rule (Thmanyah family, letter spacing 0, no uppercase, taller line height), and use logical properties for layout.
- **Do** keep the ROWD credit (`includes/rowd_credit.html`) on every shell and public page, with the white mark on brand surfaces and the navy mark on light ones.
- **Do** source the product name and logo only from Site Settings, and let `_logo_tone` choose the logo backdrop.
- **Do** use IBM Plex Mono for numbers, the formula, times, keys and data-index labels, and keep the formula LTR-isolated.
- **Do** give every 3D surface a static, readable fallback and honour `prefers-reduced-motion`.

### Don't:
- **Don't** load three.js, GSAP scroll scenes or Lenis on working screens. Spectacle belongs on public pages only.
- **Don't** hard-code a customer name, logo or brand colour, or a hex value in the component layer.
- **Don't** recolour, distort or add effects to the ROWD mark, or move the credit into the theme layer.
- **Don't** use amber for anything but alerts, overdue states and warnings.
- **Don't** use bounce, overshoot or spring easing. UI motion stays in the 160–240ms ease-out band.
- **Don't** set headings, sentences or buttons in IBM Plex Mono.
- **Don't** let Arabic inherit negative letter spacing or uppercase.
- **Don't** add new multi-colour icon tiles or rows of identical stat cards. They are legacy patterns awaiting page passes, not system components.

## Known Gaps

- **Home (`templates/pages/dashboard.html`).** Rebuilt as Roadmap first (`templates/includes/wt_home_top.html`, data from `_wt_home_context`); the module toolbar row and the table view still carry legacy styles and the legacy `extra_css` block.

- **Legacy page styles.** Individual app pages (for example `manager_portal.html`, `worker_portal.html`, `admin_dashboard.html`, `admin_users.html`, `audit_logs.html`) still carry large inline `<style>` blocks and `style=""` attributes. These include multi-colour gradient icon tiles (`linear-gradient(135deg, #...)`) and rows of same-size stat cards. The shell, the Bootstrap re-skin and the legacy variable aliases pull them toward the theme, but each page needs its own pass. Do not copy their patterns.
- **Translation overrides.** The admin `TranslationItem` table is applied at render time by `DynamicTranslationMiddleware`. Where a template writes both languages (`lang-en` + `lang-ar` pair), the template wins over the machine-generated `auto.` rows (3,185 of 3,198 at the time of writing); only human-written rows, matched on the English text, may override it. Single-language text is still translated from the table, so the machine rows can still surface there. The client-side map fetch is disabled.
- **Signal Blue is not a brand input.** `--wt-signal` (links, the focus outline, the top 3D slab, the banner glow) and `--bs-link-color-rgb: 45, 107, 255` stay blue when a customer sets a non-blue brand. Until signal is derived from or exposed alongside the brand, a custom brand inherits blue links and a blue glow.