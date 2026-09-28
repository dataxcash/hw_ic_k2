"""M2 · `eda_eng ripup` --- 执行拆除（#K2-360 §一 M2）。

输入：M1 清单（`netplan` 输出）        输出：拆后板
判据：拆后 **unconnected == 预期 N**（预期 = 新出现的未连接项**全部落在受影响网上**）· **他网零触碰（逐段 diff 证）**

纪律（#K2-360 §二 · #K2-347 封存令）：**只拆 M1 清单里逐条列出的那几件**（网＋层＋几何＋宽/钻孔逐一匹配），
不按"网"整片删、不做任何"顺手清理"。计数不符即 **fail-fast**（清单陈旧 ⇒ 拒拆）。

注：pcbnew 在 `Remove()` 时会向 stderr 打 SWIG「memory leak」提示（已知噪声，不影响结果）；调用方可重定向 stderr。
"""
from __future__ import annotations
import hashlib, json, os


def _pcbnew():
    import pcbnew as P
    return P


def _key_track(P, b, t):
    nm = t.GetNetname() if hasattr(t, "GetNetname") else b.FindNet(t.GetNetCode()).GetNetname()
    s, e = t.GetStart(), t.GetEnd()
    return (nm, t.GetLayerName(),
            round(P.ToMM(s.x), 4), round(P.ToMM(s.y), 4), round(P.ToMM(e.x), 4), round(P.ToMM(e.y), 4),
            round(P.ToMM(t.GetWidth()), 4))


def _key_via(P, b, t):
    nm = t.GetNetname() if hasattr(t, "GetNetname") else b.FindNet(t.GetNetCode()).GetNetname()
    pos = t.GetPosition()
    return (nm, round(P.ToMM(pos.x), 4), round(P.ToMM(pos.y), 4), round(P.ToMM(t.GetDrill()), 4))


def execute(board, plan, out, dry=False):
    """按 M1 清单拆除。返回报告（含逐条匹配统计与 fail-fast 原因）。"""
    P = _pcbnew()
    b = P.LoadBoard(board)
    want_tracks, want_vias = set(), set()
    for net, items in plan["teardown"].items():
        for t in items["tracks"]:
            want_tracks.add((net, t["layer"], t["a"][0], t["a"][1], t["b"][0], t["b"][1], t["width_mm"]))
        for v in items["vias"]:
            want_vias.add((net, v["at"][0], v["at"][1], v["drill_mm"]))
    have_tracks, have_vias = {}, {}
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            have_vias.setdefault(_key_via(P, b, t), []).append(t)
        else:
            have_tracks.setdefault(_key_track(P, b, t), []).append(t)
    miss_t = [k for k in want_tracks if k not in have_tracks]
    miss_v = [k for k in want_vias if k not in have_vias]
    if miss_t or miss_v:
        return {"status": "REFUSED_STALE_PLAN", "missing_tracks": miss_t[:5], "missing_vias": miss_v[:5],
                "note": "the plan does not match the board (stale netplan) - refusing to rip anything"}
    report = {"artifact": "eda_eng_ripup", "board": board, "plan_affected_nets": sorted(plan["teardown"]),
              "dry_run": dry,
              "matched": {"tracks": sum(len(have_tracks[k]) for k in want_tracks),
                          "vias": sum(len(have_vias[k]) for k in want_vias),
                          "unique_keys": {"tracks": len(want_tracks), "vias": len(want_vias)}},
              "removed": {"tracks": 0, "vias": 0}}
    if dry:
        report["status"] = "DRY_RUN_OK"
        return report
    for k in want_tracks:
        for t in have_tracks[k]:
            b.Remove(t); report["removed"]["tracks"] += 1
    for k in want_vias:
        for t in have_vias[k]:
            b.Remove(t); report["removed"]["vias"] += 1
    P.SaveBoard(out, b)
    report.update({"status": "RIPPED", "out": out,
                   "out_sha16": hashlib.sha256(open(out, "rb").read()).hexdigest()[:16]})
    return report


def run(*_a, **_k):
    return {"status": "NOT_IMPLEMENTED"}
