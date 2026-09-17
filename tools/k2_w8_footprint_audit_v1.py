#!/usr/bin/env python3
"""K2 · W-8（J-7「封装 = 库」）**电气级逐件审计**（确定性，只读板 + 只读库）。

依据（监理裁定 #K2-19 §二 W-8，权威原文）：
  「**裁定：以板为准** —— 板实作 pad **电气几何 = 库**（`J2` pad 74 = 74 ✓），差异仅**图形/属性级**
   （`fp_line` 0/8、`property` 4/2）。判据**容忍图形级差异**，**电气级必须 0**（pad **数/名/尺寸/旋转/位置**逐件比）；
   35 件**逐条登记**。**同时建 `fp-lib-table`**（F-12 收口）」

本器职责 = **交测量**（判定权归监理）：对板上**每颗** footprint，与其**命名库副本**做**电气级**比对：
  ① pad 数；② pad 名集合；③ 逐 pad：形状 / 尺寸(x,y) / 钻孔 / 自转 / **局部位置**；
  ④ **相对几何**（pad 两两相对向量的集合，对原点平移不变）—— 用于区分「footprint 原点约定差异」（物理等价）
     与「真实 land pattern 差异」。⑤ 输出 JSON（机读）+ MD（逐条登记表）。

只读：板 + 库文件；不写板、不写库、不改判据。库解析 = `--std-root`（KiCad 标准库根，默认 AppDir）
+ `--proj-lib`（项目库根，默认板同目录 `lib/`）。
CLI: python3 k2_w8_footprint_audit_v1.py --board <pcb> [--std-root DIR] [--proj-lib DIR] --out-json J --out-md M
"""
from __future__ import annotations
import argparse, collections, hashlib, json, math, os, re, sys
import pcbnew

MM = pcbnew.ToMM
KEYS = ("shape", "sx", "sy", "dx", "dy", "rot", "drill_d")


def fmt(v, nd=4):
    s = f"{v:.{nd}f}".rstrip("0").rstrip(".")
    return s if s else "0"


def pad_sig(fp):
    """ref -> 电气级签名（局部坐标系）"""
    out = {}
    for p in fp.Pads():
        r = p.GetFPRelativePosition(); d = p.GetDrillSize()
        out[p.GetNumber()] = (int(p.GetShape()), round(MM(p.GetSize().x), 4), round(MM(p.GetSize().y), 4),
                              round(MM(r.x), 4), round(MM(r.y), 4), round(p.GetOrientationDegrees(), 2),
                              round(MM(d.x), 4))
    return out


def rel_geom(sig):
    """两两相对向量集合（平移不变）；键为 pad 名对"""
    names = sorted(sig)
    return {("%s|%s" % (a, b)): (round(sig[b][3] - sig[a][3], 4), round(sig[b][4] - sig[a][4], 4))
            for i, a in enumerate(names) for b in names[i + 1:]}


