"""
Author: SakuraiCora
Date: 2024-12-30 19:26:29
LastEditors: SakuraiCora
LastEditTime: 2024-12-30 19:30:01
Description: WebUI 管理模块
"""

import random
import time
from string import ascii_lowercase, digits

import nonebot
from fastapi import FastAPI
from nonebot.adapters.onebot.v11.event import PrivateMessageEvent
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata

from src.config.general_config import general_config
from src.utils.enums import PluginPermissionEnum, TriggerTypeEnum
from src.utils.message_builder import NoticeBuilder

name = "WebUI 管理模块"
description = """
WebUI 管理模块，正在开发中
""".strip()

usage = f"""
📖 ===== {name} =====

命令前缀: #admin

1.获取验证码 🔐
  示例: #admin.auth

其余功能正在开发中

⚠️ 注意事项:
1. 验证码 30 秒内只能使用一次。
2. 如需进一步支持，请联系管理员，或加入反馈群「{general_config.support_group_id}」💬。
""".strip()

__plugin_meta__ = PluginMetadata(
    name=name,
    description=description,
    usage=usage,
    extra={
        "author": "SakuraiCora",
        "version": "0.1.0",
        "trigger": TriggerTypeEnum.ACTIVE,
        "permission": PluginPermissionEnum.SUPERUSER,
    },
)


app: FastAPI = nonebot.get_app()

varification_code_dict: dict[int, tuple[str, float]] = {}

admin_command_group = nonebot.CommandGroup("admin")
admin_auth = admin_command_group.command(
    "auth",
    permission=SUPERUSER,
    priority=5,
    block=False,
)


@app.get("/api")
async def custom_api(code: str):
    auth_dict = {v[0]: (k, v[1]) for k, v in varification_code_dict.items()}.get(code)
    if auth_dict and time.time() < auth_dict[1]:
        user_id = auth_dict[0]
        varification_code_dict.pop(user_id)
        return {"message": "验证成功"}
    else:
        return {"message": "验证码无效，请尝试重新获取"}


@admin_auth.handle()
async def _(event: PrivateMessageEvent):
    varification_code, expire_time = varification_code_dict.get(
        event.user_id, ("", 0.0)
    )
    if varification_code and time.time() < expire_time:
        NoticeBuilder.warning
        await admin_auth.finish(
            NoticeBuilder.warning(
                f"您已经发送过验证码，请勿重复发送。您的验证码为：{varification_code}"
            )
        )
    else:
        varification_code = "".join(random.sample(ascii_lowercase + digits, 16))
        varification_code_dict[event.user_id] = (varification_code, time.time() + 30)
        await admin_auth.finish(
            NoticeBuilder.access(f"验证码为：{varification_code}，请在30秒内完成验证")
        )
