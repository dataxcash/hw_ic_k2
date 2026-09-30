#!/usr/bin/env python3
"""k2_drawing_delivery_check_v1.py —— #K2-462 sec.2.8 / sec.4 **图纸件交付自审机器闸**（纯函数 · 零 pcbnew）。

用途：凡交 §16.3 图纸件（尤其 `buildability=relocation_listed`），**先**用本闸对照**在册判据清单**逐项自审，
**缺项即 fail-closed（`ok=False` ＋ 逐项具名）**。立法依据：#K2-413／#K2-416（**逐廊道守恒不得以域级充数**）·
#K2-461 §2.5（搬迁清单须具名「哪些网／从哪到哪／依据哪条授权／含参考面缝合孔与 `ref_plane_continuity`」）·
#K2-462 §2.3（R1462 缺 4 项 ⇒ 打回）。
"""
from __future__ import annotations

ELEMENTS = ("1_one_line_cause_of_death", "2_verified_fact_list",
            "3_corrected_complete_construction_drawing", "4_buildability")
MOVED_ITEMS = ("from_where", "to_where")          # 搬迁项必须具名「从哪／到哪」
DOMAIN_ONLY = ("50x", "frame-level", "域级")        # 域级口径关键字（不得单独充数）


def audit_drawing(doc):
    """返回 {"ok","missing","reasons"}。纯判定 · 不改盘。"""
    miss, why = [], []
    el = doc.get("sec16_3_four_elements") or {}
    for k in ELEMENTS:
        if not el.get(k):
            miss.append(k)
    d = el.get("3_corrected_complete_construction_drawing") or {}
    if not d.get("action_board_state"):
        miss.append("action_board_state")
    b = el.get("4_buildability")
    if b == "relocation_listed":
        items = d.get("items_to_yield") or []
        if not items:
            miss.append("items_to_yield")
        for i, it in enumerate(items):
            for k in MOVED_ITEMS:
                if not it.get(k):
                    miss.append("items_to_yield[%d].%s" % (i, k))
        for k in ("authority_for_the_move", "ref_plane_continuity", "per_corridor_conservation"):
            if not d.get(k):
                miss.append(k)
        pc = str(d.get("per_corridor_conservation") or "")
        low = pc.lower()
        if pc and ("corridor" not in low):
            why.append("per_corridor_conservation 未点名**廊道级**口径 ⇒ 触 #K2-413／#K2-416「域级充数」禁令")
        if any(x in pc for x in DOMAIN_ONLY) and "corridor" not in low:
            why.append("per_corridor_conservation 以**域级**（框级）论据充数 ⇒ 禁用")
        if not (d.get("preserve_list") or d.get("preserve_list_note")):
            why.append("未列 preserve_list（搬迁区内**他网铜须保留**之具名项）")
    elif b == "no_move":
        if not d.get("reservation"):
            why.append("no_move 图纸须给 reservation")
        for k in ("per_corridor_conservation", "authority_for_the_move", "ref_plane_continuity"):
            if not d.get(k):
                miss.append(k)
    else:
        why.append("buildability 须为 no_move 或 relocation_listed")
    return {"ok": not miss and not why, "missing": sorted(set(miss)), "reasons": why}


def main(argv=None):                                        # 便于人工/链内自查
    import argparse, json, sys
    ap = argparse.ArgumentParser(); ap.add_argument("--spec", required=True)
    a = ap.parse_args(argv)
    r = audit_drawing(json.load(open(a.spec, encoding="utf-8")))
    print(json.dumps(r, ensure_ascii=False))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
