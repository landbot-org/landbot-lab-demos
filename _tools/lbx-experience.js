/* lb-js: lbx-experience 1.0 (2026-10-10) — Landbot demos: turns a v4 web chat into a one-question-per-screen experience.
   What it does, all on the page and nothing else:
     1. a header with the flow name, "Step n of N" and progress dots (counts the visitor's own answers);
     2. focus mode: messages before the visitor's last answer get a class so the CSS can fold them away;
     3. the message right after the summary intro gets a class so the CSS draws it as a lead card.
   It only reads text already on the page and adds classes and its own elements; it never sends anything.
   Change only CONFIG. On any error the plain chat keeps working (the CSS styles only what this adds). */
(function () {
  var CONFIG = {
    title: 'Best Egg · Check your options',
    total: 5,
    stepText: 'Step {n} of {total}',
    doneText: 'Your summary',
    summaryIntro: 'Here is what',
    cardMarker: '💰',          // the summary bubble starts with this emoji
    cardBadge: 'Lead ready · priority high',
    cardLabels: { '💰': 'Amount', '🎯': 'Purpose', '📊': 'Credit', '✉️': 'Email' }
  };
  try {
    if (window.__lbxExp) return;
    var stats = window.__lbxExp = { renders: 0 };
    document.body.classList.add('lbx-exp');
    var total = Math.max(1, parseInt(CONFIG.total, 10) || 1);

    var head = document.createElement('div');
    head.id = 'lbx-head'; head.setAttribute('aria-hidden', 'true');
    var t = document.createElement('span'); t.className = 'lbx-title'; t.textContent = CONFIG.title;
    var s = document.createElement('span'); s.className = 'lbx-step';
    var dots = document.createElement('div'); dots.className = 'lbx-dots';
    for (var i = 0; i < total; i++) { var d = document.createElement('i'); dots.appendChild(d); }
    head.appendChild(t); head.appendChild(s); head.appendChild(dots);
    document.body.appendChild(head);

    function render() {
      try {
        var msgs = document.querySelectorAll('[data-lb-part="message"]');
        var lastUser = -1, answered = 0, summaryAt = -1;
        for (var i = 0; i < msgs.length; i++) {
          var m = msgs[i];
          if (m.getAttribute('data-lb-author') === 'user') { lastUser = i; answered++; }
          else if (summaryAt < 0 && (m.textContent || '').indexOf(CONFIG.summaryIntro) !== -1) { summaryAt = i; }
        }
        for (var j = 0; j < msgs.length; j++) {
          var past = j < lastUser;
          if (msgs[j].classList.contains('lbx-past') !== past) msgs[j].classList.toggle('lbx-past', past);
          var card = summaryAt >= 0 && j === summaryAt + 1;
          if (msgs[j].classList.contains('lbx-card') !== card) msgs[j].classList.toggle('lbx-card', card);
        }
        var done = summaryAt >= 0;
        var step = Math.min(answered + 1, total);
        s.textContent = done ? CONFIG.doneText : CONFIG.stepText.replace('{n}', step).replace('{total}', total);
        var ds = dots.children;
        for (var k = 0; k < ds.length; k++) {
          var on = done || k < step;
          if (ds[k].classList.contains('on') !== on) ds[k].classList.toggle('on', on);
        }
        document.body.classList.toggle('lbx-done', done);
        var bubbles = document.querySelectorAll('[data-lb-part="message"][data-lb-author="bot"] [data-lb-part="message-bubble"]');
        var afterCard = false;
        for (var q = 0; q < bubbles.length; q++) {
          var bb = bubbles[q];
          if (bb.classList.contains('lbx-card')) { afterCard = true; continue; }
          if (afterCard && !bb.classList.contains('lbx-after')) bb.classList.add('lbx-after');
          var txt = bb.textContent || '';
          if (txt.indexOf(CONFIG.cardMarker) !== 0 && txt.replace(/^\s+/, '').indexOf(CONFIG.cardMarker) !== 0) continue;
          var box = document.createElement('div'); box.className = 'lbx-rows';
          var badge = document.createElement('div'); badge.className = 'lbx-badge'; badge.textContent = CONFIG.cardBadge; box.appendChild(badge);
          txt.split('·').forEach(function (part) {
            part = part.trim(); if (!part) return;
            var label = '', value = part;
            Object.keys(CONFIG.cardLabels).forEach(function (em) { if (part.indexOf(em) === 0) { label = CONFIG.cardLabels[em]; value = part.slice(em.length).trim(); } });
            value = value.replace(/^[A-Za-z ]+:\s*/, function (m) { return label ? '' : m; });
            var row = document.createElement('div'); row.className = 'lbx-row';
            var l = document.createElement('span'); l.textContent = label || ' ';
            var v = document.createElement('b'); v.textContent = value;
            row.appendChild(l); row.appendChild(v); box.appendChild(row);
          });
          bb.appendChild(box); bb.classList.add('lbx-card'); afterCard = true;
        }
        stats.renders++;
      } catch (e) { stats.error = String(e); }
    }
    render();
    setInterval(render, 350);
  } catch (err) { window.__lbJsError = 'lbx-experience: ' + String(err); }
})();
