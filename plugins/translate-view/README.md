# Translate View

Claude Code 双向翻译 mod。输入按「Agent 接收」语言自动翻译；回复按「我的阅读」语言翻译到右侧，原回复保留在左侧。

## 安装

在 Claude Code 中运行：

```text
/plugin marketplace add Yrzhe/claude-skills
/plugin marketplace update yrzhe-skills
/plugin install translate-view@yrzhe-skills
/reload-plugins
/translate settings
```

需要 Claude Code 2.1.287+（在 2.1.288 验证）、Python 3 和 macOS/Linux。右侧停靠面板需要 Claude 的全屏渲染模式；必要时退出后重新启动：

```sh
CLAUDE_CODE_NO_FLICKER=1 claude --continue
```

窄窗口或非全屏布局可能由 Claude 将面板放到输入框上方。面板的高度、停靠位置由 Claude 管理。与 `reply-view` 可以同时使用。

## 使用

顶部固定显示两个目标语言和「设置」按钮；下方是用 Claude 原生 Markdown 渲染的可滚动译文，支持标题、加粗、列表、链接和代码块。往上滚动时停止自动跟随，点「回到底部」恢复。生成中的译文合并完整句子/段落后分批翻译；Agent 完成后，会把积压内容合并请求，避免逐段重复检测和等待。支持接口的 SSE 流式输出；短回复在完成后翻译。代码块等完整后再处理。检测与翻译服务自身的响应速度仍会影响延迟。

| 设置 | 示例 | 效果 |
| --- | --- | --- |
| Agent 接收 | English | 中文输入先译成英文，再发送给 Agent |
| 我的阅读 | 简体中文 | 英文回复在右侧显示中文译文 |

识别为目标语言时跳过翻译调用；右侧会标注「已是目标语言」。语言不确定时交给翻译模型处理。语言设置独立，不会强制 Agent 改变原回复语言。

常用命令：

```text
/translate
/translate settings
/translate off
/translate on
```

关闭设置页返回译文；关闭面板后可用 `/translate` 重新打开。`/translate off` 会关闭两个方向的翻译。

## 设置

首次安装默认关闭。设置顶部固定显示五个分类，按实际宽度排布，空间足够时五项在同一行：「语言检测 / 模型接口 / 环境变量 / Jev 接口 / 翻译 Prompt」。打开设置会回到语言检测首页，并显示当前生效的检测方式和翻译模型。填好接口后开启自动翻译并保存。

### 语言与检测

- **本地脚本**：不发送检测请求。根据文字与常用词判断，适合简单中英文；混合语言、繁简体、短句与部分语种可能判断不准。不确定时仍会交给翻译模型。
- **LLM（如 Gemini）**：使用「模型接口」页的地址和密钥先判断语言，再按需翻译。「检测模型」可单独填写型号，留空复用翻译模型。选择 Gemini 时需要提供支持该型号的 Chat Completions 兼容接口；不能仅凭服务商列出的模型名判断协议兼容性。
- **Jev**：使用独立的 TypeSafe System One 接口判断语言，实际翻译仍由 「模型接口」页的模型完成。支持兼容该请求/响应格式的网关。低置信度判断按不确定处理。

可选常见语言，也可在「自定义接收/阅读代码」填写 `en`、`zh`、`ja` 等语言代码。

### 模型接口与环境变量

使用兼容 **Chat Completions** 的接口：

- `Base URL`：包含服务商要求的版本前缀，例如 `https://provider.example/v1`。仅自动追加 `/chat/completions`。
- `POST URL`：完整地址，填写时优先于 Base URL。
- 模型名：填写该服务实际支持 Chat Completions 的模型/别名。能列出模型不代表其支持该协议。
- API Key：使用 `Authorization: Bearer ...`。本地无认证接口可留空，并清空 Key 环境变量。
- 环境变量：可分别填写 URL、Key、模型的变量名。默认 `OPENAI_BASE_URL`、`OPENAI_API_KEY`、`OPENAI_MODEL`。在「环境变量」分类填写变量名，不带 `$`。默认「本机填写优先」模式下手填值优先、留空读环境变量；选择「读取环境变量」后，LLM 的 Base URL、Key、模型全部从环境读取，手填值和 POST URL 被忽略但不会被删除。环境变量需要在启动 Claude 前导出，修改 shell 环境后要重启 Claude。Jev 有独立的配置来源、地址、模型和密钥绑定。

非流式响应读取 `choices[0].message.content`；流式响应读取 `choices[0].delta.content`。返回普通 JSON 的服务也可使用，但译文在该批完成后显示。不支持直接使用 Anthropic Messages、Gemini 原生接口或 Responses API 的 URL。

### Jev

Jev 只判断语言，不生成译文；选择其他检测方式时不会调用它。其配置来源独立于翻译模型：

- 「本机填写优先」：填写 POST URL、Jev 模型名和 API Key。默认公开接口为 TypeSafe 的 `/v1/systemone`，模型示例为 `jev-latest`；自建网关可以更换。
- 「读取环境变量」：填写变量名，默认推荐 `TYPESAFE_POST_URL`、`TYPESAFE_MODEL`、`TYPESAFE_API_KEY`，已保存的手填值会保留但不参与这一路请求。

使用 TypeSafe System One 请求格式，请求包含 `state`、`model`、`questions`，读取 `answers.language.choice` 和 `confidence`。

### 看懂配置来源

