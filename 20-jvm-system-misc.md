# 20 · JVM / 进程 / 系统级 / 杂项

> 场景组:目录路径(`home`/`conf.dir`/`work.dir`/`tmp.dirs`)+ JVM 监控 + 泄漏检测 + License + 动态配置 + 多集群 + K8s
> 配置数:**42** · 别名 2 · 废弃 1 · 数据来源:`PropertyKey.java` · 生成表:`_data/gen_table.py 20`

---

## 1. 本组概览

本组是**进程与系统级基础设施**——安装目录、JVM 暂停监控、资源泄漏检测、License 校验、动态配置、多集群、K8s 标记。多为部署时设定、运行期少变的"环境底座"。

四个子场景:

| 子场景 | 关键配置 | 说明 |
|---|---|---|
| 目录布局 | `home`、`conf.dir`、`work.dir`、`tmp.dirs`、`site.conf.dir` | 安装/配置/工作/临时目录 |
| JVM 健康 | `jvm.monitor.*`、`leak.detector.*`、`exit.collect.info` | GC 停顿监控 / 泄漏检测 |
| License | `license`、`license.check.*` | 企业版授权校验 |
| 运行时能力 | `conf.dynamic.update`、`dynamic.configuration.etcd.*`、`multi.cluster.*`、`k8s.env.deployment` | 动态配置 / 多集群 / K8s |

---

## 2. 配置清单速查表(全量 42 项)

### 2.1 目录布局
| 配置项 | 默认值 | 类型 | Scope | 说明 |
|---|---|---|---|---|
| `alluxio.home` | /opt/alluxio | string | ALL | 安装目录 |
| `alluxio.conf.dir` | ${home}/conf | string | ALL | 配置目录(改用环境变量 $ALLUXIO_CONF_DIR) |
| `alluxio.work.dir` | ${home} | string | SERVER | 工作目录(journal/logs/本地 UFS 数据) |
| `alluxio.work.dir`(MASTER 变体) | ${work}/underFSStorage | — | MASTER | UFS 根存储地址(别名 underfs.address) |
| `alluxio.tmp.dirs` | /tmp | list | SERVER | 临时文件目录(多个随机选) |
| `alluxio.lib.dir` | ${home}/lib | string | — | jar 目录 |
| `alluxio.third.party.dir` | — | string | SERVER | 第三方 jar 目录 |
| `alluxio.site.conf.dir` | — | list | ALL | alluxio-site.properties 搜索路径 |
| `alluxio.site.conf.rocks.block.file` | — | string | ALL | RocksDB block store 配置文件 |
| `alluxio.site.conf.rocks.inode.file` | — | string | ALL | RocksDB inode store 配置文件 |

### 2.2 JVM 健康与泄漏检测
| 配置项 | 默认值 | 类型 | Scope | 说明 |
|---|---|---|---|---|
| `alluxio.jvm.monitor.sleep.interval` | 1sec | duration | SERVER | JVM 监控线程 sleep |
| `alluxio.jvm.monitor.warn.threshold` | 10sec | duration | SERVER | 暂停超此记 WARN(别名 severe.pause) |
| `alluxio.jvm.monitor.minor.pause.threshold` | 1sec | duration | SERVER | 暂停超此记 INFO |
| `alluxio.jvm.monitor.minor.pause.frequency.threshold` | 0.1 | double | SERVER | 窗口内 minor 暂停占比超此判严重 |
| `alluxio.standalone.fuse.jvm.monitor.enabled` | false | boolean | WORKER | 独立 FUSE 进程 JVM 监控 |
| `alluxio.leak.detector.level` | DISABLED | enum | ALL | 资源泄漏检测:DISABLED/SIMPLE/ADVANCED/PARANOID |
| `alluxio.leak.detector.exit.on.leak` | false | boolean | ALL | 检测到泄漏即退出(仅测试) |
| `alluxio.exit.collect.info` | true | boolean | SERVER | 退出时把 metrics/jstack dump 到日志 |
| `alluxio.file.lock.manager.unused.lock.expiration.ttl` | 1h | duration | ALL | 文件锁管理器锁 TTL |

### 2.3 License
| 配置项 | 默认值 | 类型 | Scope | 说明 |
|---|---|---|---|---|
| `alluxio.license` | — | string | ALL | License 内容字符串 |
| `license.check.enabled` | 常量 | boolean | ALL | 是否启用 License 校验 |
| `license.check.interval.second` | 常量 | int | ALL | License 校验间隔 |
| `license.expiration.pending.warning.days` | 7 | int | ALL | 到期前多少天开始告警 |

### 2.4 运行时能力(动态配置/多集群/K8s)
| 配置项 | 默认值 | 类型 | Scope | 说明 |
|---|---|---|---|---|
| `alluxio.conf.dynamic.update.enabled` | false | boolean | ALL | 支持动态更新属性 |
| `alluxio.conf.validation.enabled` | true | boolean | ALL | 初始化时校验配置 |
| `alluxio.dynamic.configuration.etcd.sync.interval` | 10s | duration | ALL | 从 etcd 同步动态配置间隔 |
| `alluxio.dynamic.configuration.etcd.timeout` | 3s | duration | ALL | 动态配置访问 etcd 超时 |
| `alluxio.multi.cluster.enabled` | false | boolean | ALL | 客户端连多集群 |
| `alluxio.multi.cluster.config.path` | — | string | ALL | 多集群配置文件路径 |
| `alluxio.k8s.env.deployment` | false | boolean | ALL | 是否 K8s 部署 |
| `alluxio.extra.loaded.filesystem.classname` | DoraCacheFileSystem | class | ALL | 显式加载的文件系统类 |

