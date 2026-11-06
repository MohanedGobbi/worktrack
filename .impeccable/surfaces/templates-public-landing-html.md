---
version: 1
slug: "templates-public-landing-html"
primary_target: "templates/public/landing.html"
related_targets: ["templates/auth/login.html","templates/auth/register.html"]
---

# Surface: public landing + sign-in (`/`, `/login/`, `/register/`)

Mode: Persuade. Visitor: the customer organisation's own staff and managers arriving at their install. The action is signing in, in its working form, inside the first viewport. Register and password reset are secondary.

Constraints: white-label theme layer (name, logo, colours from SiteConfiguration); fixed "by ROWD Tech" credit with the ROWD mark; Arabic-first, full RTL; 3D must not block typing or navigation, must respect prefers-reduced-motion, and must degrade to a static composition on weak GPUs or when WebGL is missing. No invented customers, numbers or testimonials.

## Direction contract

THESIS: Three modules, one system. The ROWD stadium module is the product's own unit of work, so the page is built from it: you sign in by completing the middle module of the stack. Refuses the category default of a headline beside a floating dashboard screenshot.

OWN-WORLD: Rowd Blue field owning the first viewport, satin extruded stadium modules in blue to signal-blue to cyan, white working surfaces, Montserrat Alternates display, Montserrat body, IBM Plex Mono for data and the formula, Thmanyah for Arabic. Hairline steel rules, 12px cards, 8px inputs, soft blue-tinted shadows. Recognisable with all copy removed: a blue field with a stack of three offset rounded slabs, the middle one white.

STORY: The visitor learns this is their organisation's workspace, understands the path module → task → submission → review → score, sees the real scoring formula, and signs in.

FIRST VIEWPORT: Full-bleed Rowd Blue. Centre: three stadium modules stacked and offset like the mark, the top and bottom ones rendered in WebGL, the middle one a white DOM sign-in panel (email, password, remember, sign in) aligned to the stack. Product name and a one-line headline set large above the stack, the customer logo top-start, language switch top-end, ROWD credit at the bottom edge. Scroll cue at the base.

FORM: Pinned by the user's brand (ROWD guideline, 2026-11-06); it replaced the rolled mashrabiya direction (index 5 on the grounded list). seed:41602e2b7d9450c9. Signature interaction: scrolling disassembles the stack into the workflow (one module becomes a module slab, splits into task pills, pills pass review and lock into the score stack), pointer tilts the stack. Motion grammar: ease-out 200–300ms for UI, one scroll-scrubbed timeline for the scene, no bounce.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
