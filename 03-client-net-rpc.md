# 03 · 客户端网络 / RPC / 连接池

> 场景组:`alluxio.user.network.*` + `alluxio.user.rpc.*` + `alluxio.user.worker.*`(选择策略) + `alluxio.user.conf.*` + `alluxio.user.master.*`
> 配置数:**58** · 别名 12 · 废弃 9 · 数据来源:`PropertyKey.java` · 生成表:`_data/gen_table.py 03`

---

## 1. 本组概览

本组管**客户端到 master/worker 的传输层**:gRPC 连接参数、重试、worker 选择算法、配置同步。理解本组的关键是**三套连接族的历史演进**:

| 连接族 | 前缀 | 状态 | 用途 |
|---|---|---|---|
| **legacy netty** | `user.network.netty.*`、`user.network.{keepalive,flowcontrol,zerocopy}.*` | 部分**⚠️已废弃**(9 项),部分**仍在用** | channel/keepalive/flowcontrol 语义已被取代;cumulator/packets/pool/timeout 仍服务 netty 数据读写 |
| **rpc(gRPC 控制面)** | `user.network.rpc.*`、`user.rpc.*` | 现役 | 元数据/控制 RPC(RPC/CVS 分组) |
| **streaming(gRPC 数据面)** | `user.network.streaming.*` | 现役 | 块读写数据流(STREAMING 分组) |

> `network.{keepalive,flowcontrol,max.inbound}.*` 顶级名及 `network.netty.channel` 已被 `network.streaming.*` / `network.rpc.*` 取代,旧名多作为新名的**别名**保留;但 `network.netty.*` 里的 cumulator/packets/pool/timeout **仍服务于活着的 netty 数据客户端,不是废弃项**(见 3.1、3.10)。配置连接参数时用 `rpc.*` / `streaming.*` 新名。

四个子场景:

| 子场景 | 关键配置 | 核心矛盾 |
|---|---|---|
| gRPC 连接与保活 | `network.rpc.keepalive.*`、`network.streaming.keepalive.*`、`*.flowcontrol.window`、`*.max.inbound.message.size` | 吞吐/连通性 vs 内存 |
| 连接数与线程 | `network.rpc.max.connections`、`network.streaming.max.connections`、`*.netty.worker.threads` | 并发 vs 资源 |
| worker 选择算法 | `worker.selection.policy.type`、`consistent.hash.provider.impl`、`ketama/maglev/multi.probe.*` | 均衡性 vs 稳定性 |
| RPC 重试 | `rpc.retry.base.sleep`、`rpc.retry.max.sleep`、`rpc.retry.max.duration` | 韧性 vs 故障放大 |

---

## 2. 配置清单速查表(全量 58 项)

### 2.1 gRPC 控制面(rpc)与配置同步
| 配置项 | 默认值 | 类型 | Scope | 一致性 | 说明 |
|---|---|---|---|---|---|
| `alluxio.user.network.rpc.flowcontrol.window` | 2MiB | dataSize | CLIENT | WARN | rpc 连接的 HTTP2 流控窗口 |
| `alluxio.user.network.rpc.max.inbound.message.size` | 100MiB | dataSize | CLIENT | WARN | rpc 连接最大入站消息 |
| `alluxio.user.network.rpc.max.connections` | 1 | long | CLIENT | WARN | 每目标主机的物理连接数 |
| `alluxio.user.network.rpc.keepalive.time` | 30sec | duration | CLIENT | WARN | rpc 保活 ping 间隔 |
| `alluxio.user.network.rpc.keepalive.timeout` | 30sec | duration | CLIENT | WARN | rpc 保活响应超时 |
| `alluxio.user.network.rpc.netty.channel` | EPOLL | enum | CLIENT | WARN | rpc netty channel 类型(EPOLL 不可用回退 NIO) |
| `alluxio.user.network.rpc.netty.worker.threads` | 0 | int | CLIENT | WARN | rpc 客户端读线程数(0=默认) |
| `alluxio.user.network.rpc.health.check.interceptor.enabled` | true | boolean | WORKER | ENFORCE | 创建 gRPC channel 时加健康检查拦截器 |
| `alluxio.user.rpc.retry.base.sleep` | 50ms | duration | CLIENT | WARN | RPC 指数退避基准(别名 ...base.sleep.ms) |
| `alluxio.user.rpc.retry.max.sleep` | 3sec | duration | CLIENT | WARN | RPC 退避最大等待(别名 ...max.sleep.ms) |
| `alluxio.user.rpc.retry.max.duration` | 10s | duration | — | — | RPC 重试最大总时长 |
| `alluxio.user.conf.cluster.default.enabled` | true | boolean | CLIENT | — | 加载集群级/路径级默认配置 |
| `alluxio.user.conf.sync.interval` | 1min | duration | CLIENT | WARN | 从 meta master 同步配置的心跳周期 |
| `alluxio.user.master.polling.timeout` | 30sec | duration | CLIENT | WARN | 等待 master 响应的最大时间 |

### 2.2 gRPC 数据面(streaming)
| 配置项 | 默认值 | 类型 | Scope | 一致性 | 说明 |
|---|---|---|---|---|---|
| `alluxio.user.network.streaming.flowcontrol.window` | 2MiB | dataSize | CLIENT | WARN | streaming 流控窗口(别名 network.flowcontrol.window) |
| `alluxio.user.network.streaming.max.inbound.message.size` | 100MiB | dataSize | CLIENT | WARN | streaming 最大入站消息(别名 ...max.inbound...) |
| `alluxio.user.network.streaming.max.connections` | 64 | int | CLIENT | WARN | 每目标主机的物理连接数 |
| `alluxio.user.network.streaming.keepalive.time` | Long.MAX | duration | CLIENT | WARN | streaming 保活 ping 间隔(别名 keepalive.time) |
| `alluxio.user.network.streaming.keepalive.timeout` | 30sec | duration | CLIENT | WARN | streaming 保活响应超时(别名 keepalive.timeout) |
| `alluxio.user.network.streaming.netty.channel` | EPOLL | enum | CLIENT | WARN | streaming channel 类型(别名 netty.channel) |
| `alluxio.user.network.streaming.netty.worker.threads` | 0 | int | CLIENT | WARN | streaming 读线程数(别名 netty.worker.threads) |

