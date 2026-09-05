import re, json, sys
txt = open("/tmp/opencode/ds320_text.txt", encoding="utf-8").read()
# 匹配 Table 5-1 信号球行：位置(如 N2/AA10) + 信号(如 A_PERp0)
# 信号后缀数字 = lane 号；前面 A_PER/A_PET/B_PER/B_PET + 极性 p/n
pat = re.compile(r'^\s*([A-Z]+)([0-9]+)\s+([AB])_([A-Z]+)([pn])([0-9]+)\s')
balls = []
for line in txt.split("\n"):
    m = pat.match(line)
    if m:
        row, col, side, kind, pol, lane = m.groups()
        balls.append(dict(name=f"{side}_{kind}{pol}{lane}", row=row, col=int(col),
                          side=side, kind=kind, pol=pol, lane=int(lane)))
print(f"parsed signal balls = {len(balls)}")
# 验证每 lane 8 球
from collections import Counter
cl = Counter(b['lane'] for b in balls)
print("balls per lane:", dict(sorted(cl.items())))
# lane0 明细
for b in sorted([x for x in balls if x['lane']==0], key=lambda x:(x['kind'],x['pol'])):
    print(f"  lane0 {b['name']:8s} row={b['row']:3s} col={b['col']:2d}")
# 列带分布: 每个 kind 的 col 集合
bands = {}
for b in balls:
    key=(b['side'],b['kind'])
    bands.setdefault(key, set()).add(b['col'])
for k,cols in sorted(bands.items()):
    print(f"  {k}: cols {sorted(cols)}")
json.dump(balls, open("/tmp/opencode/ballmap_raw.json","w"), indent=1)
