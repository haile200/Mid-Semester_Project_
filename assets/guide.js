// My Beta study guide: topic navigation, search, progress, theme, diagrams and study tools.
(function () {
  'use strict';

  const SVG_NS = 'http://www.w3.org/2000/svg';
  const STORE_LEARNED = 'mybeta-guide-learned';
  const STORE_LAST = 'mybeta-guide-last';
  const STORE_THEME = 'mybeta-guide-theme';

  // localStorage can be blocked (private mode, file://); the guide must work without it.
  const store = {
    get(key, fallback) {
      try {
        const value = localStorage.getItem(key);
        return value === null ? fallback : JSON.parse(value);
      } catch (error) {
        return fallback;
      }
    },
    set(key, value) {
      try { localStorage.setItem(key, JSON.stringify(value)); } catch (error) { /* ignore */ }
    }
  };

  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  const topics = $$('section.topic');
  // Sections are id="topic-tN" while the URL hash is #tN, so the browser never jumps to an anchor
  // and hides the heading under the sticky header.
  const keyOf = (topic) => topic.id.replace(/^topic-/, '');
  const isRtl = document.documentElement.dir === 'rtl';
  let current = 0;
  let learned = new Set(store.get(STORE_LEARNED, []));
  let allMode = false;

  // ---------- Theme ----------
  function applyTheme(theme) {
    if (theme === 'light' || theme === 'dark') {
      document.documentElement.setAttribute('data-theme', theme);
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    const btn = $('#theme-btn');
    if (btn) {
      const dark = isDark();
      btn.textContent = dark ? 'מצב בהיר' : 'מצב כהה';
      btn.setAttribute('aria-pressed', String(dark));
    }
  }
  function isDark() {
    const forced = document.documentElement.getAttribute('data-theme');
    if (forced) return forced === 'dark';
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  // ---------- Table of contents ----------
  function buildToc() {
    const list = $('#toc-list');
    topics.forEach((topic, index) => {
      const li = document.createElement('li');
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.dataset.index = String(index);
      btn.innerHTML = '<span class="num">' + (index + 1) + '</span><span class="tt"></span><span class="done" aria-hidden="true">✔</span>';
      btn.querySelector('.tt').textContent = topic.dataset.title;
      btn.addEventListener('click', () => {
        if (document.body.classList.contains('searching')) clearSearch();
        if (allMode) {
          topic.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
          show(index);
        }
        document.body.classList.remove('toc-open');
      });
      li.appendChild(btn);
      list.appendChild(li);
    });
  }

  function refreshToc() {
    $$('#toc-list li').forEach((li, index) => {
      li.classList.toggle('learned', learned.has(keyOf(topics[index])));
      li.querySelector('button').setAttribute('aria-current', String(index === current && !allMode));
    });
    const done = topics.filter((t) => learned.has(keyOf(t))).length;
    $('#progress-text').textContent = done + '/' + topics.length + ' נלמדו';
    $('#progress-fill').style.width = Math.round((done / topics.length) * 100) + '%';
    topics.forEach((topic) => {
      const box = $('.learned-box input', topic);
      if (box) box.checked = learned.has(keyOf(topic));
    });
  }

  // ---------- Showing topics ----------
  function show(index, fromHash) {
    current = Math.max(0, Math.min(topics.length - 1, index));
    topics.forEach((topic, i) => topic.classList.toggle('shown', allMode || i === current));
    if (!fromHash && location.hash !== '#' + keyOf(topics[current])) {
      history.pushState(null, '', '#' + keyOf(topics[current]));
    }
    store.set(STORE_LAST, keyOf(topics[current]));
    refreshToc();
    if (!allMode) window.scrollTo({ top: 0, behavior: 'auto' });
    redrawLabels(topics[current]);
  }

  function buildNavCards() {
    topics.forEach((topic, index) => {
      const prev = topics[index - 1];
      const next = topics[index + 1];
      const wrap = document.createElement('div');
      wrap.className = 'nav-cards';
      wrap.innerHTML =
        '<button type="button" class="nav-card prev"><small>הנושא הקודם</small><span></span></button>' +
        '<button type="button" class="nav-card next"><small>הנושא הבא</small><span></span></button>';
      const prevBtn = $('.prev', wrap);
      const nextBtn = $('.next', wrap);
      if (prev) { $('span', prevBtn).textContent = prev.dataset.title; prevBtn.addEventListener('click', () => show(index - 1)); }
      else prevBtn.hidden = true;
      if (next) { $('span', nextBtn).textContent = next.dataset.title; nextBtn.addEventListener('click', () => show(index + 1)); }
      else nextBtn.hidden = true;
      topic.appendChild(wrap);

      const finish = document.createElement('div');
      finish.className = 'finish';
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn btn-coral';
      btn.textContent = next ? 'סמן כנלמד ועבור לנושא הבא' : 'סמן כנלמד';
      btn.addEventListener('click', () => {
        setLearned(keyOf(topic), true);
        if (next) show(index + 1);
      });
      finish.appendChild(btn);
      topic.appendChild(finish);

      const box = document.createElement('label');
      box.className = 'learned-box';
      box.innerHTML = '<input type="checkbox"> למדתי את הנושא הזה';
      $('input', box).addEventListener('change', (event) => setLearned(keyOf(topic), event.target.checked));
      const lead = $('.lead', topic);
      (lead || $('h2', topic)).insertAdjacentElement('afterend', box);
    });
  }

  function setLearned(id, value) {
    if (value) learned.add(id); else learned.delete(id);
    store.set(STORE_LEARNED, Array.from(learned));
    refreshToc();
  }

  function setAllMode(value) {
    allMode = value;
    document.body.classList.toggle('all-mode', allMode);
    $('#all-btn').textContent = allMode ? 'נושא אחד בכל פעם' : 'הצג הכול בגלילה אחת';
    $('#all-btn').setAttribute('aria-pressed', String(allMode));
    show(current, true);
    if (allMode) topics.forEach((t) => redrawLabels(t));
  }

  function topicFromHash() {
    const id = location.hash.replace('#', '');
    const index = topics.findIndex((t) => keyOf(t) === id);
    return index;
  }

  // ---------- Search ----------
  function clearHighlights() {
    $$('mark.hit').forEach((mark) => {
      const parent = mark.parentNode;
      parent.replaceChild(document.createTextNode(mark.textContent), mark);
      parent.normalize();
    });
  }

  function highlight(root, term) {
    const lower = term.toLowerCase();
    let count = 0;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        if (!node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        if (node.parentElement.closest('svg, script, style, button, .nav-cards, .finish')) return NodeFilter.FILTER_REJECT;
        return node.nodeValue.toLowerCase().includes(lower) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      const text = node.nodeValue;
      const frag = document.createDocumentFragment();
      let pos = 0;
      let at = text.toLowerCase().indexOf(lower, pos);
      while (at !== -1) {
        frag.appendChild(document.createTextNode(text.slice(pos, at)));
        const mark = document.createElement('mark');
        mark.className = 'hit';
        mark.textContent = text.slice(at, at + term.length);
        frag.appendChild(mark);
        count += 1;
        pos = at + term.length;
        at = text.toLowerCase().indexOf(lower, pos);
      }
      frag.appendChild(document.createTextNode(text.slice(pos)));
      node.parentNode.replaceChild(frag, node);
    });
    return count;
  }

  function runSearch(term) {
    clearHighlights();
    term = term.trim();
    if (term.length < 2) { clearSearch(true); return; }
    document.body.classList.add('searching');
    let matches = 0;
    topics.forEach((topic) => {
      const hits = highlight(topic, term);
      topic.classList.toggle('shown', hits > 0);
      if (hits > 0) {
        matches += 1;
        $$('mark.hit', topic).forEach((mark) => {
          const details = mark.closest('details');
          if (details) details.open = true;
          const qa = mark.closest('.qa');
          if (qa) qa.classList.add('revealed');
        });
      }
    });
    $('#search-note').textContent = matches
      ? 'תוצאות עבור "' + term + '": ' + matches + ' נושאים. Esc לניקוי.'
      : 'לא נמצאו תוצאות עבור "' + term + '".';
  }

  function clearSearch(keepValue) {
    clearHighlights();
    document.body.classList.remove('searching');
    if (!keepValue) $('#search').value = '';
    show(current, true);
  }

  // ---------- Copy buttons ----------
  function addCopyButtons() {
    $$('pre').forEach((pre) => {
      if (pre.parentElement.classList.contains('codebox')) return;
      const box = document.createElement('div');
      box.className = 'codebox';
      pre.parentNode.insertBefore(box, pre);
      box.appendChild(pre);
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn copy';
      btn.textContent = 'העתק';
      btn.addEventListener('click', () => {
        const text = pre.innerText;
        const done = () => { btn.textContent = 'הועתק'; setTimeout(() => { btn.textContent = 'העתק'; }, 1400); };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(done, done);
        } else {
          done();
        }
      });
      box.appendChild(btn);
    });
  }

  // ---------- Q&A and drills ----------
  function setupQa() {
    $$('.qa').forEach((qa) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn reveal';
      btn.textContent = 'הצג תשובה';
      btn.addEventListener('click', () => {
        qa.classList.toggle('revealed');
        btn.textContent = qa.classList.contains('revealed') ? 'הסתר תשובה' : 'הצג תשובה';
      });
      $('.q', qa).insertAdjacentElement('afterend', btn);
    });
    const allQa = () => $$('.qa');
    const sync = () => allQa().forEach((qa) => { $('.reveal', qa).textContent = qa.classList.contains('revealed') ? 'הסתר תשובה' : 'הצג תשובה'; });
    const reveal = $('#qa-reveal');
    if (reveal) reveal.addEventListener('click', () => { allQa().forEach((qa) => qa.classList.add('revealed')); sync(); });
    const hide = $('#qa-hide');
    if (hide) hide.addEventListener('click', () => { allQa().forEach((qa) => qa.classList.remove('revealed')); sync(); });
    const random = $('#qa-random');
    if (random) random.addEventListener('click', () => {
      const list = allQa();
      list.forEach((qa) => qa.classList.remove('revealed'));
      sync();
      const pick = list[Math.floor(Math.random() * list.length)];
      pick.scrollIntoView({ behavior: 'smooth', block: 'center' });
      pick.classList.add('flash');
      $('.reveal', pick).focus({ preventScroll: true });
    });
    const drill = $('#drill-random');
    if (drill) drill.addEventListener('click', () => {
      const recipes = $$('details.recipe');
      recipes.forEach((d) => { d.open = false; });
      const pick = recipes[Math.floor(Math.random() * recipes.length)];
      pick.open = true;
      pick.scrollIntoView({ behavior: 'smooth', block: 'center' });
      $('summary', pick).focus({ preventScroll: true });
    });
  }

  // ---------- Diagram label backgrounds ----------
  // Every <text class="lbl"> gets a rectangle behind it so crossing lines stay readable.
  function redrawLabels(root) {
    $$('svg', root || document).forEach((svg) => {
      $$('rect.label-bg', svg).forEach((r) => r.remove());
      $$('text.lbl', svg).forEach((text) => {
        let box;
        try { box = text.getBBox(); } catch (error) { return; }
        if (!box || !box.width) return;
        const rect = document.createElementNS(SVG_NS, 'rect');
        rect.setAttribute('class', 'label-bg');
        rect.setAttribute('x', box.x - 3);
        rect.setAttribute('y', box.y - 1);
        rect.setAttribute('width', box.width + 6);
        rect.setAttribute('height', box.height + 2);
        rect.setAttribute('rx', 3);
        text.parentNode.insertBefore(rect, text);
      });
    });
  }

  // ---------- Zoom ----------
  function setupZoom() {
    const dialog = $('#zoom');
    $$('figure.diagram, .seq').forEach((fig) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn';
      btn.textContent = 'הגדל';
      btn.addEventListener('click', () => {
        const svg = $('svg', fig);
        if (!svg) return;
        const body = $('.zbody', dialog);
        body.innerHTML = '';
        body.appendChild(svg.cloneNode(true));
        $('#zoom-title').textContent = fig.dataset.title || '';
        if (typeof dialog.showModal === 'function') dialog.showModal(); else dialog.setAttribute('open', '');
        redrawLabels(body);
      });
      const host = $('figcaption', fig) || $('.seq-head', fig);
      if (host) host.appendChild(btn);
    });
    $('#zoom-close').addEventListener('click', () => { if (dialog.close) dialog.close(); else dialog.removeAttribute('open'); });
  }

  // ---------- Sequence diagrams ----------
  function el(name, attrs, text) {
    const node = document.createElementNS(SVG_NS, name);
    Object.keys(attrs || {}).forEach((key) => node.setAttribute(key, attrs[key]));
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function renderSeq(host) {
    const data = (window.SEQ_DATA || {})[host.dataset.seq];
    if (!data) return;
    host.dataset.title = data.title;
    const colW = 150;
    const top = 50;
    const stepH = 46;
    const width = data.actors.length * colW + 20;
    const height = top + data.steps.length * stepH + 30;
    const svg = el('svg', { viewBox: '0 0 ' + width + ' ' + height, role: 'img', 'aria-label': data.title });
    const defs = el('defs');
    const marker = el('marker', { id: 'seq-arrow-' + host.dataset.seq, viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: 'auto-start-reverse' });
    marker.appendChild(el('path', { d: 'M0,0 L10,5 L0,10 z', class: 'arrowhead' }));
    defs.appendChild(marker);
    svg.appendChild(defs);
    const x = (i) => 10 + i * colW + colW / 2;
    data.actors.forEach((name, i) => {
      svg.appendChild(el('line', { x1: x(i), y1: 38, x2: x(i), y2: height - 8, class: 'lifeline' }));
      svg.appendChild(el('rect', { x: x(i) - 68, y: 6, width: 136, height: 30, rx: 7, class: 'actor box' }));
      svg.appendChild(el('text', { x: x(i), y: 26, 'text-anchor': 'middle', class: 'bold' }, name));
    });
    const groups = [];
    data.steps.forEach((step, n) => {
      const g = el('g', { class: 'msg-group' });
      const y = top + n * stepH + 22;
      if (step.from === step.to) {
        const sx = x(step.from);
        g.appendChild(el('path', { d: 'M' + sx + ',' + (y - 6) + ' h34 v14 h-30', class: 'msg', fill: 'none', 'marker-end': 'url(#seq-arrow-' + host.dataset.seq + ')' }));
        g.appendChild(el('text', { x: sx + 40, y: y + 4, class: 'lbl' }, (n + 1) + '. ' + step.label));
      } else {
        const x1 = x(step.from);
        const x2 = x(step.to);
        const dir = x2 > x1 ? 1 : -1;
        g.appendChild(el('line', { x1: x1, y1: y, x2: x2 - dir * 4, y2: y, class: 'msg' + (step.ret ? ' ret' : ''), 'marker-end': 'url(#seq-arrow-' + host.dataset.seq + ')' }));
        g.appendChild(el('text', { x: (x1 + x2) / 2, y: y - 6, 'text-anchor': 'middle', class: 'lbl' }, (n + 1) + '. ' + step.label));
      }
      svg.appendChild(g);
      groups.push(g);
    });
    $('.seq-svg', host).appendChild(svg);

    let at = -1;
    const textBox = $('.seq-text', host);
    const counter = $('.seq-count', host);
    function render() {
      groups.forEach((g, i) => {
        g.classList.toggle('current', i === at);
        g.classList.toggle('future', at >= 0 && i > at);
      });
      if (at < 0) {
        textBox.innerHTML = 'לחץ "הבא" כדי לעבור על הזרימה צעד אחר צעד, או "הצג הכול".';
        counter.textContent = '0/' + groups.length;
      } else {
        textBox.innerHTML = '<b>' + (at + 1) + '.</b> ' + data.steps[at].text;
        counter.textContent = (at + 1) + '/' + groups.length;
      }
    }
    $('.seq-next', host).addEventListener('click', () => { at = Math.min(groups.length - 1, at + 1); render(); });
    $('.seq-prev', host).addEventListener('click', () => { at = Math.max(-1, at - 1); render(); });
    $('.seq-all', host).addEventListener('click', () => { at = -1; render(); });
    render();
  }

  function buildSeqPlayers() {
    $$('.seq').forEach((host) => {
      host.innerHTML =
        '<div class="seq-head"><b></b><div class="toolbar" style="margin:0">' +
        '<button type="button" class="btn seq-prev">הקודם</button>' +
        '<button type="button" class="btn btn-coral seq-next">הבא</button>' +
        '<button type="button" class="btn seq-all">הצג הכול</button>' +
        '<span class="seq-count" aria-live="polite"></span></div></div>' +
        '<div class="seq-svg"></div><div class="seq-text" aria-live="polite"></div>';
      const data = (window.SEQ_DATA || {})[host.dataset.seq];
      $('.seq-head b', host).textContent = data ? data.title : host.dataset.seq;
      renderSeq(host);
    });
  }

  // ---------- AI failure simulator ----------
  const SCENARIOS = {
    ok: { path: ['s-req', 's-limit', 's-brain', 's-gemini', 's-ok'], text: 'Gemini עונה בזמן, התשובה עוברת בדיקת JSON, והמשתמש מקבל תשובת AI אמיתית.' },
    down_user: { path: ['s-req', 's-limit', 's-brain', 's-gemini', 's-offline', 's-ok'], text: 'Gemini מחזיר 503 או לא עונה בזמן. FallbackBrain עובר למוח ה-offline, והמשתמש עדיין מקבל תשובה, פשוטה יותר.' },
    down_bot: { path: ['s-bot', 's-brain', 's-gemini', 's-skip'], text: 'לבוט אין גיבוי (fallback=False): נזרק BrainUnavailable, הפעולה מדולגת ונרשמת ביומן. לא מפרסמים טקסט מתבנית.' },
    bad_json: { path: ['s-req', 's-limit', 's-brain', 's-gemini', 's-offline', 's-ok'], text: 'Gemini עונה בלי JSON תקין או בלי allowed בוליאני. זו BrainError, בדיוק כמו נפילה, ועוברים לגיבוי.' },
    toxic: { path: ['s-req', 's-limit', 's-brain', 's-gemini', 's-reject'], text: 'הבדיקה מחזירה allowed=false. נזרק ContentRejected, חוזר 400 עם הסיבה, וה-draft נשאר אצל המשתמש.' },
    limited: { path: ['s-req', 's-limit', 's-429'], text: 'הבקשה ה-11 בדקה מאותו משתמש: 429 עם Retry-After, עוד לפני ש-Gemini נקרא.' },
    anon: { path: ['s-req', 's-401'], text: 'אין cookie תקף: login_required מחזיר 401 לפני ההגבלה, כך שמשתמש אנונימי לא נספר ולא עולה כסף.' }
  };

  function setupSimulator() {
    const sim = $('#sim');
    if (!sim) return;
    const out = $('#sim-out', sim);
    $$('.sim-buttons .btn', sim).forEach((btn) => {
      btn.addEventListener('click', () => {
        const scenario = SCENARIOS[btn.dataset.scenario];
        $$('.sim-buttons .btn', sim).forEach((b) => b.setAttribute('aria-pressed', String(b === btn)));
        $$('[data-node]', sim).forEach((node) => {
          const on = scenario.path.includes(node.dataset.node);
          node.classList.toggle('lit', on);
          node.classList.toggle('dim', !on);
        });
        out.textContent = scenario.text;
      });
    });
    const toggle = $('#sim-durations', sim);
    if (toggle) {
      toggle.addEventListener('change', () => {
        $$('[data-dur]', sim).forEach((text) => {
          if (!text.dataset.plain) text.dataset.plain = text.textContent;
          text.textContent = toggle.checked ? text.dataset.dur : text.dataset.plain;
        });
        redrawLabels(sim);
      });
    }
  }

  // ---------- Keyboard ----------
  function setupKeys() {
    document.addEventListener('keydown', (event) => {
      const tag = (event.target.tagName || '').toLowerCase();
      const typing = tag === 'input' || tag === 'textarea' || event.target.isContentEditable;
      if (event.key === '/' && !typing) {
        event.preventDefault();
        $('#search').focus();
        return;
      }
      if (event.key === 'Escape') {
        if (document.body.classList.contains('searching') || $('#search').value) clearSearch();
        document.body.classList.remove('toc-open');
        return;
      }
      if (typing || allMode || document.body.classList.contains('searching')) return;
      if (event.altKey || event.ctrlKey || event.metaKey) return;
      const forward = isRtl ? 'ArrowLeft' : 'ArrowRight';
      const back = isRtl ? 'ArrowRight' : 'ArrowLeft';
      if (event.key === forward) show(current + 1);
      if (event.key === back) show(current - 1);
    });
  }

  // ---------- Start ----------
  function init() {
    applyTheme(store.get(STORE_THEME, 'auto'));
    $('#theme-btn').addEventListener('click', () => {
      const next = isDark() ? 'light' : 'dark';
      store.set(STORE_THEME, next);
      applyTheme(next);
      topics.forEach((t) => redrawLabels(t));
    });
    if (window.matchMedia) {
      const mq = window.matchMedia('(prefers-color-scheme: dark)');
      const onChange = () => applyTheme(store.get(STORE_THEME, 'auto'));
      if (mq.addEventListener) mq.addEventListener('change', onChange);
    }

    buildToc();
    buildNavCards();
    buildSeqPlayers();
    addCopyButtons();
    setupQa();
    setupZoom();
    setupSimulator();
    setupKeys();

    $('#all-btn').addEventListener('click', () => setAllMode(!allMode));
    $('#menu-btn').addEventListener('click', () => document.body.classList.toggle('toc-open'));
    let timer = null;
    $('#search').addEventListener('input', (event) => {
      clearTimeout(timer);
      const value = event.target.value;
      timer = setTimeout(() => runSearch(value), 180);
    });
    window.addEventListener('popstate', () => {
      const index = topicFromHash();
      if (index >= 0) show(index, true);
    });

    let start = topicFromHash();
    if (start < 0) {
      const last = store.get(STORE_LAST, null);
      start = Math.max(0, topics.findIndex((t) => keyOf(t) === last));
    }
    show(start, true);
    // The browser jumps to the #tN anchor on load, which hides the heading under the sticky header.
    if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(() => topics.forEach((t) => redrawLabels(t)));
    }
    window.__guide = { show, runSearch, clearSearch, setAllMode, get current() { return current; }, learned: () => Array.from(learned) };
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