### 2.3 worker 选择算法
| 配置项 | 默认值 | 类型 | Scope | 一致性 | 说明 |
|---|---|---|---|---|---|
| `alluxio.user.worker.selection.policy.type` | CONSISTENT_HASH | enum | CLIENT | WARN | path→worker 映射策略 |
| `alluxio.user.worker.selection.policy` | — | class | CLIENT | WARN | ⚠️已废弃(迁移 ...policy.type) |
| `alluxio.user.worker.selection.policy.consistent.hash.provider.impl` | DEFAULT | class | CLIENT | WARN | 一致性哈希实现:DEFAULT/KETAMA/MAGLEV/MULTI_PROBE |
| `alluxio.user.worker.selection.policy.ketama.hash.replicas` | 200 | int | CLIENT | WARN | ketama 虚拟节点数 |
| `alluxio.user.worker.selection.policy.maglev.hash.lookup.size` | 65537 | int | CLIENT | WARN | maglev 查找表大小(必须质数) |
| `alluxio.user.worker.selection.policy.multi.probe.hash.probe.num` | 21 | int | CLIENT | WARN | multi-probe 探测次数 |
| `alluxio.user.worker.list.refresh.interval` | 45s | duration | CLIENT | WARN | 客户端刷新存活 worker 列表间隔 |
| `alluxio.user.worker.data.reader.refresh.interval` | -1 | duration | CLIENT | WARN | 刷新 worker 列表间隔;-1 不刷新 |
| `alluxio.user.worker.monitor.enabled` | true | boolean | CLIENT | WARN | worker 可用性监控 |
| `alluxio.user.worker.monitor.probe.policy` | TIME_PROPORTIONAL | enum | CLIENT | WARN | 探测离线 worker 存活的策略 |
| `alluxio.user.worker.num.to.get.from.presto` | 1 | int | CLIENT | IGNORE | 从 presto 活跃列表取的首选 worker 数 |

### 2.4 legacy netty(多数已废弃/别名)
| 配置项 | 默认值 | 类型 | Scope | 一致性 | 说明 |
|---|---|---|---|---|---|
| `alluxio.user.network.netty.timeout` | 10sec | duration | — | — | netty 数据响应超时(别名 ...timeout.ms) |
| `alluxio.user.network.netty.channel.pool.size.max` | 1024 | int | — | — | netty channel 池最大数 |
| `alluxio.user.network.netty.channel.pool.gc.threshold` | 300sec | duration | — | — | netty channel 空闲关闭阈值(别名 ...gc.threshold.ms) |
| `alluxio.user.network.netty.channel.pool.disabled` | false | boolean | — | — | 禁用 netty channel 池 |
| `alluxio.user.network.netty.connect.timeout` | — | duration | — | — | netty 连接超时 |
| `alluxio.user.network.netty.future.await.timeout` | 5m | duration | CLIENT | WARN | 等待 netty future 完成的超时(安全网) |
| `alluxio.user.network.netty.frame.decoder.buffer.cumulator` | COMPOSITE | enum | CLIENT | WARN | 帧解码缓冲累积器:MERGE / COMPOSITE |
| `alluxio.user.network.netty.reader.buffer.size.packets` | 16 | int | — | — | netty 读缓冲 packet 数 |
| `alluxio.user.network.netty.writer.buffer.size.packets` | 16 | int | — | — | netty 写缓冲 packet 数 |
| `alluxio.user.network.netty.writer.packet.size.bytes` | 1024KiB | dataSize | — | — | netty 写 packet 大小 |
| `alluxio.user.network.netty.worker.threads` | 0 | int | CLIENT | WARN | netty 远程读线程数 |
| `alluxio.user.network.netty.buffer.receive` | — | dataSize | — | — | SO_RCVBUF |
| `alluxio.user.network.netty.buffer.send` | — | dataSize | — | — | SO_SNDBUF |
| `alluxio.user.network.netty.channel` | NIO | enum | CLIENT | WARN | ⚠️已废弃 netty channel 类型 |
| `alluxio.user.network.flowcontrol.window` | — | dataSize | CLIENT | WARN | ⚠️已废弃(迁移 streaming.flowcontrol.window) |
| `alluxio.user.network.max.inbound.message.size` | — | dataSize | CLIENT | WARN | ⚠️已废弃(迁移 streaming.max.inbound...) |
| `alluxio.user.network.keepalive.time` | — | duration | CLIENT | WARN | ⚠️已废弃(迁移 streaming.keepalive.time) |
| `alluxio.user.network.keepalive.timeout` | — | duration | CLIENT | WARN | ⚠️已废弃(迁移 streaming.keepalive.timeout) |
| `alluxio.user.network.writer.close.timeout` | — | duration | CLIENT | WARN | ⚠️已废弃(别名 ...close.timeout.ms) |
| `alluxio.user.network.writer.flush.timeout` | — | duration | CLIENT | WARN | ⚠️已废弃 |
| `alluxio.user.network.zerocopy.enabled` | — | boolean | CLIENT | WARN | ⚠️已废弃(迁移 streaming.zerocopy.enabled) |
| `alluxio.user.network.data.bind.host` | 0.0.0.0 | string | — | — | 数据客户端绑定主机(多 NIC) |
| `alluxio.user.network.data.bind.device` | — | string | WORKER | WARN | 数据客户端绑定网卡 |
| `alluxio.user.network.data.hostname` | — | string | ALL | — | 客户端主机名 |
| `alluxio.user.network.data.port` | 0 | int | CLIENT | — | 客户端数据端口 |

---

## 3. 逐项深度分析(充分细节)

> 本组 58 项按配置族逐一深挖:三套连接族的演进与别名映射 → gRPC channel pool / 网络分组机制 → 保活/流控/消息大小 → ChannelType 与线程 → **worker 选择算法四实现的原理与取舍** → worker 列表刷新 → **worker 可用性监控与探测策略** → RPC 重试 → 配置同步 → legacy netty 数据路径 → 数据客户端绑定。代码求证:`GrpcChannelPool`/`GrpcNetworkGroup`/`GrpcChannel`、`ConsistentHashProvider` 及四个 `*HashProvider`、`WorkerAvailabilityMonitor`、`WorkerLocationPolicy.Factory`。

### 3.1 三套连接族的演进与别名映射(理解本组的总纲)

本组表面是一堆 `network.*` 参数,骨架是**同一套 gRPC channel pool 被多个"网络分组"复用**。代码级机制(`GrpcChannelPool.createManagedChannelBuilder`):所有 channel 参数(keepalive/flowcontrol/max.inbound/netty.channel/worker.threads)都不是直接读死配置,而是通过 **`PropertyKey.Template.USER_NETWORK_*.format(networkGroup.getPropertyCode())`** 按分组动态解析 property 名。`GrpcNetworkGroup` 枚举有 4 值,但 `getPropertyCode()` 只返回两个码:

| GrpcNetworkGroup | propertyCode | 用途 | 读的配置族 |
|---|---|---|---|
| `RPC` | `rpc` | 元数据/控制 RPC(getStatus/create/rename/quota 等) | `network.rpc.*` |
| `CVS` | `rpc` | 凭证下发(credential vending) | 复用 `network.rpc.*` |
| `STREAMING` | `streaming` | 块读写数据流 | `network.streaming.*` |
| `SECRET` | (抛异常) | 密钥交换,独立 self-signed TLS,不走模板 | — |

