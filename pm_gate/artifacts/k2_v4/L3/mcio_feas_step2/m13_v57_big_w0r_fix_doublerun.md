# W0R-FIX 双跑与证据记录（m13_v57_big_w0r_fix_doublerun）

- 日期：2026-09-10（Asia/Taipei）
- 卡片：W0R-FIX（关 W0R-G1/G2/G3，见 `EDA_AUTONOMOUS_EXECUTION_PLAN_v2.md` §1/§5）
- 修订：`W0R-FIX.1`（生成器/验证器同修订号，模型 schema 1 → 2）
- 本文件角色：G0/G1 风格的双跑字节一致性 + 冻结不变性记录（证据，非修复许可）

## 1. 交付物指纹（最终状态）

| 文件 | SHA-256 |
|---|---|
| `tools/p3_v57_big_w0r_corridor_model.py`（生成器） | `1283d2b68a5d3459436c922d5f2ecb9b2ae35c7979de7482598267f43585d31b` |
| `tools/p3_v57_big_w0r_validator.py`（验证器） | `4b8b90dd618f1ee860cb5a15be55c9fa4c9ff575ef6e19a334955a2c34fcb8e8` |
| `m13_v57_big_w0r_inputs.json`（输入信封，未变更） | `4ca3e134407634dd8fb4fb396d35aebcbe2893c1548119566f0ff0913771eb17` |
| `m13_v57_big_w0r_corridor_model.json`（模型） | `fee23ebe3aa6fed838441fbbb7e57c552dd025fc4f506a36cc49bc52b60741a2` |
| `m13_v57_big_w0r_validation.json`（独立验证） | `63993e6d3ed2af317a27d6c54a2926342c3a187660e3b07c000b0696c59d2112` |

配对关系：模型 `producer` 块内嵌生成器与验证器源文件指纹；验证结果内嵌模型与
两工具指纹。任一工具在产物生成后被改动 → 验证器报
`producer_*_hash_stale`（陈旧配对检测）。

## 2. 冻结源不变性（跑前 == 跑后 == 信封声明）

| 冻结源 | SHA-256（前=后=inputs_sha256 声明值） |
|---|---|
| `SPEC_k2_v4.json` | `3bdecb10ab4747a9280131c89cb5a25b64466b62966b3354c4780c5fbf9a0d7a` |
| `k2_v4.kicad_pcb` | `f6273de613f43d05555d12d6c3492b1e70f383761d8db5121f12b2ca0695af9a` |
| `m13_v57_s1_page_manifest.json` | `87c4c97378ff6f151fad214e6c63c64094f921fa5ab6f6cc0e269c3ac6c03360` |
| `_shared/eda_core/drc_rules.json` | `0a459839e15960b8fbfe0e1f5bb154a02b30cbafa1cbb0d56c2b810a71228448` |

未触碰：SPEC、冻结放置、`_shared`、W1/W2 产物、PCB 铜（生成器/验证器仅读
footprint 几何，tracks/vias/zones 仍为声明的非输入）。`git status` 核对：本卡
改动仅限上表 5 个交付物文件 + 本记录。

## 3. 双跑字节一致性

- 生成器连跑 2 次：`inputs.json` 与 `corridor_model.json` 两次 SHA-256 完全一致
  （上表值）。输入信封与修复前字节相同（`4ca3e134…` 未变，接受部分未重建）。
- 验证器连跑 2 次：`validation.json` 两次 SHA-256 完全一致，verdict=PASS，
  failures=[]。
- 规范化契约不变：canonical JSON（sorted keys、indent=1、结尾换行）。

## 4. 终态与三缺口关闭摘要

- **verdict = `B1.5 PASS`**（终态二选一之一；`verdict_rule` 字段写明推导规则，
  无第三态）。certificates = []。
- **W0R-G1**：两走廊 `refclk_resource_domain.resource_kind =
  conservation_certificate`，status=SATISFIED，含 required/available/shortage/
  conflicting_resources/minimal_core（空核 ⇔ 守恒成立），per-page per-corridor
  行带核算：EAST REFCLK0 [45.17,46.63]@45.9、REFCLK1 [50.57,52.03]@51.3；
  WEST REFCLK0 [45.02,46.48]@45.75、REFCLK1 [60.72,62.18]@61.45；行距
  5.4/15.7 ≥ pitch 1.46；全部落于单跨 [33.3,78.7]。
  `refclk_passage_witness`（顶层）给出芯片区通行存在性证明：REFCLK0 南通道
  [43.425,48.675]；REFCLK1 北窗 [62.525,63.575]（C83/C82 间隙，高 1.05 ≥
  对铜展布 0.585，其余北窗 0.15/0.05/负间隙全部封死并逐一记录）。仅存在性，
  非路由；构造/选窗归 W3/R3-R4。
