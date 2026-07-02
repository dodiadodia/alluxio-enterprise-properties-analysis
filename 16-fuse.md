# 16 · FUSE 挂载

> 场景组:`alluxio.fuse.*` + `alluxio.user.fuse.*`
> 配置数:**82** · 别名 8 · 废弃 0 · 数据来源:`PropertyKey.java` · 生成表:`_data/gen_table.py 16`

---

## 1. 本组概览

FUSE 把 Alluxio 挂载成本地 POSIX 文件系统,让 PyTorch/训练脚本/传统应用**像读本地文件一样**读 Alluxio(AI 训练最常用入口)。本组管挂载、POSIX 语义适配、认证、写回缓存、随机写流、非中断迁移。多为 `Scope=CLIENT`(FUSE 进程)。

六个子场景:

| 子场景 | 关键配置 | 核心矛盾 |
|---|---|---|
| 挂载 | `mount.point`、`mount.options`、`mount.alluxio.path` | 挂载行为 |
| POSIX 语义适配 | `enable.read.dir.plus`、`silly.rename`、`symlink`、`fsync`、`hard.link` | 兼容性 vs 性能 |
| 认证/权限 | `auth.policy.class`、`user.group.translation`、`authorization.user.cache.*` | 权限正确 vs 开销 |
| 写回缓存(writeback) | `user.fuse.write.back.*`(约 18 项) | 写吞吐 vs 空间/一致性 |
| 随机写流 | `user.fuse.random.access.*`、`local.backed.stream.*` | 随机写支持 vs 复杂度 |
| 非中断迁移 | `non.disruptive.migration.*`、`migration.ongoing.request.grace` | K8s 平滑升级 |

---

## 2. 配置清单速查表(全量 82 项)

### 2.1 挂载
| 配置项 | 默认值 | 类型 | Scope | 说明 |
|---|---|---|---|---|
| `alluxio.fuse.mount.point` | /mnt/alluxio-fuse | string | ALL | 本地挂载路径(别名 worker.fuse.*) |
| `alluxio.fuse.mount.alluxio.path` | / | string | ALL | 映射到挂载点的 Alluxio 路径(别名) |
| `alluxio.fuse.mount.options` | attr_timeout=600,entry_timeout=600 | list | ALL | FUSE 挂载选项(别名) |
| `alluxio.fuse.fs.name` | alluxio-fuse | string | CLIENT | FUSE 文件系统名 |
| `alluxio.fuse.umount.timeout` | 0s | duration | CLIENT | 卸载前等在途读写完成(0=不等) |
| `alluxio.fuse.web.port` / `bind.host` / `hostname` | 49999 / 0.0.0.0 / — | — | CLIENT | FUSE Web UI |
| `<unresolved:FUSE_V2_ENABLED>` | false | boolean | ALL | 启用 FUSE V2(模板名) |

### 2.2 POSIX 语义适配与性能
| 配置项 | 默认值 | 类型 | Scope | 说明 |
|---|---|---|---|---|
| `alluxio.fuse.enable.read.dir.plus` | true | boolean | CLIENT | 按 offset 读目录(readdirplus) |
| `alluxio.fuse.read.dir.plus.batch.size` | 12 | int | CLIENT | readdirplus 批大小 |
| `alluxio.fuse.dir.stream.cache.size` | 100000 | int | CLIENT | 单次列举缓存的子项数 |
| `alluxio.fuse.cached.paths.max` | 500 | int | CLIENT | FUSE↔Alluxio 路径映射缓存数 |
| `alluxio.fuse.list.timeout` | 0s | duration | CLIENT | 列目录超时(≤0 等到完成) |
| `alluxio.fuse.enforce.direct.io.read` | false | boolean | CLIENT | 只读文件强制 direct io |
| `alluxio.fuse.fast.copy.enabled` | false | boolean | CLIENT | 忽略 chmod/chown 加速拷贝 |
| `alluxio.fuse.silly.rename.interceptor.enabled` | false | boolean | CLIENT | 拦截 .fuse_hidden 的 silly rename |
| `alluxio.fuse.special.command.enabled` | false | boolean | CLIENT | 允许 .alluxiocli 特殊命令 |
| `alluxio.fuse.use.create.file.options.overwrite.flag` | false | boolean | ALL | 覆盖用 overwrite flag 而非先删 |
| `alluxio.fuse.max.reader.concurrency` | 1024 | int | ALL | 单文件最大并发读 |
| `alluxio.fuse.open.read.status.cache.enabled` | false | boolean | CLIENT | 缓存 URIStatus 1s 避免重复 getStatus |
| `alluxio.fuse.enable...`(其余见生成表) | — | — | — | 其它 POSIX 行为开关 |
| `alluxio.user.fuse.symlink.enabled` | false | boolean | CLIENT | 启用符号链接 |
| `alluxio.user.fuse.fsync.enabled` | false | boolean | CLIENT | (实验)处理 fsync |
| `alluxio.user.fuse.hard.link.fallback.as.copy` | false | boolean | CLIENT | 硬链接失败回退为拷贝 |
| `alluxio.user.fuse.multipart.upload.enabled` | false | boolean | CLIENT | 写 UFS 时分片并行上传 |
| `alluxio.user.fuse.sync.close.enabled` | true | boolean | CLIENT | 关闭文件时同步刷入 UFS |

### 2.3 认证与权限
| 配置项 | 默认值 | 类型 | Scope | 说明 |
|---|---|---|---|---|
| `alluxio.fuse.auth.policy.class` | LaunchUserGroupAuthPolicy | class | CLIENT | 认证策略类 |
| `alluxio.fuse.auth.policy.custom.user` / `custom.group` | — | string | CLIENT | 自定义策略的用户/组 |
| `alluxio.fuse.authorizer.classname` | CustomPolicyAuthorizer | class | CLIENT | 授权器类 |
| `alluxio.fuse.user.group.translation.enabled` | false | boolean | CLIENT | Alluxio 用户/组翻译成 Unix uid/gid |
| `alluxio.fuse.authorization.user.group.translation.enabled` | false | boolean | CLIENT | 授权中的用户/组翻译 |
| `alluxio.fuse.authorization.user.cache.max.size` | 10000 | int | CLIENT | 授权信息缓存用户数 |
| `alluxio.fuse.authorization.user.cache.expiration.time` | 1h | duration | CLIENT | 授权缓存过期 |

### 2.4 写回缓存(writeback,约 18 项)
| 配置项 | 默认值 | 类型 | 说明 |
|---|---|---|---|
| `alluxio.user.fuse.write.back.buffer.size` | 1MiB | dataSize | writeback 内存缓冲 |
| `alluxio.user.fuse.write.back.dir` / `dir.quota` | — / 0(无限) | — | writeback 目录及配额 |
| `alluxio.user.fuse.write.back.dir.quota.max.usage.ratio` | 0.8 | double | 配额用量超此比例降级为常规写 |
| `alluxio.user.fuse.write.back.max.acceleration.threads` | 16 | int | 本地 writeback 线程(共享) |
| `alluxio.user.fuse.write.back.max.upload.tasks` | 10000 | long | 最大异步上传任务(超则降同步) |
| `alluxio.user.fuse.write.back.allow.overwrite.uploading.files` | true | boolean | 允许覆盖正上传的文件 |
| `alluxio.user.fuse.write.back.degraded.sync.write.on.insufficient.space` | false | boolean | 空间不足时降级同步写(而非报错) |
| `alluxio.user.fuse.write.back.sync.flush.empty.file` | true | boolean | 空文件同步创建到 UFS |
| `alluxio.user.fuse.write.back.status.bloom.filter.enabled` / `.refresh.period` | false / 5min | — | 布隆过滤状态(加速小文件写) |
| `alluxio.user.fuse.write.cache.async.delete.enabled` | true | boolean | 删除/覆盖异步清理 page store |
| `alluxio.user.fuse.write.cache.async.delete.thread.count` | 8 | int | 异步删除线程 |
| `alluxio.user.fuse.write.cache.async.delete.max.pending.file.count` / `.size` | 128K / 8GiB | — | 异步删除队列上限(满则降同步) |
| `alluxio.user.fuse.write.cache.defer.open.file.attr.update.enabled` | false | boolean | 已开写缓存文件的 chmod/chown 延迟本地 |

