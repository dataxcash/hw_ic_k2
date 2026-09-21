#!/usr/bin/env python3
"""In5 等长基线（R4 闸前置 · ENG 只交测量）：PCIE_UP_OUT 16 网之 In5 走线长度 + N/P skew。
只读解析 .kicad_pcb 文本 · 不改任何件。用法: python3 in5_len_baseline.py <board> [out.json]"""
import re,sys,json,math,collections
b=sys.argv[1]; t=open(b,encoding='utf-8').read()
# 取所有 (segment ...) 块 -> start/end/width/layer/net
blocks=re.split(r'\n\s*\(segment\n', t)
rows=[]
for blk in blocks[1:]:
    blk=blk.split('\n\t)')[0]
    m=re.search(r'\(start ([\-\d\.]+) ([\-\d\.]+)\)',blk); n=re.search(r'\(end ([\-\d\.]+) ([\-\d\.]+)\)',blk)
    lay=re.search(r'\(layer "([^"]+)"\)',blk); net=re.search(r'\(net "([^"]+)"\)',blk)
    if not(m and n and lay and net): continue
    x1,y1=float(m.group(1)),float(m.group(2)); x2,y2=float(n.group(1)),float(n.group(2))
    rows.append((net.group(1),lay.group(1),math.dist((x1,y1),(x2,y2))))
L=collections.defaultdict(lambda: collections.defaultdict(float))
for net,lay,d in rows: L[net][lay]+=d
res={}
for i in range(8):
    n=f"PCIE_UP_OUT{i}_N_J2"; p=f"PCIE_UP_OUT{i}_P_J2"
    ln=L.get(n,{}).get("In5.Cu",0.0); lp=L.get(p,{}).get("In5.Cu",0.0)
    res[f"pair{i}"]={"N_in5_mm":round(ln,3),"P_in5_mm":round(lp,3),"skew_mm":round(abs(ln-lp),3)}
tot_n=sum(res[f"pair{i}"]["N_in5_mm"] for i in range(8)); tot_p=sum(res[f"pair{i}"]["P_in5_mm"] for i in range(8))
out={"board":b,"layer":"In5.Cu","per_pair":res,"total_N_mm":round(tot_n,3),"total_P_mm":round(tot_p,3),
     "max_skew_mm":round(max(v["skew_mm"] for v in res.values()),3),"note":"ENG 测量件 · 无 verdict 字段 · 阈值归 SPEC/监理"}
print(json.dumps(out,ensure_ascii=False,indent=1))
if len(sys.argv)>2: json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False,indent=1)
