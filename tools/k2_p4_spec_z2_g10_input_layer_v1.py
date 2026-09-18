#!/usr/bin/env python3
"""K2 · P4 · **写入 Z2/G10 输入层 + 版本 bump**（`keepout_geometry` / `pd.zone_defs.board_realized_zones` / `mounting_holes`）。

依据：监理 **#K2-23 §二-4**（Z2：18 zone + 4 NPTH 落件）+ §二-1（Z4 权威源＝整族刷新至 P4 真值）
+ 一次投递包 `K2-P4-Z4-Z2-ONE-SHOT-DELIVERY-v1.md` **§5 Step 2**。

数据源：合并输入块 `p4_g10_input_block_merged.json`（schema `k2-p4-g10-input-block/v1`，`board_sha16` 须 == 受审板）
—— 内容＝受审板**实测**；口径＝监理 **「以板为准」**（#K2-23 §二-4）。**逐条 verbatim 转写，不做任何变换**。

本器只做（**不写板/库/pro**）：
  ① `keepout_geometry`（含 8 keepout 区 + KO-7 处置登记）；
  ② `pd.zone_defs.board_realized_zones`（10 有网铜区）；
  ③ `mounting_holes`（4 NPTH：逐座标 + Ø3.2 + keepout 6.00×6.00 + edge_material）；
  ④ 新增 `_spec_rev_<new-rev>` 记账卡 + `spec_version` bump；同步 `project.yaml::spec_name`。

纪律：**T-22**（先备份 + 落改后校验旧 rev 逐字节未变）· **T-41**（`--apply` 须 `--confirm-repo-write`）·
**rev-N 原件永不改** · dry-run 自带 `--work-dir` 预览 · **确定性**（同输入同输出）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys

EXPECT = {"zones": 18, "keepout": 8, "copper": 10, "npth": 4}


def sha16(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec-base", required=True)
    ap.add_argument("--spec-new", required=True)
    ap.add_argument("--input-block", required=True)
    ap.add_argument("--project-yaml", required=True)
    ap.add_argument("--board", default="k2/hw/k2_v4_8L.l5.kicad_pcb")
    ap.add_argument("--new-rev", type=int, required=True)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--confirm-repo-write", action="store_true")
    a = ap.parse_args()

    base_name, new_name = os.path.basename(a.spec_base), os.path.basename(a.spec_new)
    S = json.load(open(a.spec_base, encoding="utf-8"))
    B = json.load(open(a.input_block, encoding="utf-8"))

    # ── fail-closed 前置 ──
    key = "_spec_rev_%d" % a.new_rev
    if key in S:
        print("REFUSE: %s 已存在于 base" % key, file=sys.stderr); return 2
    sv_old = S.get("spec_version", "")
    if sv_old != "1.1.spec-rev-%d" % (a.new_rev - 1):
        print("REFUSE: spec_version=%r 非预期" % sv_old, file=sys.stderr); return 2
    if B.get("schema") != "k2-p4-g10-input-block/v1":
        print("REFUSE: 输入块 schema=%r 非预期" % B.get("schema"), file=sys.stderr); return 2
    board_sha = sha16(a.board)
    if B.get("board_sha16") != board_sha:
        print("REFUSE: 输入块 board_sha16=%s != 受审板 %s（陈旧即 fail-closed）"
              % (B.get("board_sha16"), board_sha), file=sys.stderr); return 2
    c = B.get("counts") or {}
    if {k: c.get(k) for k in EXPECT} != EXPECT:
        print("REFUSE: counts=%r != %r" % (c, EXPECT), file=sys.stderr); return 2
    zones = B["g10_zones"]
    ko = [z for z in zones if z.get("net") is None]
    cu = [z for z in zones if z.get("net") is not None]
    if not (len(zones) == 18 and len(ko) == 8 and len(cu) == 10):
        print("REFUSE: zones 拆分异常 %d/%d/%d" % (len(zones), len(ko), len(cu)), file=sys.stderr); return 2
    for guard in ("keepout_geometry", "mounting_holes"):
        if guard in S:
            print("REFUSE: %s 已存在（勿覆盖）" % guard, file=sys.stderr); return 2
    if "board_realized_zones" in (S.get("pd", {}).get("zone_defs") or {}):
        print("REFUSE: pd.zone_defs.board_realized_zones 已存在", file=sys.stderr); return 2

    prov = ("受审板实测（board_sha16=%s）+ 监理 #K2-23 §二-4「以板为准」裁定 + §二-1 Z4 权威源"
            "（真源 → SPEC → 板；板为本文输入层的实测来源）" % board_sha)

    # ── 写入（verbatim 转写，零变换）──
    S["keepout_geometry"] = {
        "basis": prov,
        "board_sha16": board_sha,
        "count": len(ko),
        "ko7_disposition": {
            "board_has_standalone_zone": False,
            "carried_by_rule": "min_copper_edge_clearance=0.3",
            "action": "不补实体 zone",
            "reason": "板无 KO-7 独立实体 zone；由规则承载（inc61 §3 建议，#K2-23 §二-4 口径确认）",
        },
        "zones": ko,
    }
    S.setdefault("pd", {}).setdefault("zone_defs", {})["board_realized_zones"] = {
        "basis": prov, "board_sha16": board_sha, "count": len(cu), "zones": cu,
    }
    S["mounting_holes"] = {
        "basis": prov, "board_sha16": board_sha, "count": len(B["g10_npth"]),
        "np_thru_hole": {"drill_mm": 3.2, "size_mm": 3.2, "layers": ["*.Cu", "*.Mask"]},
        "holes": B["g10_npth"],
    }
    S[key] = {
        "card": "SPEC-REV-%d（Z2/G10 输入层）" % a.new_rev,
        "at": "2026-09-18",
        "authority": ("监理 #K2-23 §二-4（Z2：18 zone + 4 NPTH 落件，回归 18/0 与 4/0 PASS、"
                      "KiCad 级 roundtrip 4/4、确定性）+ §二-1（Z4 权威源＝整族刷新至 P4 真值）"),
        "basis": [
            "写入 Z2/G10 **输入层**（一次投递包 §5 Step 2）：`keepout_geometry`（8 keepout 区 + KO-7 处置）·"
            " `pd.zone_defs.board_realized_zones`（10 有网铜区）· `mounting_holes`（4 NPTH）。",
            "数据源＝合并输入块 `p4_g10_input_block_merged.json`（schema v1，子块 `zones_input.json` / `npth_input.json`）；"
            "**逐条 verbatim 转写，零变换**；输入块 `board_sha16` 与受审板一致性由本器 fail-closed 断言。",
            "口径（#K2-23 §二-4／一次投递包 §4.2，全部取受审板实测）：孔 keepout 4 区＝全 8 层 · 6.00×6.00 ·"
            " 精确居中于孔心 · tracks/vias/copperpour not_allowed、pads/footprints allowed（图纸 `KO-1..4` 五开关全 blocked ⇒ 口径差，已在此以板为准）；"
            "ESC keepout 4 区＝F.Cu · copperpour not_allowed（图纸 `KO-5/6` 枚举陈旧）；"
            "有网铜区 10＝In1/In3/In6 GND + In4{12V_IN×2, P3V3_AUX×2, P3V3×2, MCU_VDD×1}（板 10/10 全填充）；"
            "NPTH 4＝H1(26.10,75.60) H2(139.60,39.60) H3(45.10,75.10) H4(114.60,36.10)，Ø3.2，通配层写法 `*.Cu`/`*.Mask`。",
            "KO-7：板**无**独立实体 zone（由规则 `min_copper_edge_clearance=0.3` 承载）⇒ **不补实体 zone**（具名登记，见 `keepout_geometry.ko7_disposition`）。",
            "本 rev **只写输入层**：生成器**尚未**消费（Step 3 才改生成器）；不改板/库/pro/criteria/真源；rev-%d 原件逐字节不变。"
            % (a.new_rev - 1),
            "**C1（`PWR_5V_KEY`/`layer_plan.low_speed_nets`）不属本 rev**（待 ⑤ owner）。",
        ],
        "board_sha16": board_sha,
    }
    S["spec_version"] = sv_old.replace("spec-rev-%d" % (a.new_rev - 1), "spec-rev-%d" % a.new_rev)

    os.makedirs(a.work_dir, exist_ok=True)
    preview = os.path.join(a.work_dir, new_name)
    with open(preview, "w", encoding="utf-8") as fh:
        json.dump(S, fh, ensure_ascii=False, indent=1, sort_keys=False)
    print("[plan] keepout_geometry.zones=%d · pd.zone_defs.board_realized_zones=%d · mounting_holes=%d"
          % (len(ko), len(cu), len(B["g10_npth"])))
    print("[plan] spec_version: %s → %s ; 新增 %s" % (sv_old, S["spec_version"], key))
    print("[preview] %s (sha16 %s)" % (preview, sha16(preview)))
    if not a.apply:
        print("\n[DRY-RUN] 批准后执行：追加 --apply --confirm-repo-write")
        return 0
    if not a.confirm_repo_write:
        print("REFUSE: --apply 需 --confirm-repo-write（T-41）", file=sys.stderr); return 2

    bdir = os.path.join(a.work_dir, "backup")
    os.makedirs(bdir, exist_ok=True)
    shutil.copy2(a.spec_base, os.path.join(bdir, base_name))
    shutil.copy2(a.project_yaml, os.path.join(bdir, os.path.basename(a.project_yaml)))
    base_sha_before = sha16(a.spec_base)
    ytxt = open(a.project_yaml, encoding="utf-8").read()
    if base_name not in ytxt:
        print("REFUSE: project.yaml 未含 %s" % base_name, file=sys.stderr); return 2
    shutil.copy2(preview, a.spec_new)
    open(a.project_yaml, "w", encoding="utf-8").write(ytxt.replace(base_name, new_name))
    if sha16(a.spec_base) != base_sha_before:
        raise RuntimeError("旧 rev 被改动 ⇒ 中止（T-22）")
    print("[apply] %s sha16=%s" % (new_name, sha16(a.spec_new)))
    print("[apply] %s sha16=%s" % (os.path.basename(a.project_yaml), sha16(a.project_yaml)))
    print("[apply] 旧 rev 未变：%s %s ✓" % (base_name, base_sha_before))
    return 0


if __name__ == "__main__":
    sys.exit(main())
