"""shadow --- 影子工程根（#K2-358/359：引擎在链外副本上跑，绝不碰真源/冻结四源）。

机制（env 驱动 · 零生成器改动）：`pm_gate.config.discover_project_root()` **优先读** `PM_GATE_PROJECT_ROOT`
⇒ 构造一个影子根，其 `pm_gate/project.yaml` 与 `pm_gate/artifacts/k2_v4/{L2,L3}` 指向（符号链接）真源，
**只把要被场景改动的文件做成真副本**（放置源 / SPEC）。真仓的 `hw/`、`_shared/` 由脚本自身 ROOT 解析，不受影响。
"""
from __future__ import annotations
import json, os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REAL = os.path.join(ROOT, "pm_gate")
L2_REAL = os.path.join(REAL, "artifacts", "k2_v4", "L2")
L3_REAL = os.path.join(REAL, "artifacts", "k2_v4", "L3")
PLACEMENT_NAME = "PLACEMENT_SOLUTION_v1.json"


def build(shadow_root, spec_name=None, replace=("placement",)):
    """建影子根。replace: 哪些文件要做真副本（可改）；其余一律符号链接到真源。"""
    for sub in ("pm_gate/artifacts/k2_v4/L2", "pm_gate/artifacts/k2_v4/L3"):
        os.makedirs(os.path.join(shadow_root, sub), exist_ok=True)
    yml = os.path.join(shadow_root, "pm_gate", "project.yaml")
    if "project_yaml" in replace:
        txt = open(os.path.join(REAL, "project.yaml"), encoding="utf-8").read()
        if spec_name:
            import re
            txt = re.sub(r"^spec_name:.*$", "spec_name: %s" % spec_name, txt, flags=re.M)
        open(yml, "w", encoding="utf-8").write(txt)
    else:
        _link(os.path.join(REAL, "project.yaml"), yml)
    for name in os.listdir(L2_REAL):
        src, dst = os.path.join(L2_REAL, name), os.path.join(shadow_root, "pm_gate/artifacts/k2_v4/L2", name)
        if name == PLACEMENT_NAME and "placement" in replace:
            shutil.copy2(src, dst)
        else:
            _link(src, dst)
    dstL3 = os.path.join(shadow_root, "pm_gate/artifacts/k2_v4/L3")
    for name in os.listdir(L3_REAL):
        _link(os.path.join(L3_REAL, name), os.path.join(dstL3, name))
    return {"shadow_root": shadow_root, "spec_name": spec_name, "replaced": list(replace),
            "placement": os.path.join(shadow_root, "pm_gate/artifacts/k2_v4/L2", PLACEMENT_NAME)}


def _link(src, dst):
    if os.path.islink(dst) or os.path.exists(dst):
        return
    os.symlink(src, dst)


def edit_placement_at(shadow_root, refs, delta_mm):
    """场景：把影子副本里 refs 的坐标整体位移。返回逐件旧→新（不碰真源）。"""
    p = os.path.join(shadow_root, "pm_gate/artifacts/k2_v4/L2", PLACEMENT_NAME)
    d = json.load(open(p, encoding="utf-8"))
    rows = []
    for r in refs:
        done = False
        for key in ("refs", "components", "placements"):
            blk = d.get(key)
            if isinstance(blk, dict) and r in blk and isinstance(blk[r], dict) and "at" in blk[r]:
                old = list(blk[r]["at"])
                # keep every trailing element (rotation etc.) - the chain's loader expects (x, y, rot)
                blk[r]["at"] = ([round(float(old[0]) + delta_mm[0], 4), round(float(old[1]) + delta_mm[1], 4)]
                                + list(old[2:]))
                rows.append({"ref": r, "old": old, "new": blk[r]["at"]})
                done = True
                break
        if not done:
            rows.append({"ref": r, "old": None, "new": None, "missing": True})
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return {"placement_file": p, "refs": refs, "delta_mm": delta_mm, "moves": rows,
            "real_source_untouched": True}
