(function() {
  'use strict';

  var script = document.currentScript || (function() {
    var scripts = document.getElementsByTagName('script');
    return scripts[scripts.length - 1];
  })();

  var containerId = script.getAttribute('data-jml-container') || 'jason-media-library';
  var dataUrl = script.getAttribute('data-jml-data-url') || 'https://jason-shanks-media.netlify.app/data/media_links.json';
  var container = document.getElementById(containerId);
  if (!container) return;

  var categories = ['Video', 'Podcast', 'Radio', 'Writing', 'Talk', 'Book', 'Interview', 'Recognition'];

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function(ch) {
      return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]);
    });
  }

  function formatDate(value) {
    if (!value) return '';
    var parts = String(value).split('-');
    if (parts.length !== 3) return esc(value);
    var date = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
    if (isNaN(date.getTime())) return esc(value);
    return date.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' });
  }

  function card(item, extraClass) {
    var tags = (item.tags || []).filter(function(t) {
      return t && ['web-search', 'YouTube', 'RSS'].indexOf(t) === -1;
    }).slice(0, 3).map(function(t) {
      return '<span class="jml-tag">' + esc(t) + '</span>';
    }).join('');

    var cat = esc(item.category || 'Writing');
    var desc = item.description ? '<div class="jml-desc">' + esc(item.description) + '</div>' : '';
    var date = item.date ? '<span class="jml-date">' + formatDate(item.date) + '</span>' : '';
    var tagWrap = tags ? '<div class="jml-tags">' + tags + '</div>' : '';

    return '<a href="' + esc(item.url || '#') + '" target="_blank" rel="noopener noreferrer" class="jml-card ' + (extraClass || '') + '" data-category="' + cat + '">' +
      '<div class="jml-card-top"><span class="jml-badge jml-badge-' + cat + '">' + cat + '</span><span class="jml-source">' + esc(item.source || '') + '</span></div>' +
      '<div class="jml-title">' + esc(item.title || '') + '</div>' + desc +
      '<div class="jml-meta">' + date + tagWrap + '</div></a>';
  }

  function pickFeatured(items) {
    var featured = items.filter(function(i) { return i.featured; }).slice(0, 6);
    var seen = {};
    featured.forEach(function(i) { seen[i.category || ''] = true; });
    items.forEach(function(i) {
      if (featured.length >= 6) return;
      var cat = i.category || '';
      if (!seen[cat] && featured.indexOf(i) === -1) { featured.push(i); seen[cat] = true; }
    });
    items.forEach(function(i) { if (featured.length < 6 && featured.indexOf(i) === -1) featured.push(i); });
    return featured;
  }

  function render(items) {
    items = (items || []).filter(function(i) { return i && i.verified !== false; });
    items.sort(function(a, b) { return String(b.date || '').localeCompare(String(a.date || '')) || String(a.title || '').localeCompare(String(b.title || '')); });

    var counts = {};
    items.forEach(function(i) { var c = i.category || 'Writing'; counts[c] = (counts[c] || 0) + 1; });
    var filters = '<button class="jml-fbtn active" data-cat="All">All</button>';
    categories.forEach(function(cat) { if (counts[cat]) filters += '<button class="jml-fbtn" data-cat="' + esc(cat) + '">' + esc(cat) + ' <span class="jml-fcount">(' + counts[cat] + ')</span></button>'; });

    var total = items.length;
    var featured = pickFeatured(items);
    container.innerHTML = '<div class="jml-wrap">' +
      '<a href="https://www.amazon.com/dp/B09J36FDP5" target="_blank" rel="noopener noreferrer" class="jml-cta"><div class="jml-cta-text"><div class="jml-cta-title">The Foundations and Pillars of Evangelization</div><div class="jml-cta-sub">By Jason Shanks &mdash; A foundational work defining evangelization through the documents of Vatican II</div></div><span class="jml-cta-btn">Buy the Book</span></a>' +
      '<div class="jml-controls"><input type="search" class="jml-search" id="jml-search" placeholder="Search ' + total + ' appearances…" aria-label="Search media library"><div class="jml-filters" id="jml-filters" role="group" aria-label="Filter by category">' + filters + '</div></div>' +
      '<div class="jml-stats" id="jml-stats" aria-live="polite">Showing ' + total + ' of ' + total + ' appearances</div>' +
      '<h2 class="jml-section-title">Featured</h2><div class="jml-featured-grid">' + featured.map(function(i) { return card(i, 'jml-featured'); }).join('') + '</div>' +
      '<hr class="jml-divider"><h2 class="jml-section-title">Browse All</h2><div class="jml-grid" id="jml-grid">' + items.map(function(i) { return card(i, ''); }).join('') + '</div>' +
      '<div class="jml-empty" id="jml-empty" hidden>No appearances match your search.</div></div>';

    var grid = container.querySelector('#jml-grid');
    var search = container.querySelector('#jml-search');
    var filtersEl = container.querySelector('#jml-filters');
    var statsEl = container.querySelector('#jml-stats');
    var emptyEl = container.querySelector('#jml-empty');
    var cards = Array.prototype.slice.call(grid.querySelectorAll('.jml-card'));
    var activeCat = 'All', query = '';

    function norm(s) { return (s || '').toLowerCase(); }
    function apply() {
      var shown = 0, q = norm(query);
      cards.forEach(function(c) {
        var catOk = activeCat === 'All' || c.getAttribute('data-category') === activeCat;
        var txtOk = !q || norm(c.textContent).indexOf(q) !== -1;
        c.hidden = !(catOk && txtOk);
        if (catOk && txtOk) shown++;
      });
      statsEl.textContent = 'Showing ' + shown + ' of ' + total + ' appearances';
      emptyEl.hidden = shown !== 0;
    }

    filtersEl.addEventListener('click', function(e) {
      var btn = e.target.closest('.jml-fbtn');
      if (!btn) return;
      activeCat = btn.getAttribute('data-cat');
      Array.prototype.forEach.call(filtersEl.querySelectorAll('.jml-fbtn'), function(b) { b.classList.remove('active'); });
      btn.classList.add('active');
      apply();
    });
    search.addEventListener('input', function() { query = search.value.trim(); apply(); });
  }

  container.innerHTML = '<div class="jml-wrap"><div class="jml-stats">Loading media appearances…</div></div>';
  fetch(dataUrl, { credentials: 'omit' })
    .then(function(res) { if (!res.ok) throw new Error('HTTP ' + res.status); return res.json(); })
    .then(render)
    .catch(function(err) {
      container.innerHTML = '<div class="jml-wrap"><div class="jml-empty">Media appearances could not be loaded. Please refresh the page.</div></div>';
      if (window.console) console.error('Jason media library failed to load:', err);
    });
})();