### 2.5 随机写流 / local backed stream
| 配置项 | 默认值 | 类型 | 说明 |
|---|---|---|---|
| `alluxio.user.fuse.random.access.file.stream.enabled` | false | boolean | 写已存在文件用随机写流 |
| `alluxio.user.fuse.force.random.access.write.stream.enabled` | true | boolean | 写文件总用 RandomAccessFuseFileStream |
| `alluxio.user.fuse.random.access.file.stream.atomic.write.enabled` | true | boolean | 随机写流用原子写上传 |
| `alluxio.user.fuse.random.access.file.stream.buffer.size` | 4MiB | int | 随机写流缓冲 |
| `alluxio.user.fuse.random.access.file.stream.truncate.immediately.enabled` | false | boolean | truncate(0) 立即同步到 UFS |
| `alluxio.user.fuse.read.write.random.access.stream.enabled` | false | boolean | 读写同流(同时读写) |
| `alluxio.user.fuse.read.write.random.access.stream.compatible.flush.enabled` | true | boolean | flush/fsync 兼容处理 |
| `alluxio.user.fuse.read.on.incomplete.file.enabled` | false | boolean | 允许读正在被创建的文件 |
| `alluxio.fuse.local.backed.stream.enabled` | false | boolean | 用多路复用随机读写流(替代旧实现) |
| `alluxio.fuse.local.backed.stream.buffer.size` | 4MiB | int | local backed stream 缓冲 |
| `alluxio.fuse.local.backed.stream.tmp.dir` / `.capacity` | /tmp/... / 1GB | — | local backed stream 临时目录/容量 |

### 2.6 非中断迁移 / 工作区元存储 / 其它
| 配置项 | 默认值 | 类型 | 说明 |
|---|---|---|---|
| `alluxio.fuse.non.disruptive.migration.enabled` | false | boolean | FUSE 非中断迁移(K8s 平滑升级) |
| `alluxio.fuse.non.disruptive.migration.state.file.directory.path` | /tmp | string | 迁移状态文件目录(新旧 pod 都可访问) |
| `alluxio.fuse.migration.ongoing.request.grace_period` | 5s | duration | 迁移前在途请求宽限(超时强制中止) |
| `alluxio.fuse.request.hard.timeout` | -1 | duration | 请求硬超时(>0 生效,到点立即失败) |
| `alluxio.fuse.return.timeout.error.on.request.hard.timeout` | true | boolean | 硬超时返回超时错误码 |
| `alluxio.fuse.in.memory.workspace.metastore.inode.quota` | 100万 | long | 内存工作区元存储 inode 配额(别名 fdb) |
| `alluxio.fuse.in.memory.workspace.metastore.logical.size.quota` | 10GB | dataSize | 逻辑大小配额(别名 fdb) |
| `alluxio.fuse.in.memory.workspace.metastore.state.persist.interval` | 5min | duration | 状态持久化间隔(别名 fdb) |
| `alluxio.fuse.in.memory.workspace.metastore.state.ufs.path` | /tmp/fs_snapshot | string | 状态持久化 UFS 路径(别名 fdb) |
| `<unresolved:FUSE_POSIX_LOCK_ENABLED>` | false | boolean | 分布式 POSIX 锁(需 GENERIC_FDB_BACKED_V2) |
| `alluxio.fuse.debug.enabled` / `logging.threshold` | false / 10s | — | 调试/慢调用日志 |
| `alluxio.user.fuse.cross.quota.domain.return.exdev.enabled` | false | boolean | 跨配额域 rename 返回 EXDEV |

---

## 3. 逐项深度分析(充分细节)

> 本组 82 项按配置族逐一深挖:挂载与元数据 TTL → 目录/读性能 → POSIX 语义适配(silly rename / xattr / symlink / hard link / special command)→ 认证与授权 → **写回缓存(writeback)降级链** → 随机写流三套实现 → 非中断迁移 → 内存工作区元存储与 POSIX 锁 → 超时/迁移收尾 → Web UI/调试。代码路径已翻证:FUSE 侧 `dora/integration/fuse/`,writeback 侧 `dora/core/client/fs/.../client/file/ufs/`(`LocalWriteBackCacheFileSystem`/`LocalWriteBackOutStream`/`UploadManager`)。

### 3.1 挂载与元数据 TTL(性能关键)

- **`mount.point`(默认 `/mnt/alluxio-fuse`)/`mount.alluxio.path`(默认 `/`)**:分别是本地挂载路径与映射到该挂载点的 Alluxio 路径(子树挂载)。三者均带别名 `alluxio.worker.fuse.*`(旧版 worker 内嵌 FUSE 的命名),Scope=ALL、一致性 WARN。
- **`mount.options`(默认 `attr_timeout=600,entry_timeout=600`,list,别名 `worker.fuse.mount.options`)**:平台相关的挂载选项,逗号分隔。**代码级机制**(`AlluxioFuse.buildLowLevelFuseStartupOptions`/`parseTimeoutSeconds`):`attr_timeout`/`entry_timeout` **被 FUSE 低层单独消费**(`LOW_LEVEL_CONSUMED_OPTIONS`),解析成秒后传给 `LowLevelFuseStartupOptions`,其余选项以 `-o key=value` 透传给 libfuse。语义是**内核缓存文件属性(stat)与目录项(lookup)各 600 秒**——绝大多数 getattr/lookup 直接命中内核缓存,不进 FUSE 进程,是只读高性能的关键;代价是**外部对 UFS 的改动最长 600s 内 FUSE 不可见**(陈旧窗口)。CLI `-o` 会覆盖配置文件里的同名项。
- **`open.read.status.cache.enabled`(默认 false)**:开启后同一**只读**文件被频繁 open 时缓存 URIStatus **1 秒**,避免每次 open 都发 getStatus RPC——训练反复打开同一批文件时收益显著。仅只读路径生效,与 `mount.options` 的内核缓存互补(一个缓 stat/lookup,一个缓 open 时的 status)。
- **`low.level.active.inode.attr.cache.ttl`(默认 `0ms`)**:低层 FUSE active inode 表里可**直接返回而不刷新**的属性快照最大保留时长;默认 0=每次都刷新(最新鲜)。
- **`umount.timeout`(默认 `0s`)**:收到 SIGTERM 时,卸载前等待在途读写完成的时长;`0`=不等,立即卸载(可能中断在途 IO)。生产建议设一个宽限值,避免 `fusermount` 卡死或 IO 被硬截断。
- **`fs.name`(默认 `alluxio-fuse`)**:FUSE 文件系统名(`df`/`mount` 显示)。
- **Web UI**:`web.port`(49999)/`web.bind.host`(0.0.0.0)/`web.hostname`——FUSE 内嵌 Jetty Web 服务,同时承载**非中断迁移的 REST 端点**(见 3.7)。
- **`<FUSE_V2_ENABLED>`(默认 false,模板名)**:启用 FUSE V2(低层 libfuse 接口 + `AlluxioJniFuseFileSystemV2`);V2 是当前的主实现,以下 POSIX 语义、迁移、POSIX 锁均在 V2 上落地。

