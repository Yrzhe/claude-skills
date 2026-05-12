# agentlog-pool-design

## 范围

Pool Architect 只定义两块：

1. pool 存储格式：append-only JSONL schema、扩展字段、分片策略、ID 防重。
2. GitHub 同步策略：`~/.agent-seeds/` repo 的 auto-pull、auto-push、并发 append 冲突、大文件资产处理。

不定义 source adapter 接口、CLI 命令面、SKILL.md 写法。

## 目录布局

推荐布局：

```text
~/.agent-seeds/
  README.md
  .gitignore
  pool.jsonl                  # 兼容入口；只保留最近 7 天索引或软迁移说明
  pool/
    dt=2026-05-12/
      device=<device_id>/
        source=<source_type>/
          shard-000.jsonl
    dt=2026-05-13/
      ...
  sessions/                   # 现有 seed session 迁移目标，保持原始 session 资产
  artifacts/
    dt=2026-05-12/
      <artifact_id>.<ext>
  state/
    devices/<device_id>.json
    sync-state.json
  indexes/
    daily/2026-05-12.json
```

推荐：真实写入使用 `pool/dt=.../device=.../source=.../shard-000.jsonl`，根目录 `pool.jsonl` 作为兼容入口，不作为长期主写文件。

理由：spec 写了“pool 主文件：append-only `pool.jsonl`”，但多设备并发写同一个文件会把冲突集中到单点。按天 + device + source 分片后，绝大多数 append 不会触碰同一文件；`pool.jsonl` 保留给早期工具和人类入口，后续可由 CLI 汇总生成最近窗口。

OPEN：如果总管坚持字面单文件 `pool.jsonl`，则同步策略必须切换为更频繁 rebase + union merge driver，复杂度和冲突率都会上升。

## JSONL 记录模型

每行一个完整 JSON object，UTF-8，无尾随逗号，append-only。单行必须可独立解析；禁止跨行 JSON。

### 必备字段

```json
{
  "schema_version": "agentlog.event.v1",
  "id": "01HX...",
  "timestamp": "2026-05-12T17:04:31.238+08:00",
  "ingested_at": "2026-05-12T17:04:35.102+08:00",
  "actor": {
    "type": "agent",
    "name": "Codex",
    "id": "codex:local-default"
  },
  "source_type": "codex",
  "source": {
    "device_id": "macbook-pro-m3-yrzhe",
    "host": "yrzhe-mbp",
    "process_id": "pid-12345",
    "session_id": "019df..."
  },
  "project": {
    "name": "自媒体运营",
    "path": "/Users/renzheyu/Library/CloudStorage/GoogleDrive-qq1514337391@gmail.com/My Drive/自媒体运营",
    "git_remote": null,
    "git_commit": null
  },
  "action": {
    "type": "session_stop",
    "status": "completed",
    "label": "recap generated"
  },
  "artifact_ref": [
    {
      "type": "file",
      "uri": "sessions/2026-05-12/codex/019df.../recap.md",
      "sha256": "...",
      "bytes": 12431
    }
  ],
  "summary": "Codex finished a self-media fact-check and wrote sources/codex-fact-check.md."
}
```

### 字段定义

| 字段 | 类型 | 规则 | 理由 |
|---|---:|---|---|
| `schema_version` | string | 必填，固定 `agentlog.event.v1` | 允许未来 v2 并行读取。 |
| `id` | string | 必填，ULID 或 UUIDv7 | 时间有序，跨设备生成无需中心服务。 |
| `timestamp` | RFC3339 string | 必填，事件发生时间，保留时区 | 支持按真实工作时间回放。 |
| `ingested_at` | RFC3339 string | 必填，写入 pool 时间 | 区分事件时间和同步延迟。 |
| `actor` | object | 必填，执行者身份 | 跨 agent 汇总时不能只靠 source_type。 |
| `source_type` | enum string | 必填，如 `claude_code` / `codex` / `maestri` / `browser_use` / `manual` | 支持 adapter 路由和过滤。 |
| `source` | object | 必填，设备、host、session、process 信息 | 定位日志来源和排查重复写入。 |
| `project` | object | 必填，可部分为空 | 支持按项目聚合，不强依赖 git。 |
| `action` | object | 必填，事件类型、状态、人类短标签 | 避免 summary 承担结构化过滤职责。 |
| `artifact_ref` | array | 必填，可为空数组 | 统一表达截图、recap、diff、外链。 |
| `summary` | string | 必填，1-5 句纯文本 | 直接服务日报和搜索。 |

推荐：字段名使用 snake_case；必备字段永远存在，未知信息用 `null` 或空数组，不省略。

理由：稳定字段让 recap 和搜索逻辑简单；`null` 比缺字段更容易做兼容检查。

## 扩展字段

可选字段放顶层，保留以下命名：

