# agentlog spec v0.5 · 合稿

源：`01-pool-design-v0.md` (Cistern) + `02-adapter-design-v0.md` (Junction)
本文是后续实现阶段的权威 spec。冲突点全部按本稿决议。

## 0. 项目定位

- 一句话：把一个人在多设备、多 agent（Claude Code / Codex / Maestri 节点 / browser-use / 未来其他源）上的活动，按统一 schema 同步进一个 GitHub-backed 共享池。
- 不替换现有 `~/.claude/skills/seed/`。Seed 继续负责单机 tweet 素材合成；agentlog 负责跨设备跨 agent 池。
- **Skill 仓库 ≠ Pool 数据仓库**：
  - Skill：`yrzhe_skill/plugins/agentlog/`（开源、所有用户共享一份代码）
  - Pool：`~/.agent-seeds/`（每个用户一个 private GitHub repo，自带数据）
  - 两个 repo 不嵌套。

---

## 1. 统一 Event Schema（合稿）

### 1.1 决议表（11 个冲突点）

| # | 维度 | 决议 | 出处 / 理由 |
|---|---|---|---|
| 1 | schema_version 值 | `"agentlog.event.v0"` | 用 v0 不用 v1（先发布稳定后再升 v1）；用 event 不用 activity，名字短 |
| 2 | 事件 ID 双轨制 | 顶层 `id`（UUIDv7 / ULID） + 顶层 `source_event_id`（adapter 侧确定性 id） | Cistern 的 `id` 用于 pool 主键 + 时间排序；Junction 的 `source_event_id` 用于 adapter cursor 恢复和重试幂等 |
| 3 | action 结构 | 嵌套 `action.{type, status, label}` | Cistern。status (`completed/blocked/error/in_progress`) 和 label 都有用，pool 查询不会变慢 |
| 4 | action.type 枚举 | 采纳 Junction 的 14 个值 | `session_started/session_completed/user_request/agent_response/tool_call/tool_result/file_changed/command_run/note_created/note_updated/message_sent/browser_step/error/checkpoint` |
| 5 | 时间戳 | 双时间戳 `timestamp` + `ingested_at` | Cistern。同步延迟监测必需 |
| 6 | device_id | **必填**，在 `source.device_id` | Cistern。Pool 分片路径依赖它。CLI 启动时若 `~/.agent-seeds/state/devices/<device_id>.json` 不存在则生成 |
| 7 | artifact 字段名 | `artifact_refs`（复数 array） | Junction 命名更直觉 |
| 8 | payload | 必填顶层 `payload` 对象，可为空 `{}` | Junction。Adapter 输出大量结构化细节，没 payload 信息会丢 |
| 9 | summary 上限 | 240 字符硬上限 | Junction。可量化、易索引 |
| 10 | dedupe | 两层：`source_event_id` (adapter 写入幂等) + `dedupe_key` (pool 读取层兜底) | 兼容两份设计 |
| 11 | 扩展字段位置 | 跨 adapter 已稳定字段放顶层（Cistern：tags/links/metrics/parent_id/thread_id/privacy/raw_ref），adapter 特有字段强制放 `payload` | Cistern |

### 1.2 权威 schema

所有 adapter 必须输出符合下表的 event。snake_case，未知信息用 `null` 或空数组，不省略字段。

| 字段 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `schema_version` | string | Y | 固定 `"agentlog.event.v0"` |
| `id` | string | Y | UUIDv7 或 ULID，pool 主键；永不复用 |
| `source_event_id` | string | Y | adapter 侧稳定 ID（如 `${source_type}:${session_id}:${line_index}`），cursor 恢复与重试幂等 |
| `schema_version` | string | Y | 固定 `"agentlog.event.v0"` |
| `timestamp` | RFC3339 | Y | 事件实际发生时间（带时区） |
| `ingested_at` | RFC3339 | Y | 写入 pool 时间 |
| `actor` | object | Y | `{ id, name, kind: "human"\|"agent"\|"system" }` |
| `source_type` | enum | Y | `claude_code` / `codex` / `maestri` / `browser_use` / `manual` |
| `source` | object | Y | `{ device_id, host?, process_id?, session_id? }` — device_id **必填** |
| `project` | object | Y | `{ name, path?, id?, git_remote?, git_commit? }` — name 至少 `"unknown"` |
| `action` | object | Y | `{ type (enum 见决议 #4), status, label? }` |
| `summary` | string | Y | 单行，≤ 240 字符 |
| `payload` | object | Y | 结构化源细节；adapter 特有字段必须放这里；text_excerpt ≤ 2,000 字符 |
| `artifact_refs` | array | Y | 0+ 个 ref；空数组允许 |
| `session` | object | N | `{ id, title?, cwd? }` |
| `parent_id` | string | N | 时间链/因果链上的前序 event id |
| `thread_id` | string | N | 同一 session 内的对话/任务流 id |
| `tags` | string[] | N | 自由 tag 如 `["fact-check", "maestri"]` |
| `links` | array | N | `[{ type, url }]` |
| `metrics` | object | N | `{ duration_ms, input_tokens, output_tokens, ... }` |
| `privacy` | object | N | `{ level, redacted }` |
| `dedupe_key` | string | N | sha256 复合；不存则 pool 端按规则补算 |
| `raw_ref` | object | N | `{ type, uri }` 指向原始 jsonl 片段 |

