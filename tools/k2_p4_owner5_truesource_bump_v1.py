#!/usr/bin/env python3
"""k2_p4_owner5_truesource_bump_v1.py — owner ⑤ 执行（**删 `C89` + `PWR_5V_KEY`**）真源 bump（#K2-24 §三-1）。

窄授权（#K2-24 §二）：**仅** `C89` 与 `PWR_5V_KEY` 及其连带引用（3 处）：
  ① `nets.GND` 成员去掉 `C89/B`
  ② 删整条 `nets.PWR_5V_KEY`（`- C89/A`）
  ③ 删 `C89` placement（`- ref: C89` + symbol/card）
**原件 `k2/hw/data/k2_sch.yaml` `dd794c54f7ce7417` 逐字节不动**；基线 = 现行消费件 `errata-1` `17d540f058631a5e`。
**不含** errata-2 的历史内容（105 NC / 其他删网）—— #K2-23 §二-6 已驳、本裁定未授权。

做法：**文本级最小 diff**（非重排 YAML）⇒ 逐行删除上述 3 块 + 顶部插入 basis 注释；
      并以 **PyYAML 语义断言**（删除集恰等于上述 3 处，其余字段逐项相同）fail-closed。
输出：默认沙箱（`--out`）；写仓库须 `--apply --confirm-repo-write`（T-41）+ T-22 备份/旧 sha。
"""
from __future__ import annotations
import argparse, hashlib, io, os, shutil, time
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
K2 = os.path.join(ROOT, "k2")
SRC = os.path.join(K2, "hw/data/k2_sch.errata-1.yaml")
DST = os.path.join(K2, "hw/data/k2_sch.errata-2.yaml")
HDR = """# k2_sch.errata-2.yaml — 真源网表（乙2 线；**仅** owner ⑤ 删减）
# basis: owner 裁定「删」（.omo/supervision/ledger/OWNER-RULING-20260918-delete-C89-PWR5V.md）+ 监理 #K2-24（§三-1）
#  删减且仅删减：`nets.PWR_5V_KEY` · `C89` placement · `nets.GND` 成员 `C89/B`。
#  **不含** #K2-23 §二-6 已驳回的 errata-2 内容（105 条 NC / 其他删网）——未经授权，不得夹带。
# 上游：`k2_sch.yaml`（原件 dd794c54f7ce7417，逐字节不动）→ `k2_sch.errata-1.yaml`（17d540f058631a5e）→ 本件。
"""


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--out", default=DST)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--confirm-repo-write", action="store_true")
    a = ap.parse_args()

    lines = io.open(a.src, encoding="utf-8").read().splitlines(keepends=True)
    before = yaml.safe_load("".join(lines))

    # 精确定位 3 块（逐行匹配 + 邻域校验；命中数必须为 1）
    def find(pred, near=None, ctx=None):
        hits = [i for i, l in enumerate(lines) if pred(l)]
        if len(hits) != 1:
            raise SystemExit(f"FAIL-CLOSED: 目标行命中数 = {len(hits)}（期望 1）：{[lines[h].rstrip() for h in hits][:5]}")
        i = hits[0]
        if near is not None and lines[i + near] != ctx:
            raise SystemExit(f"FAIL-CLOSED: 行 {i+1} 邻域不符：{lines[i+near]!r} != {ctx!r}")
        return i

    i_gnd = find(lambda l: l == "  - C89/B\n", near=-1, ctx="  - C88/B\n")
    i_net = find(lambda l: l == "  PWR_5V_KEY:\n", near=+1, ctx="  - C89/A\n")
    i_plc = find(lambda l: l == "  - ref: C89\n", near=+1, ctx="    symbol: C_4R7\n")
    if lines[i_plc + 2] != "    card: '2'\n":
        raise SystemExit("FAIL-CLOSED: C89 placement 第三行不符（期望 card '2'）")

    drop = {i_gnd, i_net, i_net + 1, i_plc, i_plc + 1, i_plc + 2}
    out_lines = [HDR] + [l for i, l in enumerate(lines) if i not in drop]
    after = yaml.safe_load("".join(out_lines))

    # ── 语义断言：删除集恰为 3 处，其余逐项相同 ─────────────────────────────
    assert set(before["nets"]) - set(after["nets"]) == {"PWR_5V_KEY"}, "nets 删除集不符"
    assert set(after["nets"]) - set(before["nets"]) == set(), "nets 新增"
    for k in before["nets"]:
        if k == "PWR_5V_KEY":
            continue
        exp = before["nets"][k]
        got = after["nets"][k]
        if k == "GND":
            assert set(exp) - set(got) == {"C89/B"} and set(got) - set(exp) == set(), "GND 成员删除集不符"
            assert [m for m in got] == [m for m in exp if m != "C89/B"], "GND 成员顺序被改动"
        else:
            assert got == exp, f"net {k} 内容被改动"
    b_plc = [(sh["title"], p) for sh in before["sheets"] for p in sh["placements"]]
    a_plc = [(sh["title"], p) for sh in after["sheets"] for p in sh["placements"]]
    assert [x for x in b_plc if x[1]["ref"] != "C89"] == a_plc, "placements 非「仅删 C89」"
    assert len(a_plc) == len(b_plc) - 1, "placements 计数不符"
    for f in ("symbols", "sheets", "strap_intents", "links"):
        b_ = before.get(f)
        a_ = after.get(f)
        if f == "sheets":
            b_ = [{k: v for k, v in sh.items() if k != "placements"} for sh in b_]
            a_ = [{k: v for k, v in sh.items() if k != "placements"} for sh in a_]
        assert a_ == b_, f"字段 {f} 被改动"
    print(f"[verify] nets {len(before['nets'])}→{len(after['nets'])}（删 PWR_5V_KEY）· "
          f"GND 成员 {len(before['nets']['GND'])}→{len(after['nets']['GND'])}（删 C89/B）· "
          f"placements {len(b_plc)}→{len(a_plc)}（删 C89）")

    payload = "".join(out_lines)
    out = os.path.abspath(a.out)
    repo = os.path.abspath(DST)
    print(f"[before] {os.path.relpath(a.src, ROOT)} sha16={sha16(a.src)}")
    if out == repo and not (a.apply and a.confirm_repo_write):
        print("BLOCKED(T-41): 目标是仓库真源路径；须 --apply --confirm-repo-write（或用 --out 沙箱）。")
        return 2
    os.makedirs(os.path.dirname(out), exist_ok=True)
    io.open(out, "w", encoding="utf-8", newline="").write(payload)
    print(f"[save] {out} sha16={sha16(out)}")
    if out == repo:
        bk = f"/tmp/opencode/backup-owner5-{time.strftime('%Y%m%dT%H%M%S')}"
        os.makedirs(bk, exist_ok=True)
        shutil.copy2(a.src, os.path.join(bk, os.path.basename(a.src)))
        print(f"[T-22] 上游件备份 sha16={sha16(a.src)} -> {bk}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
