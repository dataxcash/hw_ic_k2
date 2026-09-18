#!/usr/bin/env python3
"""k2_p4_owner5_del_c89_board_v1.py — owner ⑤ 执行（**删 `C89`**）板侧删除器（#K2-24 §三-5）。

授权：owner 裁定「删」（`.omo/supervision/ledger/OWNER-RULING-20260918-delete-C89-PWR5V.md`）+
      #K2-24 执行放行令（§三 7 载体；§四 守恒闸）。**窄授权**：只删 `C89` 及其**直接**连线。

动作（fail-closed）：
  ① 断言板上恰有 1 个 `C89` footprint 且恰 2 pad（pad1=PWR_5V_KEY / pad2=GND）；
  ② 断言 **`PWR_5V_KEY` 无任何 track/via**（1 节点网 ⇒ 应无布线；否则**停**，具名上报）；
  ③ 删除 `C89` footprint；删除**端点落在其 pad 中心**的 track/via（pad2 的 GND 短段 + 缝合 via）；
  ④ 若 `PWR_5V_KEY` 在板内 net 表成为 0 pad 孤网 ⇒ 自板 net 表移除（避免孤网）；
  ⑤ 输出前后计数（footprints / pads / tracks / vias / nets / zones）+ 删除明细。
输出：默认沙箱（`--out`）；写仓库须 `--apply --confirm-repo-write`（T-41），落盘前 T-22 备份 + 打印旧 sha。
"""
from __future__ import annotations
import argparse, hashlib, os, shutil, time
import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
K2 = os.path.join(ROOT, "k2")
DEFAULT_BOARD = os.path.join(K2, "hw/k2_v4_8L.l5.kicad_pcb")


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def counts(b):
    tr = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
    vi = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    return {"footprints": len(b.GetFootprints()), "pads": sum(len(list(f.Pads())) for f in b.GetFootprints()),
            "tracks": len(tr), "vias": len(vi), "nets": len(b.GetNetsByName()), "zones": len(b.Zones())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", default=DEFAULT_BOARD)
    ap.add_argument("--out", default=DEFAULT_BOARD, help="默认＝仓库受审板；沙箱请显式指定 /tmp 路径")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--confirm-repo-write", action="store_true")
    a = ap.parse_args()

    b = pcbnew.LoadBoard(a.board)
    before = counts(b)
    print(f"[before] {os.path.relpath(a.board, ROOT)} sha16={sha16(a.board)} {before}")

    c89 = [f for f in b.GetFootprints() if f.GetReference() == "C89"]
    if len(c89) != 1:
        raise SystemExit(f"FAIL-CLOSED: C89 footprint 数 = {len(c89)}（期望 1）")
    fp = c89[0]
    pads = list(fp.Pads())
    if len(pads) != 2:
        raise SystemExit(f"FAIL-CLOSED: C89 pad 数 = {len(pads)}（期望 2）")
    nets = sorted(p.GetNetname() for p in pads)
    if nets != ["GND", "PWR_5V_KEY"]:
        raise SystemExit(f"FAIL-CLOSED: C89 pad 网 = {nets}（期望 ['GND','PWR_5V_KEY']）")

    key_tracks = [t for t in b.GetTracks() if t.GetNetname() == "PWR_5V_KEY"]
    if key_tracks:
        raise SystemExit(f"FAIL-CLOSED: `PWR_5V_KEY` 仍有 {len(key_tracks)} 条 track/via ⇒ 停（须具名上报）")

    centers = {(p.GetPosition().x, p.GetPosition().y) for p in pads}

    def _ends(t):
        return {(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)}

    def _key(t):   # SWIG 包装对象 id() 不稳定 ⇒ 用几何/类型稳定键
        return (t.Type(), int(t.GetLayer()), t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y)

    victims = [t for t in list(b.GetTracks()) if _ends(t) & centers]
    # 级联：被删段另一端若有**唯一**连接件（= 该点的缝合 via）⇒ 一并删；若该点还有别的连接 ⇒ 停（歧义）
    seen = {_key(t) for t in victims}
    pending = list(victims)
    while pending:
        t = pending.pop()
        for pt in _ends(t) - centers:
            at = [u for u in b.GetTracks() if _key(u) not in seen and pt in _ends(u)]
            if len(at) == 1:
                victims.append(at[0]); seen.add(_key(at[0])); pending.append(at[0])
            elif len(at) > 1:
                raise SystemExit(f"FAIL-CLOSED: 点 ({(pcbnew.ToMM(pt[0])):.3f},{(pcbnew.ToMM(pt[1])):.3f}) 处仍有 "
                                 f"{len(at)} 个连接件 ⇒ 歧义，停（须具名上报）")
    print(f"[plan] 删除 C89 footprint + {len(victims)} 条连线：")
    for t in victims:
        print(f"   - {t.GetNetname():8s} type={'VIA' if t.Type()==pcbnew.PCB_VIA_T else 'TRACE'} "
              f"layer={b.GetLayerName(t.GetLayer())} "
              f"{[round(pcbnew.ToMM(t.GetStart().x),3),round(pcbnew.ToMM(t.GetStart().y),3)]} -> "
              f"{[round(pcbnew.ToMM(t.GetEnd().x),3),round(pcbnew.ToMM(t.GetEnd().y),3)]}")
    for t in victims:
        b.Remove(t)
    b.Remove(fp)

    # 孤网清理：PWR_5V_KEY 若已无 pad 且无 track ⇒ 自 net 表移除
    remain_pads = sum(1 for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == "PWR_5V_KEY")
    remain_tr = sum(1 for t in b.GetTracks() if t.GetNetname() == "PWR_5V_KEY")
    dropped_net = False
    if remain_pads == 0 and remain_tr == 0:
        ni = b.FindNet("PWR_5V_KEY")
        if ni is not None:
            b.RemoveNative(ni)
            dropped_net = True
            print("[plan] 孤网 `PWR_5V_KEY`（0 pad / 0 track）自板 net 表移除")
    after = counts(b)
    print(f"[after-runtime] {after}  孤网移除={dropped_net}")

    out = os.path.abspath(a.out)
    repo_board = os.path.abspath(DEFAULT_BOARD)
    if out == repo_board and not (a.apply and a.confirm_repo_write):
        print("BLOCKED(T-41): 目标是仓库板路径；须 --apply --confirm-repo-write（或用 --out 指沙箱）。")
        return 2
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if out == repo_board:                      # T-22：**先备份旧件**，再写
        bk = f"/tmp/opencode/backup-owner5-{time.strftime('%Y%m%dT%H%M%S')}"
        os.makedirs(bk, exist_ok=True)
        shutil.copy2(a.board, os.path.join(bk, os.path.basename(a.board)))
        print(f"[T-22] 旧板备份 sha16={sha16(a.board)} -> {bk}/")
    pcbnew.SaveBoard(out, b)
    print(f"[save] {out} sha16={sha16(out)}")
    if out != repo_board:
        print("[sandbox] 未落仓库（沙箱目标）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
