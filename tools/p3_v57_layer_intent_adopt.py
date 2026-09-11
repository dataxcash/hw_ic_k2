#!/usr/bin/env python3
"""层意图派生结果的**采用/版本化**（整改 #03 的落地步；机械版本 bump，非决策闸口）。

输入：冻结四源 + m13_v57_layer_intent_derived_v1.json（LID.1, 派生层意图）。
输出（新文件，原件不动）：
  - SPEC_k2_v4_8L_LID1.json  : SPEC 的**版本化 stackup/pd 修订件**（8L：In2+In6 信号层；In1/In3/In5 GND；In4 P3V3）
  - <--out>                  : 采用记录（含闭合验证 + 消费契约；engine 下一步据此改 layer palette）
纪律：不改冻结四源原件；零搜索（只读/写 + 闭式校验）。
"""
from __future__ import annotations
import argparse, copy, hashlib, json
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3"; S2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.json"; DERIVED = S2 / "m13_v57_layer_intent_derived_v1.json"
EXPECT_SPEC = "0bd52ed48e720b8c"


def sha16(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""): h.update(b)
    return h.hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--spec-out", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    spec_sha = sha16(SPEC)
    if spec_sha != EXPECT_SPEC:
        print("FROZEN_DRIFT spec", spec_sha); return 2
    spec = json.loads(SPEC.read_text()); der = json.loads(DERIVED.read_text())
    if der.get("verdict") != "DERIVED_STACKUP_REQUIRED":
        print("unexpected derived verdict", der.get("verdict")); return 3
    roles = {e["layer"]: e["role"] for e in der["derived_stackup"]["layer_purpose"]}
    sig = der["derived_stackup"]["signal_layers"]
    total = der["derived_stackup"]["total_layers"]

    spec2 = copy.deepcopy(spec)
    spec2["stackup"] = {**{k: {"signal" if v == "signal" else v: ""} and "" for k, v in roles.items()}}
    # 逐层写入语义（signal 层保留 F.Cu/In2/In6/B 的用途；平面层标注 GND/PWR）
    purpose = {"signal": "signal (PCIe + escape)", "GND": "GND_PLANE (full)", "PWR": "POWER_PLANE (P3V3)"}
    spec2["stackup"] = {k: purpose[v] for k, v in roles.items()}
    spec2["stackup"]["material"] = spec["stackup"]["material"]
    spec2["stackup"]["basis"] = "LID.1 capacity-closure derivation (rect #03); 8L derived, NOT owner parameter"
    spec2["pd"]["gnd_planes"] = [k for k, v in roles.items() if v == "GND"]
    spec2["pd"]["power_plane_layer"] = [k for k, v in roles.items() if v == "PWR"][0]
    spec2["_stackup_derivation"] = {"authority": "k2/tools/p3_v57_layer_intent_derive.py", "rev": "LID.1",
                                    "signal_layers": sig, "total_layers": total,
                                    "frozen_spec_sha16": spec_sha, "frozen_sources_untouched": True}
    Path(a.spec_out).write_text(json.dumps(spec2, ensure_ascii=False, indent=1, sort_keys=True))

    # 闭合/自洽校验
    ref_ok = all(roles[k] == "GND" for k in ("In1.Cu", "In3.Cu", "In5.Cu")) and roles["In4.Cu"] == "PWR"
    closure = der["closure"]
    rec = {
        "artifact": "m13_v57_layer_intent_adoption", "revision": "LID-ADOPT.1", "schema": 1, "date": "2026-09-11",
        "authority": "mechanical adoption of LID.1 derivation; no owner/work-order parameter",
        "inputs": {"spec_sha16": spec_sha, "derived_sha16": sha16(DERIVED)},
        "adopted_stackup": {"total_layers": total, "signal_layers": sig,
                            "layer_purpose": der["derived_stackup"]["layer_purpose"],
                            "reference_sandwich_ok": ref_ok,
                            "pd": {"gnd_planes": spec2["pd"]["gnd_planes"], "power_plane_layer": spec2["pd"]["power_plane_layer"]}},
        "spec_revision_written": str(Path(a.spec_out)),
        "original_spec_unchanged": sha16(SPEC) == spec_sha,
        "closure": closure,
        "self_consistent": bool(ref_ok and all(v["closed"] for v in closure["region_closure"].values())
                                and closure["same_layer_crossings"] == 0),
        "consumption_contract": {
            "layer_palette": sig,
            "chip_row_to_layer": der["derived_topology"]["chip_row_to_signal_layer"],
            "rule": "W3 引擎 palette[" + ",".join(sig) + "]；每 chip 逃逸行→独立信号层（L_escape=4 下 R1 逃逸列冲突消解）",
            "gate": "same-layer crossings == 0 ∧ D <= capacity (per region)"
        },
        "next_wave": ["W3 引擎消费本件（palette += In6）→ 重跑 W3 under 完整净距", "W4/L4/L5 重签 G7"],
    }
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True))
    print(json.dumps({"self_consistent": rec["self_consistent"], "adopted": rec["adopted_stackup"],
                      "spec_out": rec["spec_revision_written"]}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
