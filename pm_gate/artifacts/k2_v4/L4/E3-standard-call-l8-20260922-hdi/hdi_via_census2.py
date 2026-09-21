#!/usr/bin/env python3
"""HDI 过孔结构 census v2（修正：覆盖 `(via` 之多行/单行两种写法）· 只读
用法: python3 hdi_via_census2.py <board> [out.json]"""
import re,sys,json,collections
ORDER=["F.Cu","In1.Cu","In2.Cu","In3.Cu","In4.Cu","In5.Cu","In6.Cu","B.Cu"]
lines=open(sys.argv[1],encoding='utf-8').read().split('\n')
vias=[];i=0
while i<len(lines):
    if re.match(r'^\s*\(via(\s|$)',lines[i]):
        blk=[];d=0
        while i<len(lines):
            blk.append(lines[i]); d+=lines[i].count('(')-lines[i].count(')'); i+=1
            if d<=0: break
        t='\n'.join(blk)
        at=re.search(r'\(at ([\-\d\.]+) ([\-\d\.]+)\)',t); lay=re.search(r'\(layers ([^)]*)\)',t)
        sz=re.search(r'\(size ([\d\.]+)\)',t); dr=re.search(r'\(drill ([\d\.]+)\)',t)
        net=re.search(r'\(net "([^"]*)"\)',t)
        if at and lay:
            ls=re.findall(r'"([^"]+)"',lay.group(1))
            ls=[l for l in ls if l in ORDER]
            if ls: vias.append({"x":float(at.group(1)),"y":float(at.group(2)),"top":ls[0],"bot":ls[-1],
                                "size":float(sz.group(1)) if sz else None,"drill":float(dr.group(1)) if dr else None,
                                "net":net.group(1) if net else None})
    else: i+=1
pair=collections.Counter((v["top"],v["bot"]) for v in vias)
def key(k): return (ORDER.index(k[0]),ORDER.index(k[1]))
dp={f"{a}->{b}":n for (a,b),n in sorted(pair.items(),key=lambda kv:key(kv[0]))}
inner=[f"{a}->{b}" for (a,b) in pair if a not in("F.Cu","B.Cu") and b not in("F.Cu","B.Cu")]
rep={"board":sys.argv[1],"n_vias":len(vias),"drill_pair_counts":dp,
     "n_through":pair.get(("F.Cu","B.Cu"),0),
     "n_blind_buried":len(vias)-pair.get(("F.Cu","B.Cu"),0),
     "inner_to_inner_pairs":sorted(inner),
     "with_in5":sum(1 for v in vias if ORDER.index(v["top"])<=5<=ORDER.index(v["bot"])),
     "note":"ENG 测量件 · 无 verdict · 工艺准入(阶数/允许盲埋)归 criteria/jlc_hdi_capability.yaml + 监理"}
print(json.dumps(rep,ensure_ascii=False,indent=1))
if len(sys.argv)>2: json.dump(rep,open(sys.argv[2],'w'),ensure_ascii=False,indent=1)
