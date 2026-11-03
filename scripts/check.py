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

counts = {'00-开始阅读':4, '01-决策方法':8, '02-日常生活':10, '03-重要选择':5, '04-完整案例':5, '05-可复制模板':7, '06-理论工具':6}
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

# Validate public catalog coverage and source references, then check generated artifacts.
catalog = json.loads((ROOT/'data/catalog.json').read_text())
article_paths = {p.relative_to(ROOT).as_posix() for p in (ROOT/'docs').rglob('*.md') if p.name != 'README.md'}
meta_paths = [a['path'] for a in catalog['articles']]
if len(meta_paths) != len(set(meta_paths)) or set(meta_paths) != article_paths:
    errors.append('catalog article coverage mismatch')
ids = [a['id'] for a in catalog['articles']]
if len(ids) != len(set(ids)): errors.append('duplicate catalog ids')
for a in catalog['articles']:
    for key in ['scene','theory','stage']:
        if not a[key] or len(a[key]) != len(set(a[key])) or not set(a[key]) <= set(catalog['vocabulary'][key]):
            errors.append(f"{a['path']}: invalid {key} tags")
    if not a['aliases'] or any(not t.strip() for t in a['aliases']): errors.append(f"{a['path']}: empty aliases")
source_ids = set(re.findall(r'^## (S\d{2})$', (ROOT/'references/sources.md').read_text(), re.M))
for f in markdown:
    for source in set(re.findall(r'\bS\d{2}\b', f.read_text())):
        if source not in source_ids: errors.append(f'{f.relative_to(ROOT)}: unknown source {source}')
import sys
sys.dont_write_bytecode = True
from build import outputs
for rel, expected in outputs().items():
    if not (ROOT/rel).exists() or (ROOT/rel).read_text() != expected: errors.append(f'stale generated file: {rel}')

# Independently evaluate numeric equations printed in the new teaching notes.
import ast
from fractions import Fraction

def calculate(node):
    if isinstance(node, ast.Expression): return calculate(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int,float)): return Fraction(str(node.value))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub): return -calculate(node.operand)
    if isinstance(node, ast.BinOp):
        left,right=calculate(node.left),calculate(node.right)
        if isinstance(node.op,ast.Add): return left+right
        if isinstance(node.op,ast.Sub): return left-right
        if isinstance(node.op,ast.Mult): return left*right
        if isinstance(node.op,ast.Div): return left/right
    raise ValueError('unsupported equation')
new_equations=0
for f in (ROOT/'docs/06-理论工具').glob('*.md'):
    for expression in re.findall(r'`([^`\n]+)`',f.read_text()):
        normalized=expression.replace('×','*').replace('÷','/')
        if not re.fullmatch(r'[\d. ()+*/=\-]+',normalized) or normalized.count('=')!=1: continue
        left,right=normalized.split('=')
        if calculate(ast.parse(left.strip(),mode='eval')) != calculate(ast.parse(right.strip(),mode='eval')):
            errors.append(f'{f.name}: wrong equation {expression}')
        new_equations+=1
if new_equations < 6: errors.append('new teaching equation coverage unexpectedly low')
# Enumerate test outcomes independently, including the option not to buy.
states=[(Fraction(3,5),600,Fraction(4,5)),(Fraction(2,5),-400,Fraction(1,5))]
without=max(Fraction(0),sum(p*payoff for p,payoff,_ in states))
with_test=sum(max(Fraction(0),sum(p*payoff*(q if passed else 1-q) for p,payoff,q in states)) for passed in [True,False])
perfect=sum(p*max(0,payoff) for p,payoff,_ in states)
assert without==200 and with_test==256 and perfect==360
assert 0 <= with_test-without <= perfect-without
assert with_test-without-30==26 and with_test-without-70==-14

required = ['README.md','LICENSE','LICENSE-CODE','index.html','.nojekyll','vendor/docsify.min.js','vendor/search.min.js','vendor/vue.css','vendor/docsify-LICENSE','assets/guide.js','assets/guide.css','data/catalog.json','data/search-index.json','标签索引.md','理论索引.md']
for rel in required:
    if not (ROOT/rel).is_file(): errors.append(f'missing {rel}')
if (ROOT/'LICENSE').exists() and 'Attribution 4.0 International' not in (ROOT/'LICENSE').read_text(): errors.append('wrong document license')
for f in ROOT.rglob('*'):
    if not f.is_file() or '.git' in f.parts: continue
    rel = f.relative_to(ROOT)
    if '.obsidian' in rel.parts or f.suffix in {'.pdf','.zip','.sqlite','.db','.log','.pyc'}:
        errors.append(f'not a public handbook artifact: {rel}'); continue
    # This checker intentionally contains literal credential/path patterns below.
    if 'vendor' in rel.parts or f == Path(__file__).resolve(): continue
    text = f.read_text()
    if re.search(r'/Users/|/private/tmp/|(?:ghp_|github_pat_)[A-Za-z0-9_]{15,}|-----BEGIN .*PRIVATE KEY-----',text):
        errors.append(f'private path or credential pattern: {rel}')
result = {'markdown_files':len(markdown), 'chapters_and_templates':sum(counts.values()), 'local_links':links, 'catalog_articles':len(meta_paths), 'tag_vocabulary':sum(len(v) for v in catalog['vocabulary'].values()), 'new_printed_equations_checked':new_equations, 'key_example_calculations':'passed', 'errors':errors}
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))