### 2.5 其它杂项
| 配置项 | 默认值 | 类型 | Scope | 说明 |
|---|---|---|---|---|
| `alluxio.version` | 构建常量 | string | ALL | Alluxio 版本(勿改) |
| `alluxio.debug` | false | boolean | SERVER | 调试模式(额外日志+Web UI 信息) |
| `alluxio.test.mode` | false | boolean | ALL | 测试模式(仅测试用) |
| `alluxio.ds.worker.copy.threads.max` | 128 | int | WORKER | data shuttle 拷贝线程池上限 |
| `alluxio.cacheability.timestamp.error.margin` | 1s | duration | ALL | cacheability 时间戳比较容错(时钟不同步) |
| `alluxio.load.job.without.quota.allowed` | true | boolean | ALL | 配额不存在时 load 跳过配额检查 |
| `alluxio.pddm.permission.check.enabled` | false | boolean | ALL | PDDM copy/move 时向安全服务查权限 |
| `alluxio.hadoop.checksum.combine.mode` | — | — | CLIENT | 文件校验和合并模式 |
| `debug.fuse.slowness.injector.path` | /tmp/slowness_injection.json | string | ALL | (测试)对指定路径注入慢速 |
| `debug.performance.diagnostics.enabled` | false | boolean | ALL | 虚拟性能诊断文件 |
| `TEST_DEPRECATED_KEY` | — | — | — | ⚠️已废弃(仅测试用) |

---

## 3. 逐项深度分析(充分细节)

> 本组 42 项按配置族逐一深挖:目录布局 → JVM 暂停监控(**翻 JvmPauseMonitor 求证机制**)→ 资源泄漏检测(**Netty ResourceLeakDetector 级别语义**)→ 退出信息 dump → License 校验(**翻 EnterpriseLicenseChecker 生命周期**)→ 动态配置(**两套系统辨析**)→ 多集群/K8s/运行时能力 → 杂项与诊断项。代码路径以 `dora/core/common`、`dora/core/server/common/ProcessUtils`、`dora/core/common/util/JvmPauseMonitor`、`dora/core/common/license/checker` 为准。

### 3.1 目录布局:`home` 为根,改位置优先用环境变量

安装/运行期目录以 `alluxio.home`(默认 `/opt/alluxio`,Scope=ALL)为根,其余目录多默认相对它展开:

| 配置项 | 默认值(展开自) | 关键点 |
|---|---|---|
| `alluxio.home` | `/opt/alluxio` | 安装根;所有相对目录的基准 |
| `alluxio.conf.dir` | `${home}/conf` | 配置目录。**`setIgnoredSiteProperty(true)`**——即写在 `alluxio-site.properties` 里也被忽略;description 明确"仅内部用,改位置请设环境变量 `$ALLUXIO_CONF_DIR`" |
| `alluxio.work.dir` | `${home}` | SERVER 工作目录;**journal、logs、本地 UFS 数据**默认写这里。`logs.dir` 默认 `${work.dir}/logs` |
| `alluxio.lib.dir` | `${home}/lib` | Alluxio 自身 jar 目录 |
| `alluxio.third.party.dir` | 无默认(SERVER) | 第三方 jar 目录(如自定义 UFS 扩展) |
| `alluxio.tmp.dirs` | `/tmp`(list,SERVER) | 临时文件目录;多个则**每个临时文件随机选一个**。⚠️ description 限定:**"当前仅用于要上传到对象存储的文件"**——即 UFS 上传暂存,并非通用临时目录 |
| `alluxio.site.conf.dir` | `${conf.dir}/,${user.home}/.alluxio/,/etc/alluxio/`(list) | `alluxio-site.properties` 的**搜索路径**(按顺序找到第一个即用) |
| `alluxio.site.conf.rocks.block.file` / `.inode.file` | 无默认 | 指向 RocksDB block/inode store 的调优 ini(模板 `rocks-block.ini.template` / `rocks-inode.ini.template`);高级调优,一般不设 |

**代码级要点(为什么改属性可能不生效)**:`CONF_DIR` 与 `VERSION` 等一样带 `setIgnoredSiteProperty(true)`——属性加载流程本身要先定位 conf 目录才能读 `alluxio-site.properties`,存在"鸡生蛋"依赖,故这类目录**通过 site 属性改无效,必须用环境变量**(`$ALLUXIO_CONF_DIR`/`$ALLUXIO_LOGS_DIR`,由 `alluxio-config.sh`/`log4j2.xml` 消费)。

**⚠️ 关于"`work.dir` 双定义"的澄清(翻代码求证)**:速查表把两行都标成 `alluxio.work.dir` 是 `gen_table.py` 的分组产物,实际是**两个不同的 PropertyKey**:
- `PropertyKey.WORK_DIR`(`alluxio.work.dir`,Scope=SERVER,默认 `${home}`)——真正的工作目录。
- 另一行是 `PropertyKey.MASTER_MOUNT_TABLE_ROOT_UFS`(`alluxio.master.mount.table.root.ufs`,**别名 `alluxio.underfs.address`**,Scope=MASTER,默认 `${work.dir}/underFSStorage`,`ENFORCE`)——Alluxio 根挂载点的 **UFS 存储地址**,只是默认值引用了 `${work.dir}`,故被分到同族。二者语义完全不同:一个是本地工作目录,一个是根 UFS 地址(详见 [10组](10-ufs-common.md))。**不要把它当成 work.dir 的第二个值。**

### 3.2 JVM 暂停监控 `jvm.monitor.*`(翻 `JvmPauseMonitor` 求证机制)