### 3.2 目录与读性能(readdirplus / 并发 / direct io)

- **`enable.read.dir.plus`(默认 true)+ `read.dir.plus.batch.size`(默认 12)**:启用**按 offset 分批读目录**(readdirplus,一次返回目录项及其属性,省去逐项 getattr)。batch=12 是每次 offset 推进返回的条目数;大目录列举时批大内核往返少,但单批延迟高。
- **`dir.stream.cache.size`(默认 100000)**:一次目录列举中在内存缓存的子项数——大目录(十万级)列举时限制内存占用。
- **`cached.paths.max`(默认 500)**:FUSE 路径 ↔ Alluxio URI 转换的映射缓存条目数(`mPathResolverCache`,Guava LoadingCache),命中避免重复解析。
- **`list.timeout`(默认 `0s`)**:列目录超时;`≤0`=等到列完(不超时)。
- **`max.reader.concurrency`(默认 1024,ALL,一致性 WARN)**:单文件的最大并发读者数——高并发随机读(如多 DataLoader worker 读同一大文件)的上限。
- **`enforce.direct.io.read`(默认 false)**:对只读文件强制 direct io 模式(绕过内核页缓存),避免双重缓存(内核 + Alluxio client cache)带来的内存放大;顺序大文件读收益明显。
- **`pre.allocate.all.async.prefetch.buffers.enabled`(默认继承 `USER_POSITION_READER_STREAMING_ASYNC_PREFETCH_SHARED_CACHE_ENABLED`)**:是否预分配全部可用异步预取缓冲内存——与位置读的流式预取共享缓存联动(见 01 组)。
- **`fast.copy.enabled`(默认 false)**:拷贝场景忽略 chmod/chown,减少一次 setAttribute RPC 提速。
- **`use.create.file.options.overwrite.flag`(默认 false,ALL)**:覆盖写文件时用 `createFileOptions` 的 overwrite 标志**原子覆盖**,而非"先 delete 再 create"两步——避免中间态被别的请求看到。

### 3.3 POSIX 语义适配(兼容性关键,均在 V2 落地)

FUSE 需把 POSIX 语义翻译到对象存储/Alluxio,以下开关处理 libfuse 与内核带来的一系列 POSIX 惯例:

- **silly rename**(`silly.rename.interceptor.enabled`,默认 false):删除仍被打开的文件时,libfuse 会先把它 rename 成 `.fuse_hiddenXXXX` 占位、待最后 close 再 unlink。**代码机制**(`AlluxioJniFuseFileSystemV2` rename/unlink + `SillyRenamePathCache` + `AlluxioFuseUtils.isSillyRename`):开启后 Alluxio **拦截** silly rename——rename 目标是 `.fuse_hidden*` 时不真正在 UFS 建隐藏文件,而是把 inode→占位路径记入 `mSillyRenamePathCache`;最终 unlink 时按 inode 清理映射。避免在对象存储里遗留 `.fuse_hidden` 垃圾对象。writeback 侧也用正则 `\.fuse_hidden.+` **直接跳过**这些文件(`LocalWriteBackCacheFileSystem.localWriteBackEnabledForPath`)。
- **`intercept.system.xattr.get.enabled`(默认 true)**:对 `security.capability`、`system.posix_acl_access`、`system.posix_acl_default` 这几个内核**探针 xattr** 的 getxattr 请求,**本地直接回 `ENODATA`**(`AlluxioFuseUtils.shouldInterceptSystemXattrGet` + `getxattrInternal`),不发 RPC。内核在每次 exec/权限检查时都会探这些 xattr,拦截掉可**显著减少无谓 RPC**。默认开是纯收益。
- **`symlink.enabled`(默认 false)**:启用符号链接(`symlink`/`readlink`)。开启后 `symlinkInternal` 调 `mFileSystem.symlink`,`readlink` 校验 `isSymlink`。默认关是因为多数对象存储 UFS 无原生 symlink 语义。
- **hard link**(`link()` in V2):`hard.link.fallback.as.copy`(默认 false)=硬链接不被 UFS 支持时**回退为拷贝**而非报错;`hard.link.return.exdev.enabled`(默认 false)=针对 **RocksDB < 7.1.1 不正确处理 `EOPNOTSUPP`** 的 workaround,让 FUSE 返回 `EXDEV`(coreutils `mv`/`cp -l` 见 EXDEV 会自动降级为 copy+unlink)。代码里 `link` 失败按异常类型返回 `EOPNOTSUPP`/`EEXIST`/`ENOENT`,跨配额域按 `directoryQuotaErrno` 返回 `EXDEV`/`EDQUOT`。
- **`cross.quota.domain.return.exdev.enabled`(默认 false)**:rename/hard link 因源与目标处于**不同写缓存目录配额域**被拒时,返回的 errno 选择——开启返回 `EXDEV`(让 `mv` 降级为跨设备复制),否则默认 `EIO`。
- **`special.command.enabled`(默认 false)**:允许通过 `ls -l /mnt/alluxio-fuse/path/.alluxiocli.<command>.<subcommand>` 下发**特殊运维命令**(`FuseShell`/`isSpecialCommand` 检测 `.alluxiocli` 前缀,解析后走 `FuseCommand`)。是无需额外通道即可对挂载点做运维查询/操作的后门,默认关(有一定安全含义)。
- **`fsync.enabled`(默认 false,实验)**:处理 fsync,调用内部 flush 实现;随机写流的 `fsync()` 会把临时文件回传 UFS(见 3.5)。
- **`multipart.upload.enabled`(默认 false)**:写 UFS 时把数据分片并行上传(依赖对应 UFS 的 multipart 能力,如 `alluxio.underfs.s3.multipart.upload.enabled`),提升大文件写吞吐。
- **`sync.close.enabled`(默认 true)**:关闭文件时**同步刷入 UFS**——保证 close 返回即数据落 UFS(POSIX close 语义、写后强一致),代价是后续写/close 变慢。这是 FUSE 写的**默认安全语义**;writeback(3.4)是它的异步加速替代。
- **`read.on.incomplete.file.enabled`(默认 false)**:允许**读一个正在被另一线程创建的文件**(需随机写或位置写特性配合),用于边写边读的流水线场景。

### 3.4 认证与授权

- **`auth.policy.class`(默认 `alluxio.fuse.auth.LaunchUserGroupAuthPolicy`,一致性 IGNORE)**:认证策略类,由 `AuthPolicyFactory` 反射 `create(FileSystem, AlluxioConfiguration, Optional<FuseFileSystem>)` 实例化后 `init()`。可选值:
  - `LaunchUserGroupAuthPolicy`(默认):用**启动 FUSE 进程的 Unix uid/gid**(`AlluxioFuseUtils.getSystemUid/getSystemGid`)统一身份访问 Alluxio;`setUserGroup` 为空操作(不写回元数据 owner)——最简单、开销最低。
  - `CustomAuthPolicy`:用固定的 `auth.policy.custom.user`/`auth.policy.custom.group` 作为身份。
  - `UidAwareAuthPolicy`:用启动用户 uid/gid,但 `setUserGroupIfNeeded` 会**回写 uid/gid 到 Alluxio 元数据**(`setAttribute` + `useNumericOwner`),并从写缓冲 inode 读取真实 owner(`getUidFromUriStatus`)。
