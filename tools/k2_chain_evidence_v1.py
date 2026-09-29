#!/usr/bin/env python3
"""k2_chain_evidence_v1.py --- **链证据健壮提取器**（#K2-438 §三.1 · `M-ENG-EVIDENCE-EXTRACTION` 补法）。

WHY：`per_block_C1_gate` **在生产链内已生成**，却因提取脚本按固定形状（`['chain']['chain']`）解析而在回执里成了
`null`（R1286 的实际故障）；同一脚本又把**残余网的具名表抄错**（R1288 误把旧跑的 `SWDIO/SWCLK_BOOT0` 写成本跑
残余，本跑真值是 `NRST/P3V3_AUX/I2C1_SDA/P3V3`）。本器：

  * `find_stage`  —— **递归**搜索阶段，兼容链被存成 dict/list/**JSON 字符串**三种形态；找不到 ⇒ **fail-loud**；
  * `residual_table` —— 从原始 DRC 的 `unconnected_items` **逐项**取出「网 ∈ 哪个功能块」，描述里读不出网名 ⇒
    **fail-loud**（绝不静默漏项 —— 这正是 R1288 抄错的机制）。

零搜索 · 纯函数 · 同输入恒同输出。
"""
from __future__ import annotations
import argparse, importlib.util, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
_NET_RE = re.compile(r"\[([^\]]+)\]")


def find_stage(obj, stage):
    """**递归**查找含 `{"stage": <stage>}` 的字典；兼容 dict / list / JSON 字符串。
    找不到 ⇒ 抛 `KeyError`（**fail-loud**，不返回 null）。"""
    if isinstance(obj, str):
        try:
            obj = json.loads(obj)
        except Exception:                                        # noqa: BLE001
            raise KeyError("stage %r not found (string that is not JSON)" % stage)
    if isinstance(obj, dict):
        if obj.get("stage") == stage:
            return obj
        for v in obj.values():
            try:
                return find_stage(v, stage)
            except KeyError:
                continue
    elif isinstance(obj, list):
        for v in obj:
            try:
                return find_stage(v, stage)
            except KeyError:
                continue
    raise KeyError("stage %r not found" % stage)


def _family_of(nets):
    """复用 K-2 的**确定性**功能族表（单一事实源；不重造）。"""
    spec = importlib.util.spec_from_file_location("kfb_ev", os.path.join(HERE, "k2_functional_block_v1.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.family_of(nets)


def parse_net(desc):
    """从 DRC 条目描述里取网名 `[...]`；读不出 ⇒ **fail-loud**（绝不静默丢项）。"""
    got = _NET_RE.search(desc or "")
    if not got:
        raise KeyError("unparseable DRC item (no [NET]): %r" % desc)
    return got.group(1)


def residual_table(drc):
    """原始 DRC（`unconnected_items`）⇒ 逐项归因行；含每项所涉网、功能族、条目描述。"""
    rows = []
    for it in (drc.get("unconnected_items") or []):
        nets, descs = [], []
        for i in (it.get("items") or []):
            d = i.get("description") or ""
            n = parse_net(d)
            if n not in nets:
                nets.append(n)
            descs.append(d)
        rows.append({"type": it.get("type"), "nets": nets, "family": _family_of(nets), "items": descs})
    return rows


def per_block_attribution(drc):
    """逐功能块归因表：块 → 条目/网数。**注**：块内计数按**网去重**，故其和可 < C1 条目数。"""
    rows = residual_table(drc)
    by = {}
    for r in rows:
        b = by.setdefault(r["family"], {"items": 0, "nets": []})
        b["items"] += 1
        for n in r["nets"]:
            if n not in b["nets"]:
                b["nets"].append(n)
    return {"n_items": len(rows), "n_nets": len({n for r in rows for n in r["nets"]}),
            "per_block": {k: {"items": v["items"], "nets": sorted(v["nets"])} for k, v in sorted(by.items())},
            "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True, help="the verdict/record artifact OR a raw DRC file")
    ap.add_argument("--stage", help="extract the chain stage of this name (fail-loud)")
    ap.add_argument("--attrib", action="store_true", help="emit the per-block residual attribution from a raw DRC")
    a = ap.parse_args()
    d = json.load(open(a.json, encoding="utf-8"))
    if a.attrib:
        print(json.dumps(per_block_attribution(d), ensure_ascii=False, indent=1))
    else:
        print(json.dumps(find_stage(d, a.stage), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
