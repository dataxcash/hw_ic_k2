# K2 · R324 · 交付链**字节级可复现复核**（PASS 29/29）

**件**：`K2_R324_DELIVERY_PIPELINE_BYTE_LEVEL_REPRODUCIBILITY_v1.json`（约定A **`002939003036b8a8`**）
**据**：《K2 整体整改计划》§P4（产出 = 板 + Gerber + 钻孔 + 打包）· **ENG 契约 §3.3 阶段⑤完工判据「包齐 ∧ 逐文件 sha ∧ 字节级可复现」** · owner #14③（完工定义 = 可制造 Gerber）
**锚**：冻结四源 **4/4 未动** · `criteria` rev=6 MATCH · 受审板 l8 **`7a5c89913d6e5d0a`** · **owner 闸口 0**

---

## 〇、一句话

以受审板 l8 之 **/tmp 只读副本**、按打包器**所载同一命令**重出 Gerber + Excellon、施加**同一时间戳规范化**后，与已 commit 的 `L6/jlc_package_l8r3` **逐文件 sha256 比对**：

> **29 / 29 件字节级完全相同（0 不一致 · 0 缺件 · 0 多件）⇒ 字节级可复现 PASS。**

仓库工作树**未改**（导出全程在 `/tmp` 副本上进行）。

## 一、方法与证据

| 步骤 | 内容 |
|---|---|
| ① 只读复制 | l8 板/工程 → `/tmp` 副本（副本 sha16 校验 == 受审板 `7a5c89913d6e5d0a`） |
| ② 重出 | `kicad-cli pcb export gerbers --board-plot-params --no-x2 --layers <8铜+2丝印+2阻焊+边框>` · `kicad-cli pcb export drill --format excellon --excellon-units mm --generate-map --map-format svg --generate-report` |
| ③ 规范化 | 同一时间戳规则 → `2026-09-19T00:00:00+08:00`（gerber 14 件 · drill 15 件被规范化） |
| ④ 比对 | **逐文件 sha256** vs 已 commit 包 |

## 二、结果与清点

| 项 | 值 |
|---|---|
| **逐文件 sha256 相同** | **29 / 29** |
| 不一致 / 缺件 / 多件 | **0 / 0 / 0** |
| Gerber 件数 | **14**（含 **8 铜层** `F/In1..In6/B` + `F/B_Mask` + `F/B_Silkscreen` + `Edge_Cuts` + `.gbrjob`）|
| Excellon 件数 | **15**（含 **7 个 `.drl`**，其中有 **HDI 盲埋孔分对**：`front-in1` `front-in2` `front-in4` `front-in5` `in2-in5` `back-in5` + 通孔）|
| 钻孔总数（MANIFEST） | **754** |
| 包内件数（MANIFEST） | **53** |
| **DFM（包内 MANIFEST 记载）** | **16 PASS / 1 ACCEPT / 0 FAIL**（JLC HDI 通道；ACCEPT = 阻焊坝 <0.09mm 之板厂按「无阻焊坝」印制项，不妨碍可制造性） |
| 判据锚 / kicad | rev=6 · kicad-cli 10.0.5 |

## 三、范围声明（不作过度主张）

- 本件**只复核交付链之可复现性**（阶段⑤之机械判据），**不改变 ②-UP 之未决状态**、**不主张 P4 全绿**。
- 受审板仍为 **l8**；最终交付件待 **②-UP 口径**（R323 之两条自裁）与**判据侧**（R317 之 `lib_electrical_level`）裁定落定后**同批重出**（fail-closed）。
- **P4 未全绿**（R317 verdict 18/19）⇒ **不进 P5、不下单**。

## 四、复现

```bash
R=/tmp/opencode/repro_$(date +%s); mkdir -p $R/g $R/d
cp k2/hw/k2_v4_8L.l8.kicad_pcb k2/hw/k2_v4_8L.l8.kicad_pro $R/
AppDir/bin/kicad-cli pcb export gerbers --board-plot-params --no-x2 \
  --layers F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,In5.Cu,In6.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts \
  --output $R/g $R/k2_v4_8L.l8.kicad_pcb
AppDir/bin/kicad-cli pcb export drill --format excellon --excellon-units mm --generate-map --map-format svg \
  --generate-report --report-path $R/d/drill_report.txt --output $R/d $R/k2_v4_8L.l8.kicad_pcb
# 时间戳规范化后与 k2/pm_gate/artifacts/k2_v4/L6/jlc_package_l8r3/ 逐文件 sha256 比对
# 期望: 29/29 相同
```

## 五、边界

冻结四源不改 · `criteria/` 只读 · 未烙板 · 未派 WORKER · 未改生成器/SPEC/原理图 · 临时仅 `/tmp/opencode` · 未写 `.omo/supervision/**` · **仓库工作树未改** · **P4 fail-closed 维持**。

—— ENG（ARCHER）· 2026-09-22 · k2 `250b6af`（本件另提交）· owner 闸口 **0**
