#!/usr/bin/env python3
"""Emit a Markdown table (全量入表) for a given scenario group.

Usage: python3 gen_table.py <group-code> [--sub N]
  <group-code>  e.g. 05-worker-s3-gateway  (or just "05")
  --full        also print full (untruncated) descriptions

Reads grouped.json produced by categorize.py (same directory).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, "grouped.json"), encoding="utf-8"))

if len(sys.argv) < 2:
    print("groups:")
    for g in sorted(data):
        print("  %-24s %d" % (g, len(data[g])))
    sys.exit(0)

sel = sys.argv[1]
full = "--full" in sys.argv
key = sel if sel in data else next((g for g in data if g.startswith(sel)), None)
if not key:
    print("no such group:", sel)
    sys.exit(1)

rows = sorted(data[key], key=lambda r: r["name"])
n_dep = sum(1 for r in rows if r.get("deprecated"))
n_alias = sum(1 for r in rows if r.get("aliases"))
print("<!-- group: %s | count: %d | deprecated: %d | aliased: %d -->"
      % (key, len(rows), n_dep, n_alias))
print("| 配置项 | 默认值 | 类型 | Scope | 一致性 | 说明 |")
print("|---|---|---|---|---|---|")
for r in rows:
    desc = r.get("description", "").replace("|", "\\|")
    if not full and len(desc) > 150:
        desc = desc[:147] + "..."
    prefix = ""
    if r.get("deprecated"):
        dm = (r.get("deprecated_message") or "").strip()
        prefix += "⚠️**已废弃**%s " % (("(迁移: %s)" % dm) if dm else "")
    if r.get("aliases"):
        prefix += "[别名: %s] " % r["aliases"].replace("|", "\\|")
    dflt = (r.get("default", "") or "").replace("|", "\\|")
    print("| `%s` | %s | %s | %s | %s | %s%s |" % (
        r["name"], dflt or "—", r.get("type", ""),
        r.get("scope", "") or "—", r.get("consistency", "") or "—",
        prefix, desc or "—"))