**演进结论**:
- **legacy netty**(`network.netty.*` 的 channel/keepalive/flowcontrol 语义 + `network.{flowcontrol,keepalive,zerocopy,max.inbound}.*` 顶级名)是 DORA 前用自研 netty 数据传输时的参数;数据面早已切到 gRPC(streaming 分组),故这些**被 `streaming.*` / `rpc.*` 取代**。
- **现役控制面** `network.rpc.*`、**现役数据面** `network.streaming.*` 是同一 channel pool 的两个分组实例,互不共享连接。
- ⚠️ **别名 ≠ 全部 netty 都废弃**:`network.netty.*` 里仍有**活着的成员**——`frame.decoder.buffer.cumulator`、`reader/writer.buffer.size.packets`、`writer.packet.size.bytes`、`netty.timeout`、`channel.pool.*`、`future.await.timeout`——它们服务于**仍在用的 netty 数据读写客户端**(`NettyClient`、`AutoRefreshHeuristicDataReader`,见 3.10),不是废弃项。真正废弃的只有 9 项(见 3.11)。

**别名映射关系**(旧名 → 新名,`streaming.*` 均为对应旧顶级名的别名):

| 废弃/旧名 | 现役新名 | 关系 |
|---|---|---|
| `network.flowcontrol.window` | `network.streaming.flowcontrol.window` | 旧名是新名的**别名**(读旧配置仍生效) |
| `network.max.inbound.message.size` | `network.streaming.max.inbound.message.size` | 别名 |
| `network.keepalive.time` | `network.streaming.keepalive.time` | 别名 |
| `network.keepalive.timeout` | `network.streaming.keepalive.timeout` | 别名 |
| `network.netty.channel` | `network.streaming.netty.channel` | 别名(旧名单独又标 ⚠️废弃) |
| `network.netty.worker.threads` | `network.streaming.netty.worker.threads` | 别名 |
| `network.zerocopy.enabled` | `network.streaming.zerocopy.enabled` | ⚠️废弃迁移(streaming 版不在本 58 项) |
| `network.writer.{close,flush}.timeout` | (netty 写关闭超时) | ⚠️废弃 |

- ⚠️ **易错点**:同一逻辑项同时设旧名(别名)和新名时,以别名解析规则为准(一般 canonical 名优先),**避免同时设**,防止读到非预期值。

### 3.2 gRPC 保活、流控与消息大小(连通性/吞吐核心)

这三族都通过 `GrpcChannelPool` 施加到 `NettyChannelBuilder`,rpc 与 streaming **各一份**:

- **`keepalive.time` / `keepalive.timeout`**(`channelBuilder.keepAliveTime/keepAliveTimeout`):
  - **rpc**:默认 `30s` / `30s` —— 控制面 RPC 短且频繁,主动 ping 保证连接快速探活。
  - **streaming**:`keepalive.time` 默认 **`Long.MAX_VALUE`(等价于关闭主动 ping)**、timeout `30s` —— 数据面靠数据帧本身保活,默认不额外 ping 省开销。
  - ⚠️ **关键取舍**:数据流经过会掐断空闲连接的中间设备(LB/NAT/防火墙)时,大流在传输间隙可能长时间无帧 → 被中间设备断开。此时应把 streaming `keepalive.time` 设为**有限值(30~60s)**主动维持长连接。注意 gRPC 对 keepalive.time 有服务端最小间隔约束,过小(如 <10s)可能被服务端 GOAWAY。
- **`flowcontrol.window`(2MiB,`channelBuilder.flowControlWindow`)**:HTTP2 连接级流控窗口。带宽时延积(BDP)大的高延迟广域链路上,2MiB 会成为吞吐瓶颈(窗口满则发送方阻塞等 ACK);调大(如 8~16MiB)可提升吞吐,代价是每连接内存占用上升。
- **`max.inbound.message.size`(100MiB,`channelBuilder.maxInboundMessageSize`)**:单条 gRPC 消息上限。**rpc 分组**在返回超大目录 list、超大元数据批时可能触碰上限 → 抛 `RESOURCE_EXHAUSTED`;此时调大 rpc 版。streaming 数据本身分帧,一般够用。
- **`max.connections`**(`getChannelKey` 里 `groupIndex % maxConnectionsForGroup` 决定落到哪个物理连接槽):
  - **rpc 默认 1**(long):控制面 RPC 走 HTTP2 多路复用,单条物理连接足以承载大量并发流,复用降低握手/FD 成本。
  - **streaming 默认 64**(int):数据面单流吞吐大、易把单连接的 HTTP2 流窗打满,故给每目标主机开最多 64 条物理连接分摊。高并发数据流可再上调。
  - **机制**:连接按 `(网络分组内自增序号 % max.connections)` 取模映射到固定槽位,`GrpcChannelKey` 带槽位号,同槽位复用同一 `ManagedChannel`(引用计数,归零优雅关闭)。

### 3.3 ChannelType 与 netty 读线程(`netty.channel` / `netty.worker.threads`)

- **`netty.channel`(`ChannelType`,rpc/streaming 默认均 `EPOLL`)**:底层 netty 传输实现。`EPOLL`(Linux 原生 epoll,性能更好)/ `NIO`(JDK NIO,跨平台兜底)。代码 `NettyUtils.getChannelType/getChannelClass` 在 **EPOLL 不可用时自动回退 NIO**,故非 Linux 或缺 native epoll 库时无需手动改。event loop 按网络分组共享(`acquireNetworkEventLoop`,引用计数)。
- **`netty.worker.threads`(默认 0)**:该网络分组 event loop 的 IO 线程数,**0 = 用 netty 默认**(通常 2×CPU)。rpc 与 streaming 各自独立。IO 密集且 CPU 多时可显式设,一般保持 0。
- **`network.rpc.health.check.interceptor.enabled`(默认 true,WORKER,ENFORCE)**:建 gRPC channel 时挂健康检查拦截器。代码(`GrpcChannel.authenticate`):**即使认证为 NOSASL(clientHandler 为 null)也会加**该拦截器 —— 拦截器跟踪 server call、失败时置 channel 为不健康,`GrpcChannelPool` 复用连接前 `waitForConnectionReady` 会据此剔除坏连接、重建。ENFORCE 一致性:全集群语义须统一,故不建议关。

### 3.4 worker 选择算法(缓存亲和的算法层,重点)

**`worker.selection.policy.type`(`WorkerLocationPolicyType`,默认 `CONSISTENT_HASH`)** 决定 path→worker 的映射策略族。枚举全 4 值(`WorkerLocationPolicy.Factory.create`):