- **W0R-G2**：终态 verdict + v1 §3 六项证据协议字段映射
  （`evidence_protocol_v1_s3`）+ producer 版本块 + `legal_escape_hatches`
  （仅上游输入变更）。
- **W0R-G3**：每走廊 `projection_evidence`：谓词（严格 x 重叠 + 端点排除集
  {J2,J3,J4,U6} + 0.175 y 膨胀）、源指纹、42 封装全枚举（37 有几何 + 5 无几何
  逐个列明 J6/J9/J11/J12/J13 @x=26.5，距 WEST 走廊 38.55mm）、端点重叠明细
  （EAST：J2 悬伸 0.65mm 焊盘场、U6 0.35mm 纯庭院无焊盘；WEST：U6 0.35mm）
  与空集理由。[] 为真实枚举减法结果，非默认空值。

## 5. 验证器咬合力（变异测试，13/13 + 7/7 全部捕获）

对模型做单点篡改后验证器均 FAIL（随后字节级恢复原状）：
verdict 非终态 / resource_kind 回退 candidate_only / 行带漂移 / 间距篡改 /
见证窗扩大 / 见证通道篡改 / 枚举旗标翻转 / 总数篡改 / SATISFIED 下最小核非空 /
producer 哈希陈旧 / 下游逃生门(L4) / 空集理由删除 / 面净距篡改。

## 6. 规则防漂移断言

生成器/验证器均在运行时从 `drc_rules.json` 推导并断言：
pitch = p_gap + 2×p_width + inter_pair = 0.175+0.41+0.875 = 1.46；
PCIe85 clearance = 0.175 = BODY_CLEARANCE。漂移即硬停机（非静默）。

## 7. Oracle 终审与修复（PASS → 加固）

独立 Oracle 复核（读全部产物 + 独立重算 42 封装 census / 端点重叠 / 切片 /
两个见证窗 / 冻结 hash；并复核双跑）结论：**PASS（条件性）**，无伪造/无隐藏
`tracks_y` 授权（SPEC.corridors 为声明非输入且从不读取；实测板文件为裸放置板：
0 segment / 0 via / 0 zone，故"板铜非输入"不仅合规且实质为空）。终审指出 1 个
MED 潜在缺陷 + 若干盲区，本卡已修复：

- **D1（已修）**：`refclk_resource_domain` 失败分支未填 `minimal_core`，且
  INFEASIBLE 证书核与域核可能不一致。现 `minimal_core.members` /
  `shortage.detail` / 证书 `canonical_core` 三者同源同一最小冲突核。
- **D2（已修）**：验证器补检 `data_bands_cross_layer.outcome`、
  EAST `inter_pad_transit`、WEST 转接 `outcome`、`evidence_protocol_v1_s3`
  值非空，并新增 INFEASIBLE 分支一致性守卫（状态/核/明细/证书核匹配）。
- **鲁棒性（已修）**：芯片区无电容柱（仅 U6）时 `min()` 空序列崩溃 → 已加
  保护；当前板输出保持字节不变。

**合成 INFEASIBLE 实测**：monkeypatch 走廊 x 范围 + REFCLK0 锚点 y 落入被占
区间，真实触发失败分支：verdict=`B1.5 INFEASIBLE_CERT`，EAST 域
status=INFEASIBLE、`minimal_core.members=['PCIE_REFCLK0/input']`、
`shortage.detail` 给出 band_y 与可用跨、证书 `canonical_core` 与域核一致。
测试后已恢复，真实产物哈希与上表一致，验证器 PASS。

**新增守卫变异测试**：7/7 全部捕获（状态翻转+空核、空 shortage 明细、
跨层 outcome、EAST 盘间转接、WEST 转接 outcome、证据协议值置空、L3 下游逃生门）。

## 8. 残留注意项（移交 G1 评审，不改变终态）

- 验证器"独立"= 不 import + 独立重解析，但算法语义与生成器同构；共享的建模
  约定（端点排除、body 代理、旋转方向）无法被其捕获（D3）。
- REFCLK1 东带 y=51.3 位于 U6 y 范围内，其"单跨包含"仅在端点排除语义下成立；
  实际通行由芯片区见证（北绕）保证，非整走廊行（D4，抽象而非墙）。
- `SPEC.corridors`（非输入）中 refclk 层记为 `In6.Cu`（栈中不存在），与
  `F.Cu` 候选不一致；已作为 L2 逃生门列出，建议 G1 前确认（D5）。
- 解析器未处理 pad 局部旋转；当前板无影响，未来改版需注意（D6）。

