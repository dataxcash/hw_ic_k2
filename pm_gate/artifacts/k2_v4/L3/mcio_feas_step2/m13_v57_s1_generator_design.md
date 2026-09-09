# m13 v57 — S1 图纸生成器 设计细案（先交后码 · 开工门交付）

> 依据：DRAWING IRON LAW v57（L1-L7）+ m13_v57_execution_plan.md S1 + m13_v57_s0_gate_record.md。
> 状态：**设计细案（本文件为 S1 开工前交付物）**；编码不得先于本文件 commit。
> 输入真源（只读，单向）：S0 权威端点模型 `m13_v57_s0_endpoint_model.json`、
> SPEC `SPEC_k2_v4.json`（corridors/capacitor_walls/constraints）、DRC 规则 `drc_rules.json`、
> `route_model_config.json`、DS320 ballmap `ds320pr1601_ballmap.json`。
> 板文件/escape_spec/旧 landing 簿 = 被审派生物（L4），**永不进入本生成器输入**。

---

## 0. 术语与范围

- **图纸页（page）**：`(base, segname)` 唯一键的一段施工图。全 K2 = **34 页**。
- **图纸（drawing）**：34 页联合体（每页含：权威双端锚 + 全部几何节点 + 轨道/层声明）。
- **资源单元（resource unit）**：层上的离散独占槽位（列/隙/道/via 位）。图纸生成 = 把
  每页需求指派到资源单元，全部单元互不重叠 → 构造性合法。
- **守恒层（conservation layer）**：一类资源单元的集合 + 每页在该层上的需求。
  联合可行 = 各层同时可行。
- **证书（certificate）**：不可行时输出的最小不满足集（层 + 资源 + 需求子集 +
  冲突证据），机器可读、逐字节确定。
- **本设计不含**：solve 几何执行细节、DRC 驱动、逃逸形态微调、施工连连看（S2）、
  设计层接口文档（S3）。边界=生成器本体 + 其机器验收（A1.1-A1.4）。

### 0.1 页清单（34 = 16 输入 + 16 输出 + 2 REFCLK，机器派生见 `m13_v57_s1_page_manifest.json`）

| 族 | 页键 `(base, segname)` | 芯片侧球族（出逃侧） | 走廊 | 对端连接器 |
|---|---|---|---|---|
| PCIE_DN0-7 / input | A_PER（东出） | EAST_CHIP_TO_J2 dn | J2 TX0-7 |
| PCIE_DN0-7 / out_MCIO | A_PET（西出） | WEST_MCIO_TO_CHIP dn | J3(RX0-3)/J4(RX0-3) |
| PCIE_UP0-7 / input | B_PER（西出） | WEST_MCIO_TO_CHIP up | J3(TX0-3)/J4(TX0-3) |
| PCIE_UP0-7 / out_J2 | B_PET（东出） | EAST_CHIP_TO_J2 up | J2 RX0-7 |
| PCIE_REFCLK0-1 / input | 无芯片端（直通） | EAST+WEST refclk | J2 ↔ J3(0)/J4(1) |

页键派生规则（脚本 p3_v57_s1_page_manifest.py，双跑字节一致）：
- 数据页 32：对每个 chip 网 `PCIE_{stem}`，按 corridor 成员关系配对 `(chip_net, conn_net)`；
  `segname` = `input`（conn 端 = J2 的 TX/RX = 芯片输入侧链路）| `out_J2`（J2 的 RX 输出）|
  `out_MCIO`（J3/J4 RX 输出）。**判别只用网表全链名 + SPEC corridor band 成员，零坐标反猜。**
- REFCLK 页 2：`PCIE_REFCLK{k}`，双端 = 两连接器（J2 & J3/J4），芯片端 = 无。

