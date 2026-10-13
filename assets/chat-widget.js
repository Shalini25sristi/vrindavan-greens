/*! Property Desk chat widget. One script tag, no dependencies, styles isolated in a shadow root.
 *
 * <script src="https://YOUR-SERVER/widget.js" data-client="shree-heights" defer></script>
 *
 * Attributes
 *   data-client  (required) business id, the name of a file in clients/ on the server
 *   data-api     backend URL. Defaults to the server that serves this file
 *   data-color   brand colour override, e.g. #7A2E2A. Defaults to the colour in the client's config
 *   data-title   header title override
 *   data-source  lead source label. Campaign tags (utm_*, fbclid, gclid) on the page link are sent automatically
 *   data-open    "1" to open the chat automatically on desktop after a few seconds (optional)
 */
(function () {
  'use strict';
  if (window.__propertyDeskChat) return;
  window.__propertyDeskChat = true;

  var script = document.currentScript || document.querySelector('script[data-client][src*="widget"]');
  var ds = (script && script.dataset) || {};
  var clientId = (ds.client || '').trim();
  if (!clientId) { if (window.console) console.warn('Property Desk chat: add data-client="..." to the script tag.'); return; }
  var api = (ds.api || (script && script.src ? new URL(script.src, location.href).origin : '')).replace(/\/$/, '');
  if (api === 'null' || api.indexOf('file:') === 0) api = 'http://localhost:8000';

  function store(kind, key, val) {
    try {
      var s = kind === 'local' ? localStorage : sessionStorage;
      if (val === undefined) return s.getItem(key);
      if (val === null) { s.removeItem(key); return null; }
      s.setItem(key, val);
    } catch (e) { return null; }
    return null;
  }
  var K = 'pd.' + clientId + '.';

  // Campaign attribution kept for the visit
  function clean(v) { return (v || '').replace(/[^\w\-. ]/g, '').slice(0, 60); }
  function readUtm() {
    var p = new URLSearchParams(location.search);
    var u = { utm_source: clean(p.get('utm_source')), utm_medium: clean(p.get('utm_medium')), utm_campaign: clean(p.get('utm_campaign')) };
    if (!u.utm_source && p.get('fbclid')) u.utm_source = 'meta';
    if (!u.utm_source && p.get('gclid')) u.utm_source = 'google';
    if (!u.utm_source && ds.source) u.utm_source = clean(ds.source);
    if (u.utm_source) { store('session', K + 'utm', JSON.stringify(u)); return u; }
    try { return JSON.parse(store('session', K + 'utm') || 'null') || {}; } catch (e) { return {}; }
  }
  var utm = readUtm();

  var color = /^#[0-9a-fA-F]{3,8}$/.test(ds.color || '') ? ds.color : '#0d6a5a';
  var biz = { name: 'our team', privacy_url: '' };

  var host = document.createElement('div');
  host.setAttribute('data-property-desk-root', '');
  var root = host.attachShadow({ mode: 'open' });
  var style = document.createElement('style');
  root.appendChild(style);
  function paint() {
    style.textContent =
      ':host{all:initial}' +
      '*{box-sizing:border-box;font-family:system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans","Noto Sans Bengali","Noto Sans Devanagari",sans-serif}' +
      '.fab{position:fixed;right:16px;bottom:16px;width:58px;height:58px;border-radius:50%;border:0;background:' + color + ';color:#fff;cursor:pointer;box-shadow:0 4px 16px rgba(0,0,0,.28);z-index:2147483000;display:flex;align-items:center;justify-content:center}' +
      'button:focus-visible,input:focus-visible,a:focus-visible{outline:2px solid ' + color + ';outline-offset:2px}' +
      '.panel{position:fixed;right:16px;bottom:88px;width:380px;max-width:calc(100vw - 24px);height:600px;max-height:calc(100vh - 104px);background:#fff;color:#1b1f1d;border-radius:16px;box-shadow:0 14px 44px rgba(0,0,0,.3);display:flex;flex-direction:column;overflow:hidden;z-index:2147483000}' +
      '.panel[hidden],.chat[hidden],.intake[hidden]{display:none}' +
      '@media (max-width:480px){.panel{right:0;bottom:0;left:0;width:100%;max-width:100%;height:100%;max-height:100%;border-radius:0}.fab{right:12px;bottom:12px}}' +
      'header{background:' + color + ';color:#fff;padding:12px 14px;display:flex;justify-content:space-between;align-items:center;gap:8px}' +
      'header strong{display:block;font-size:15px;line-height:1.2}header span{font-size:12px;opacity:.88}' +
      '.hbtn{background:transparent;border:0;color:#fff;font-size:13px;cursor:pointer;padding:6px 8px;border-radius:8px;opacity:.9}.hbtn:hover{background:rgba(255,255,255,.18)}' +
      '.x{font-size:24px;line-height:1;padding:2px 8px}' +
      '.bar{height:3px;background:rgba(0,0,0,.08)}.bar i{display:block;height:100%;width:0;background:' + color + ';transition:width .3s}' +
      '.intake{padding:16px;display:flex;flex-direction:column;gap:11px;overflow:auto}' +
      '.intake p{margin:0;font-size:14px;color:#3d4642;line-height:1.45}' +
      'label{font-size:12px;color:#3d4642;display:flex;flex-direction:column;gap:4px}' +
      '.in{border:1px solid #c9d0cb;border-radius:10px;padding:10px 11px;font-size:16px;width:100%;background:#fff;color:#1b1f1d}' +
      '.phone{display:flex;align-items:stretch;border:1px solid #c9d0cb;border-radius:10px;overflow:hidden}.phone b{background:#f0f2ef;padding:10px 10px;font-size:15px;font-weight:600;color:#3d4642}.phone input{border:0;border-radius:0;flex:1;min-width:0;padding:10px 11px;font-size:16px}' +
      '.consent{flex-direction:row;align-items:flex-start;gap:8px;font-size:12px;line-height:1.4}.consent input{margin-top:2px}' +
      '.go{background:' + color + ';color:#fff;border:0;border-radius:10px;padding:11px 16px;font-size:15px;font-weight:600;cursor:pointer}.go[disabled]{opacity:.55;cursor:default}' +
      '.err{color:#b3261e;font-size:13px;min-height:18px;margin:0}' +
      '.chat{display:flex;flex-direction:column;flex:1;min-height:0}' +
      '.log{flex:1;overflow:auto;padding:12px;display:flex;flex-direction:column;gap:8px;background:#f4f5f2;scroll-behavior:smooth}' +
      '.m{max-width:88%;padding:9px 12px;border-radius:14px;font-size:14.5px;line-height:1.45;white-space:pre-wrap;overflow-wrap:anywhere}' +
      '.m.you{align-self:flex-end;background:' + color + ';color:#fff;border-bottom-right-radius:4px}' +
      '.m.bot{align-self:flex-start;background:#fff;border:1px solid #e1e5df;border-bottom-left-radius:4px}' +
      '.typing{align-self:flex-start;background:#fff;border:1px solid #e1e5df;border-radius:14px;padding:10px 14px;display:flex;gap:4px}.typing i{width:6px;height:6px;border-radius:50%;background:#9aa49e;animation:b 1s infinite}.typing i:nth-child(2){animation-delay:.15s}.typing i:nth-child(3){animation-delay:.3s}' +
      '@keyframes b{0%,60%,100%{transform:none;opacity:.5}30%{transform:translateY(-4px);opacity:1}}' +
      '.chips{display:flex;flex-wrap:wrap;gap:7px;align-self:flex-start;max-width:100%}' +
      '.chip{border:1.5px solid ' + color + ';background:#fff;color:' + color + ';border-radius:999px;padding:8px 13px;font-size:13.5px;line-height:1.2;cursor:pointer;text-align:left}.chip:hover,.chip:active{background:' + color + ';color:#fff}.chip[disabled]{opacity:.5;cursor:default}' +
      '.quick{display:flex;gap:6px;padding:8px 10px 0;overflow-x:auto;background:#fff;border-top:1px solid #e1e5df;scrollbar-width:none}.quick::-webkit-scrollbar{display:none}' +
      '.q{flex:none;border:0;background:#eef1ed;color:#2b332f;border-radius:999px;padding:6px 11px;font-size:12.5px;cursor:pointer;white-space:nowrap}.q:hover{background:#e0e5df}' +
      '.send{display:flex;gap:8px;padding:8px 10px 6px;background:#fff}.send .in{flex:1;border-radius:999px;padding:9px 14px}' +
      '.send .go{border-radius:999px;padding:9px 16px}' +
      '.fine{margin:0;padding:0 12px 9px;font-size:11px;color:#6b7771;background:#fff}' +
      '@media (prefers-reduced-motion:no-preference){.panel{animation:rise .18s ease-out}@keyframes rise{from{transform:translateY(8px);opacity:0}to{transform:none;opacity:1}}}';
  }
  paint();

  var wrap = document.createElement('div');
  wrap.innerHTML =
    '<button class="fab" type="button" aria-label="Open chat" aria-expanded="false" hidden>' +
    '<svg width="27" height="27" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/></svg></button>' +
    '<section class="panel" role="dialog" aria-label="Chat" hidden>' +
    '<header><div><strong class="ttl"></strong><span class="sub">Typically replies in seconds</span></div>' +
    '<div><button class="hbtn newchat" type="button" hidden>New chat</button><button class="hbtn x" type="button" aria-label="Close chat">&times;</button></div></header>' +
    '<div class="bar" aria-hidden="true"><i></i></div>' +
    '<form class="intake" novalidate>' +
    '<p class="lead"></p>' +
    '<label>Your name<input class="in" type="text" name="name" autocomplete="name" maxlength="80"></label>' +
    '<label>Mobile number<span class="phone"><b>+91</b><input type="tel" name="phone" autocomplete="tel-national" inputmode="numeric" maxlength="16" placeholder="10-digit number"></span></label>' +
    '<label class="consent"><input type="checkbox" name="consent"><span class="ctext"></span></label>' +
    '<p class="err" role="alert"></p>' +
    '<button class="go" type="submit">Start chat</button></form>' +
    '<div class="chat" hidden><div class="log" role="log" aria-live="polite"></div>' +
    '<div class="quick" role="toolbar" aria-label="Quick questions"></div>' +
    '<form class="send" novalidate><input class="in" type="text" name="msg" maxlength="500" placeholder="Type your message" aria-label="Your message" autocomplete="off"><button class="go" type="submit">Send</button></form>' +
    '<p class="fine"></p></div>' +
    '</section>';
  while (wrap.firstChild) root.appendChild(wrap.firstChild);

  function $(sel) { return root.querySelector(sel); }
  var fab = $('.fab'), panel = $('.panel'), intake = $('.intake'), chat = $('.chat'), log = $('.log'), quick = $('.quick');
  var sendForm = $('.send'), msgInput = sendForm.elements.msg, err = $('.err'), bar = $('.bar i'), newBtn = $('.newchat');
  var sessionId = store('local', K + 'sid') || '';
  var contact = null;
  try { contact = JSON.parse(store('local', K + 'contact') || 'null'); } catch (e) { contact = null; }
  var busy = false;

  function scroll() { log.scrollTop = log.scrollHeight; }
  function addMsg(role, text) {
    var d = document.createElement('div');
    d.className = 'm ' + role;
    d.textContent = text;
    log.appendChild(d);
    scroll();
  }
  function clearChips() { var all = log.querySelectorAll('.chips'); for (var i = 0; i < all.length; i++) all[i].remove(); }
  function addChips(chips) {
    clearChips();
    if (!chips || !chips.length) return;
    var w = document.createElement('div');
    w.className = 'chips';
    chips.forEach(function (c) {
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'chip'; b.textContent = c.label;
      b.addEventListener('click', function () { if (!busy) send('', c); });
      w.appendChild(b);
    });
    log.appendChild(w);
    scroll();
  }
  function setQuick(items) {
    quick.textContent = '';
    (items || []).forEach(function (c) {
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'q'; b.textContent = c.label;
      b.addEventListener('click', function () { if (!busy) send('', c); });
      quick.appendChild(b);
    });
    quick.hidden = !(items && items.length);
  }
  function setProgress(p) { if (p && p[1]) bar.style.width = Math.round(100 * p[0] / p[1]) + '%'; }
  function typing(on) {
    var t = log.querySelector('.typing');
    if (on && !t) { t = document.createElement('div'); t.className = 'typing'; t.innerHTML = '<i></i><i></i><i></i>'; log.appendChild(t); scroll(); }
    if (!on && t) t.remove();
  }
  function setBusy(v) { busy = v; sendForm.querySelector('button').disabled = v; }

  function post(path, body) {
    var ctl = typeof AbortController === 'function' ? new AbortController() : null;
    var timer = ctl ? setTimeout(function () { ctl.abort(); }, 20000) : null;
    return fetch(api + path, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body), signal: ctl ? ctl.signal : undefined
    }).then(function (r) {
      if (timer) clearTimeout(timer);
      return r.json().catch(function () { return {}; }).then(function (j) {
        if (!r.ok) {
          var er = new Error(j.detail && typeof j.detail === 'string' ? j.detail : 'Something went wrong');
          er.status = r.status; er.fromServer = true;
          throw er;
        }
        return j;
      });
    });
  }
  function fail(e) {
    typing(false);
    if (e && e.status === 404) { // session expired on the server: start over with the saved details
      store('local', K + 'sid', null); sessionId = '';
      if (contact) { startSession(); return; }
    }
    if (e && e.fromServer) { addMsg('bot', e.message); return; }
    if (window.console && console.warn) console.warn('Property Desk chat: cannot reach ' + api);
    addMsg('bot', 'I cannot reach the chat server right now. Please try again in a moment.');
  }

  function render(j, delay) {
    var msgs = j.messages || [];
    var i = 0;
    (function next() {
      if (i < msgs.length) {
        typing(true);
        setTimeout(function () { typing(false); addMsg('bot', msgs[i]); i++; next(); }, delay ? Math.min(650, 220 + msgs[i].length * 4) : 0);
      } else {
        addChips(j.chips); setQuick(j.quick); setProgress(j.progress); setBusy(false);
        if (!panel.hidden) msgInput.focus({ preventScroll: true });
      }
    })();
  }

  function send(text, chipObj) {
    if (busy) return;
    if (!text && !chipObj) return;
    setBusy(true); clearChips();
    addMsg('you', text || chipObj.label);
    typing(true);
    post('/api/chat', { session_id: sessionId, message: text || '', chip_id: chipObj ? chipObj.id : '' })
      .then(function (j) { typing(false); render(j, true); })
      .catch(function (e) { fail(e); setBusy(false); });
  }

  function startSession() {
    setBusy(true);
    log.textContent = '';
    typing(true);
    post('/api/session', {
      client_id: clientId, name: contact.name, phone: contact.phone, consent: true, resume_session_id: sessionId,
      page_url: (location.origin + location.pathname).slice(0, 300),
      utm_source: utm.utm_source || '', utm_medium: utm.utm_medium || '', utm_campaign: utm.utm_campaign || ''
    }).then(function (j) {
      typing(false);
      sessionId = j.session_id; store('local', K + 'sid', sessionId);
      if (j.transcript) {
        j.transcript.forEach(function (m) { addMsg(m.role === 'lead' ? 'you' : 'bot', m.text); });
        addChips(j.chips); setQuick(j.quick); setProgress(j.progress); setBusy(false);
      } else { render(j, true); }
    }).catch(function (e) { typing(false); setBusy(false); showIntake(e.fromServer ? e.message : 'Could not reach the chat server. Please try again.'); });
  }

  function showIntake(msg) {
    intake.hidden = false; chat.hidden = true; newBtn.hidden = true;
    err.textContent = msg || '';
    intake.elements.name.focus();
  }
  function showChat() {
    intake.hidden = true; chat.hidden = false; newBtn.hidden = false;
    if (sessionId && log.childNodes.length) { msgInput.focus(); return; }
    startSession();
  }
  function open() {
    panel.hidden = false; fab.setAttribute('aria-expanded', 'true'); fab.setAttribute('aria-label', 'Close chat');
    if (contact && contact.phone) showChat(); else showIntake('');
  }
  function close() {
    panel.hidden = true; fab.setAttribute('aria-expanded', 'false'); fab.setAttribute('aria-label', 'Open chat'); fab.focus();
  }
  fab.addEventListener('click', function () { if (panel.hidden) open(); else close(); });
  $('.x').addEventListener('click', close);
  panel.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
  newBtn.addEventListener('click', function () {
    if (!window.confirm('Start a new chat? This clears the conversation on this device.')) return;
    store('local', K + 'sid', null); store('local', K + 'contact', null);
    sessionId = ''; contact = null; log.textContent = ''; quick.textContent = ''; bar.style.width = '0';
    intake.elements.name.value = ''; intake.elements.phone.value = ''; intake.elements.consent.checked = false;
    showIntake('');
  });

  intake.addEventListener('submit', function (e) {
    e.preventDefault();
    var name = intake.elements.name.value.trim();
    var digits = intake.elements.phone.value.replace(/\D/g, '');
    if (digits.length === 12 && digits.indexOf('91') === 0) digits = digits.slice(2);
    else if (digits.length === 11 && digits.charAt(0) === '0') digits = digits.slice(1);
    if (name.length < 2) { err.textContent = 'Please enter your name.'; return; }
    if (!/^[6-9]\d{9}$/.test(digits)) { err.textContent = 'Please enter a valid 10-digit mobile number.'; return; }
    if (!intake.elements.consent.checked) { err.textContent = 'Please tick the box to continue.'; return; }
    err.textContent = '';
    if (contact && contact.phone !== '+91' + digits) { store('local', K + 'sid', null); sessionId = ''; }
    contact = { name: name, phone: '+91' + digits };
    store('local', K + 'contact', JSON.stringify(contact));
    intake.hidden = true; chat.hidden = false; newBtn.hidden = false;
    startSession();
  });
  sendForm.addEventListener('submit', function (e) {
    e.preventDefault();
    var t = msgInput.value.trim();
    if (!t) return;
    msgInput.value = '';
    send(t, null);
  });

  // Load the business's name and colour, then show the button. Hidden if the server refuses this website.
  fetch(api + '/api/config/' + encodeURIComponent(clientId)).then(function (r) {
    if (!r.ok) throw new Error('config ' + r.status);
    return r.json();
  }).then(function (j) {
    biz = j;
    if (!/^#[0-9a-fA-F]{3,8}$/.test(ds.color || '') && /^#[0-9a-fA-F]{3,8}$/.test(j.color || '')) color = j.color;
    paint();
    $('.ttl').textContent = ds.title || j.name;
    $('.lead').textContent = 'Ask about ' + j.name + ' or arrange a visit. Share your name and mobile number to start.';
    var link = j.privacy_url ? ' <a href="' + j.privacy_url.replace(/"/g, '') + '" target="_blank" rel="noopener">Privacy policy</a>' : '';
    $('.ctext').innerHTML = 'I agree that ' + (j.name || 'the team').replace(/[<>&]/g, '') + ' may save my chat and details to help with my enquiry.' + link;
    $('.fine').textContent = j.disclaimer || 'Final prices and terms are confirmed by our sales team.';
    fab.hidden = false;
    if (ds.open === '1' && window.innerWidth > 700 && !store('session', K + 'seen')) {
      store('session', K + 'seen', '1');
      setTimeout(function () { if (panel.hidden) open(); }, 4000);
    }
  }).catch(function (e) {
    if (window.console && console.warn) console.warn('Property Desk chat not shown: ' + e.message + ' (check data-client, data-api and the server allow-list)');
  });

  function mount() { document.body.appendChild(host); }
  if (document.body) mount(); else document.addEventListener('DOMContentLoaded', mount);
})();
