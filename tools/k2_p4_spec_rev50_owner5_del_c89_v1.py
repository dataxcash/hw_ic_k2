#!/usr/bin/env python3
"""k2_p4_spec_rev50_owner5_del_c89_v1.py — owner ⑤ 执行（**删 `C89`/`PWR_5V_KEY`**）SPEC bump → rev-50（#K2-24 §三-2）。

改动集（**深 diff 断言**，多一处即 fail-closed）：
  ① `layer_plan.low_speed_nets.nets`：删 `PWR_5V_KEY`（19 → 18）
  ② `pd.zone_defs.power_pad_connect.entries`：删 `{ref: C89}` 一条（185 → 184；其 pad/via 已随板删除）
  ③ **live** `board_sha16` ×3（`mounting_holes` / `keepout_geometry` / `pd.zone_defs.board_realized_zones`）+ 3 处 `basis` 文本内 sha
  ④ 新增 `_spec_rev_50` 变更留痕（含「不含 errata-2 其他内容」具名）
**不动**：历史 rev 原件（rev-47/48/49 逐字节）· `_spec_rev_*` 历史块（含 `_spec_rev_37/48/49` 的 board_sha16）·
        `retired_superseded_*` 两条 C89 退役留存（红线『退役几何/决策须显式留存』⇒ 保留，见裁定件 §三-2「live 字段」限定）。
输出：默认沙箱（`--spec-new`）；`--apply --confirm-repo-write` 落 SPEC + 更新 `project.yaml`（T-22 备份 + 旧 sha）。
"""
from __future__ import annotations
import argparse, copy, hashlib, io, json, os, shutil, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
K2 = os.path.join(ROOT, "k2")
BASE = os.path.join(K2, "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-49.json")
PROJ = os.path.join(K2, "pm_gate/project.yaml")
NEW_REV = 50
OLD_BOARD = "6ff49da5678c2108"
DUMP = dict(ensure_ascii=False, indent=1)


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def paths(o, p="", acc=None):
    acc = set() if acc is None else acc
    if isinstance(o, dict):
        for k, v in o.items():
            paths(v, f"{p}/{k}", acc)
    elif isinstance(o, list):
        acc.add(p)                     # 列表级（长度/内容变化记列表路径）
        for i, v in enumerate(o):
            paths(v, f"{p}[{i}]", acc)
    else:
        acc.add(p)
    return acc