| 值 | 实现类 | 语义 |
|---|---|---|
| `CONSISTENT_HASH` | `ConsistentHashPolicy` | **默认·唯一生产选项**;一致性哈希把 fileId 稳定映射到 worker,保证缓存亲和 |
| `LOCAL` | `LocalWorkerPolicy` | 优先本地 worker(内部/特殊场景) |
| `REMOTE_ONLY` | `RemoteOnlyPolicy` | 强制远程 worker(内部测试) |
| `PINNED_CAPACITY_BASED` | `PinnedCapacityBasedPolicy` | 按容量钉选(特殊) |

> 为什么必须确定性:`WorkerLocationPolicy` 接口 Javadoc 明确——策略必须**确定性**,否则同一 path 的不同读者散落到不同 worker,各自留一份缓存副本,命中率崩溃、浪费缓存空间。这是"缓存亲和"的根本约束,也是**全客户端必须用同一算法+同一参数**的原因。

**已废弃**:`user.worker.selection.policy`(class 类型)→ 迁移 `...policy.type`。Factory 里若用户设了旧的 class 名,`WorkerLocationPolicyType.fromDeprecatedClassName` 把旧类名映射回枚举并打 WARN。

#### 一致性哈希四种 provider 实现(`consistent.hash.provider.impl`,默认 `DEFAULT`)

`ConsistentHashProvider.Factory.create` 按名(大写)分发,四种(文档口径 DEFAULT/KETAMA/MAGLEV/MULTI_PROBE;代码另有 JUMP、CAPACITY 隐藏项)。四者都用 `murmur3_32` 哈希、都懒初始化并按 TTL(`worker.list.ttl`,跨组)刷新 worker 列表、都用 CAS 保证并发下只有一个线程重建、`getMultiple` 靠"多次不同 index 哈希取不重复 worker"选出 N 个副本。差别在**环/表的构建方式**:

| 算法 | 关键参数(本组) | 数据结构与原理 | 构建成本 | 查找成本 | 均衡性 | 增删 worker 重分布 |
|---|---|---|---|---|---|---|
| **DEFAULT** | (虚节点数在跨组 `virtual.node.count.per.worker`) | 经典虚拟节点 + TreeMap 哈希环;每 worker 撒 K 个虚节点 | 中 | O(log N) | 依虚节点数 | 最小化(仅邻接段迁移) |
| **KETAMA** | `ketama.hash.replicas`=200 | 每 worker 生成 `replicas` 个虚节点(`hash(i+node+i)`)放入 `TreeMap<Integer,Worker>`;查找 `tailMap(hash).firstKey()` 顺时针找第一个,空则回绕 `firstKey` | 高(200×N 次哈希) | O(log(200N)) | 好(虚节点越多越均匀) | 最小化 |
| **MAGLEV** | `maglev.hash.lookup.size`=65537(**须质数**) | Maglev 查找表:每 worker 生成一个 (offset, skip) **排列**,轮流往固定大小表(质数)填空槽直到填满;查找 `abs(hash % lookupSize)` 一次数组访问 | 高(构建表 O(lookupSize)) | **O(1) 数组访问** | **很好**(近乎均匀) | 较小(表越大扰动越小) |
| **MULTI_PROBE** | `multi.probe.hash.probe.num`=21 | 每 worker 一个点排序成环(`List<Point>`);查找时对 key 做 `probes` 次哈希,各自二分找环上最近点,**取距离最小的那个** | 低(N 个点) | O(probes×log N) | 好(探测越多越均匀) | 最小化 |

参数取舍要点(代码求证):
- **`ketama.hash.replicas`(200)**:官方描述——replicas 应为物理节点数的 X 倍,X 是"均匀度 vs 构建/内存成本"的平衡。200 意味着 100 节点集群建 20000 个 TreeMap 项。调大更均匀但刷新更慢、内存更高。
- **`maglev.hash.lookup.size`(65537=2^16+1,质数)**:`Factory.create` **强校验 `isPrime()`,非质数直接抛 `IllegalArgumentException`**。要求 `lookupSize >> maxNodes`;表越大分布越均匀、增删扰动越小,代价是构建/内存随表大小线性增长。改这个值务必挑质数(如 65537、131071)。
- **`multi.probe.hash.probe.num`(21)**:探测次数。每次查找做 21 次哈希+二分取最近,probe 越多分布越均匀但**单次查找越慢**(线性放大)。适合"想要好均衡又不愿承担 Maglev 大表构建"的折中。
- **选型建议**:默认(DEFAULT)对绝大多数集群足够。追求极致均衡+O(1) 查找、且能接受构建开销的大规模集群→**MAGLEV**;想在中等成本下提升均衡→ KETAMA 或 MULTI_PROBE。⚠️ **同一路由域内所有客户端必须用相同 provider + 相同参数**,否则不同客户端把同一 path 算到不同 worker,缓存亲和失效。
- **多集群**:`ConsistentHashPolicy` 内按 clusterName 维护独立 provider(`mHashProviderMap`),`MULTI_CLUSTER_ENABLED` 时空集群返回空列表而非抛异常(见 [14 组](14-membership-etcd.md))。

### 3.5 worker 列表刷新(`worker.list.refresh.interval` / `data.reader.refresh.interval`)

- **`worker.list.refresh.interval`(45s,CLIENT)**:客户端刷新**存活 worker 列表**的间隔——列表来自 etcd 成员视图([14 组](14-membership-etcd.md)),刷新后喂给一致性哈希 provider 触发环重建。太长→ worker 增删后路由长期陈旧;太短→ etcd/成员查询压力。注意该值还**间接决定** worker 可用性监控黑名单的记忆窗口(见 3.6)。
- **`worker.data.reader.refresh.interval`(-1,CLIENT)**:netty 数据读流刷新 worker 列表的间隔;**-1 = 不刷新**(读流生命周期内固定 worker)。>0 时 `AutoRefreshHeuristicDataReader` 周期性重算目标,用于长读流期间适配成员变化。这是 legacy netty 读路径的启发式,一般保持 -1。
- **`worker.num.to.get.from.presto`(1,CLIENT,IGNORE)**:Presto 集成时从 active worker 列表取的首选 worker 数。IGNORE 一致性=纯客户端本地行为。

### 3.6 worker 可用性监控与探测策略(`worker.monitor.*`,重点)

- **`worker.monitor.enabled`(true,CLIENT)**:开启后 `WorkerAvailabilityMonitor` 用 `HealthMonitoringWorkerClient` 包装每个 worker client:**任一 RPC 返回 `UNAVAILABLE` 就把该 worker 记入黑名单缓存(Caffeine),任一 RPC 成功就立即解禁**。黑名单条目 TTL = 一个 `worker.list.refresh.interval`(默认 45s)——因为过了这个窗口,刷新后的 worker 列表已把真下线的 worker 剔除,黑名单无需再记。关闭则不做本地探活,故障 worker 会被反复重试。
- **`worker.monitor.probe.policy`(`WorkerAvailabilityProbePolicy`,默认 `TIME_PROPORTIONAL`)**:决定"某 worker 已被标记不可用时,是否放行一次探测请求给它"。枚举全 3 值(`WorkerAvailabilityMonitor` 构造函数 switch):

