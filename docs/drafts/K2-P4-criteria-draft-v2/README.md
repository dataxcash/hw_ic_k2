# K2 · P4 判据侧草案 v2（**DRAFT：未安装**）

按监理 #K2-21 §二②④⑤ 与 §三 起草。**ENG 只起草到 `k2/docs`**；安装（`criteria/` / `.kicad_pro` / `pipeline.yaml`）
须走「监理正/负控复验 → gate 属主侧版本 bump 安装 → 监理登记 sha + 锚 rev=2」。本目录文件**不生效**。

| 文件 | 对应裁定 | 说明 |
|---|---|---|
| `adjudicate.py` | ②④⑤ + §三 | 判定器补丁草案（含新检查实现；正/负控见交件文档） |
| `manifest.k2.yaml` | §三 | 判据清单 v2 草案（新增 J-1 / J-2·V1 / J-7a / J-8(keepout) / 声明 pending 4 项 + `drill_count` 补正） |
| `pipeline.yaml.draft` | ④ | k2 域门禁接入草案（**符合 eda_core 管线 schema**：含 `phases` + 3 项必选 sch 检查；安装时复制为 `k2/pipeline.yaml`） |
| `run_controls.py` | 验证 | 正/负控复跑脚本（7 案；需 `AppDir` + `python3`+PyYAML） |
