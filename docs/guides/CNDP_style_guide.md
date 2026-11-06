# CNDP Design System: Style Guide

**المركز الوطني للوثائق التربوية** (National Centre for Educational Documentation)

Use this file as the single reference to reproduce the look and feel of the CNDP website on other pages or platforms.

---

## 1. Concept

A **dark crimson reading room**. Deep wine-red backgrounds carry glowing red accents, a bright "paper" band (cream-pink) holds content cards, and 3D elements (folded pages, a rotating shelf, a smart book) tie everything to the theme: **documents, books, archives, knowledge**.

One committed look: **deep red + white**. There is no light/dark switch.

**Keywords:** archival, bookish, warm, premium, bilingual (Arabic first, RTL), 3D paper, diamond lattice.

---

## 2. Color Tokens

```css
:root {
  --ink:       #14060a;  /* page background (near-black red) */
  --ink-2:     #1e0a11;
  --wine:      #4a0b16;  /* deep gradient end */
  --crimson:   #9b1022;  /* primary brand red, buttons, labels on paper */
  --red:       #d4202f;  /* bright red, icon tiles, accents */
  --ember:     #ff5a5f;  /* glow / highlight / eyebrow text / focus ring */
  --paper:     #fbf3f2;  /* light section background */
  --paper-2:   #f3e3e1;  /* info boxes on paper */
  --paper-ink: #2a0a10;  /* text on paper */
  --fg:        #fdf1f0;  /* main text on dark */
  --muted:     rgba(253,241,240,.70);  /* secondary text on dark */
  --line:      rgba(255,255,255,.16);  /* borders on dark */
  --line-dark: rgba(42,10,16,.16);     /* borders on paper */
}
```

### Usage rules
| Surface | Background | Text | Accent |
|---|---|---|---|
| Dark sections | `--ink` to `#1b0810` gradient | `--fg` / `--muted` | `--ember` |
| Paper section | `--paper` | `--paper-ink` | `--crimson` / `--red` |
| Cards on dark | white 9% → 2% gradient + `--line` border | `--fg` | `--ember` for small labels |
| Cards on paper | crimson → wine gradient | white | `#ffd2d4` for dates/status |
| Footer | `#0c0306` | `--muted` | white on hover |

### Signature gradients
```css
/* Hero glow */
background:
  radial-gradient(60% 70% at 78% 42%, rgba(212,32,47,.55), transparent 70%),
  radial-gradient(50% 60% at 15% 100%, rgba(155,16,34,.45), transparent 70%),
  linear-gradient(160deg, #230810 0%, var(--ink) 55%, #0c0306 100%);

/* Activity card */
background: linear-gradient(160deg, #a8132a, var(--wine) 90%);

/* Icon tile */
background: linear-gradient(145deg, var(--red), var(--crimson));

/* Progress bar */
background: linear-gradient(90deg, var(--ember), #fff);
```
In LTR mode the hero glow is mirrored (`78%` becomes `22%`).

---

## 3. Typography

Google Fonts:
```html
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600&family=Outfit:wght@300;500;700;800&family=Reem+Kufi:wght@400;500;600;700&display=swap">
```

```css
--f-display: "Outfit", "Reem Kufi", system-ui, sans-serif;               /* English headings, numbers, acronym */
--f-kufi:    "Reem Kufi", "Outfit", system-ui, sans-serif;               /* Arabic headings */
--f-body:    "IBM Plex Sans Arabic", "Outfit", system-ui, sans-serif;    /* body text, both languages */
```

| Element | Font | Size | Weight |
|---|---|---|---|
| Body | Plex Arabic | 16px, line-height 1.7 | 400 |
| H1 (hero) | Reem Kufi (AR) / Outfit (EN) | `clamp(38px, 6.2vw, 78px)`, lh 1.12 | 700 |
| H2 (section) | same | `clamp(30px, 4.2vw, 52px)`, max-width 16em | 600 |
| H3 (card) | same | 22 to 24px | 600 |
| Acronym "CNDP" | Outfit | `clamp(30px, 4.4vw, 54px)`, letter-spacing `.18em` | 800 |
| Eyebrow (small label above H2) | body | 14px (EN: 12px uppercase, tracking `.16em`) | 500 |
| Lede / subtitle | body | `clamp(17px, 1.6vw, 20px)` | 400, `--muted` |

- Always use `text-wrap: balance` on headings.
- In the hero, one word of the title is highlighted in `--ember` using `<em>` (no italics).
- Big Dewey numbers (e.g. **371.3**) use Outfit 800, in `--crimson`.

---

## 4. Layout and Spacing

```css
--gutter: clamp(16px, 4vw, 48px);
--maxw: 1180px;
.wrap { max-width: var(--maxw); margin-inline: auto; padding-inline: var(--gutter); }
.sec  { padding-block: clamp(64px, 9vw, 120px); }
```

