'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {search} = require('../assets/guide.js');
const root = path.resolve(__dirname, '..');
const index = JSON.parse(fs.readFileSync(path.join(root, 'data/search-index.json'), 'utf8'));
const catalog = JSON.parse(fs.readFileSync(path.join(root, 'data/catalog.json'), 'utf8'));
let checks = 0;
function includes(query, id, filters = {}) {
  const matches = search(index.articles, query, filters);
  assert(matches.some(a => a.id === id), `${query}: expected ${id}`); checks++;
  return matches;
}
assert.equal(includes('裸辞', '03-01')[0].id, '03-01'); checks++;
assert.equal(includes('冲动消费', '02-01')[0].id, '02-01'); checks++;
assert.equal(includes('不甘心', '01-02')[0].id, '01-02'); checks++;
includes('纠结', '01-01');
includes('沉没成本', '01-02');
includes('计划超时', '06-01');
includes('如果那么', '06-03');
includes('ＥＶＰＩ', '06-02');
includes('IMPLEMENTATION INTENTIONS', '06-03');
includes('裸辞 现金流', '03-03');
assert.equal(search(index.articles, '一个不存在的检索词xyz', {}).length, 0); checks++;
assert.equal(search(index.articles, '<img src=x onerror=alert(1)>', {}).length, 0); checks++;
const filtered = includes('', '06-03', {scene: '学习', theory: '实施意图', stage: '开始行动'});
assert(filtered.every(a => a.scene.includes('学习') && a.theory.includes('实施意图') && a.stage.includes('开始行动'))); checks++;
assert.equal(search(index.articles, '', {scene: '居住', theory: '实施意图'}).length, 0); checks++;
// Every catalog article remains discoverable via its unique title and each assigned facet.
for (const meta of catalog.articles) {
  const entry = index.articles.find(a => a.id === meta.id);
  assert(entry);
  assert.equal(search(index.articles, entry.title, {})[0].id, meta.id); checks++;
  for (const key of ['scene','theory','stage']) {
    for (const tag of meta[key]) {
      assert(search(index.articles, '', {[key]: tag}).some(a => a.id === meta.id)); checks++;
    }
  }
}
console.log(JSON.stringify({search_checks: checks, indexed_pages: index.articles.length, article_metadata: catalog.articles.length, errors: []}, null, 2));
