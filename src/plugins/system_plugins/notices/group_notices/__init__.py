"""
Author: SakuraiCora
Date: 2024-12-28 14:41:29
LastEditors: SakuraiCora
LastEditTime: 2024-12-29 21:31:54
Description: 群组事件处理
"""

import asyncio
from datetime import datetime

from nonebot import on_notice
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.event import (
    GroupBanNoticeEvent,
    GroupDecreaseNoticeEvent,
)
from nonebot.params import Depends
from nonebot.plugin import PluginMetadata
from nonebot.rule import is_type
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache.memory_cache import memory_cache
from src.database.system.dao import GroupInfoDAO, GroupLogDAO, GroupService
from src.database.system.database import (
    get_session as get_system_session,
)
from src.scripts.init_memory_cache import init_group_info
from src.utils.common_helper import (
    CommonHelper,
    GroupStatusEnum,
)
from src.utils.enmus import (
    PluginPermissionEnum,
    TriggerTypeEnum,
)
from src.utils.message_builder import AlertTemplate

name = "群组事件处理"
description = """
群组事件处理:
  群组通知事件处理
  迎新
  被禁言自动退群拉黑
  更新群组状态

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


@on_notice(priority=5, rule=is_type(GroupDecreaseNoticeEvent)).handle()
async def _(
    bot: Bot,
    event: GroupDecreaseNoticeEvent,
    session: AsyncSession = Depends(get_system_session, use_cache=False),
):
    if event.sub_type == "kick_me" and event.is_tome():
        await GroupService(
            GroupInfoDAO(session), GroupLogDAO(session)
        ).update_status_with_log(
            group_id=event.group_id.__str__(),
            status=GroupStatusEnum.BAN,
            operator_id=bot.self_id,
            remark="被移出群聊自动拉黑",
            effective_time=datetime.max,
        )
        await init_group_info(session)
        for superuser in memory_cache.super_users:
            await bot.send_private_msg(
                user_id=int(superuser),
                message=AlertTemplate.build_tip_notification(
                    event_name="群组被踢出",
                    event_details=(
                        "不好，被扔出来了，已自动拉黑\n"
                        f"群组：{event.group_id}\n"
                        f"操作者：{event.operator_id}"
                    ),
                ),
            )
            await asyncio.sleep(1)


@on_notice(priority=5, rule=is_type(GroupBanNoticeEvent)).handle()
async def _(
    bot: Bot,
    event: GroupBanNoticeEvent,
    session: AsyncSession = Depends(get_system_session, use_cache=False),
):
    if (
        event.sub_type == "ban"
        and event.user_id == 0
        and await CommonHelper.is_group_valid(event.group_id.__str__())
    ):
        await GroupService(
            GroupInfoDAO(session), GroupLogDAO(session)
        ).update_status_with_log(
            group_id=event.group_id.__str__(),
            status=GroupStatusEnum.DISABLE,
            operator_id=bot.self_id,
            remark="白名单群组全员禁言，暂停使用",
            effective_time=datetime.max,
        )
        await session.commit()
        await init_group_info(session)
    elif (
        event.sub_type == "lift_ban"
        and event.user_id == 0
        and memory_cache.groups[str(event.group_id)].status == GroupStatusEnum.DISABLE
    ):
        await GroupService(
            GroupInfoDAO(session), GroupLogDAO(session)
        ).update_status_with_log(
            group_id=event.group_id.__str__(),
            status=GroupStatusEnum.ENABLE,
            operator_id=bot.self_id,
            remark="白名单群组解除全员禁言，恢复使用",
            effective_time=datetime.max,
        )
        await session.commit()
        await init_group_info(session)
    elif event.is_tome():
        await bot.set_group_leave(group_id=event.group_id)
        group_service = GroupService(GroupInfoDAO(session), GroupLogDAO(session))
        await group_service.update_status_with_log(
            group_id=event.group_id.__str__(),
            status=GroupStatusEnum.BAN,
            operator_id=bot.self_id,
            remark="恶意禁言自动拉黑",
            effective_time=datetime.max,
        )
        await group_service.update_effective_time_with_log(
            group_id=event.group_id.__str__(),
            effective_time=datetime(year=2099, month=12, day=31),
            operator_id=bot.self_id,
        )
        await session.commit()
        await init_group_info(session)
        for superuser in memory_cache.super_users:
            await bot.send_private_msg(
                user_id=int(superuser),
                message=AlertTemplate.build_tip_notification(
                    event_name="群组禁言",
                    event_details=(
                        "检测到禁言行为，已自动退出群聊\n"
                        f"群组：{event.group_id}\n"
                        f"操作者：{event.operator_id}\n"
                        f"禁言时间：{event.duration}秒"
                    ),
                ),
            )
            await asyncio.sleep(1)