> 本组是**阈值参数**;总开关按角色在别组:`master.jvm.monitor.enabled`(默认 true,[13](13-coordinator-master.md))、`worker.jvm.monitor.enabled`(默认 true,[07](07-worker-mgmt.md))、`standalone.fuse.jvm.monitor.enabled`(默认 **false**,本组,WORKER)。开启后 worker/master/security/fuse 进程各起一条守护线程 `JvmPauseMonitor`。

**检测原理(核心)**:线程循环 `sleep(sleep.interval)`(默认 1s),用 `Stopwatch` 测真实耗时,`pauseMs = 实际耗时 - 预期 sleep`。若 `pauseMs>0` 说明 JVM 在这段睡眠里被"卡住"了(GC STW、OS 调度、swap 等),同时对比 sleep 前后各 `GarbageCollectorMXBean` 的 count/time 差,判断这次停顿是否由 GC 引起。

**分级记录(阈值语义)**:
- `pauseMs > jvm.monitor.warn.threshold`(默认 **10sec**,别名 `jvm.monitor.severe.pause.threshold`)→ 记 **WARN**,日志含"JVM paused Xms"、GC list 差异、内存快照(max/total/free)。
- `pauseMs > jvm.monitor.minor.pause.threshold`(默认 **1sec**)→ 记 **INFO**。
- 构造期有 `Preconditions` 校验:`sleep.interval>0`、`warn.threshold>minor.pause.threshold`、`0≤frequency≤1`——**配错(如 warn<minor)进程启动即抛异常**,注意别把 warn 配得比 minor 还小。

**健康判定 `jvm.monitor.minor.pause.frequency.threshold`(默认 0.1)**:内部维护一个 **10 分钟滑动窗口**(`EvictingQueue`,最多 100 条事件),对外暴露一个名为 `JVM_PAUSE` 的 `ServiceHealthMonitor`。判"不健康"的两个条件(或):
1. 窗口内出现**至少一次 severe pause**(≥ warn.threshold);
2. 窗口内所有 minor pause 的**总时长 / 窗口(10min)> frequency**——默认 0.1 即"10 分钟里累计卡了超过 1 分钟"也判不健康(即使没有单次超 10s 的严重停顿)。

**可观测性(排障闭环)**:master 侧 `JvmMonitorService` 还把三个指标注册为 gauge——`Process.TotalExtraTime`(累计额外停顿 ms)、`Process.InfoTimeExceeded`、`Process.WarnTimeExceeded`(超阈值次数)。**排障价值**:延迟毛刺时先看这些指标 + JVM pause WARN 日志;频繁 WARN 说明 GC 是瓶颈,应调堆大小/GC 算法/减少大对象分配。

**调参建议**:阈值一般保持默认;若集群本身 GC 压力大、日志被 INFO 刷屏,可上调 `minor.pause.threshold`;`sleep.interval` 调小检测更灵敏但增一点常驻开销(可忽略)。standalone FUSE 进程默认不开,长跑 FUSE 排查卡顿时可临时开 `standalone.fuse.jvm.monitor.enabled=true`。

### 3.3 资源泄漏检测 `leak.detector.*`(Netty ResourceLeakDetector 级别语义)

> `AlluxioResourceLeakDetector` 继承 Netty `ResourceLeakDetector`,用于追踪 `CloseableResource`/`LockResource`/gRPC 流等未 `close()` 就被 GC 的泄漏。

**`leak.detector.level`(默认 `DISABLED`,枚举,Scope=ALL,`IGNORE`)**:值取自 Netty `ResourceLeakDetector.Level`,`AlluxioResourceLeakDetector` 的 **static 块在类加载时读一次**并 `ResourceLeakDetector.setLevel()` 设为全局级别(**进程级、不可热改**)。四档开销递增:
| 级别 | 行为 | 开销 |
|---|---|---|
| `DISABLED` | 不追踪任何泄漏 | 无(**生产默认**) |
| `SIMPLE` | **抽样**部分资源,仅报泄漏、不记最近访问轨迹 | 低 |
| `ADVANCED` | 抽样 + 记录对象**最近访问栈** | 较高 |
| `PARANOID` | **追踪每一次分配**,信息最全 | 最高(严重降性能) |

**`leak.detector.exit.on.leak`(默认 false,Scope=ALL,`IGNORE`)**:检测到泄漏时,`reportTracedLeak`/`reportUntracedLeak` 除了打 ERROR 日志("`X.close()` was not called before ... garbage-collected"),还会 **`System.exit(1)` 直接终止 JVM**——**仅测试/CI 用**,生产绝不可开(一次误报即导致进程退出)。

**建议**:生产保持 `DISABLED`;定位疑似 ByteBuf/连接泄漏时,**临时**开 `SIMPLE`(开销可控),查完立即关;`ADVANCED`/`PARANOID` 仅在开发/压测环境短时使用。

### 3.4 退出信息 dump `exit.collect.info`(崩溃排障关键,翻 `ProcessUtils` 求证)

**`exit.collect.info`(默认 true,Scope=SERVER,`WARN`)**:进程退出时 `ProcessUtils.dumpInformationOnExit()` 把现场快照 dump 到 `logs.dir`:
- **metrics**:整个 `MetricsSystem.METRIC_REGISTRY` 序列化为 JSON(约 100KB),文件 `alluxio-<type>-exit-metrics-<时间>.json`。
- **jstack**:全线程栈,文件 `alluxio-<type>-exit-stacks-<时间>.txt`。

