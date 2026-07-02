#!/usr/bin/env python3
"""Assign every PropertyKey to a scenario group and export CSV + grouped JSON."""
import csv
import json
import os
from collections import Counter, defaultdict

SP = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(SP + "/properties.json"))
recs = d["records"]

BUILDER_TYPE = {
    "booleanBuilder": "boolean", "intBuilder": "int", "longBuilder": "long",
    "doubleBuilder": "double", "durationBuilder": "duration",
    "dataSizeBuilder": "dataSize", "listBuilder": "list", "classBuilder": "class",
    "enumBuilder": "enum", "stringBuilder": "string", "new Builder": "custom",
}

# code -> (order, title). Files named <order>-<code>.md
GROUPS = {
    "01-client-fs-io":      "客户端文件系统与读写路径",
    "02-client-cache":      "客户端本地缓存 / 元数据缓存",
    "03-client-net-rpc":    "客户端网络 / RPC / 连接池",
    "04-worker-page-store": "Worker Page Store 存储引擎",
    "05-worker-s3-gateway": "Worker S3 API 网关",
    "06-worker-net-rpc":    "Worker 网络 / RPC / Web",
    "07-worker-mgmt":       "Worker 生命周期 / 成员 / 注册 / Rebalance",
    "08-worker-data-accel": "Worker 数据格式加速 (OCI/Parquet/Preload)",
    "10-ufs-common":        "UFS 通用行为 (挂载/元数据/一致性)",
    "11-ufs-s3":            "UFS S3 / 对象存储后端",
    "12-ufs-backends":      "UFS 各存储后端 (OSS/GCS/HDFS/OBS/COS/TOS/...)",
    "13-coordinator-master":"Coordinator / Master 元数据与调度",
    "14-membership-etcd":   "成员管理 / etcd / 一致性哈希 / 集群",
    "15-network-transport": "全局网络 / gRPC / 传输",
    "16-fuse":              "FUSE 挂载",
    "17-security":          "安全 / 认证 / 授权 / 审计",
    "18-observability":     "可观测性 (Metrics/Web/日志)",
    "19-write-ttl-quota":   "写入 / TTL / 配额",
    "20-jvm-system-misc":   "JVM / 进程 / 系统级 / 杂项",
}


def sw(n, *prefixes):
    return n.startswith(prefixes)


# For keys whose property-name string is built via format()/template and could
# not be resolved, route by their Java constant name instead.
def assign_by_const(const):
    c = const or ""
    if c.startswith("FUSE"):
        return "16-fuse"
    if c.startswith("MASTER_MOUNT"):
        return "13-coordinator-master"
    if c.startswith("UNDERFS"):
        return "10-ufs-common"
    if c.startswith("USER_CLIENT_CACHE") or c.startswith("USER_METADATA"):
        return "02-client-cache"
    if c.startswith("WORKER_JOB"):
        return "07-worker-mgmt"
    if c.startswith("WORKER_PARQUET") or c.startswith("WORKER_OCI"):
        return "08-worker-data-accel"
    if c.startswith("WRITE_BUFFER"):
        return "19-write-ttl-quota"
    return "20-jvm-system-misc"