- Card grids use 3 columns, 2 columns below 960px and 1 column below 600px. The gap is 22 to 24px.
- Radius scale: **cards 22px**, panels 18px, info boxes 14px, popup 26px, buttons/chips/tags **999px (pill)**.
- Shadows are deep and soft, never grey, for example `0 30px 60px -30px rgba(0,0,0,.8)`.
- Always use **logical properties** (`margin-inline`, `inset-inline-start`, `padding-inline`) so RTL/LTR flip automatically.

---

## 5. Signature Background: Diamond Lattice

A faint diamond-and-dot pattern echoing the logo, fading out with a radial mask:

```css
.lattice {
  position: absolute; inset: 0; pointer-events: none; opacity: .55;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='72' height='72' viewBox='0 0 72 72'><g fill='none' stroke='%23ff5a5f' stroke-opacity='0.16' stroke-width='1'><path d='M36 6 66 36 36 66 6 36Z'/><circle cx='36' cy='36' r='4'/></g></svg>");
  background-size: 72px 72px;
  mask-image: radial-gradient(ellipse at 70% 40%, #000 0%, transparent 72%);
}
```
Place it as the first child of dark sections (hero, role). Vary the mask position per section.

---

## 6. Components

### Navigation bar
- Sticky, `rgba(20,6,10,.72)` with `backdrop-filter: blur(14px)`, 1px bottom `--line`.
- Brand: 38px logo, "CNDP" in Outfit 800, with the full Arabic name in small muted text beneath.
- Links are pill-shaped and turn into a white 8% background on hover. A language toggle pill sits at the end.
- Hidden links on mobile (below 760px); the language button stays.

### Buttons
| Type | Style |
|---|---|
| **Primary** | White pill, `--crimson` text, 14×26px padding, glow shadow `rgba(255,90,95,.6)`, lifts `-2px` on hover |
| **Ghost** | Transparent, 1px `rgba(255,255,255,.35)` border, white text |
| **Red** (on paper) | `--crimson` fill, white text, count badge `+N` in a translucent white pill |
| **More / outline** (inside cards) | Transparent, 1px white 40% border, fills white with crimson text on card hover. Includes an arrow icon (flipped in RTL) |

### Kicker (status pill above H1)
Pill with 1px `--line` border and a pulsing `--ember` dot (`pulse` animation, 2.4s).

### Chips (filters)
Pill, transparent with `--line-dark` border. Active (`aria-pressed="true"`) turns `--crimson` with white text.

### Role card (dark section)
Glassy card (white 9% to 2% gradient), 22px radius, inset top highlight, a 56px red gradient icon tile, ember verb label, H3, muted paragraph. **3D tilt on hover** (see Motion).

### Activity card (paper section)
- Vertical card: 200px image at the top, then date (small, `#ffd2d4`), H3, text, "Read more" button.
- Over the image: type tag (top start) and status pill (top end), both dark translucent with blur. A dark gradient at the bottom of the image improves legibility.
- The **featured** card spans 2 columns and is horizontal (image + text); it becomes vertical on mobile.
- Image zooms to `scale(1.12) rotate(.6deg)` over .9s on hover.
- First 5 cards show, then a **"Show more +N"** button reveals the rest.

### Popup (detail modal)
- Overlay: `rgba(12,3,6,.72)` plus `blur(10px)`.
- Card: paper background, 26px radius, max-width 760px; image header (210px) with slow Ken-Burns zoom; tag + status; H3; lead text; 3 info boxes (date, time, venue); programme list; footer with Previous / counter / Next.
- Entrance: `rotateX(-16deg) translateY(60px) scale(.9)` to none in .6s (`cubic-bezier(.2,.8,.2,1)`).
- Switching items plays a page-turn `rotateY(-28deg)` swap animation.
- Close with ×, Esc, or a click outside. Arrow keys navigate.

### Dewey shelf ring (3D carousel)
Six paper panels (210×270) placed on a ring (`rotateY(i*60deg) translateZ(330px)`), draggable, with arrows, slow auto-drift and a label under the ring. Each panel has a huge crimson Dewey number, a thin red rule and a short title and description.

### Smart book navigation
- **Floating button** (66px circle, bottom corner): a miniature 3D crimson book that straightens on hover, a chapter-number badge (`00` to `04`), and a tooltip.
- **Open book overlay:** a crimson cover (logo + CNDP) swings open (`rotateY(-180deg)`, 1.1s) to reveal a table of contents. Each entry has a big crimson number, a title and a subtitle. Choosing a chapter **turns the page** (leaf rotates), then triggers the page-flip transition.

### Page-flip transition
Seven full-height crimson strips rotate in (`rotateY(90deg)` to `0`, staggered 70ms), show the logo and chapter title, the page scrolls instantly, then the strips rotate out (`-90deg`). Total about 2.1s. Applied to every in-page `#anchor` link.

