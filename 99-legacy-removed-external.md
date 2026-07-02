# 99 · 已移除 / 未注册 / 外部引用 key(附录)

> **附录性质**:本文覆盖**不在当前 main 分支注册集(1243 项 + 别名)** 里、但仍出现在仓库配置/文档中的 `alluxio.*` key。
> 目的:防止照旧配置/旧文档设置**已失效的 key**(静默忽略)而不自知。
> 数据来源:`_data/scan_wild.py`(扫 `conf/`、`integration/`、`dev/docs/` 等)· 结果:`_data/wild_keys.json`
> ⚠️ 本组结论多为**启发式**,采用前请逐项 `git log -S <key>` / 查代码确认(标注为"建议验证")。

---

## 1. 扫描方法与口径

- **已知集**:`PropertyKey.java` 注册的 1243 项**名称 + 133 项别名** = 1346 个已知 key。
- **扫描范围**:`conf/`、`integration/`(含 proxy README、k8s helm、oci-proxy)、`dev/docs/`、`bin/`、`libexec/` 下的 `.properties/.yaml/.md/.sh/.conf/...`。
- **过滤**:剔除含大写字母的 token(Java 类名/logger 名/测试名,非配置 key)。
- **命中**:出现在上述文件、但不在已知集里的 `alluxio.*`/`fs.*` key,共 **17** 个。
- **历史分类**:`was_in_pk_history` = 该 key 曾出现在 `PropertyKey.java` 的 git 历史中(即"曾注册、后移除/改名"的强信号)。

---

## 2. 命中清单(17 项)

| key | 出现位置(首个) | 曾注册? | 初步判定 | 建议 |
|---|---|:--:|---|---|
| `alluxio.worker.s3.only.read.current.worker.data.enabled` | integration/proxy/README.md:208 | 是 | **已从 main 移除**(提交 5500a0e0168) | ⚠️设了会被静默忽略;用 `worker.s3.only.read.cache.data.enabled`([05](05-worker-s3-gateway.md)) |
| `alluxio.dora.enabled` | k8s trino withEdge.yaml:58 | 是 | 疑似已移除/恒开 | 建议验证是否仍需设 |
| `alluxio.user.metrics.collection.enabled` | k8s trino withEdge.yaml:60 | 是 | 疑似已移除/改名 | 建议验证,可能迁到 [18](18-observability.md) metrics |
| `alluxio.client.cache.dirs` | k8s trino withEdge.yaml:62 | 否 | Hadoop-SDK 风格旧名 | 对应注册项 `user.client.cache.dirs`([02](02-client-cache.md)) |
| `alluxio.client.cache.size` | k8s trino withEdge.yaml:61 | 否 | Hadoop-SDK 风格旧名 | 对应 `user.client.cache.size`([02](02-client-cache.md)) |
| `alluxio.underfs.s3.access.key` | dev/docs/ALLUXIO-OPS-PLAYBOOK.md:219 | 否 | Hadoop 风格 S3 凭证(透传 SDK) | 现代用 `s3a.accessKeyId`/AssumeRole/CVS([11](11-ufs-s3.md)) |
| `alluxio.underfs.s3.secret.key` | dev/docs/ALLUXIO-OPS-PLAYBOOK.md:220 | 否 | 同上 ⚠️敏感 | 同上,走密管([17](17-security.md)) |
| `alluxio.underfs.s3.aws.access.key` | dev/docs/ALLUXIO-OPS-PLAYBOOK.md:222 | 否 | 同上 | 同上 |
| `alluxio.worker.data.load.staging.enabled` | dev/docs/DISTRIBUTED-LOAD-DESIGN.md:288 | 是 | 设计文档中的 key(可能未落地/已改) | 建议验证是否已实现 |
| `alluxio.worker.data.load.staging.buffer.size` | dev/docs/DISTRIBUTED-LOAD-DESIGN.md:270 | 是 | 同上 | 建议验证 |
| `alluxio.worker.load.admission.budget.ratio` | dev/docs/DISTRIBUTED-LOAD-DESIGN.md:371 | 是 | 设计文档 key | 建议验证 |
| `alluxio.worker.job.executor.task.queue.size` | dev/docs/DISTRIBUTED-LOAD-DESIGN.md:279 | 是 | **实为注册项**(模板名未被本扫描识别) | 已在 [07](07-worker-mgmt.md),非真缺失 |
| `alluxio.worker.oci.registry.cache.blacklist.local` | integration/oci-proxy/README.md:209 | 是 | 疑似与 `cache.blacklist.etcd.path` 相关变体 | 建议验证([08](08-worker-data-accel.md)) |
| `alluxio.worker.http.port` | integration/oci-proxy/REST_API.md:11 | 否 | 文档简写 | 实为 `worker.http.server.port`([05](05-worker-s3-gateway.md)) |
| `alluxio.master.audit` | dev/docs/BUILD.md:64 | 是 | **截断/前缀**(非完整 key) | 误报,忽略 |
| `alluxio.worker.s3` | dev/docs/ALLUXIO-OPS-PLAYBOOK.md:364 | 是 | 日志级别前缀(如 `alluxio.worker.s3=DEBUG`) | 误报(是 logger 名非配置 key) |
| `alluxio.azurecr.io` | integration/oci-proxy/README.md:316 | 否 | 主机名(azurecr.io)误匹配 | 误报,忽略 |