```json
{
  "tags": ["fact-check", "maestri"],
  "links": [
    { "type": "github_pr", "url": "https://github.com/..." }
  ],
  "metrics": {
    "duration_ms": 184000,
    "input_tokens": 12000,
    "output_tokens": 2400
  },
  "privacy": {
    "level": "private",
    "redacted": false
  },
  "parent_id": "01HX...",
  "thread_id": "019df...",
  "dedupe_key": "sha256:...",
  "raw_ref": {
    "type": "file",
    "uri": "sessions/.../raw.jsonl"
  },
  "extra": {
    "adapter_specific": true
  }
}
```

推荐：adapter 特有字段只能放 `extra`；跨 adapter 已稳定的字段才提升到顶层。

理由：防止第一版 schema 被单个来源污染，同时保留低成本扩展。

## ID 和去重

推荐 ID：UUIDv7 或 ULID，由本地设备生成。

推荐 dedupe_key：

```text
sha256(source_type + "
" + source.device_id + "
" + source.session_id + "
" + action.type + "
" + timestamp + "
" + normalized_summary)
```

规则：

- `id` 用于事件身份；永不复用。
- `dedupe_key` 用于发现同一 adapter 重试造成的重复写入。
- 同一 `dedupe_key` 出现多次时，读取层保留 `ingested_at` 最早的一条，后续重复行不删除。
- 同一 `id` 出现内容不同，标记为 corrupt duplicate，读取层只接受第一条，并在 sync diagnostic 输出告警。

理由：append-only 不做原地删除；去重放读取层不会引入跨设备写锁。

## 分片策略

推荐分片路径：

```text
pool/dt=YYYY-MM-DD/device=<device_id>/source=<source_type>/shard-NNN.jsonl
```

滚动规则：

- 首选按本地 `timestamp` 日期分区。
- 单个 shard 超过 64 MB 时滚到下一个 `shard-NNN.jsonl`。
- 单行超过 256 KB 时，正文缩短进 `summary`，原始内容写入 `artifact_ref` 或 `raw_ref`。
- 每次 append 只打开当前 device/source/day 的最后一个 shard。

理由：按天便于日报和人工检查；按 device/source 避免多设备同时写同一文件；64 MB 对 git diff、merge、GitHub web 查看仍可接受。

OPEN：日志量极大时，按小时分片可作为 v2 选项，但 v0 不启用，避免目录过碎。

## pool.jsonl 兼容策略

推荐：根目录 `pool.jsonl` 不承载全量长期数据，只作为兼容窗口：

- v0 可写入一行注释不可行，因为 JSONL 不支持注释；因此 `pool.jsonl` 保持合法 JSONL。
- CLI 可把最近 7 天事件汇总 append 或重建到 `pool.jsonl`，供简单工具读取。
- 权威数据在 `pool/` 分片目录。

理由：既满足“主文件”心智模型，又不把所有冲突压到一个文件。

OPEN：是否允许 `pool.jsonl` 由工具重建而非 append-only，需要总管在 CLI 设计里定；如果严格 append-only，则它只能作为早期过渡写入目标。

## GitHub 同步模型

repo：`~/.agent-seeds/` 是用户私有 pool repo。每台设备 clone 同一个 GitHub repo。

推荐同步原则：

1. 写本地优先：agent 结束时先 append 本地 JSONL，不等网络。
2. pull 先于 push：任何 push 前必须 fetch + rebase/merge 远端。
3. 分片避冲突：正常情况下不同设备写不同路径，不依赖复杂 merge。
4. append-only：冲突处理只能保留行，不能丢行。

理由：agent 活动记录不能因为网络失败阻塞；GitHub 只做异步同步层。

## Auto-pull 策略

触发时机：

| 时机 | 推荐 | 理由 |
|---|---|---|
| daemon/CLI 启动 | 立即 pull 一次 | 让本机先看到其他设备最新 pool。 |
| 写入前 | 不强制 pull | 写入本地分片不需要远端最新状态，降低延迟。 |
| push 前 | 必须 pull --rebase | 避免非快进 push。 |
| 空闲后台 | 每 5 分钟 pull 一次 | 多设备使用时延迟可接受，不会太吵。 |
| 用户手动 recap 前 | pull 一次 | 日报需要尽量完整。 |
| 网络恢复后 | 立即 pull 一次 | 快速收敛离线期间的远端变化。 |

推荐：auto-pull 使用 debounce，最短间隔 60 秒；连续失败采用 1m / 5m / 15m 指数退避，上限 30m。

理由：GitHub 同步是协作后台动作，过高频率会制造锁冲突和电量消耗。

## Auto-push 策略

触发时机：

| 时机 | 推荐 | 理由 |
|---|---|---|
| 每次事件 append 后 | 标记 dirty，不立刻 push | agent 高频事件会造成提交噪音。 |
| dirty 后防抖 | 30 秒无新事件则 push | 保持接近实时，又能合并 burst。 |
| 累计事件数 | 50 条立即 push | 长 session 不等太久。 |
| 累计字节数 | 1 MB 立即 push | 大量日志及时上传。 |
| session stop | 立即 flush push | session 结束是最重要同步点。 |
| 关机/进程退出 | best-effort push | 降低本地未同步窗口。 |

推荐 commit message：

```text
append pool events: <device_id> <YYYY-MM-DD> <count>
```

