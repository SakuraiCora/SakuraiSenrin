"""
Author: SakuraiCora
Date: 2024-12-30 19:56:59
LastEditors: SakuraiCora
LastEditTime: 2024-12-30 19:58:54
Description: 检测服务
"""

from datetime import datetime

from nonebot import get_bot, require
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.event import (
    Event,
    MessageEvent,
)
from nonebot.exception import IgnoredException
from nonebot.matcher import Matcher
from nonebot.message import run_preprocessor
from nonebot.plugin import PluginMetadata

from src.cache.memory_cache import memory_cache
from src.config.general_config import general_config
from src.database.system.dao import (
    GroupInfoDAO,
    GroupLogDAO,
    GroupService,
    UserInfoDAO,
    UserLogDAO,
    UserService,
)
from src.database.system.database import (
    async_session as system_session,
)
from src.scripts.init_database import init_system_database
from src.scripts.init_memory_cache import init_group_info, init_user_info
from src.utils.common_helper import (
    CommonHelper,
    GroupStatusEnum,
    UserStatusEnum,
)
from src.utils.message_builder import NoticeBuilder

require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler  # noqa: E402

name = "检测服务"
description = """
黑白名单检测:
  检测用户是否在黑名单中
  检测群组是否在白名单中
  定时任务校验合法群组，对于不合法的进行退群处理
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
        "trigger": "Passive",
        "permission": "SUPERUSER",
    },
)


@scheduler.scheduled_job("cron", minute="*")
async def check_valid_group():
    if not ((bot := get_bot()) and isinstance(bot, Bot)):
        return
    async with system_session() as session:
        group_info_dao = GroupInfoDAO(session)
        group_log_dao = GroupLogDAO(session)
        group_service = GroupService(group_info_dao, group_log_dao)
        if group_id_list := set(
            [(i["group_id"]) for i in await bot.get_group_list()]
        ) & set(
            [
                int(i.group_id)
                for i in memory_cache.groups.values()
                if i.status
                in [GroupStatusEnum.UNAUTH, GroupStatusEnum.BAN, GroupStatusEnum.LEAVE]
            ]
        ):
            for group_id in group_id_list:
                # await bot.set_group_leave(group_id=group_id)  # TODOc
                await group_service.update_status_with_log(
                    group_id=str(group_id),
                    status=GroupStatusEnum.LEAVE,
                    operator_id=bot.self_id,
                    remark="检测服务自动退出未授权群组",
                    effective_time=datetime.max,
                )
            await session.commit()
            await init_group_info(session)
            await session.commit()


@scheduler.scheduled_job("cron", hour="*")
async def update_system_database():
    await init_system_database()


@run_preprocessor
async def _(bot: Bot, event: Event, matcher: Matcher) -> None:
    user_id = str(getattr(event, "user_id", ""))
    if user_id in general_config.ignore_user_list:
        raise IgnoredException("用户已被忽略")
    group_id = str(getattr(event, "group_id", ""))

    if (
        # (isinstance(event, GroupIncreaseNoticeEvent) and event.is_tome())
        # or (
        #     isinstance(event, GroupDecreaseNoticeEvent)
        #     and event.sub_type == "kick_me"
        #     and event.is_tome()
        # )
        # or (isinstance(event, GroupBanNoticeEvent))
        # or (isinstance(event, RequestEvent))
        (
            (plugin := matcher.plugin)
            and (
                plugin.module_name.startswith("src.plugins.system_plugins")
                or (
                    (metadata := plugin.metadata)
                    and metadata.extra.get("no_check", False)
                )
            )
        )
        or user_id in memory_cache.super_users
    ):
        return

    if (user := memory_cache.users.get(user_id)) and user.status == UserStatusEnum.BAN:
        if datetime.now() > user.effective_time:
            async with system_session() as session:
                await UserService(
                    UserInfoDAO(session), UserLogDAO(session)
                ).update_status_with_log(
                    user_id,
                    UserStatusEnum.ENABLE,
                    bot.self_id,
                    remark="封禁到期自动解除",
                )
                await session.commit()
                await init_user_info(session)
        elif isinstance(event, MessageEvent) and event.is_tome():
            await bot.send(
                event,
                NoticeBuilder.warning(
                    f"{user_id} 用户处于封禁状态，请在 {datetime.strftime(user.effective_time, '%Y-%m-%d %H:%M:%S')} 后再进行操作 🚫\n"
                    f"用户封禁原因：{user.remark}"
                ),
            )
            raise IgnoredException("封禁用户")

    if (
        group := memory_cache.groups.get(group_id)
    ) and group.status == GroupStatusEnum.BAN:
        if datetime.now() > group.effective_time:
            async with system_session() as session:
                await GroupService(
                    GroupInfoDAO(session), GroupLogDAO(session)
                ).update_status_with_log(
                    group_id,
                    GroupStatusEnum.ENABLE,
                    bot.self_id,
                    remark="封禁到期自动解除",
                    effective_time=datetime.now(),
                )
                await session.commit()
                await session.commit()
                await init_group_info(session)
        elif isinstance(event, MessageEvent) and event.is_tome():
            await bot.send(
                event,
                f"{group_id} 群组处于封禁状态，请在 {datetime.strftime(group.effective_time, '%Y-%m-%d %H:%M:%S')} 后再进行操作 🚫\n"
                f"群组封禁原因：{group.remark}",
            )
            raise IgnoredException("封禁群组")

    if user_id and not await CommonHelper.is_user_valid(user_id):
        raise IgnoredException(f"User {user_id} is invalid, ignore...")
    if group_id and not await CommonHelper.is_group_valid(group_id):
        raise IgnoredException(f"group {group_id} is invalid, ignore...")
