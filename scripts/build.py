"""Build shared Markdown navigation, readable metadata and the offline search index."""
from pathlib import Path
from urllib.parse import quote
import argparse, json, re

ROOT=Path(__file__).resolve().parents[1]
LABELS={'scene':'场景','theory':'理论','stage':'阶段'}
META=re.compile(r'\n<!-- guide-meta:start -->.*?<!-- guide-meta:end -->\n',re.S)
def title(text):return re.search(r'^# (.+)$',text,re.M).group(1)
def link(path):return quote(str(path),safe='/.-_')
def plain(text):
    text=META.sub('\n',text)
    text=re.sub(r'<!--.*?-->','',text,flags=re.S)
    text=re.sub(r'!?(\[([^\]]*)\])\([^\n)]*\)',r'\2',text)
    text=re.sub(r'[`*_>#|]',' ',text)
    return re.sub(r'\s+',' ',text).strip()

def outputs():
    catalog=json.loads((ROOT/'data/catalog.json').read_text())
    out={};entries=[];groups={}
    for row in catalog['articles']:
        path=row['path'];original=(ROOT/path).read_text();body=META.sub('\n',original)
        first,rest=body.split('\n',1)
        tags=['#'+LABELS[k]+'/'+x for k in LABELS for x in row[k]]
        meta='\n<!-- guide-meta:start -->\n标签： '+' '.join(tags)+'\n\n检索词：'+'、'.join(row['aliases'])+'\n<!-- guide-meta:end -->\n'
        body=first+'\n'+meta+rest.lstrip('\n')
        out[path]=body
        entry={**row,'title':title(body),'group':Path(path).parent.name.split('-',1)[1]}
        entries.append(entry);groups.setdefault(Path(path).parent,[]).append(entry)
    sidebar=['- [阅读首页](/README.md)','- [标签索引](/'+link('标签索引.md')+')','- [理论索引](/'+link('理论索引.md')+')','']
    for group,rows in sorted(groups.items()):
        name=group.name.split('-',1)[1]
        summary='复制到自己的私人笔记后填写，按实际问题删减。\n\n' if name=='可复制模板' else ''
        index='# '+name+'\n\n'+summary
        for e in rows:index+='- ['+e['title']+']('+link(Path(e['path']).name)+')\n'
        index+='\n[标签索引](../../'+link('标签索引.md')+') · [理论索引](../../'+link('理论索引.md')+') · [返回阅读首页](../../README.md)\n'
        out[(group/'README.md').as_posix()]=index
        sidebar+=['**'+name+'**','']
        for e in rows:sidebar+=['- ['+e['title']+'](/'+link(e['path'])+')']
        sidebar+=['']
    sidebar+=['**来源与维护**','','- [参考来源](/references/sources.md)','- [证据与应用](/references/evidence-map.md)','- [贡献指南](/CONTRIBUTING.md)','- [变更记录](/CHANGELOG.md)','']
    out['_sidebar.md']='\n'.join(sidebar)
    tags='# 标签索引\n\n先选你面对的场景，再看要处理的阶段或相关理论。每篇文章的标签与检索词同时适用于 Obsidian 阅读副本；网站搜索栏可组合筛选。\n\n例如：消费 + 比较方案，或学习 + 开始行动。筛选没有结果时可以放宽一个条件。\n\n'
    tags+='[按问题选工具](docs/00-开始阅读/04-按问题选择工具.md) · [理论索引]('+link('理论索引.md')+') · [阅读首页](README.md)\n\n'
    for k,label in LABELS.items():
        tags+='## '+label+'入口\n\n'+' · '.join('['+t+'](#'+label+'-'+t+')' for t in catalog['vocabulary'][k])+'\n\n'
        for tag in catalog['vocabulary'][k]:
            tags+='## '+label+'-'+tag+'\n\n'
            tags+='\n'.join('- ['+e['title']+']('+link(e['path'])+')' for e in entries if tag in e[k])+'\n\n'
    out['标签索引.md']=tags
    theory='# 理论索引\n\n从概念找到生活问题，再进入场景、案例与工具。部分理论已有独立精读，其他概念通过现有章节讲解；名称相同不表示所有生活应用都获得研究直接验证。\n\n先看：[怎样读研究与建议](docs/00-开始阅读/03-怎样读研究与建议.md) · [证据与应用](references/evidence-map.md) · [标签索引]('+link('标签索引.md')+')\n\n'
    guide={
    '参考类预测':('计划总比预计久','docs/06-理论工具/01-用相似经历校正你的计划.md','S13'),
    '信息价值':('继续查资料能否改善选择','docs/06-理论工具/02-算清再查一次资料值不值.md','S15'),
    '实施意图':('想做，却迟迟没有开始','docs/06-理论工具/03-把想做变成遇到情境就行动.md','S14'),
    '实物期权':('先试、等待还是直接投入','docs/06-理论工具/04-为不确定的选择保留下一步.md','S16'),
    '比较优势':('怎样分工并讨论公平','docs/06-理论工具/05-分工比较各自放弃了什么.md','S17'),
    '匹配理论':('自己的愿望怎样遇上对方选择','docs/06-理论工具/06-双向选择还要看对方与规则.md','S18'),
    '机会成本':('同一份时间与钱还能怎样使用','docs/01-决策方法/02-只比较从现在开始的代价.md','S01'),
    '沉没成本':('舍不得已投入的时间与钱','docs/01-决策方法/02-只比较从现在开始的代价.md','S01'),
    '边际分析':('再多投入一单位值不值','docs/02-日常生活/10-工具升级先算端到端收益.md','S01'),
    '前景理论':('参考点怎样影响得失感受','docs/02-日常生活/01-买东西先找真实使用场景.md','S03'),
    '有限理性':('怎样把复杂问题缩小到可处理','docs/00-开始阅读/02-一套能调整的生活安排.md','S02'),
    '心理账户':('账面有余钱却仍错过付款','docs/04-完整案例/03-月底有结余为什么月中还缺钱.md','S02'),
    '贝叶斯':('新证据怎样改变原有判断','docs/01-决策方法/05-先问证据来自哪里.md','S09'),
    '因果推断':('前后变化是否真由某方法造成','docs/01-决策方法/06-把生活小实验做得可比较.md','S05'),
    '实验设计':('怎样让试用结果更可比较','docs/01-决策方法/06-把生活小实验做得可比较.md','S04'),
    '自我控制':('计划怎样受到环境和当下偏好影响','docs/01-决策方法/07-让环境帮助你执行.md','S02'),
    '激励':('指标、规则怎样改变行动','docs/01-决策方法/08-合作先看规则和激励.md','S06'),
    '信息不对称':('对方知道更多时怎样检查信息','docs/01-决策方法/05-先问证据来自哪里.md','S07'),
    '交易成本':('协作、迁移和退出还有哪些代价','docs/03-重要选择/05-长期使用的平台要保留迁移能力.md','S08'),
    '风险分散':('多个收入或平台是否仍依赖同一风险','docs/01-决策方法/04-平均划算还要看失败能否承受.md','S10')}
    for term in catalog['vocabulary']['theory']:
        question,path,source=guide[term]
        theory+='## '+term+'\n\n'+question+'。先读[核心解释]('+link(path)+')，来源见['+source+'](references/sources.md#'+source.lower()+')。\n\n'
        related=[e for e in entries if term in e['theory'] and e['path']!=path]
        theory+='\n'.join('- ['+e['title']+']('+link(e['path'])+')' for e in related)+'\n\n'
    theory+='''## 理论给出不同方向时

**坚持还是退出：**[沉没成本](docs/01-决策方法/02-只比较从现在开始的代价.md)提醒你不被不可追回的投入绑住；[实施意图](docs/06-理论工具/03-把想做变成遇到情境就行动.md)帮助落实仍然值得的目标。先比较未来投入与价值，再决定是否加强执行。

**继续调查还是开始行动：**[信息价值](docs/06-理论工具/02-算清再查一次资料值不值.md)比较信息可能带来的改善与获取成本；[实物期权](docs/06-理论工具/04-为不确定的选择保留下一步.md)还要保留等待导致的损失。等不到新信息、也无法改行动时，单纯等待可能没有帮助。

**效率还是公平：**[比较优势](docs/06-理论工具/05-分工比较各自放弃了什么.md)帮助查看总产出与机会成本；[隐形责任](docs/02-日常生活/07-家庭分工要把隐形责任说出来.md)提醒你检查负担分配。节省时间不能独自决定谁应该承担责任。

'''
    out['理论索引.md']=theory
    entrymap={e['path']:e for e in entries};search=[]
    mdpaths={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*.md')}|{p for p in out if p.endswith('.md')}
    for path in sorted(mdpaths-{'_sidebar.md'}):
        text=out.get(path) if path in out else (ROOT/path).read_text()
        e=entrymap.get(path,{'id':path,'path':path,'title':title(text),'group':'索引与说明','scene':[],'theory':[],'stage':[],'aliases':[]})
        search.append({**e,'sources':sorted(set(re.findall(r'\bS\d{2}\b',text))),'text':plain(text)})
    out['data/search-index.json']=json.dumps({'version':catalog['version'],'updated':catalog['updated'],'vocabulary':catalog['vocabulary'],'articles':search},ensure_ascii=False,separators=(',',':'))+'\n'
    return out

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    expected=outputs();stale=[]
    for name,text in expected.items():
        path=ROOT/name
        if args.check:
            if not path.exists() or path.read_text()!=text:stale.append(name)
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    print(json.dumps({'generated_files':len(expected),'stale':stale},ensure_ascii=False))
    raise SystemExit(bool(stale))
if __name__=='__main__':main()