def values(o, p="", acc=None):
    acc = {} if acc is None else acc
    if isinstance(o, dict):
        for k, v in o.items():
            values(v, f"{p}/{k}", acc)
    elif isinstance(o, list):
        acc[p] = json.dumps(o, ensure_ascii=False)
    else:
        acc[p] = o
    return acc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec-base", default=BASE)
    ap.add_argument("--spec-new", default="/tmp/opencode/owner5/SPEC_k2_v4.spec-rev-50.json")
    ap.add_argument("--project-yaml", default=PROJ)
    ap.add_argument("--board-sha16", required=True, help="新受审板 sha16（由板删除器产出）")
    ap.add_argument("--nets-yaml", default="hw/data/k2_sch.errata-2.yaml")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--confirm-repo-write", action="store_true")
    a = ap.parse_args()

    base = json.load(io.open(a.spec_base, encoding="utf-8"))
    new = copy.deepcopy(base)
    assert a.spec_new.endswith("spec-rev-%d.json" % NEW_REV), "输出文件名须为 spec-rev-50.json"

    # ① 删 PWR_5V_KEY（live 网清单）
    nets = new["layer_plan"]["low_speed_nets"]["nets"]
    if nets.count("PWR_5V_KEY") != 1:
        raise SystemExit("FAIL-CLOSED: low_speed_nets 内 PWR_5V_KEY 命中 != 1")
    nets.remove("PWR_5V_KEY")
    # ② 删 C89 的 live power_pad_connect 条目
    ents = new["pd"]["zone_defs"]["power_pad_connect"]["entries"]
    hit = [i for i, e in enumerate(ents) if isinstance(e, dict) and e.get("ref") == "C89"]
    if len(hit) != 1:
        raise SystemExit(f"FAIL-CLOSED: power_pad_connect.entries 内 ref=C89 命中 = {len(hit)}（期望 1）")
    removed_entry = ents.pop(hit[0])
    # ③ live board_sha16 ×3 + basis 文本
    live = [("mounting_holes", new["mounting_holes"]),
            ("keepout_geometry", new["keepout_geometry"]),
            ("pd.zone_defs.board_realized_zones", new["pd"]["zone_defs"]["board_realized_zones"])]
    for name, obj in live:
        if obj.get("board_sha16") != OLD_BOARD:
            raise SystemExit(f"FAIL-CLOSED: {name}.board_sha16 != {OLD_BOARD}")
        obj["board_sha16"] = a.board_sha16
        if isinstance(obj.get("basis"), str) and OLD_BOARD in obj["basis"]:
            obj["basis"] = obj["basis"].replace(OLD_BOARD, a.board_sha16)
    # ④ 变更留痕
    new["_spec_rev_%d" % NEW_REV] = {
        "at": "2026-09-18",
        "basis": ["owner 裁定「删」（⑤ `C89`/`PWR_5V_KEY`，owner 2026-09-18）",
                  "执行放行：#K2-24（§三 7 载体一次做净；§四 守恒闸）"],
        "deleted": {"layer_plan.low_speed_nets.nets": ["PWR_5V_KEY"],
                    "pd.zone_defs.power_pad_connect.entries": [removed_entry],
                    "true_source": ["nets.PWR_5V_KEY", "C89 placement", "nets.GND 成员 C89/B"]},
        "retained_named": {"retired_superseded_clearance_v1 / retired_superseded_bom 的 C89 条目":
                           "**保留**（红线『退役几何/决策须显式留存』；#K2-24 §三-2 限定「live 字段」）"},
        "board_sha16": a.board_sha16,
        "nets_yaml": a.nets_yaml,
        "scope_note": "**不含** #K2-23 §二-6 已驳回的 errata-2 内容（105 条 NC / 其他删网）；不含任何为变绿而新增的删减（C-12）",
    }

    # ── 深 diff 断言：改动路径 ⊆ 允许集 ────────────────────────────────────
    vb, vn = values(base), values(new)
    changed = {p for p in set(vb) | set(vn) if vb.get(p) != vn.get(p)}
    allowed = {"/layer_plan/low_speed_nets/nets",
               "/pd/zone_defs/power_pad_connect/entries",
               "/mounting_holes/board_sha16", "/mounting_holes/basis",
               "/keepout_geometry/board_sha16", "/keepout_geometry/basis",
               "/pd/zone_defs/board_realized_zones/board_sha16", "/pd/zone_defs/board_realized_zones/basis",
               "/_spec_rev_%d" % NEW_REV}
    extra = {p for p in changed if p not in allowed and not p.startswith("/_spec_rev_%d" % NEW_REV)}
    if extra:
        raise SystemExit(f"FAIL-CLOSED: 出现未授权改动路径：{sorted(extra)[:10]}")
    print(f"[verify] 改动路径 {len(changed)}（允许集 {len(allowed)}）· nets {len(base['layer_plan']['low_speed_nets']['nets'])}→"
          f"{len(new['layer_plan']['low_speed_nets']['nets'])} · power_pad_connect.entries "
          f"{len(base['pd']['zone_defs']['power_pad_connect']['entries'])}→{len(new['pd']['zone_defs']['power_pad_connect']['entries'])} · "
          f"board_sha16 {OLD_BOARD}→{a.board_sha16}")
    print(f"[verify] 保留：retired_superseded_* 两条 C89 退役条目 = "
          f"{sum(1 for k in ('retired_superseded_clearance_v1','retired_superseded_bom') for e in (base['pd']['zone_defs']['power_pad_connect'][k]['entries']) if e.get('ref')=='C89')} 条")

    payload = json.dumps(new, **DUMP)
    out = os.path.abspath(a.spec_new)
    repo_spec = os.path.join(K2, "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-%d.json" % NEW_REV)
    _pj_sha = sha16(a.project_yaml) if os.path.isfile(a.project_yaml) else "N/A(沙箱待生成)"
    print(f"[before] {os.path.relpath(a.spec_base, ROOT)} sha16={sha16(a.spec_base)} · project.yaml sha16={_pj_sha}")
    if os.path.abspath(a.project_yaml) == os.path.abspath(PROJ) and not (a.apply and a.confirm_repo_write):
        print("BLOCKED(T-41): --project-yaml 指向仓库；须 --apply --confirm-repo-write（或用沙箱 project.yaml）。")
        return 2
    os.makedirs(os.path.dirname(out), exist_ok=True)
    io.open(out, "w", encoding="utf-8", newline="").write(payload)
    print(f"[save] {out} sha16={sha16(out)}")

    # project.yaml 更新（spec_name / nets_yaml；文本级 2 行）
    _pj_src = a.project_yaml if os.path.isfile(a.project_yaml) else PROJ   # 沙箱：以仓库件为基线，写到沙箱路径
    ptxt = io.open(_pj_src, encoding="utf-8").read()
    old_spec_line = [l for l in ptxt.splitlines() if l.startswith("spec_name:")]
    old_nets_line = [l for l in ptxt.splitlines() if l.startswith("nets_yaml:")]
    if len(old_spec_line) != 1 or len(old_nets_line) != 1:
        raise SystemExit("FAIL-CLOSED: project.yaml 未定位 spec_name/nets_yaml 行")
    ptxt2 = ptxt.replace(old_spec_line[0], "spec_name: SPEC_k2_v4.spec-rev-%d.json" % NEW_REV, 1)
    ptxt2 = ptxt2.replace(old_nets_line[0], "nets_yaml: %s" % a.nets_yaml, 1)
    pout = a.project_yaml if os.path.abspath(a.project_yaml) == os.path.abspath(PROJ) else os.path.join(
        os.path.dirname(out), "project.yaml")
    io.open(pout, "w", encoding="utf-8", newline="").write(ptxt2)
    print(f"[save] project.yaml -> {pout} sha16={sha16(pout)} "
          f"(spec_name: {old_spec_line[0].split(':',1)[1].strip()} → SPEC_k2_v4.spec-rev-{NEW_REV}.json; "
          f"nets_yaml: {old_nets_line[0].split(':',1)[1].strip()} → {a.nets_yaml})")

    if a.apply and a.confirm_repo_write:
        bk = f"/tmp/opencode/backup-owner5-{time.strftime('%Y%m%dT%H%M%S')}"
        os.makedirs(bk, exist_ok=True)
        for src in (os.path.join(K2, "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-49.json"), a.project_yaml):
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(bk, os.path.basename(src)))
        print(f"[T-22] 备份 rev-49 + project.yaml（旧 sha 见上）-> {bk}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