| 值 | 实现 | 行为 |
|---|---|---|
| `ALWAYS` | `AlwaysProbe` | 永远放行——不做规避,黑名单形同虚设(激进恢复,故障 worker 持续被打) |
| `NEVER` | `NeverProbe` | 永不放行——一旦拉黑,直到 TTL 到期都绝不碰(最保守,恢复慢) |
| `TIME_PROPORTIONAL` | `TimeBasedUniformProbabilisticProbe` | **默认·概率放行**:放行概率随距离上次错误的时间**递增** |

  - **TIME_PROPORTIONAL 算法(代码级)**:设 `elapsed`=距上次错误时长、`ttl`=记忆窗口(=list.refresh.interval)。若 `elapsed > ttl` 直接放行;否则计算 `ratio = (ttl - elapsed) / elapsed`,以 `random(0,1) > ratio` 的概率放行。含义:刚出错时 ratio 很大→几乎不放行;时间越久 ratio 越小→放行概率越高,平滑地从"规避"过渡到"恢复"。这是保守恢复(NEVER)与激进恢复(ALWAYS)之间的**时间比例折中**,避免了对刚故障 worker 的雪崩式重试,又能尽快在其恢复后重新启用。

### 3.7 RPC 重试(指数退避,韧性)

- **指数退避三参**(`user.rpc.retry.*`,均有 `.ms` 后缀别名):`base.sleep`(50ms)起步,每次翻倍到 `max.sleep`(3s)封顶,累计重试时长不超 `max.duration`(10s)后放弃。仅对**瞬时错误**(transient)自动重试。
- **调优取舍**:worker/网络抖动频繁时适度增大 `max.duration` 提升韧性;但过大会在**真故障**时放大端到端延迟、拖慢失败暴露(上游还在等重试,实际已不可恢复)。
- **与超时/可用性监控协同**:重试(失败后重试多久)要与单次 RPC 超时([02 组](02-client-cache.md) 的超时分层,决定单次多久算失败)、以及 3.6 的可用性监控(把持续故障 worker 拉黑,避免重试全砸同一坏 worker)三者配合。重试总时长应 ≤ 上游作业的整体超时预算,否则"重试还没结束、上游已判失败"。

### 3.8 配置同步(`user.conf.*`)

- **`user.conf.cluster.default.enabled`(true,CLIENT)**:开启后客户端启动时从 master 加载**集群级默认配置 + 路径级配置**——让运维在 master 侧集中下发默认值,客户端无需逐一本地配置。关闭则只用客户端本地/默认值。
- **`user.conf.sync.interval`(1min,CLIENT,WARN)**:客户端向 meta master 心跳、按需**周期性拉取最新配置**的间隔。调短→配置变更更快生效、心跳更频;调长→反之。WARN 一致性:与集群不一致时告警但不强制。
- **`user.master.polling.timeout`(30s,CLIENT,WARN)**:RPC 客户端等待 master 响应的最大时间——master 繁忙/网络差时的等待上限,超时判失败进入重试。

### 3.9 数据客户端网络绑定(`network.data.*`,多 NIC 场景)

- **`network.data.bind.host`(0.0.0.0)**:数据客户端绑定的主机地址;多网卡场景指定具体 NIC 的 IP。
- **`network.data.bind.device`(空,WORKER,WARN)**:按**网卡设备名**绑定(如 `eth0`),用于精确选择出网卡。
- **`network.data.hostname`(空,ALL)**:客户端对外主机名。
- **`network.data.port`(0,CLIENT)**:客户端数据端口,0=系统分配。
- 这四项服务于多 NIC / 网络隔离场景,一般默认(全网卡/随机端口)即可。

### 3.10 legacy netty 数据读写路径(仍在用的 netty.*,非废弃)

DORA 主数据面已是 gRPC streaming,但 netty 数据客户端(`NettyClient`)在部分读写路径仍在用,以下参数**服务于它,不是废弃项**:
- **`netty.frame.decoder.buffer.cumulator`(`FrameDecoderCumulatorType`,默认 `COMPOSITE`)**:帧解码器累积多个到达的 ByteBuf 的方式。枚举 2 值:`MERGE`=缓冲将溢出时**重新分配并拷贝**数据(内存连续、有拷贝开销);`COMPOSITE`=用**组合缓冲**零拷贝拼接(省拷贝、随机访问稍慢)。默认 COMPOSITE 偏吞吐。
- **`netty.reader/writer.buffer.size.packets`(各 16)**:客户端读/写远程 worker 时缓冲的 packet 数(背压窗口)。
- **`netty.writer.packet.size.bytes`(1024KiB)**:写远程 worker 的单 packet 上限。
- **`netty.timeout`(10s,别名 `.ms`)**:netty 数据客户端等 data server 响应的超时。
- **`netty.connect.timeout`**:netty 连接建立超时。
- **`netty.future.await.timeout`(5m,CLIENT,WARN)**:等待 netty future 完成的**安全网**超时——防 bug/异常下无限等待。
- **`netty.buffer.receive` / `netty.buffer.send`**:socket 选项 `SO_RCVBUF` / `SO_SNDBUF` 建议值。
- **channel pool 三参**:`netty.channel.pool.size.max`(1024,池上限)、`netty.channel.pool.gc.threshold`(300s,空闲超此值关闭连接,别名 `.ms`)、`netty.channel.pool.disabled`(false,禁用 netty channel 池——仅当 client≥1.3 而 server≤1.2 的老兼容场景才开)。

### 3.11 废弃项集中区(9 项)与迁移

真正标 ⚠️ 废弃的 9 项(附录 A 中标注),全部在 legacy netty / 顶级 network 语义,应迁到 `streaming.*`(见 3.1 别名表):
- `network.netty.channel` → `network.streaming.netty.channel`
- `network.flowcontrol.window` → `network.streaming.flowcontrol.window`
- `network.max.inbound.message.size` → `network.streaming.max.inbound.message.size`
- `network.keepalive.time` → `network.streaming.keepalive.time`
- `network.keepalive.timeout` → `network.streaming.keepalive.timeout`
- `network.zerocopy.enabled` → `network.streaming.zerocopy.enabled`(streaming 版不在本组 58 项内)
- `network.writer.close.timeout` / `network.writer.flush.timeout` → netty writer 已被 streaming 写路径取代
- `user.worker.selection.policy`(class)→ `...policy.type`(enum)