def assign(n):
    # reroute a few otherwise-misc keys into their real scenario home
    if sw(n, "alluxio.hadoop.security"):
        return "17-security"
    if sw(n, "alluxio.priority.eviction"):
        return "04-worker-page-store"
    if sw(n, "alluxio.concurrent.write"):
        return "19-write-ttl-quota"
    if sw(n, "alluxio.stream.consistency"):
        return "01-client-fs-io"
    if sw(n, "alluxio.oci.registry"):
        return "12-ufs-backends"
    if (sw(n, "alluxio.security", "alluxio.security_server", "alluxio.user.security",
            "alluxio.underfs.security", "alluxio.access", "alluxio.audit")
            or ".kerberos" in n):
        return "17-security"
    if sw(n, "alluxio.fuse", "alluxio.user.fuse"):
        return "16-fuse"
    if sw(n, "alluxio.underfs.oss", "alluxio.underfs.gcs", "alluxio.underfs.cephfs",
            "alluxio.underfs.tos", "alluxio.underfs.hdfs", "alluxio.underfs.bos",
            "alluxio.underfs.obs", "alluxio.underfs.cos", "alluxio.underfs.nas",
            "alluxio.underfs.ozone", "alluxio.underfs.seaweedfs", "alluxio.underfs.gemini",
            "alluxio.underfs.huggingface",
            "fs.oss", "fs.obs", "fs.cos", "fs.tos", "fs.bos", "fs.nas",
            "fs.azure", "fs.gcs", "fs.huggingface"):
        return "12-ufs-backends"
    if sw(n, "alluxio.underfs.s3", "s3a.", "aws."):
        return "11-ufs-s3"
    if sw(n, "alluxio.underfs", "alluxio.mount"):
        return "10-ufs-common"
    if sw(n, "alluxio.worker.s3", "alluxio.worker.http", "alluxio.worker.rest",
            "alluxio.worker.sts", "alluxio.worker.secure"):
        return "05-worker-s3-gateway"
    if sw(n, "alluxio.worker.oci", "alluxio.worker.parquet", "alluxio.worker.preload"):
        return "08-worker-data-accel"
    if sw(n, "alluxio.worker.network", "alluxio.worker.rpc", "alluxio.worker.web",
            "alluxio.worker.bind"):
        return "06-worker-net-rpc"
    if sw(n, "alluxio.worker.page", "alluxio.worker.block", "alluxio.worker.ramdisk",
            "alluxio.worker.data", "alluxio.worker.free", "alluxio.worker.write",
            "alluxio.worker.ufs", "alluxio.worker.file", "alluxio.worker.async"):
        return "04-worker-page-store"
    if sw(n, "alluxio.worker"):
        return "07-worker-mgmt"
    if sw(n, "alluxio.user.client", "alluxio.user.metadata", "alluxio.user.local",
            "alluxio.user.logs", "alluxio.user.logging"):
        return "02-client-cache"
    if sw(n, "alluxio.user.network", "alluxio.user.rpc", "alluxio.user.worker",
            "alluxio.user.master", "alluxio.user.conf"):
        return "03-client-net-rpc"
    if sw(n, "alluxio.user", "alluxio.client"):
        return "01-client-fs-io"
    if sw(n, "alluxio.master", "alluxio.coordinator", "alluxio.job"):
        return "13-coordinator-master"
    if sw(n, "alluxio.dora", "alluxio.etcd", "alluxio.cluster", "alluxio.node",
            "alluxio.foundationdb", "license.etcd", "alluxio.membership"):
        return "14-membership-etcd"
    if sw(n, "alluxio.network", "alluxio.grpc"):
        return "15-network-transport"
    if sw(n, "alluxio.metrics", "alluxio.web", "alluxio.logs", "alluxio.logger"):
        return "18-observability"
    if sw(n, "alluxio.write", "alluxio.ttl", "alluxio.quota"):
        return "19-write-ttl-quota"
    return "20-jvm-system-misc"


grouped = defaultdict(list)
rows = []
for r in recs:
    n = r.get("name")
    if not n:
        n = "<unresolved:%s>" % r.get("name_const", r.get("const"))
    g = assign(n) if r.get("name") else assign_by_const(r.get("const"))
    typ = BUILDER_TYPE.get(r.get("builder", ""), r.get("builder", ""))
    row = {
        "group": g, "group_title": GROUPS[g], "name": n,
        "type": typ, "default": r.get("default", ""),
        "scope": r.get("scope", ""), "consistency": r.get("consistency", ""),
        "aliases": "; ".join(r.get("aliases", []) or []),
        "deprecated": "Y" if r.get("deprecated") else "",
        "deprecated_message": r.get("deprecated_message", ""),
        "const": r.get("const", ""), "description": r.get("description", ""),
    }
    rows.append(row)
    grouped[g].append(row)

# CSV
cols = ["group", "group_title", "name", "type", "default", "scope",
        "consistency", "aliases", "deprecated", "deprecated_message",
        "const", "description"]
with open(SP + "/properties.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in sorted(rows, key=lambda x: (x["group"], x["name"])):
        w.writerow(r)

# grouped JSON (for building per-group docs later)
json.dump({g: grouped[g] for g in GROUPS if g in grouped},
          open(SP + "/grouped.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

print("total rows:", len(rows))
print("\n== per-group counts ==")
c = Counter(r["group"] for r in rows)
for g in GROUPS:
    print("  %-24s %3d  %s" % (g, c.get(g, 0), GROUPS[g]))

print("\n== misc bucket (20) contents ==")
for r in sorted(grouped["20-jvm-system-misc"], key=lambda x: x["name"]):
    print("  ", r["name"])
