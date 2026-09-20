#!/usr/bin/env python3
"""k2_batch2_s1_shadow_verify_v1.py — 批 2 · S1（`_shared` 引擎四修 B1/B2/B3/B4）**影子预验证**。

真源零改动：拷贝 `k2/_shared` → `/tmp/opencode/batch2_shadow`，在影子内施加四修并跑 CLI 矩阵。
补丁（依 #K2-41 §三-②③）：
  B1 `hs_route_model.py` link_topology `x_l/x_r` 空序列 → None + cap_wall None 守卫（fail-closed）
  B2 CLI 层包装刻意抛错（`--chain` / `--chain-v2` / `--nets`）⇒ `status=INFRA_ERROR` + **rc=3（可机辨）**
  B3 `--capacity-map` 总判 = worst-of(region, corridor)（`insufficient_corridors` 子字段保留）
  B4 `_corridor_clear_span` 对 `x_range` 形状校验（显式具名错误，非裸 ValueError）
实测（2026-09-20 影子）：p3 载体 `--link-topology` 崩溃→CROSSING_FOUND[UP4..UP7]；`--capacity-map` 吞数→
INSUFFICIENT + insufficient_corridors=[EAST_CHIP_TO_J2_refclk]；`--chain UP0` rc=1 裸 traceback→rc=3+INFRA_ERROR；
遗留载体结果不回退（`--link-topology` 同、`--chain REFCLK0` INFEASIBLE、`--chain-v2 UP0` INFEASIBLE）。
用法（容器根）：python3 k2/tools/k2_batch2_s1_shadow_verify_v1.py
"""
import shutil, os, subprocess, sys, json, hashlib
from pathlib import Path
REPO=Path("/home/fila/jqdDev_2025/ic_hw"); K2=REPO/"k2"; SH=Path("/tmp/opencode/batch2_shadow")
shutil.rmtree(SH, ignore_errors=True)
shutil.copytree(K2/"_shared", SH/"shared", ignore=shutil.ignore_patterns(".git","__pycache__",".pytest_cache"))
hp=SH/"shared/eda_core/hs_route_model.py"; s=hp.read_text(encoding="utf-8")
P=[]
P.append(("""        x_l = min(s["end_left"]["x"] for s in segs
                  if "end_left" in s)
        x_r = max(s["end_right"]["x"] for s in segs
                  if "end_right" in s)""",
"""        _ls = [s["end_left"]["x"] for s in segs if "end_left" in s]
        _rs = [s["end_right"]["x"] for s in segs if "end_right" in s]
        x_l = min(_ls) if _ls else None
        x_r = max(_rs) if _rs else None"""))
P.append(("""            if xr and xr[0] <= x_r and xr[1] >= x_l:""",
"""            if (xr and x_l is not None and x_r is not None
                    and xr[0] <= x_r and xr[1] >= x_l):"""))
P.append(("""        comps = self.spec.get("components") or {}
        x0, x1 = corridor["x_range"]""",
"""        comps = self.spec.get("components") or {}
        xr = corridor.get("x_range") or []
        if not isinstance(xr, (list, tuple)) or len(xr) != 2:
            raise ValueError(
                "corridor.x_range 形状非法（预期 2 元素，fail-closed）: "
                f"{corridor.get('id')!r}")
        x0, x1 = float(xr[0]), float(xr[1])"""))
P.append(("""        bad_regions = [rid for rid, r in cap["regions"].items()
                       if r.get("status") != "CAPACITY_OK"]""",
"""        bad_regions = [rid for rid, r in cap["regions"].items()
                       if r.get("status") != "CAPACITY_OK"]
        # B3（#K2-41 §三-③）：总判 = worst-of(region, corridor)；region 保留为子字段
        bad_corridors = [cid for cid, c in cap["corridors"].items()
                         if c.get("status") != "CAPACITY_OK"]"""))
P.append(("""        print(json.dumps({"status": "CAPACITY_OK" if not bad_regions
                          else "INSUFFICIENT",""",
"""        print(json.dumps({"status": "CAPACITY_OK" if not bad_regions
                          and not bad_corridors else "INSUFFICIENT",
                          "insufficient_corridors": bad_corridors,"""))
P.append(("""        return 0 if not bad_regions else 1""",
"""        return 0 if (not bad_regions and not bad_corridors) else 1"""))
P.append(("""        res = m.solve_chain(args.chain)""",
"""        try:
            res = m.solve_chain(args.chain)
        except Exception as exc:   # B2：刻意 fail-closed 抛错 → CLI 机辨化
            print(json.dumps({"status": "INFRA_ERROR", "error_kind": "SOLVER_RAISED",
                              "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
            return 3"""))
P.append(("""        res = m.solve_chain_v2(args.chain_v2)""",
"""        try:
            res = m.solve_chain_v2(args.chain_v2)
        except Exception as exc:   # B2
            print(json.dumps({"status": "INFRA_ERROR", "error_kind": "SOLVER_RAISED",
                              "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
            return 3"""))
P.append(("""    res = m.solve_pair_segment(nets[0], nets[1])""",
"""    try:
        res = m.solve_pair_segment(nets[0], nets[1])
    except Exception as exc:       # B2
        print(json.dumps({"status": "INFRA_ERROR", "error_kind": "SOLVER_RAISED",
                          "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
        return 3"""))
for old,new in P:
    assert s.count(old)==1, "MISS x%d: %r" % (s.count(old), old[:50])
    s=s.replace(old,new,1)
hp.write_text(s, encoding="utf-8")
import py_compile; py_compile.compile(str(hp), doraise=True)
print("PATCHED OK B1/B2/B3/B4:", hashlib.sha256(s.encode()).hexdigest()[:16])
def run(carrier, extra, timeout=300):
    alloc="/tmp/opencode/current_alloc_from_pipeline.json" if carrier=="p3" else str(K2/"pm_gate/artifacts/k2_v4/L3/model_solves/channel_alloc_v2/channel_alloc.json")
    env={k:v for k,v in os.environ.items() if k!="PM_GATE_PROJECT_ROOT"}; env["PYTHONPATH"]=str(SH/"shared")
    out=Path("/tmp/opencode/b2shadow_out")/carrier/extra[0].strip("-"); out.mkdir(parents=True, exist_ok=True)
    cmd=[sys.executable,"-m","eda_core.hs_route_model","--board",str(K2/"hw/k2_v4_8L.kicad_pcb"),
         "--spec",str(K2/"pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json"),"--alloc",alloc,
         "--rules",str(K2/"_shared/eda_core/drc_rules.json"),"--pro",str(K2/"hw/k2_v4_8L.kicad_pro"),*extra,"--out",str(out)]
    pr=subprocess.run(cmd,cwd=str(SH),env=env,capture_output=True,text=True,timeout=timeout)
    last=[l for l in pr.stdout.strip().splitlines() if l.strip()]
    try: j=json.loads(last[-1]) if last else {}
    except Exception: j={}
    return {"carrier":carrier,"cmd":" ".join(extra),"rc":pr.returncode,"status":j.get("status"),
            "insufficient_corridors":j.get("insufficient_corridors"),"crossing":j.get("crossing_links")}
for r in [run(c,x) for c in ("p3","legacy") for x in (["--link-topology"],["--capacity-map"],["--chain","UP0"],["--chain","REFCLK0"],["--chain-v2","UP0"])]:
    print(json.dumps(r, ensure_ascii=False))