- **`authorizer.classname`(默认 `alluxio.fuse.auth.CustomPolicyAuthorizer`)**:授权器类(在 auth policy 之上做访问控制);另有 `PassAllAuthorizer`/`ReadOnlyAuthorizer` 等。
- **`user.group.translation.enabled`(默认 false,一致性 **ENFORCE**)**:把 Alluxio 用户名/组名翻译成 Unix uid/gid 暴露给 POSIX——需要 `ls -l` 显示**真实 owner/group**(而非全是启动用户)时开启。因涉及元数据展示一致性,是 **ENFORCE**(要求全一致)。
- **`authorization.user.group.translation.enabled`(默认 false)**:授权判定环节中的用户/组翻译(与上一项区别:上项管展示,此项管鉴权计算)。
- **`authorization.user.cache.max.size`(默认 10000)/`.expiration.time`(默认 `1h`)**:授权用户信息缓存条目数与过期——摊薄用户/组翻译与鉴权的开销(`UserGroupCache`)。缓存越大越省 RPC,过期越长越省但越可能陈旧。

### 3.5 写回缓存(writeback)—— FUSE 写性能核心(约 18 项)

FUSE 写默认走 3.3 的 `sync.close.enabled=true`(close 即同步落 UFS,安全但慢)。writeback 是它的**异步加速替代**:写落到本地 writeback 目录,后台异步上传 UFS。实现:`LocalWriteBackCacheFileSystem`(包装底层 FS)+ `LocalWriteBackOutStream`(写流)+ `UploadManager`(上传/清理调度)。**它按路径规则启用**——`localWriteBackEnabledForPath` 匹配 `PathConfigEntity` 的正则规则(而非一个全局开关),故 writeback 是**路径级**能力。

**写路径与事务模型**(`createFile`):每次 createFile 视为一次 **WORM 事务**——生成 uuid,建 meta 文件(记录事务)、data 文件(内容)、UFS placeholder(标记进行中);client 写 data 文件,close 时置 finishedTs 标记完成,再提交异步上传。任一步失败 `cleanOnFailure` 清全部。

**降级链(核心,createFile 时逐条判断)**:
1. **配额比例**:`mUploader.getSpaceUsedRatio() >= dir.quota.max.usage.ratio`(默认 **0.8**)→ 记日志并 `prepareForSyncWrites`,**降级为同步写**(直接写底层 FS,close 后刷元数据缓存)。
2. **任务积压**:`getUploadTasksNumber() > max.upload.tasks`(默认 **10000**)→ 同样降级同步写。⚠️ 该值是单进程内的软上限。
3. **正在上传冲突**:若 `allow.overwrite.uploading.files=false`(默认 true)且同路径有在途上传任务 → **抛 `IllegalStateException`** 拒绝覆盖(防后写被先写覆盖)。默认允许覆盖。
4. **空间不足(写入过程中)**(`LocalWriteBackOutStream.writeInternal`):`mUploadManager.allocate()` 失败(超 `dir.quota`)时,`degraded.sync.write.on.insufficient.space`=false(默认)→ **抛 IOException**;=true → `switchToSyncWrites()`(关本地流、等在途上传、改直写 UFS)。
- **`write.back.dir`(默认无)**:writeback 本地暂存目录;**未配则 writeback 不可用**。`write.back.dir.quota`(默认 `0`=无限)配额上限;`max.usage.ratio`(0.8)是降级阈值。
- **`write.back.buffer.size`(默认 1MiB)**:writeback 内存缓冲(`LocalWriteBackOutStream` 的 `BUFFER_SIZE`,配合软限缓冲池)。
- **`write.back.max.acceleration.threads`(默认 16)**:本地写加速线程池(`write-back-acceleration`,弹性线程池,所有 writeback 写共享),配合大小为 `threads+1` 的缓冲队列减少 GC。
- **`write.back.sync.flush.empty.file`(默认 true)**:检测到写的是**空文件**时,同步在 UFS 直接创建(`createEmptyUfsFile`),不走异步上传流水线。
- **`write.back.status.bloom.filter.enabled`(默认 false)+ `.refresh.period`(默认 5min)**:用**布隆过滤器**加速"文件是否存在"判定(`BloomFilterAbsenceStatusChecker`),对**大量小文件写**场景把 getStatus/list 的负判定本地化,减少 RPC;开启后 create/rename/createDirectory/list 都会 `putPath` 更新过滤器。
- **异步删除(async delete)**:`write.cache.async.delete.enabled`(默认 true)把删除/覆盖 inode 的 **page store 清理**移到后台执行,不阻塞 delete/rename 热路径;`.thread.count`(默认 8)线程数;`.max.pending.file.count`(默认 128K)与 `.max.pending.file.size`(默认 8GiB)是待清理队列上限,**满则降级为同步清理**(阻塞删除,防积压耗尽本地空间)。
- **`write.cache.defer.open.file.attr.update.enabled`(默认 false)**:对**已开写缓存文件**的 chmod/chown/utimens,延迟到可搭已有写缓存元数据提交的顺风车时再合并——减少单独的元数据往返。
- ⚠️ **丢失窗口**:writeback 在异步上传完成前,数据仅在**本地 writeback 目录**;节点/进程崩溃虽可从本地目录 `recoveryFromLocalDir` 恢复重传,但本地盘同时损坏则丢失。上传失败重试 5 次后进 `UPLOAD_FAILED` 目录**需人工介入**。关键 checkpoint 需权衡是否用 `sync.close`。

### 3.6 随机写流(POSIX 随机写支持)—— 三套实现

对象存储不支持随机写(只能整对象 PUT),但 POSIX 应用会 `seek`+`write`、`truncate`。FUSE 用"下载到本地临时文件 → 本地随机改 → close 时整体回传 UFS"适配。三套实现按能力递进:

- **`force.random.access.write.stream.enabled`(默认 true)**:写文件时**总是**用 `RandomAccessFuseFileStream`(否则仅对已存在文件用,见下)。
- **`random.access.file.stream.enabled`(默认 false)**:对**已存在文件**的写用随机写流。
- **`RandomAccessFuseFileStream` 机制**(已翻证):`initTmpFile` 把 UFS 文件下载到 `File.createTempFile` 本地临时文件(下载后立即 `delete` 但保留打开的 fd,进程退出自动回收),之后所有 read/write/truncate 走本地 `RandomAccessFile`;`close`/`fsync` 时 `copyFromTmpFile` 整体回传 UFS。**仅当有实际写或非零 truncate 时才回传**(纯读打开不回传)。
  - `random.access.file.stream.buffer.size`(默认 4MiB):下载/回传的拷贝缓冲。
  - `random.access.file.stream.atomic.write.enabled`(默认 true):回传用 `setIsAtomicWrite`——**异常时不破坏原文件**(先写临时对象再原子切换)。
  - `random.access.file.stream.truncate.immediately.enabled`(默认 false):`truncate(0)` 时**立即**在 UFS 建空文件(而非等 close)——为兼容 pandas `to_parquet` 等先 truncate(0) 再写的用法。
  - ⚠️ 大文件小改动代价高:`checkIfUfsFileTooLarge`(>1GB)会 WARN,因为要整文件下载+整文件回传。
- **`read.write.random.access.stream.enabled`(默认 false)+ `.compatible.flush.enabled`(默认 true)**:`ReadWriteRandomAccessStream` 支持**同一文件同时读写**(顺序读+随机写),对顺序读性能更好;`compatible.flush` 让 flush/fsync 在底层流支持时调其 flush(兼容处理)。
- **`local.backed.stream.enabled`(默认 false)+ `.buffer.size`(4MiB)/`.tmp.dir`(`/tmp/alluxio-fuse-local-backed-stream`)/`.tmp.dir.capacity`(1GB)**:用**多路复用读写随机流**服务 FUSE 读写,旨在**替代旧的随机写流**;临时目录及容量限制本地盘用量。⚠️ `tmp.dir` 默认在 `/tmp`,生产应改大容量持久盘。

### 3.7 非中断迁移(K8s 平滑升级)

