#!/usr/bin/env python3
"""k2_lane_draft_v1.py --- **车道起草器（同源硬闸版）**（#K2-443 sec.2.5 / #K2-446 sec.2.3(3) 的关账件）。

WHY：R1326 之前的一次起草**喂了异源 DRC**（板来自 A、DRC 来自 B）⇒ 路由器 `added=[] blocked=[]` **静默零产出**，
被当成「不可行」。本器把「**同源**」变成**结构性保证**：**DRC 由本器自己对同一块板现跑**（调用方无法传异源），
并对**空产出**做**响亮失败**（`ok=False` + 具名原因）。

CLI: python3 tools/k2_lane_draft_v1.py --board B --net NET --rect x0,y0,x1,y1 --out O [--ledger L]
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def draft_verdict(ledger):
    """**纯函数**：判一次起草的成败。**空产出 ⇒ 响亮失败**（绝不静默当作「不可行」）。"""
    added = ledger.get("added") or []
    blocked = ledger.get("blocked") or []
    if not added:
        return {"ok": False, "why": "EMPTY DRAFT: nothing was added (foreign DRC / no matching unconnected items / net "
                                    "already routed). Not a proof of infeasibility.", "added": 0, "blocked": len(blocked)}
    return {"ok": True, "why": "draft produced %d piece(s)" % len(added), "added": len(added), "blocked": len(blocked)}


def draft(board, net, rect, out, ledger_path=None, cli=None, py=None, timeout=1800):
    """**同源起草**：本器**自己**对 `board` 现跑 DRC ⇒ 不存在异源输入。空产出 ⇒ `ok=False`（响亮）。"""
    cli = cli or os.environ.get("EDA_ENG_CLI", "kicad-cli")
    py = py or os.environ.get("EDA_ENG_PY") or sys.executable
    drc = tempfile.mktemp(suffix="_same_source_drc.json")
    rc = subprocess.run([cli, "pcb", "drc", "--format", "json", "--severity-all", "-o", drc, board],
                        capture_output=True, text=True, timeout=timeout).returncode
    if rc != 0 or not os.path.isfile(drc):
        return {"artifact": "k2_lane_draft_v1", "ok": False, "why": "DRC_FAILED", "rc": rc}
    led = ledger_path or tempfile.mktemp(suffix="_lane_ledger.json")
    rc2 = subprocess.run([py, os.path.join(ROOT, "tools", "k2_reroute_router_floor_v1.py"),
                          "--in", board, "--drc", drc, "--out", out, "--ledger", led,
                          "--margin", "3.0", "--floor", "0.20",
                          "--bound-rect", ",".join(str(v) for v in rect), "--only-net", net],
                         capture_output=True, text=True, timeout=timeout).returncode
    ledger = json.load(open(led, encoding="utf-8")) if os.path.isfile(led) else {}
    v = draft_verdict(ledger)
    v.update({"artifact": "k2_lane_draft_v1", "board": board, "net": net, "same_source_drc": drc,
              "router_rc": rc2, "out": out, "ledger": led, "OWNER-ITEMS": 0})
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True); ap.add_argument("--net", required=True)
    ap.add_argument("--rect", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--ledger", default=None); ap.add_argument("--json-out", dest="json_out", default=None)
    a = ap.parse_args()
    rep = draft(a.board, a.net, [float(v) for v in a.rect.split(",")], a.out, a.ledger)
    if a.json_out:
        json.dump(rep, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False))
    return 0 if rep.get("ok") else 2


def _require_pcbnew():
    """#K2-448 sec.2.5(2): a tool that needs pcbnew must FAIL LOUDLY under a python without it (R1356's lesson:
    a host-python run silently aborted mid-script). Refusing to continue beats a silent no-op."""
    try:
        import pcbnew  # noqa: F401
    except Exception as _e:                                            # noqa: BLE001
        raise RuntimeError(
            "k2: this tool requires EDA_ENG_PY (a python with pcbnew); refusing to run silently under %s (%s)"
            % (sys.executable, type(_e).__name__))


_require_pcbnew()


if __name__ == "__main__":
    sys.exit(main())