### Footer
`#0c0306`, 56px logo, short about text, link row, and a copyright line with a top border.

### Scroll progress bar
3px fixed bar at the top, `scaleX` tied to scroll, origin on the reading start side.

---

## 7. Motion Language

| Effect | Spec |
|---|---|
| **3D tilt** (cards) | `perspective(900px) rotateX/rotateY ±7deg` following the pointer, `transition: .25s ease-out`, plus a radial white highlight at the cursor (`--mx/--my`). Inner items use `translateZ(14 to 40px)` for depth |
| **Reveal on scroll** | `opacity 0 → 1`, `translateY(34px) rotateX(10deg) → none`, .8s `cubic-bezier(.2,.7,.2,1)` via IntersectionObserver |
| **Card entrance** | `rise` (`translate 0 22px` to 0), .6s, staggered by 70ms |
| **Hover lift** | Buttons `translateY(-2px/-3px)` |
| **Ease curves** | Smooth: `cubic-bezier(.2,.8,.2,1)`; page turn: `cubic-bezier(.5,.1,.2,1)` |
| **Hero** | Three.js scene: central gem, four folded pages, floating discs, tilted rings, 64 drifting documents, dust particles; follows the pointer; drag to spin |

**Always** provide a `prefers-reduced-motion: reduce` fallback (skip the tilt, flip and auto-drift; shorten transitions to about 0.01s).

---

## 8. Imagery

- Brand logo: white diamond/folded-page emblem, used on dark/crimson backgrounds with a red glow: `drop-shadow(0 0 40px rgba(255,90,95,.6))`.
- Activity illustrations are flat SVG scenes (exhibition, training, forum, publication) built from: crimson to wine gradient, the diamond lattice at 10% opacity, a large translucent circle (top end), white paper rectangles and dark silhouettes. Use 3 gradient variants for variety: `#e0303f→#4a0b16`, `#ff6a6f→#8a1226`, `#b3172a→#1e0a11`.
- Real photos work too. Put them in `object-fit: cover` and keep the dark gradient overlay at the bottom of the image.
- Icons are 24px line icons: stroke `1.6 to 2`, round caps and joins, white on the red tile.

---

## 9. Bilingual / RTL Rules

- Root: `<div id="app" lang="ar" dir="rtl">`, with the language switched by JS (`lang` + `dir`), saved in `localStorage`.
- Duplicate content with `<span class="ar">…</span><span class="en">…</span>` and hide with:
  ```css
  #app[lang="ar"] .en { display: none !important; }
  #app[lang="en"] .ar { display: none !important; }
  ```
- Flip directional icons in RTL: `#app[dir="rtl"] svg.arrow { transform: scaleX(-1); }`.
- 3D scenes (ring, book) are forced `direction: ltr` for geometry, while their text is set back to `rtl` for Arabic.
- English labels get a more technical look: uppercase and wide letter-spacing on eyebrows and verbs.

---

## 10. Accessibility Checklist

- Focus ring: `outline: 2px solid var(--ember); outline-offset: 3px`.
- Modal: `role="dialog" aria-modal="true" aria-labelledby`, focus moves to the close button and returns on close, Esc closes.
- Buttons have `aria-label`s; decorative layers use `aria-hidden="true"`.
- Chips use `aria-pressed`; the ring label uses `aria-live="polite"`.
- Keep contrast high: white or `--fg` on dark red; `--paper-ink` on paper.

---

## 11. Quick Starter Snippet

```html
<div id="app" lang="ar" dir="rtl">
  <section class="hero">
    <div class="lattice"></div>
    <div class="wrap">
      <span class="kicker"><i></i>ذاكرة المنظومة التربوية الجزائرية</span>
      <h1>المركز الوطني<br>لل<em>وثائق</em> التربوية</h1>
      <p class="lede">نجمع الوثيقة التربوية ونحفظها وننشرها…</p>
      <div class="cta">
        <a class="btn btn-primary" href="#role">اكتشف دور المركز</a>
        <a class="btn btn-ghost" href="#activities">آخر الأنشطة</a>
      </div>
    </div>
  </section>
</div>
```

---

## 12. Do / Don't

**Do**
- Alternate dark crimson sections with one bright paper band.
- Use pill shapes for every small control.
- Add depth with `translateZ`, soft deep shadows and the cursor highlight.
- Keep one accent: `--ember` on dark, `--crimson` on paper.

**Don't**
- Don't add other hues (blue, green, purple). The palette is red, pink-white and near-black only.
- Don't use pure black or grey shadows. Tint them with wine or ink.
- Don't use sharp corners.
- Don't use physical `left/right` properties. Use logical ones.
- Don't ship motion without a reduced-motion fallback.
