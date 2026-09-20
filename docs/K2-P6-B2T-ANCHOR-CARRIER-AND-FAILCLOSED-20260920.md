# K2 · B2-T 续作 · **测试锚承载形态验证 + B1 同族 fail-closed 普查**（ENG / ARCHER · 只读）

> 机读：`k2/pm_gate/artifacts/k2_v4/P6_execution/B2T_FAILCLOSED_SWEEP_v1.json`
> 生成：`python3 k2/tools/k2_p6_b2t_anchor_and_failclosed_v1.py --verify-determinism`
> 真源零改动（只读 `k2/_shared`、`k2/hw`、`criteria/`；重放输出落 /tmp）

## 1. 测试锚承载形态验证（① ，ledger 排队项 a）

| 观测 | 重放（今日：8L 板） | 仓库内 P3 报告（Sept-9） |
|---|---|---|
| board sha16 | fb07d25ac426ff84 | f6273de613f43d05 |
| input_fp | `ce5e470537cdbb4d807618b55b514ecc985f96ea38f590db6afe5f1facead755` | `5113681d4d3256f53d6b0e928d2945e2054c741aa8b484e9b3bd4f61c1fe7d64` |
| capacity | INFEASIBLE（bottleneck TRACK） | — |
| alloc | **0 条 / 0 SOLVED** | 34 条 / 34 SOLVED |
| 与 Sept-9 载体逐字节同 | **False** | — |

**结论**：`k2/k2_v4.kicad_pcb` 现为符号链接 → `hw/k2_v4_8L.kicad_pcb`（2026-09-16 建），而 Sept-9 P3 报告
记录的 `board.sha256 = f6273de613f43d05`（其自记 `sha_expected = 6c387dff`，**当时即已板身份不符**）
⇒ **测试锚不能"运行期自建"**（今日输入下 alloc 阶段 0 解）。
锚迁移只能走 **(i) 具名承载**（登记该冻结载体 + 血缘/版次）或 **(ii) 合成现行 fixture**（保性质）。
仓库内 P3 报告未被本次重放改写：**True**。

## 2. fail-closed 普查（②，ledger 排队项 c）

静态（`min/max` over 推导式 + `next` 无 default，共 15 处）：

| 行 | 代码 | 判定 |
|---|---|---|
| 397 | `src_corr = next((c for c in spec.get("corridors", [])` | 已守卫（紧接 `if src_corr is None: return None`） |
| 401 | `src_tys = next((b.get("tracks_y") or [] for b in src_corr.get("bands", [])` | 已守卫（405 `if src_tys is None or tgt_tys is None: return None`） |
| 403 | `tgt_tys = next((b.get("tracks_y") or [] for b in tgt_corr.get("bands", [])` | 已守卫（同上） |
| 416 | `tgt_band = next(b for b in tgt_corr.get("bands", [])` | 已守卫（前一步 None 判定后使用） |
| 744 | `seg = next((r for r in solved if r["status"] == "SOLVED"` | 有 default（跨行 `, None)`）+ 显式 None 判定（非 B1 同族） |
| 803 | `corr = next((c for c in self.spec.get("corridors", [])` | 有 default（跨行 None）+ 调用侧判定 |
| 2547 | `corridor = next((c for c in self.spec.get("corridors", [])` | 有 default（跨行 None）+ 调用侧判定 |
| 2721 | `corridor = next((c for c in self.spec.get("corridors", [])` | 有 default（跨行 None）+ 调用侧判定 |
| 2936 | `gap = min(b - a for a, b in zip(ys, ys[1:]))` | 已守卫（len(ys) < 2 → 2.0） |
| 2948 | `mw = max((d["half_w"] for d in reds.values()), default=0.0)` | 有 default（0.0） |
| 2949 | `mh = max((d["half_h"] for d in reds.values()), default=0.0)` | 有 default（0.0） |
| 3077 | `min_chip_x = min(c["x"] for c in chip_ends)` | 已守卫（if chip_ends:） |
| 3136 | `x_l = min(s["end_left"]["x"] for s in segs` | **未守卫 ⇒ 缺陷 B1**（本轮已定位；影子守卫已验证） |
| 3138 | `x_r = max(s["end_right"]["x"] for s in segs` | **未守卫 ⇒ 缺陷 B1**（同处 x_r） |
| 4607 | `idx = next((i for i in range(len(new_path) - 1)` | 有 default（0） |

动态（33 个 API 调用 × 2 载体）：

| 载体 | API | 异常 |
|---|---|---|
| p3_alloc_sept9 | link_topology_map | ValueError: min() arg is an empty sequence |

**结论**：唯一抛异常 = `link_topology_map`（**缺陷 B1**，现行 schema 载体）；其余 API 均 fail-closed 返回
状态（`INFRA_ERROR`/`NO_CORRIDOR`/`INSUFFICIENT` 等）。⇒ B1 为**单点缺陷**，非系统性崩溃面。
确定性两跑：**MATCH**。

## 3. 待监理裁定（不阻塞，属批2 授权面）

1. 锚承载形态：**(i) 具名冻结载体** vs **(ii) 合成现行 fixture**（ENG 建议：能力类断言走 (ii)，
   契约/结构类可走 (i)）。
2. B1 守卫（`_shared` 2 处 fail-closed）——影子已验。
3. A1–A12 期望重基线批。

—— ENG（ARCHER）· 2026-09-20 · 引擎 sha16 `b6f88d35bc0669e4` · 阶段：**P6 未开（只出计划件）**
