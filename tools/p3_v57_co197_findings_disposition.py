#!/usr/bin/env python3
"""CO-197 — **非执行者对抗复评 CO-192..CO-195 之形态完备性**（L2 自裁）：findings 入登记簿（幂等 upsert）+ counts 复算。

K-1 = `teeth_hygiene_scan` 漏计关键字**解包**形态（`dict(**{...})` / `.update(**{...})`）⇒ 恒真齿可经该形态逃逸 t18。
K-2 = `md_write_scan` 漏计同族写/拷形态（`io.open(<md>,"w")` / `Path(...)`、路径别名 `.replace|rename(<md>)`）⇒ 此类 md 可落出受控集。
只改登记簿。CLI: python3 tools/p3_v57_co197_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ITEM_REF = "CO-197（runner 升 **CO-197.1**；复评 CO-192..CO-195 之形态完备性）"
ADD = [
    {"finding": "co197:K-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**牙齿扫描漏计关键字解包形态**：`teeth_hygiene_scan` 对 `dict(**{\"t01\": True})` 与 `teeth.update(**{\"t01\": True})`"
             "（AST `keyword.arg is None`）一律 `n_teeth=0` ⇒ 经该形态加入的**恒真齿**既不被计数、亦不被 constancy 检 ⇒ "
             "t18 的「逐工具齿数下限 + 常量齿零违规」一并被绕过（工具其余齿数达标时下限不触）。"
             "R-CO192-1 列举 `dict(...)` / `.update(...)` 为受覆盖形态，而其**解包子形态**未实现 ⇒ 「**全部**容器形态」为过强声明"
             "（同族：CO-187 F-1 恒真齿 / CO-192 F-1 容器形态漏计）。**复评实测**：as-found `52235b5` 与 `5e6ddde` 均 n=0，"
             "CO-192.1 未闭合。",
     "disposition": ITEM_REF + "：`_tooth_call_pairs()` 与 `update` 分支对 `kw.arg is None` 递归 `_tooth_dict_pairs(kw.value)`"
                    "（补关键字**解包**）；t18 合成正控补 2 例（`dict(**{...})` / `update(**{...})`），漏计即停机。",
     "status": "CLOSED", "next": "扫描器的「已列形态」须**逐子形态**落地并合成控覆盖；`keyword.arg is None`（`**` 解包）属必测子形态。",
     "evidence": ["复评实测（修前）：`dict(**{\"t01\": True})` / `update(**{\"t01\": True})` ⇒ `n_teeth=0`（as-found `52235b5` 与 `5e6ddde` 同）",
                  "复评实测（修后）：两形态 `n_teeth=1` 且报常量齿；`--check` t18 含该 2 例合成正控全 True"],
     "refs": ["CO-197", "CO-192", "CO-187"], "closed_by": ["CO-197"]},
    {"finding": "co197:K-2", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**md 写/拷扫描漏计同族形态**：`md_write_scan` 对 `io.open(<md>, \"w\")`、`Path(...).replace|rename(<md>)` 以及"
             "**路径别名** `P = Path(...); P.replace|rename(<md>)` 一律 `==[]` ⇒ 此类 `.md` 产物既不入 `ORDER_MD_PRODUCTS` pin、"
             "t20 亦不截 ⇒ 可静默落出受控集（违 R-CO186-1 之目的）。R-CO192-1 列举 `open(w)` / `Path.open(w)` / "
             "`os.replace|rename` 为受覆盖形态，其 **io/pathlib 同族**未实现；且 `io.open` 在 **boundary 读取**侧已纳扫、"
             "在 **md 写**侧未覆盖（**不对称**）。**复评实测**：as-found `52235b5` 与 `5e6ddde` 均 `==[]`，CO-192.1 未闭合。",
     "disposition": ITEM_REF + "：`md_write_scan` 补 ① `io.open(<md>, \"w\")`（写模式）；② `Path(...)` 及**模块级路径别名**的 "
                    "`.replace|rename(<md>)` **目的**参数。t20 合成控补 3 例正控 + 2 例对偶负控（只读 `io.open` 不得报、"
                    "`\"a.md\".replace(\".md\",\"\")` **字符串操作不得误报**）。",
     "status": "CLOSED", "next": "md 写/拷形态须覆盖 builtins / io / pathlib 三族及其别名；新增形态须补**对偶负控**防字符串操作误报。",
     "evidence": ["复评实测（修前）：`io.open(\"probe.md\",\"w\")` / `Path(\"a.md\").replace(\"dst.md\")` / 别名 `P.rename(\"dst.md\")` 均 `==[]`",
                  "复评实测（修后）：三者分别 `==[\"probe.md\"]` / `==[\"dst.md\"]` / `==[\"dst.md\"]`；`\"a.md\".replace(\".md\",\"\")` 与只读 `io.open` 仍 `==[]`",
                  "零误报核对：现行 ORDER 全工具的 md 命中集与齿数**逐工具不变**（t20/t18 零冲击）"],
     "refs": ["CO-197", "CO-192", "CO-186"], "closed_by": ["CO-197"]},
    {"finding": "co197:K-3", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**注解 upsert 的段边界缺陷（J-5 修正引入，本件实现期自捕获）**：J-5 把注解 upsert 改为 "
             "`trim 旧注解段 + append`，但 trim 取 `updated_by[:index(标记)]` —— 即**裁到末尾**。当其后**另有 CO 追加注解**时，"
             "重跑本 CO 的 disposition 会连同**他人的注解一并静默删除**。**实测**：co197 注解写入后再跑 "
             "`p3_v57_co196_findings_disposition.py`，登记簿 `updated_by` 中 `；**CO-197（…）**` 整段消失（条目 `co197:K-1/K-2` 仍在）"
             "⇒ 审计面**自述缺段**、且跨工具重跑**非幂等**。",
     "disposition": "CO-197：注解 upsert 改**原位替换** —— 本 CO 段自标记起、至**下一 `；**CO-` 注解起点**（无则至末尾）"
                    "**就地**以现注解替换，其余 CO 段**原样保位**；co197/co196 两件同步落地。红线 **R-CO197-4**：注解 upsert 只可**原位**改本段。",
     "status": "CLOSED", "next": "注解类 upsert 的 trim **必须带段右界**（下一 CO 标记）；**禁**无界裁尾；须以「交替重跑两 CO」验证互不侵蚀。",
     "evidence": ["实测（修前）：co197 注解 → 跑 co196 disposition ⇒ `；**CO-197（…）**` 段**消失**（`updated_by` 缺段）",
                  "实测（修后）：co196 ↔ co197 **交替重跑**（两种次序）⇒ 注解段**均在且保位**、登记簿 sha **恒定**（顺序无关）、条目/计数稳定（135 项 / OPEN 0）"],
     "refs": ["CO-197", "CO-196"], "closed_by": ["CO-197"]},
]


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text(encoding="utf-8"))
    by_id = {i["finding"]: n for n, i in enumerate(reg["items"])}
    added, updated = [], []
    for it in ADD:
        if it["finding"] in by_id:
            if reg["items"][by_id[it["finding"]]] != it:
                reg["items"][by_id[it["finding"]]] = it
                updated.append(it["finding"])
        else:
            reg["items"].append(it)
            added.append(it["finding"])
    note = ("；**CO-197（非执行者对抗复评 CO-192..CO-195 ＋ L2 自裁处置）**：+3 TOOL_DEFECT（`co197:K-1`,`K-2`,`K-3`，全 low，全 CLOSED；"
            "runner 升 **CO-197.1** —— `teeth_hygiene_scan` 补关键字解包形态、`md_write_scan` 补 io/pathlib 同族写/拷形态 + 对偶负控；"
            "复评 verdict **PASS_WITH_FINDINGS**、正控 V1..V8 全 True、负控 P1..P6 全 True；as-found 独立复现 CO-195 之 t28 验证循环"
            "（已由 CO-196 J-1 关闭，不重复计数）；**K-3** 注解 upsert 段边界（J-5 修正引入）⇒ trim 带段右界）。")
    # CO-196（J-5）：注解 upsert 须**可重入**（trim 旧 CO-197 注解段 + append 现注解），重复运行幂等且自述恒与条目实况一致。
    _MARK = "；**CO-197（非执行者对抗复评"
    _ub = reg["meta"].get("updated_by", "")
    # CO-197（K-3）：本注解段**原位替换**（右界 = 下一 `；**CO-` 注解起点 / 末尾）。
    # ① 不得无界裁尾（会静默删除**他人**注解段）；② 不得「裁掉再追加」（会把本段**移到末尾** ⇒ 状态随
    # 「最后跑的是哪个 CO 的 disposition」而变 ⇒ 登记簿 sha / 由它派生的 pin **顺序敏感、不可复现**）。
    if _MARK in _ub:
        _i = _ub.index(_MARK)
        _j = _ub.find("；**CO-", _i + len(_MARK))
        _ub = _ub[:_i] + note + (_ub[_j:] if _j != -1 else "")
    else:
        _ub = _ub + note
    reg["meta"]["updated_by"] = _ub
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"],
                      "register_sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
