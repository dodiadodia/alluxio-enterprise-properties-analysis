#!/usr/bin/env python3
"""Scan deployment configs & docs for alluxio.* keys NOT in the registered set.

Surfaces keys that users may still set (from old configs, docs, k8s manifests,
proxy README, playbooks) but that are removed / renamed / never-registered on the
current branch. Output: _data/wild_keys.json + console summary.
"""
import json
import os
import re
import subprocess

REPO = "/root/work/enterprise"
HERE = os.path.dirname(os.path.abspath(__file__))

# Registered names + aliases (the "known" set on current branch)
props = json.load(open(os.path.join(HERE, "properties.json"), encoding="utf-8"))
known = set()
for r in props["records"]:
    if r.get("name") and not r["name"].startswith("<"):
        known.add(r["name"])
    for a in r.get("aliases", []) or []:
        known.add(a)

# Config/doc file globs to scan (NOT java/go source — those define, not consume)
INCLUDE_DIRS = [
    "conf", "integration", "dev/docs", "bin", "libexec",
]
EXTS = (".properties", ".template", ".yaml", ".yml", ".md", ".conf",
        ".sh", ".env", ".txt", ".json")

KEY_RE = re.compile(r'\b((?:alluxio|fs\.cos|fs\.oss|fs\.obs|fs\.tos|fs\.bos|'
                    r'fs\.nas|fs\.azure|fs\.gcs|fs\.huggingface|s3a|aws)\.[a-zA-Z0-9_.]*[a-zA-Z0-9_])')

wild = {}  # key -> list of "relpath:line"
for d in INCLUDE_DIRS:
    base = os.path.join(REPO, d)
    for root, _, files in os.walk(base):
        for fn in files:
            if not fn.endswith(EXTS):
                continue
            fp = os.path.join(root, fn)
            rel = os.path.relpath(fp, REPO)
            try:
                for i, line in enumerate(open(fp, encoding="utf-8", errors="ignore"), 1):
                    for m in KEY_RE.finditer(line):
                        key = m.group(1)
                        # ignore obvious non-keys / too-short
                        if key.count(".") < 2:
                            continue
                        # real property keys are all-lowercase dotted; skip class /
                        # logger / test names (they carry CamelCase segments)
                        if any(c.isupper() for c in key):
                            continue
                        if key in known:
                            continue
                        wild.setdefault(key, [])
                        if len(wild[key]) < 6:
                            wild[key].append("%s:%d" % (rel, i))
            except Exception:
                pass

# Optional (slow): classify each wild key as removed (in git java history) vs typo.
# Enabled only with --history because pickaxe over full history is expensive.
CHECK_HISTORY = "--history" in os.sys.argv


def in_history(key):
    try:
        out = subprocess.run(
            ["git", "-C", REPO, "log", "--all", "--oneline", "-S", key, "--",
             "dora/core/common/src/main/java/alluxio/conf/PropertyKey.java"],
            capture_output=True, text=True, timeout=20)
        return bool(out.stdout.strip())
    except Exception:
        return False


result = []
for key in sorted(wild):
    rec = {"key": key, "seen_in": wild[key], "count": len(wild[key])}
    if CHECK_HISTORY:
        rec["was_in_pk_history"] = in_history(key)
    result.append(rec)

json.dump(result, open(os.path.join(HERE, "wild_keys.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

print("known (names+aliases):", len(known))
print("wild keys (in configs/docs, not registered):", len(result))
print()
for r in result:
    tag = ""
    if CHECK_HISTORY:
        tag = " [was in PK history]" if r.get("was_in_pk_history") else " [never in PK]"
    print("  %-58s %s%s" % (r["key"], r["seen_in"][0], tag))
