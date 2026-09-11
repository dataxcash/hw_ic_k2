#!/usr/bin/env python3
"""CO-73：【L2 PDN/叠层分配】SPEC rev-7 —— 层角色声明**一致性终扫**（一次性，非历史件）。

CO-72 已把 pd 的 GND 平面清单对齐 In1/In3/In6；本件终结**其余当前态**声明中残留的旧层角色：
  1. `pd.zone_defs.gnd_stitch_via`（note + 各 coordinates[*].basis）：『GND 回路由 **In1/3/5** 平面承担』→ **In1/3/6**
     （31 条 blocked 缝合位的回路归宿；REV6 下 In5=信号、In6=GND）。
  2. `constraints.j2_escape_topology.outer_basis`：『B.Cu 释放给低速（2026-08-19 用户裁决）』与 LID.1/REV6
     （B.Cu=高速信号层，承载 dn 带逃逸/落段）矛盾 → 更正为 REV6 事实。
  3. `layer_plan.in6_usage`：旧『removed: 8L In6.Cu semantics』→ REV6 下 In6=GND 平面（在册）。
  4. `layer_plan.strap_domain_v32.deps[1]`：PDN 平面清单补 In6。
**不动**历史件（`_spec_rev_*` 溯源块 / `appendix` / `pd.ecn_pending_items[*]` 既往 PM 裁决文本）。
只读冻结源；版本 bump 新文件；零几何/阈值改动（引擎不消费上述键）。
"""
from __future__ import annotations
import copy, hashlib, json, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
SRC = L3 / "SPEC_k2_v4.spec-rev-6.json"
OUT = L3 / "SPEC_k2_v4.spec-rev-7.json"
REC = L3 / "mcio_feas_step2/m13_v57_co73_layer_role_consistency.json"