**代码级要点**:
- 仅对 **MASTER/WORKER** 生效(`COLLECT_ON_EXIT` 白名单,client/其它类型跳过;与 description "only applies to master and worker" 一致)。
- **同步执行**(阻塞退出流程)——为尽量抓全崩溃现场,故进程停止会稍慢。
- 内部有 `sInfoDumpOnExitCheck` 幂等保护,一次退出只 dump 一次。
- 关闭时(false)会打日志提示"set ...=true to enable"。

**建议**:保持开启——这是崩溃/OOM/被 kill 后**唯一能拿到退出瞬间 metrics + jstack** 的手段;关掉会丢失事后分析素材。代价仅是退出多花百毫秒级 + logs 目录多两个文件。

### 3.5 文件锁 TTL `file.lock.manager.unused.lock.expiration.ttl`

- **`file.lock.manager.unused.lock.expiration.ttl`(默认 1h,duration,Scope=ALL,`IGNORE`)**:文件锁管理器中**空闲锁对象**的存活时长,超时后回收——控制锁表的内存占用。一般无需改;锁竞争极高、锁对象频繁创建的场景可适当调小以更快回收(权衡:太小会增加重复创建开销)。

### 3.6 License 校验 `alluxio.license` / `license.check.*`(翻 `EnterpriseLicenseChecker` 求证)

> Enterprise 版授权校验,由 `EnterpriseLicenseChecker` 实现,底座是 etcd(见 [14组](14-membership-etcd.md) license.etcd)。

**四态生命周期(`License.getLicenseStatus`)**:按当前时间对比到期日与宽限期日,返回四态,行为逐级收紧:
| 状态 | 触发 | 行为 |
|---|---|---|
| `HEALTHY` | 距到期 > `expiration.pending.warning.days` | 正常 |
| `EXPIRATION_PENDING` | 进入到期前 N 天(默认 **7**)窗口 | `regularCheck` 打 WARN、UI 告警;**仍可运行/启动** |
| `GRACE_PERIOD` | 已过到期日、未过宽限期 | 打 WARN;**运行中进程继续跑,但新进程无法启动**(`startupCheck` 抛异常) |
| `EXPIRED` | 超过宽限期 | **进程终止且无法重启**(`startupCheck`/`regularCheck` 均抛 `LicenseCheckException`) |

**`startupCheck()`(启动时,一次性且有副作用)**:校验链——production ID 匹配、version 正则匹配当前 `alluxio.version`、bound cluster 匹配(容忍 ≤2 且 ≤半数节点差异)、到期状态、**每进程资源约束**(vCPU/JVM 内存/存储容量,worker 用 `worker.page.store.sizes` 汇总)、**集群总量约束**(进程数/总 vCPU/总存储,从 etcd 汇总各进程)。通过后以 **60s lease**(`LICENSE_RESOURCE_LEASE_TTL_SECOND`)注册到 etcd `/LE/instances/<cluster>`,并在 license 从 etcd 下发时挂 watch 监听热更换 license。

**`regularCheck()`(运行期周期检查)**:挂在 master 的 **`MASTER_LICENSE_CHECK` 心跳**上,周期 = `license.check.interval.second`(默认 **300s = 5min**)。每次:检查四态(见上);若 license 带集群约束,还从 etcd 读回本进程注册项——**若发现自己已被摘除(decommission)则退出**;若 etcd 连不上,累计错误时间超 `LICENSE_ETCD_CONNECTION_ERROR_TOLERANT_SECOND`(默认 **24h**,换算成次数 = 24h/interval)才退出(容忍短时 etcd 抖动)。

**配置项精确对应**:
- `alluxio.license`(`LICENSE_STRING`,ENFORCE):license 内容字符串本身(通常经文件/etcd 下发,base64 编码,`LicenseCryptography` 加解密)。
- `license.check.enabled`(ENFORCE):是否启用校验。**注意**:是否真正读这个属性取决于**编译常量 `license.check.configurable`**——`LicenseConstants.getEnabled()` 仅当该编译常量为 true 时才读运行时属性,否则用编译期固定值。同理 `license.check.interval.second`、连接容忍时长也受此编译常量门控(**发行版通常不可运行时改**,建议验证)。
- `license.expiration.pending.warning.days`(变量名 `LICENSE_EXPIRATION_PENDING_WARNING_DURATION_DAYS`,默认 7,ENFORCE):进入 `EXPIRATION_PENDING` 的提前告警天数。

**运维建议**:监控 `EXPIRATION_PENDING` WARN 日志 + `LICENSE_EXPIRATION_DATE` 指标,**至少提前 7 天续期**;避免拖到 `GRACE_PERIOD`(新进程/扩容将起不来)甚至 `EXPIRED`(集群停摆)。license 依赖 etcd,etcd 长时间不可用(>24h)也会导致进程按 license 保护退出。

### 3.7 动态配置(**两套系统辨析** + `conf.validation.enabled`)

> ⚠️ 本组两个 key 常被混为一谈,实为**两套不同的动态配置机制**:

**(A)`conf.dynamic.update.enabled`(默认 false,Scope=ALL,`WARN`)**:属性级"运行期热更某些 `alluxio.*` 属性"的总开关。翻代码:该 PropertyKey 在 Java 主干**无直接消费者**(仅有 CLI `fsadmin` 的编辑命令与该能力相关),推测其运行期热更逻辑由 console/Go 层或特定命令路径消费。**因此不要指望打开它就能热改任意配置**——大量 key 是 `ENFORCE`(需全集群一致)或需重启才生效,能热更的是很小子集(建议验证具体哪些)。

