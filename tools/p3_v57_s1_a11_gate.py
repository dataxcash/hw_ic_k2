#!/usr/bin/env python3
"""P3 v57 S1 — A1.1 门：守恒判定 对照 独立穷举基准（合成反例两族 + 随机）。

验收（m13_v57_s1_generator_design.md §6 / m13_v57_execution_plan.md A1.1）：
  对每组生成实例：
   1) conservation 核心判定 == 独立穷举基准判定（决策一致）；
   2) 不可行实例：核心证书 == 基准证书（规范最小不满足集，逐字节一致）；
   3) 证书自检：core 不可行且任意真子集可行（cardinality asc / lex 首个 = 唯一核）。
  两族（各自可辨识标签，防"同源两实现自我对拍"空转）：
   F1 看似有隙实无解：naive 乐观计数预判(每页域内≥2空槽 且 总空槽≥2n)=FEASIBLE，
      而精确引擎=INFEASIBLE（分离/独占约束破坏计数假象）。
   F2 看似无解实可行：id 序 first-fit 贪心预判=INFEASIBLE，而精确引擎=FEASIBLE
      （灵活配对绕过贪心死路）。

确定性：固定 seed；全部实例与报告逐字节可复现（A0.1 同款纪律）。
任一不匹配 → exit 1（L7：不过即停）。
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3_v57_s1_conservation as core        # noqa: E402
import p3_v57_s1_exhaustive_ref as ref       # noqa: E402

OUT = (Path(__file__).resolve().parents[1] / "pm_gate" / "artifacts" / "k2_v4" /
       "L3" / "mcio_feas_step2" / "m13_v57_s1_a11_report.json")
SEED = 20260909
SEP = 0.36


# ---- 合成实例生成 ---------------------------------------------------------
def make_spec(slot_pos: list, free_idx: list, pages: list, seed_rng) -> dict:
    free_set = set(free_idx)
    blockers = [{"pos": round(slot_pos[i], 3), "radius": 0.05}
                for i in range(len(slot_pos)) if i not in free_set]
    return {"slots": [{"i": i, "pos": round(x, 3)}
                      for i, x in enumerate(slot_pos)],
            "blockers": blockers, "sep": SEP,
            "pages": [{"id": f"P{k}", "domain": [d[0], d[1]]}
                      for k, d in enumerate(pages)]}


def _rand_instance(rng: random.Random):
    m = rng.randint(5, 10)
    # 基础 pitch 0.2 + 随机加宽缺口（制造可隔位配对），保证 0.3~1.8 轴长
    pos = [round(i * 0.2 + (0.12 if i % 3 == 2 else 0.0), 3)
           for i in range(m)]
    pos = [pos[0]] + [round(max(pos[i], pos[i - 1] + 0.18), 3)
                      for i in range(1, m)]
    free_all = set(range(m))
    n_blk = rng.randint(0, max(1, m - 2))
    for _ in range(n_blk):
        if len(free_all) > 2:
            free_all.discard(rng.choice(sorted(free_all)))
    np_ = rng.randint(2, 5)
    pages = []
    for k in range(np_):
        lo = rng.randint(0, max(0, m - 2))
        hi = rng.randint(min(lo + 1, m - 1), m - 1)
        pages.append([lo, hi])
    return make_spec(pos, sorted(free_all), pages, rng)


def naive_count_predict(spec: dict) -> bool:
    """乐观计数预判（无分离/无冲突语义）：每页域内空槽≥2 且 总空槽≥2n → 可行。"""
    free = {s["i"] for s in spec["slots"]
            if not any(abs(s["pos"] - b["pos"]) < b["radius"]
                       for b in spec["blockers"])}
    if len(free) < 2 * len(spec["pages"]):
        return False
    for p in spec["pages"]:
        lo, hi = p["domain"]
        if sum(1 for i in free if lo <= i <= hi) < 2:
            return False
    return True


def greedy_firstfit_predict(spec: dict) -> bool:
    """id 序 first-fit 贪心（无回溯）：每页取字典序首个可行对，卡住=不可行。"""
    free = set(s["i"] for s in spec["slots"])
    for p in sorted(spec["pages"], key=lambda q: q["id"]):
        lo, hi = p["domain"]
        cand = [s for s in spec["slots"] if lo <= s["i"] <= hi and s["i"] in free
                and not any(abs(s["pos"] - b["pos"]) < b["radius"]
                            for b in spec.get("blockers", []))]
        picked = None
        for a in range(len(cand)):
            for b in range(a + 1, len(cand)):
                if cand[b]["pos"] - cand[a]["pos"] >= spec["sep"] - 1e-9:
                    picked = (cand[a]["i"], cand[b]["i"])
                    break
            if picked:
                break
        if picked is None:
            return False
        free -= set(picked)
    return True


def _cert_selfcheck(spec: dict, cert: dict, eng) -> bool:
    """核自检：cert.core 不可行（引擎真值）且任意真子集可行。"""
    if cert is None:
        return True
    core_ids = set(cert["minimal_core"])
    sub = {"slots": spec["slots"], "blockers": spec.get("blockers", []),
           "sep": spec["sep"],
           "pages": [p for p in spec["pages"] if p["id"] in core_ids]}
    if eng(sub)[0]:
        return False
    from itertools import combinations
    ids = sorted(core_ids)
    for r in range(1, len(ids)):
        for combo in combinations(ids, r):
            ss = {"slots": spec["slots"], "blockers": spec.get("blockers", []),
                  "sep": spec["sep"],
                  "pages": [p for p in spec["pages"] if p["id"] in set(combo)]}
            if not eng(ss)[0]:
                return False
    return True


def main() -> int:
    rng = random.Random(SEED)
    instances = []                       # (family, spec)
    # F1: 乐观计数=可行 且 精确=不可行
    f1, tries = 0, 0
    while f1 < 40 and tries < 4000:
        tries += 1
        sp = _rand_instance(rng)
        if naive_count_predict(sp) and not core.feasible(sp):
            instances.append(("F1_looks_roomy_infeasible", sp))
            f1 += 1
    # F2: first-fit 贪心=不可行 且 精确=可行
    f2, tries = 0, 0
    while f2 < 40 and tries < 4000:
        tries += 1
        sp = _rand_instance(rng)
        if not greedy_firstfit_predict(sp) and core.feasible(sp):
            instances.append(("F2_looks_blocked_feasible", sp))
            f2 += 1
    # 随机集（两种精确引擎是否一致的一般性检验）
    for _ in range(60):
        instances.append(("RANDOM", _rand_instance(rng)))

    tally = {"F1": 0, "F2": 0, "RANDOM": 0}
    decision_mismatch = []
    cert_mismatch = []
    cert_selfcheck_fail = []
    for fam, sp in instances:
        tally[fam.split("_")[0]] = tally.get(fam.split("_")[0], 0) + 1
        ok_core, _ = core._solve_kernel(sp)
        ok_ref, _ = ref._solve_bruteforce(sp)
        if ok_core != ok_ref:
            decision_mismatch.append({"family": fam, "spec": sp,
                                      "core": ok_core, "ref": ok_ref})
            continue
        if not ok_core:
            c_core = core.certificate(sp)
            c_ref = ref.certificate(sp)
            norm = lambda c: {k: c[k] for k in ("minimal_core", "check")}
            if json.dumps(norm(c_core), sort_keys=True) != \
                    json.dumps(norm(c_ref), sort_keys=True):
                cert_mismatch.append({"family": fam, "core": c_core,
                                      "ref": c_ref})
            if not _cert_selfcheck(sp, c_core, core._solve_kernel):
                cert_selfcheck_fail.append({"family": fam, "spec": sp,
                                            "cert": c_core})

    n = len(instances)
    ok = (not decision_mismatch and not cert_mismatch and
          not cert_selfcheck_fail)
    report = {
        "artifact": "m13_v57_s1_a11_report",
        "predicate": "A1.1 守恒判定正确性(合成反例两族+随机, 核心 vs 独立穷举基准)",
        "seed": SEED,
        "tally": tally,
        "n_instances": n,
        "decision_match": n - len(decision_mismatch),
        "cert_match": (sum(1 for _, sp in instances
                           if not core.feasible(sp)) - len(cert_mismatch)),
        "cert_selfcheck_ok": (sum(1 for _, sp in instances
                                  if not core.feasible(sp)) -
                              len(cert_selfcheck_fail)),
        "decision_mismatch": decision_mismatch,
        "cert_mismatch": cert_mismatch,
        "cert_selfcheck_fail": cert_selfcheck_fail,
        "verdict": "PASS" if ok else "FAIL",
    }
    OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False,
                              sort_keys=True), encoding="utf-8")
    print(json.dumps({"tally": tally, "n": n,
                      "decision_match": report["decision_match"],
                      "cert_match": report["cert_match"],
                      "cert_selfcheck_ok": report["cert_selfcheck_ok"],
                      "verdict": report["verdict"]}, indent=1,
                      ensure_ascii=False))
    print("artifact:", OUT)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
