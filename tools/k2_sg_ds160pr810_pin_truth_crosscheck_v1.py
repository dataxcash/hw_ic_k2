#!/usr/bin/env python3
"""K2 · sch_gate 真源 pin 全量对表（DS160PR810 / TI SNLS658 WQFN-64）—— 只读。

授权：#K2-51 §二 SG-AUDIT-1「知悉 + 放行补检」（排期补检 `DS160PR810`（64 脚）·
`TLV61046A`）。本工具把 **厂商 PDF 的 Pin Functions 表**逐脚解析，与在库真源
`_shared/eda_core/sch_gate/datasheets/DS160PR810.yaml#pins` **64/64 全量**比对
（前一版仅抽样 14/64；残差 = `pdftotext -layout` 跨页/折行使 64 行仅 9 行可正则化）。

本工具**只读**：不改 PDF、不改 YAML、不改 criteria。输入 PDF 由调用方提供
（本仓零写；下载件放 /tmp）。

用法：
  python3 k2/tools/k2_sg_ds160pr810_pin_truth_crosscheck_v1.py \
      --pdf /tmp/opencode/sgaudit/ds160pr810.pdf \
      --yaml _shared/eda_core/sch_gate/datasheets/DS160PR810.yaml \
      --out-json /tmp/opencode/sgaudit/ds160pr810_crosscheck.json
"""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys

# Pin Functions 表所在页（TI SNLS658：§5 Pin Configuration and Functions；表体 = p4..p6，
# p3 为 Figure 5-1 封装俯视图 —— 其列排布会把 pin 号错读，故**排除**）。
PIN_TABLE_PAGES = (4, 6)

NAME_RE = r"[A-Z][A-Za-z0-9_]*(?:\s*/\s*[A-Za-z][A-Za-z0-9_]*)?"
# 行首 = NAME + 引脚号(可为逗号列表)；其后可有 I/O 类型（同行）或直接换行。
ROW_TYPED = re.compile(rf"^\s{{1,4}}({NAME_RE})\s+(\d{{1,2}}(?:\s*,\s*\d{{1,2}})*)\s*,?\s+[A-Za-z—\-].*$")
ROW_BARE = re.compile(rf"^\s{{1,4}}({NAME_RE})\s+(\d{{1,2}}(?:\s*,\s*\d{{1,2}})*)\s*$")
CONT_RE = re.compile(r"^\s+\d{1,2}(\s*,\s*\d{1,2})*,?\s*$")


def pdf_text(pdf: str, first: int, last: int) -> str:
    return subprocess.run(
        ["pdftotext", "-f", str(first), "-l", str(last), "-layout", pdf, "-"],
        check=True, capture_output=True, text=True).stdout


def parse_pin_functions(pdf: str) -> dict[int, str]:
    lines = pdf_text(pdf, *PIN_TABLE_PAGES).splitlines()
    rows: dict[str, set[int]] = {}
    for i, ln in enumerate(lines):
        m = ROW_TYPED.match(ln) or ROW_BARE.match(ln)
        if not m:
            continue
        name = re.sub(r"\s*/\s*", "_", m.group(1))
        nums = [int(x) for x in re.findall(r"\d{1,2}", m.group(2))]
        j = i + 1
        while j < len(lines) and CONT_RE.match(lines[j]):   # 折行续号（如 GND 的 53,56,64）
            nums += [int(x) for x in re.findall(r"\d{1,2}", lines[j])]
            j += 1
        rows.setdefault(name, set()).update(nums)
    # GND 行在 PDF 中拆三行（`EP, 9, 12, 21,` / `GND 24, 32, 41, 44,` / `53, 56, 64`）
    g = [i for i, l in enumerate(lines) if "EP, 9, 12, 21," in l]
    if g:
        rows["GND"] = set(int(x) for x in re.findall(r"\d{1,2}", "\n".join(lines[g[0]:g[0] + 3])))
    pin2name: dict[int, str] = {}
    dup: list[tuple[int, str, str]] = []
    for name, ps in rows.items():
        for p in ps:
            if p in pin2name:
                dup.append((p, name, pin2name[p]))
            pin2name[p] = name
    if dup:
        print(f"WARN duplicate pin numbers in PDF parse: {dup}", file=sys.stderr)
    return pin2name


def load_yaml_pins(path: str) -> dict[int, str]:
    import yaml  # 仅用于读取
    with open(path) as f:
        d = yaml.safe_load(f)
    return {int(k): v for k, v in d["pins"].items()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--yaml", required=True)
    ap.add_argument("--out-json")
    a = ap.parse_args(argv)

    pdf_sha = hashlib.sha256(open(a.pdf, "rb").read()).hexdigest()
    ds = parse_pin_functions(a.pdf)
    yp = load_yaml_pins(a.yaml)

    keys = sorted(set(ds) | set(yp))
    diff = [{"pad": p, "pdf": ds.get(p), "yaml": yp.get(p)} for p in keys if ds.get(p) != yp.get(p)]
    missing = sorted(set(range(1, 65)) - set(ds))          # 覆盖缺口（应为空）
    out_of_range = sorted(set(ds) - set(range(1, 65)))
    verdict = "PASS 64/64" if (not diff and not missing and not out_of_range and len(ds) == 64) else "FAIL"

    rep = {
        "artifact": "k2_sg_ds160pr810_pin_truth_crosscheck",
        "schema": 1,
        "id": "SG-AUDIT-1c",
        "authorization": "#K2-51 §二 SG-AUDIT-1「知悉 + 放行补检」· 只读",
        "device": "TI DS160PR810",
        "package": "WQFN-64 (NJX)",
        "doc": "TI SNLS658 (Rev B)",
        "table": "§5 Pin Functions (Table 5-1) + Figure 5-1",
        "pdf_sha256": pdf_sha,
        "method": "pdftotext -layout -f 4 -l 6（表体页；排除 p3 Figure 5-1 封装图以防列错读）→ 逐行 NAME+PIN 正则 + 折行续号合并",
        "coverage": {"parsed_pins": len(ds), "yaml_pins": len(yp),
                     "missing_in_pdf": missing, "out_of_range": out_of_range},
        "n_conflicts": len(diff),
        "conflicts": diff,
        "verdict": verdict,
    }
    print(f"{verdict}  conflicts={len(diff)}  parsed={len(ds)}  pdf_sha256={pdf_sha[:16]}")
    if diff:
        for d in diff:
            print("  DIFF", d)
    if a.out_json:
        json.dump(rep, open(a.out_json, "w"), ensure_ascii=False, indent=1)
        print("wrote", a.out_json)
    return 0 if verdict.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
