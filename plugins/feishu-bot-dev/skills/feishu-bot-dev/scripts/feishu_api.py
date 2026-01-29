#!/usr/bin/env python3
"""
飞书 API 封装库
支持消息发送、群组管理、文档操作等核心功能
"""

import os
import json
import time
import requests
from typing import Optional, List, Dict, Any
from functools import wraps


# ============== 配置 ==============

def get_config():
    """获取配置"""
    return {
        "app_id": os.environ.get("FEISHU_APP_ID", ""),
        "app_secret": os.environ.get("FEISHU_APP_SECRET", ""),
        "base_url": "https://open.feishu.cn/open-apis"
    }


# ============== Token 管理 ==============

class TokenManager:
    """Token 管理器，支持自动刷新"""

    _instance = None
    _token = None
    _expire_time = 0

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_token(self) -> str:
        """获取有效的 tenant_access_token"""
        # 提前5分钟刷新
        if time.time() > self._expire_time - 300:
            self._refresh_token()
        return self._token

    def _refresh_token(self):
        """刷新 token"""
        config = get_config()
        url = f"{config['base_url']}/auth/v3/tenant_access_token/internal"

        response = requests.post(url, json={
            "app_id": config["app_id"],
            "app_secret": config["app_secret"]
        })
        data = response.json()

        if data.get("code") == 0:
            self._token = data["tenant_access_token"]
            self._expire_time = time.time() + data.get("expire", 7200)
        else:
            raise Exception(f"获取 token 失败: {data}")


def get_headers() -> Dict[str, str]:
    """获取请求头"""
    token_manager = TokenManager()
    return {
        "Authorization": f"Bearer {token_manager.get_token()}",
        "Content-Type": "application/json"
    }


# ============== 限流装饰器 ==============