> 工件 `m13_v57_s1_page_manifest.json` 落 34 页：`{page_id, base, segname, kind,
> side(chip 出逃侧或 conn pass), corridor_id, band, nets{P,N}, anchor{chip{...}|null,
> conn{ref,pad}, }, req_layers}`。全部锚坐标来自 S0 端点模型字段（chip=expect_xy；
> conn=at_global_est），不读取 k2_v4.kicad_pcb。

---

## 1. 资源层编码（R1-R4，全部由权威端点 + 规则派生）

四个资源层与 K2 物理一一对应。**候选单元集合的构造 = 纯几何推导**（球阵/连接器
列几何 + 放置变换 + 净空/间距规则），**零板文件窗口扫描、零 max-x 取端**（V1 关闭）。

### R1 — 芯片出逃列域（chip escape column domain）

- **定义**：芯片每侧（东 = 廊道入口 x≈105.25；西 = 廊道入口 x≈82.35）每个数据球
  的 F.Cu→In2 via 可落列集合。每差分对占用 **2 列**（P/N 各一），对列错距 ≥ 0.36
  （列对最小间距，防 P/N 竖腿净距违例，> p_width+clearance = 0.205+0.175）。
- **推导**（权威，非窗口）：
  1. 球位 = `expect_xy`（S0：ballmap×放置变换，已与板 pad 64/64 对证）；
  2. 阻挡集合 = 同球列/相邻列上异网球铜（GND/信号/N-C），球铜半径取 ball
     `~=0.2`(solder) 且以 DRC clearance 0.175 + 半线宽 0.1025 膨胀为禁列条件
     （净空口径 = clearance + half_track，引擎 escape_check 同源）；
  3. 域 = 出逃方向 0.15..1.5mm 区间按 0.05 步离散列 ∩ 禁列补集 ∩ 对列错距约束。
- **守恒条件（每域）**：每球恰 1 via 列；同侧同 y 带不同球域不重叠（球列中心距
  ≥0.3，域宽 ≤0.15 → 域天然互斥，例外经 0.05 步与净空判据裁决）；域空 = 该页
  chip 侧无资源。

### R2 — 走廊 lane（corridor track lane）

- **定义**：走廊（EAST x∈[105.25,132.65] / WEST x∈[65.05,82.35]）内带（dn/up/refclk）
  的纵向轨位。lane = 差分对中心线 y（P/N 展开 ±PAIR_HALF_PITCH=0.19）。
- **推导**（权威）：
  1. lane 集成员 = corridor band `nets` 列表（SPEC 注入的带成员，序号 = lane 序）；
  2. lane 中心 y 与 pitch = **守恒约束求解**：`n_pairs × pitch ≤ 带可用 y 跨度`，
     `pitch ≥ inter_pair 中心距`（capacity_audit 声明 1.46mm = 铜边 0.875 + 对宽
     0.205 + gap 0.175 + 对半 0.19×2 余量口径）；带间最小净空由 y 带边界检查。
     SPEC corridors 的 `tracks_y` 记录只作**对照参考**（v32 求解器反演值 = 派生物），
     生成器 lane 位置以规则 re-derive；若与记录差异 → 以守恒解为准（authority-first）。
  3. refclk lane：J2↔J3/J4 直通轨（2 lane，东/西走廊各复算），层 = 6L 有效内层
     （见 §2.3 层语义裁决）。
- **守恒条件**：同带同层 lane 两两 y 距 ≥ pitch；异带最小 y 距 ≥ 带隔离净空。
  每 lane 独占 = 每页恰占 1 lane（除 REFCLK 每页 1 lane 东 + 1 lane 西）。

### R3 — 连接器出逃隙（connector escape gap）

- **定义**：连接器焊盘墙 → 走廊的落点行隙。J2 双列（inner 132.65 / outer 135.0）
  0.6 pitch/37 行；J3/J4 MCIO A/B 列。隙 = 连接器 pad 的 F.Cu→In2（或 F.Cu 直连）
  落点/via 可放行区。