- **`non.disruptive.migration.enabled`(默认 false)**:升级 FUSE pod 时,**旧 pod 把打开文件状态存盘、新 pod 接管挂载而不中断应用 IO**——K8s 滚动升级 FUSE 不断流的关键。**代码机制**(`AlluxioFuseMigrationRestHandler` + `AlluxioLibfuseUserDataHandler`):FUSE Web 端点 `/api/.../fuse/migration` 收到 POST(带 `apiVersion=v1.0`、新 pod `uuid`)→ 用 CAS 把迁移状态从 `NOT_TRIGGERED` 置 `MIGRATING`(拒绝重复触发,返回 403)→ 清理 domain socket → 后台线程 `triggerMigrationCallback` 交接文件描述符 → 置 `FINISHED`。GET 端点返回当前迁移状态/pid/outbound uuid 供编排查询。
- **`non.disruptive.migration.state.file.directory.path`(默认 `/tmp`)**:保存/恢复迁移状态文件的**本地目录**。⚠️ **K8s 下必须新旧 FUSE pod 都能访问**(共享卷 / hostPath),否则新 pod 读不到状态,迁移失败。
- **`migration.ongoing.request.grace_period`(默认 `5s`)**:迁移前给在途请求的**收尾宽限**;超时的请求被强制中止。
- **`request.hard.timeout`(默认 `-1`=关)+ `return.timeout.error.on.request.hard.timeout`(默认 true,别名 `non.disruptive.migration.return.timeout.error.on.timeout`)**:`>0` 时 FUSE 请求到点**立即失败**;返回 true=回超时错误码(用户看到明确错误,但**可能触发应用意外重试**),false=其它处理。`callWithMigrationInterruptCheck` 在每个 FUSE op 外层统一检查迁移/超时中断。
- **`open.file.reference.creation.wait.previous.close.timeout`(默认 `120s`)**:同一路径上一个 close 仍在进行时,创建打开文件引用的等待超时(open 文件注册表并发控制)。

### 3.8 内存工作区元存储 与 分布式 POSIX 锁(需 V2 FDB 后端)

- **内存工作区元存储**(`in.memory.workspace.metastore.*`,均带别名 `in.memory.fdb.metastore.*`,当元存储实现为 `InMemoryFdbMetastore` 时生效):
  - `inode.quota`(默认 100万):单个内存工作区元存储实例的 inode 数配额。
  - `logical.size.quota`(默认 10GB):逻辑文件长度配额。
  - `state.persist.interval`(默认 5min):**定期把内存元存储状态持久化**到 UFS 的固定间隔。
  - `state.ufs.path`(默认 `/tmp/fs_snapshot`):状态恢复/持久化的 UFS 路径——重启时从此路径恢复,故 `/tmp` 生产应改持久位置。
  - 用于多工作区(`MULTI_WORKSPACE_GENERIC`,见 19 组 3.2)在内存里管元数据、UFS 作 page store 的形态。
- **`<FUSE_POSIX_LOCK_ENABLED>`(默认 false,模板名,一致性 WARN)**:启用 FUSE V2 的**分布式 POSIX 锁**(flock/fcntl)。**硬前置**:`alluxio.write.cache.dual.buffer.file.system.type` 必须为 `GENERIC_FDB_BACKED_V2`(见 19 组 3.2——否则代码直接抛 `IllegalArgumentException`)。**代码机制**:`AlluxioJniFuseFileSystemV2` 在 `FUSE_POSIX_LOCK_ENABLED=true` 时用 `FdbMetastoreImpl.getInstance()` 建锁管理器,每挂载一个 UUID 的 `FuseLockHandler` 把锁操作落 **FoundationDB**——故锁状态**跨节点/跨 FUSE 实例可见**,支持多客户端并发写同文件的 POSIX 锁语义。

### 3.9 调试与其它

- **`debug.enabled`(默认 false)**:FUSE debug 模式,记录每个 FS 请求(排障用,量大)。
- **`logging.threshold`(默认 `10s`)**:某个 FUSE API 调用耗时超此阈值就打日志——定位慢调用(慢 UFS/慢 RPC)的低成本手段。
- **`read.write.lock.manager.try.lock.timeout`(默认 `20s`,ALL,一致性 WARN)**:FUSE 读写锁管理器 tryLock 超时——随机写流/POSIX 锁获取文件锁的等待上限。
- **`path.based.config.file.path`(默认无)**:指定一个文件,从中加载**基于路径的 FUSE 配置**(按路径前缀差异化配置,如某目录启用 writeback、另一目录不启用)。

---

## 4. 配置关联关系图

```mermaid
flowchart TD
    MO[mount.options attr/entry_timeout=600] --> KC[内核缓存stat/lookup 600s<br/>快但外部改动看不到]
    OSC[open.read.status.cache 1s] --> KC
    XATTR[intercept.system.xattr.get=true] --> LESSRPC[探针xattr本地回ENODATA<br/>省无谓RPC]
    WRITE{FUSE 写} -->|默认 sync.close=true| SYNC[close即同步UFS 安全]
    WRITE -->|按路径规则 writeback| WB[本地dir缓冲→异步上传]
    WB --> D1{ratio≥0.8?}
    WB --> D2{tasks>10000?}
    WB --> D3{写中 allocate 失败?}
    D1 -->|是| SYNCW[降级同步写 prepareForSyncWrites]
    D2 -->|是| SYNCW
    D3 -->|degraded.sync=true| SYNCW
    D3 -->|degraded.sync=false 默认| ERR[抛 IOException]
    WB -.崩溃.-> REC[从本地目录恢复重传<br/>失败5次→UPLOAD_FAILED 需人工]
    WB -.本地盘同损.-> LOSS[丢失窗口]
    RW[随机写/seek] --> RAS[RandomAccessFuseFileStream<br/>下载→本地改→close回传]
    RAS -.atomic.write=true.-> SAFE[异常不破坏原文件]
    RAS -.>1GB.-> WARN[整文件下载+回传 WARN]
    LOCK[FUSE_POSIX_LOCK_ENABLED] -->|需 V2 GENERIC_FDB_BACKED_V2| FDBLK[锁落FDB 跨节点可见]
    MIG[non.disruptive.migration] --> CAS[CAS NOT_TRIGGERED→MIGRATING]
    CAS --> STATE[state.dir 新旧pod共享卷] --> K8S[滚动升级不断流]
    UGT[user.group.translation ENFORCE] --> POSIXOWNER[ls -l 真实owner]
```

---

## 5. 典型场景配置组合建议

