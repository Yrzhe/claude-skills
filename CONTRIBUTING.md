# Contributing Guide / 插件贡献指南

本文档规范了向本仓库添加新 Skill 插件的标准流程。**所有贡献者（包括 AI Agent）必须严格遵循此结构。**

## 目录结构规范

每个插件必须遵循以下目录结构：

```
plugins/<plugin-name>/
├── .claude-plugin/
│   └── plugin.json              # 插件元数据（必须）
└── skills/
    └── <plugin-name>/           # 与插件同名（必须）
        ├── SKILL.md             # Skill 定义文件（必须）
        ├── scripts/             # 脚本目录（可选）
        ├── references/          # 参考文档目录（可选）
        ├── experiences/         # 经验/模式记录（可选）
        ├── setup.sh             # 环境安装脚本（可选）
        ├── requirements.txt     # Python 依赖（可选）
        └── .gitignore           # 忽略规则（可选）
```

**关键规则：**
- `<plugin-name>` 全小写，单词间用 `-` 连接（如 `my-awesome-tool`）
- `plugins/<plugin-name>/skills/<plugin-name>/` — 这两层的名字**必须一致**
- 不要把文件直接放在 `plugins/<plugin-name>/` 根目录下，所有 Skill 内容都在 `skills/<plugin-name>/` 内

---

## 必须文件详解

### 1. `.claude-plugin/plugin.json`

插件注册元数据，Claude Code 插件系统靠它识别插件。

```json
{
  "name": "my-plugin-name",
  "version": "1.0.0",
  "description": "一句话描述插件功能",
  "author": {
    "name": "yrzhe",
    "url": "https://x.com/yrzhe_top"
  },
  "license": "MIT",
  "repository": "https://github.com/yrzhe/claude-skills",
  "keywords": ["关键词1", "关键词2", "关键词3"]
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 是 | 与文件夹名一致 |
| `version` | 是 | 语义化版本号 `x.y.z` |
| `description` | 是 | 简明描述，会展示在 marketplace 中 |
| `author` | 是 | 作者信息 |
| `license` | 是 | 许可证，一般为 `MIT` |
| `repository` | 是 | 仓库地址 |
| `keywords` | 是 | 标签数组，用于搜索和分类 |

### 2. `SKILL.md`

Skill 的核心定义文件，Claude Code 加载 Skill 时读取此文件。

文件开头必须包含 YAML frontmatter：

```yaml
---
name: my-plugin-name
description: 插件功能的完整描述。这段文字决定了 Claude 何时激活此 Skill。
version: 1.0.0
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
  - WebSearch
---
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 是 | 与文件夹名一致 |
| `description` | 是 | 详细描述，Claude 根据此判断何时触发 Skill |
| `version` | 否 | 版本号 |
| `user-invocable` | 否 | 设为 `true` 则用户可通过 `/plugin-name` 手动调用 |
| `allowed-tools` | 否 | 该 Skill 可使用的工具列表 |

frontmatter 之后是 Skill 的正文——即指导 Claude 如何执行任务的 Prompt。

---

## 可选文件说明

| 文件/目录 | 用途 |
|-----------|------|
| `scripts/` | 可执行脚本（Python/Shell 等），Skill 运行时调用 |
| `references/` | 参考文档、API 映射、示例等 |
| `experiences/` | 运行经验记录、站点模式、教训总结 |
| `setup.sh` | 首次使用时的依赖安装脚本 |
| `requirements.txt` | Python 依赖列表 |

---

## 注册到 Marketplace

新插件**必须**同时注册到 `.claude-plugin/marketplace.json` 的 `plugins` 数组中：

```json
{
  "name": "my-plugin-name",
  "source": "./plugins/my-plugin-name",
  "description": "与 plugin.json 中的 description 一致",
  "version": "1.0.0",
  "author": {
    "name": "yrzhe",
    "url": "https://x.com/yrzhe_top"
  },
  "repository": "https://github.com/yrzhe/claude-skills",
  "license": "MIT",
  "tags": ["关键词1", "关键词2"]
}
```

注意：marketplace 中用 `tags`（数组），plugin.json 中用 `keywords`（数组），内容保持一致。

---

## 添加新插件的完整 Checklist

按顺序执行以下步骤：

- [ ] **1. 创建目录结构**
  ```bash
  mkdir -p plugins/<name>/.claude-plugin
  mkdir -p plugins/<name>/skills/<name>
  ```

- [ ] **2. 编写 `SKILL.md`**
  - 放在 `plugins/<name>/skills/<name>/SKILL.md`
  - 包含正确的 YAML frontmatter
  - 正文写清楚 Skill 的使用指导

- [ ] **3. 编写 `plugin.json`**
  - 放在 `plugins/<name>/.claude-plugin/plugin.json`
  - 所有必填字段齐全

- [ ] **4. 添加脚本和参考资料**（如有）
  - 脚本放 `plugins/<name>/skills/<name>/scripts/`
  - 文档放 `plugins/<name>/skills/<name>/references/`

- [ ] **5. 注册到 marketplace.json**
  - 在 `.claude-plugin/marketplace.json` 的 `plugins` 数组末尾添加条目

- [ ] **6. 更新 README.md**
  - 在 `README.md` 的 "Available Plugins" 部分添加新插件介绍

- [ ] **7. 验证结构**
  ```bash
  # 确认关键文件存在
  ls plugins/<name>/.claude-plugin/plugin.json
  ls plugins/<name>/skills/<name>/SKILL.md

  # 确认 JSON 格式正确
  python3 -c "import json; json.load(open('plugins/<name>/.claude-plugin/plugin.json'))"
  python3 -c "import json; json.load(open('.claude-plugin/marketplace.json'))"
  ```

- [ ] **8. 提交并推送**

---

## 常见错误

| 错误 | 后果 | 正确做法 |
|------|------|----------|
| 文件直接放在 `plugins/<name>/` 下 | 无法通过插件系统安装 | 必须放在 `plugins/<name>/skills/<name>/` 下 |
| 缺少 `plugin.json` | 插件系统无法识别 | 必须创建 `.claude-plugin/plugin.json` |
| `name` 不一致 | 安装后 Skill 找不到 | 文件夹名、plugin.json name、SKILL.md name 三者一致 |
| 没注册 marketplace.json | 用户搜不到插件 | 每次添加新插件都要注册 |
| SKILL.md 缺少 frontmatter | Claude 无法正确加载 | 必须以 `---` 开头的 YAML 块 |

---

## 给 AI Agent 的指令

如果你是一个 AI Agent，被要求向本仓库添加新的 Skill 插件，请：

1. **先读本文档**，理解完整规范
2. **严格遵循目录结构**，不要省略任何一层
3. **使用 Checklist** 逐项完成，不要跳步
4. **验证 JSON 格式**，确保 `plugin.json` 和 `marketplace.json` 语法正确
5. **保持命名一致**，`<plugin-name>` 在所有位置完全相同
6. **提交前检查**，运行验证命令确认结构正确