- **推导**（权威）：
  1. 每网连接器端 pad 中心 = S0 `at_global_est`（库/手册 pad#↔网名 + 放置变换）；
  2. 出逃方向/列序 = 连接器列相对走廊侧（J2 内侧列向左水平出、外侧列右绕 In2 —
     constraints.j2_escape_topology 注入语义）；MCIO A 列向走廊（AC 墙位于其间）；
  3. 隙候选 = pad 行 y ± 半行距内可落 via 的 x 列（经 pad/相邻 pad 铜 + 净空判据）。
- **守恒条件**：每 pad 恰 1 落点；同列相邻 pad 落点 y 距 ≥ via 外径 + clearance。

### R4 — AC 耦合墙穿越隙 + 内层穿越（west crossing / cap-wall slot）

- **定义**：西走廊数据对（MCIO out/UP in）在 AC 电容墙（C17-C32 down / C49-C64 up，
  0402，mcio_side_x∈[75,90]，min_center_pitch 1.3）上的逐对穿越隙 + 墙后 In2 段。
- **推导**（权威）：墙 pad 位 = SPEC `downstream_refs/upstream_refs` refdes ∩ 网名
  `_MCIO`（引擎既有 derive_cap_wall_pads 同语义，但 pad 锚取权威网表端而非 max-x
  板扫描）；每网恰 1 墙 pad = 出逃链强制节点；墙隙 = 以墙 pad 为中心的微净空域
  （escape_clearance 0.075 例内）。
- **守恒条件**：每墙 pad 网独占；同墙邻 pad 中心距 ≥ min_center_pitch（1.3mm 注入）
  → 墙隙按 pad 序天然互斥，跨网不竞争（几何由 SPEC 声明保证，判据防声明冲突）。

---

## 2. 每层守恒的联合判定（禁贪婪 / 禁顺序耦合的核心）

### 2.1 判定形状

34 页联合问题 = 对每页 `(base, segname)` 在 R1-R4 上取资源，且：
- **层内独占**：同层同带同列（R1/R3）或同 y 带（R2）资源不重叠；
- **层间几何传递**：页的 R1 列位必须与其 R2 lane 的 y 带相容（via2 落在 lane 起点的
  可达域内）——以**几何谓词**预计算为"页需求 × 层资源的允许关系"，不必联立搜索。

即：**联合可行性等价于四个独立计数/匹配问题**，每层判定为多项式守恒谓词
（容量 vs 需求 + 允许关系），**不做逐网搜索分配**。判定输出要么全层可行
（→ 直接进入确定性构造 §3 投影），要么给出**最小不满足集**。

### 2.2 序无关性论证（设计层证明，机器验证见 A1.2）

1. 判定层：谓词 = 纯函数 `feasible(inputs) ∈ {FEASIBLE, INFEASIBLE(core)}`，无内部
   枚举序依赖（容量条件写成闭式守恒不等式；允许关系预计算后为图匹配可行性，
   用确定性图算法一次求值）。因此**任意确定性枚举序不改变判定结果**。
2. 证书层：最小不满足集按**规范最小核**定义 —— 在同一偏序下做一次确定性
   删除式收缩（deletion-based core，删除序 = 固定键序），对同一输入输出唯一；
   对合成实例与穷举基准对照时，证书定义与基准的"最小"口径逐字节对齐。
3. 构造层（可行时）：§3 的发射规则为**纯坐标函数**——给定 (页, 已指派资源) 输出
   节点序列，无候选回退循环。指派本身在判定层已定（非贪婪逐网），因此
   正序/倒序/密度序枚举**只改变无关紧要的中间迭代对象，不改变输出字节**
   （实现约束：生成器输入聚合顺序统一 canonical sort，禁止在发射路径上
   依赖任何"首个可用"选择）。

### 2.3 层语义裁决（6L 有效层；关闭 SPEC 陈旧 In6 引用）

