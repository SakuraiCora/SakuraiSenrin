"""
Author: SakuraiCora
Date: 2024-12-30 19:36:51
LastEditors: SakuraiCora
LastEditTime: 2024-12-30 19:37:14
Description: 好友通知事件处理
"""

import asyncio
import random

from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.event import FriendRequestEvent
from nonebot.params import Depends
from nonebot.plugin import PluginMetadata, on_request
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache.memory_cache import memory_cache
from src.database.system.dao import (
    UserInfoDAO,
    UserLogDAO,
    UserService,
)
from src.database.system.database import (
    get_session as get_system_session,
)
from src.utils.enmus import (
    PluginPermissionEnum,
    TriggerTypeEnum,
    UserStatusEnum,
)
from src.utils.message_builder import NoticeBuilder

name = "好友通知事件处理"
description = """
好友通知事件处理:
  处理好友请求
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


@on_request(priority=5).handle()
async def _(
    bot: Bot,
    event: FriendRequestEvent,
    session: AsyncSession = Depends(get_system_session, use_cache=False),
):
    await asyncio.sleep(random.randint(10, 20))
    await bot.set_friend_add_request(flag=event.flag, approve=True)
    user_name: str | None = (await bot.get_stranger_info(user_id=event.user_id)).get(
        "nickname"
    )

    await UserService(UserInfoDAO(session), UserLogDAO(session)).upsert_info_with_log(
        user_id=event.get_user_id(),
        user_name=user_name,
        status=UserStatusEnum.ENABLE,
        operator_id=str(event.self_id),
    )

    for super_user_id in memory_cache.super_users:
        await bot.send_private_msg(
            user_id=int(super_user_id),
            message=NoticeBuilder.info(f"收到了新的好友请求，已同意：{event.user_id}"),
        )
        await asyncio.sleep(1)