### 1.3 artifact_refs[] schema

| 字段 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `kind` | enum | Y | `file` / `url` / `note` / `screenshot` / `terminal` / `repo` / `diff` / `unknown` |
| `uri` | string | Y | 路径、URL、note 名 |
| `storage` | enum | Y | `git` / `external` / `local_only` — pool 用此决定大文件策略（Cistern §大文件） |
| `sha256` | string | N | 入 git 强烈推荐填，便于跨设备校验 |
| `bytes` | int | N | |
| `mime_type` | string | N | |
| `title` | string | N | |
| `metadata` | object | N | `{ line_range, byte_range, git_commit, tool_id, ... }` |

### 1.4 JSON example

```json
{
  "schema_version": "agentlog.event.v0",
  "id": "01HX5Z9NYV8Q8YQ6KMPVR3GW3R",
  "source_event_id": "codex:019df-3a/line-88:response_item",
  "timestamp": "2026-05-12T17:04:31.238+08:00",
  "ingested_at": "2026-05-12T17:04:35.102+08:00",
  "actor": { "id": "codex:local-default", "name": "Codex", "kind": "agent" },
  "source_type": "codex",
  "source": {
    "device_id": "macbook-pro-m3-yrzhe",
    "host": "yrzhe-mbp",
    "process_id": "pid-12345",
    "session_id": "019df-3a"
  },
  "project": {
    "name": "自媒体运营",
    "path": "/Users/renzheyu/.../自媒体运营",
    "git_remote": null,
    "git_commit": null
  },
  "action": { "type": "session_completed", "status": "completed", "label": "recap generated" },
  "summary": "Codex finished a self-media fact-check and wrote sources/codex-fact-check.md.",
  "payload": {
    "duration_ms": 184000,
    "tool_calls": 6,
    "text_excerpt": "Fact-check complete. 5 claims verified, 1 needs source."
  },
  "artifact_refs": [
    {
      "kind": "file",
      "uri": "sessions/2026-05-12/codex/019df-3a/recap.md",
      "storage": "git",
      "sha256": "...",
      "bytes": 12431,
      "mime_type": "text/markdown"
    }
  ],
  "session": { "id": "019df-3a", "cwd": "/Users/renzheyu/.../自媒体运营" },
  "metrics": { "duration_ms": 184000, "input_tokens": 12000, "output_tokens": 2400 }
}
```

---

## 2. Pool 存储（采纳 Cistern）

完整设计见 `01-pool-design-v0.md`。本节只列权威结论：

### 2.1 目录布局

```
~/.agent-seeds/
  README.md
  .gitignore
  .gitattributes              # pool/**/*.jsonl merge=union; *.jsonl text eol=lf
  pool.jsonl                  # 兼容入口；CLI 重建，非主写
  pool/
    dt=YYYY-MM-DD/
      device=<device_id>/
        source=<source_type>/
          shard-NNN.jsonl     # ≤ 64 MB / shard
  sessions/                   # 从现有 seed 迁移目标，按 source/session 归档
  artifacts/
    dt=YYYY-MM-DD/
      <artifact_id>.<ext>
  state/
    devices/<device_id>.json
    sync-state.json
    cursors/                  # adapter cursor files (见 §3)
  indexes/
    daily/YYYY-MM-DD.json
```

### 2.2 写入不变量

- writer 只能 append，不能改历史行
- 单 writer 队列 + atomic append（temp + fsync + rename，或 OS flock）
- 写入后立即单行 JSON parse 校验
- push 前对 touched shard 做 parse 校验
- shard 滚动：≥ 64 MB 切下一个 NNN
- 单行 ≥ 256 KB：正文进 `payload.text_excerpt`，原文写 `artifact_refs[*]` 或 `raw_ref`

