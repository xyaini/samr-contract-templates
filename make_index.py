import os, json, re
from collections import defaultdict

ROOT = "/var/minis/workspace/samr_contracts/dl"
rows = []
for dp, dn, fn in os.walk(ROOT):
    for f in fn:
        p = os.path.join(dp, f)
        rel = os.path.relpath(p, ROOT)
        parts = rel.split(os.sep)
        cat = parts[0]
        dept = parts[1] if len(parts) > 2 else ""
        rows.append((cat, dept, os.path.splitext(f)[0], os.path.splitext(f)[1].lstrip(".").upper(),
                     os.path.getsize(p), rel))

rows.sort(key=lambda r: (r[0], r[1], r[2], r[3]))
lines = ["# 全国合同示范文本库 全量下载清单", "",
         f"- 来源：国家市场监督管理总局 · 合同示范文本库（{chr(104)+'ttps://htsfwb.samr.gov.cn'}）",
         "- 下载日期：2026-10-27",
         f"- 文件总数：{len(rows)}（{len(set(r[2] for r in rows))} 份合同，Word + PDF 两种格式）",
         f"- 总体积：约 {sum(r[4] for r in rows)/1048576:.0f} MB", "",
         "每份合同同时提供 Word（可编辑，.doc/.docx/.wps）与 PDF（定稿排版）两个版本。", ""]

bycat = defaultdict(list)
for r in rows:
    bycat[r[0]].append(r)

for cat in sorted(bycat):
    items = bycat[cat]
    names = sorted(set((r[1], r[2]) for r in items))
    lines.append(f"## {cat}（{len(names)} 份 / {len(items)} 个文件）")
    lines.append("")
    lines.append("| # | 部门/地区 | 合同名称 | 格式 |")
    lines.append("|---|---|---|---|")
    for i, (dept, name) in enumerate(names, 1):
        fmts = ",".join(sorted(set(r[3] for r in items if r[2] == name)))
        lines.append(f"| {i} | {dept} | {name} | {fmts} |")
    lines.append("")

open("/var/minis/workspace/samr_contracts/合同清单.md", "w").write("\n".join(lines))
print("rows", len(rows), "cats", len(bycat))
print({c: len(set(r[2] for r in v)) for c, v in bycat.items()})
