# k2/docs/drafts/p4-manifest-completion-v2/ —— P4 判据缺口补齐草案（ENG 草案件）

> 状态：**未安装、未签认**（`not_countersigned: true`）。`criteria/`（0444, owner=ic_hw_gate）逐字节未动。
> 依据：监理 `#K2-20 §二`（`criteria/manifest` 不予签认 ⇒ 须先补齐转写）+ `§五-2`（ENG 起草 → 监理正/负控复验 → 版本 bump 安装 → 监理签认）。
> 提交与证据说明见：`k2/docs/K2-P4-MANIFEST-COMPLETION-SUBMISSION-v1.md`。

## 件清单（sha256/16）

| 件 | sha256(16) | 说明 |
|---|---|---|
| `manifest.k2.draft-v2.yaml` | `890ed50eedf57e6d` | 转写补齐版判据清单草案（含 `null` = 待监理填的取值） |
| `adjudicate.draft-v2.py` | `db629a013c0563ba` | 判定器草案（实现；自跑 kicad-cli DRC，防伪造绿） |
| `make_negatives_v2.py` | `8a000f5c294e3a8d` | 负控造件脚本 v2（格式无关括号匹配；m6 改电气级 pad 尺寸突变） |

## 修订（v2.1 · 2026-09-17）

- 依 **#K2-19 §二 W-9**（k2 门 = k2-scoped）实现 `pipeline_present` 的 scope：新增 `manifest.pipeline_scope: [k2]` + 判定器按 scope 过滤 sch 目录 ⇒ 报 `k2/hw/sch` 1 目录（原 6 目录）。
- 两者 sha 随之为上表 v2.1 值；`make_negatives_v2.py` 未变。

## 与 `/tmp` 副本的关系

本目录是 `/tmp/opencode/p4/draft/` 中同名草案件的**仓库耐久副本**（`/tmp` 为易失区）。
`manifest.k2.draft-v2.yaml` 与 `adjudicate.draft-v2.py` 与 `/tmp` 原件**逐字节同**（sha 一致）；
`make_negatives_v2.py` = `/tmp/opencode/p4/draft/make_negatives.py` 的 v2（2026-09-17 修：适配增量 16 板的新封装头格式 `\t(footprint "LIB:NAME"`，旧正则致 m6 未注入）。

## 变更纪律

`criteria/` 是只读冻结件（`897e8bfd…` / `7ce08757…`）。本目录的草案只有在监理完成正/负控复验后，才由**属主侧**以版本 bump 安装并签认。
