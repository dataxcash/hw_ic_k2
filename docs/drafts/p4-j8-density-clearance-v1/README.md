# J-8 密度/间距（`density_and_clearance`）· ENG 起草区（**未安装；`criteria/` 未动**）

补齐 J-8 末项（登记册 §C J-8「密度分布 / 关键间距」；v2/v3 manifest 中恒为 `enabled:false, pending`）。

| 文件 | 说明 |
|---|---|
| `j8_dc_common.py` | 共用几何层（pad AABB 口径与 `measure_pads_within_outline.py` 同源） |
| `measure_density_and_clearance.py` | **测量件**（无 `verdict`）：多口径网格密度（5/10/20mm × 两种原点）· 三横带占用 · 异网 pad AABB 最小间隙 · 孔-孔 · courtyard · pad 到板边 · 工艺实达值 |
| `measure_min_clearance_drc.py` | **测量件**（无 `verdict`）：用 `kicad-cli pcb drc` 在 `/tmp` 副本上 bracket 全板最小铜间距（真值区间） |
| `adjudicate.draft-v4.py` | **v3 的严格超集**（diff = 3 hunk / 全为新增：2 个 `--*-json` 参数 · 2 处测量装载 · 1 个检查块） |
| `manifest.k2.v4.yaml` | **安装件**：`density_and_clearance` 仍 `enabled:false`（阈值待监理），但 `consume` 与阈值键已定 |
| `manifest.k2.control-v4.yaml` | **仅正负控用**（示例阈值；非政策提案、非安装件） |
| `run_controls_v4.py` | 七案正负控驱动（A/B/C/D/E/F/G） |

## 跑法

```bash
cd /home/fila/jqdDev_2025/ic_hw
K=AppDir/usr/bin/python3.11; D=k2/docs/drafts/p4-j8-density-clearance-v1
B=k2/hw/k2_v4_8L.l5.kicad_pcb; P=k2/hw/k2_v4_8L.l5.kicad_pro
# ① 两件测量（fail-closed 前置）
$K $D/measure_density_and_clearance.py --board $B --json /tmp/opencode/dc/dc.json
python3 $D/measure_min_clearance_drc.py --board $B --pro $P --kicad-cli AppDir/bin/kicad-cli \
    --work-dir /tmp/opencode/dc/clr --json /tmp/opencode/dc/mc.json
# ② 判定（v4）
python3 $D/adjudicate.draft-v4.py --board $B --manifest $D/manifest.k2.v4.yaml --pro $P \
    --nets k2/hw/data/k2_sch.errata-1.yaml --sch-dir k2/hw/sch --drc-cli AppDir/bin/kicad-cli \
    --density-json /tmp/opencode/dc/dc.json --min-clearance-json /tmp/opencode/dc/mc.json
# ③ 正负控（七案矩阵）
python3 $D/run_controls_v4.py
```

## 阈值键（`thresholds.density_and_clearance`；**归监理**）

| 键 | 必填 | 语义 |
|---|---|---|
| `cell_mm` | ✅ | 网格边长（建议 10） |
| `cell_origin` | ✖ | `absolute_zero`（默认，复现登记提案）或 `frame_origin`（以板框左下为原点） |
| `max_fp_per_cell` | ✅ | 件/格上限 |
| `min_copper_clearance_mm` | ✅ | 全板最小铜间距下限（DRC bracket 真值） |
| `max_band_occupancy_ratio` | ✖ | 三横带最大占用比上限（M-12 口径明确定义版） |
| `min_via_annular_mm` | ✖ | 最小孔环下限 |
| `min_pad_to_edge_mm` | ✖ | pad 到板边最小距离下限 |

**fail-closed**：测量缺件 / 两 JSON 的 `board_sha16` ≠ 受审板 / **必填阈值未给** ⇒ 一律 FAIL（不假装实现、不缩口径）。

## 口径说明（ENG 不择一）

- 网格原点会改变峰值：本板 10mm 格 = **5**（`absolute_zero`，复现登记提案）vs **7**（`frame_origin`）⇒ 由监理择一。
- 三横带占用（焊盘 AABB 并集 ∩ 带 / 带面积）= **4.78% / 7.59% / 2.19%**；登记册 M-12 的「19–27%」口径仍须监理补定义（S-6a）。
- 异网 pad AABB 间隙 = **保守下界**（真值 ≥ 本值）；全板真值由 DRC bracket 给（本板 ∈ **[0.100, 0.105] mm**）。

详见 `k2/docs/K2-P4-J8-DENSITY-CLEARANCE-MECHANISM-EVIDENCE-v1.md`。
