# M14 v47 承接 — ①实现勘误：E3 全量判据依赖②形态谓词（不造半个注册表）；E2+D2 可激活；下一步 = ②首片

> 承接 v46。唯一必读 = 本文件 + v46 handoff + 设计文档（m14_alloc_escape_precheck_design.md，
> 含 §2.8 勘误）。v45/v46 事实仍有效勿重推。
> 纪律复盘（v47 教训）：E3 曾在 alloc 层内尝试"全局 pad ∃ via"判据——因 pads provider
> 返回全链段 pad（含 J2/MCIO 连接器侧），连接器侧 pad 必合法 → 判据退化假过，DN5 抓不住；
> 判别"芯片侧竖排 col 形态"须形态归属（col_stack vs landing），alloc 层无此知识 → **按路线
> 停机：E3 谓词归②形态注册表，不在 alloc 内造半个注册表**（行为不扭曲路线）。

---

## 0. 一句话状态

ENG `_shared` +2 commit（`ce4a5a6` E3(a) point_ok 同源修正 / `0b056e8` E3(b) pair_half
P/N 行对齐）；freeze 0/0/0 lock。**E2（逃逸载体行位净空）= alloc 层稳健可落地**（与形态
无关的走廊外可达性）；**E3(a)/(b) 代码框架在 ENG 但默认休眠**——全量判据须②形态谓词
逐侧注入后才激活。K2 侧 config 未启用（等②首片后与 E3 一并激活验证，避免噪声半跑）。

---

## 1. 钉死事实（v47 增量；勿重推）

| # | 事实 | 依据 |
|---|---|---|
| N1 | 引擎 col-top via 落点净空判定 = `field.point_ok(via 点)`（_col_stack_escape L1987-88 / _layer_swap L1110-13）；`via_ok` 的 pad 分支只查 clearance inflation（无 annulus 语义）→ E3(a) 用 point_ok 才与 solve 同源 | v47 读码对照 + 单测 |
| N2 | kb 公式 `|via.y − band_row| ≥ via_keepout + track_half` 的 band_row = **P/N 实际行**（=中心轨行 ± PAIR_HALF_PITCH 0.19），非中心行 → E3(b) 以 pair_half 展开 rows_other | v47 pair_half 修正 |
| N3 | `_chain_nets_for` 返回全链段网（input P/N + out 各 suffix P/N，板存在性过滤）→ pads provider 含连接器侧 pad（J2/MCIO）；**全局 ∃ via 判据退化**：DN5 芯片侧被封但同链 J2 pad 合法 → 假过 | v47 读码 + 几何分析 |
| N4 | 判别"该侧是否 col 形态（竖排 dy≥0.45）"是 col_stack 内禀属性（触发条件），alloc 层无形态归属知识 → **E3 逐侧判据 = ②形态注册表行位可行性谓词**，alloc 只消费 | v47 架构判断（用户"行为不扭曲路线"背书） |
| N5 | E2（带载体层行位在逃逸跨段 [pad 列, 走廊界] 净空）= 与形态无关 → alloc 层落地正确；36 单测全绿（含 E3 框架用例） | v47 pytest |

---

## 2. v48 唯一主线：②首片（形态注册表 + C-1/C-3 谓词）→ 然后 ①E3+K2 e2e 一并激活

1. **②首片设计**：形态注册表（ENG 数据驱动，config 声明形态族 per corridor/band/side 特征
   触发条件）+ **行位可行性谓词接口**（= E2/E3 的逐侧适用判据注入点）：
   - C-1 谓词：尾段载体两轮适用性（F.Cu 被表层墙挡 → In2 载体；行位净空判据已在 E2）
   - C-3 谓词：col 侧（芯片竖排 dy≥0.45 触发）via 落点包络 vs REFCLK 带行（pair_half +
     keepout + band_spans）——**按侧注入**，不再全局 ∃
   - landing/direct 侧（连接器）不跑 col via 判据（落点由 landing 表消费，另有净空闸）
2. **K2 config 激活**（一次性）：
   - `route_model_config.json channel_alloc.half_pitch: 0.19`（开启 D2=E1 + E2）
   - `escape_check` 按②谓词注册的 esc 参数（keepout 0.37 / pair_half 0.19 / half_track
     0.1025 / band_spans refclk[55,134] / e3 激活键）——数值以 solve 构造常量/rules 校验
3. **K2 alloc 重跑 + e2e 一次性验证**（≤2 次）：DN5@64.3 期望被 E3(a) 芯片侧谓词拒、
   REFCLK 带与 UP 列 via 包络由 E3(b) 谓词约束；目标 18 bases SOLVED + REFCLK0/1 全保 +
   skew<0.15 + P/N≥0.175。
4. 合规：单测全绿 → e2e 绿 → lock → commit+push（ENG + kb 784034b 待 push 一并）。

---

## 3. 资产 / 停止态

| 项 | 状态 |
|---|---|
| ENG `_shared` | HEAD `0b056e8`（v46 `3f33cbc` + v47 `ce4a5a6`/`0b056e8`）；freeze 0/0/0 lock；pre-existing 脏仅 escape_closure_analysis.py/install.sh + .bak_v33_perball（勿 commit） |
| k2 | 未改动；板 sha f6273de6 未动 |
| 文档 | 设计文档 §2.8 勘误已落（E3 → ②谓词）；本 handoff |
| 单测 | test_escape_envelope.py 9 用例（E2 拒/过、E3a point_ok 拒、E3b 吞噬/存在性、降级、alloc 集成）全绿 |

**勿做**：勿在 alloc 层内补"侧判别"启发式（那是②形态谓词职责，N4）；勿半跑 K2 e2e
（E3 未激活 → 结果无增量意义，P4：归因以谓词齐全后的真 shared run 为准）；勿动 SPEC/
corridor 冻结物。
