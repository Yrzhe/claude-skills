---
name: feishu-bot-dev
description: 飞书机器人开发完整指南。支持三种模式：1) 零代码（机器人助手）- 可视化搭建自动化流程；2) 全代码（开放平台API）- 完整API能力；3) AI集成（MCP Server）- AI Agent与飞书协作。包含最新SDK、消息卡片搭建工具、最佳实践。
version: 2.0.0
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - WebFetch
  - Task
  - mcp__plugin_playwright_playwright__browser_navigate
  - mcp__plugin_playwright_playwright__browser_snapshot
  - mcp__plugin_playwright_playwright__browser_click
  - mcp__plugin_playwright_playwright__browser_type
---

# 飞书机器人开发完整指南

飞书机器人开发全栈指南，支持零代码、全代码、AI集成三种模式。

---

## 开发模式选择

| 模式 | 适用场景 | 技术要求 | 入口 |
|------|----------|----------|------|
| **飞书机器人助手** | 定时提醒、消息推送、自动化流程 | 无需编程 | [botbuilder.feishu.cn](https://botbuilder.feishu.cn/home) |
| **飞书开放平台 API** | 复杂业务逻辑、系统深度集成 | 需要编程 | [open.feishu.cn](https://open.feishu.cn/) |
| **MCP Server 集成** | AI Agent 协作、智能助手 | 需要编程 | [MCP 文档](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/mcp_integration/mcp_introduction) |

## 开发者工具箱

| 工具 | 用途 | 链接 |
|------|------|------|
| **消息卡片搭建工具** | 可视化设计卡片消息，告别手写JSON | [Card Builder](https://open.feishu.cn/tool/cardbuilder) |
| **API Explorer** | 在线调试API，一键生成代码 | [API Explorer](https://open.feishu.cn/api-explorer) |
| **AI Playground** | 自然语言生成代码 | [AI Playground](https://open.feishu.cn/app/ai/playground) |
| **opdev CLI** | 命令行开发工具 | `npm i -g @anthropic/opdev` |

---

# 第一部分：飞书机器人助手（零代码）

## 一、快速入门

### 1.1 创建机器人应用

1. 访问 [飞书机器人助手](https://botbuilder.feishu.cn/home)
2. 点击 **+ 新建机器人应用**
3. 填写：
   - **应用名称**：如"值班通知机器人"
   - **应用描述**：说明机器人用途
   - **应用图标**：支持默认或自定义

### 1.2 使用模板快速搭建

系统提供多种预设模板：

| 模板类型 | 典型场景 |
|----------|----------|
| 消息助手 | 行政通知、财务通知 |
| 群智能助手 | 入群欢迎、自动回复 |
| 新人入职 | 入职引导、信息收集 |
| 定时提醒 | 周报填写、任务催办 |
| 值班通知 | 排班提醒、签到管理 |
| 数据推送 | 系统告警、数据同步 |

### 1.3 核心概念

**触发器**：流程的起点，定义何时启动
- 定时任务：按设定时间触发
- 工作表变化：数据变动时触发
- Webhook：外部系统调用触发
- 新员工入职：人事变动触发
- @机器人消息：群内互动触发

**操作节点**：触发后执行的动作
- 发送飞书消息
- 创建飞书群/文档
- 查找/新增/修改多维表格记录
- 发送 HTTP 请求

---

## 二、流程设计

### 2.1 触发器类型详解

#### 系统内置触发器

| 触发器 | 说明 | 示例场景 |
|--------|------|----------|
| 定时任务 | 按时间和频率触发 | 每天9点发送周报提醒 |
| 工作表变化 | 新增/修改/删除记录 | 新员工入职自动欢迎 |
| 机器人会话首次创建 | 用户首次打开机器人 | 发送使用指南 |
| 单聊机器人消息 | 用户私聊关键词触发 | 关键词自助查询 |
| @机器人群聊消息 | 群内@机器人触发 | 问题反馈汇总 |

#### 飞书集成触发器

| 触发器 | 说明 |
|--------|------|
| 新员工入职 | 账号激活或入职特定部门 |
| 多维表格内容变更 | 满足条件的记录变更 |
| 用户进群 | 用户加入指定群组 |
| 收到新审批 | 审批状态变更 |

#### 应用连接器触发器

| 触发器 | 说明 |
|--------|------|
| Webhook 触发 | 接收外部 HTTP 请求 |
| GitLab 事件 | commit/MR/Issue 变动 |
| Sentry 事件 | 新错误产生 |
| Grafana 告警 | 监控报警触发 |
| Gmail 新邮件 | 收到新邮件时触发 |

### 2.2 操作节点配置

#### 发送飞书消息

```markdown
## 消息内容支持的格式

| 样式 | 语法 | 效果 |
|------|------|------|
| 加粗 | `**文字**` | **粗体** |
| 斜体 | `*文字*` | *斜体* |
| 删除线 | `~~文字~~` | ~~删除线~~ |
| 颜色 | `<font color='green'>文字</font>` | 绿色文字 |
| @指定人 | `<at id=open_id></at>` | @用户名 |
| @所有人 | `<at user_id="all"></at>` | @所有人 |
| 超链接 | `[文字](https://url)` | 可点击链接 |
```

**注意事项**：
- 发送到群组时，需确保群设置允许"所有群成员"发言
- @所有人需要群管理员权限
- 超链接必须包含协议头 (https/http)

#### Webhook 配置

```bash
# 测试 Webhook (macOS)
curl -X POST -H "Content-Type: application/json" \
 -d '{"msg_type":"text","content":{"id":"1","name":"Tom"}}' \
 [Webhook地址]

# 测试 Webhook (Windows)
curl -X POST -H "Content-Type: application/json" \
 -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"test\"}}" \
 [Webhook地址]
```

---

## 三、发布与管理

### 3.1 应用发布流程

1. 完成流程设计后点击 **发布**
2. 填写 **审核备注**（说明申请权限的理由）
3. 配置 **可用范围**（确定谁能接收消息）
4. 提交审核，等待管理员通过

### 3.2 权限管理

- **应用权限**：系统自动添加所需权限
- **可用范围**：部门数量无上限，人员上限 1000
- **所有权转移**：支持主动转移或离职自动转移

### 3.3 常见问题

| 问题 | 解决方案 |
|------|----------|
| 无法接收消息 | 检查是否在应用可用范围内 |
| 流程运行失败 | 查看运行日志排查原因 |
| 群组发送失败 | 确保群设置允许所有成员发言 |

---

# 第二部分：飞书开放平台 API（全代码）

## 一、开发准备

### 1.1 创建应用

1. 访问 [开发者后台](https://open.feishu.cn/app/)
2. 点击 **创建自建应用**
3. 获取凭证：
   - **App ID**：应用唯一标识
   - **App Secret**：应用密钥（妥善保管）

### 1.2 获取访问凭证

飞书 API 支持两种访问凭证：

| 凭证类型 | 适用场景 | 获取方式 |
|----------|----------|----------|
| `tenant_access_token` | 应用身份调用 API | App ID + App Secret |
| `user_access_token` | 用户身份调用 API | OAuth 2.0 授权 |

#### 获取 tenant_access_token

```python
import requests

def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    """获取 tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    response = requests.post(url, json=payload)
    data = response.json()

    if data.get("code") == 0:
        return data["tenant_access_token"]
    else:
        raise Exception(f"获取 token 失败: {data}")

# 使用示例
token = get_tenant_access_token("cli_xxx", "xxx")
```

```javascript
// Node.js 版本
const axios = require('axios');

async function getTenantAccessToken(appId, appSecret) {
    const response = await axios.post(
        'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
        { app_id: appId, app_secret: appSecret }
    );

    if (response.data.code === 0) {
        return response.data.tenant_access_token;
    }
    throw new Error(`获取 token 失败: ${JSON.stringify(response.data)}`);
}
```

### 1.3 使用官方 SDK

飞书提供多语言官方 SDK（截至 2026 年最新版本）：

```bash
# Python
pip install lark-oapi

# Node.js (v1.56.1)
npm install @larksuiteoapi/node-sdk

# Go (v3)
go get github.com/larksuite/oapi-sdk-go/v3

# Java
# Maven: com.larksuite.oapi:oapi-sdk
```

### 1.4 MCP Server 集成（AI Agent）

飞书官方 MCP Server 支持 AI Agent 与飞书深度协作：

```bash
# 安装 MCP Server
npm install @larksuiteoapi/lark-mcp
```

**支持的能力**：
- 文档服务：读取/创建飞书文档
- 机器人服务：发送消息和卡片
- 聊天服务：管理群组和会话
- 日历服务：创建和管理日程
- 多维表格：数据读写操作

**配置示例**（Claude Desktop / Cursor）：

```json
{
  "mcpServers": {
    "feishu": {
      "command": "npx",
      "args": ["@larksuiteoapi/lark-mcp"],
      "env": {
        "FEISHU_APP_ID": "your_app_id",
        "FEISHU_APP_SECRET": "your_app_secret"
      }
    }
  }
}
```

**常用 MCP 工具**：
| 工具名 | 功能 |
|--------|------|
| `send_text_message` | 发送文本消息 |
| `send_card_message` | 发送卡片消息 |
| `create_document` | 创建文档 |
| `read_document` | 读取文档内容 |
| `create_calendar_event` | 创建日程 |
| `search_bitable_records` | 查询多维表格 |

---

## 二、核心 API 使用

### 2.1 消息卡片搭建工具

**强烈推荐**：使用 [消息卡片搭建工具](https://open.feishu.cn/tool/cardbuilder) 可视化设计卡片！

**核心优势**：
- 纯可视化编辑，无需手写 JSON
- 一键保存为模板，构建专属卡片库
- 使用卡片 ID 直接发送，代码极简

**使用流程**：
1. 访问 Card Builder，可视化设计卡片
2. 保存卡片获取 `template_id`
3. 代码中使用模板 ID 发送：

```python
# 使用模板发送卡片（推荐）
def send_card_by_template(receive_id: str, template_id: str, template_variable: dict):
    """使用卡片模板发送消息"""
    content = {
        "type": "template",
        "data": {
            "template_id": template_id,
            "template_variable": template_variable
        }
    }
    return send_message(receive_id, "interactive", content)

# 使用示例
send_card_by_template(
    receive_id="ou_xxx",
    template_id="AAqkxxxxxxxx",
    template_variable={
        "title": "周报提醒",
        "content": "请在今天下班前提交周报"
    }
)
```

### 2.2 发送消息

**API 端点**：`POST /open-apis/im/v1/messages`

#### Python 示例

```python
import lark_oapi as lark
from lark_oapi.api.im.v1 import *

# 创建客户端
client = lark.Client.builder() \
    .app_id("cli_xxx") \
    .app_secret("xxx") \
    .build()

# 发送文本消息
def send_text_message(receive_id: str, text: str, receive_id_type: str = "open_id"):
    """
    发送文本消息

    Args:
        receive_id: 接收者ID (open_id/user_id/union_id/email/chat_id)
        text: 消息内容
        receive_id_type: ID类型
    """
    request = CreateMessageRequest.builder() \
        .receive_id_type(receive_id_type) \
        .request_body(CreateMessageRequestBody.builder()
            .receive_id(receive_id)
            .msg_type("text")
            .content('{"text": "' + text + '"}')
            .build()) \
        .build()

    response = client.im.v1.message.create(request)

    if not response.success():
        raise Exception(f"发送失败: {response.msg}")

    return response.data.message_id

# 发送富文本消息
def send_rich_text_message(receive_id: str, title: str, content_list: list):
    """
    发送富文本消息

    Args:
        receive_id: 接收者ID
        title: 消息标题
        content_list: 富文本内容列表
    """
    import json

    content = {
        "zh_cn": {
            "title": title,
            "content": content_list
        }
    }

    request = CreateMessageRequest.builder() \
        .receive_id_type("open_id") \
        .request_body(CreateMessageRequestBody.builder()
            .receive_id(receive_id)
            .msg_type("post")
            .content(json.dumps(content))
            .build()) \
        .build()

    response = client.im.v1.message.create(request)
    return response.data.message_id

# 使用示例
send_text_message("ou_xxx", "Hello, 飞书!")

# 富文本示例
content = [
    [
        {"tag": "text", "text": "项目进度更新："},
        {"tag": "a", "text": "查看详情", "href": "https://example.com"}
    ],
    [
        {"tag": "at", "user_id": "ou_xxx"},
        {"tag": "text", "text": " 请确认"}
    ]
]
send_rich_text_message("ou_xxx", "项目周报", content)
```

#### Node.js 示例

```javascript
const lark = require('@larksuiteoapi/node-sdk');

// 创建客户端
const client = new lark.Client({
    appId: 'cli_xxx',
    appSecret: 'xxx',
});

// 发送文本消息
async function sendTextMessage(receiveId, text, receiveIdType = 'open_id') {
    const response = await client.im.message.create({
        params: { receive_id_type: receiveIdType },
        data: {
            receive_id: receiveId,
            msg_type: 'text',
            content: JSON.stringify({ text }),
        },
    });

    if (response.code !== 0) {
        throw new Error(`发送失败: ${response.msg}`);
    }

    return response.data.message_id;
}

// 发送卡片消息
async function sendCardMessage(receiveId, card) {
    const response = await client.im.message.create({
        params: { receive_id_type: 'open_id' },
        data: {
            receive_id: receiveId,
            msg_type: 'interactive',
            content: JSON.stringify(card),
        },
    });

    return response.data.message_id;
}

// 卡片消息示例
const card = {
    "config": { "wide_screen_mode": true },
    "header": {
        "title": { "tag": "plain_text", "content": "项目通知" },
        "template": "blue"
    },
    "elements": [
        {
            "tag": "div",
            "text": { "tag": "lark_md", "content": "**任务完成**\n项目A已完成部署" }
        },
        {
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "text": { "tag": "plain_text", "content": "查看详情" },
                    "type": "primary",
                    "url": "https://example.com"
                }
            ]
        }
    ]
};

sendCardMessage('ou_xxx', card);
```

### 2.3 群组管理

#### 创建群组

```python
from lark_oapi.api.im.v1 import *

def create_chat(name: str, description: str, owner_id: str, user_id_list: list):
    """创建群组"""
    request = CreateChatRequest.builder() \
        .user_id_type("open_id") \
        .request_body(CreateChatRequestBody.builder()
            .name(name)
            .description(description)
            .owner_id(owner_id)
            .user_id_list(user_id_list)
            .chat_mode("group")
            .chat_type("private")
            .build()) \
        .build()

    response = client.im.v1.chat.create(request)
    return response.data.chat_id

# 使用示例
chat_id = create_chat(
    name="项目讨论群",
    description="项目A进度讨论",
    owner_id="ou_xxx",
    user_id_list=["ou_aaa", "ou_bbb", "ou_ccc"]
)
```

#### 添加群成员

```python
def add_chat_members(chat_id: str, member_ids: list):
    """添加群成员"""
    request = CreateChatMembersRequest.builder() \
        .chat_id(chat_id) \
        .member_id_type("open_id") \
        .request_body(CreateChatMembersRequestBody.builder()
            .id_list(member_ids)
            .build()) \
        .build()

    response = client.im.v1.chat_members.create(request)
    return response.success()
```

### 2.4 文档操作

#### 创建文档

```python
from lark_oapi.api.docx.v1 import *

def create_document(title: str, folder_token: str = None):
    """创建飞书文档"""
    request = CreateDocumentRequest.builder() \
        .request_body(CreateDocumentRequestBody.builder()
            .title(title)
            .folder_token(folder_token)
            .build()) \
        .build()

    response = client.docx.v1.document.create(request)
    return {
        "document_id": response.data.document.document_id,
        "title": response.data.document.title
    }

# 使用示例
doc = create_document("周会纪要 2024-01-15")
print(f"文档ID: {doc['document_id']}")
```

#### 写入文档内容

```python
def create_document_block(document_id: str, block_type: str, content: dict):
    """向文档添加内容块"""
    request = CreateDocumentBlockRequest.builder() \
        .document_id(document_id) \
        .request_body(CreateDocumentBlockRequestBody.builder()
            .block_type(block_type)
            .text_run(TextRun.builder()
                .content(content.get("text", ""))
                .build())
            .build()) \
        .build()

    response = client.docx.v1.document_block.create(request)
    return response.data.block
```

### 2.5 多维表格操作

#### 读取记录

```python
from lark_oapi.api.bitable.v1 import *

def list_bitable_records(app_token: str, table_id: str, page_size: int = 20):
    """获取多维表格记录"""
    request = ListAppTableRecordRequest.builder() \
        .app_token(app_token) \
        .table_id(table_id) \
        .page_size(page_size) \
        .build()

    response = client.bitable.v1.app_table_record.list(request)
    return response.data.items
```

#### 新增记录

```python
def create_bitable_record(app_token: str, table_id: str, fields: dict):
    """新增多维表格记录"""
    request = CreateAppTableRecordRequest.builder() \
        .app_token(app_token) \
        .table_id(table_id) \
        .request_body(AppTableRecord.builder()
            .fields(fields)
            .build()) \
        .build()

    response = client.bitable.v1.app_table_record.create(request)
    return response.data.record

# 使用示例
record = create_bitable_record(
    app_token="bascnxxx",
    table_id="tblxxx",
    fields={
        "姓名": "张三",
        "部门": "技术部",
        "入职日期": "2024-01-15"
    }
)
```

### 2.6 日历操作

#### 创建日程

```python
from lark_oapi.api.calendar.v4 import *

def create_calendar_event(
    summary: str,
    start_time: int,
    end_time: int,
    attendee_ids: list = None
):
    """创建日程"""
    attendees = None
    if attendee_ids:
        attendees = [
            CalendarEventAttendee.builder()
                .type("user")
                .user_id(uid)
                .build()
            for uid in attendee_ids
        ]

    request = CreateCalendarEventRequest.builder() \
        .calendar_id("primary") \
        .request_body(CalendarEvent.builder()
            .summary(summary)
            .start_time(TimeInfo.builder()
                .timestamp(str(start_time))
                .build())
            .end_time(TimeInfo.builder()
                .timestamp(str(end_time))
                .build())
            .attendees(attendees)
            .build()) \
        .build()

    response = client.calendar.v4.calendar_event.create(request)
    return response.data.event

# 使用示例
import time
start = int(time.time()) + 3600  # 1小时后
end = start + 3600  # 持续1小时

event = create_calendar_event(
    summary="项目评审会议",
    start_time=start,
    end_time=end,
    attendee_ids=["ou_xxx", "ou_yyy"]
)
```

---

## 三、事件订阅

### 3.1 配置事件订阅

1. 进入应用详情页 → **事件订阅**
2. 配置请求地址（你的服务器 URL）
3. 选择需要订阅的事件

### 3.2 事件处理示例

```python
from flask import Flask, request
import lark_oapi as lark
from lark_oapi.adapter.flask import *

app = Flask(__name__)

# 创建事件处理器
def handle_message_receive(data):
    """处理接收消息事件"""
    message = data.event.message
    content = message.content
    sender_id = message.sender.sender_id.open_id

    print(f"收到消息: {content}, 发送者: {sender_id}")

    # 自动回复
    # send_text_message(sender_id, "收到您的消息")

handler = lark.EventDispatcherHandler.builder("", "") \
    .register_p2_im_message_receive_v1(handle_message_receive) \
    .build()

@app.route("/webhook/event", methods=["POST"])
def event_handler():
    return handler.do(parse_req())

if __name__ == "__main__":
    app.run(port=8080)
```

### 3.3 常用事件类型

| 事件 | 说明 |
|------|------|
| `im.message.receive_v1` | 接收消息 |
| `im.chat.member.user.added_v1` | 用户入群 |
| `im.chat.member.user.deleted_v1` | 用户退群 |
| `contact.user.created_v3` | 新员工入职 |
| `approval.approval.updated_v4` | 审批状态变更 |

---

## 四、权限申请

### 4.1 常用权限列表

| 权限 | 说明 |
|------|------|
| `im:message` | 获取与发送单聊、群聊消息 |
| `im:chat` | 获取与更新群组信息 |
| `contact:user.base:readonly` | 获取用户基本信息 |
| `docs:doc` | 读写云文档 |
| `bitable:app` | 读写多维表格 |
| `calendar:calendar` | 读写日历 |

### 4.2 申请流程

1. 进入应用详情页 → **权限管理**
2. 搜索并开通所需权限
3. 提交审核（需要管理员批准）

---

## 五、最佳实践

### 5.1 错误处理

```python
def safe_api_call(func, *args, **kwargs):
    """安全的 API 调用封装"""
    try:
        response = func(*args, **kwargs)

        if hasattr(response, 'success') and not response.success():
            print(f"API 错误: code={response.code}, msg={response.msg}")
            return None

        return response.data

    except Exception as e:
        print(f"调用异常: {e}")
        return None
```

### 5.2 Token 缓存

```python
import time

class TokenManager:
    """Token 管理器，支持自动刷新"""

    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
        self._token = None
        self._expire_time = 0

    def get_token(self):
        # 提前5分钟刷新
        if time.time() > self._expire_time - 300:
            self._refresh_token()
        return self._token

    def _refresh_token(self):
        token = get_tenant_access_token(self.app_id, self.app_secret)
        self._token = token
        self._expire_time = time.time() + 7200  # 2小时有效期
```

### 5.3 限流处理

```python
import time
from functools import wraps

def rate_limit(max_calls, period):
    """限流装饰器"""
    calls = []

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            calls[:] = [c for c in calls if c > now - period]

            if len(calls) >= max_calls:
                sleep_time = period - (now - calls[0])
                time.sleep(sleep_time)

            calls.append(time.time())
            return func(*args, **kwargs)

        return wrapper
    return decorator

# 使用示例：每秒最多5次调用
@rate_limit(max_calls=5, period=1)
def send_message(receive_id, text):
    # ...
    pass
```

---

## 六、常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 99991663 | tenant token invalid | 检查 App ID/Secret，重新获取 token |
| 99991668 | user token invalid | 用户授权已失效，需重新授权 |
| 99991400 | permission denied | 检查是否申请了所需权限 |
| 99991401 | app not activated | 应用未发布或未被管理员审核通过 |
| 230001 | message send failed | 检查 receive_id 是否正确 |

---

## 七、实用工具

### 7.1 API Explorer

飞书提供在线调试工具：[API Explorer](https://open.feishu.cn/api-explorer)

功能：
- 一键获取 token
- 在线调试 API
- 生成多语言示例代码

### 7.2 AI 智能助手

飞书 AI 助手支持自然语言生成代码：[AI Playground](https://open.feishu.cn/app/ai/playground)

支持语言：
- Node.js 22.14
- Python 3.11
- Go 1.23
- Java JDK 21

### 7.3 SDK 讨论群

加入官方开发者社区获取技术支持。

---

## 八、参考资源

- [飞书开放平台文档](https://open.feishu.cn/document/)
- [飞书机器人助手](https://botbuilder.feishu.cn/home)
- [API Explorer](https://open.feishu.cn/api-explorer)
- [开发者后台](https://open.feishu.cn/app/)
- [消息卡片搭建工具](https://open.feishu.cn/tool/cardbuilder)

---

## 九、配置检查清单

### 零代码开发（机器人助手）

- [ ] 创建机器人应用
- [ ] 设计自动化流程
- [ ] 配置触发器和操作节点
- [ ] 设置应用可用范围
- [ ] 发布应用并等待审核

### 全代码开发（开放平台）

- [ ] 创建自建应用
- [ ] 获取 App ID 和 App Secret
- [ ] 申请所需 API 权限
- [ ] 配置事件订阅（如需要）
- [ ] 安装官方 SDK
- [ ] 实现 Token 管理
- [ ] 添加错误处理和重试逻辑
