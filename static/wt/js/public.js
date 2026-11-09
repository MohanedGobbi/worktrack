/* WorkTrack Pro · public pages: smooth scroll, intro, form behaviour. */
(function () {
  'use strict';
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Show / hide password
  document.querySelectorAll('[data-reveal]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const input = document.getElementById(btn.dataset.reveal);
      if (!input) return;
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      const icon = btn.querySelector('i');
      if (icon) icon.className = 'fas ' + (show ? 'fa-eye-slash' : 'fa-eye');
      const ar = document.documentElement.lang === 'ar';
      const label = show ? (ar ? 'إخفاء كلمة المرور' : 'Hide password') : (ar ? 'إظهار كلمة المرور' : 'Show password');
      btn.setAttribute('aria-label', label);
      btn.title = label;
      input.focus();
    });
  });

  // Submit: native validation first, then a loading state so a slow server never looks frozen
  document.querySelectorAll('form[data-module]').forEach((form) => {
    form.addEventListener('submit', (e) => {
      if (!form.checkValidity()) {
        e.preventDefault();
        form.reportValidity();
        return;
      }
      const btn = form.querySelector('[type="submit"]');
      if (btn && !btn.disabled) {
        btn.disabled = true;
        btn.setAttribute('aria-busy', 'true');
        const arrow = btn.querySelector('.fa-arrow-right');
        if (arrow) arrow.remove();
        btn.insertAdjacentHTML('beforeend', '<span class="wt-loader" aria-hidden="true"></span>');
      }
    });
  });

  // Coming back through the browser cache would reuse a stale CSRF token
  window.addEventListener('pageshow', (e) => { if (e.persisted) window.location.reload(); });

  // Smooth scrolling, driven by GSAP's ticker so the scene and the scroll share one clock
  let lenis = null;
  if (!reduce && window.Lenis && document.body.dataset.scene === 'landing') {
    lenis = new window.Lenis({ duration: 1.05, smoothWheel: true, wheelMultiplier: 0.95 });
    if (window.gsap) {
      if (window.ScrollTrigger) {
        window.gsap.registerPlugin(window.ScrollTrigger);
        lenis.on('scroll', window.ScrollTrigger.update);
      }
      window.gsap.ticker.add((t) => lenis.raf(t * 1000));
      window.gsap.ticker.lagSmoothing(0);
    } else {
      const raf = (t) => { lenis.raf(t); requestAnimationFrame(raf); };
      requestAnimationFrame(raf);
    }
  }
  window.wtLenis = lenis;

  // In-page links (and "Sign in" from the bottom of the page focuses the email field)
  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href');
      const target = id && id.length > 1 ? document.querySelector(id) : null;
      if (!target) return;
      e.preventDefault();
      const focus = () => {
        if (a.hasAttribute('data-focus-signin')) {
          const email = document.getElementById('signin-email');
          if (email) email.focus({ preventScroll: true });
        }
      };
      if (lenis) lenis.scrollTo(target, { duration: 1.4, onComplete: focus });
      else { target.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth' }); window.setTimeout(focus, reduce ? 0 : 600); }
    });
  });

  // Intro: the copy and the middle module arrive with the 3D stack (content stays visible without JS)
  if (!reduce && window.gsap) {
    const g = window.gsap;
    const ease = 'expo.out';
    g.from('.lp-title, .lp-auth-title', { y: 26, autoAlpha: 0, duration: 1.1, ease, delay: 0.05 });
    g.from('.lp-sub', { y: 16, autoAlpha: 0, duration: 1.1, ease, delay: 0.16 });
    g.from('[data-module]', { y: 22, autoAlpha: 0, duration: 1.1, ease, delay: 0.28 });
    g.from('.lp-meta, .lp-alert', { autoAlpha: 0, duration: 0.9, ease: 'power2.out', delay: 0.6 });
  }
})();