新部署一律用现役新名。

---

## 4. 配置关联关系图

```mermaid
flowchart TD
    subgraph POOL[GrpcChannelPool 单例 · 按网络分组复用]
      RPCG[RPC分组 code=rpc<br/>max.connections=1]
      STRG[STREAMING分组 code=streaming<br/>max.connections=64]
    end
    TPL[Template.USER_NETWORK_*<br/>.format 分组码] --> RPCG
    TPL --> STRG
    NET[legacy netty.* channel/keepalive/flowcontrol<br/>⚠️废弃 9 项] -. 别名/迁移 .-> STRG
    NETALIVE[netty.* 仍活:cumulator/packets/pool/timeout<br/>服务 NettyClient 数据读写] -.-> DATA[legacy netty 数据路径]
    STRG --> KA{streaming.keepalive.time}
    KA -->|Long.MAX 默认| IDLE[空闲不ping<br/>过LB/NAT可能被断]
    KA -->|有限值 30~60s| KEEP[维持长连接]
    SEL[worker.selection.policy.type=CONSISTENT_HASH<br/>确定性=缓存亲和] --> IMPL{provider.impl}
    IMPL --> D[DEFAULT 虚节点环]
    IMPL --> K[KETAMA replicas=200 TreeMap]
    IMPL --> M[MAGLEV lookup.size 质数 O1查表]
    IMPL --> P[MULTI_PROBE probe.num=21 取最近]
    SEL -.环刷新.-> LR[worker.list.refresh 45s ← 14成员]
    MON[worker.monitor.enabled] --> PP{probe.policy}
    PP --> A[ALWAYS 不规避]
    PP --> NV[NEVER 拉黑到TTL]
    PP --> TP[TIME_PROPORTIONAL 概率随时间递增]
    LR -.记忆窗口=list.refresh.-> MON
    RT[rpc.retry base 50ms→max 3s→max.duration 10s] --> RESIL[韧性 vs 故障放大]
    RT -.协同.-> MON
```

---

## 5. 典型场景配置组合建议

| 场景 | 推荐组合 | 理由 |
|---|---|---|
| **过 LB/NAT 的长连接** | `network.streaming.keepalive.time=30~60s`(≥10s 避免服务端 GOAWAY) | streaming 默认 Long.MAX 不 ping,长空闲流会被中间设备掐断 |
| **高延迟广域链路(大 BDP)** | 调大 `streaming.flowcontrol.window`(如 8~16MiB) | 默认 2MiB 窗口在高 BDP 下成吞吐瓶颈,调大代价是每连接内存 |
| **超大目录 list / 大元数据批** | 调大 `network.rpc.max.inbound.message.size` | 避免控制面 RESOURCE_EXHAUSTED(改 rpc 版,非 streaming) |
| **高并发数据流** | 调大 `streaming.max.connections`(默认 64) | 每目标主机开更多物理连接,分摊单连接 HTTP2 流窗压力 |
| **大规模集群均衡 + O(1) 查找** | `consistent.hash.provider.impl=MAGLEV` + `maglev.hash.lookup.size` 取更大质数 | 近乎均匀分布、查表 O(1);代价是构建/内存随表大小增长 |
| **中等成本提升均衡** | `provider.impl=KETAMA`(调大 replicas)或 `MULTI_PROBE`(调大 probe.num) | 无需 Maglev 大表;replicas/probe 越大越均匀但更慢 |
| **worker 抖动频繁(想快恢复)** | `worker.monitor.probe.policy=TIME_PROPORTIONAL`(默认)或缩短 `worker.list.refresh.interval` | 概率放行随时间递增,平滑恢复;缩短刷新窗口也缩短黑名单记忆 |
| **worker 故障需强规避** | `worker.monitor.probe.policy=NEVER` | 拉黑后直到 TTL 到期绝不重试坏 worker(恢复慢但最保守) |
| **worker 抖动 + 上游有超时预算** | 适度增大 `rpc.retry.max.duration` 但 ≤ 上游超时 | 提升瞬时故障韧性,又不至于"重试没结束上游已判失败" |
| **master 侧集中下发配置** | `user.conf.cluster.default.enabled=true` + 调 `user.conf.sync.interval` | 集群级/路径级默认由 master 统一管理,同步周期控制生效速度 |
| **多网卡精确出网** | `network.data.bind.host` / `network.data.bind.device` 指定 NIC | 多 NIC / 网络隔离场景绑定指定网卡 |
| **多集群路由** | 各集群一致的 `provider.impl` + 参数;`MULTI_CLUSTER_ENABLED`(见 14) | 每 clusterName 独立哈希环,空集群返回空列表不抛异常 |

---

## 6. 风险与注意事项

1. **⚠️ 别名 ≠ netty 全废弃**:`network.netty.*` 里 `frame.decoder.buffer.cumulator`、`reader/writer.buffer.size.packets`、`writer.packet.size.bytes`、`netty.timeout`、`channel.pool.*`、`future.await.timeout`、`buffer.{send,receive}` **仍服务于活着的 netty 数据客户端**(`NettyClient`),不是废弃项;别把它们和真废弃项混为一谈。真正废弃只有 9 项(见 3.11)。
2. **废弃项(9)集中在 legacy netty / 顶级 network 语义**:`network.netty.channel`、`network.{flowcontrol,keepalive.time,keepalive.timeout,zerocopy,max.inbound}.*`、`network.writer.{close,flush}.timeout`、`user.worker.selection.policy`(class)→ 新部署用 `streaming.*` / `rpc.*` / `...policy.type`。
3. **别名新旧同设的歧义**:12 项别名(如 `streaming.*` 的 `network.*` 旧别名、`rpc.retry.*` 的 `.ms` 后缀名),同时设新旧名时读到的值取决于别名解析规则,**务必只设一个**。
4. **streaming 默认不保活**:`keepalive.time=Long.MAX_VALUE`,经 LB/NAT/防火墙的长连接需显式设有限值(30~60s);但过小(<10s)可能触发服务端 GOAWAY。
5. **worker 选择算法须全客户端严格一致(算法 + 参数)**:同一路由域内不同客户端用不同 `provider.impl` 或不同 `replicas`/`lookup.size`/`probe.num`,会把同一 path 算到不同 worker → 缓存亲和错乱、多份冗余副本、命中率崩。
6. **MAGLEV lookup.size 必须质数**:`ConsistentHashProvider.Factory` 强校验,非质数直接抛 `IllegalArgumentException` 启动失败;改值只能挑质数(65537/131071 等)。
7. **rpc vs streaming 参数别搞反**:控制面(list/元数据 RESOURCE_EXHAUSTED)调 `rpc.*`;数据面(吞吐/并发/长连接)调 `streaming.*`。两组是同一 pool 的不同分组,互不共享连接。
8. **worker 黑名单记忆窗口 = list.refresh.interval**:`WorkerAvailabilityMonitor` 的黑名单 TTL 直接取 `worker.list.refresh.interval`;改后者会同时改变故障 worker 被规避的时长,`probe.policy` 的时间比例基准也随之变。
9. **probe.policy 的极端取舍**:`ALWAYS` 让黑名单形同虚设(故障 worker 被持续打),`NEVER` 恢复最慢;非特殊需求保持默认 `TIME_PROPORTIONAL`。
10. **重试、超时、可用性监控三者协同**:重试总时长应 ≤ 上游作业超时预算;并依赖可用性监控把持续故障 worker 拉黑,避免重试全砸同一坏 worker、放大端到端延迟。
11. **health check interceptor 默认开且 ENFORCE**:`network.rpc.health.check.interceptor.enabled` 关闭会失去坏连接自动剔除/重建能力;全集群语义须一致,不建议改。