def s16(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    s6 = json.loads(SRC.read_text(encoding="utf-8"))
    src_sha = s16(SRC)
    s7 = copy.deepcopy(s6)
    s7["spec_version"] = "1.1.spec-rev-7"
    touched = []

    # 1) gnd_stitch_via：In1/3/5 -> In1/3/6
    gsv = s7["pd"]["zone_defs"]["gnd_stitch_via"]
    def fix(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                fix(v, path + "/" + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                fix(v, path + f"[{i}]")
        elif isinstance(o, str) and "In1/3/5" in o:
            touched.append(path)
            parent = s7
            # 就地替换（通过闭包外引用不可行，改用显式回写列表）
    n_before = json.dumps(gsv, ensure_ascii=False).count("In1/3/5")
    def repl(o):
        if isinstance(o, dict):
            return {k: repl(v) for k, v in o.items()}
        if isinstance(o, list):
            return [repl(v) for v in o]
        if isinstance(o, str):
            return o.replace("In1/3/5", "In1/3/6")
        return o
    s7["pd"]["zone_defs"]["gnd_stitch_via"] = repl(gsv)
    n_after = json.dumps(s7["pd"]["zone_defs"]["gnd_stitch_via"], ensure_ascii=False).count("In1/3/5")
    assert n_before > 0 and n_after == 0, (n_before, n_after)

    # 2) j2_escape_topology.outer_basis
    j = s7["constraints"]["j2_escape_topology"]
    assert "B.Cu 释放给低速" in j["outer_basis"]
    j["outer_basis"] = ("8 层（LID REV6）：In2 独立走廊容纳全部 UP_OUT；B.Cu 为**高速信号层**（dn 带逃逸/落段，"
                        "REV6 下由 In6=GND 参考、阻抗可控）。CO-73 更正：原文『B.Cu 释放给低速 (2026-08-19 用户裁决)』"
                        "与 LID.1/REV6 事实矛盾；低速网归属见 layer_plan。")

    # 3) layer_plan.in6_usage
    lp = s7["layer_plan"]
    lp["in6_usage"] = ("in_use: LID REV6（方案(a)）下 In6.Cu = **GND 平面**（4 平面之一；信号层 = F/In2/In5/B）。"
                       "CO-73 更正：原文『removed: 8L In6.Cu semantics (6L stack …)』为 6L 时代残留。")

    # 4) strap_domain_v32 deps 平面清单
    deps = lp.get("strap_domain_v32", {}).get("deps")
    for i, dep in enumerate(deps or []):
        if isinstance(dep, str) and "In1 In3 GND pours" in dep:
            deps[i] = dep.replace("In1 In3 GND pours", "In1 In3 In6 GND pours")
            touched.append(f"/layer_plan/strap_domain_v32/deps[{i}]")

    s7["_spec_rev_7"] = {
        "card": "SPEC-REV-7", "at": "2026-09-12",
        "authority": "L2 PDN/叠层分配 自裁（CO-73；PDN·层角色声明一致性终扫）",
        "changes": ["spec_version: 1.1.spec-rev-6 -> 1.1.spec-rev-7",
                    "pd.zone_defs.gnd_stitch_via（note + coordinates[*].basis）：In1/3/5 平面 -> In1/3/6",
                    "constraints.j2_escape_topology.outer_basis：更正『B.Cu 释放给低速』（REV6 下 B.Cu=高速信号层）",
                    "layer_plan.in6_usage：更正为 REV6 In6=GND 平面（在册）",
                    "layer_plan.strap_domain_v32.deps：PDN 平面清单补 In6"],
        "unchanged": "stackup / impedance / net_classes / vias / corridors / board / components / pd.zone_defs 的层与网 全部未动；零几何",
        "not_touched": "历史件（_spec_rev_* 溯源块 / appendix / pd.ecn_pending_items 既往 PM 裁决文本）",
        "geometry_impact_expected": "none（引擎不消费上述键）",
        "rollback": "删除本文件；引擎/记录指回 spec-rev-6 (9e8fb5bae4a33207)"}

    def diff(a, b, pre=""):
        out = []
        if isinstance(a, dict) and isinstance(b, dict):
            for k in set(a) | set(b):
                if k in ("spec_version", "_spec_rev_7"):
                    continue
                if k not in a: out.append(pre + "/" + k + " (added)")
                elif k not in b: out.append(pre + "/" + k + " (removed)")
                else: out += diff(a[k], b[k], pre + "/" + k)
        elif isinstance(a, list) and isinstance(b, list):
            if json.dumps(a) != json.dumps(b): out.append(pre + " (list changed)")
        elif a != b:
            out.append(pre + " (changed)")
        return out
    changes = diff(s6, s7)
    allowed = ("/pd/zone_defs/gnd_stitch_via", "/constraints/j2_escape_topology/outer_basis",
               "/layer_plan/in6_usage", "/layer_plan/strap_domain_v32/deps")
    unexpected = [c for c in changes if not any(c.startswith(a) for a in allowed)]
    OUT.write_text(json.dumps(s7, ensure_ascii=False, indent=1), encoding="utf-8")
    rec = {"artifact": "m13_v57_co73_layer_role_consistency", "schema": 1, "revision": "CO-73.1",
           "nature": "L2 PDN/层角色声明一致性终扫（rev-7）",
           "spec_rev6_sha16": src_sha, "spec_rev6_sha16_after": s16(SRC), "spec_rev7_sha16": s16(OUT),
           "changed_keys": changes, "unexpected_changes": unexpected,
           "gnd_stitch_plane_text_fixed": {"before_In1/3/5": n_before, "after": n_after},
           "geometry_invariance_expected": True,
           "redline": "原件未动；零几何/阈值；历史件不触碰。"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"spec_rev7_sha16": s16(OUT), "rev6_unchanged": src_sha == s16(SRC),
                      "changed_keys": changes, "unexpected": unexpected,
                      "gnd_stitch_fixed": n_before}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
