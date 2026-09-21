#!/usr/bin/env python3
"""K2 · A 锚笼 v2 —— **合并序一致指派**（L2 · #K2-72 Q2/Q3 · 自板派生）。

动机（R161 结构诊断）：v1（R149_a_grpsep）之 A 锚↔网 指派按「到 B 位总距最小（Hungarian）」求，
**未约束合并序** ⇒ 车队自 B 端驶向锚笼时必然发生「跨线交换」（R159 实测 3 对真交叉 + 3 对贴限）。
本器改为：**以 B 位（源侧固定）之横向序为键，单调指派锚位（x 升序）** ⇒ 嵌套扇形（经典非交叉）。

  · 锚位集合、锚笼几何（pitch≥1.70 · 分组分离）**一律不动**（只置换「网↔锚位」对应）
  · DN：源侧在西（B x≈53–65）· UP：源侧在东（B x≈127–141）⇒ UP 可反向（--up-order desc）

用法：python3 a_cage_v2.py <a_v1.json> <b_sites.json> <out.json> [asc|desc]
"""
import json, sys

def main():
    a = json.load(open(sys.argv[1])); b = json.load(open(sys.argv[2]))
    up_order = sys.argv[4] if len(sys.argv) > 4 else "asc"
    out = {}
    for grp in ("PCIE_DN_OUT", "PCIE_UP_OUT"):   # note: b/a keys are PCIE_DN_OUT* / PCIE_UP_OUT*
        nets = sorted(n for n in a if n.startswith(grp))
        holes = sorted(([float(v[0]), float(v[1])] for v in (a[n] for n in nets)), key=lambda p: (p[0], p[1]))
        # 源侧序键：B 位之横向序（y 升，再 x 升）
        key = sorted(nets, key=lambda n: (float(b[n][1]), float(b[n][0])))
        if grp.startswith("PCIE_UP") and up_order == "desc":
            holes = holes[::-1]
        for n, h in zip(key, holes):
            out[n] = [round(h[0], 4), round(h[1], 4)]
    json.dump(out, open(sys.argv[3], "w"), ensure_ascii=False, indent=1, sort_keys=True)
    # 自检：锚位集合不变
    assert sorted(map(tuple, out.values())) == sorted(map(tuple, ([round(float(x),4),round(float(y),4)] for x, y in a.values()))), "hole set changed!"
    print("wrote", sys.argv[3], "· hole-set preserved · up_order=", up_order)

if __name__ == "__main__":
    main()
