/* Original handbook search and tag navigation. MIT license. No external search service. */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else {
    root.HandbookSearch = api;
    root.$docsify = root.$docsify || {};
    root.$docsify.plugins = [].concat(root.$docsify.plugins || [], function (hook) {
      let data, pending, panel;
      const labels = {scene: '场景', theory: '理论', stage: '阶段'};
      function el(tag, text, className) {
        const node = document.createElement(tag);
        if (text !== undefined) node.textContent = text;
        if (className) node.className = className;
        return node;
      }
      function route(path) {
        return '#/' + path.replace(/\.md$/, '').split('/').map(encodeURIComponent).join('/');
      }
      function load() {
        if (!pending) pending = fetch('data/search-index.json?v=1.1.0').then(function (r) {
          if (!r.ok) throw new Error('search unavailable');
          return r.json();
        }).then(function (value) { data = value; return value; }).catch(function () {
          pending = null;
          if (panel) {
            panel.status.textContent = '搜索暂未加载，可先使用标签索引。';
            panel.input.disabled = true;
          }
        });
        return pending;
      }
      function render() {
        if (!data || !panel) return;
        const query = panel.input.value;
        const filters = {};
        Object.keys(labels).forEach(k => { filters[k] = panel.selects[k].value; });
        panel.results.replaceChildren();
        if (!query.trim() && !Object.values(filters).some(Boolean)) {
          panel.status.textContent = '试试“裸辞”“不甘心”“计划超时”，也可组合标签。';
          return;
        }
        const matches = api.search(data.articles, query, filters);
        panel.status.textContent = matches.length ? '找到 ' + matches.length + ' 篇' + (matches.length > 8 ? '，先显示前 8 篇' : '') : '没有找到，可换个词或放宽一个标签条件。';
        matches.slice(0, 8).forEach(function (entry) {
          const item = el('li', undefined, 'guide-result');
          const a = el('a', entry.title); a.href = route(entry.path);
          item.append(a, el('small', entry.group));
          const tokens = api.normalize(query).split(/\s+/).filter(Boolean);
          const text = entry.text || '';
          const lower = api.normalize(text);
          const positions = tokens.map(t => lower.indexOf(t)).filter(n => n >= 0);
          const start = positions.length ? Math.max(0, Math.min.apply(null, positions) - 25) : 0;
          item.append(el('p', (start ? '…' : '') + text.slice(start, start + 95) + (text.length > start + 95 ? '…' : '')));
          panel.results.append(item);
        });
      }
      function metadata() {
        if (!data) return;
        let path;
        try { path = decodeURIComponent(location.hash.split('?')[0].replace(/^#\//, '')).replace(/\.md$/, ''); }
        catch (_) { return; }
        const entry = data.articles.find(e => e.path.replace(/\.md$/, '') === path);
        const article = document.querySelector('.markdown-section');
        if (!entry || !article || article.querySelector('.guide-tags')) return;
        const h1 = article.querySelector('h1');
        if (!h1 || !entry.scene.length) return;
        const nav = el('nav', undefined, 'guide-tags'); nav.setAttribute('aria-label', '本篇标签');
        Object.keys(labels).forEach(function (k) {
          entry[k].forEach(function (tag) {
            const a = el('a', labels[k] + '：' + tag, 'guide-tag');
            a.href = '#/' + encodeURIComponent('标签索引') + '?id=' + encodeURIComponent(labels[k] + '-' + tag);
            nav.append(a);
          });
        });
        h1.after(nav);
        Array.from(article.querySelectorAll('p')).forEach(function (p) {
          if (p.textContent.startsWith('标签：#场景/')) p.hidden = true;
        });
      }
      function mount() {
        const sidebar = document.querySelector('.sidebar');
        if (!sidebar) return;
        if (!panel || !sidebar.contains(panel.node)) {
          const node = el('section', undefined, 'guide-search'); node.setAttribute('aria-label', '搜索与标签');
          node.append(el('h2', '搜索与标签'));
          const input = el('input'); input.type = 'search'; input.placeholder = '搜索生活问题或理论';
          input.setAttribute('aria-label', '搜索生活问题或理论'); input.autocomplete = 'off';
          node.append(input);
          const selects = {};
          Object.keys(labels).forEach(function (k) {
            const row = el('label', undefined, 'guide-filter'); row.append(el('span', labels[k]));
            const select = el('select'); select.setAttribute('aria-label', '按' + labels[k] + '筛选');
            const option = el('option', '全部' + labels[k]); option.value = ''; select.append(option);
            row.append(select); node.append(row); selects[k] = select;
            select.addEventListener('change', render);
          });
          const actions = el('div', undefined, 'guide-search-actions');
          const tags = el('a', '标签索引'); tags.href = '#/' + encodeURIComponent('标签索引');
          const theories = el('a', '理论索引'); theories.href = '#/' + encodeURIComponent('理论索引');
          const clear = el('button', '清除'); clear.type = 'button';
          actions.append(tags, theories, clear); node.append(actions);
          const status = el('p', '正在准备搜索…', 'guide-status'); status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
          const results = el('ul', undefined, 'guide-results'); node.append(status, results);
          sidebar.prepend(node); panel = {node, input, selects, status, results};
          input.addEventListener('input', render);
          function reset() { input.value = ''; Object.values(selects).forEach(s => { s.value = ''; }); render(); input.focus(); }
          clear.addEventListener('click', reset);
          input.addEventListener('keydown', e => { if (e.key === 'Escape') reset(); });
        }
        load().then(function () {
          if (!data) return;
          panel.input.disabled = false;
          Object.keys(labels).forEach(function (k) {
            const select = panel.selects[k];
            if (select.options.length > 1) return;
            data.vocabulary[k].forEach(function (tag) { const option = el('option', tag); option.value = tag; select.append(option); });
          });
          render(); metadata();
        });
      }
      hook.mounted(mount); hook.doneEach(mount);
    });
  }
})(typeof globalThis === 'object' ? globalThis : this, function () {
  'use strict';
  function normalize(value) { return String(value || '').normalize('NFKC').toLocaleLowerCase().trim(); }
  function search(articles, query, filters) {
    const tokens = normalize(query).split(/\s+/).filter(Boolean);
    filters = filters || {};
    return articles.map(function (entry) {
      if (['scene', 'theory', 'stage'].some(k => filters[k] && !(entry[k] || []).includes(filters[k]))) return null;
      const title = normalize(entry.title), aliases = (entry.aliases || []).map(normalize);
      const tags = normalize([].concat(entry.scene || [], entry.theory || [], entry.stage || []).join(' '));
      const body = normalize(entry.text);
      let score = (entry.scene || []).length ? 5 : 0;
      for (const token of tokens) {
        if (title === token) score += 120;
        else if (title.includes(token)) score += 75;
        else if (aliases.includes(token)) score += 90 + (aliases[0] === token ? 15 : 0);
        else if (aliases.some(a => a.includes(token))) score += 60;
        else if (tags.includes(token)) score += 40;
        else if (body.includes(token)) score += 1;
        else return null;
      }
      return Object.assign({}, entry, {score});
    }).filter(Boolean).sort((a, b) => b.score - a.score || a.path.localeCompare(b.path, 'zh-CN'));
  }
  return {normalize, search};
});