- 高速数据（32 页 chip 侧 + 走廊）层序：F.Cu（stub/出逃）→ In2.Cu（穿越/走廊承载）
  → F.Cu（连接器端 stub）。每线 ≤2 via（SPEC vias.high_speed）。
- REFCLK 页（2）直通：承载层以 **In2.Cu**（6L 有效内层）替代 SPEC corridors 中
  遗留的 In6.Cu 引用（层 plan 已声明 in6 删除，6L 栈 F/In1/GND/In2/In3/GND/In4/B）。
  此为"注入规则修正"，落 DESIGN-NOTE，不改模型输入文件。

---

## 3. 确定性构造规则（可行页 → 全节点图纸）

每可行页按页型模板发射**全部节点**（不搜索、不迭代回退）：

- **chip 侧（32 数据页）**：`pad(anchor) → F.Cu stub(≤1.5mm 直或 1 折) → via₁(F→In2,
  列位=R1 指派) → In2 竖/斜段至 lane 起点 → via₂`；stub 长度与形态 = 由 pad 与
  via₁ 列位差唯一决定（无候选选择）。
- **走廊段**：`lane 入口 (corridor bound_x, lane_y) → lane 出口（另一 bound）` 水平
  直线，P/N = lane_y ± 0.19（带内 P 上 N 下，方向与球列极性一致——极性 = 页内
  唯一定义，无 flip 选择）。
- **连接器侧**：`→ via₃(F→In2/或 F 直连) → F.Cu stub → pad(anchor)`（R3 落点）。
- **AC 墙（西数据页）**：`F.Cu pad(R4) 微净空接入 → 墙 pad`（series cap 强节点）。
- **REFCLK（2 页）**：J2 端 → 东走廊 lane → 西走廊 lane → MCIO 端（连接两走廊 lane
  的跨越段以 In2 直连，锚定芯片带外净空区——几何由 lane 带 + 禁列区谓词保证）。
- **节点输出**：每页 `nodes{P,N}` = 有序点列 + 每段层 + via 位置表 + 强节点
  （pad/via/墙 pad）索引；另附 `chip_landing_rows`（每网 1 行：method=VIA_IN2、
  落点=via₁ 位）供 S2 solve 的 chip_landing 命名空间直接消费（§5）。

发射后**立即自验**几何不变量套件（§6 A1.3），违例 = 生成器 bug（红级），
当场停，绝不出图。

---

## 4. 证书格式（不可行页 / 联合不可行）

```jsonc
{
  "cert_id": "ESC-PCIE_DN_OUT0/out_MCIO",
  "kind": "CONSERVATION_CERTIFICATE",
  "infeasible_layer": "R1_chip_escape_column",
  "page_id": "PCIE_DN_OUT0/out_MCIO",
  "resources": ["chip_side.dn_out_mcio.A_PET0.cols"],   // 被占死的资源
  "demand": {"pair_cols": 2, "domain_mm": [82.9, 84.9]},
  "blockers": [{"kind": "gnd_ball", "at": [83.2, 52.4], "via_clearance_req_mm": 0.4775}],
  "minimal_core": ["PCIE_DN_OUT0/out_MCIO", "PCIE_DN_OUT1/out_MCIO"], // 最小不满足集(层内)
  "why_no_alloc_possible": "2 对 4 列需求 vs 域内可用列 2(净空后) + 错列≥0.36 约束下无 2 对同时可行"
}
```

- 每证书字段可直读对账（无 guess/隐藏常量）——A3.1 顺带满足（S3 复验）。
- 证书=页级或层级的**最小核**：删除任一成员页/需求即可行（对删除基规范的确定性
  核，见 §2.2）。

---

## 5. 职责边界与施工消费接口