def resolve(nick, name, std_root, proj_lib):
    if nick == "ForgeOS":
        d = os.path.join(proj_lib, "ForgeOS.pretty")
        return d if os.path.isdir(d) else None
    if not nick:
        return None
    d = os.path.join(std_root, "%s.pretty" % nick)
    return d if os.path.isdir(d) else None


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    default_std = os.path.normpath(os.path.join(here, "..", "..", "AppDir", "share", "kicad", "footprints"))
    ap.add_argument("--board", required=True)
    ap.add_argument("--std-root", default=default_std)
    ap.add_argument("--proj-lib", default=None)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    a = ap.parse_args()
    proj_lib = a.proj_lib or os.path.join(os.path.dirname(os.path.abspath(a.board)), "lib")
    b = pcbnew.LoadBoard(a.board)
    recs = []
    for fp in b.GetFootprints():
        fid = fp.GetFPID()
        nick, name = str(fid.GetLibNickname()), str(fid.GetLibItemName())
        ref = fp.GetReference()
        board = pad_sig(fp)
        rec = dict(ref=ref, lib_id="%s:%s" % (nick, name) if nick else ("(no-nickname) " + name),
                   fp_rot=round(fp.GetOrientationDegrees(), 2), n_board=len(board), verdict=None, diffs=[], rel_geom_same=None)
        d = resolve(nick, name, a.std_root, proj_lib)
        if d is None:
            rec["verdict"] = "no_library_link" if not nick else "library_dir_missing"
            recs.append(rec); continue
        try:
            lfp = pcbnew.FootprintLoad(d, name)
        except Exception:
            lfp = None
        if lfp is None or lfp.GetPadCount() == 0:
            rec["verdict"] = "library_item_missing"; recs.append(rec); continue
        lib = pad_sig(lfp)
        rec["n_lib"] = len(lib)
        if set(board) != set(lib):
            rec["diffs"].append(dict(kind="pad_name_set", board_only=sorted(set(board) - set(lib))[:8],
                                     lib_only=sorted(set(lib) - set(board))[:8]))
        cmn = sorted(set(board) & set(lib))
        pad_diff = 0
        for n in cmn:
            dd = [k for k, x, y in zip(KEYS, board[n], lib[n]) if x != y]
            if dd:
                pad_diff += 1
                if len(rec["diffs"]) < 6:
                    rec["diffs"].append(dict(kind="pad", pad=n, fields=dd,
                                             board=dict(zip(KEYS, board[n])), lib=dict(zip(KEYS, lib[n]))))
        rec["n_pad_diff"] = pad_diff
        if cmn and len(set(board)) == len(set(lib)):
            same = rel_geom(board) == rel_geom(lib)
            rec["rel_geom_same"] = same
            if same and pad_diff:
                dv = collections.Counter((round(board[n][3] - lib[n][3], 4), round(board[n][4] - lib[n][4], 4)) for n in cmn)
                rec["uniform_translation"] = (len(dv) == 1)
        rec["verdict"] = ("electrical_identical" if (not rec["diffs"] and pad_diff == 0)
                          else ("pad_name_set_only" if pad_diff == 0 else "electrical_diff"))
        recs.append(rec)

    flag = [r for r in recs if r["verdict"] in ("electrical_diff", "pad_name_set_only",
                                                "library_dir_missing", "library_item_missing")]
    ok = [r for r in recs if r["verdict"] == "electrical_identical"]
    nons = [r for r in recs if r["verdict"] == "no_library_link"]
    summary = dict(
        board=a.board, board_sha16=hashlib.sha256(open(a.board, "rb").read()).hexdigest()[:16],
        std_root=a.std_root, proj_lib=proj_lib, n_footprints=len(recs),
        n_electrical_identical=len(ok), n_electrical_diff=sum(1 for r in recs if r["verdict"] == "electrical_diff"),
        n_pad_name_set_only=sum(1 for r in recs if r["verdict"] == "pad_name_set_only"),
        n_no_library_link=len(nons), n_library_unloadable=sum(1 for r in recs if r["verdict"] in ("library_dir_missing", "library_item_missing")),
        electrical_identical_refs=[r["ref"] for r in ok],
        electrical_diff_refs=[r["ref"] for r in flag], tool_sha16=hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16])
    json.dump(dict(summary=summary, records=recs), open(a.out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    L = []
    L.append("# K2 · J-7 / W-8「封装 = 库」电气级逐件审计（v1）\n")
    L.append("> 生成器：`k2/tools/k2_w8_footprint_audit_v1.py`（确定性只读；sha256 前16 = `%s`）\n" % summary["tool_sha16"])
    L.append("> 板：`%s`（sha256 前16 = `%s`）；标准库根 `%s`；项目库根 `%s`\n" % (a.board, summary["board_sha16"], a.std_root, proj_lib))
    L.append("> 口径（监理 #K2-19 §二 W-8）：**以板为准**；判据容忍**图形级**差异；**电气级必须 0**")
    L.append("> （pad 数 / 名 / 尺寸 / 旋转 / 位置逐件比）。本件只交测量，判定权归监理。\n")
    L.append("| 量 | 值 |")
    L.append("|---|---|")
    L.append("| 板上 footprint 总数 | %d |" % summary["n_footprints"])
    L.append("| 电气级完全一致 | **%d** |" % summary["n_electrical_identical"])
    L.append("| **电气级存在差异** | **%d** |" % summary["n_electrical_diff"])
    L.append("| 仅 pad 名集合不同 | %d |" % summary["n_pad_name_set_only"])
    L.append("| 无库链接（无 nickname，KiCad 不比对） | %d |" % summary["n_no_library_link"])
    L.append("| 库不可加载 | %d |\n" % summary["n_library_unloadable"])
    L.append("## 逐条登记\n")
    L.append("| ref | 库 ID | pads 板/库 | 差异 pad 数 | 相对几何同 | 电气结论 | 差异字段 |")
    L.append("|---|---|---|---|---|---|---|")
    for r in sorted(recs, key=lambda x: x["ref"]):
        if r["verdict"] == "no_library_link":
            continue
        flds = []
        for d_ in r["diffs"]:
            flds.append(d_["kind"] if d_["kind"] != "pad" else "pad:%s" % "/".join(d_["fields"]))
        v = dict(electrical_identical="**一致**", electrical_diff="**差异**", pad_name_set_only="**名集合差异**",
                 library_dir_missing="库目录缺", library_item_missing="库件缺")[r["verdict"]]
        L.append("| %s | %s | %s/%s | %s | %s | %s | %s |" % (
            r["ref"], r["lib_id"], r["n_board"], r.get("n_lib", "-"), r.get("n_pad_diff", "-"),
            {True: "是", False: "否", None: "-"}[r.get("rel_geom_same")], v, "; ".join(flds)[:70]))
    L.append("\n## 单件明细（电气差异者）\n")
    for r in sorted(recs, key=lambda x: x["ref"]):
        if r["verdict"] != "electrical_diff":
            continue
        L.append("### %s · `%s`\n" % (r["ref"], r["lib_id"]))
        L.append("- 板 pads %s / 库 pads %s；差异 pad = %s；相对几何同 = %s%s" % (
            r["n_board"], r.get("n_lib"), r.get("n_pad_diff"),
            r.get("rel_geom_same"),
            ("（全部 pad 差同一常量平移 ⇒ **物理等价，仅原点约定**）" if r.get("uniform_translation") else "")))
        for d_ in r["diffs"]:
            if d_["kind"] == "pad":
                L.append("  - pad `%s`：差异字段 `%s`；板 `%s`；库 `%s`" % (
                    d_["pad"], "/".join(d_["fields"]),
                    ", ".join("%s=%s" % (k, d_["board"][k]) for k in d_["fields"]),
                    ", ".join("%s=%s" % (k, d_["lib"][k]) for k in d_["fields"])))
            else:
                L.append("  - %s：板独有 `%s`；库独有 `%s`" % (d_["kind"], d_["board_only"], d_["lib_only"]))
        L.append("")
    open(a.out_md, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