| 场景 | 推荐组合 | 理由 |
|---|---|---|
| **AI 训练只读(高性能)** | 保持大 `attr/entry_timeout`、`open.read.status.cache.enabled=true`、`intercept.system.xattr.get.enabled=true`(默认)、`enforce.direct.io.read=true` | 最大化元数据/内核缓存命中,拦截探针 xattr 省 RPC,direct io 避免双缓存 |
| **大目录列举** | `enable.read.dir.plus=true`(默认)+ 增大 `read.dir.plus.batch.size`、按内存调 `dir.stream.cache.size` | readdirplus 一次带回属性,减内核往返 |
| **需强新鲜度** | 调小 `mount.options` 的 attr/entry_timeout、`open.read.status.cache.enabled=false` | 外部改动更快可见(牺牲缓存命中) |
| **训练 checkpoint 写(吞吐优先)** | `write.back.dir`=持久盘 + `dir.quota` + `dir.quota.max.usage.ratio`、按内存调 `max.acceleration.threads`;小文件多再开 `status.bloom.filter.enabled` | writeback 异步上传;布隆过滤加速小文件存在性判定 |
| **checkpoint 写(安全优先)** | 保持 `sync.close.enabled=true`(默认)、不启 writeback | close 即落 UFS,无丢失窗口 |
| **随机写/pandas to_parquet** | `random.access.file.stream.enabled=true` + `atomic.write.enabled=true`(默认)+ `truncate.immediately.enabled=true` | 下载-改-回传,原子写不破坏原文件,truncate(0) 立即建空文件 |
| **边写边读流水线** | `read.write.random.access.stream.enabled=true` + `read.on.incomplete.file.enabled=true` | 同文件同时读写 |
| **多客户端并发写同文件(需锁)** | `FUSE_POSIX_LOCK_ENABLED=true` + `dual.buffer.file.system.type=GENERIC_FDB_BACKED_V2`(19 组) | 分布式 POSIX 锁,锁状态落 FDB |
| **POSIX 权限正确** | `user.group.translation.enabled=true` + `authorization.user.cache.*` | ls -l 显示真实 owner,缓存摊薄翻译开销 |
| **对象存储写(避免 .fuse_hidden 垃圾)** | `silly.rename.interceptor.enabled=true` | 拦截 silly rename,不在 UFS 留隐藏对象 |
| **K8s 滚动升级不断流** | `non.disruptive.migration.enabled=true` + `state.file.directory.path`=新旧 pod 共享卷 + 合理 `grace_period` | FUSE 升级平滑接管 |
| **优雅卸载** | `umount.timeout`>0 | SIGTERM 后等在途 IO,避免硬中断 |

---

## 6. 风险与注意事项

1. **`attr/entry_timeout=600` 的陈旧窗口**:内核缓存 stat/lookup 长达 10 分钟,外部对 UFS 的改动在窗口内 FUSE 不可见;强一致/频繁外部改动场景必调小(牺牲缓存命中)。
2. **writeback 数据丢失窗口**:异步上传完成前数据仅在本地 writeback 目录;进程/节点崩溃可从本地目录 `recoveryFromLocalDir` 恢复重传,但**本地盘同时损坏则丢失**;上传重试 5 次仍失败会进 `UPLOAD_FAILED` 目录**需人工介入**。关键 checkpoint 权衡是否改用 `sync.close`。
3. **writeback 是路径级、依赖本地目录**:`write.back.dir` 未配则 writeback 不可用;启用范围由 `PathConfigEntity` 正则规则(可经 `path.based.config.file.path`)决定,不是单一全局开关。生产 `write.back.dir` 应指向持久大盘而非 `/tmp`。
4. **降级到同步写的隐性行为**:配额比例达 0.8 或在途任务超 10000 会**静默降级为同步写**(仅 debug 日志),表现为写变慢但不报错;`degraded.sync.write.on.insufficient.space=false`(默认)则空间不足时**直接抛 IOException**。上线前压测确认预期行为。
5. **随机写对象存储代价**:大文件小改动=整文件下载+整文件回传(>1GB 会 WARN);评估是否真需随机写,或改用位置写/追加。`local.backed.stream.tmp.dir`/随机写临时文件默认在 `/tmp`,注意容量。
6. **POSIX 锁硬依赖 V2 + FDB**:`FUSE_POSIX_LOCK_ENABLED=true` 时 `dual.buffer.file.system.type` 必须为 `GENERIC_FDB_BACKED_V2`(19 组),否则启动即抛 `IllegalArgumentException`;锁状态落 FoundationDB,需 FDB 高可用。
7. **迁移状态目录可达性**:K8s 下 `non.disruptive.migration.state.file.directory.path` 必须新旧 pod 都能访问(共享卷/hostPath),否则新 pod 读不到状态,迁移失败;`state.ufs.path`(内存工作区元存储)与其默认都在 `/tmp`,生产改持久位置。
8. **`request.hard.timeout` 的重试副作用**:开启且 `return.timeout.error.on.request.hard.timeout=true` 时,超时返回错误码可能触发**应用意外重试**;评估应用对错误码的处理再开。
9. **`special.command.enabled` 的安全含义**:开启后可通过 `ls -l .../.alluxiocli.*` 下发运维命令,默认关;仅在受控环境按需开。
10. **`user.group.translation.enabled` 是 ENFORCE**:需全集群/全挂载一致,否则元数据展示不一致。
11. **别名(8)**:`worker.fuse.*`→`fuse.*`(旧版 worker 内嵌 FUSE)、`in.memory.fdb.metastore.*`→`in.memory.workspace.metastore.*`、`non.disruptive.migration.return.timeout.error.on.timeout`→`return.timeout.error.on.request.hard.timeout` 等。

---

## 跨组关联速览
- [01-client-fs-io](01-client-fs-io.md) —— 读写类型/位置读(FUSE 底层复用)
- [02-client-cache](02-client-cache.md) —— 客户端本地缓存(FUSE 进程内)
- [04-worker-page-store](04-worker-page-store.md) —— 写缓存 page store(writeback 落点)
- [14-membership-etcd](14-membership-etcd.md) —— 集群级 FUSE 限流令牌
- [17-security](17-security.md) —— 认证体系(FUSE auth policy 之上)

---

## 附录A:本组全量配置清单(脚本生成)

> 由 `_data/gen_table.py 16-fuse` 生成,逐 key 一行,保证覆盖本组**全部 82 项**(与上文按子场景组织的中文速查表互补;此处描述为官方英文原文,便于精确检索)。

