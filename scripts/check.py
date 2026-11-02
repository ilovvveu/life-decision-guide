"""Validate the handbook's local links, chapter inventory and key teaching examples."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from decimal import Decimal
import json, re

ROOT = Path(__file__).resolve().parents[1]
errors = []
links = 0
markdown = sorted(ROOT.rglob('*.md'))
for f in markdown:
    text = f.read_text()
    if f.name != '_sidebar.md' and not text.startswith('# '): errors.append(f'{f.relative_to(ROOT)}: missing clear title')
    # Code examples are not navigable links.
    clean = re.sub(r'^```.*?^```\s*$', '', text, flags=re.M|re.S)
    for m in re.finditer(r'!?\[[^\]\n]*\]\(([^)\n]+)\)', clean):
        target = m.group(1)
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:|^//', target): continue
        u = urlsplit(target)
        base = ROOT if u.path.startswith('/') else f.parent
        dest = (base/unquote(u.path).lstrip('/')).resolve() if u.path else f
        if not dest.is_relative_to(ROOT) or not dest.is_file():
            errors.append(f'{f.relative_to(ROOT)}: broken {target}'); continue
        links += 1
        if u.fragment and dest.suffix == '.md':
            hs = re.findall(r'^#{1,6}\s+(.+?)\s*$', dest.read_text(), re.M)
            def slug(h):
                return re.sub(r'\s+', '-', re.sub(r'[^\w\s\-]', '', h).lower())
            if unquote(u.fragment) not in {slug(h) for h in hs}:
                errors.append(f'{f.relative_to(ROOT)}: missing heading {target}')

counts = {'00-开始阅读':4, '01-决策方法':8, '02-日常生活':10, '03-重要选择':5, '04-完整案例':3, '05-可复制模板':7}
for group, expected in counts.items():
    actual = len([p for p in (ROOT/'docs'/group).glob('*.md') if p.name != 'README.md'])
    if actual != expected: errors.append(f'{group}: expected {expected}, got {actual}')

# Recompute prominent teaching numbers using the stated hypothetical inputs.
assert Decimal('.9')*1000 - Decimal('.1')*5000 == 400
assert (3000-1000+500)/100 == 25
assert 60*4 == 240 and 60*12 == 720
assert (35-(4+8+15+3))*24 == 120
assert 6/(120/60) == 3 and 6/((35-30)*8/60) == 9
assert 11000-9000-700 == 1300 and 1300-500 == 800
assert 4000/800 == 5
balances = [6000]
for n in [-3500,-2000,-1500,11000]: balances.append(balances[-1]+n)
assert min(balances) == -1000 and balances[-1] == 10000
assert 6000+11000-7000-1200 == 8800
assert 90/(90+90) == .5

required = ['README.md','LICENSE','LICENSE-CODE','index.html','.nojekyll','vendor/docsify.min.js','vendor/search.min.js','vendor/vue.css','vendor/docsify-LICENSE']
for rel in required:
    if not (ROOT/rel).is_file(): errors.append(f'missing {rel}')
if (ROOT/'LICENSE').exists() and 'Attribution 4.0 International' not in (ROOT/'LICENSE').read_text(): errors.append('wrong document license')
for f in ROOT.rglob('*'):
    if not f.is_file() or '.git' in f.parts: continue
    rel = f.relative_to(ROOT)
    if '.obsidian' in rel.parts or f.suffix in {'.pdf','.zip','.sqlite','.db','.log','.pyc'}:
        errors.append(f'not a public handbook artifact: {rel}')
    # This checker intentionally contains literal credential/path patterns below.
    if 'vendor' in rel.parts or f == Path(__file__).resolve(): continue
    text = f.read_text()
    if re.search(r'/Users/|/private/tmp/|(?:ghp_|github_pat_)[A-Za-z0-9_]{15,}|-----BEGIN .*PRIVATE KEY-----',text):
        errors.append(f'private path or credential pattern: {rel}')
result = {'markdown_files':len(markdown), 'chapters_and_templates':sum(counts.values()), 'local_links':links, 'key_example_calculations':'passed', 'errors':errors}
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))
