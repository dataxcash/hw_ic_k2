#!/usr/bin/env python3
"""K1 批 6 · 把两个**只读影子**固化成可复核补丁（供 R-1/R-3 裁定用；不落件）。

产物（写入 BATCH6_DRAFT/）：
  ① `BATCH6_CORRECTED_BASELINE_v1.patch`（容器 `_shared` → 修正基线 shadow）
     = D-1（段级 P/N 门搬到**拼接后**的段对象上）· D-2（阈值 = 线宽 + 项目 p_gap）
       · D-3（段级违规不得被 base 级掩盖：base 门下沉为段级）· D-4（累积门下沉为逐段）
       · D-5（逃逸候选起点层须 ∈ 焊盘铜层）· ④零长段守卫 · ⑤端点对齐模板
       · (d) 直接对角线候选 · ⑥对级双向耦合
  ② `BATCH6_VG_PAIRAWARE_v1.patch`（修正基线 → VG 对级化）**R-3 落件候选本体**

只读：本件不写 `_shared`/`criteria`/冻结件；只在 k2 侧写这两个 patch（draft）。
用法：cd <容器根> && python3 <本件>
"""
import hashlib
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
NEW = os.path.join(HERE, "BATCH6_DRAFT/BATCH6_CORRECTED_BASELINE_v1.patch")
NEW2 = os.path.join(HERE, "BATCH6_DRAFT/BATCH6_VG_PAIRAWARE_v1.patch")
REL = "_shared/eda_core/hs_route_model.py"
SHADOW_D5 = "/tmp/opencode/k2side/tree_d5"
SHADOW_VG = "/tmp/opencode/k2side/tree_vg"
NEW3 = os.path.join(HERE, "BATCH6_DRAFT/BATCH6_VG_PAIRAWARE_v2.patch")
SHADOW_VG2 = "/tmp/opencode/vgscope/best_of"   # 由 k1_vg_pairaware_scope_probe_v1.py --only best_of 产出


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def mkpatch(old, new, out):
    r = subprocess.run(["diff", "-u",
                        "--label", "a/" + REL, "--label", "b/" + REL,
                        old, new], capture_output=True, text=True)
    if r.returncode not in (0, 1):
        raise SystemExit("diff 失败: %s" % r.stderr)
    open(out, "w").write(r.stdout)
    return len(r.stdout)


def verify_applies(patch, dst_root, expected_sha16):
    """在临时树根上 `git apply -p1` ⇒ 结果 sha 须逐字节 == 期望（可复现守卫）。"""
    with tempfile.TemporaryDirectory(prefix="pgen_") as tmp:
        sub = os.path.join(tmp, "_shared/eda_core")
        os.makedirs(sub)
        base = os.path.join(dst_root, REL)
        # 头部上下文行的来源文件：patch 的 “a/” 侧 = 该树的上一态
        import shutil
        shutil.copyfile(base, os.path.join(sub, "hs_route_model.py"))
        r = subprocess.run(["git", "apply", "-p1", patch], cwd=tmp,
                           capture_output=True, text=True)
        if r.returncode != 0:
            return {"git_apply": "FAIL", "stderr": r.stderr.strip()[:300]}
        got = sha16(os.path.join(sub, "hs_route_model.py"))
    return {"git_apply": "OK", "sha16": got, "matches_expected": got == expected_sha16}


def main():
    data_root = os.getcwd()
    src_container = os.path.join(data_root, REL)
    if not os.path.isfile(src_container):
        raise SystemExit("容器 _shared 未找到（请在容器根跑）")
    for p in (SHADOW_D5, SHADOW_VG):
        if not os.path.isfile(os.path.join(p, REL)):
            raise SystemExit("影子缺失: %s" % p)
    s_d5, s_vg = sha16(os.path.join(SHADOW_D5, REL)), sha16(os.path.join(SHADOW_VG, REL))
    n1 = mkpatch(src_container, os.path.join(SHADOW_D5, REL), NEW)
    n2 = mkpatch(os.path.join(SHADOW_D5, REL), os.path.join(SHADOW_VG, REL), NEW2)
    n3 = None
    v2 = None
    if os.path.isfile(os.path.join(SHADOW_VG2, REL)):
        s_vg2 = sha16(os.path.join(SHADOW_VG2, REL))
        n3 = mkpatch(os.path.join(SHADOW_D5, REL), os.path.join(SHADOW_VG2, REL), NEW3)
        v2 = {"bytes": n3, "sha16_of_patch": sha16(NEW3), "target_sha16": s_vg2,
              "verify_from_corrected": verify_applies(NEW3, SHADOW_D5, s_vg2),
              "strategy": "best_of（两序都算，取通过修正门且 P/N 边缘净距更大者；已去 ⑥）"}
    out = {
        "artifact": "k1_corrected_baseline_patchgen",
        "purpose": "把两个只读影子固化成可复核补丁（draft，未落件）",
        "container_shared_hs_route_model_sha16": sha16(src_container),
        "patches": {
            os.path.basename(NEW): {"bytes": n1, "sha16_of_patch": sha16(NEW),
                                    "target_sha16": s_d5,
                                    "verify_from_container": verify_applies(NEW, data_root, s_d5)},
            os.path.basename(NEW2): {"bytes": n2, "sha16_of_patch": sha16(NEW2),
                                     "target_sha16": s_vg,
                                     "verify_from_corrected": verify_applies(
                                         NEW2, SHADOW_D5, s_vg)},
        },
        "readonly_repo": True,
        "not_landed": True,
    }
    if v2:
        out["patches"][os.path.basename(NEW3)] = v2
    print(__import__("json").dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