| 系统 | 职责 | 边界（不做什么） |
|---|---|---|
| **S1 生成器（本卡，k2 装配层）** | 页清单派生、R1-R4 编码、守恒判定、证书、全节点图纸发射 | 不连线段落、不写板、不消费旧簿 |
| 既有 alloc / channel_alloc | **被取代（图纸层内不再调用）**；保留仅作历史对照 | 不得出现在生成器输入路径 |
| 既有 landing / v53-v54 簿（EscapeTable/ColumnBook/construction_fact） | 对照/审计对象 | 生成器不读写；其错误锚/反演结论不得进入 |
| S2 施工（solve, 后续阶段） | 消费图纸：`chip_landing` 命名空间接线 + 连连看 | 不改节点；缺页 fail-closed（drawing_only 保持） |
| S0 端点模型 | 唯一锚源 | — |

**接口形状（喂 solve）**：图纸工件 JSON 含全局 `drawings[]`（34 页）+ 每页
`chip_landing_rows[]`（`{net, method:"VIA_IN2", pad, landing:{x,y}, signal, ball}`）
与既有 `chip_landing_v33.json` 同构但**锚=权威 expect_xy**；S2 装配时把行注入
solve 的 chip_landing 命名空间（命名空间键 = 网名，独立于连接器 landing 表）。

---

## 6. 机器验收映射（A1.1-A1.4 → 工具/谓词）

| 谓词 | 机器验证方式 | 工具（k2 tools/） |
|---|---|---|
| **A1.1 守恒判定正确性** | 守恒谓词在**合成反例集**上与**独立穷举基准**逐例一致（两族：看似有隙实无解 / 看似无解实可行）；证书 = 最小核与基准一致 | `p3_v57_s1_conservation.py`（判定核心）+ `p3_v57_s1_exhaustive_ref.py`（穷举基准，独立实现，无共享逻辑）+ `p3_v57_s1_a11_gate.py`（跑两族 ≥N 例，报告逐例 PASS/FAIL） |
| **A1.2 序无关** | 同输入三枚举序（正/倒/密度）→ 图纸+证书文件逐字节一致 | `p3_v57_s1_a12_gate.py` |
| **A1.3 生成即合法** | 发射节点过几何不变量套件（P/N 中心距=0.38±ε、P/N 竖腿边缘距≥0.155、via 孔/铜净空、同列同格密度、锚定只读、每线 via≤2） | `p3_v57_s1_a13_invariants.py`（套件独立于发射器实现，防同源自证） |
| **A1.4 单向性** | grep 谓词：生成器输入/发射路径无 `x-window`/`max-x`/板文件反猜；锚字段引用白名单 = S0 模型 + SPEC 声明 | `p3_v57_s1_a14_gate.py` |

**不过即停**：任一门 FAIL → 停 S1、报告、整改、重验，禁止进 S2（L7）。

---

## 7. 不做（本卡边界硬性）

- 不做板级 DRC/DRC 驱动；不产出 kicad_pcb 段；不改 _shared（freeze 保持 locked；
  生成器与验收全在 k2/tools + artifacts，模型零改动）。
- 不做 S2 施工消费改造、不关/放宽 drawing_only 闸门、不重算 S0 已钉端点。
- 不把 SPEC corridors 陈旧 `tracks_y`/`In6` 当输入依赖（对照口径，见 §2.3）。
- 不做"看似可行即图纸"的乐观发射：凡守恒判据过不去 → 证书，绝不硬凑。

---

## 8. 遗留（进编码前已知、不阻塞设计，但记录）

1. R2 lane 位置以规则 re-derive 后，与 SPEC 记录的旧轨道值偏差 → 落 DESIGN-NOTE
   差异表，S2 装配与 capacity 对账时引用（authority-first：守恒解优先）。
2. R4 墙隙守恒当前依赖 SPEC 声明间距（1.3mm 注入）保证互斥；若真板墙 pad 实测
   间距与声明冲突 → 生成器对墙层输出证书（不做逐 pad 妥协）。
3. 出逃域 R1 的 0.05 步离散与球铜膨胀口径需在 A1.3 套件中以合成几何板对拍
   （独立穷举同源判据），避免"生成器自证"。