def rate_limit(max_calls: int = 5, period: float = 1.0):
    """限流装饰器"""
    calls = []

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            calls[:] = [c for c in calls if c > now - period]

            if len(calls) >= max_calls:
                sleep_time = period - (now - calls[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)

            calls.append(time.time())
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ============== 消息发送 ==============

@rate_limit(max_calls=5, period=1)
def send_message(
    receive_id: str,
    msg_type: str,
    content: Dict[str, Any],
    receive_id_type: str = "open_id"
) -> Dict[str, Any]:
    """
    发送消息

    Args:
        receive_id: 接收者ID
        msg_type: 消息类型 (text, post, image, interactive 等)
        content: 消息内容
        receive_id_type: ID类型 (open_id, user_id, union_id, email, chat_id)

    Returns:
        消息信息
    """
    config = get_config()
    url = f"{config['base_url']}/im/v1/messages"

    params = {"receive_id_type": receive_id_type}
    payload = {
        "receive_id": receive_id,
        "msg_type": msg_type,
        "content": json.dumps(content) if isinstance(content, dict) else content
    }

    response = requests.post(url, params=params, json=payload, headers=get_headers())
    data = response.json()

    if data.get("code") != 0:
        raise Exception(f"发送消息失败: {data}")

    return data.get("data", {})


def send_text(receive_id: str, text: str, receive_id_type: str = "open_id") -> Dict:
    """发送文本消息"""
    return send_message(
        receive_id=receive_id,
        msg_type="text",
        content={"text": text},
        receive_id_type=receive_id_type
    )


def send_card(receive_id: str, card: Dict, receive_id_type: str = "open_id") -> Dict:
    """发送卡片消息"""
    return send_message(
        receive_id=receive_id,
        msg_type="interactive",
        content=card,
        receive_id_type=receive_id_type
    )


def send_card_by_template(
    receive_id: str,
    template_id: str,
    template_variable: Dict = None,
    receive_id_type: str = "open_id"
) -> Dict:
    """
    使用卡片模板发送消息（推荐）

    通过消息卡片搭建工具 (https://open.feishu.cn/tool/cardbuilder) 创建模板后使用

    Args:
        receive_id: 接收者ID
        template_id: 卡片模板ID (在卡片搭建工具中获取)
        template_variable: 模板变量字典
        receive_id_type: ID类型

    Returns:
        消息信息
    """
    content = {
        "type": "template",
        "data": {
            "template_id": template_id,
            "template_variable": template_variable or {}
        }
    }
    return send_message(
        receive_id=receive_id,
        msg_type="interactive",
        content=content,
        receive_id_type=receive_id_type
    )


def send_rich_text(
    receive_id: str,
    title: str,
    content_blocks: List[List[Dict]],
    receive_id_type: str = "open_id"
) -> Dict:
    """
    发送富文本消息

    Args:
        receive_id: 接收者ID
        title: 标题
        content_blocks: 内容块列表
            示例: [[{"tag": "text", "text": "Hello"}, {"tag": "at", "user_id": "all"}]]
        receive_id_type: ID类型

    Returns:
        消息信息
    """
    content = {
        "zh_cn": {
            "title": title,
            "content": content_blocks
        }
    }
    return send_message(
        receive_id=receive_id,
        msg_type="post",
        content=content,
        receive_id_type=receive_id_type
    )


# ============== 群组管理 ==============

def create_chat(
    name: str,
    description: str = "",
    owner_id: str = None,
    user_id_list: List[str] = None,
    chat_mode: str = "group"
) -> str:
    """
    创建群组

    Args:
        name: 群名称
        description: 群描述
        owner_id: 群主 ID
        user_id_list: 成员 ID 列表
        chat_mode: group(群组) 或 topic(话题)

    Returns:
        chat_id
    """
    config = get_config()
    url = f"{config['base_url']}/im/v1/chats"

    params = {"user_id_type": "open_id"}
    payload = {
        "name": name,
        "description": description,
        "chat_mode": chat_mode,
        "chat_type": "private"
    }

    if owner_id:
        payload["owner_id"] = owner_id
    if user_id_list:
        payload["user_id_list"] = user_id_list

    response = requests.post(url, params=params, json=payload, headers=get_headers())
    data = response.json()

    if data.get("code") != 0:
        raise Exception(f"创建群组失败: {data}")

    return data["data"]["chat_id"]


def add_chat_members(chat_id: str, member_ids: List[str]) -> bool:
    """添加群成员"""
    config = get_config()
    url = f"{config['base_url']}/im/v1/chats/{chat_id}/members"

    params = {"member_id_type": "open_id"}
    payload = {"id_list": member_ids}

    response = requests.post(url, params=params, json=payload, headers=get_headers())
    data = response.json()

    return data.get("code") == 0


def remove_chat_members(chat_id: str, member_ids: List[str]) -> bool:
    """移除群成员"""
    config = get_config()
    url = f"{config['base_url']}/im/v1/chats/{chat_id}/members"

    params = {"member_id_type": "open_id"}
    payload = {"id_list": member_ids}

    response = requests.delete(url, params=params, json=payload, headers=get_headers())
    data = response.json()

    return data.get("code") == 0


def update_chat(chat_id: str, name: str = None, description: str = None) -> bool:
    """更新群信息"""
    config = get_config()
    url = f"{config['base_url']}/im/v1/chats/{chat_id}"

    payload = {}
    if name:
        payload["name"] = name
    if description:
        payload["description"] = description

    response = requests.put(url, json=payload, headers=get_headers())
    data = response.json()

    return data.get("code") == 0


def get_chat_info(chat_id: str) -> Dict:
    """获取群信息"""
    config = get_config()
    url = f"{config['base_url']}/im/v1/chats/{chat_id}"

    response = requests.get(url, headers=get_headers())
    data = response.json()

    if data.get("code") != 0:
        raise Exception(f"获取群信息失败: {data}")

    return data.get("data", {})


# ============== 文档操作 ==============

def create_document(title: str, folder_token: str = None) -> Dict:
    """
    创建文档

    Args:
        title: 文档标题
        folder_token: 文件夹 token (可选)

    Returns:
        文档信息 {document_id, title}
    """
    config = get_config()
    url = f"{config['base_url']}/docx/v1/documents"

    payload = {"title": title}
    if folder_token:
        payload["folder_token"] = folder_token

    response = requests.post(url, json=payload, headers=get_headers())
    data = response.json()

    if data.get("code") != 0:
        raise Exception(f"创建文档失败: {data}")

    doc = data["data"]["document"]
    return {
        "document_id": doc["document_id"],
        "title": doc["title"]
    }


def get_document_content(document_id: str) -> Dict:
    """获取文档内容"""
    config = get_config()
    url = f"{config['base_url']}/docx/v1/documents/{document_id}/raw_content"

    response = requests.get(url, headers=get_headers())
    data = response.json()

    if data.get("code") != 0:
        raise Exception(f"获取文档内容失败: {data}")

    return data.get("data", {})


# ============== 多维表格 ==============

def list_bitable_records(
    app_token: str,
    table_id: str,
    page_size: int = 20,
    page_token: str = None,
    filter_expr: str = None
) -> Dict:
    """
    获取多维表格记录

    Args:
        app_token: 多维表格 token
        table_id: 数据表 ID
        page_size: 每页数量
        page_token: 分页标记
        filter_expr: 筛选条件

    Returns:
        {items: [...], page_token: str, has_more: bool}
    """
    config = get_config()
    url = f"{config['base_url']}/bitable/v1/apps/{app_token}/tables/{table_id}/records"

    params = {"page_size": page_size}
    if page_token:
        params["page_token"] = page_token
    if filter_expr:
        params["filter"] = filter_expr

    response = requests.get(url, params=params, headers=get_headers())
    data = response.json()

    if data.get("code") != 0:
        raise Exception(f"获取记录失败: {data}")

    return data.get("data", {})


def create_bitable_record(app_token: str, table_id: str, fields: Dict) -> Dict:
    """
    新增多维表格记录

    Args:
        app_token: 多维表格 token
        table_id: 数据表 ID
        fields: 字段数据

    Returns:
        新增的记录
    """
    config = get_config()
    url = f"{config['base_url']}/bitable/v1/apps/{app_token}/tables/{table_id}/records"

    payload = {"fields": fields}

    response = requests.post(url, json=payload, headers=get_headers())
    data = response.json()

    if data.get("code") != 0:
        raise Exception(f"新增记录失败: {data}")

    return data["data"]["record"]


def update_bitable_record(
    app_token: str,
    table_id: str,
    record_id: str,
    fields: Dict
) -> Dict:
    """更新多维表格记录"""
    config = get_config()
    url = f"{config['base_url']}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"

    payload = {"fields": fields}

    response = requests.put(url, json=payload, headers=get_headers())
    data = response.json()

    if data.get("code") != 0:
        raise Exception(f"更新记录失败: {data}")

    return data["data"]["record"]


# ============== 日历 ==============

def create_calendar_event(
    summary: str,
    start_time: int,
    end_time: int,
    description: str = "",
    attendee_ids: List[str] = None,
    calendar_id: str = "primary"
) -> Dict:
    """
    创建日程

    Args:
        summary: 日程标题
        start_time: 开始时间戳 (秒)
        end_time: 结束时间戳 (秒)
        description: 描述
        attendee_ids: 参与者 ID 列表
        calendar_id: 日历 ID

    Returns:
        日程信息
    """
    config = get_config()
    url = f"{config['base_url']}/calendar/v4/calendars/{calendar_id}/events"

    payload = {
        "summary": summary,
        "description": description,
        "start_time": {"timestamp": str(start_time)},
        "end_time": {"timestamp": str(end_time)}
    }

    if attendee_ids:
        payload["attendees"] = [
            {"type": "user", "user_id": uid}
            for uid in attendee_ids
        ]

    params = {"user_id_type": "open_id"}

    response = requests.post(url, params=params, json=payload, headers=get_headers())
    data = response.json()

    if data.get("code") != 0:
        raise Exception(f"创建日程失败: {data}")

    return data["data"]["event"]


# ============== 用户信息 ==============

def get_user_info(user_id: str, user_id_type: str = "open_id") -> Dict:
    """获取用户信息"""
    config = get_config()
    url = f"{config['base_url']}/contact/v3/users/{user_id}"

    params = {"user_id_type": user_id_type}

    response = requests.get(url, params=params, headers=get_headers())
    data = response.json()

    if data.get("code") != 0:
        raise Exception(f"获取用户信息失败: {data}")

    return data["data"]["user"]


# ============== CLI 入口 ==============

def main():
    import argparse

    parser = argparse.ArgumentParser(description="飞书 API 命令行工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 发送消息
    send_parser = subparsers.add_parser("send", help="发送消息")
    send_parser.add_argument("--to", required=True, help="接收者ID")
    send_parser.add_argument("--text", required=True, help="消息内容")
    send_parser.add_argument("--type", default="open_id", help="ID类型")

    # 发送卡片模板消息
    card_parser = subparsers.add_parser("send-card", help="发送卡片模板消息")
    card_parser.add_argument("--to", required=True, help="接收者ID")
    card_parser.add_argument("--template", required=True, help="卡片模板ID")
    card_parser.add_argument("--vars", default="{}", help="模板变量 (JSON格式)")
    card_parser.add_argument("--type", default="open_id", help="ID类型")

    # 创建群组
    chat_parser = subparsers.add_parser("create-chat", help="创建群组")
    chat_parser.add_argument("--name", required=True, help="群名称")
    chat_parser.add_argument("--desc", default="", help="群描述")

    # 创建文档
    doc_parser = subparsers.add_parser("create-doc", help="创建文档")
    doc_parser.add_argument("--title", required=True, help="文档标题")

    # 测试连接
    subparsers.add_parser("test", help="测试 API 连接")

    args = parser.parse_args()

    if args.command == "send":
        result = send_text(args.to, args.text, args.type)
        print(f"消息已发送: {result.get('message_id')}")

    elif args.command == "send-card":
        template_vars = json.loads(args.vars)
        result = send_card_by_template(args.to, args.template, template_vars, args.type)
        print(f"卡片消息已发送: {result.get('message_id')}")

    elif args.command == "create-chat":
        chat_id = create_chat(args.name, args.desc)
        print(f"群组已创建: {chat_id}")

    elif args.command == "create-doc":
        doc = create_document(args.title)
        print(f"文档已创建: {doc}")

    elif args.command == "test":
        try:
            token_manager = TokenManager()
            token = token_manager.get_token()
            print(f"✓ API 连接成功")
            print(f"  Token: {token[:20]}...")
        except Exception as e:
            print(f"✗ API 连接失败: {e}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