---

## 3. 分类小结

### 3.1 真·已移除(照旧配置会静默失效)
- **`only.read.current.worker.data.enabled`** —— 确证已从 main 删除(见本任务过程)。**这是本附录的核心案例**:仓库文档(proxy README、ops playbook)仍在推荐它,但代码已删,设了会记 "unknown property" 警告并忽略。迁移到 `only.read.cache.data.enabled`。
- `dora.enabled` / `user.metrics.collection.enabled` —— 曾注册、现不在;疑似移除或改名(建议验证)。

### 3.2 Hadoop 风格透传 key(不是注册项,但可能被 SDK 消费)
- `alluxio.client.cache.{dirs,size}`(对应注册的 `user.client.cache.*`)、`alluxio.underfs.s3.{access,secret}.key`——这些是 Hadoop/SDK 习惯写法,建议改用注册项名。

### 3.3 设计文档中的前瞻 key(可能未落地)
- `worker.data.load.staging.*`、`worker.load.admission.budget.ratio` —— 出现在 `DISTRIBUTED-LOAD-DESIGN.md`,可能是设计草案 key,未必已实现(建议验证)。

### 3.4 误报(扫描噪声,非真 key)
- `alluxio.master.audit`(截断)、`alluxio.worker.s3`(logger 级别前缀)、`alluxio.azurecr.io`(主机名)、`alluxio.worker.http.port`(文档简写)。

---

## 4. 使用建议

1. **迁移旧配置前先对表**:部署配置里若出现本表左列的 key,按"建议"列迁移到注册项名。
2. **`git log -S <key> -- '*.java'`** 可确认某 key 的历史(何时加入/移除)。
3. **重跑刷新**:代码/文档变更后 `python3 _data/scan_wild.py --history` 重新扫描。
4. **本附录是启发式**:误报已尽量标注,但采用结论前建议逐项验证。

---

## 跨组关联速览
- [05-worker-s3-gateway](05-worker-s3-gateway.md) —— `only.read.cache.data.enabled`(替代已移除项)
- [02-client-cache](02-client-cache.md) —— `user.client.cache.*`(替代 `client.cache.*`)
- [11-ufs-s3](11-ufs-s3.md) —— S3 凭证正规写法
- [08-worker-data-accel](08-worker-data-accel.md) —— OCI 镜像相关 key
- 主索引:[README.md](README.md)