**(B)`dynamic.configuration.etcd.*` + `EtcdDynamicConfiguration`(实体级动态配置,现役主力)**:这是一套**基于 etcd 的实体(Entity)动态配置系统**,与 (A) 不同——它管理的是 `alluxio.conf.dynamic` 包下的**结构化实体**(路径配置、虚拟路径映射、缓存过滤、限流、TTL 规则、配额、副本规则等),而非扁平的 `alluxio.*` 属性。机制:
- `DynamicConfiguration.global()`:**设了 `etcd.endpoints` 就用 `EtcdDynamicConfiguration`,否则退回 `InMemoryDynamicConfiguration`**。
- `dynamic.configuration.etcd.sync.interval`(默认 **10s**,ENFORCE):后台单线程 updater 全量 range-scan `/alluxio/CONF/<cluster>/` 前缀、刷新本地快照的周期。
- `dynamic.configuration.etcd.timeout`(默认 **3s**,ENFORCE):访问 etcd 的单次超时(配 `ExponentialBackoffRetry` + `etcd.max.retries`)。
- 支持 create/replace(乐观锁 CAS,靠 modRevision)/put/patch/delete,写后经 `mCallbackQueue` 异步触发 watch 回调,让相关特性即时感知变更。`isInitialized()` 用于区分"没这条配置" vs "还没首次加载完",首次成功 range-scan 后才置 true(etcd 启动期抖动不会误判为空)。
- 降级兼容:遇到本版本没有的实体类(如降级后 etcd 里存着新版实体)会**每 key 只 warn 一次并跳过**,不影响其它配置同步。

**`conf.validation.enabled`(默认 true,Scope=ALL,`WARN`)**:客户端/服务端初始化时是否校验配置属性(类型、取值、一致性)。**保持默认 true**——关掉会让错误配置到运行期才暴露;仅在极特殊需要绕过校验的场景临时关。

### 3.8 多集群 / K8s / 运行时能力

- **`multi.cluster.enabled`(默认 false,ALL)** + **`multi.cluster.config.path`(ALL)**:开启后客户端可连**多个 Alluxio 集群**;`MultiClusterConfig` 从 `multi.cluster.config.path` 指定的文件读各集群定义。跨区域/多集群副本放置(见 [14组](14-membership-etcd.md) 的 multi.cluster 副本规则)场景使用。
- **`k8s.env.deployment`(默认 false,ALL,`ENFORCE`)**:标记进程运行在 K8s 环境,影响主机名解析/网络绑定等行为(与 [15组](15-network-transport.md) `ip.address.used` 等配合)。`ENFORCE` 表示需全集群一致。
- **`extra.loaded.filesystem.classname`(默认 `alluxio.client.file.DoraCacheFileSystem`,class,ALL,`ENFORCE`)**:客户端 `FileSystem.Factory` 的 **static 块显式加载**的文件系统类。默认加载 `DoraCacheFileSystem`,确保 DORA 缓存文件系统实现被类加载器提前注册。一般无需改;定制/替换客户端 FS 实现时才动(改错会导致客户端起不来)。

### 3.9 杂项:版本 / 调试 / 测试 / 线程 / 时钟容错 / 权限 / 校验和

| 配置项 | 默认值 | Scope | 说明与代码级要点 |
|---|---|---|---|
| `alluxio.version` | 构建常量 `ProjectConstants.VERSION` | ALL(`IGNORE`,`setIgnoredSiteProperty`) | Alluxio 版本号,**用户绝不可改**;license 的 version 正则(见 3.6)校验的就是它 |
| `alluxio.debug` | false | SERVER(`WARN`) | 调试模式:额外日志 + Web UI 展示更多内部信息。排障时临时开;**生产勿常开**(日志量大、UI 暴露内部状态) |
| `alluxio.test.mode` | false | ALL(`WARN`) | 测试模式,放开若干"仅测试可用"的特殊行为;**仅测试用,生产必须 false** |
| `alluxio.ds.worker.copy.threads.max` | 128 | WORKER(`WARN`) | 变量名 `WORKER_DS_COPY_EXECUTOR_THREADS_MAX`;data shuttle 拷贝线程池上限(`GrpcExecutors` 消费)。大量 copy/move 作业时可上调,注意 worker CPU/内存 |
| `alluxio.cacheability.timestamp.error.margin` | 1s | ALL | 比较 cacheability 时间戳时的**容错窗口**,吸收 Alluxio 与 UFS 间**时钟不同步**。UFS/Alluxio 节点时钟漂移较大时可适当调大,避免误判缓存失效 |
| `alluxio.load.job.without.quota.allowed` | true | ALL | 变量名 `DORA_LOAD_JOB_WITHOUT_QUOTA_ALLOWED`;load 作业遇到**配额不存在**时是否跳过配额检查(默认跳过)。与 [19组](19-write-ttl-quota.md) 配额、[14组](14-membership-etcd.md) `must.check.quota` 配合 |
| `alluxio.pddm.permission.check.enabled` | false | ALL(`WARN`) | 开启后 worker 执行 PDDM copy/move 作业时,**向安全服务(security server)发 RPC 校验用户权限**。默认关(省一次 RPC);启用鉴权隔离时开,代价是每作业多一次安全服务往返 |
| `alluxio.hadoop.checksum.combine.mode` | 无默认 | CLIENT(`WARN`,boolean) | Hadoop 文件 checksum 的合并模式,影响 `getFileChecksum` 与 HDFS 兼容行为;按需在客户端设 |
| `debug.fuse.slowness.injector.path` | `/tmp/slowness_injection.json` | ALL(`ENFORCE`) | **(测试/故障注入)** 若该文件存在,对其中指定路径注入人为慢速——用于验证慢 IO 下的行为。生产勿设 |
| `debug.performance.diagnostics.enabled` | false | ALL(`ENFORCE`) | **(诊断)** 开启后暴露**虚拟性能诊断文件**,便于排查性能问题。属诊断开关,按需临时开 |
| `<TEST_DEPRECATED_KEY>` | — | — | ⚠️**已废弃**,仅用于测试废弃机制,忽略 |

