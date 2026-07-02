# Alluxio Enterprise 配置(Properties)全量分析

> 从代码角度系统梳理 Alluxio Enterprise 的全部配置项:每项的作用、不同取值的影响、以及配置间的相互关联。
> 按**业务场景**分组,采用**分层深度**(全量入表 + 重点深挖)。本任务可随时中断续作,进度见下方看板。

---

## 1. 数据来源与方法

| 项 | 说明 |
|---|---|
| **权威来源** | `enterprise/dora/core/common/src/main/java/alluxio/conf/PropertyKey.java`(14687 行) |
| **提取方式** | 脚本解析每个 `PropertyKey` 定义,抽取:名称 / 类型 / 默认值 / 官方描述 / Scope / 一致性级别 |
| **总量** | 注册 PropertyKey **1243** 项(其中 1230 项解析出名称、1210 项带描述、1052 项带默认值) |
| **分组** | 按业务场景归入 **19 个场景组 + 1 个杂项组**,每项唯一归属 |

### 复现/更新数据(代码变更后重跑)

```sh
cd analysis/_data
python3 parse_props.py      # PropertyKey.java -> properties.json
python3 categorize.py       # 归组 -> properties.csv / grouped.json
python3 gen_table.py 05     # 打印某组的 Markdown 全量表(如 05-worker-s3-gateway)
```

- `_data/properties.csv` —— **全量 1243 项结构化清单**(可直接用 Excel/表格工具筛选)
- `_data/grouped.json` —— 按组聚合的结构化数据(生成文档用)

---

## 2. 分析深度约定(分层)

- **全量入表**:每个分组文档开头有一张"配置清单速查表",覆盖该组**所有**配置(名称/默认值/类型/Scope/一致性/官方说明)。→ 保证不漏。经脚本校验,19 组**零覆盖缺口**(每个注册 key 都在其文档中出现)。
- **充分细节深挖**(已全面升级):第 3 节"逐项深度分析(充分细节)"对该组**每一个配置族**逐一深挖——不同取值/枚举的行为差异、影响取舍、族内/跨族关联、以及**翻代码求证的机制**。深挖中还纠正了多处"官方 description 与代码实现不符"的偏差(均以代码为准,并对不确定项标注"建议验证")。
- **附录 A(部分文档)**:对采用矩阵/家族合并的文档,附一张脚本生成的全量清单(逐 key 一行),保证 Ctrl-F 可检索到每一项。
- **关联关系**:用 Mermaid 图 + 关系表表达配置间的耦合;跨组关联在文末"跨组关联"小节点明。
- **别名 / 废弃(内联标注)**:表内对有别名的项标 `[别名: ...]`,对 `@Deprecated` 项标 `⚠️已废弃(迁移: ...)`(数据来自代码,133 项别名 / 15 项废弃)。
- **历史变更 / 已移除 / 外部引用**:降级为**最后一个任务**(见索引 99),扫描结果已存 `_data/wild_keys.json`,主线全部完成后再单独成附录,不在每组文档展开。

### 每个分组文档统一结构(6 段式)

1. 本组概览 —— 这组配置管什么、核心矛盾
2. 配置清单速查表 —— 全量入表
3. 逐项深度分析 —— 重点项深挖
4. 配置关联关系图 —— Mermaid + 关系表
5. 典型场景配置组合建议
6. 风险与注意事项(含一致性级别提示、易混淆命名)

---

## 3. 场景分组索引 + 进度看板

> 状态:⬜ 未开始 · 🟡 进行中 · ✅ 已完成 · 📋 仅入表(暂未深挖)

| # | 文档 | 场景 | 配置数 | 状态 |
|---|---|---|---:|:--:|
| 01 | [01-client-fs-io.md](01-client-fs-io.md) | 客户端文件系统与读写路径 | 118 | ✅ |
| 02 | [02-client-cache.md](02-client-cache.md) | 客户端本地缓存 / 元数据缓存 | 56 | ✅ |
| 03 | [03-client-net-rpc.md](03-client-net-rpc.md) | 客户端网络 / RPC / 连接池 | 58 | ✅ |
| 04 | [04-worker-page-store.md](04-worker-page-store.md) | Worker Page Store 存储引擎 | 73 | ✅ |
| 05 | [05-worker-s3-gateway.md](05-worker-s3-gateway.md) | Worker S3 API 网关 | 56 | ✅ |
| 06 | [06-worker-net-rpc.md](06-worker-net-rpc.md) | Worker 网络 / RPC / Web | 60 | ✅ |
| 07 | [07-worker-mgmt.md](07-worker-mgmt.md) | Worker 生命周期 / 成员 / 注册 / Rebalance | 26 | ✅ |
| 08 | [08-worker-data-accel.md](08-worker-data-accel.md) | Worker 数据格式加速 (OCI/Parquet/Preload) | 31 | ✅ |
| 10 | [10-ufs-common.md](10-ufs-common.md) | UFS 通用行为 (挂载/元数据/一致性) | 37 | ✅ |
| 11 | [11-ufs-s3.md](11-ufs-s3.md) | UFS S3 / 对象存储后端 | 74 | ✅ |
| 12 | [12-ufs-backends.md](12-ufs-backends.md) | UFS 各存储后端 (OSS/GCS/HDFS/OBS/COS/TOS/...) | 143 | ✅ |
| 13 | [13-coordinator-master.md](13-coordinator-master.md) | Coordinator / Master 元数据与调度 | 94 | ✅ |
| 14 | [14-membership-etcd.md](14-membership-etcd.md) | 成员管理 / etcd / 一致性哈希 / 集群 | 56 | ✅ |
| 15 | [15-network-transport.md](15-network-transport.md) | 全局网络 / gRPC / 传输 | 41 | ✅ |
| 16 | [16-fuse.md](16-fuse.md) | FUSE 挂载 | 82 | ✅ |
| 17 | [17-security.md](17-security.md) | 安全 / 认证 / 授权 / 审计 | 118 | ✅ |
| 18 | [18-observability.md](18-observability.md) | 可观测性 (Metrics/Web/日志) | 26 | ✅ |
| 19 | [19-write-ttl-quota.md](19-write-ttl-quota.md) | 写入 / TTL / 配额 | 52 | ✅ |
| 20 | [20-jvm-system-misc.md](20-jvm-system-misc.md) | JVM / 进程 / 系统级 / 杂项 | 42 | ✅ |
| | | **合计** | **1243** | |
| 99 | [99-legacy-removed-external.md](99-legacy-removed-external.md) | 已移除 / 未注册 / 外部引用 key(附录) | 17 | ✅ |

---

## 4. 续作说明(How to resume)

1. 看本页进度看板,挑一个 ⬜ 的分组。
2. `python3 _data/gen_table.py <编号>` 生成该组全量表,粘进文档第 2 节。
3. 按 6 段式补齐深挖分析,完成后把看板状态改为 ✅。
4. 跨组强关联(如 S3 网关 ↔ Page Store ↔ 一致性哈希)在各自文档"跨组关联"小节互相链接,不重复展开。

## 5. 说明与边界

- 分析基于当前分支代码的 `PropertyKey.java`;版本升级后重跑 `_data` 脚本即可刷新。
- 少量配置名通过 `format()` 模板拼接,已按 Java 常量名归组并在文档内标注(见各组"待确认"标记)。
- 深挖内容中的调优建议为**基于代码描述与架构的分析性建议**,生产环境采用前建议结合实际压测验证(标注为"建议验证")。
