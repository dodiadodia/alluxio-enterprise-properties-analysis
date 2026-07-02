#!/usr/bin/env python3
"""Parse Alluxio PropertyKey.java into structured records.

Extracts, per registered PropertyKey: constant name, property string,
builder type, default value, description, scope, consistency level.
"""
import json
import os
import re
import sys
from collections import Counter

PK = "/root/work/enterprise/dora/core/common/src/main/java/alluxio/conf/PropertyKey.java"

src = open(PK, encoding="utf-8").read()
lines = src.splitlines()

# ---- Pass 1: Name inner-class constants -> actual property string ----
# e.g.  public static final String WORKER_S3_API_ENABLED = "alluxio.worker.s3.api.enabled";
name_map = {}
name_re = re.compile(r'public static final String (\w+)\s*=\s*"([^"]+)"\s*;')
for m in name_re.finditer(src):
    name_map[m.group(1)] = m.group(2)

# Also capture templated / format-built name strings (best effort): constants whose
# value is a format(...) — record raw expression so we know they exist.
name_expr_re = re.compile(r'public static final String (\w+)\s*=\s*([^;]+);', re.S)
templated_names = {}
for m in name_expr_re.finditer(src):
    k, v = m.group(1), m.group(2).strip()
    if k not in name_map:
        templated_names[k] = " ".join(v.split())

# ---- Pass 2: PropertyKey definitions ----
# Find each:  public static final PropertyKey CONST =  ... .build();
records = []
# Iterate over occurrences of the declaration head.
decl_re = re.compile(r'public static final PropertyKey (\w+)\s*=')
for m in decl_re.finditer(src):
    const = m.group(1)
    start = m.end()
    # Grab the block up to the terminating .build(); (first one after start)
    tail = src[start:]
    bm = re.search(r'\.build\(\)\s*;', tail)
    if not bm:
        continue
    block = tail[:bm.end()]

    rec = {"const": const}

    # builder type + name reference
    bt = re.search(r'(\w*Builder|new Builder)\s*\(\s*(?:PropertyType\.\w+\s*,\s*)?Name\.(\w+)', block)
    if bt:
        rec["builder"] = bt.group(1)
        rec["name_const"] = bt.group(2)
        rec["name"] = name_map.get(bt.group(2))
        if rec["name"] is None and bt.group(2) in templated_names:
            rec["name"] = "<templated:%s>" % templated_names[bt.group(2)]
    else:
        # some use Name.X directly without builder helper
        nm = re.search(r'Name\.(\w+)', block)
        if nm:
            rec["name_const"] = nm.group(1)
            rec["name"] = name_map.get(nm.group(1))

    # default value
    dv = re.search(r'\.setDefaultValue\((.*?)\)\s*\n', block, re.S)
    if not dv:
        dv = re.search(r'\.setDefaultValue\((.*?)\)\s*\.', block, re.S)
    if dv:
        rec["default"] = " ".join(dv.group(1).split())

    # scope
    sc = re.search(r'\.setScope\(Scope\.(\w+)\)', block)
    if sc:
        rec["scope"] = sc.group(1)

    # consistency level
    cc = re.search(r'\.setConsistencyCheckLevel\(ConsistencyCheckLevel\.(\w+)\)', block)
    if cc:
        rec["consistency"] = cc.group(1)

    # is aliased / deprecated markers
    if ".setIsHidden(true)" in block:
        rec["hidden"] = True

    # aliases: .setAlias("a", "b", Name.X) — collect string literals + resolved Name refs
    aliases = []
    for am in re.finditer(r'\.setAlias\(([^;]*?)\)\s*\n', block):
        arg = am.group(1)
        aliases += re.findall(r'"([^"]+)"', arg)
        for nm in re.findall(r'Name\.(\w+)', arg):
            if nm in name_map:
                aliases.append(name_map[nm])
    if aliases:
        rec["aliases"] = aliases

    # deprecated: @Deprecated annotation sits BEFORE the declaration (not in block).
    # Look only at the gap between the previous statement and this declaration.
    pre = src[max(0, m.start() - 500):m.start()]
    gap = pre.rsplit(";", 1)[-1]  # text after previous statement's terminating ';'
    dm = re.search(r'@Deprecated\s*(?:\(\s*message\s*=\s*(.*?)\)\s*)?$', gap, re.S)
    desc_dep = bool(re.search(r'\bDeprecated\b', block))
    if dm or desc_dep:
        rec["deprecated"] = True
        if dm and dm.group(1):
            lits = re.findall(r'"([^"]*)"', dm.group(1))
            msg = " ".join(lits)
            for nm in re.findall(r'Name\.(\w+)', dm.group(1)):
                if nm in name_map:
                    msg += " " + name_map[nm]
            rec["deprecated_message"] = " ".join(msg.split())

    # description: capture setDescription( ... ) balancing parens
    di = block.find(".setDescription(")
    if di != -1:
        j = di + len(".setDescription(")
        depth = 1
        buf = []
        while j < len(block) and depth > 0:
            ch = block[j]
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    break
            buf.append(ch)
            j += 1
        raw = "".join(buf)
        # join concatenated string literals; drop format() scaffolding but keep text
        # extract all "..." literals
        lits = re.findall(r'"((?:[^"\\]|\\.)*)"', raw)
        desc = "".join(lits)
        desc = desc.replace('\\"', '"').replace("\\n", " ").replace("\\t", " ")
        desc = " ".join(desc.split())
        rec["description"] = desc
        # note if description referenced other keys via format placeholders
        if "%s" in desc or "format(" in raw:
            rec["desc_has_refs"] = True

    records.append(rec)

# ---- Summary ----
by_prefix = Counter()
for r in records:
    nm = r.get("name") or ""
    parts = nm.split(".")
    if len(parts) >= 2:
        by_prefix["%s.%s" % (parts[0], parts[1])] += 1
    else:
        by_prefix["<other>"] += 1

out = {
    "total_registered": len(records),
    "with_name": sum(1 for r in records if r.get("name")),
    "with_description": sum(1 for r in records if r.get("description")),
    "with_default": sum(1 for r in records if "default" in r),
    "with_alias": sum(1 for r in records if r.get("aliases")),
    "deprecated": sum(1 for r in records if r.get("deprecated")),
    "by_prefix": dict(by_prefix.most_common()),
    "records": records,
}

outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "properties.json")
json.dump(out, open(outpath, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("registered PropertyKey defs :", out["total_registered"])
print("resolved name               :", out["with_name"])
print("with description            :", out["with_description"])
print("with default value          :", out["with_default"])
print("with alias(es)              :", out["with_alias"])
print("deprecated                  :", out["deprecated"])
print("written to                  :", outpath)
