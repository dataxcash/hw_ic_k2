# CO-154 — 非执行者对抗复评（CO-153 + CO-152）｜rev-19

- verdict：**PASS_WITH_FINDINGS**｜findings：7
- 板 `d4e81f647be7f980`｜SPEC `5f72182a2616392c`｜冻结四源 4/4 MATCH

| id | sev | kind | what（摘要） |
|---|---|---|---|
| F-1 | medium | executor-regression | CO-152 从 CO-150 记录删去 `register.open_total` 字段（改为 note）却**未同步两处消费者**（`p3_v57_co150_k9_domai... |
| F-2 | medium | reproducibility | CO-152 只要清理了 `*_sha16_after` 类**下游 sha** 快照，未覆盖同族的**下游计数/版本快照**：co147 记录内嵌 `register.open_... |
| F-3 | low | pin-label-hygiene | boundary 对同一实件的修订号自相矛盾：§26（CO-150 段）记 co124 = **CO-124.5**，§29 pin 表记 **CO-124.6**，而实件（记录 ... |
| F-4 | medium | rule-unenforced | R-CO153-1（「K9 各域均须由规范复现序内具名生产者产出；禁止一次性写入台账域」）对本条**不成立且无机判**：`domain_cap`/`identity`/`proce... |
| F-5 | medium | gate-coverage | K9 对「域集合」无牙齿：`kind` 取未列值（如 `bogus_domain`）或 `kind=domain_cap` 但缺 `domains` 列表时，无任何分支命中 ⇒ *... |
| F-6 | medium | gate-weakness | CO-153 新增的 `declared` 判据只做**证据 pin 检查**（path 可解析 + sha16 现行 + basis 非空），与被声明的值**无语义关联**：实测... |
| F-7 | low | gate-weakness | `conservative_ge` 的「忠实下界」由该 DV **自带的** inputs.span_mm / w_outer_mm 重算（faithful = span+2·w_... |

独立确认（非空过证据）：

- 冻结四源 4/4 MATCH（含 drc_rules 0a459839e15960b8）；交付板 = d4e81f647be7f980
- CO-153 主张成立：co124 = PASS / findings 0 / 牙齿 17-17 全 True（复评独立复跑一致）
- CO-152 P5 按声明成立：co120 = PASS / snaps 8 / undeclared 0 / basis_not_ok 0 / teeth ok
- CO-152 R2 勘误已落实（doc 值 0.2577 + 保留旧值 0.3294 供追溯），裁定仍 ACCEPT_L2 ⇒ **不改变结论**
- 两类新判据在真违规时确被抓（declared 陈旧 sha / conservative value<faithful）⇒ 牙齿非空过
