#!/usr/bin/env python3
"""reproduce_c3_spec_regen_draft.py — 复跑 C3 对齐准备：生产 SPEC 注入 DS320PR1601.per_ball → 生产模型 ⑦ 真执行。

背景：REVIEW_ADVERSARIAL_v26 条件 C3 — SPEC_k2_v4.json 仍旧 U3/U7 无 bga_escape.per_ball
→ 生产 plan() 得 ⑦=not_configured（ok=True 静默过，可验证性断裂）。v27 已用 SPEC 副本
（SPEC_k2_v4_c3poc.json）POC 证明机制路径；本脚本 = v28 对齐准备：以**当前生产 SPEC 本体**
深拷贝 + 注入节点（1:1 契约复用 POC）生成 /tmp 再生草案 → 生产 RoutingTopologyGate.plan()
v1.4 真执行 → 断言 ⑦ = evaluated + FEASIBLE（SPEC 本体级机器证明，消除假静默）。

性质（G3 证书边界）：本脚本非引擎、非模型结论 —— 只做「spec 文档变换（注入）+ 喂模型 +
读模型输出断言」的壳，零新增求解逻辑；⑦ 判定全部来自生产模型输出。

用途：DS320PR1601 原理图 ECO 落地后的 SPEC 真再生 session 可直接复用本脚本（改 SPEC 输入
路径为再生后 SPEC / 移除 U3/U7 遗留项后重跑即可）。

依赖（容器根权威 _shared 引擎 v1.4）：
  SPEC_k2_v4.json                    = 生产 SPEC（当前仍 U3/U7 旧拓扑，C3 本体对象）
  SPEC_k2_v4_c3poc.json              = v27 POC 注入节点源（DS320PR1601.per_ball 契约 1:1）
  /tmp/opencode/boards/k2_v6.kicad_pcb（卡0落位板，生产基线）
  channel_alloc_v4/channel_alloc.json（生产 alloc）

用法：python3 reproduce_c3_spec_regen_draft.py [--spec 生产SPEC路径]
输出：stdout 逐约束状态 + 草案路径/sha16；断言 ⑦ = evaluated + DS320PR1601 FEASIBLE。
注意：草案只写 /tmp（不碰生产 SPEC，冻结纪律）；U3/U7 遗留项保留至 ECO 完成换名
（见 C3_SPEC_REGEN_v27.md §4 注入注意）。本脚本 = 对齐准备，非 ECO 后终态再生的替代。
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# 权威 _shared = 最外含 .gitmodules 的父（容器根）；避免命中 k2 内嵌陈旧副本
_gm = [p for p in HERE.parents if (p / ".gitmodules").exists()]
SP = _gm[-1] if _gm else HERE.parents[-1]
sys.path.insert(0, str(SP / "_shared"))

from eda_core.routing_topology_gate import RoutingTopologyGate  # noqa: E402

PROD_SPEC = HERE.parent / "SPEC_k2_v4.json"          # k2_v4/L3/SPEC_k2_v4.json
POC_SPEC = HERE / "SPEC_k2_v4_c3poc.json"            # v27 POC 注入节点源
DRAFT_OUT = Path("/tmp/opencode/c3_spec_regen_draft/SPEC_k2_v4_ds320_draft.json")
K2_BOARD = "/tmp/opencode/boards/k2_v6.kicad_pcb"
K2_ALLOC = str(HERE.parent / "model_solves" / "channel_alloc_v4" / "channel_alloc.json")
K2_RULES = str(SP / "_shared" / "eda_core" / "drc_rules.json")
K2_CONFIG = str(HERE.parent.parent / "L2" / "route_model_config.json")  # k2_v4/L2


def _sha16(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=str(PROD_SPEC), help="生产/再生 SPEC 输入路径")
    args = ap.parse_args()

    prod_path = Path(args.spec)
    prod = json.loads(prod_path.read_text(encoding="utf-8"))
    poc = json.loads(POC_SPEC.read_text(encoding="utf-8"))

    # 注入节点 1:1 取自 v27 POC（契约复用，逐字节不手造）
    inj = copy.deepcopy(poc["components"]["redriver"]["DS320PR1601"])
    n_ball = len(inj["bga_escape"]["per_ball"]["ballmap"])
    assert n_ball == 354, f"ballmap 异常: {n_ball}"
    assert "DS320PR1601" not in prod["components"]["redriver"], \
        "SPEC 已含 DS320PR1601（ECO 已落地？）——本脚本用于未落地前对齐准备"
    prod["components"]["redriver"]["DS320PR1601"] = inj  # U3/U7 保留至 ECO 完成换名

    DRAFT_OUT.parent.mkdir(parents=True, exist_ok=True)
    DRAFT_OUT.write_text(json.dumps(prod, indent=1, ensure_ascii=False), encoding="utf-8")

    cfg = json.load(open(K2_CONFIG, encoding="utf-8"))
    gate = RoutingTopologyGate(K2_BOARD, str(DRAFT_OUT), K2_ALLOC, K2_RULES, config=cfg)
    r = gate.plan()
    print("version=%s verdict=%s" % (r["version"], r["verdict"]))
    c7 = r["constraints"]["BGA_PER_BALL_ESCAPE"]
    print("BGA_PER_BALL_ESCAPE ok=%s status=%s level=%s"
          % (c7["ok"], c7.get("status"), c7.get("level")))
    for ref, res in (c7.get("per_ref") or {}).items():
        print("  %s: verdict=%s ok=%s signal=%d direct=%d via=%d crossing=%d deficits=%d"
              % (ref, res.get("verdict"), res.get("ok"), res.get("signal_ball_count"),
                 res.get("direct_count"), res.get("via_count"),
                 res.get("crossing_pairs"), len(res.get("deficits", []))))
    print("prod_sha16=%s draft_sha16=%s" % (_sha16(prod_path), _sha16(DRAFT_OUT)))
    print("draft=%s" % DRAFT_OUT)

    passed = (c7.get("status") == "evaluated" and c7.get("ok")
              and any(v.get("verdict") == "FEASIBLE"
                      for v in (c7.get("per_ref") or {}).values()))
    print("REGEN_DRAFT_PASS" if passed else "REGEN_DRAFT_FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