推荐：每台设备用本地文件锁保护 `git` 操作，例如 `state/sync.lock` 或 OS flock；同一设备内多个 agent 写入由 append writer 排队。

理由：批量 push 控制 repo 历史噪音；本地锁避免同一机器多个 hook 同时 git commit。

## Git 冲突处理

推荐正常路径：按 `device_id/source_type/date` 分片，避免不同设备写同一 JSONL 文件。

当仍发生冲突：

1. 先执行 `git fetch origin`。
2. 对本地提交执行 `git rebase origin/main`。
3. 如果冲突文件是 JSONL shard：使用 union merge 保留双方新增行。
4. rebase 后运行 JSONL 校验：逐行 parse、按 `id` 检查重复、按 `dedupe_key` 标记重复。
5. 校验通过后 push；校验失败则 abort rebase，保留本地分支并输出人工修复路径。

推荐 `.gitattributes`：

```gitattributes
pool/**/*.jsonl merge=union
*.jsonl text eol=lf
```

推荐 git config：

```bash
git config merge.union.driver true
```

理由：append-only JSONL 的冲突语义是“双方新增行都保留”；union merge 符合日志池模型。分片设计让这个路径只处理少数异常。

OPEN：union merge 可能重复保留同一行；读取层 dedupe 必须上线，不能只靠 git merge。

## 大文件资产策略

资产类型：截图、附件、长 transcript、原始 session json、生成文件快照。

推荐分层：

| 类型 | v0 存储 | 理由 |
|---|---|---|
| 小文本 artifact <= 256 KB | 入 repo，放 `sessions/` 或 `artifacts/` | 可 diff、可搜索、日报可引用。 |
| 图片/截图 <= 2 MB | 入 repo，放 `artifacts/dt=.../` | v0 简单可靠，不强依赖外部服务。 |
| 二进制或图片 > 2 MB | 不入普通 git；记录外链或本地路径 | 避免 repo 快速膨胀。 |
| 长原始日志 > 1 MB | gzip 后可选入 repo，或只保留摘要 | 保持 pool 可 clone。 |
| 敏感文件 | 默认不入库，只写 redacted summary | pool repo 即使私有也不能默认收集敏感资产。 |

推荐：v0 不启用 Git LFS 作为默认路径。

理由：Git LFS 增加安装、认证、迁移复杂度；agentlog v0 需要开源可装、VPS 可用。先用大小阈值 + 外链/本地路径，后续再给重度用户开启 LFS profile。

artifact_ref 推荐格式：

```json
{
  "type": "image",
  "uri": "artifacts/dt=2026-05-12/01HX....png",
  "sha256": "...",
  "bytes": 481203,
  "mime": "image/png",
  "storage": "git"
}
```

外链格式：

```json
{
  "type": "image",
  "uri": "https://...",
  "sha256": null,
  "bytes": null,
  "mime": "image/png",
  "storage": "external"
}
```

本地跳过格式：

```json
{
  "type": "image",
  "uri": "file:///Users/.../screenshot.png",
  "sha256": "...",
  "bytes": 8931244,
  "mime": "image/png",
  "storage": "local_only",
  "note": "skipped: exceeds v0 git asset limit"
}
```

## 读写不变量

- writer 只能 append 新行，不能修改历史行。
- 每行写入使用 temp file + fsync + atomic append 或单 writer 队列，避免半行。
- 写入后立即做单行 JSON parse 校验。
- push 前做 touched shard parse 校验。
- recap 前做全量或按日期 parse 校验。
- 读取层按 `timestamp` 排序，`ingested_at` 只用于同 timestamp tie-break。

理由：JSONL 一旦出现半行，会破坏后续读取；校验点必须靠近写入和同步。

## v0 推荐结论

1. 权威 pool 使用 `pool/dt=YYYY-MM-DD/device=<device_id>/source=<source_type>/shard-NNN.jsonl` 分片；`pool.jsonl` 保留兼容入口。
2. event schema 固定 11 个必备字段：`schema_version/id/timestamp/ingested_at/actor/source_type/source/project/action/artifact_ref/summary`。
3. ID 使用 UUIDv7 或 ULID；重复处理用 `dedupe_key`，读取层保留最早写入。
4. auto-pull：启动、push 前、recap 前、网络恢复、后台 5 分钟。
5. auto-push：30 秒防抖、50 条/1 MB 阈值、session stop 立即 flush。
6. 并发冲突主要靠分片避免；异常 JSONL 冲突用 union merge + parse/dedupe 校验。
7. 大文件 v0 默认不启用 Git LFS；小文本和小图入 git，大文件写 external/local_only artifact_ref。

## 交给总管的接口约束

- CLI 写入时必须知道 `device_id`，不存在时生成并保存到 `state/devices/<device_id>.json`。
- CLI recap 读取时必须扫描 `pool/` 分片，而不是只读根目录 `pool.jsonl`。
- CLI sync 必须实现本地 git 锁、push 前 pull/rebase、JSONL parse 校验。
- Adapter 只产出 event object；最终落盘路径由 pool writer 根据 `timestamp/device_id/source_type` 决定。
