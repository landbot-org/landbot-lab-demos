/* lb-js: lbx-file 2.0 (2026-10-11) — Landbot demos: a live "lead file" that fills as the visitor answers.
   What it does, all on the page and nothing else:
     1. a header that lists the qualifying fields and fills each one with the visitor's answer as it is given;
     2. focus mode (optional): messages before the visitor's last answer get a class so the CSS can fold them away;
     3. the summary bubble (it starts with CONFIG.cardMarker) is redrawn as a lead card whose badge carries the route.
   It only reads text already on the page and adds classes, attributes and its own elements; it never sends anything.
   Change only CONFIG. On any error the plain chat keeps working (the CSS styles only what this adds). */
(function () {
  var CONFIG = {
    fileTitle: 'Your request',
    fileDone: 'What the team receives',
    focus: true,
    slots: [{ q: 'How much', label: 'Amount' }],
    cardMarker: '🚦',
    cardLabels: { '🚦': 'Route' },
    tiers: { hot: 'Hot', warm: 'Nurture', cold: 'Not a fit' },
    placeholder: ''
  };
  try {
    if (window.__lbxFile) return;
    var stats = window.__lbxFile = { renders: 0 };
    document.body.classList.add('lbx-exp');
    if (CONFIG.focus) document.body.classList.add('lbx-focus');

    var head = document.createElement('div'); head.id = 'lbx-head';
    var ttl = document.createElement('div'); ttl.className = 'lbx-ttl'; ttl.textContent = CONFIG.fileTitle;
    var list = document.createElement('div'); list.className = 'lbx-slots';
    var slotEls = CONFIG.slots.map(function (s) {
      var el = document.createElement('div'); el.className = 'lbx-slot';
      var l = document.createElement('span'); l.className = 'lbx-l'; l.textContent = s.label;
      var v = document.createElement('span'); v.className = 'lbx-v';
      el.appendChild(l); el.appendChild(v); list.appendChild(el); return { el: el, v: v, q: s.q.toLowerCase() };
    });
    head.appendChild(ttl); head.appendChild(list); document.body.appendChild(head);

    function tierOf(text) {
      for (var k in CONFIG.tiers) { if (text.indexOf(CONFIG.tiers[k]) !== -1) return k; }
      return 'warm';
    }

    function buildCard(bb, txt) {
      var box = document.createElement('div'); box.className = 'lbx-rows';
      var tier = 'warm';
      txt.split('·').forEach(function (part) {
        part = part.trim(); if (!part) return;
        var label = '', value = part;
        Object.keys(CONFIG.cardLabels).forEach(function (em) { if (part.indexOf(em) === 0) { label = CONFIG.cardLabels[em]; value = part.slice(em.length).trim(); } });
        if (!value) return;
        if (part.indexOf(CONFIG.cardMarker) === 0) {
          tier = tierOf(value);
          var badge = document.createElement('div'); badge.className = 'lbx-badge lbx-' + tier; badge.textContent = value;
          box.insertBefore(badge, box.firstChild); return;
        }
        var row = document.createElement('div'); row.className = 'lbx-row';
        var l = document.createElement('span'); l.textContent = label;
        var v = document.createElement('b'); v.textContent = value;
        row.appendChild(l); row.appendChild(v); box.appendChild(row);
      });
      bb.appendChild(box); bb.classList.add('lbx-card'); bb.setAttribute('data-lbx-tier', tier);
      head.setAttribute('data-lbx-tier', tier);
    }

    function render() {
      try {
        var msgs = document.querySelectorAll('[data-lb-part="message"]');
        var lastUser = -1, lastBotText = '', done = false;
        for (var i = 0; i < msgs.length; i++) {
          var m = msgs[i], txt = (m.textContent || '').trim();
          if (m.getAttribute('data-lb-author') === 'user') {
            lastUser = i;
            var q = lastBotText.toLowerCase();
            for (var s = 0; s < slotEls.length; s++) {
              if (q.indexOf(slotEls[s].q) !== -1 && slotEls[s].v.textContent !== txt) {
                slotEls[s].v.textContent = txt; slotEls[s].el.classList.add('lbx-filled', 'lbx-new');
                (function (el) { setTimeout(function () { el.classList.remove('lbx-new'); }, 900); })(slotEls[s].el);
              }
            }
          } else {
            lastBotText = txt;
          }
        }
        for (var j = 0; j < msgs.length; j++) {
          var past = j < lastUser;
          if (msgs[j].classList.contains('lbx-past') !== past) msgs[j].classList.toggle('lbx-past', past);
        }
        var bubbles = document.querySelectorAll('[data-lb-part="message"][data-lb-author="bot"] [data-lb-part="message-bubble"]');
        var after = false;
        for (var b = 0; b < bubbles.length; b++) {
          var bb = bubbles[b];
          if (bb.classList.contains('lbx-card')) { after = true; done = true; continue; }
          if (after && !bb.classList.contains('lbx-after')) bb.classList.add('lbx-after');
          var t = (bb.textContent || '').trim();
          if (t.indexOf(CONFIG.cardMarker) === 0) { buildCard(bb, t); after = true; done = true; }
        }
        ttl.textContent = done ? CONFIG.fileDone : CONFIG.fileTitle;
        document.body.classList.toggle('lbx-done', done);
        var active = !!document.querySelector('[data-lb-part="message"], [data-lb-part="options-group"], [data-lb-part="input-field"]');
        if (document.body.classList.contains('lbx-active') !== active) document.body.classList.toggle('lbx-active', active);
        if (CONFIG.placeholder) {
          var ins = document.querySelectorAll('[data-lb-part="input-field"] textarea, [data-lb-part="input-field"] input');
          for (var z = 0; z < ins.length; z++) { if (ins[z].getAttribute('placeholder') !== CONFIG.placeholder) ins[z].setAttribute('placeholder', CONFIG.placeholder); }
        }
        stats.renders++;
      } catch (e) { stats.error = String(e); }
    }
    render();
    setInterval(render, 350);
  } catch (err) { window.__lbJsError = 'lbx-file: ' + String(err); }
})();
