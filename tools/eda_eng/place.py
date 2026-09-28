"""place --- 放置（声明式）。v1 = 读放置源 + 施加场景位移 + 出报告；**不碰板**。

放置源：pm_gate/artifacts/k2_v4/L2/PLACEMENT_SOLUTION_v1.json（链唯一坐标源）
场景：{refs:[...], delta_mm:[dx,dy]} —— 例：考题 A 的 U1/U2/U4/U5 +5mm。
"""
from __future__ import annotations
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "pm_gate", "artifacts", "k2_v4", "L2", "PLACEMENT_SOLUTION_v1.json")


def load_source(path=SRC):
    d = json.load(open(path, encoding="utf-8"))
    return d


def apply_scenario(refs, delta_mm, src=SRC, out=None):
    d = load_source(src)
    moved, missing = [], []
    for r in refs:
        hit = False
        for key in ("refs", "components", "placements"):
            blk = d.get(key)
            if isinstance(blk, dict) and r in blk:
                v = blk[r]
                if isinstance(v, dict) and "at" in v and isinstance(v["at"], list):
                    v["at"] = [round(float(v["at"][0]) + delta_mm[0], 4), round(float(v["at"][1]) + delta_mm[1], 4)]
                    moved.append({"ref": r, "at": v["at"]})
                    hit = True
                    break
        if not hit:
            missing.append(r)
    res = {"artifact": "eda_eng_place_scenario", "source": os.path.relpath(src, ROOT),
           "refs": refs, "delta_mm": delta_mm, "moved": moved, "missing": missing,
           "board_touched": False, "note": "declarative only; a board is produced by route (engine), never by hand"}
    if out:
        json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        res["written_source"] = out
    return res