**别名/废弃小结(本组 2 别名 1 废弃)**:
- `jvm.monitor.warn.threshold` 别名 `jvm.monitor.severe.pause.threshold`(见 3.2)。
- MASTER 的 UFS 根 `master.mount.table.root.ufs` 别名 `underfs.address`(见 3.1,速查表误并入 work.dir 行)。
- `TEST_DEPRECATED_KEY` 永久废弃,仅测试。

---

## 4. 配置关联关系图

```mermaid
flowchart TD
    HOME[alluxio.home /opt/alluxio] --> CONF[conf.dir ${home}/conf]
    HOME --> WORK[work.dir ${home}<br/>journal/logs/本地UFS]
    HOME --> LIB[lib.dir ${home}/lib]
    WORK --> LOGS[logs.dir ${work}/logs]
    WORK -.默认值引用.-> UFSROOT[master.mount.table.root.ufs<br/>别名 underfs.address]
    ENV[环境变量 $ALLUXIO_CONF_DIR<br/>site属性被忽略] -.唯一改位置方式.-> CONF

    JVM[jvm.monitor 阈值] --> PAUSE{pauseMs vs 阈值}
    PAUSE -->|>warn 10s| W[WARN + GC/内存快照]
    PAUSE -->|>minor 1s| I[INFO]
    W --> HEALTH[JVM_PAUSE 健康监控<br/>10min窗口 + frequency 0.1]
    HEALTH --> METRIC[Process.TotalExtraTime<br/>WarnTimeExceeded]
    METRIC -.排障.-> GC[调堆/GC参数]

    EXIT[exit.collect.info=true] --> DUMP[ProcessUtils.dumpInformationOnExit<br/>metrics.json + jstack → logs.dir<br/>仅MASTER/WORKER 同步]
    LEAK[leak.detector.level DISABLED] -.仅测试.-> LV[SIMPLE→ADVANCED→PARANOID<br/>开销递增/进程级不可热改]
    LEAKEXIT[exit.on.leak] -.测试.-> SEXIT[检测到即 System.exit-1]

    LIC[license 四态] --> HEALTHY --> PENDING[到期前7天 WARN] --> GRACE[宽限期:老进程跑/新进程起不来] --> EXPIRED[超宽限:进程退出]
    LIC -.startupCheck/regularCheck.-> LETCD[14 license.etcd<br/>60s lease + 5min心跳]
    LETCD -.etcd缺失>24h.-> SEXIT2[进程退出]

    subgraph DYN[动态配置:两套系统]
      A[conf.dynamic.update.enabled<br/>属性级/主干无消费者<br/>仅小子集可热更 待验证]
      B[EtcdDynamicConfiguration<br/>实体级/etcd/sync 10s timeout 3s<br/>路径映射/限流/TTL/配额...]
    end
    ETCDSET{etcd.endpoints 设置?} -->|是| B
    ETCDSET -->|否| INMEM[InMemoryDynamicConfiguration]

    K8S[k8s.env.deployment ENFORCE] -.配合.-> IP[15 ip.address.used]
    EXTRAFS[extra.loaded.filesystem<br/>DoraCacheFileSystem] --> FSFACTORY[FileSystem.Factory static加载]
```

---

## 5. 典型场景配置组合建议

| 场景 | 推荐组合 | 理由 |
|---|---|---|
| **崩溃/延迟排障** | `exit.collect.info=true`(默认) + 关注 `jvm.monitor.*` WARN 与 `Process.TotalExtraTime`/`WarnTimeExceeded` 指标 | 退出快照(metrics+jstack)+ GC 停顿定位闭环 |
| **GC 停顿灵敏度调整** | 日志被 INFO 刷屏→上调 `jvm.monitor.minor.pause.threshold`;需更早预警→下调 `sleep.interval` | 平衡检测灵敏度与噪声(注意 warn 必须 > minor,否则启动报错) |
| **FUSE 长跑卡顿排查** | 临时开 `standalone.fuse.jvm.monitor.enabled=true` | 独立 FUSE 进程默认不监控 JVM |
| **K8s 部署** | `k8s.env.deployment=true`(ENFORCE,全集群一致) + [15]`ip.address.used` 评估 | 适配容器网络/主机名 |
| **多区域/多集群客户端** | `multi.cluster.enabled=true` + `multi.cluster.config.path` 指向集群定义文件 | 客户端连多集群、跨集群副本 |
| **改目录位置** | 用 `$ALLUXIO_CONF_DIR`/`$ALLUXIO_LOGS_DIR` 环境变量;临时/UFS 上传暂存改 `tmp.dirs` 指持久大盘 | `conf.dir` 等 site 属性被忽略,只能环境变量;`/tmp` 易满/重启清空 |
| **排查内存/连接泄漏(临时)** | `leak.detector.level=SIMPLE` | 低开销抽样追踪(生产查完即关;绝不开 `exit.on.leak`) |
| **实体级动态配置(路径映射/限流/TTL/配额)** | 配 `etcd.endpoints` 走 `EtcdDynamicConfiguration`;按需调 `dynamic.configuration.etcd.sync.interval`/`timeout` | 免重启热更结构化实体配置(非扁平 `alluxio.*` 属性) |
| **License 续期防护** | 监控 `EXPIRATION_PENDING` WARN + `LICENSE_EXPIRATION_DATE` 指标,提前 >7 天续期 | 避免进入 GRACE_PERIOD(扩容起不来)/EXPIRED(停摆) |
| **PDDM 需鉴权隔离** | `pddm.permission.check.enabled=true` | copy/move 作业向安全服务校验用户权限(代价:每作业多一次 RPC) |

