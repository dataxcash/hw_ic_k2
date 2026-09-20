# MANIFEST · **新 rev `l8` P4 重锚册**（canonical 19 · 判据 rev=6 在岗）· 监理 #K2-57 R3

- 受审板：`k2/hw/k2_v4_8L.l8.kicad_pcb` **`7a5c89913d6e5d0a`**（本册测量件 `board_sha16` 须与之相等；不等 ⇒ 判定器 fail-closed）
- 配套 pro：`k2/hw/k2_v4_8L.l8.kicad_pro` **`c009058005829f09`**
- SPEC 锚：`L3/SPEC_k2_v4.spec-rev-53.json` **`4e92b3a05cd5a223`**（`pm_gate/project.yaml::spec_name` 指针）
- 网表：`hw/data/k2_sch.errata-3.yaml` **`5dc7b82a901d11c8`**（pin 映射订正；`k2_sch.yaml dd794c54` 逐字节未改）
- 判据：**rev=6 COUNTERSIGNED**（`criteria/manifest.k2.yaml 727d09953cf9bd78` · `adjudicate.py 1937a40ae68bc288` · `CHANGELOG eb3da49f2ad97e37`）；阈/维 **一字未动**
- **标准调用 verdict**：**19 OK / 0 FAIL · `passed=True` · `provisional=False`**（`verdict_19dim_rev6_board_l8_7a5c8991.json`）
- **链**：`k2_gen_v5 bc5dbda29cb06da0` → `k2_route_segment_v1 f28a4b5a --upto all`（与 l7 **同版链**）
- **保真对照**：同链于未订正 nets（errata-2）跑 ⇒ `c5a7df90aadb66e0` = 在岗 l7 **逐字节同** ⇒ 本 rev 差异（唯一 4 条 pad→net：`U4/2,3` + `D1/1,2`）**可完全归因输入变更**

| 件 | sha16 | bytes |
|---|---|---|
| `density_board_l8_7a5c8991.json` | `6d973cb9a888d999` | 5,751 |
| `measure_raw_board_l8_7a5c8991.json` | `ae1c44d57fabd102` | 2,255,711 |
| `min_clearance_drc_board_l8_7a5c8991.json` | `1ef40d47f81f708e` | 1,529 |
| `pads_within_outline_board_l8_7a5c8991.json` | `f5c48128dffb0fa6` | 165,139 |
| `ref_plane_continuity_board_l8_7a5c8991.json` | `b7800f98cb3a1b1d` | 1,909,414 |
| `refplane_nonantipad_board_l8_7a5c8991.json` | `7daaebc50861784a` | 3,084 |
| `verdict_19dim_rev6_board_l8_7a5c8991.json` | `562b482fac5ee941` | 3,635 |
| `w8_audit_board_l8_7a5c8991.json` | `5a5cc20f2ec3f8f6` | 16,842 |

## 1. 读数（本册，与 l7 册前→后对照）

- **19 维**：`PASS` · 19 OK / 0 FAIL（l7 = 19/0）⇒ **无回退**
- **DRC（全新 work-dir）**：`error 0` · `unconnected 0` · verdict 内违规总 **170 全 warning**；未登记 warning 类型 **0/9**
- **drc_warning_dispositions**：9 类全登记（含 `lib_footprint_mismatch`）
- **出框**：AABB 0 · 接口件 0 · 真外框多边形 0（676 pad）
- **ref_plane_continuity**：`non_antipad_gap = 0.0 mm²` @R=0.5mm（antipad 20.9552 / split 0.0 / keepout 0.0062）；V3 名义全长覆盖 3795/3795 = 信息项
- **density_and_clearance**：10mm/frame_origin 峰值 **7**（≤8）· 最小铜间距 **0.10**（≥0.10）· 横带占用 **0.07586** · 孔环 0.075 · pad 到边 **0.38** mm
- **non45**：0/5180 · **zone_filled** 10/10 · **lib_electrical_level** 电气级差异 0（B 口径豁免 2）

## 2. fail-closed 自检（ENG 实跑）

- 本册扫 `board_sha16` 字段 **12** 处，与受审板 `7a5c89913d6e5d0a` 不等者 = **0** ⇒ **全一致**
- 测量件（w8/pads/v3/density/min-clearance/refplane-gap）**无顶层 `verdict` 字段** ⇒ 不得作 `--artifacts` 传入

---
—— ENG（ARCHER）· 2026-09-21 · 只读取证件（本册为 l8 之 P4 重锚；旧册 `E3-standard-call-l7-20260919/` 保留，各册不可逐数直比）
