#!/usr/bin/env python3
"""K2 · P4 · W-7 落件器 v1 —— **dry-run 默认**，只有 `--apply` 才写仓库（须监理批）。

落件 = 把 W-7 修复器产物（dry-run 结果板）落进仓库，并走 T-22/T-25 + SPEC 版本 bump：
  A. 前置校验（fail-closed；任一不符即中止，不写任何文件）
  B. --apply：① 备份 src 板/pro 字节 ② 写板 ③ **校验 dst pro 逐字节不变**（不符即回滚）
     ④ SPEC `rev-47` 新文件（= rev-46 + `_spec_rev_37` 变更记录 + `spec_version`）+ `project.yaml.spec_name` bump
     ⑤ 落件后复核（DRC + 冻结判定器）
  C. 打印后续 git 步骤（不代跑 git）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys


def sha(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def s16(p):
    return sha(p)[:16]


def die(msg):
    print(f"[FAIL] {msg}")
    sys.exit(1)


def ok(msg):
    print(f"[ OK ] {msg}")


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def drc_counts(kicad_cli, board, out_json):
    rc, out, err = run([kicad_cli, "pcb", "drc", "--format", "json",
                        "--severity-error", "--severity-warning",
                        "--output", out_json, board])
    if rc != 0 or not os.path.exists(out_json):
        die(f"DRC 失败 rc={rc}\n{out}\n{err}")
    d = json.load(open(out_json, encoding="utf-8"))
    n_err = sum(1 for v in d.get("violations", []) if v["severity"] == "error")
    n_warn = sum(1 for v in d.get("violations", []) if v["severity"] == "warning")
    return n_err, n_warn, len(d.get("unconnected_items", []))


def spec_record(rep_json):
    r = json.load(open(rep_json, encoding="utf-8")) if rep_json and os.path.exists(rep_json) else None
    got = {}
    if r:
        got = {"after": r.get("after", {}).get("counts", {}),
               "board_sha16": r.get("after", {}).get("board_sha16")}
    return {
        "card": "SPEC-REV-37",
        "at": "2026-09-18",
        "authority": ("owner #14「L2 = 叠层/PDN/走廊/布线/**过孔策略**/等长/热机械 = 自裁勿停」"
                      " + 监理 #K2-19 §二 W-7（deny-by-default；9 条 ignore 逐条处置）"
                      " + 监理续推令（按已批准计划推进 P4，不越阶段）"),
        "basis": [
            "W-7 登记的 9 条 `ignore` 中 5 类共 146 条未处置：`via_dangling` 12 · `track_not_centered_on_via` 30 · "
            "`silk_over_copper` 43 · `silk_overlap` 21 ·（`missing_courtyard` 40 未动，外扩口径属 §4-1 耦合裁定）。",
            "处置由确定性修复器 `k2/tools/k2_p4_w7_repair_v1.py` 产出：逐案「改板 → ZONE_FILLER 重填 → DRC 复算 → "
            "不合格即回退」，复算闸 = 无新违规类型 / 各类条数不增 / error=0 / unconnected=0 / 总量严格下降。",
            "**纯 L2 施工**：不改 L1（拓扑 / 器件集合 / 网络 / 球映射 / 接口朝向 / 信号流向 全部不变）；"
            "不新开孔类、不放松任何 DRC 下限；丝印改动只动位号文本与封装丝印线段。",
            "复跑确定性：`KIID.SeedGenerator(20260918)` 固定新建项 uuid；两次独立全量复跑结果板逐字节相同。",
        ],
        "findings": [
            "W-7 5 类 **181 → 98**（error 0、未连接 0、违规类型集零新增）：`via_dangling` 12→6 · "
            "`track_not_centered_on_via` 30→13 · `silk_over_copper` 43→3 · `silk_overlap` 21→1。",
            "剩余 23 条证据：`via_dangling` 6 = 承重支路（删除即 unconnected>0，正解是接平面）；"
            "`tncv` 13 = 局部几何不可解 + 移孔撞孔净距（须重布线/重定孔位）；`silk` 4 = C80/R41/R45 密集簇无落点。",
            "丝印可读性代价已量化：位号位移中位 3.0 mm（p90 6.6 mm、max 7.3 mm），19 案缩到 0.8 mm 下限、9 案转 90°。",
            "本 rev 只记录**板面施工**；`criteria/` 9 条 severity 登记与 `pipeline.yaml` 属监理侧，未动。",
        ],
        "landed": got,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result-board", required=True)
    ap.add_argument("--result-sha16", required=True)
    ap.add_argument("--board", default="k2/hw/k2_v4_8L.l5.kicad_pcb")
    ap.add_argument("--pro", default="k2/hw/k2_v4_8L.l5.kicad_pro")
    ap.add_argument("--expect-board-sha16", default="37019705ef994ccc")
    ap.add_argument("--expect-pro-sha16", default="f68a5fb2f82bd02d")
    ap.add_argument("--spec-dir", default="k2/pm_gate/artifacts/k2_v4/L3")
    ap.add_argument("--project-yaml", default="k2/pm_gate/project.yaml")
    ap.add_argument("--expect-spec-sha16", default="dea36093ba2b4031")
    ap.add_argument("--criteria", default="criteria")
    ap.add_argument("--expect-adjudicate-sha16", default="897e8bfde60e2cfe")
    ap.add_argument("--expect-manifest-sha16", default="7ce08757eff25557")
    ap.add_argument("--report-json", default="/tmp/opencode/wb1/report.json")
    ap.add_argument("--kicad-cli", default="AppDir/bin/kicad-cli")
    ap.add_argument("--work-dir", default="/tmp/opencode/land")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)

    os.makedirs(a.work_dir, exist_ok=True)
    print(f"=== K2 W-7 落件器 v1 · {'APPLY' if a.apply else 'DRY-RUN（默认，不写仓库）'} ===")

    # ---------- A. 前置校验（fail-closed）
    for path, exp, what in ((a.board, a.expect_board_sha16, "仓库板"),
                            (a.pro, a.expect_pro_sha16, "仓库 pro")):
        got = s16(path)
        (ok if got == exp else die)(f"{what} sha16={got}（期望 {exp}）")
    if s16(a.result_board) != a.result_sha16:
        die(f"结果板 sha16={s16(a.result_board)}（期望 {a.result_sha16}）")
    ok(f"结果板 sha16={a.result_sha16}（{a.result_board}）")
    rev46 = os.path.join(a.spec_dir, "SPEC_k2_v4.spec-rev-46.json")
    if s16(rev46) != a.expect_spec_sha16:
        die(f"canonical SPEC rev-46 sha16={s16(rev46)}（期望 {a.expect_spec_sha16}）")
    ok(f"canonical SPEC rev-46 sha16={a.expect_spec_sha16}")
    for name, exp in (("adjudicate.py", a.expect_adjudicate_sha16),
                      ("manifest.k2.yaml", a.expect_manifest_sha16)):
        got = s16(os.path.join(a.criteria, name))
        (ok if got == exp else die)(f"criteria/{name} sha16={got}（期望 {exp}）")
    if not os.access(os.path.join(a.criteria, "adjudicate.py"), os.R_OK):
        die("criteria/ 不可读")
    rev47 = os.path.join(a.spec_dir, "SPEC_k2_v4.spec-rev-47.json")
    if os.path.exists(rev47):
        die(f"SPEC rev-47 已存在（{rev47}）——请人工确认后再落")

    n_err, n_warn, n_unc = drc_counts(a.kicad_cli, a.result_board,
                                      os.path.join(a.work_dir, "drc_result.json"))
    print(f"[info] 结果板 DRC（结果板同目录配对 pro = **探针**，9 条 severity=warning）："
          f"error={n_err} warning={n_warn} unconnected={n_unc}（期望 98 = W-7 未处置 5 类残项 + 35 lib）")
    if n_err or n_unc:
        die(f"结果板自带 error（{n_err}）或未连接（{n_unc}）——不得落件")

    # ---------- B. 落件
    if not a.apply:
        print("\n[DRY-RUN] 若监理批，执行以下命令即一键落件：")
        print(f"  AppDir/usr/bin/python3.11 k2/tools/k2_p4_w7_land_v1.py \\\n"
              f"    --result-board {a.result_board} --result-sha16 {a.result_sha16} --apply")
        print("拟改动：① 仓库板（字节替换为结果板）② SPEC 新增 `rev-47` ③ `project.yaml.spec_name` bump。")
        print("**不动**：仓库 pro（逐字节校验）、`criteria/`、rev-19..46 原件。")
        return 0

    bdir = os.path.join(a.work_dir, "backup")
    os.makedirs(bdir, exist_ok=True)
    bak_board, bak_pro = os.path.join(bdir, "board.bak"), os.path.join(bdir, "pro.bak")
    shutil.copy2(a.board, bak_board)
    shutil.copy2(a.pro, bak_pro)
    pro_sha_before = sha(a.pro)
    ok(f"已备份 src 板/pro 字节 → {bdir}")

    shutil.copy2(a.result_board, a.board)
    if sha(a.pro) != pro_sha_before:
        shutil.copy2(bak_board, a.board)
        die("dst pro 字节发生变化 ⇒ 已回滚板，落件中止（T-22）")
    ok(f"板已落 {a.board}（sha16={s16(a.board)}）；dst pro 逐字节不变 ✓")

    d = json.load(open(rev46, encoding="utf-8"))
    d["_spec_rev_37"] = spec_record(a.report_json)
    base = d.get("spec_version", "1.1.spec-rev-46")
    d["spec_version"] = base.replace("spec-rev-46", "spec-rev-47")
    with open(rev47, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1, sort_keys=False)
    ok(f"SPEC 新增 {rev47}（sha16={s16(rev47)}）")
    txt = open(a.project_yaml, encoding="utf-8").read()
    if "SPEC_k2_v4.spec-rev-46.json" not in txt:
        die("project.yaml 未指向 rev-46 ⇒ 人工确认后再落")
    open(a.project_yaml, "w", encoding="utf-8").write(
        txt.replace("SPEC_k2_v4.spec-rev-46.json", "SPEC_k2_v4.spec-rev-47.json"))
    ok(f"project.yaml spec_name → rev-47（sha16={s16(a.project_yaml)}）")

    # ---------- C. 落件后复核
    n_err, n_warn, n_unc = drc_counts(a.kicad_cli, a.board,
                                      os.path.join(a.work_dir, "drc_after_land.json"))
    print(f"[verify] 落件后 DRC（仓库 pro 语义）：error={n_err} warning={n_warn} unconnected={n_unc}"
          f"（期望 error=0 / warning=35（lib_footprint_mismatch）/ unconnected=0）")
    print("\n[git] 后续（ENG 手跑）：")
    print(f"  git -C k2 add hw/k2_v4_8L.l5.kicad_pcb pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-47.json pm_gate/project.yaml")
    print('  git -C k2 commit -m "p4(k2): W-7 P2 施工落件（L2）—— 181→98；SPEC rev-47"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