| 配置项 | 默认值 | 类型 | Scope | 一致性 | 状态 | 说明 |
|---|---|---|---|---|---|---|
| `<unresolved:FUSE_POSIX_LOCK_ENABLED>` | false | — | ALL | WARN | — | Whether to enable distributed POSIX locks in FUSE V2. Requires alluxio.write.cache.dual.buffer.file.system.type to be GENERIC_FDB_BACKED_V2. |
| `<unresolved:FUSE_V2_ENABLED>` | false | — | ALL | WARN | — | — |
| `alluxio.fuse.auth.policy.class` | "alluxio.fuse.auth.LaunchUserGroupAuthPolicy" | class | CLIENT | IGNORE | — | The fuse auth policy class. Valid options include: `alluxio.fuse.auth.LaunchUserGroupAuthPolicy` using the user launching the AlluxioFuse applicati... |
| `alluxio.fuse.auth.policy.custom.group` | — | string | CLIENT | IGNORE | — | The fuse group name for custom auth policy. Only valid if the is alluxio.fuse.auth.CustomAuthPolicy |
| `alluxio.fuse.auth.policy.custom.user` | — | string | CLIENT | IGNORE | — | The fuse user name for custom auth policy. Only valid if the is alluxio.fuse.auth.CustomAuthPolicy |
| `alluxio.fuse.authorization.user.cache.expiration.time` | "1h" | duration | CLIENT | IGNORE | — | The expiration time for the cached user authorization info in FUSE. |
| `alluxio.fuse.authorization.user.cache.max.size` | 10000 | int | CLIENT | IGNORE | — | The maximum number of users to cache authorization info for in FUSE. |
| `alluxio.fuse.authorization.user.group.translation.enabled` | false | boolean | CLIENT | IGNORE | — | Whether to enable user/group translation in FUSE authorization. |
| `alluxio.fuse.authorizer.classname` | "alluxio.fuse.auth.CustomPolicyAuthorizer" | class | CLIENT | — | — | The class name of the authorizer used for FUSE authorization |
| `alluxio.fuse.cached.paths.max` | 500 | int | CLIENT | IGNORE | — | Maximum number of FUSE-to-Alluxio path mappings to cache for FUSE conversion. |
| `alluxio.fuse.debug.enabled` | false | boolean | CLIENT | IGNORE | — | Run FUSE in debug mode, and have the fuse process log every FS request. |
| `alluxio.fuse.dir.stream.cache.size` | 100_000 | int | CLIENT | IGNORE | — | Number of child entries cached during a directory listing |
| `alluxio.fuse.enable.read.dir.plus` | true | boolean | CLIENT | — | — | If enabled, the fuse will read dir by offset. |
| `alluxio.fuse.enforce.direct.io.read` | false | boolean | CLIENT | — | — | If enabled, fuse will enforce the direct io mode for read only files. |
| `alluxio.fuse.fast.copy.enabled` | false | boolean | CLIENT | — | — | If enabled, ignore chmod and chown for fast copying. |
| `alluxio.fuse.fs.name` | "alluxio-fuse" | string | CLIENT | IGNORE | — | The FUSE file system name. |
| `alluxio.fuse.in.memory.workspace.metastore.inode.quota` | 1_000_000L | long | CLIENT | IGNORE | 别名:alluxio.fuse.in.memory.fdb.metastore.inode.quota | The inode count quota enforced per in-memory workspace metastore instance. |
| `alluxio.fuse.in.memory.workspace.metastore.logical.size.quota` | "10GB" | dataSize | CLIENT | IGNORE | 别名:alluxio.fuse.in.memory.fdb.metastore.logical.size.quota | The logical file length quota enforced per in-memory workspace metastore instance. |
| `alluxio.fuse.in.memory.workspace.metastore.state.persist.interval` | "5min" | duration | CLIENT | IGNORE | 别名:alluxio.fuse.in.memory.fdb.metastore.state.persist.interval | The fixed-rate interval for periodically persisting the in-memory workspace metastore state to . |
| `alluxio.fuse.in.memory.workspace.metastore.state.ufs.path` | "/tmp/fs_snapshot" | string | CLIENT | IGNORE | 别名:alluxio.fuse.in.memory.fdb.metastore.state.ufs.path | The UFS path used to restore and persist the in-memory workspace metastore state for FUSE when the metastore implementation is InMemoryFdbMetastore... |
| `alluxio.fuse.list.timeout` | "0s" | duration | CLIENT | IGNORE | — | The timeout to wait for list dir. A value smaller than or equal to zero means wait for readdir until finished. |
| `alluxio.fuse.local.backed.stream.buffer.size` | 1024 * 1024 * 4 | int | CLIENT | IGNORE | — | This buffer size is used in FuseLocalBackedStream when copying the UFS file to local and copying the local file to UFS. |
| `alluxio.fuse.local.backed.stream.enabled` | false | boolean | CLIENT | — | — | If enabled, FUSE will use multiplex read/write random access stream to serve FUSE read/write requests. This feature aims to replace the legacy and ... |
| `alluxio.fuse.local.backed.stream.tmp.dir` | "/tmp/alluxio-fuse-local-backed-stream" | string | CLIENT | — | — | The local temporary directory for FUSE local backed stream. |
| `alluxio.fuse.local.backed.stream.tmp.dir.capacity` | "1GB" | dataSize | CLIENT | — | — | The maximum disk usage for FUSE local backed stream. |
| `alluxio.fuse.logging.threshold` | "10s" | duration | CLIENT | IGNORE | — | Logging a FUSE API call when it takes more time than the threshold. |
| `alluxio.fuse.low.level.active.inode.attr.cache.ttl` | "0ms" | duration | CLIENT | IGNORE | — | The maximum age of a retained low-level active inode snapshot that can be returned directly from the low-level FUSE active inode table without refr... |
| `alluxio.fuse.max.reader.concurrency` | 1024 | int | ALL | WARN | — | Max number of concurrent readers per file in FUSE |
| `alluxio.fuse.migration.ongoing.request.grace_period` | "5s" | duration | CLIENT | — | — | The grace period for ongoing requests before migration. Timed out requests will be aborted forcefully. |
| `alluxio.fuse.mount.alluxio.path` | "/" | string | ALL | WARN | 别名:alluxio.worker.fuse.mount.alluxio.path | The Alluxio path to mount to the given Fuse mount point configured by %s. |
| `alluxio.fuse.mount.options` | "attr_timeout=600,entry_timeout=600" | list | ALL | WARN | 别名:alluxio.worker.fuse.mount.options | The platform specific Fuse mount options to mount the given Fuse mount point. If multiple mount options are provided, separate them with comma. |
| `alluxio.fuse.mount.point` | "/mnt/alluxio-fuse" | string | ALL | WARN | 别名:alluxio.worker.fuse.mount.point | The absolute local filesystem path that mount Alluxio path to. |
| `alluxio.fuse.non.disruptive.migration.enabled` | false | boolean | CLIENT | — | — | Whether enable fuse non-disruptive migration. |
| `alluxio.fuse.non.disruptive.migration.state.file.directory.path` | "/tmp" | string | CLIENT | — | — | The local directory path for save/restore fuse migration state files. If we are in k8s env, make sure both of new fuse pod and old fuse can access ... |
| `alluxio.fuse.open.file.reference.creation.wait.previous.close.timeout` | "120s" | duration | CLIENT | — | — | Timeout for creating open file reference in the open file registry, when there is a previous close operation on the same file path in progress. |
| `alluxio.fuse.open.read.status.cache.enabled` | false | boolean | CLIENT | — | — | If enabled, caches file metadata (URIStatus) for 1 second to avoid repeated getStatus RPCs when the same read-only file is opened frequently. Only ... |
| `alluxio.fuse.pre.allocate.all.async.prefetch.buffers.enabled` | format("${%s}", Name.USER_POSITION_READER_STREAMING_ASYNC_PREFETCH_SHARED_CACHE_ENABLED) | boolean | CLIENT | IGNORE | — | Whether to pre-allocate all available memory. |
| `alluxio.fuse.read.dir.plus.batch.size` | 12 | int | CLIENT | — | — | the batch size of read dir by offset. |
| `alluxio.fuse.read.write.lock.manager.try.lock.timeout` | "20s" | duration | ALL | WARN | — | Timeout for read write lockmanager trylock operation. |
| `alluxio.fuse.request.hard.timeout` | -1 | duration | CLIENT | IGNORE | — | If enabled, FUSE requests will be failed immediately when the timeout is reached. Only takes effect if the timeout is > 0 |
| `alluxio.fuse.return.timeout.error.on.request.hard.timeout` | true | boolean | CLIENT | — | 别名:alluxio.fuse.non.disruptive.migration.return.timeout.error.on.timeout | Whether return timeout error code on timeout. This provides the user a more explicit error but may cause unexpected application retry behavior. |
| `alluxio.fuse.silly.rename.interceptor.enabled` | false | boolean | CLIENT | — | — | Manually manages the 'silly rename' behavior in FUSE. By enabling this, Alluxio intercepts rename requests that would create '.fuse_hidden' files. ... |
| `alluxio.fuse.special.command.enabled` | false | boolean | CLIENT | — | — | If enabled, user can issue special FUSE commands by using 'ls -l /path/to/fuse_mount/.alluxiocli.<command_name>.<subcommand_name>', For example, wh... |
| `alluxio.fuse.umount.timeout` | "0s" | duration | CLIENT | IGNORE | — | The timeout to wait for all in progress file read and write to finish before unmounting the Fuse filesystem when SIGTERM signal is received. A valu... |
| `alluxio.fuse.use.create.file.options.overwrite.flag` | false | boolean | ALL | — | — | When this configuration is set to true, Fuse will use the overwrite flag in createFileOptions when overwriting files instead of directly deleting t... |
| `alluxio.fuse.user.group.translation.enabled` | false | boolean | CLIENT | ENFORCE | — | Whether to translate Alluxio users and groups into Unix users and groups when exposing Alluxio files through the FUSE API. When this property is se... |
| `alluxio.fuse.web.bind.host` | "0.0.0.0" | string | CLIENT | — | — | The hostname Alluxio FUSE web UI binds to. |
| `alluxio.fuse.web.hostname` | — | string | ALL | — | — | The hostname of Alluxio FUSE web UI. |
| `alluxio.fuse.web.port` | 49999 | int | CLIENT | — | — | The port Alluxio FUSE web UI runs on. |
| `alluxio.user.fuse.cross.quota.domain.return.exdev.enabled` | false | boolean | CLIENT | IGNORE | — | Controls the errno FUSE returns when a rename or hard link is rejected because the source and destination are in different write-cache directory-qu... |
| `alluxio.user.fuse.force.random.access.write.stream.enabled` | true | boolean | CLIENT | IGNORE | — | If enabled, RandomAccessFuseFileStream which support random write operation would be always used when writing file in FUSE. |
| `alluxio.user.fuse.fsync.enabled` | false | boolean | CLIENT | IGNORE | — | [Experimental] If enabled, the fuse fsync operation will be handled, calling the internal alluxio flush implementation. |
| `alluxio.user.fuse.hard.link.fallback.as.copy` | false | boolean | CLIENT | IGNORE | — | If enabled, when creating a hard link in FUSE, the operation will fall back to copying the file instead of returning an error. |
| `alluxio.user.fuse.hard.link.return.exdev.enabled` | false | boolean | CLIENT | IGNORE | — | Enables a workaround for RocksDB versions older than 7.1.1 that do not handle EOPNOTSUPP correctly. When enabled, Alluxio FUSE will return EXDEV in... |
| `alluxio.user.fuse.intercept.system.xattr.get.enabled` | true | boolean | CLIENT | IGNORE | — | If enabled, FUSE getxattr requests for well-known probe xattrs such as security.capability and system.posix_acl_* are answered locally with ENODATA... |
| `alluxio.user.fuse.multipart.upload.enabled` | false | boolean | CLIENT | IGNORE | — | If enabled, when writing a file to UFS by fuse, data will be partitioned into multiple parts and uploaded in parallel. This improves the write perf... |
| `alluxio.user.fuse.path.based.config.file.path` | — | string | CLIENT | IGNORE | — | If specified, alluxio will load path based fuse config from the file. |
| `alluxio.user.fuse.random.access.file.stream.atomic.write.enabled` | true | boolean | CLIENT | IGNORE | — | If enabled, RandomAccessFuseFileStream will use atomic write feature to upload file. |
| `alluxio.user.fuse.random.access.file.stream.buffer.size` | 1024 * 1024 * 4 | int | CLIENT | IGNORE | — | This buffer size is used in RandomAccessFuseFileStream when copying the UFS file to local and copying the local file to UFS. |
| `alluxio.user.fuse.random.access.file.stream.enabled` | false | boolean | CLIENT | IGNORE | — | If enabled, RandomAccessFuseFileStream which support random write operation would be used when writing an existing file in FUSE. |
| `alluxio.user.fuse.random.access.file.stream.truncate.immediately.enabled` | false | boolean | CLIENT | IGNORE | — | If enabled, RandomAccessFuseFileStream will truncate the file to UFS immediately when processing truncate(0) operation. |
| `alluxio.user.fuse.read.on.incomplete.file.enabled` | false | boolean | CLIENT | IGNORE | — | If enabled, fuse allows a file to be read while it is being created by another thread. If either the random write feature or position write feature... |
| `alluxio.user.fuse.read.write.random.access.stream.compatible.flush.enabled` | true | boolean | CLIENT | IGNORE | — | When this configuration is set to true, during a flush or fsync operation, if the underlying stream supports flushing, the stream’s flush method wi... |
| `alluxio.user.fuse.read.write.random.access.stream.enabled` | false | boolean | CLIENT | IGNORE | — | Whether to use ReadWriteRandomAccessStream. This stream supports simultaneous reading and writing, and provides better performance for sequential r... |
| `alluxio.user.fuse.symlink.enabled` | false | boolean | CLIENT | IGNORE | — | Whether enable symlink. |
| `alluxio.user.fuse.sync.close.enabled` | true | boolean | CLIENT | IGNORE | — | If enabled, when closing a file in fuse, the file will be flushed into UFS synchronously, at the cost of degraded performance of following writes a... |
| `alluxio.user.fuse.write.back.allow.overwrite.uploading.files` | true | boolean | CLIENT | WARN | — | This setting is used to configure whether overwriting files currently being uploaded is allowed. If this value is set to false, writeback will thro... |
| `alluxio.user.fuse.write.back.buffer.size` | "1MiB" | dataSize | CLIENT | WARN | — | Memory buffer size for writeback. |
| `alluxio.user.fuse.write.back.degraded.sync.write.on.insufficient.space` | false | boolean | CLIENT | WARN | — | When this configuration is enabled, writeback will degrade to synchronous writing when space is insufficient, instead of throwing an exception dire... |
| `alluxio.user.fuse.write.back.dir` | — | string | CLIENT | IGNORE | — | If specified, this directory is used for holding writeback enabled writes in FUSE. |
| `alluxio.user.fuse.write.back.dir.quota` | "0" | dataSize | CLIENT | WARN | — | Quota for writeback cache directory. Setting values less than or equal to 0 represents no limitation. |
| `alluxio.user.fuse.write.back.dir.quota.max.usage.ratio` | 0.8 | double | CLIENT | WARN | — | The maximum ratio of quota utilized by writeback, exceeding this ratio, new write requests will degrade to regular writes instead of using writeback. |
| `alluxio.user.fuse.write.back.max.acceleration.threads` | 16 | int | CLIENT | WARN | — | The maximum number of threads for local writeback, with all writeback requests sharing these threads. |
| `alluxio.user.fuse.write.back.max.upload.tasks` | 10000 | long | CLIENT | WARN | — | Maximum allowable asynchronous upload tasks for writeback. Exceeding this value will degrade to synchronous upload. Please note that this value is ... |
| `alluxio.user.fuse.write.back.status.bloom.filter.enabled` | false | boolean | CLIENT | WARN | — | Whether using a Bloom filter to filter status, which could improve the performance of writing small files. |
| `alluxio.user.fuse.write.back.status.bloom.filter.refresh.period` | "5min" | duration | CLIENT | WARN | — | Bloom filter refresh period. |
| `alluxio.user.fuse.write.back.sync.flush.empty.file` | true | boolean | CLIENT | WARN | — | If this configuration is set to true, when writeback detects that the file is empty, it will synchronize creation in UFS. |
| `alluxio.user.fuse.write.cache.async.delete.enabled` | true | boolean | CLIENT | IGNORE | — | If enabled, deleted/overwritten inodes are queued for asynchronous page-store cleanup instead of blocking the delete/rename path. |
| `alluxio.user.fuse.write.cache.async.delete.max.pending.file.count` | 128 * 1024 | int | CLIENT | IGNORE | — | Maximum number of inodes that can be queued for asynchronous page-store cleanup. When this limit is reached, new deletes fall back to synchronous c... |
| `alluxio.user.fuse.write.cache.async.delete.max.pending.file.size` | "8GiB" | dataSize | CLIENT | IGNORE | — | Maximum total file size (bytes) of inodes that can be queued for asynchronous page-store cleanup. When this limit is reached, new deletes fall back... |
| `alluxio.user.fuse.write.cache.async.delete.thread.count` | 8 | int | CLIENT | IGNORE | — | Maximum number of threads in the async delete executor pool used to clean up page-store files in the background. |
| `alluxio.user.fuse.write.cache.defer.open.file.attr.update.enabled` | false | boolean | CLIENT | IGNORE | — | If enabled, chmod/chown/utimens on an already-open write-cache file will stay local until they can piggyback on an existing write-cache metadata co... |
