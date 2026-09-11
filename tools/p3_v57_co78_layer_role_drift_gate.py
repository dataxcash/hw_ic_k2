#!/usr/bin/env python3
"""CO-78：【L2 声明一致性 · 回归闸】层角色漂移（layer-role drift）机判闸。

把 CO-76 F1 / CO-72 / CO-73 的缺陷类固化为**可重复回归闸**：
  在**当前态**工件中，任何把「平面层」当信号层、或把「信号层」当平面层的**角色声明**都判 FAIL。
  LID REV6 口径：signal = F/In2/In5/B；plane = In1/In3/In6(GND) + In4(P3V3)。

豁免（显式、按 JSON 路径或字符串标记）：历史/provenance/已退役几何/既往裁决原文/更正说明
（`_spec_rev_*` / `supersedes` / `retired_*` / `ecn_pending_items` / `ruled*` / `appendix` / `rollback` /
 「更正」「已失效」「原 」「PROHIBITED」「禁止」「不得」）。

用法：python3 tools/p3_v57_co78_layer_role_drift_gate.py [--control-historical PATH]
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
STEP2 = L3 / "mcio_feas_step2"
OUT = STEP2 / "m13_v57_co78_layer_role_drift_gate.json"
ENGINE = K2 / "tools/p3_v57_w3_constructive.py"

SIGNAL = {"F.Cu", "In2.Cu", "In5.Cu", "B.Cu"}
PLANE = {"In1.Cu", "In3.Cu", "In6.Cu"}          # GND
POWER = {"In4.Cu"}                               # P3V3
SIG_WORDS = re.compile(r"lane|stub|escape|river|transition_eligible|信号层|通道|走线带|槽")
PLANE_WORDS = re.compile(r"GND|gnd|平面|plane|参考|reference|pour|铜皮")
EXEMPT_PATH = re.compile(r"_spec_rev|supersed|retired|ecn_pending|ruled|appendix|rollback|provenance")
EXEMPT_TEXT = re.compile(r"更正|已失效|原 |禁止|不得|PROHIBITED|历史")

CUR_INPUTS = [L3 / "SPEC_k2_v4.json", L3 / "SPEC_k2_v4.spec-rev-8.json",
              L2 / "route_model_config.json",
              STEP2 / "m13_v57_layer_intent_rev6.json",
              STEP2 / "m13_v57_big_w0r_corridor_model.json",
              STEP2 / "m13_v57_co16_channel_allocation_v7.json",
              STEP2 / "m13_v57_co37_escape_domain.json",
              STEP2 / "m13_v57_s1_page_manifest.json"]
CUR_OUTPUTS = [STEP2 / n for n in (
    "m13_v57_w3_joint_assignment.json", "m13_v57_w3_chip_landing_rows.json",
    "m13_v57_w3_validation.json", "m13_v57_l4_construction.json",
    "m13_v57_l4_validation.json", "m13_v57_l5_fab_record.json",
    "m13_v57_l5_dfm_dft_record.json", "m13_v57_l5_si_pi_emc_record.json")]
CONTROL = STEP2 / "SPEC_k2_v4_8L_LID1.json"      # 历史对照（LID.1 下 In6 = 信号层）


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def scan_json(path: Path) -> list:
    doc = json.loads(path.read_text(encoding="utf-8"))
    flags = []

    def classify(text, path, flags):
        if EXEMPT_PATH.search(path) or EXEMPT_TEXT.search(text):
            return
        for lyr, role in [(l, "plane") for l in PLANE | POWER] + [(l, "signal") for l in SIGNAL]:
            if lyr not in text:
                continue
            if role == "plane" and SIG_WORDS.search(text) and not PLANE_WORDS.search(text):
                flags.append({"path": path, "layer": lyr, "claim": "plane-as-signal", "text": text[:160]})
            if role == "signal" and PLANE_WORDS.search(text) and not SIG_WORDS.search(text) \
                    and re.search(r"layers?|层|Cu\\b|plane", text):
                flags.append({"path": path, "layer": lyr, "claim": "signal-as-plane", "text": text[:160]})

    def walk(o, p=""):
        if isinstance(o, dict):
            for k, v in o.items():
                # 角色声明常编码为 key->value（如 {"In6.Cu": "transition_eligible"}）：
                if isinstance(v, str) and "Cu" in str(k):
                    classify("K:%s V:%s" % (k, v), p + "/" + str(k), flags)
                elif "In" in str(k) and isinstance(v, (str, int, float, bool)):
                    classify("%s=%s" % (k, v), p + "/" + str(k), flags)
                walk(v, p + "/" + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, p + "[" + str(i) + "]")
        elif isinstance(o, str) and "In" in o:
            classify(o, p, flags)
    walk(doc)
    return flags


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--control-historical", default=str(CONTROL))
    a = ap.parse_args(argv)
    files = CUR_INPUTS + CUR_OUTPUTS + [ENGINE]
    per, total = {}, []
    for f in files:
        if not Path(f).exists():
            per[str(Path(f).name)] = {"missing": True}
            continue
        if Path(f).suffix == ".json":
            fl = scan_json(f)
        else:  # 引擎源码：裸 token 扫描（In6 仅允许出现在 In6->In5 迁移注）
            fl = [{"path": "L%d" % (i + 1), "layer": "In6.Cu", "claim": "engine-bare-In6",
                   "text": ln.strip()[:160]}
                  for i, ln in enumerate(Path(f).read_text(encoding="utf-8").splitlines())
                  if "In6" in ln and "In6->In5" not in ln]
        per[Path(f).name] = {"sha16": s16(f), "flags": fl}
        total += fl
    # 对照（历史件）必须被抓到 —— 证明闸有齿
    ctl = Path(a.control_historical)
    ctl_flags = scan_json(ctl) if ctl.exists() else []
    rec = {"artifact": "m13_v57_co78_layer_role_drift_gate", "schema": 1, "revision": "CO-78.1",
           "nature": "L2 层角色漂移回归闸（当前态工件）",
           "policy": {"signal": sorted(SIGNAL), "gnd_plane": sorted(PLANE), "power": sorted(POWER)},
           "scope": [str(f) for f in files], "per_file": per,
           "total_flags": len(total), "flags": total,
           "control_historical": {"file": str(ctl), "n_flags": len(ctl_flags),
                                  "detected": len(ctl_flags) > 0},
           "verdict": "PASS" if not total else "FAIL",
           "teeth": "对照历史件（LID.1 下 In6=信号层）应被抓到；否则闸无效",
           "redline": "只读；不改工件；零几何/阈值改动。"}
    rec["teeth_ok"] = rec["control_historical"]["detected"]
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"], "total_flags": len(total),
                      "tooth_control_detected": rec["teeth_ok"],
                      "control_flags": len(ctl_flags), "record": s16(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
