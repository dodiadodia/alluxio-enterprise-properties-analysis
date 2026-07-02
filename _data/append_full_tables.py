#!/usr/bin/env python3
"""Append a script-generated COMPLETE property table to group docs that have gaps,
so every registered key literally appears as a row (guarantees 全量入表)."""
import json
import os
import re
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
ANALYSIS = os.path.dirname(HERE)
grouped = json.load(open(os.path.join(HERE, "grouped.json"), encoding="utf-8"))

MARK = "## 附录A:本组全量配置清单(脚本生成)"


def full_table(code):
    rows = sorted(grouped[code], key=lambda r: r["name"])
    out = [MARK, "",
           "> 由 `_data/gen_table.py %s` 生成,逐 key 一行,保证覆盖本组**全部 %d 项**"
           "(与上文按子场景组织的中文速查表互补;此处描述为官方英文原文,便于精确检索)。"
           % (code, len(rows)), "",
           "| 配置项 | 默认值 | 类型 | Scope | 一致性 | 状态 | 说明 |",
           "|---|---|---|---|---|---|---|"]
    for r in rows:
        desc = (r.get("description", "") or "").replace("|", "\\|")
        if len(desc) > 150:
            desc = desc[:147] + "..."
        dflt = (r.get("default", "") or "").replace("|", "\\|") or "—"
        status = []
        if r.get("deprecated"):
            dm = (r.get("deprecated_message") or "").strip()
            status.append("⚠️废弃" + (("→" + dm) if dm else ""))
        if r.get("aliases"):
            status.append("别名:" + r["aliases"].replace("|", "\\|"))
        st = "; ".join(status) or "—"
        out.append("| `%s` | %s | %s | %s | %s | %s | %s |" % (
            r["name"], dflt, r.get("type", "") or "—",
            r.get("scope", "") or "—", r.get("consistency", "") or "—",
            st, desc or "—"))
    return "\n".join(out) + "\n"


# find gappy docs
gappy = []
for f in sorted(glob.glob(os.path.join(ANALYSIS, "[0-9][0-9]-*.md"))):
    code = os.path.basename(f)[:-3]
    if code not in grouped:
        continue
    txt = open(f, encoding="utf-8").read()
    names = [r["name"] for r in grouped[code]]
    missing = [n for n in names if n not in txt]
    if missing and MARK not in txt:
        gappy.append((f, code, len(missing)))

for f, code, nmiss in gappy:
    with open(f, "a", encoding="utf-8") as fh:
        fh.write("\n---\n\n" + full_table(code))
    print("appended full table to %-32s (had %d missing)" % (os.path.basename(f), nmiss))

print("\ndone. docs updated:", len(gappy))
