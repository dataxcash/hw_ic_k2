# Card 1.1 归属声明 — Connectors 页栅格修订

> 归属声明（AGENTS.md §2.2 铁律 3）
> 日期：2026-08-26

## 归属
- **ECO 任务**: M13 v8 Card 1.0 后续阻塞（阻塞解除）
- **修复类型**: 输入层页面计划修订（yaml 单行）
- **文件**: `revA/boards/ioconvert_v2.yaml`（L2895 Connectors 页 `columns: 3 → 2`，仅此一行）
- **根因**: ECO#31（a3862c0, 8-21）加入 U11(PI3DBS16412) 后，Connectors 页 3 个大器件
  （J14 42脚/J2 74脚/U11 43脚）大列超 A2 界 0.1mm；8-21 起被 loader 崩溃（U1/PB8）遮蔽，
  master 从未可生成。
- **裁决依据**: `BIG_COL_START = 50 + columns*80 + 70`、`BIG_COL_STEP = 100`
  （generate_sch_v5.py layout_sheet 既有参数，本卡未改）验算：
  - columns=3 → 大列 360/460/560，第 3 列 560 + U11 符号 → 579.1 > 579.0（出界 0.1mm）
  - columns=2 → 大列 280/380/480，第 3 列 480 + 宽 ≤ 519.1 < 579.0（余量 79.9mm）
- **载荷验证（Card 1.0 产出，本卡勿动）**: loader (ref,card) 泛化已就位；
  U1 卡1→MCU_STM32G0(QFN-32)/卡2→MCU_STM32G0_C2(LQFP-48)，零悬空。
- **口径**: M-D"全链绿"系 8-20 陈旧产物；本次一切数字 = 真实首跑新基线。

## 验收链（Card 1 全链）
生成 exit 0 ×2 确定性 → split_sch 自证 → validate valid → ERC error=0
→ 节点归属 4 断言 → 出图门禁 → gen_card_nets 锚点 diff → 测试回归 → ECO S2/S3/S4