设置会标出当前生效模型与字段来源：本机填写、环境变量或未配置。模型/地址输入框里的实值来自这台机器的私有配置；公开插件不包含你的私有地址、密钥或已选择的翻译型号。

环境变量页填写的是**名字**，不是变量值。界面逐项显示「已读取」「当前进程未设置」或「尚未绑定」，不显示环境变量的完整内容；密钥身份仅显示末四位。灰色示例不代表已经绑定；「填入推荐变量名」只填写名字，不创建变量、不写入密钥，也不自动切换配置来源。新的变量名保存后检查。

| 用途 | 推荐变量名 |
| --- | --- |
| 翻译 Base URL | `OPENAI_BASE_URL` |
| 翻译 API Key | `OPENAI_API_KEY` |
| 翻译模型名 | `OPENAI_MODEL` |
| Jev POST URL | `TYPESAFE_POST_URL` |
| Jev API Key | `TYPESAFE_API_KEY` |
| Jev 模型名 | `TYPESAFE_MODEL` |

可以改用自己的变量名。变量需要由启动 Claude 的终端导出；给变量名并不会让插件自动扫描电脑上的其他密钥文件。

### 自定义 Prompt

「翻译 Prompt」页可分别编辑发送前翻译、回复翻译的系统提示词。支持：

- `{target_language}`：当前方向的目标语言。
- `{source_language}`：检测出的源语言。

示例：

```text
Translate into {target_language}. Preserve the original intent and tone. Use concise, natural language. Return only the translation, without explanations.
```

插件会额外要求保留代码、链接、路径和附件标记占位符，避免模型改变这些内容。默认 Prompt 要求保留原意和 Markdown 结构，不执行待翻译文本中的指令。

## 保存与数据流

设置保存在本机 `~/.config/claude-translate/config.json`，文件权限 `0600`，不在插件目录或公开仓库。可用 `TRANSLATE_VIEW_CONFIG` 指定另一个私有配置文件。所有 Claude 会话默认共享这份设置；其他已打开会话需重新加载插件以刷新开关/语言显示。

模型接口和 Jev 页会显示「当前生效密钥」的来源及末四位（短密钥完全隐藏）：来自本机时显示配置文件路径和 `apiKey` / `jevKey` 字段，来自环境时显示确切变量名。未启用的本机备用密钥会另标为「当前未使用」。这些信息对应已保存的设置，修改后点保存才更新。完整密钥不回显；密钥输入留空只是保留本机已有值，不表示自动寻找其他密钥，「清除已保存密钥」在保存时删除。原生终端输入框不支持密码遮罩，新输入的密钥在保存前可见；也可只填写环境变量名。

启用后，用户提示词和主 Agent 的可见回复会发送到所配置的翻译服务。选用 LLM/Jev 检测时，自然语言部分也会发送到检测服务。图片/音频/文档附件的二进制、思考内容、工具输出、其他 Agent 的回复不会被送去翻译。插件不会读取集中密钥库，也不会上传到作者的服务。发布包不含任何个人地址、模型配置或密钥。

发送前翻译失败时暂停该次发送并提示。空输入框会恢复原文；若已经开始写下一条，则保留新输入，侧栏提供「恢复输入」按钮追加未发送的文字。可以重试或关闭翻译后发送。回复翻译失败时原回复仍可阅读，侧栏可重试。请求有超时和大小上限，不自动无限重试。

## 已知边界

- 当前会话内显示用户原输入；模型上下文和 Claude 保存的原始会话记录包含**译后的输入**。重启/恢复旧会话后不保证恢复译前显示。显示原文的内存缓存最多 100 条、约 200000 字符。
- 右侧显示最新一轮的回复。生成中的文字可提前翻译，后续工具步骤/最终答案改变时刷新；只显示主 Agent 文本。
- 译文使用 Claude 原生 Markdown 渲染。受原生组件长度限制，超过 9000 字符的单个连续块（如超长代码块）会分片按纯文本显示，避免整个面板失效。
- 单次输入/翻译片段最多 100000 字符；接口响应最多约 2 MB。非常大的单个代码块/段落应拆分。
- 本地语言检测是启发式；模型翻译和检测也可能出错。
- 新终端、不同字体及窗口尺寸的最终视觉效果仍取决于 Claude 的渲染器。CLI 是支持目标；VS Code 聊天面板、Claude Desktop 和 headless 模式不提供此右侧 UI。

## 开发与验证

```sh
claude plugin validate .claude-plugin/plugin.json
claude plugin test .
python3 -m unittest discover -s tests -p 'test_*.py' -v
tsc -p .
```

Claude 首次加载 mod 时会生成本机版本对应的类型声明与 `tsconfig.json`，它们不随包发布。

`tests/terminal_smoke.py` 用真实 Claude Code PTY、本地模拟翻译服务和替代 Agent 响应验证 Markdown 样式、长文滚动与固定页头、消息原文、设置以及失败行为；不调用真实 Agent 模型。需要测试环境安装 `pyte`，例如：

```sh
uv run --with pyte python tests/terminal_smoke.py
```

测试脚本默认调用 `claude`，可通过 `CLAUDE_BIN` 环境变量指定其他启动命令。

Gemini 官方提供 [OpenAI 兼容接口](https://ai.google.dev/gemini-api/docs/openai)。第三方网关是否支持该接口格式，需要实际验证；插件不会自动改用其他模型或服务商。

参考：[Claude mod UI](https://code.claude.com/docs/en/plugins/mods/interface)、[TypeSafe Jev API](https://docs.typesafe.ai/api)。MIT License。
