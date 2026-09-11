#!/usr/bin/env python3
"""CO-37：从域工件发射 KiCad 自定义规则文件 `k2_v4_8L.l4.kicad_dru`（版件，L2 自裁）。

规则内容 = SPEC `escape_transition_zone`（ECN-001, 0.075）在域内生效；**REFCLK 网不适用**
（SPEC.constraints.refclk_isolated=true）。域外维持 board/netclass 判据（PCIe85 0.175 / POWER 0.2）。
零搜索：域与排除项全部来自版本化工件（`m13_v57_co37_escape_domain.json`）。
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
DOMAIN = STEP2 / "m13_v57_co37_escape_domain.json"
OUT = K2 / "k2_v4_8L.l4.kicad_dru"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    d = json.loads(DOMAIN.read_text(encoding="utf-8"))
    ids = [x["id"] for x in d["domains"]]
    layer = d["domains"][0]["layer"]
    inz = " || ".join([f"A.intersectsArea('{i}')" for i in ids] + [f"B.intersectsArea('{i}')" for i in ids])
    excl = " && ".join([f"!(A.NetName == '{p}')" for p in d.get("excluded_nets", [])]
                       + [f"!(B.NetName == '{p}')" for p in d.get("excluded_nets", [])])
    cond = f"({inz})" + (f" && {excl}" if excl else "")
    body = (
        "(version 1)\n\n"
        "# CO-37 / L2 自裁：实现 SPEC constraints.escape_transition_zone（ECN-001，escape_clearance_mm=0.075）。\n"
        f"# 域：{'/'.join(ids)}（pad 场矩形，F.Cu，per_pin_vertical_escape + no_via）；域外维持 shop/netclass 判据。\n"
        f"# 排除：REFCLK 网（SPEC.constraints.refclk_isolated=true）⇒ 其冲突属几何缺陷（D3a），不享受逃逸区放宽。\n"
        f"# 域工件：{DOMAIN.name} sha256={sha256(DOMAIN)}\n\n"
        f"(rule \"SPEC escape_transition_zone 0.075 (ECN-001) [{d['revision']}]\"\n"
        f"\t(layer \"{layer}\")\n"
        f"\t(constraint clearance (min {d['escape_clearance_mm']}mm) )\n"
        f"\t(condition \"{cond}\")\n"
        ")\n"
    )
    OUT.write_text(body, encoding="utf-8")
    print(f"{OUT.name}: domains={len(ids)} sha16={sha256(OUT)[:16]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