### 2.3 GitHub 同步

详见 `01-pool-design-v0.md` §Auto-pull / §Auto-push / §Git 冲突处理。核心：

- pull 频率：启动 / push 前 / recap 前 / 网络恢复 / 后台 5 分钟；debounce 60s；失败指数退避 1m→5m→15m→30m 上限
- push 频率：30s 防抖；50 条或 1MB 立即；session_completed event 立即 flush
- 冲突：分片避免为主；JSONL shard 用 `merge=union` + parse 校验 + 读取层 dedupe 兜底
- 大文件：< 2MB 入 git，> 2MB 写 `storage: external` 或 `storage: local_only`，v0 不启用 LFS

---

## 3. SourceAdapter 接口（采纳 Junction，路径微调）

完整设计见 `02-adapter-design-v0.md`。本节列权威接口签名 + 路径调整。

### 3.1 接口（TypeScript / Python 等价）

```ts
type EventV0 = { /* §1.2 字段 */ };
type AdapterCursor = Record<string, unknown>;

interface SourceAdapter {
  readonly sourceType: EventV0["source_type"];

  loadCursor(): Promise<AdapterCursor>;
  saveCursor(cursor: AdapterCursor): Promise<void>;

  discover(cursor: AdapterCursor): Promise<SourceEvent[]>;
  normalize(event: SourceEvent): Promise<EventV0 | null>;  // null = 被噪音过滤

  pollOnce(): Promise<{ emitted: number; skipped: number; cursor: AdapterCursor }>;
}
```

### 3.2 Cursor 文件路径调整

Junction 原设计：`~/.agent-seeds/adapter-state/{source_type}.json`
**v0.5 改为**：`~/.agent-seeds/state/cursors/{source_type}.json`（统一所有运行时状态在 `state/` 下）

### 3.3 4 个 adapter

各 adapter 的源路径、cursor 字段、mapping、noise filter、push 频率 → 直接采纳 `02-adapter-design-v0.md` §ClaudeCodeAdapter / §CodexAdapter / §MaestriAdapter / §BrowserUseAdapter，**未做改动**。

实施时注意：
- ClaudeCodeAdapter 读 `~/.claude/projects/*/*.jsonl` 时，应只读不写（不与现有 seed Stop hook 冲突）
- CodexAdapter archive backfill 改为显式 `agentlog backfill --source codex` 触发（**修改 Junction 原 hourly 默认**），避免不必要扫描

### 3.4 Project attribution waterfall（Junction）

1. 显式 cwd/session/project 字段
2. 日志根 / 终端 cwd / note 标题语境的路径
3. cwd 最近的 git repo root
4. 配置的 fallback project name
5. `project.name = "unknown"`, `payload.project_source = "unknown"`

### 3.5 Privacy & redaction

- env 全量 dump 禁存
- 字段名为 `token / key / secret / code / password` 的 URL query 值 / 表单值 redact
- 文件 / note 全文走 `artifact_refs`，不 inline
- 命令输出 ≤ 4,000 字符 + `truncated: true`

---

## 4. `pool.append()` 接口（新增）

Adapter 通过此接口写入。Pool writer 负责落盘 + sharding。

### 4.1 签名（Python 草案）

```python
class Pool:
    def append(
        self,
        event: dict,                      # §1.2 EventV0 dict
        *,
        flush: bool = False,              # True = 立即写盘 + sync push; False = 走 debounce
    ) -> AppendResult:
        ...

@dataclass
class AppendResult:
    ok: bool
    event_id: str                          # echo 的 id（pool 可能补 dedupe_key）
    shard_path: Path                       # 落盘路径
    duplicate: bool                        # True 表示按 source_event_id 已存在
    error: Optional[str] = None
```

### 4.2 行为约定

- 同步：函数返回时 event 已落盘（fsync 完成），但 GitHub push 是异步的
- `flush=True`：触发立即 push (session_completed 等关键事件用)
- 失败处理：append 失败抛异常，**adapter cursor 必须不前进**（Junction §Failure behavior 已规定）
- 幂等：相同 `source_event_id` 二次 append 返回 `duplicate=True`，shard 不重复写
- 必填字段缺失：raise `EventValidationError`，事件被写入 `state/quarantine/YYYY-MM-DD.jsonl` 而非主 pool

