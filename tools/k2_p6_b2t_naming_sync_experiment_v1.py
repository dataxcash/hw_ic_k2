#!/usr/bin/env python3
"""B2-T 最小修复稿（草案 / 仅影子）：翻译遗留 alloc 走廊 id + 测试按角色解析走廊。真源零改动。"""
import json, os, re, shutil

SH, B3 = "/tmp/opencode/shadow", "/tmp/opencode/shadow_b3"
NEW = {"J2_TO_U": "EAST_CHIP_TO_J2", "U_TO_MCIO": "WEST_MCIO_TO_CHIP"}

shutil.rmtree(B3, ignore_errors=True)
shutil.copytree(SH, B3, symlinks=True)

src = "/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/L3/model_solves/channel_alloc_v2/channel_alloc.json"
raw = open(src, encoding="utf-8").read()
for old, new in NEW.items():
    raw = raw.replace(old, new)
open("/tmp/opencode/legacy_alloc_translated.json", "w", encoding="utf-8").write(raw)
print("translated alloc | 旧 id 残留:", sum(raw.count(o) for o in NEW))

tp = os.path.join(B3, "shared/eda_core/tests/test_hs_route_model.py")
t = open(tp, encoding="utf-8").read()
m_alloc = re.search(r'K2V4_ALLOC = \(Path\([\s\S]*?"channel_alloc\.json"\)', t)
assert m_alloc, "K2V4_ALLOC 块未匹配"
old_alloc = m_alloc.group(0)
helper = '''K2V4_ALLOC = Path("/tmp/opencode/legacy_alloc_translated.json")   # B3-DRAFT

# ── B3-DRAFT：按「角色」解析走廊（旧角色名 → 现行 SPEC id）；判定强度不变 ──
_CORRIDOR_ALIASES = {"J2_TO_U": ("EAST_CHIP_TO_J2", "J2_TO_U"),
                     "U_TO_MCIO": ("WEST_MCIO_TO_CHIP", "U_TO_MCIO")}


def _cid(role: str) -> str:
    spec = json.loads(Path(K2V4_SPEC).read_text(encoding="utf-8"))
    for cand in _CORRIDOR_ALIASES.get(role, (role,)):
        for c in spec.get("corridors", []):
            if c.get("id") == cand:
                return cand
    return role


def _corr(m, role: str):
    want = _CORRIDOR_ALIASES.get(role, (role,))
    for c in m.spec["corridors"]:
        if c.get("id") in want:
            return c
    raise LookupError(f"corridor role {role} 未在 SPEC 找到")'''
t = t.replace(old_alloc, helper, 1)
pat = re.compile(r'next\(c for c in m\.spec\["corridors"\]\s*if\s*c\["id"\]\s*==\s*"([A-Z0-9_]+)"\)')
t, n = pat.subn(lambda m: f'_corr(m, "{m.group(1)}")', t)
t = t.replace('m._track_y_for("PCIE_UP0_P", "U_TO_MCIO", "input")',
              'm._track_y_for("PCIE_UP0_P", _cid("U_TO_MCIO"), "input")')
t = t.replace('assert res["corridor"] == "J2_TO_U"',
              'assert res["corridor"] in ("EAST_CHIP_TO_J2", "J2_TO_U")')
t = t.replace('"corridor_id": "J2_TO_U", "band": "upper",',
              '"corridor_id": _cid("J2_TO_U"), "band": "upper",')
open(tp, "w", encoding="utf-8").write(t)
left = len(pat.findall(t))
print(f"test draft applied | 角色解析替换 {n} 处 | 残留旧 id 查找 {left}")
