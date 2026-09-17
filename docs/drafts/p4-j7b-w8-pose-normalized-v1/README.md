# J-7b / W-8「放置帧归一」· ENG 起草区（**未安装；`k2/tools/` 安装件未动**）

## 0. 缘起（实测，非推测）

`k2/tools/k2_w8_footprint_audit_v1.py`（sha `75404d706413d546`）在 `pad_sig()` 里直接比**文件内存储值**
（`GetFPRelativePosition()` / `GetOrientationDegrees()`）。这在两种**放置约定**下会误报：

| 约定 | 板 `.kicad_pcb` 存 | `.kicad_mod` 存 | 后果 |
|---|---|---|---|
| footprint 有**旋转** | pad 朝向 = **绝对**（含 `fp_rot`） | pad 朝向 = **局部**（FootprintSave 已减 `fp_rot`） | `rot` 字段假差异 |
| footprint 在**背面** | pad 偏移/朝向按**镜像后**坐标系存 | 库件存**正面局部** | `dy`/`rot` 假差异 |

**实测证据**（对象 = ⑦ 候选板 `f93a1698adcf4863` + 按板重建快照库）：
`n_electrical_diff` 由基线 31 降至 **8**，且该 8 件经**独立物理等价检查**（库件按板上位姿放置后比
绝对 pad 几何）**全部等价** ⇒ 8 件全为上述约定误报；同一独立检查在基线上得 33/33 **物理不同**
（基线 33 件全为真实 land pattern 差异）⇒ 归一不掩盖真差异。

## 1. 本草案

`w8_audit.draft-v2.py` sha256 前16 = **`34b83cff5fe8ade7`** = v1 的**最小外科改动**：

```python
_SCRATCH = pcbnew.BOARD()

def posed_pad_sig(fp, lfp):
    _SCRATCH.Add(lfp)
    try:
        lfp.SetOrientation(fp.GetOrientation())
        lfp.SetPosition(fp.GetPosition())
        if fp.GetLayer() == pcbnew.B_Cu:
            lfp.Flip(fp.GetPosition(), False)      # 背面镜像
        return pad_sig(lfp)                        # 在「放置帧」内取电气签名
    finally:
        _SCRATCH.RemoveNative(lfp)
```
（仅替换 `lib = pad_sig(lfp)` → `lib = posed_pad_sig(fp, lfp)`；其余口径/输出 schema/`board_sha16`
证据陈旧 fail-closed 全同 v1。）

## 2. 正 / 负控（三条，全部实跑）

```bash
cd /home/fila/jqdDev_2025/ic_hw
K=AppDir/usr/bin/python3.11; D=k2/docs/drafts/p4-j7b-w8-pose-normalized-v1/w8_audit.draft-v2.py
# ① 基线（仓库板 + 仓库库）—— 期望与 v1 逐件相同（不放松）
$K $D --board k2/hw/k2_v4_8L.l5.kicad_pcb --proj-lib k2/hw/lib --out-json /tmp/w8v2-base.json --out-md /tmp/w8v2-base.md
# ② ⑦ 候选（按板重建库）—— 期望 0/0
$K $D --board <CAND> --proj-lib <CAND_DIR>/lib --out-json /tmp/w8v2-cand.json --out-md /tmp/w8v2-cand.md
# ③ 负控：合成板（C73 pad1 宽 +0.05mm）—— 期望仅命中 C73
$K $D --board /tmp/opencode/lib7/land/mutant.kicad_pcb --proj-lib <CAND_DIR>/lib --out-json /tmp/w8v2-mut.json --out-md /tmp/w8v2-mut.md
```

| 案 | v1 安装件 | v2 草案 | 说明 |
|---|---|---|---|
| ① 基线 | `31 + 2`（33 件） | **`31 + 2`（33 件，逐件相同）** | **不放松判据**：真实差异一件不漏 |
| ② ⑦ 候选 | `8 + 0`（8 件，全为约定） | **`0 + 0`** | 归一后 J-7b ⇒ PASS |
| ③ 合成负控（C73 +0.05mm） | `9 + 0`（8 伪 + C73 真） | **`1 + 0`（恰 `['C73']`）** | 真差异仍被抓 |

## 3. 待监理裁定（**ENG 不自行改判据语义**）

1. **采纳/驳回**放置帧归一（属「判据语义澄清」，监理职权；ENG 只起草 + 交正负控）；
2. 若采纳：由 gate 属主侧 **版本 bump 安装**到 `tools/`（或 `criteria/` 侧消费口径）+ 监理登记 sha 与锚 rev；
3. 若不采纳：`lib_electrical_level` 的 8 件差异须由监理另定口径（否则该维恒 FAIL，但差异已证明**非 land pattern 问题**）。

**未动**：`k2/tools/k2_w8_footprint_audit_v1.py` · `criteria/` 两份 · SPEC · 板/库/判据安装件。
