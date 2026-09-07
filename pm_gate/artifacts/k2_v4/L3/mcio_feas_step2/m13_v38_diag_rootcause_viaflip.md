# M14 v38 极性诊断 — via 换层 flip 排序根因（实测钉死）

> 承接：m13_v38_plan_polarity_invariant.md + m13_v38_capacity_gate_record.md。
> 本文件 = 前台实测诊断（非结论定稿），锚定 v38 计划 Step1-3 的精确改造点。
> 纪律：全前台自跑、禁 task()、禁后台、禁暴力迭代；每步原始数据贴出不加工。

---

## 0. 一句话结论

v38 计划"轨道 `_expand_pair` 写死 P上N下"是**次生**矛盾，非最上游根因。
最上游根因 = **芯片侧(U7) BGA 极性位序交错**（N_top/P_top 每 base 不同），
v4 求解器在 `_escape_pair` 的 via 换层分支用 `_escape_expand` 的**中心线对称展开**
把 P/N 锚到中心轴，但 pad 实际位序（P/N x 偏移）与该展开背离，导致 flip=True 时
出口 P/N 排序 → 相向交叉（min_edge -0.2050）。

---

## 1. 探针原始数据（-0.2050 交叉定位）

### 1.1 第 1 次全量（带 chip_landing 接通，v38 依据）
```
status: PARTIAL  solved=[PCIE_UP1]  infeasible=[其余17]  solve_time_s=98.858
```
失败原因 tally（collected from hs_rebuild_summary.json）：
- 12× via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min_edge -0.2050）
- 5× 左逃逸对级失败(flip=True) 落点净空校验失败
- 14× OTHER（段级跨段未归类）
→ **结论：接通 chip_landing 后 solved 仍=1，非数据流断层，是 flip 排序本身**

### 1.2 代表 base: PCIE_DN2 / out_MCIO 段（精确坐标）
```
段 net: PCIE_DN_OUT2_P_MCIO / _N_MCIO    track_y=60.7  corridor=EAST_CHIP_TO_J2
交叉点: (57.105, 45.563)   min_edge=-0.2050
左端 pad: P=(57.10,45.75)  N=(56.50,45.75)   → 连接器侧 P-右/N-左（x 序）
右端 pad: P=(87.00,52.37)  N=(87.40,51.67)   → 芯片侧(U7) N-top（y 序）
```

### 1.3 走廊窗口净空探针（关键：窗口不对称被证伪）
```
track_y=60.7, F.Cu field, 采样 x∈[57.105,58,60,62,64]
flip=False (P=+0.19,N=-0.19): P_ok=True N_ok=True  5/5 净空
flip=True  (P=-0.19,N=+0.19): P_ok=True N_ok=True  5/5 净空
→ 走廊窗口两侧 flip 均净空，窗口不对称非真凶（Oracle 假说排除）
```

### 1.4 逃逸展开原始点（DN2 out_MCIO 左端，_escape_expand 中心线展开）
```
pad P=(57.10,45.75)  pad N=(56.50,45.75)   mid=(56.80,45.75)
中心线 cl=[(56.80,45.75),(57.105,45.75),(57.105,60.7)]
_escape_expand 展开(s按pad_p定向):
  P展开=[(56.80,45.94),(56.92,45.75),(56.91,60.70)]
  N展开=[(56.80,45.56),(57.29,45.75),(57.29,60.70)]
→ P 展开 x 收敛到 56.9，N 收敛到 57.29 —— 但 pad 实际 P=57.10/N=56.50（P右N左）
  展开 P/N x 序 = P左N右，与 pad 实际 P右N左 **相反** → 展开段初始即反向
→ flip=True 出口排序强制 P=-0.19(下)/N=+0.19(上)，与轨道段(P上N下硬编码)
  相向 → 交叉 -0.2050
```

---

## 2. 根因（分层）

| 层 | 矛盾 | 越上游 |
|---|---|---|
| L3 芯片侧 | U7 P/N y 位序交错（DN0/1/4/5=N_top, DN2/3/6/7=P_top） | 物理真值 |
| L2 轨道侧 | `_expand_pair` 写死 P=track_y-0.19(上) N=+0.19(下) | 写死 |
| L1 逃逸侧 | `_escape_expand` 中心线对称展开背离 pad 实际位序 → flip 双向相向交叉 | 次生 |

**病根 = `_escape_pair` via 换层分支的展开（`_escape_expand` + `_sym_via`）**
在 pad 对 P/N **x 分离**（P右N左，如 MCIO 连接器侧）时，`_escape_expand` 以 pad
中点 m_x 做中心线对称展开，P/N 垂直段 x 收敛到 m_x±0.19，而非各自 pad x。
这使 P/N 在走廊收敛处相向交叉（min_edge -0.2050）。**flip 双向均交叉**
（flip=False @ corridor, flip=True @ pad 级）——与 flip 无关，是展开锚定错误。

---

## 2.5 修复机制（实测验证，决定方向）

**核心修复：P/N 各锚定自身 pad x（不再收敛到 m_x）**。
- 在 pad x 分离场景，`_escape_expand` 让 P 垂直段 x=pad_P.x、N 垂直段 x=pad_N.x，
  via 沿各自 pad x 定位，轨道轨各接各的 y（flip 仍派生）。