---

## 5. CLI 命令面（新增）

工具名：`agentlog`。安装即获得（pip / brew / 单文件 python 自带，二选一在实现阶段定）。

### 5.1 一级命令

| 命令 | 说明 |
|---|---|
| `agentlog init [--repo URL]` | 初始化本机：生成 device_id，clone 用户 pool repo 到 `~/.agent-seeds/`，写 config。无 `--repo` 则提示用 `gh repo create` 新建 |
| `agentlog status` | 显示：device_id / 本机 cursor 进度 / 上次 push 时间 / sync 健康 / 各 adapter 是否就绪 |
| `agentlog sync` | `pull` + `push` 一次（手动触发） |
| `agentlog pull` | 仅拉远端 |
| `agentlog push [--force]` | 仅推本地；`--force` 跳过 debounce |
| `agentlog poll [--source X] [--once]` | 跑一次/一直跑 adapter 轮询；不带 `--source` 跑所有启用的 adapter |
| `agentlog daemon` | 后台守护进程：周期 poll + auto-sync。用于一直挂着的设备 |
| `agentlog pool [--last 4h] [--by agent\|project\|source] [--source X] [--project Y]` | 看 merged 流水，支持维度切换 |
| `agentlog recap [--date YYYY-MM-DD] [--by ...]` | 当日跨源 recap；引擎兼容现 seed `/seed recap` 输出格式 |
| `agentlog shot [URL\|--window]` | 截图绑定到当前 session（直接复用 seed/shot.py 逻辑，目标改 `~/.agent-seeds/artifacts/`） |
| `agentlog backfill --source codex [--from DATE]` | 显式触发 Codex archive / 历史数据回填 |
| `agentlog migrate-from-seed [--dry-run]` | 把现有 `~/.claude/skills/seed/state/sessions/` 导入到 agentlog pool 作为 source=`claude_code_seed` |
| `agentlog event push <json>` | 手动 push 一条 event（脚本 / 第三方 agent 用） |
| `agentlog config get\|set <key> [value]` | 编辑 config（启用/禁用 adapter、设 polling 间隔等） |

### 5.2 设计原则

- 所有 CLI 子命令必须能在 VPS 上跑（不能依赖 macOS only API）。`shot` 是唯一例外（macOS only）
- 输出默认 stdout，`--json` 切到机器可读
- daemon 用 systemd / launchd / `pm2` / 用户自选；CLI 提供 `agentlog daemon install` 帮你装一份默认 launchd plist

---

## 6. SKILL.md 大纲（新增）

`yrzhe_skill/plugins/agentlog/SKILL.md` 草稿大纲：

```markdown
---
name: agentlog
description: Load when the user wants to view, sync, or analyze multi-agent multi-device activity from a shared pool — including Claude Code / Codex / Maestri / browser-use sessions across multiple machines. Triggers on: "what did I do today across all my agents", "agentlog recap", "show me my pool", "sync the pool", "multi-device agent log". Do NOT load for single-machine tweet material capture (use seed) or for one-off project planning.
---

# agentlog · multi-agent multi-device activity pool

(开篇 2-3 句话定位 + 不与 seed 重叠的边界声明)

## 当用户说什么时触发

- "agentlog X" 命令
- "今天我在所有 agent 上做了什么"
- "跨设备的 X" / "把 vps 上那个也拉一下"
- "多 agent 池" / "shared pool"

## 不在范围

- 单机 Twitter 素材捕获 → seed
- 一次性项目规划 → planner / brainstorming

## 架构（一图流）

(贴一张文字 ASCII 图说明 skill ↔ pool repo ↔ adapter ↔ device)

## 安装与初始化

详见 `references/setup.md`。简版：
1. `pip install agentlog` 或 `brew install agentlog`
2. `agentlog init --repo git@github.com:USER/agent-seeds.git`
3. （可选）`agentlog daemon install`

## 常用流程

### 看今天所有 agent 干了啥
`agentlog recap`

### 切到按项目看
`agentlog recap --by project`

### 把 vps 上跑过的也拉下来
`agentlog pull`

### 看最近 4 小时实时流水
`agentlog pool --last 4h`

### 从某条手动 push 一条
`agentlog event push '{"action":{"type":"checkpoint"...}}'`

## Reference 索引

- `references/setup.md` — 完整安装与多设备配置
- `references/schema-v0.md` — Event schema 字段完整定义
- `references/adapters/<source>.md` — 各 adapter 配置与扩展
- `references/cli-reference.md` — 所有 CLI 命令
- `references/troubleshooting.md` — git 同步冲突、cursor 损坏、adapter 故障

## 升级路径

详见 `references/upgrade-from-seed.md`。一句话：agentlog 不替换 seed。运行 `agentlog migrate-from-seed --dry-run` 可一次性把历史 seed 数据并入 agentlog pool（保留 seed 原状态）。
```

