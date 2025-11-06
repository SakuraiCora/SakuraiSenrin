"""
Author: SakuraiCora
Date: 2024-12-30 19:32:24
LastEditors: SakuraiCora
LastEditTime: 2024-12-30 19:32:28
Description: 好友管理模块
"""

from datetime import datetime, timedelta

from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.adapters.onebot.v11.message import Message
from nonebot.params import Arg, CommandArg, Depends
from nonebot.permission import SUPERUSER
from nonebot.plugin import CommandGroup, PluginMetadata
from nonebot.typing import T_State
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache.memory_cache import memory_cache
from src.config.general_config import general_config
from src.database.system.dao import UserInfoDAO, UserLogDAO, UserService
from src.database.system.database import (
    get_session as get_system_session,
)
from src.scripts.init_memory_cache import init_user_info
from src.utils.common_helper import (
    CommonHelper,
)
from utils.enums import (
    PluginPermissionEnum,
    TriggerTypeEnum,
    UserStatusEnum,
)
from src.utils.message_builder import NoticeBuilder

name = "好友管理模块"
description = """
好友管理模块:
  处理好友黑白名单
""".strip()

usage = f"""
📖 ===== {name} =====

命令前缀: #admin.user / #用户管理

1.加入黑名单 🚫
  ban / 禁止 / 拉黑 / 封禁
  示例: #admin.user ban <用户 ID> <remark>
  需要【Senrin】管理员权限

2.解除黑名单 🔓
  unban / 解除 / 加白 / 解封
  示例: #admin.user unban <用户 ID> <remark>
  需要【Senrin】管理员权限

3.查询状态 🔍
  status / 状态
  示例: #admin.user status <用户 ID>
  需要【Senrin】管理员权限

4.帮助信息 📖
  help / 帮助
  示例: #admin.user help
  需要【Senrin】管理员权限

⚠️ 注意事项:
1. 确保输入的群组 ID 是有效的数字。
2. 如果某个指令没有返回结果，请检查异常数据是否存在。
3. 如需进一步支持，请联系管理员，或加入反馈群「{general_config.support_group_id}」💬。
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

admin_command_group = CommandGroup("admin")

admin_user_manage = admin_command_group.command(
    cmd="user",
    aliases={"用户管理"},
    permission=SUPERUSER,
    priority=5,
    block=False,
)


@admin_user_manage.handle()
async def _(
    event: MessageEvent,
    state: T_State,
    session: AsyncSession = Depends(get_system_session, use_cache=False),
    arg: Message = CommandArg(),
):
    user_info_dao = UserInfoDAO(session)
    user_log_dao = UserLogDAO(session)
    user_service = UserService(user_info_dao, user_log_dao)
    args = arg.extract_plain_text().split() or [""]
    match args[0]:
        case "ban" | "禁止" | "拉黑" | "封禁" if len(args) > 1 and (args[1].isdigit()):
            user = memory_cache.users.get(args[1])
            if not user:
                await admin_user_manage.finish(
                    NoticeBuilder.warning(
                        "这位用户还没有和凛凛聊过哦，随意封禁会挨揍哦？"
                    )
                )
            if args[1] in memory_cache.super_users:
                await admin_user_manage.finish(
                    NoticeBuilder.exception("不能封禁超级用户 🚫")
                )
            if (
                user := memory_cache.users.get(args[1])
            ) and datetime.now() < user.effective_time:
                await admin_user_manage.finish(
                    NoticeBuilder.warning("用户已经在封禁状态啦，重复封禁要挨揍哦？")
                )
            state["ban_user_id"] = args[1]
            state["session"] = session
            state["user_service"] = user_service

        case "unban" | "解除" | "加白" | "解封" if len(args) > 1 and (
            args[1].isdigit()
        ):
            await user_service.update_status_with_log(
                user_id=args[1],
                status=UserStatusEnum.ENABLE,
                operator_id=event.get_user_id(),
                remark=None if len(args) < 3 else " ".join(args[2:]),
            )
            await user_service.update_effective_time_with_log(
                user_id=args[1],
                effective_time=datetime.now(),
                operator_id=event.get_user_id(),
            )
            await init_user_info(session)
            await admin_user_manage.finish(
                NoticeBuilder.success(f"已解禁 ID 为 {args[1]} 的用户 🔓")
            )
        case "status" | "状态":
            user_id = (
                args[1] if len(args) > 2 and args[1].isdigit() else str(event.user_id)
            )
            if user_info := await user_info_dao.get_info_by_user_id(user_id):
                await admin_user_manage.finish(
                    f"用户 ID 为 {user_id} 的用户状态为 {user_info.status.value} 🔍"
                )
            else:
                await admin_user_manage.finish("用户 ID 不存在 🔍")
        case "help" | "帮助" | _:
            await admin_user_manage.finish(usage)


@admin_user_manage.got(
    "ban_time_string",
    prompt=(
        "⏳ 请输入封禁时间\n"
        "格式：d->天，h->小时，m->分钟，s->秒\n"
        "示例：1d2h3m4s 表示 1天2小时3分钟4秒 🕒\n"
        "✨ 支持任意组合，如：3h45m 或 30m。"
    ),
)
async def _(state: T_State, ban_time_string: Message = Arg()):
    try:
        state["ban_time"] = CommonHelper.time_to_timedelta(
            ban_time_string.extract_plain_text()
        )
    except ValueError:
        await admin_user_manage.reject(
            NoticeBuilder.exception("输入的时间格式不正确 🚫")
        )


@admin_user_manage.got("ban_reason", prompt="请输入封禁原因")
async def _(state: T_State, event: MessageEvent, ban_reason: Message = Arg()):
    ban_reason = state["ban_reason"]
    user_service: UserService = state["user_service"]
    session: AsyncSession = state["session"]
    ban_time: timedelta = state["ban_time"]
    await user_service.update_status_with_log(
        user_id=state["ban_user_id"],
        status=UserStatusEnum.BAN,
        operator_id=event.get_user_id(),
        remark=ban_reason.extract_plain_text(),
    )
    await user_service.update_effective_time_with_log(
        user_id=state["ban_user_id"],
        effective_time=datetime.now() + state["ban_time"],
        operator_id=event.get_user_id(),
    )
    await session.commit()
    await init_user_info(session)
    await admin_user_manage.finish(
        f"🚫 已封禁 ID 为 {state['ban_user_id']} 的用户\n"
        f"📋 原因：{ban_reason}\n"
        f"⏳ 封禁时长：{ban_time}"
    )
