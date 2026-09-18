#!/usr/bin/env python3
"""k2_p4_owner5_del_c89_pro_v1.py — owner ⑤ 执行（**删 `PWR_5V_KEY`**）pro 侧 netclass 删除器（#K2-24 §三-3）。

动作（fail-closed，文本级最小 diff）：
  ① 读 `.kicad_pro` 文本，定位 `netclass_assignments` 内 `"PWR_5V_KEY": [ ... ]` **整条**（含前后缩进/逗号）；
  ② 断言全文 `PWR_5V_KEY` 命中恰 = 1 处（entry 自身）⇒ 删后 **0**；
  ③ 断言删后 JSON 可解析且 `netclass_assignments` 数 146 → 145；
  ④ 其余字节不变（文本级替换）。
输出：默认沙箱（`--out`）；写仓库须 `--apply --confirm-repo-write`（T-41）+ T-22 备份/旧 sha。
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
K2 = os.path.join(ROOT, "k2")
DEFAULT_PRO = os.path.join(K2, "hw/k2_v4_8L.l5.kicad_pro")
NET = "PWR_5V_KEY"


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pro", default=DEFAULT_PRO)
    ap.add_argument("--out", default=DEFAULT_PRO, help="默认＝仓库 pro；沙箱请显式指定 /tmp 路径")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--confirm-repo-write", action="store_true")
    a = ap.parse_args()

    txt = open(a.pro, encoding="utf-8").read()
    before_json = json.loads(txt)
    n_before = len(before_json["net_settings"]["netclass_assignments"])
    hits = txt.count('"%s"' % NET)
    print(f"[before] {os.path.relpath(a.pro, ROOT)} sha16={sha16(a.pro)} "
          f"netclass_assignments={n_before} 命中={hits} 映射={before_json['net_settings']['netclass_assignments'].get(NET)}")
    if hits != 1:
        raise SystemExit(f"FAIL-CLOSED: 全文 `{NET}` 命中 = {hits}（期望 1）⇒ 停")

    m = re.search(r'\n(\s*)"%s": \[\n(?:[^\]]*\n)*?\s*\],?' % re.escape(NET), txt)
    if not m:
        raise SystemExit(f"FAIL-CLOSED: 未定位 `{NET}` 条目块（正则未命中）")
    block = m.group(0)
    # 去掉该条目前导换行；若其后紧跟 `}` 或 `]`（即原为末条）则同时吞掉前一条的尾逗号
    new_txt = txt.replace(block, "", 1)
    after_json = json.loads(new_txt)          # 解析即校验
    n_after = len(after_json["net_settings"]["netclass_assignments"])
    if NET in after_json["net_settings"]["netclass_assignments"] or NET in new_txt:
        raise SystemExit(f"FAIL-CLOSED: 删后仍存在 `{NET}`")
    print(f"[plan] 删除条目 {NET} → ['POWER']；netclass_assignments {n_before} → {n_after}")
    if n_before - n_after != 1:
        raise SystemExit("FAIL-CLOSED: 删除条目数 != 1")

    out = os.path.abspath(a.out)
    repo = os.path.abspath(DEFAULT_PRO)
    if out == repo and not (a.apply and a.confirm_repo_write):
        print("BLOCKED(T-41): 目标是仓库 pro；须 --apply --confirm-repo-write（或用 --out 沙箱）。")
        return 2
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if out == repo:                            # T-22：**先备份旧件**，再写
        bk = f"/tmp/opencode/backup-owner5-{time.strftime('%Y%m%dT%H%M%S')}"
        os.makedirs(bk, exist_ok=True)
        shutil.copy2(a.pro, os.path.join(bk, os.path.basename(a.pro)))
        print(f"[T-22] 旧 pro 备份 sha16={sha16(a.pro)} -> {bk}/")
    open(out, "w", encoding="utf-8", newline="").write(new_txt)
    print(f"[save] {out} sha16={sha16(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