---

## 跨组关联速览
- [01-client-fs-io](01-client-fs-io.md) —— 一致性哈希环、读写路由(本组是其传输/算法底层)
- [02-client-cache](02-client-cache.md) —— 客户端 RPC 超时分层(与重试协同)
- [14-membership-etcd](14-membership-etcd.md) —— 存活 worker 列表来源、成员管理
- [15-network-transport](15-network-transport.md) —— 服务端网络/gRPC/传输参数对照

---

## 附录A:本组全量配置清单(脚本生成)

> 由 `_data/gen_table.py 03-client-net-rpc` 生成,逐 key 一行,保证覆盖本组**全部 58 项**(与上文按子场景组织的中文速查表互补;此处描述为官方英文原文,便于精确检索)。

| 配置项 | 默认值 | 类型 | Scope | 一致性 | 状态 | 说明 |
|---|---|---|---|---|---|---|
| `alluxio.user.conf.cluster.default.enabled` | true | boolean | CLIENT | — | — | When this property is true, an Alluxio client will load the default values of cluster-wide configuration and path-specific configuration set by All... |
| `alluxio.user.conf.sync.interval` | "1min" | duration | CLIENT | WARN | — | The time period of client master heartbeat to update the configuration if necessary from meta master. |
| `alluxio.user.master.polling.timeout` | "30sec" | duration | CLIENT | WARN | — | The maximum time for a rpc client to wait for master to respond. |
| `alluxio.user.network.data.bind.device` | — | string | WORKER | WARN | — | The device name Alluxio's client binds to. |
| `alluxio.user.network.data.bind.host` | "0.0.0.0" | string | — | — | — | The hostname that the Alluxio data client runs on. This is used for specifying the exact NIC to support multiple NICs scenarios. |
| `alluxio.user.network.data.hostname` | — | string | ALL | — | — | The hostname of Alluxio client. |
| `alluxio.user.network.data.port` | 0 | int | CLIENT | — | — | The port Alluxio client data runs on. |
| `alluxio.user.network.flowcontrol.window` | — | dataSize | CLIENT | WARN | ⚠️废弃 | The HTTP2 flow control window used by user gRPC connections. Larger value will allow more data to be buffered but will use more memory. |
| `alluxio.user.network.keepalive.time` | — | duration | CLIENT | WARN | ⚠️废弃 | The amount of time for a gRPC client (for block reads and block writes) to wait for a response before pinging the server to see if it is still alive. |
| `alluxio.user.network.keepalive.timeout` | — | duration | CLIENT | WARN | ⚠️废弃 | The maximum time for a gRPC client (for block reads and block writes) to wait for a keepalive response before closing the connection. |
| `alluxio.user.network.max.inbound.message.size` | — | dataSize | CLIENT | WARN | ⚠️废弃 | The max inbound message size used by user gRPC connections. |
| `alluxio.user.network.netty.buffer.receive` | — | dataSize | — | — | — | Netty client socket option for SO_RCVBUF: the proposed buffer size that will be used for receives. |
| `alluxio.user.network.netty.buffer.send` | — | dataSize | — | — | — | Netty client socket option for SO_SNDBUF: the proposed buffer size that will be used for sends. |
| `alluxio.user.network.netty.channel` | ChannelType.NIO | enum | CLIENT | WARN | ⚠️废弃 | Type of netty channels. If EPOLL is not available, this will automatically fall back to NIO. |
| `alluxio.user.network.netty.channel.pool.disabled` | false | boolean | — | — | — | Disable netty channel pool. This should be turned on if the client version is >= 1.3.0 but server version is <= 1.2.x. |
| `alluxio.user.network.netty.channel.pool.gc.threshold` | "300sec" | duration | — | — | 别名:alluxio.user.network.netty.channel.pool.gc.threshold.ms | A netty channel is closed if it has been idle for more than this threshold. |
| `alluxio.user.network.netty.channel.pool.size.max` | 1024 | int | — | — | — | The maximum number of netty channels cached in the netty channel pool. |
| `alluxio.user.network.netty.connect.timeout` | — | duration | — | — | — | Netty client timeout options. |
| `alluxio.user.network.netty.frame.decoder.buffer.cumulator` | FrameDecoderCumulatorType.COMPOSITE | enum | CLIENT | WARN | — | Type of buffer cumulator used by the frame decoder. Options: : reallocate and copy data when current buffer would overflow. : create a composite bu... |
| `alluxio.user.network.netty.future.await.timeout` | "5m" | duration | CLIENT | WARN | — | Timeout for awaiting on Netty future completions. This is a safety net to avoid waiting indefinitely for a future to complete in case of bugs or un... |
| `alluxio.user.network.netty.reader.buffer.size.packets` | 16 | int | — | — | — | When a client reads from a remote worker, the maximum number of packets to buffer by the client. |
| `alluxio.user.network.netty.timeout` | "10sec" | duration | — | — | 别名:alluxio.user.network.netty.timeout.ms | The maximum time for a netty client (for block reads and block writes) to wait for a response from the data server. |
| `alluxio.user.network.netty.worker.threads` | 0 | int | CLIENT | WARN | — | How many threads to use for remote block worker client to read from remote block workers. |
| `alluxio.user.network.netty.writer.buffer.size.packets` | 16 | int | — | — | — | When a client writes to a remote worker, the maximum number of packets to buffer by the client. |
| `alluxio.user.network.netty.writer.close.timeout` | "30sec" | duration | — | — | 别名:alluxio.user.network.netty.writer.close.timeout.ms | The timeout to close a netty writer client. |
| `alluxio.user.network.netty.writer.packet.size.bytes` | "1024KiB" | dataSize | — | — | — | When a client writes to a remote worker, the maximum packet size. |
| `alluxio.user.network.rpc.flowcontrol.window` | "2MiB" | dataSize | CLIENT | WARN | — | The HTTP2 flow control window used by user rpc connections. Larger value will allow more data to be buffered but will use more memory. |
| `alluxio.user.network.rpc.health.check.interceptor.enabled` | true | boolean | WORKER | ENFORCE | — | If enabled, the health check interceptor will be added when a grpc channel is created regardless the authentication is enabled or not. If a GRPC ca... |
| `alluxio.user.network.rpc.keepalive.time` | "30sec" | duration | CLIENT | WARN | — | The amount of time for a rpc client to wait for a response before pinging the server to see if it is still alive. |
| `alluxio.user.network.rpc.keepalive.timeout` | "30sec" | duration | CLIENT | WARN | — | The maximum time for a rpc client to wait for a keepalive response before closing the connection. |
| `alluxio.user.network.rpc.max.connections` | 1 | long | CLIENT | WARN | — | The maximum number of physical connections to be used per target host. |
| `alluxio.user.network.rpc.max.inbound.message.size` | "100MiB" | dataSize | CLIENT | WARN | — | The max inbound message size used by user rpc connections. |
| `alluxio.user.network.rpc.netty.channel` | ChannelType.EPOLL | enum | CLIENT | WARN | — | Type of netty channels used by rpc connections. If EPOLL is not available, this will automatically fall back to NIO. |
| `alluxio.user.network.rpc.netty.worker.threads` | 0 | int | CLIENT | WARN | — | How many threads to use for rpc client to read from remote workers. |
| `alluxio.user.network.streaming.flowcontrol.window` | "2MiB" | dataSize | CLIENT | WARN | 别名:alluxio.user.network.flowcontrol.window | The HTTP2 flow control window used by user streaming connections. Larger value will allow more data to be buffered but will use more memory. |
| `alluxio.user.network.streaming.keepalive.time` | Long.MAX_VALUE | duration | CLIENT | WARN | 别名:alluxio.user.network.keepalive.time | The amount of time for a streaming client to wait for a response before pinging the server to see if it is still alive. |
| `alluxio.user.network.streaming.keepalive.timeout` | "30sec" | duration | CLIENT | WARN | 别名:alluxio.user.network.keepalive.timeout | The maximum time for a streaming client to wait for a keepalive response before closing the connection. |
| `alluxio.user.network.streaming.max.connections` | 64 | int | CLIENT | WARN | — | The maximum number of physical connections to be used per target host. |
| `alluxio.user.network.streaming.max.inbound.message.size` | "100MiB" | dataSize | CLIENT | WARN | 别名:alluxio.user.network.max.inbound.message.size | The max inbound message size used by user streaming connections. |
| `alluxio.user.network.streaming.netty.channel` | ChannelType.EPOLL | enum | CLIENT | WARN | 别名:alluxio.user.network.netty.channel | Type of netty channels used by streaming connections. If EPOLL is not available, this will automatically fall back to NIO. |
| `alluxio.user.network.streaming.netty.worker.threads` | 0 | int | CLIENT | WARN | 别名:alluxio.user.network.netty.worker.threads | How many threads to use for streaming client to read from remote workers. |
| `alluxio.user.network.writer.close.timeout` | — | duration | CLIENT | WARN | ⚠️废弃; 别名:alluxio.user.network.writer.close.timeout.ms | The timeout to close a writer client. |
| `alluxio.user.network.writer.flush.timeout` | — | duration | CLIENT | WARN | ⚠️废弃 | The timeout to wait for flush to finish in a data writer. |
| `alluxio.user.network.zerocopy.enabled` | — | boolean | CLIENT | WARN | ⚠️废弃 | Whether zero copy is enabled on client when processing data streams. |
| `alluxio.user.rpc.retry.base.sleep` | "50ms" | duration | CLIENT | WARN | 别名:alluxio.user.rpc.retry.base.sleep.ms | Alluxio client RPCs automatically retry for transient errors with an exponential backoff. This property determines the base time in the exponential... |
| `alluxio.user.rpc.retry.max.duration` | "10s" | duration | — | — | — | Alluxio client RPCs automatically retry for transient errors with an exponential backoff. This property determines the maximum duration to retry fo... |
| `alluxio.user.rpc.retry.max.sleep` | "3sec" | duration | CLIENT | WARN | 别名:alluxio.user.rpc.retry.max.sleep.ms | Alluxio client RPCs automatically retry for transient errors with an exponential backoff. This property determines the maximum wait time in the bac... |
| `alluxio.user.worker.data.reader.refresh.interval` | "-1" | duration | CLIENT | WARN | — | The interval used to refresh the worker list.If it is set to -1, the worker list will not be refreshed. |
| `alluxio.user.worker.list.refresh.interval` | "45s" | duration | CLIENT | WARN | — | The interval used to refresh the live worker list on the client |
| `alluxio.user.worker.monitor.enabled` | true | boolean | CLIENT | WARN | — | Whether to enable worker availability monitor |
| `alluxio.user.worker.monitor.probe.policy` | WorkerAvailabilityProbePolicy.TIME_PROPORTIONAL | enum | CLIENT | WARN | — | The policy that decides when to probe the liveness status of workers which were considered offline because of previous I/O errors. The default is a... |
| `alluxio.user.worker.num.to.get.from.presto` | 1 | int | CLIENT | IGNORE | — | The preferred worker number that we want to get from the presto active worker list. |
| `alluxio.user.worker.selection.policy` | — | class | CLIENT | WARN | ⚠️废弃→Use instead. alluxio.user.worker.selection.policy.type | Deprecated. Use instead. |
| `alluxio.user.worker.selection.policy.consistent.hash.provider.impl` | "DEFAULT" | class | CLIENT | WARN | — | The provider implementation of consistent hash algorithm. User can choose one of the following providers: DEFAULT, KETAMA, MAGLEV, MULTI_PROBE. By ... |
| `alluxio.user.worker.selection.policy.ketama.hash.replicas` | 200 | int | CLIENT | WARN | — | This is the value of replicas in the ketama hashing algorithm. When workers changes, it will guarantee the hash table is changed only in a minimal.... |
| `alluxio.user.worker.selection.policy.maglev.hash.lookup.size` | 65537 | int | CLIENT | WARN | — | This is the size of the lookup table in the maglev hashing algorithm. It must be a prime number. In the maglev hashing, it will generate a lookup t... |
| `alluxio.user.worker.selection.policy.multi.probe.hash.probe.num` | 21 | int | CLIENT | WARN | — | This is the number of probes in the multi-probe hashing algorithm. In the multi-probe hashing algorithm, the bigger the number of probes, the small... |
| `alluxio.user.worker.selection.policy.type` | WorkerLocationPolicyType.CONSISTENT_HASH | enum | CLIENT | WARN | — | The policy a client uses to map a file path to a worker address. The only option is Other options are for internal tests only and not for real depl... |
