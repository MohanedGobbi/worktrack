/* Site Settings: live preview, colour inputs and the on-brand contrast check.
   Works on the markup in templates/pages/site_settings.html. Without JS the form still saves. */
(function () {
  'use strict';
  const form = document.getElementById('ss-form');
  if (!form) return;

  const isAr = () => document.documentElement.lang === 'ar' || document.documentElement.dir === 'rtl';
  const T = (en, ar) => (isAr() ? ar : en);
  const INK = '#131925';
  const ROWD = JSON.parse(document.getElementById('ss-rowd').textContent);
  const preview = document.getElementById('ss-preview');
  const custom = document.getElementById('ss-custom');
  const rowdNote = document.getElementById('ss-rowd-note');
  const status = document.getElementById('ss-status');

  const fields = {
    brand: { hex: document.getElementById('ss-brand-hex'), pick: document.getElementById('ss-brand-pick'), cssVar: '--pv-brand' },
    accent: { hex: document.getElementById('ss-accent-hex'), pick: document.getElementById('ss-accent-pick'), cssVar: '--pv-accent' },
    on: { hex: document.getElementById('ss-on-hex'), pick: document.getElementById('ss-on-pick'), cssVar: '--pv-on' },
  };

  /* ── colour helpers ── */
  function norm(v) {
    v = String(v || '').trim();
    if (v && v[0] !== '#') v = '#' + v;
    if (/^#[0-9a-f]{3}$/i.test(v)) v = '#' + v.slice(1).split('').map(c => c + c).join('');
    return /^#[0-9a-f]{6}$/i.test(v) ? v.toLowerCase() : null;
  }
  function lum(hex) {
    const n = parseInt(hex.slice(1), 16);
    const ch = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map(c => {
      c /= 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2];
  }
  function ratio(a, b) {
    const la = lum(a), lb = lum(b);
    return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
  }
  const bestOn = brand => (ratio('#ffffff', brand) >= ratio(INK, brand) ? '#ffffff' : INK);

  /* ── state ── */
  const mode = () => (form.querySelector('input[name="theme_preset"]:checked') || {}).value || 'rowd';
  function current() {
    if (mode() !== 'custom') return { brand: ROWD.brand, accent: ROWD.accent, on: ROWD.on };
    return {
      brand: norm(fields.brand.hex.value) || ROWD.brand,
      accent: norm(fields.accent.hex.value) || ROWD.accent,
      on: norm(fields.on.hex.value) || ROWD.on,
    };
  }

  function paint() {
    const c = current();
    preview.style.setProperty('--pv-brand', c.brand);
    preview.style.setProperty('--pv-accent', c.accent);
    preview.style.setProperty('--pv-on', c.on);
    checkContrast(c);
  }

  /* ── contrast ── */
  const chip = document.getElementById('ss-contrast-chip');
  const verdict = document.getElementById('ss-contrast-verdict');
  const ratioOut = document.getElementById('ss-contrast-ratio');
  const fixBtn = document.getElementById('ss-contrast-fix');
  const box = document.getElementById('ss-contrast');
  function checkContrast(c) {
    const r = ratio(c.on, c.brand);
    chip.style.background = c.brand;
    chip.style.color = c.on;
    ratioOut.textContent = r.toFixed(1) + ' : 1';
    let level = 'ok';
    if (r >= 4.5) verdict.textContent = T('Easy to read', 'سهل القراءة');
    else if (r >= 3) { level = 'warn'; verdict.textContent = T('Only large text is readable', 'يُقرأ النص الكبير فقط'); }
    else { level = 'bad'; verdict.textContent = T('Hard to read', 'صعب القراءة'); }
    box.dataset.level = level;
    const better = bestOn(c.brand);
    fixBtn.hidden = level === 'ok' || better === c.on || ratio(better, c.brand) <= r;
  }
  fixBtn.addEventListener('click', () => {
    set('on', bestOn(current().brand));
    dirty();
  });

  /* ── inputs ── */
  function set(key, value) {
    const v = norm(value);
    if (!v) return;
    fields[key].hex.value = v;
    fields[key].pick.value = v;
    fields[key].hex.classList.remove('is-invalid');
    paint();
  }
  Object.entries(fields).forEach(([key, f]) => {
    const start = norm(f.hex.value);
    if (start) { f.hex.value = start; f.pick.value = start; }
    f.pick.addEventListener('input', () => { set(key, f.pick.value); dirty(); });
    f.hex.addEventListener('input', () => {
      const v = norm(f.hex.value);
      f.hex.classList.toggle('is-invalid', !v && f.hex.value.trim() !== '');
      if (v) { f.pick.value = v; paint(); }
      dirty();
    });
    f.hex.addEventListener('blur', () => { const v = norm(f.hex.value); if (v) f.hex.value = v; });
  });

  form.querySelectorAll('input[name="theme_preset"]').forEach(r => r.addEventListener('change', () => {
    const on = mode() === 'custom';
    if (on) custom.removeAttribute('data-off'); else custom.setAttribute('data-off', '');
    rowdNote.hidden = on;
    paint();
    dirty();
  }));

  form.querySelectorAll('.wt-ss-swatch').forEach(btn => btn.addEventListener('click', () => {
    const custom = form.querySelector('input[name="theme_preset"][value="custom"]');
    if (!custom.checked) { custom.checked = true; custom.dispatchEvent(new Event('change')); }
    set('brand', btn.dataset.brand);
    set('accent', btn.dataset.accent);
    set('on', bestOn(btn.dataset.brand));
    form.querySelectorAll('.wt-ss-swatch').forEach(b => b.setAttribute('aria-pressed', b === btn ? 'true' : 'false'));
    dirty();
  }));

  /* ── text bindings (names, footer) ── */
  form.querySelectorAll('[data-ss-bind]').forEach(input => {
    const key = input.dataset.ssBind;
    const out = preview.querySelector(`[data-ss-out="${key}"]`);
    const fallback = () => {
      if (key === 'foot-en') return document.getElementById('id_app_name').value || 'WorkTrack Pro';
      if (key === 'foot-ar') return document.getElementById('id_app_name_ar').value || document.getElementById('id_app_name').value;
      if (key === 'name-ar') return document.getElementById('id_app_name').value;
      return 'WorkTrack Pro';
    };
    const sync = () => {
      if (out) out.textContent = input.value.trim() || fallback();
      // Footer lines fall back to the names, so refresh them when a name changes.
      if (key.startsWith('name')) form.querySelectorAll('[data-ss-bind^="foot"]').forEach(f => f.dispatchEvent(new Event('ss-sync')));
    };
    input.addEventListener('input', () => { sync(); dirty(); });
    input.addEventListener('ss-sync', () => { if (out && !input.value.trim()) out.textContent = fallback(); });
  });

  /* ── images ── */
  const pvLogo = document.getElementById('ss-pv-logo');
  const logoThumb = document.getElementById('ss-logo-thumb');
  const monogram = '<span class="wt-monogram">wt</span>';
  function logoTone(img) {
    // Same rule as core.context_processors._logo_tone: mostly light ink sits straight on the brand.
    try {
      const c = document.createElement('canvas');
      const s = 48; c.width = s; c.height = s;
      const x = c.getContext('2d');
      x.drawImage(img, 0, 0, s, s);
      const d = x.getImageData(0, 0, s, s).data;
      let t = 0, w = 0;
      for (let i = 0; i < d.length; i += 4) {
        const a = d[i + 3];
        if (a < 40) continue;
        const k = a / 255;
        t += k * (0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2]) / 255;
        w += k;
      }
      return w && t / w > 0.72 ? 'light' : 'dark';
    } catch (e) { return 'dark'; }
  }
  function showLogo(url) {
    [pvLogo, logoThumb].forEach(el => {
      el.textContent = '';
      if (!url) { el.innerHTML = monogram; return; }
      const img = new Image();
      img.alt = '';
      img.onload = () => { el.classList.toggle('is-on-brand', logoTone(img) === 'light'); };
      img.src = url;
      el.appendChild(img);
    });
    if (!url) { pvLogo.classList.remove('is-on-brand'); logoThumb.classList.remove('is-on-brand'); }
  }
  const logoInput = document.getElementById('id_logo');
  const logoClear = document.getElementById('logo-clear');
  const logoStart = pvLogo.querySelector('img') ? pvLogo.querySelector('img').src : '';
  logoInput.addEventListener('change', () => {
    const f = logoInput.files[0];
    if (logoClear) logoClear.checked = false;
    showLogo(f ? URL.createObjectURL(f) : logoStart);
    dirty();
  });
  if (logoClear) logoClear.addEventListener('change', () => {
    showLogo(logoClear.checked ? '' : logoStart);
    if (logoClear.checked) logoInput.value = '';
    dirty();
  });

  const pvBanner = document.getElementById('ss-pv-banner');
  const bannerThumb = document.getElementById('ss-banner-thumb');
  const bannerInput = document.getElementById('id_banner_image');
  const bannerClear = document.getElementById('banner_image-clear');
  const bannerStart = pvBanner.style.getPropertyValue('--pv-banner');
  const bannerThumbStart = bannerThumb.style.backgroundImage;
  function showBanner(url) {
    const css = url ? `url("${url}")` : '';
    if (css) pvBanner.style.setProperty('--pv-banner', css); else pvBanner.style.removeProperty('--pv-banner');
    bannerThumb.style.backgroundImage = css;
  }
  bannerInput.addEventListener('change', () => {
    const f = bannerInput.files[0];
    if (bannerClear) bannerClear.checked = false;
    if (f) showBanner(URL.createObjectURL(f));
    else { pvBanner.style.setProperty('--pv-banner', bannerStart); bannerThumb.style.backgroundImage = bannerThumbStart; }
    dirty();
  });
  if (bannerClear) bannerClear.addEventListener('change', () => {
    if (bannerClear.checked) { bannerInput.value = ''; showBanner(''); }
    else { pvBanner.style.setProperty('--pv-banner', bannerStart); bannerThumb.style.backgroundImage = bannerThumbStart; }
    dirty();
  });

  /* ── unsaved state ── */
  let isDirty = false;
  function dirty() {
    if (isDirty) return;
    isDirty = true;
    status.textContent = T('Unsaved changes', 'تغييرات غير محفوظة');
    document.getElementById('ss-unsaved').hidden = false;
  }
  form.addEventListener('input', dirty);
  form.addEventListener('submit', e => {
    const bad = Object.values(fields).find(f => mode() === 'custom' && !norm(f.hex.value));
    if (bad) {
      e.preventDefault();
      bad.hex.classList.add('is-invalid');
      bad.hex.focus();
      status.textContent = T('Use a colour such as #0033a0.', 'استخدم لونًا مثل ‎#0033a0.');
      return;
    }
    isDirty = false;
  });
  window.addEventListener('beforeunload', e => { if (isDirty) { e.preventDefault(); e.returnValue = ''; } });

  paint();
})();