- **实测（DN2 out_MCIO，纯前台）**：
  ```
  pad P=(57.10,45.75) N=(56.50,45.75)  track_y=60.7  corridor=EAST_CHIP_TO_J2
  ALT-via pad-x 构造: flip=False min_edge=0.395 | flip=True min_edge=0.395  (>0.175 无交叉)
  ```
- **回归风险（已实测暴露）**：在 `_escape_pair` 共享路径全员启用 pad 锚定，
  会改变 `_probe_escape_region_pair` 的形态枚举结果（H-V via 分支变为 SOLVED，
  L-H-V 取代 LSWAP）→ `test_probe_region_lswap_integration` 回归
  （断言 form.kind=='LSWAP'，现得 'L-H-V'）。
  纯前台验证：改后 test_hs_route_model = 8 failed（基线 7 failed + 1 新增 lswap）。
  加 **horiz_sep 条件化（仅 |P.y−N.y|<0.2 水平分离才锚定）** 后回归消失
  （7 failed 维持，26 passed→无新增）。
- **收敛结论**：pad 锚定方向对，但需条件化（仅水平 x 分离 pad）。

---

## 2.6 ⚠️ 更上游根因（重大修正，实测铁证）

在验证 pad 锚定过程中，进一步实测发现 **唯一失败段（DN2 out_MCIO）的真正
上游病根不是极性，而是「通道分配把该段分配给 N 半轨被低速 pad 挡死的轨道」**：

```
DN2 out_MCIO 分配 track_y=60.70（band dn）
  P 轨(60.51) 全净空 | N 轨(60.89) 在 x=58/62/64 被 GND/NO_CONNECT pad 0.135 挡死
  （0.135 < 0.175 净空）→ N 轨永远 seg_ok=False → LSWAP_v 预检(L1817) 恒败 → 逃逸全败

同 band 净空轨道（P/N 双轨全 clear）：
  track_y=58.30 ✓ | 59.50 ✓ | 63.10 ✓ | 65.50 ✓ | 66.70 ✓（60.70/61.90/64.30 ✗）

实测：DN2 out_MCIO 改 track_y=58.30/63.10/59.50 → LSWAP_v 立即 SOLVED（两 flip 均解）✅
```

**系统性扫描（18 base 全段）**：21 个 base-段因分配轨道 P/N 半轨被占而失败
（UP input/out_J2、DN input/out_MCIO、REFCLK0/1 全族一致）。条理规律：
**channel_alloc 给高速对分配的 track_y 行经的 P/N 半轨有多处被低速/电源/
NO_CONNECT pad 挡死**。这是**全局分配缺陷**，非极性。

**与既有记录相左**：m13_v38 记录 R3 判"失败根因 = P/N 极性错配"——本 session
实测证伪该结论（至少对全部 failed 段），**真根因 = channel_alloc 选道未验证
P/N 双轨净空（分配了被占轨道）**。D2 段廊道净空验证（channel_alloc
`_candidate_window_validation`/`corridor_window_ok`）需 `static_sources`+
`half_pitch` 注入才生效；`/tmp/alloc_v33e`（v33 旧产物）无 `_track_validation`
键 → D2 未启用。现行 e2e `run_alloc` 会注入，需以现行管道重验。

---

## 3. 修改方向（待裁决定稿，勿写码）

### 方案 A（极性根因修复，条件化）
- `_escape_expand`（L1048）：当 `pad_n` 提供且 P/N 水平 x 分离（|P.y-N.y|<0.2）时，
  P/N 展开线 x 锚定各自 pad x；否则回退旧居中展开。`_escape_pair` flip 覆写 +
  corridor 起点 x 同条件化。**已实测无回归（horiz_sep 条件化）。**

### 方案 B（更上游根因，推荐优先验证）：channel_alloc 选道避让被占轨
- 现行 e2e 管道已注入 D2（`run_alloc`→`_candidate_window_validation`）；用现行
  管道重新生成 alloc，验证坏轨是否被 D2 跳过。若 e2e 产物仍含坏轨 → 查
  `_alloc_static_sources`/`_half_pitch` 注入是否真正生效（field None → D2 退化
  return True 会放过坏轨）。
- 目标：DN2 out_MCIO 改分 58.30/63.10 等净空轨。

### 排除（已证伪，勿改）
- 窗口 per-flip 对称化：§1.3 证伪（窗口两 flip 均净空）。
- 无差别 pad 锚定：§2.5 暴露 probe/LSWAP 回归——需 horiz_sep 条件化。

---

## 4. 下一步（决策后）
1. 优先验证方案 B：用现行 e2e 管道生成新 alloc，检查坏轨是否被 D2 拦截；
   若否，修 `_alloc_static_sources` 注入或 `_half_pitch` 推导（field/hp None 时
   D2 退化放过）。这是更上游且更彻底的根因修复。
2. 若 B 后仍有残余 → 叠加方案 A 条件化（pad 锚定）处理极性形态残余。
3. 单测：新增 pad 位序定向用例 + 既有 49 passed 零回归核对。
4. 第 2 次全量验证（plan 允许 ≤2，带依据）：18 SOLVED + skew<0.15 + P/N≥0.175。
5. 合规：ECN-009 unlock→备份→改→单测→lock→status 0/0/0。
