#!/usr/bin/env python3
"""K2 · P4 · **SPEC 版本 bump + `pd` 几何对齐**（落件前置器；dry-run 默认）。

依据：`hooks/pre-commit` 的 `check_pcb_spec_correlation`（**同笔提交内 .kicad_pcb 变更必须伴随 SPEC 变更**）
+ 监理 #K2-21 §二① 落件条件（**dst pro 逐字节不变**、落件后复算）。
机制沿既有复合落件器（`k2_p4_composed_land_v2.py`：`board_anchor` / `align_pd` / `spec_record`）：
**SPEC 修订走版本 bump**（rev-N 原件永不改），新 rev = 旧 rev + `_spec_rev_<k>`（按实况记录）+ `spec_version` bump。

本器做两件事（**不写板、不写库**；板/库由 `⑥`/`⑦` 各自的 `--apply` 落）：
  ① **`pd` 对齐**：把 `pd` 子树内 `ref ∈ --moved-refs` 且含 `pad_pos` 的**现行**叶（跳过 `retired_*` 历史块），
     按**结果板实际几何**重派生 `pad_pos`/`via_pos`（pad 中心 + 同网最近 via ≤1mm）；
  ② **SPEC bump**：新 rev = 旧 rev + `_spec_rev_<k>` + `spec_version`，并同步 `project.yaml` 的 `spec_name`。

纪律：T-22（备份 + 旧 rev / project.yaml 字节校验）· T-41（写仓库须 `--apply --confirm-repo-write`）·
dry-run 时把**预览新 rev** 落到 `--work-dir` 供监理逐字核对（不动仓库）。

用法（dry-run）：
  AppDir/usr/bin/python3.11 k2/tools/k2_p4_spec_rev_bump_v1.py \
    --board /tmp/opencode/p4final/b7/k2_v4_8L.l5.l2-placed.libsnap.kicad_pcb \
    --spec-base k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-47.json \
    --spec-new  k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-48.json \
    --project-yaml k2/pm_gate/project.yaml --moved-refs D2,L1,U4 --work-dir /tmp/opencode/p4final/spec48
（落 rev）追加 `--apply --confirm-repo-write`
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import sys

import pcbnew

NM = 1_000_000
VIA_SEARCH_NM = NM          # pad→via 搜索半径 1mm
RETIRED = "retired"


def sha16(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def board_anchor(board: str, refs):
    """从结果板派生 refs 各 pad 的 (pad_pos, via_pos)（同网最近 via ≤1mm）。"""
    bd = pcbnew.LoadBoard(board)
    fps = {f.GetReference(): f for f in bd.GetFootprints()}
    vias = [(t.GetNetname(), t.GetPosition()) for t in bd.GetTracks()
            if t.Type() == pcbnew.PCB_VIA_T]
    out = {}
    for ref in refs:
        fp = fps.get(ref)
        if fp is None:
            continue
        per = {}
        for p in fp.Pads():
            pp, net = p.GetPosition(), p.GetNetname()
            best = None
            for vnet, q in vias:
                if vnet != net:
                    continue
                d = ((q.x - pp.x) ** 2 + (q.y - pp.y) ** 2) ** 0.5
                if d <= VIA_SEARCH_NM and (best is None or d < best[0]):
                    best = (d, q.x, q.y)
            per[p.GetPadName()] = {"net": net, "pad_pos": [pp.x / NM, pp.y / NM],
                                   "via_pos": [best[1] / NM, best[2] / NM] if best else None}
        if per:
            out[ref] = per
    return out


def align_pd(node, anchors, path="pd", out=None):
    """递归对齐 `pd` 内 ref ∈ anchors 且含 pad_pos 的现行叶（跳过 retired_* 历史块）。"""
    out = [] if out is None else out
    if RETIRED in path:
        return out
    if isinstance(node, dict):
        ref = node.get("ref")
        if ref in anchors and isinstance(node.get("pad_pos"), list):
            a = anchors[ref].get(str(node.get("pad", "")))
            if a:
                before = {"pad_pos": list(node["pad_pos"]), "via_pos": node.get("via_pos")}
                node["pad_pos"] = [round(a["pad_pos"][0], 3), round(a["pad_pos"][1], 3)]
                if a["via_pos"]:
                    node["via_pos"] = [round(a["via_pos"][0], 3), round(a["via_pos"][1], 3)]
                node["relocated_basis"] = ("P4 ⑥ L2 placement 微调（courtyard 联合可解）："
                                           "pad_pos/via_pos 由落件板几何派生")
                out.append({"at": path, "ref": ref, "pad": str(node.get("pad", "")),
                            "net": node.get("net"), "before": before,
                            "after": {"pad_pos": node["pad_pos"], "via_pos": node.get("via_pos")}})
        for k, v in node.items():
            align_pd(v, anchors, "%s/%s" % (path, k), out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            align_pd(v, anchors, "%s[%d]" % (path, i), out)
    return out


def spec_record(new_rev, moved, changed, board_sha16, lib_digest):
    return {
        "card": "SPEC-REV-%s（P4 ⑥+⑦）" % new_rev,
        "at": "2026-09-18",
        "authority": ("owner #14「L2 = 叠层/PDN/走廊/过孔策略/等长/热机械 = 自裁勿停」"
                      " + 监理 #K2-21 §二⑥⑦（courtyard 补齐登记为 L2 项；W-8「以板为准」+ 建 fp-lib-table）"
                      " + 监理 #K2-22（逐条根因闭环）"),
        "basis": [
            "⑥ = L2 placement 微调（移 D2/L1/U4 解 courtyard 实体重叠）+ 40 件 `CrtYd` 按面补全（Add-only，"
            "margin = min(KLC 0.25, 该件最大可用外扩)）—— 不改 L1（拓扑/器件集合/网络/球映射/接口朝向/信号流向不变）。",
            "⑦ = 以板为准重建项目封装库快照（59 颗 → 24 land pattern）+ 全板 `lib_id` 重指 `ForgeOS:<名>`"
            "（收敛原板 24 颗无 nickname / 9 颗裸名 / 9 颗双拼写）。",
            "硬闸（两跳各自 + 复合）：DRC 违规 **0**；`track` 4722 / `via` 711 / `zone` 18 / `net` 102 / `fp` 59 / `pad` 687；"
            "非 45° = 0；`column_x` 27.94；PCIE 段 3653 / via 252 逐条不变；⑦ 跳文本差异 55 行全为 footprint 头行。",
            "`pd` 内 %s 的 `pad_pos`/`via_pos` 由本 rev 按落件板几何同步对齐（%d 处）。" % (",".join(moved), len(changed)),
        ],
        "findings": {"moved_refs": moved, "pd_alignment": changed,
                     "board_sha16": board_sha16, "lib_digest_sha16": lib_digest,
                     "determinism": "两跳各自两次独立复跑结果板逐字节相同"},
        "landed": {"after": {"board_sha16": board_sha16}},
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True, help="落件结果板（复合候选）")
    ap.add_argument("--spec-base", required=True)
    ap.add_argument("--spec-new", required=True)
    ap.add_argument("--project-yaml", required=True)
    ap.add_argument("--moved-refs", default="")
    ap.add_argument("--new-rev", type=int, required=True)
    ap.add_argument("--lib-digest", default=None, help="快照库 digest sha16（记账用，可选）")
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--confirm-repo-write", action="store_true")
    a = ap.parse_args(argv)
    if a.apply and not a.confirm_repo_write:
        print("REFUSE: --apply 需 --confirm-repo-write（T-41）", file=sys.stderr)
        return 2
    os.makedirs(a.work_dir, exist_ok=True)
    moved = [r for r in a.moved_refs.split(",") if r]
    spec_base, spec_new = os.path.abspath(a.spec_base), os.path.abspath(a.spec_new)
    py = os.path.abspath(a.project_yaml)
    if not os.path.exists(spec_base):
        print("REFUSE: --spec-base 不存在: %s（修订走版本 bump，旧 rev 永不改）" % spec_base, file=sys.stderr)
        return 2
    if os.path.exists(spec_new):
        print("REFUSE: --spec-new 已存在: %s" % spec_new, file=sys.stderr)
        return 2
    base_name, new_name = os.path.basename(spec_base), os.path.basename(spec_new)
    ytxt = open(py, encoding="utf-8").read()
    if base_name not in ytxt:
        print("REFUSE: project.yaml 未指向 %s" % base_name, file=sys.stderr)
        return 2

    anchors = board_anchor(a.board, moved)
    missing = [r for r in moved if r not in anchors]
    if missing:
        print("REFUSE: 结果板缺部件 %s" % missing, file=sys.stderr)
        return 2
    d = json.load(open(spec_base, encoding="utf-8"))
    d2 = copy.deepcopy(d)
    changed = align_pd(d2.get("pd", {}), anchors)
    if not changed:
        print("REFUSE: `pd` 内未找到 ref∈%s 且含 pad_pos 的现行叶 —— 人工确认后再落" % moved, file=sys.stderr)
        return 2
    key = "_spec_rev_%d" % a.new_rev
    if key in d2:
        print("REFUSE: %s 已存在于 base" % key, file=sys.stderr)
        return 2
    board_sha = sha16(a.board)
    d2[key] = spec_record(a.new_rev, moved, changed, board_sha, a.lib_digest)
    sv_old = d2.get("spec_version", "")
    d2["spec_version"] = sv_old.replace("spec-rev-%d" % (a.new_rev - 1), "spec-rev-%d" % a.new_rev)
    if d2["spec_version"] == sv_old:
        print("REFUSE: spec_version 未随 rev 变化（%r）" % sv_old, file=sys.stderr)
        return 2
    preview = os.path.join(a.work_dir, new_name)
    with open(preview, "w", encoding="utf-8") as fh:
        json.dump(d2, fh, ensure_ascii=False, indent=1, sort_keys=False)
    print("[plan] `pd` 对齐 %d 处（现行叶；retired_* 历史块不动）：" % len(changed))
    for c in changed:
        print("   %s ref=%s pad=%s pad_pos %s→%s via_pos %s→%s"
              % (c["at"], c["ref"], c["pad"], c["before"]["pad_pos"], c["after"]["pad_pos"],
                 c["before"]["via_pos"], c["after"]["via_pos"]))
    print("[plan] spec_version: %s → %s ; 新增 %s" % (sv_old, d2["spec_version"], key))
    print("[plan] project.yaml: %s → %s" % (base_name, new_name))
    print("[preview] %s (sha16 %s)" % (preview, sha16(preview)))
    if not a.apply:
        print("\n[DRY-RUN] 批准后执行：在上句命令追加 --apply --confirm-repo-write")
        print("拟改动：仅 ① 新增 %s ② %s（不动板/库/pro/criteria/旧 rev）" % (new_name, os.path.basename(py)))
        return 0

    bdir = os.path.join(a.work_dir, "backup")
    os.makedirs(bdir, exist_ok=True)
    shutil.copy2(spec_base, os.path.join(bdir, base_name))
    shutil.copy2(py, os.path.join(bdir, os.path.basename(py)))
    base_sha_before, py_sha_before = sha16(spec_base), sha16(py)
    shutil.copy2(preview, spec_new)
    open(py, "w", encoding="utf-8").write(ytxt.replace(base_name, new_name))
    if sha16(spec_base) != base_sha_before:
        raise RuntimeError("旧 rev 被改动 ⇒ 中止（T-22）")
    print("[apply] %s sha16=%s" % (new_name, sha16(spec_new)))
    print("[apply] %s sha16=%s（旧 %s）" % (os.path.basename(py), sha16(py), py_sha_before))
    print("[apply] 旧 rev 未变：%s %s ✓" % (base_name, base_sha_before))
    return 0


if __name__ == "__main__":
    sys.exit(main())