---

## 6. 风险与注意事项

1. **`leak.detector.level` 生产勿开高级别**:ADVANCED/PARANOID 严重降性能(PARANOID 追踪每次分配);级别在类加载时读一次、**进程级不可热改**。仅排障临时开 SIMPLE。
2. **`leak.detector.exit.on.leak` 生产绝不可开**:一次泄漏报告即 `System.exit(1)`,仅测试用。
3. **改目录直接改 site 属性不生效**:`conf.dir` 等带 `setIgnoredSiteProperty(true)`,只能用环境变量(`$ALLUXIO_CONF_DIR`/`$ALLUXIO_LOGS_DIR`)。
4. **`tmp.dirs` 语义受限且默认 /tmp**:当前仅用于 UFS 上传暂存;生产应指持久大盘,避免 `/tmp` 满或重启清空。
5. **License 生命周期风险**:四态 HEALTHY→EXPIRATION_PENDING(前 7 天)→GRACE_PERIOD(老进程跑/新进程起不来)→EXPIRED(进程退出)。需监控告警提前续期;且 license 依赖 etcd——**etcd 连不上超 24h 也会触发按 license 保护退出**。
6. **`license.check.*` 可能不可运行时改**:是否读运行时属性受编译常量 `license.check.configurable` 门控,发行版通常用编译期固定值(建议验证)。
7. **两套动态配置勿混淆**:`conf.dynamic.update.enabled` 是属性级开关(主干无直接消费者,能热更子集很小,建议验证);`EtcdDynamicConfiguration`(etcd 设置时启用,sync 10s/timeout 3s)才是实体级动态配置主力。大量 `ENFORCE`/需重启的 key 不吃任何动态更新。
8. **"`work.dir` 双定义"是分组假象**:实为 `work.dir`(SERVER 工作目录)与 `master.mount.table.root.ufs`(别名 `underfs.address`,MASTER 根 UFS 地址)两个不同 key,仅默认值互相引用,语义完全不同。
9. **`exit.collect.info` 勿关**:关掉会丢失崩溃/OOM/被 kill 时唯一的退出快照(metrics+jstack);代价仅退出多花百毫秒级。
10. **诊断/测试项勿带上生产**:`debug`/`test.mode`/`debug.fuse.slowness.injector.path`/`debug.performance.diagnostics.enabled` 仅排障或测试用。
11. **`extra.loaded.filesystem.classname` 改错致客户端起不来**:默认 `DoraCacheFileSystem` 由 `FileSystem.Factory` static 块加载,非必要不动(ENFORCE,需全集群一致)。

---

## 跨组关联速览
- [07-worker-mgmt](07-worker-mgmt.md) / [13-coordinator-master](13-coordinator-master.md) —— 各角色 JVM 监控开关
- [14-membership-etcd](14-membership-etcd.md) —— license.etcd / 动态配置 etcd 底座
- [15-network-transport](15-network-transport.md) —— K8s/IP 网络适配
- [10-ufs-common](10-ufs-common.md) —— work.dir 的 UFS 根(underfs.address)

---

## 附录A:本组全量配置清单(脚本生成)

> 由 `_data/gen_table.py 20-jvm-system-misc` 生成,逐 key 一行,保证覆盖本组**全部 42 项**(与上文按子场景组织的中文速查表互补;此处描述为官方英文原文,便于精确检索)。

