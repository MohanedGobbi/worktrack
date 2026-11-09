/* Site Settings > Software updates.
   Reads core.views.update_status and asks for a check through core.views.update_check (password again).
   The server does the work: a systemd .path unit sees the request file and runs deploy/linux/worktrack-update.sh,
   which writes its progress to the status file this panel polls. Never colour alone: every state has an icon and text. */
(function () {
  'use strict';
  const panel = document.getElementById('wt-updates');
  if (!panel) return;

  const isAr = () => document.documentElement.lang === 'ar' || document.documentElement.dir === 'rtl';
  const T = (en, ar) => (isAr() ? ar : en);
  const $ = (k) => panel.querySelector(`[data-upd="${k}"]`);
  const dialog = document.getElementById('wt-upd-dialog');
  const form = document.getElementById('wt-upd-form');
  const pw = document.getElementById('wt-upd-password');
  const pwError = dialog.querySelector('.wt-upd-error');
  const csrf = () => (document.querySelector('[name=csrfmiddlewaretoken]') || {}).value || '';
  const BUSY = new Set(['checking', 'downloading', 'installing']);
  const POLL_MS = 3000, GIVE_UP_MS = 180000;

  const STATES = {
    none: ['fa-circle-info', () => T('No check has run yet.', 'لم يُجرَ أي فحص بعد.')],
    checking: ['fa-magnifying-glass', () => T('Checking for a new release…', 'جارٍ البحث عن إصدار جديد…')],
    up_to_date: ['fa-circle-check', () => T('Up to date.', 'البرنامج محدَّث.')],
    downloading: ['fa-download', (s) => T(`Downloading version ${s.latest}…`, `جارٍ تنزيل الإصدار ${s.latest}…`)],
    installing: ['fa-gears', (s) => T(`Installing version ${s.latest}. The site restarts for a moment.`, `جارٍ تثبيت الإصدار ${s.latest}. سيُعاد تشغيل الموقع لحظات.`)],
    updated: ['fa-circle-check', (s) => T(`Updated to version ${s.installed || s.latest}.`, `تم التحديث إلى الإصدار ${s.installed || s.latest}.`)],
    failed: ['fa-triangle-exclamation', (s) => T(`Version ${s.latest} could not be installed; the previous version was restored.`, `تعذّر تثبيت الإصدار ${s.latest}، وأُعيد الإصدار السابق.`)],
    skipped: ['fa-forward', (s) => T(`Version ${s.latest} failed before and is skipped until a newer release appears.`, `الإصدار ${s.latest} فشل سابقًا ويُتخطّى حتى يصدر إصدار أحدث.`)],
    error: ['fa-circle-exclamation', () => T('The last check could not finish.', 'تعذّر إكمال آخر فحص.')],
    pending: ['fa-hourglass-half', () => T('Check requested. Waiting for the server…', 'تم طلب الفحص. بانتظار الخادم…')],
  };

  function fmtTime(iso) {
    if (!iso) return '–';
    const d = new Date(iso);
    if (isNaN(d)) return '–';
    try {
      return new Intl.DateTimeFormat(isAr() ? 'ar-DZ-u-nu-latn' : 'en-GB', { dateStyle: 'medium', timeStyle: 'short' }).format(d);
    } catch (e) { return d.toLocaleString(); }
  }

  let last = null;
  function render(data, override) {
    last = data;
    const s = data.status || {};
    $('installed').textContent = data.installed || '–';
    $('latest').textContent = s.latest || '–';
    $('checked').textContent = fmtTime(s.timestamp);
    const key = override || (data.pending ? 'pending' : (STATES[s.state] ? s.state : 'none'));
    const [icon, text] = STATES[key];
    const line = $('state');
    line.dataset.state = key;
    line.querySelector('i').className = `fas ${icon}`;
    line.querySelector('span').textContent = text(s);
    const detail = $('detail');
    const showDetail = (key === 'failed' || key === 'error' || key === 'skipped') && s.message;
    detail.hidden = !showDetail;
    detail.textContent = showDetail ? s.message : '';
    const btn = $('check');
    const demo = panel.dataset.demo === '1';
    btn.disabled = demo || !data.configured || busy;
    $('help').innerHTML = !data.configured
      ? `<span>${T('Automatic updates are not set up on this server (see the install guide).', 'التحديث التلقائي غير مفعّل على هذا الخادم (راجع دليل التثبيت).')}</span>`
      : demo ? `<span>${T('Not available in demo mode.', 'غير متاح في وضع التجربة.')}</span>`
        : `<span>${T('The server installs new releases by itself every night. Use the button to check now.', 'يثبّت الخادم الإصدارات الجديدة تلقائيًا كل ليلة. استخدم الزر للفحص الآن.')}</span>`;
  }

  async function fetchStatus() {
    const r = await fetch(panel.dataset.statusUrl, { credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    if (!r.ok) throw new Error(String(r.status));
    return r.json();
  }

  let busy = false;
  async function poll(startStamp, startVersion) {
    busy = true;
    const started = Date.now();
    $('check').disabled = true;
    while (Date.now() - started < GIVE_UP_MS) {
      await new Promise((res) => setTimeout(res, POLL_MS));
      let data;
      try { data = await fetchStatus(); } catch (e) { continue; } // expected while the site restarts
      const s = data.status || {};
      const versionChanged = data.installed && startVersion && data.installed !== startVersion;
      const settled = versionChanged || (s.timestamp && s.timestamp !== startStamp && !BUSY.has(s.state) && !data.pending);
      if (!settled) { render(data); continue; }
      busy = false;
      render(data);
      if (versionChanged || s.state === 'updated') {
        $('reload').hidden = false;
        const newVersion = (s.state === 'updated' && s.installed) || data.installed;
        window.showToast && window.showToast(T(`Updated to version ${newVersion}. Reload to use it.`, `تم التحديث إلى الإصدار ${newVersion}. أعد تحميل الصفحة لاستخدامه.`), 'success');
      } else if (s.state === 'up_to_date') {
        window.showToast && window.showToast(T('You already have the latest version.', 'لديك أحدث إصدار.'), 'info');
      } else if (s.state === 'failed' || s.state === 'error') {
        window.showToast && window.showToast(T('The update did not complete. See the details below.', 'لم يكتمل التحديث. انظر التفاصيل أدناه.'), 'error');
      }
      return;
    }
    busy = false;
    if (last) render(last);
    const line = $('state');
    line.querySelector('i').className = 'fas fa-moon';
    line.querySelector('span').textContent = T('No answer yet. The check will run at the next nightly update.', 'لا ردّ بعد. سيُجرى الفحص في التحديث الليلي القادم.');
  }

  $('check').addEventListener('click', () => {
    pw.value = '';
    pwError.hidden = true;
    if (typeof dialog.showModal === 'function') dialog.showModal(); else dialog.setAttribute('open', '');
    pw.focus();
  });
  $('reload').addEventListener('click', () => location.reload());
  dialog.querySelector('[data-upd="cancel"]').addEventListener('click', () => dialog.close());

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!pw.value) { pw.focus(); return; }
    const confirmBtn = dialog.querySelector('[data-upd="confirm"]');
    confirmBtn.disabled = true;
    const body = new FormData();
    body.append('password', pw.value);
    try {
      const r = await fetch(panel.dataset.checkUrl, { method: 'POST', body, credentials: 'same-origin', headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' } });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) {
        pwError.textContent = j.code === 'password' ? T('That password is not correct.', 'كلمة المرور غير صحيحة.')
          : j.code === 'demo' ? T('Not available in demo mode.', 'غير متاح في وضع التجربة.')
            : j.code === 'not_configured' ? T('Automatic updates are not set up on this server.', 'التحديث التلقائي غير مفعّل على هذا الخادم.')
              : T('The request could not be sent. Try again.', 'تعذّر إرسال الطلب. حاول مجددًا.');
        pwError.hidden = false;
        return;
      }
      dialog.close();
      const startStamp = (last && last.status && last.status.timestamp) || '';
      const startVersion = (last && last.installed) || '';
      render(Object.assign({}, last || {}, { pending: true }));
      poll(startStamp, startVersion);
    } catch (err) {
      pwError.textContent = T('The request could not be sent. Try again.', 'تعذّر إرسال الطلب. حاول مجددًا.');
      pwError.hidden = false;
    } finally {
      confirmBtn.disabled = false;
    }
  });

  fetchStatus().then((data) => {
    render(data);
    const s = data.status || {};
    if (data.pending || BUSY.has(s.state)) poll(s.timestamp || '', data.installed || '');
  }).catch(() => {
    const line = $('state');
    line.querySelector('i').className = 'fas fa-circle-exclamation';
    line.querySelector('span').textContent = T('Could not read the update status.', 'تعذّرت قراءة حالة التحديث.');
  });
})();