---

## 7. 升级路径（新增）

### 7.1 与现有 seed 共存

| 维度 | seed | agentlog |
|---|---|---|
| 数据落点 | `~/.claude/skills/seed/state/sessions/` | `~/.agent-seeds/pool/` |
| 触发 | Stop hook（被动） | poll / event push（主动）|
| 主用 | 单机 tweet 素材 | 跨设备 multi-agent 池 |
| 现状 | 不动 | 新加 |

### 7.2 一次性迁移命令

`agentlog migrate-from-seed [--dry-run]`：

1. 扫 `~/.claude/skills/seed/state/sessions/*.md`
2. 每条 turn 转成 EventV0：
   - `source_type = "claude_code_seed"`（与活的 ClaudeCodeAdapter `source_type=claude_code` 区分，避免双源采集）
   - `actor = { kind: "agent", name: "Claude Code" }`
   - `action.type` 按 turn 内容映射
   - `source_event_id = "seed:<session_id>:<turn_index>"`
3. 写入 `~/.agent-seeds/pool/dt=<date>/device=<device>/source=claude_code_seed/shard-NNN.jsonl`
4. `--dry-run` 仅打印计划

### 7.3 seed Stop hook 是否要改？

**v0.5 不改**。seed Stop hook 继续只写 seed 自己的 sessions 目录。agentlog 的 ClaudeCodeAdapter 直接读 `~/.claude/projects/*/*.jsonl`（更稳定的源），不依赖 seed hook。

v1+ 可考虑：seed Stop hook 顺手 `agentlog event push`，让 agentlog 实时拿到，但这是可选优化，不阻塞 v0。

---

## 8. 仓库脚手架（实施第一步）

`yrzhe_skill/plugins/agentlog/` 目标结构：

```
agentlog/
  SKILL.md                        # 见 §6
  README.md                       # 用户视角说明 (开源 readme)
  .claude-plugin/
    plugin.json
  scripts/
    agentlog                      # CLI 入口（python -m）
    setup_pool.py                 # init 用
    migrate_from_seed.py
  src/agentlog/                   # 实现代码
    __init__.py
    cli.py
    pool.py                       # pool.append() + sharding + git
    schema.py                     # EventV0 + 验证
    adapters/
      base.py                     # SourceAdapter ABC
      claude_code.py
      codex.py
      maestri.py
      browser_use.py
    recap.py                      # cross-source 日报
    sync.py                       # github push/pull/debounce
  references/
    setup.md
    schema-v0.md
    cli-reference.md
    adapters/
      claude-code.md
      codex.md
      maestri.md
      browser-use.md
    troubleshooting.md
    upgrade-from-seed.md
  docs/
    design/                       # 当前目录（设计稿）
  tests/
    test_schema.py
    test_pool.py
    test_adapter_claude_code.py
    ...
```

---

## 9. OPEN 项（v1 处理）

- Maestri stable event/source API（替换 hash diff scraping）
- BrowserUse 活动 session 自动发现 API（v0 由 config 提供 ids）
- 是否支持非 GitHub sync 后端（私有 git server / Radicle / Syncthing）
- Pool 端跨设备视图缓存（indexes/daily/*.json 自动维护策略）
- v1 webhook：agent 出新 event 可被订阅（dashboard / 推流）
- 团队版（多用户共享 pool）— 现 v0 是个人多设备版

---

## 10. 待 Claude Code（总管）继续

合稿完成后下一步：

1. **scaffold yrzhe_skill/plugins/agentlog/ 文件结构**（§8）
2. **写 SKILL.md v0**（§6）
3. **写 schema.py + pool.py 原型**（§1, §2, §4）
4. **写 ClaudeCodeAdapter 原型**（§3.3，最简单的源，验证管道）
5. **写 `agentlog init` + `agentlog poll --once --source claude_code`**（端到端最小可跑）
6. yrzhe 在本机试一次，成功后再扩 Codex / Maestri / BrowserUse adapter

各步骤可再分发给 Codex agents 并行实现。
