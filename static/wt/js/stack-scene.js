/* ==========================================================================
   WorkTrack Pro · "Three modules, one system" scene
   - Orthographic camera in CSS pixels: 3D modules sit exactly on their DOM slots.
   - Landing: scrolling carries the stack through the workflow
       hero stack -> modules -> tasks -> review (versions) -> score bars -> stack.
   - Auth pages: the stack only, with pointer tilt.
   Colours come from the theme tokens, so a re-themed install re-tints the scene.
   Falls back to the CSS pills when WebGL is missing; honours reduced motion.
   ========================================================================== */
import * as THREE from 'three';

const canvas = document.getElementById('lpCanvas');
const mode = document.body.dataset.scene || 'auth';
const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function webglAvailable() {
  try {
    const c = document.createElement('canvas');
    return !!(window.WebGLRenderingContext && (c.getContext('webgl2') || c.getContext('webgl')));
  } catch (e) { return false; }
}

if (canvas && webglAvailable()) {
  try { start(); } catch (err) { console.warn('[wt] scene disabled:', err); }
}

function start() {
  const root = document.documentElement;
  const css = (name, fallback) => (getComputedStyle(root).getPropertyValue(name).trim() || fallback);
  const col = (v) => new THREE.Color(v);
  const C = {
    brand: col(css('--wt-brand', '#0033a0')),
    signal: col(css('--wt-signal', '#2d6bff')),
    accent: col(css('--wt-accent', '#19bedc')),
    white: col(css('--wt-on-brand', '#ffffff')),
  };
  C.mist = C.white.clone().lerp(C.signal, 0.35);
  // Slab tones lifted off the field so the stack always reads as three objects
  C.slabA = C.signal.clone().lerp(C.white, 0.12);
  C.slabC = C.accent.clone().lerp(C.white, 0.06);
  C.ghost = C.signal.clone().lerp(C.white, 0.15);
  const ramp = [C.white.clone(), C.white.clone().lerp(C.accent, 0.45), C.accent.clone(), C.accent.clone().lerp(C.signal, 0.55)];

  const lowPower = (navigator.hardwareConcurrency || 8) <= 4 || (navigator.deviceMemory || 8) <= 4;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: !lowPower, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, lowPower ? 1 : 1.75));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.toneMappingExposure = 1.05;

  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, -3000, 3000);
  camera.position.z = 1000;

  scene.add(new THREE.HemisphereLight(0xffffff, C.brand.clone().multiplyScalar(0.6), 1.25));
  const key = new THREE.DirectionalLight(0xffffff, 2.4);
  key.position.set(-0.45, 0.7, 1.6);
  scene.add(key);
  const rim = new THREE.DirectionalLight(C.accent, 0.9);
  rim.position.set(0.9, -0.4, -0.6);
  scene.add(rim);

  /* ── Stadium module geometry with a stretchable middle ─────────────────
     Unit height 1, base length L0. stretch() moves the round caps outward
     instead of scaling them, so ends stay true semicircles at any length. */
  const L0 = 4;
  const HALF0 = L0 / 2 - 0.5;
  const BEVEL = 0.08;
  const proto = (() => {
    const r = 0.5;
    const s = new THREE.Shape();
    s.moveTo(-HALF0, -r);
    s.lineTo(HALF0, -r);
    s.absarc(HALF0, 0, r, -Math.PI / 2, Math.PI / 2, false);
    s.lineTo(-HALF0, r);
    s.absarc(-HALF0, 0, r, Math.PI / 2, Math.PI * 1.5, false);
    const g = new THREE.ExtrudeGeometry(s, {
      depth: 0.42, bevelEnabled: true, bevelThickness: 0.1, bevelSize: BEVEL,
      bevelSegments: lowPower ? 3 : 6, curveSegments: lowPower ? 16 : 28,
    });
    g.translate(0, 0, -0.21);
    return g;
  })();
  const baseX = (() => {
    const a = proto.attributes.position.array;
    const out = new Float32Array(a.length / 3);
    for (let i = 0; i < out.length; i++) out[i] = a[i * 3];
    return out;
  })();

  function stretch(geo, aspect) {
    const q = Math.round(aspect * 100) / 100;
    if (geo.userData.aspect === q) return;
    const half = Math.max(q / 2 - 0.5, 0.001);
    const arr = geo.attributes.position.array;
    for (let i = 0; i < baseX.length; i++) {
      const x = baseX[i];
      const ax = Math.abs(x);
      arr[i * 3] = ax <= HALF0 + 1e-6 ? x * (half / HALF0) : Math.sign(x) * (ax - HALF0 + half);
    }
    geo.attributes.position.needsUpdate = true;
    geo.computeBoundingSphere();
    geo.userData.aspect = q;
  }

  const TILT_X = 0.44;
  const TILT_Y = -0.16;
  const meshes = [];
  function makeModule(color) {
    const geo = proto.clone();
    const mat = new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.32, roughness: 0.3, metalness: 0.04, transparent: true, opacity: 0 });
    const m = new THREE.Mesh(geo, mat);
    m.userData.phase = Math.random() * Math.PI * 2;
    m.rotation.set(TILT_X, TILT_Y, 0);
    scene.add(m);
    meshes.push(m);
    return m;
  }
  // State: x, y, z, len, h (px), o (opacity), c (THREE.Color)
  const S = (x, y, len, h, o, c, z = 0) => ({ x, y, z, len, h, o, c });
  const mix = (a, b, t) => a + (b - a) * t;
  function lerpState(a, b, t, out) {
    out.x = mix(a.x, b.x, t); out.y = mix(a.y, b.y, t); out.z = mix(a.z, b.z, t);
    out.len = mix(a.len, b.len, t); out.h = mix(a.h, b.h, t); out.o = mix(a.o, b.o, t);
    out.c.copy(a.c).lerp(b.c, t);
    return out;
  }
  function apply(m, s, idle, t) {
    const h = Math.max(s.h, 0.5) / (1 + BEVEL * 2);
    stretch(m.geometry, Math.max(s.len / Math.max(s.h, 0.5), 1.02));
    m.scale.setScalar(h);
    m.position.set(s.x, s.y + Math.sin(t * 0.9 + m.userData.phase) * 3.2 * idle, s.z);
    m.material.color.copy(s.c);
    m.material.emissive.copy(s.c);
    m.material.opacity = s.o;
    m.visible = s.o > 0.005;
  }

  const A = makeModule(C.signal);
  const B = makeModule(C.white);
  const Cm = makeModule(C.accent);
  const TASKS = 8;
  const tasks = Array.from({ length: TASKS }, () => makeModule(C.white));
  const ghosts = Array.from({ length: TASKS }, () => makeModule(C.ghost));
  const weights = Array.from(document.querySelectorAll('[data-weights] li')).map((li) => parseFloat(getComputedStyle(li).getPropertyValue('--lp-w')) || 25);
  const bars = weights.map((_, i) => makeModule(ramp[i % ramp.length]));

  // Ambient field: small modules drifting far behind the stack
  const FIELD = reduce ? 0 : (lowPower ? 8 : 16);
  let field = null;
  const fieldData = [];
  if (FIELD) {
    const g = proto.clone();
    stretch(g, 3.2);
    const mat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.5, metalness: 0, transparent: true, opacity: 0.11, depthWrite: false });
    field = new THREE.InstancedMesh(g, mat, FIELD);
    field.renderOrder = -1;
    const tints = [C.signal, C.mist, C.accent];
    for (let i = 0; i < FIELD; i++) {
      fieldData.push({ u: Math.random(), v: Math.random(), z: -900 - Math.random() * 600, s: 9 + Math.random() * 16, sp: 0.004 + Math.random() * 0.01, r: (Math.random() - 0.5) * 0.6 });
      field.setColorAt(i, tints[i % tints.length]);
    }
    scene.add(field);
  }
  const dummy = new THREE.Object3D();

  /* ── Layout ───────────────────────────────────────────────────────────── */
  let W = 1, H = 1;
  const slotA = document.querySelector('[data-slot="a"]');
  const slotC = document.querySelector('[data-slot="c"]');
  const moduleEl = document.querySelector('[data-module]');
  const story = document.getElementById('lpStory');
  const closeEl = document.querySelector('.lp-close');
  const steps = story ? story.querySelectorAll('[data-step]') : [];

  function rect(el) {
    const r = el.getBoundingClientRect();
    return { x: r.left + r.width / 2 - W / 2, y: H / 2 - (r.top + r.height / 2), w: r.width, h: r.height };
  }
  function resize() {
    W = window.innerWidth; H = window.innerHeight;
    renderer.setSize(W, H, false);
    camera.left = -W / 2; camera.right = W / 2; camera.top = H / 2; camera.bottom = -H / 2;
    camera.updateProjectionMatrix();
  }
  resize();
  window.addEventListener('resize', resize);

  // Pointer tilt
  const tilt = { x: 0, y: 0, tx: 0, ty: 0 };
  if (!reduce) {
    window.addEventListener('pointermove', (e) => {
      tilt.tx = (e.clientY / H - 0.5) * 0.22;
      tilt.ty = (e.clientX / W - 0.5) * 0.3;
    }, { passive: true });
  }

  // Intro: the outer modules slide in from opposite sides and lock around the form
  const intro = { v: reduce ? 1 : 0 };
  if (!reduce) {
    if (window.gsap) window.gsap.to(intro, { v: 1, duration: 1.5, ease: 'expo.out', delay: 0.15 });
    else intro.v = 1;
  }

  const smooth = (e0, e1, x) => { const t = Math.min(Math.max((x - e0) / (e1 - e0), 0), 1); return t * t * (3 - 2 * t); };
  const easeIO = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

  /* ── Keyframes ────────────────────────────────────────────────────────── */
  const tmp = () => S(0, 0, 0, 0, 0, new THREE.Color());
  const scratch = { a: tmp(), b: tmp(), c: tmp(), t: tasks.map(tmp), g: ghosts.map(tmp), r: bars.map(tmp) };

  function stage() {
    const wide = W > 900;
    const dir = document.documentElement.dir === 'rtl' ? -1 : 1;
    const size = wide ? Math.min(H * 0.82, W * 0.4) : Math.min(W * 0.88, H * 0.46);
    return { cx: wide ? dir * W * 0.22 : 0, cy: wide ? 0 : H * 0.2, s: size, dir };
  }

  function frameAt(k, st, hero) {
    const { cx, cy, s, dir } = st;
    const P = (x, y) => ({ x: cx + dir * x * s, y: cy + y * s });
    const H_ = 0.105 * s, Ht = 0.075 * s;
    const f = { a: null, b: null, c: null, t: [], g: [], r: [] };
    const stack = {
      a: () => { const p = P(-0.05, 0.135); return S(p.x, p.y, 0.8 * s, H_, 1, C.slabA); },
      b: () => { const p = P(0, 0); return S(p.x, p.y, 0.82 * s, H_, 1, C.white); },
      c: () => { const p = P(0.13, -0.135); return S(p.x, p.y, 0.52 * s, H_, 1, C.slabC); },
    };
    const lanes = [-0.36, 0, 0.36];
    const laneOf = [0, 0, 0, 1, 1, 1, 2, 2];
    const rowOf = [0, 1, 2, 0, 1, 2, 0, 1];
    const maxW = Math.max(...weights, 1);

    if (k === 0) {
      // Hero: live DOM slots
      const ra = hero.a, rb = hero.b, rc = hero.c;
      const slide = (1 - intro.v) * W * 0.6;
      f.a = S(ra.x - dir * slide, ra.y, ra.w, ra.h, intro.v, C.slabA);
      f.b = S(rb.x, rb.y, rb.w, rb.h, 0, C.white);
      f.c = S(rc.x + dir * slide, rc.y, rc.w, rc.h, intro.v, C.slabC);
      for (let i = 0; i < TASKS; i++) { f.t.push(S(rb.x, rb.y, rb.h * 1.6, rb.h * 0.7, 0, C.white)); f.g.push(S(rb.x, rb.y, rb.h * 1.6, rb.h * 0.7, 0, C.ghost, -60)); }
      bars.forEach((_, i) => f.r.push(S(rb.x, rb.y, rb.h, rb.h * 0.6, 0, ramp[i % ramp.length])));
      return f;
    }
    if (k === 1 || k === 5) {
      f.a = stack.a(); f.b = stack.b(); f.c = stack.c();
      const b = f.b;
      for (let i = 0; i < TASKS; i++) { f.t.push(S(b.x + dir * (i - 3.5) * 0.08 * s, b.y, 0.2 * s, Ht, 0, C.white)); f.g.push(S(b.x, b.y, 0.2 * s, Ht, 0, C.ghost, -60)); }
      bars.forEach((_, i) => { const p = P(-0.36, 0.2 - i * 0.13); f.r.push(S(p.x, p.y, 0.12 * s, Ht, 0, ramp[i % ramp.length])); });
      return f;
    }
    // Outer modules step aside while the work happens
    const pa = P(-0.2, 0.43), pc = P(0.26, -0.43);
    f.a = S(pa.x, pa.y, 0.62 * s, H_ * 0.8, 0.32, C.signal, -120);
    f.c = S(pc.x, pc.y, 0.42 * s, H_ * 0.8, 0.32, C.accent, -120);
    const pb = P(0, 0);
    f.b = S(pb.x, pb.y, 0.5 * s, H_, 0, C.white);
    for (let i = 0; i < TASKS; i++) {
      if (k === 2) {
        const p = P(lanes[laneOf[i]], 0.2 - rowOf[i] * 0.14);
        f.t.push(S(p.x, p.y, 0.27 * s, Ht, 1, laneOf[i] === 2 ? C.accent : C.white));
        f.g.push(S(p.x, p.y, 0.27 * s, Ht, 0, C.ghost, -60));
      } else if (k === 3) {
        const p = P(0.04, 0.3 - i * 0.085);
        const approved = i !== 2 && i !== 5;
        f.t.push(S(p.x, p.y, 0.44 * s, Ht * 0.92, 1, approved ? C.accent : C.white));
        const gp = P(0.04 - 0.035, 0.3 - i * 0.085 + 0.03);
        f.g.push(S(gp.x, gp.y, 0.44 * s, Ht * 0.92, 0.55, C.ghost, -80));
      } else {
        const bi = Math.min(Math.floor(i / 2), bars.length - 1);
        const L = (weights[bi] / maxW) * 0.74 * s;
        const p = P(-0.36, 0.2 - bi * 0.13);
        f.t.push(S(p.x + dir * L * 0.5, p.y, 0.1 * s, Ht, 0, ramp[bi % ramp.length]));
        f.g.push(S(p.x + dir * L * 0.5, p.y, 0.1 * s, Ht, 0, C.ghost, -80));
      }
    }
    bars.forEach((_, i) => {
      const L = (weights[i] / maxW) * 0.74 * s;
      const p = P(-0.36, 0.2 - i * 0.13);
      const on = k === 4;
      f.r.push(S(p.x + dir * (on ? L : 0.12 * s) * 0.5, p.y, on ? L : 0.12 * s, Ht, on ? 1 : 0, ramp[i % ramp.length]));
    });
    return f;
  }

  /* ── Progress from scroll ─────────────────────────────────────────────── */
  function progress() {
    if (mode !== 'landing' || !story || !steps.length) return { p: 0, fade: 1 };
    const sr = story.getBoundingClientRect();
    const stepH = sr.height / steps.length;
    const p = Math.min(Math.max((H / 2 - sr.top) / stepH + 0.5, 0), steps.length);
    let fade = 1;
    if (closeEl) fade = smooth(H * 0.15, H * 0.75, closeEl.getBoundingClientRect().top);
    return { p, fade };
  }

  function heroRects() {
    const fallback = { x: 0, y: 0, w: 10, h: 10 };
    return { a: slotA ? rect(slotA) : fallback, b: moduleEl ? rect(moduleEl) : fallback, c: slotC ? rect(slotC) : fallback };
  }

  /* ── Loop ─────────────────────────────────────────────────────────────── */
  const clock = new THREE.Clock();
  let started = false;
  function render() {
    requestAnimationFrame(render);
    if (document.hidden) return;
    const t = clock.getElapsedTime();
    const { p, fade } = progress();
    if (started) canvas.style.opacity = fade < 0.999 ? String(fade) : '';
    if (fade <= 0.001 && started) return;

    const st = stage();
    const hero = heroRects();
    const k = Math.min(Math.floor(p), steps.length ? steps.length - 1 : 0);
    let frac = p - k;
    if (k === 0) frac = smooth(0.08, 0.92, frac);
    else frac = easeIO(Math.min(Math.max((frac - 0.22) / 0.56, 0), 1));
    const f0 = frameAt(k, st, hero);
    const f1 = mode === 'landing' && steps.length ? frameAt(k + 1, st, hero) : f0;

    const idle = reduce ? 0 : 1;
    const bFade = k === 0 ? smooth(0.35, 0.85, p) : 1;
    apply(A, lerpState(f0.a, f1.a, frac, scratch.a), idle, t);
    const sb = lerpState(f0.b, f1.b, frac, scratch.b);
    if (k === 0) sb.o *= bFade;
    apply(B, sb, idle, t);
    apply(Cm, lerpState(f0.c, f1.c, frac, scratch.c), idle, t);
    tasks.forEach((m, i) => apply(m, lerpState(f0.t[i], f1.t[i], frac, scratch.t[i]), idle * 0.6, t));
    ghosts.forEach((m, i) => apply(m, lerpState(f0.g[i], f1.g[i], frac, scratch.g[i]), idle * 0.6, t));
    bars.forEach((m, i) => apply(m, lerpState(f0.r[i], f1.r[i], frac, scratch.r[i]), 0, t));

    tilt.x += (tilt.tx - tilt.x) * 0.06;
    tilt.y += (tilt.ty - tilt.y) * 0.06;
    for (const m of meshes) m.rotation.set(TILT_X + tilt.x, TILT_Y + tilt.y * (m === B ? 0.6 : 1), 0);

    if (field) {
      const scrollY = window.scrollY || 0;
      for (let i = 0; i < FIELD; i++) {
        const d = fieldData[i];
        d.v = (d.v + d.sp * 0.016) % 1.2;
        dummy.position.set((d.u - 0.5) * W * 1.1, ((d.v - 0.6) * H * 1.3) + scrollY * 0.08 % H, d.z);
        dummy.rotation.set(TILT_X, TILT_Y + d.r, d.r * 0.4);
        dummy.scale.setScalar(d.s);
        dummy.updateMatrix();
        field.setMatrixAt(i, dummy.matrix);
      }
      field.instanceMatrix.needsUpdate = true;
    }

    renderer.render(scene, camera);
    if (!started) {
      started = true;
      document.body.classList.add('has-scene');
      canvas.classList.add('is-live');
      window.setTimeout(() => { canvas.style.transition = 'none'; }, 700);
    }
  }
  requestAnimationFrame(render);

  // Language flips direction: the stage mirrors on the next frame automatically.
  window.addEventListener('languagechange', resize);
}
