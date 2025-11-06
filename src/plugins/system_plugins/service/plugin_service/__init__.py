"""
Author: SakuraiCora
Date: 2025-01-02 15:10:00
LastEditors: SakuraiCora
LastEditTime: 2025-01-02 15:10:45
Description: 插件相关服务
"""

from nonebot.adapters.onebot.v11.event import Event, Sender
from nonebot.matcher import Matcher
from nonebot.message import run_postprocessor
from nonebot.plugin import PluginMetadata

from src.cache.memory_cache import memory_cache
from src.database.system.dao import (
    PluginLogDAO,
    UserInfoDAO,
    UserLogDAO,
    UserService,
)
from src.database.system.database import async_session as system_session
from src.scripts.init_memory_cache import init_user_info
from utils.enums import (
    OnebotV11EventEnum,
    PluginPermissionEnum,
    TriggerTypeEnum,
    UserStatusEnum,
)

name = "插件服务"
description = """
插件相关服务：
  记录插件使用日志
""".strip()

usage = """
被动触发
""".strip()

__plugin_meta__ = PluginMetadata(
    name=name,
    description=description,
    usage=usage,
    extra={
        "author": "SakuraiCora",
        "version": "0.1.0",
        "trigger": TriggerTypeEnum.PASSIVE,
        "permission": PluginPermissionEnum.SUPERUSER,
    },
)


@run_postprocessor
async def _(
    matcher: Matcher,
    event: Event,
):
    try:
        operator_id = str(getattr(event, "operator_id", event.get_user_id()))
        event_type = OnebotV11EventEnum(type(event).__name__)
        assert matcher.plugin_name
    except Exception:
        return
    sender: Sender | None = getattr(event, "sender", None)
    if sender and str(sender.user_id) not in memory_cache.users:
        async with system_session() as session:
            await UserService(
                UserInfoDAO(session), UserLogDAO(session)
            ).upsert_info_with_log(
                user_id=str(sender.user_id),
                user_name=sender.nickname,
                status=UserStatusEnum.ENABLE,
                operator_id=operator_id,
                remark="调用插件自动记录用户信息",
            )
            await session.commit()
            await init_user_info(session)

    if plugin_info := memory_cache.plugins.get(matcher.plugin_name):
        async with system_session() as session:
            await PluginLogDAO(session).insert_log(
                plugin_id=plugin_info.id,
                operator_id=operator_id,
                event_json=event.model_dump(),
                event_type=event_type,
            )
            await session.commit()