| 配置项 | 默认值 | 类型 | Scope | 一致性 | 状态 | 说明 |
|---|---|---|---|---|---|---|
| `<unresolved:TEST_DEPRECATED_KEY>` | — | — | — | — | ⚠️废弃→This key is used only for testing. It is always deprecated | — |
| `alluxio.cacheability.timestamp.error.margin` | "1s" | duration | ALL | — | — | The error margin when comparing timestamps in cacheability requirements to account for out of sync clocks between Alluxio and the UFS |
| `alluxio.conf.dir` | format("${%s}/conf", Name.HOME) | string | ALL | WARN | — | The directory of Alluxio configuration files. This property is only for internal use. To change the location, set environment variable $ALLUXIO_CON... |
| `alluxio.conf.dynamic.update.enabled` | false | boolean | ALL | WARN | — | Whether to support dynamic update property. |
| `alluxio.conf.validation.enabled` | true | boolean | ALL | WARN | — | Whether to validate the configuration properties when initializing Alluxio clients or server process. |
| `alluxio.debug` | false | boolean | SERVER | WARN | — | Set to true to enable debug mode which has additional logging and info in the Web UI. |
| `alluxio.ds.worker.copy.threads.max` | 128 | int | WORKER | WARN | — | Maximum number of copy thread pools in data shuttle. |
| `alluxio.dynamic.configuration.etcd.sync.interval` | "10s" | duration | ALL | ENFORCE | — | Interval for syncing the dynamic configurations from etcd |
| `alluxio.dynamic.configuration.etcd.timeout` | "3s" | duration | ALL | ENFORCE | — | Timeout for accessing etcd cluster in dynamic configuration management |
| `alluxio.exit.collect.info` | true | boolean | SERVER | WARN | — | If true, the process will dump metrics and jstack into the log folder. This only applies to Alluxio master and worker processes. |
| `alluxio.extra.loaded.filesystem.classname` | "alluxio.client.file.DoraCacheFileSystem" | class | ALL | ENFORCE | — | Full name of the class that will be loaded explicit for filesystem. |
| `alluxio.file.lock.manager.unused.lock.expiration.ttl` | "1h" | duration | ALL | IGNORE | — | TTL of locks in file lock manager. |
| `alluxio.hadoop.checksum.combine.mode` | — | — | CLIENT | WARN | — | File Checksum combine mode. |
| `alluxio.home` | "/opt/alluxio" | string | ALL | WARN | — | Alluxio installation directory. |
| `alluxio.jvm.monitor.minor.pause.frequency.threshold` | 0.1 | double | SERVER | WARN | — | When the ratio of the total time of minor pauses in a fixed time window exceeds this threshold, flag as if a severe pause has happened. |
| `alluxio.jvm.monitor.minor.pause.threshold` | "1sec" | duration | SERVER | WARN | — | When the JVM pauses for anything longer than this, log an INFO message. |
| `alluxio.jvm.monitor.sleep.interval` | "1sec" | duration | SERVER | WARN | — | The time for the JVM monitor thread to sleep. |
| `alluxio.jvm.monitor.warn.threshold` | "10sec" | duration | SERVER | WARN | 别名:alluxio.jvm.monitor.severe.pause.threshold | When the JVM pauses for anything longer than this, log a WARN message. |
| `alluxio.k8s.env.deployment` | false | boolean | ALL | ENFORCE | — | If Alluxio is deployed in K8s environment. |
| `alluxio.leak.detector.exit.on.leak` | false | boolean | ALL | IGNORE | — | If set to true, the JVM will exit as soon as a leak is detected. Use only in testing environments. |
| `alluxio.leak.detector.level` | ResourceLeakDetector.Level.DISABLED | enum | ALL | IGNORE | — | Set this to one of {DISABLED, SIMPLE, ADVANCED, PARANOID} to track resource leaks in the Alluxio codebase. DISABLED does not track any leaks. SIMPL... |
| `alluxio.lib.dir` | String.format("${%s}/lib", PropertyKey.Name.HOME) | string | — | — | — | — |
| `alluxio.license` | — | string | ALL | ENFORCE | — | String represented license content |
| `alluxio.load.job.without.quota.allowed` | true | boolean | ALL | — | — | If the quota not exist, the job skip quota check. |
| `alluxio.multi.cluster.config.path` | — | string | ALL | — | — | The alluxio multi cluster config path file |
| `alluxio.multi.cluster.enabled` | false | boolean | ALL | — | — | If enabled, alluxio client is able to connect to multiple clusters |
| `alluxio.pddm.permission.check.enabled` | false | boolean | ALL | WARN | — | If enabled, when the workers executes the PDDM copy job and move job, workers will make RPCs to the security server to check user permissions. |
| `alluxio.site.conf.dir` | — | list | ALL | WARN | — | Comma-separated search path for %s. |
| `alluxio.site.conf.rocks.block.file` | — | string | ALL | — | — | Path of file containing RocksDB block store configuration. A template configuration cab be found at ${%s}/rocks-block.ini.template. See https://git... |
| `alluxio.site.conf.rocks.inode.file` | — | string | ALL | — | — | Path of file containing RocksDB inode store configuration. A template configuration cab be found at ${%s}/rocks-inode.ini.template. See https://git... |
| `alluxio.standalone.fuse.jvm.monitor.enabled` | false | boolean | WORKER | WARN | — | Whether to enable start JVM monitor thread on the standalone fuse process. This will start a thread to detect JVM-wide pauses induced by GC or othe... |
| `alluxio.test.mode` | false | boolean | ALL | WARN | — | Flag used only during tests to allow special behavior. |
| `alluxio.third.party.dir` | — | string | SERVER | WARN | — | The directory containing Alluxio third party jars. |
| `alluxio.tmp.dirs` | "/tmp" | list | SERVER | — | — | The path(s) to store Alluxio temporary files, use commas as delimiters. If multiple paths are specified, one will be selected at random per tempora... |
| `alluxio.version` | ProjectConstants.VERSION | string | ALL | IGNORE | — | Version of Alluxio. User should never modify this property. |
| `alluxio.work.dir` | format("${%s}", Name.HOME) | string | SERVER | WARN | — | The directory to use for Alluxio's working directory. By default, the journal, logs, and under file storage data (if using local filesystem) are wr... |
| `alluxio.work.dir` | format("${%s}/underFSStorage", Name.WORK_DIR) | — | MASTER | ENFORCE | 别名:alluxio.underfs.address | The storage address of the UFS at the Alluxio root mount point. |
| `debug.fuse.slowness.injector.path` | "/tmp/slowness_injection.json" | string | ALL | ENFORCE | — | If set, slowness will be injected for specific paths for testing |
| `debug.performance.diagnostics.enabled` | false | boolean | ALL | ENFORCE | — | If enabled, virtual performance diagnostics files are accessible to debug performance issues |
| `license.check.enabled` | Boolean.parseBoolean(LicenseConstants.LICENSE_CHECK_ENABLED) | boolean | ALL | ENFORCE | — | Whether license check is enabled |
| `license.check.interval.second` | LicenseConstants.LICENSE_CHECK_INTERVAL_SECOND | int | ALL | ENFORCE | — | The interval for license checking in seconds |
| `license.expiration.pending.warning.days` | 7 | int | ALL | ENFORCE | — | The number of days before license expiration to start displaying warnings |
