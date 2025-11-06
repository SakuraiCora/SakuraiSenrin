"""
Author: SakuraiCora
Date: 2024-12-30 19:31:20
LastEditors: SakuraiCora
LastEditTime: 2024-12-30 19:32:00
Description: 群组管理模块
"""

from datetime import datetime, timedelta

from nonebot.adapters.onebot.v11.event import GroupMessageEvent, MessageEvent
from nonebot.adapters.onebot.v11.message import Message
from nonebot.params import Arg, CommandArg, Depends
from nonebot.permission import SUPERUSER
from nonebot.plugin import CommandGroup, PluginMetadata
from nonebot.typing import T_State
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache.memory_cache import memory_cache
from src.config.general_config import general_config
from src.database.system.dao import GroupInfoDAO, GroupLogDAO, GroupService
from src.database.system.database import (
    get_session as get_system_session,
)
from src.scripts.init_memory_cache import init_group_info
from src.utils.common_helper import (
    CommonHelper,
    GroupStatusEnum,
)
from src.utils.enums import (
    PluginPermissionEnum,
    TriggerTypeEnum,
)
from src.utils.message_builder import NoticeBuilder

name = "群组管理模块"
description = """
群组管理模块:
  处理群组黑白名单
""".strip()

usage = f"""
📖 ===== {name} =====

命令前缀: #admin.group / #群组管理

1.加入黑名单 🚫
  ban / 禁止 / 拉黑 / 封禁
  示例: #admin.group ban <群组 ID> <remark>
  需要【Senrin】管理员权限

2.解除黑名单 🔓
  unban / 解除 / 加白 / 解封
  示例: #admin.group unban <群组 ID> <remark>
  需要【Senrin】管理员权限

3.授权群组 🔑
  auth / 授权
  示例: #admin.group auth <群组 ID> <remark>
  需要【Senrin】管理员权限

4.取消授权 ❌
  unauth / 取消授权
  示例: #admin.group unauth <群组 ID> <remark>
  需要【Senrin】管理员权限

5.查询状态 🔍
  status / 状态
  示例: #admin.group status <群组 ID>
  需要【Senrin】管理员权限

6.帮助信息 📖
  help / 帮助
  示例: #admin.group help
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

admin_group_manage = admin_command_group.command(
    cmd="group",
    aliases={"群组管理"},
    permission=SUPERUSER,
    priority=5,
    block=False,
)


@admin_group_manage.handle()
async def _(
    event: MessageEvent,
    state: T_State,
    session: AsyncSession = Depends(get_system_session, use_cache=False),
    arg: Message = CommandArg(),
):
    group_info_dao = GroupInfoDAO(session)
    group_log_dao = GroupLogDAO(session)
    group_service = GroupService(group_info_dao, group_log_dao)
    args = arg.extract_plain_text().split() or [""]
    match args[0]:
        case "ban" | "禁止" | "拉黑" | "封禁" if len(args) > 1 and (args[1].isdigit()):
            if (
                group := memory_cache.users.get(args[1])
            ) and datetime.now() < group.effective_time:
                await admin_group_manage.finish(
                    NoticeBuilder.warning("群组已经在封禁状态啦，重复封禁要挨揍哦？")
                )
            state["ban_group_id"] = args[1]
            state["session"] = session
            state["group_service"] = group_service
            

        case "unban" | "解除" | "解封" if len(args) > 1 and (args[1].isdigit()):
            await group_service.update_status_with_log(
                group_id=args[1],
                status=GroupStatusEnum.UNAUTH,
                operator_id=event.get_user_id(),
                remark=None if len(args) < 3 else " ".join(args[2:]),
                effective_time=datetime.now(),
            )
            await session.commit()
            await init_group_info(session)
            await admin_group_manage.finish(
                NoticeBuilder.maintenance(f"已解禁 ID 为 {args[1]} 的群组 🔓")
            )
        case "auth" | "授权":
            group_id = (
                args[1]
                if len(args) > 1 and args[1].isdigit()
                else str(event.group_id)
                if isinstance(event, GroupMessageEvent)
                else ""
            )
            if group := await group_info_dao.get_info_by_group_id(group_id):
                if group.status == GroupStatusEnum.BAN:
                    await admin_group_manage.finish(
                        NoticeBuilder.warning(
                            f"群组 ID 为 {group_id} 的群组已被封禁，无法授权！"
                        )
                    )
                await group_service.update_status_with_log(
                    group_id=group_id,
                    status=GroupStatusEnum.ENABLE,
                    operator_id=event.get_user_id(),
                    remark=None if len(args) < 3 else " ".join(args[2:]),
                    effective_time=datetime.now(),
                )
                await session.commit()
                await init_group_info(session)
                await admin_group_manage.finish(
                    NoticeBuilder.maintenance(f"已授权 ID 为 {group_id} 的群组 🔑")
                )
            else:
                await admin_group_manage.finish("群组 ID 不存在 🔑")
        case "unauth" | "取消授权":
            group_id = (
                args[1]
                if len(args) > 1 and args[1].isdigit()
                else str(event.group_id)
                if isinstance(event, GroupMessageEvent)
                else ""
            )
            if await group_info_dao.get_info_by_group_id(group_id):
                await group_service.update_status_with_log(
                    group_id=group_id,
                    status=GroupStatusEnum.DISABLE,
                    operator_id=event.get_user_id(),
                    remark=None if len(args) < 3 else " ".join(args[2:]),
                    effective_time=datetime.max,
                )
                await session.commit()
                await init_group_info(session)
                await admin_group_manage.finish(
                    NoticeBuilder.maintenance(f"已取消授权 ID 为 {group_id} 的群组 ❌")
                )
            else:
                await admin_group_manage.finish("群组 ID 不存在 ❌")
        case "status" | "状态":
            group_id = (
                args[1]
                if len(args) > 1 and args[1].isdigit()
                else str(event.group_id)
                if isinstance(event, GroupMessageEvent)
                else ""
            )
            if group_info := await group_info_dao.get_info_by_group_id(group_id):
                await admin_group_manage.finish(
                    f"群组 ID 为 {group_id} 的群组状态为 {group_info.status.value} 🔍"
                )
            else:
                await admin_group_manage.finish("群组 ID 不存在 🔍")
        case "help" | "帮助" | _:
            await admin_group_manage.finish(usage)


@admin_group_manage.got(
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
        await admin_group_manage.reject(
            NoticeBuilder.exception("输入的时间格式不正确 🚫")
        )


@admin_group_manage.got("ban_reason", prompt="请输入封禁原因")
async def _(state: T_State, event: MessageEvent, ban_reason: Message = Arg()):
    ban_reason = state["ban_reason"]
    group_service: GroupService = state["group_service"]
    session: AsyncSession = state["session"]
    ban_time: timedelta = state["ban_time"]
    effective_time = datetime.now() + state["ban_time"]
    await group_service.update_status_with_log(
        group_id=state["ban_group_id"],
        status=GroupStatusEnum.BAN,
        operator_id=event.get_user_id(),
        remark=ban_reason.extract_plain_text(),
        effective_time=effective_time,
    )
    await session.commit()
    await init_group_info(session)
    await admin_group_manage.finish(
        f"🚫 已封禁 ID 为 {state['ban_group_id']} 的群组\n"
        f"📋 原因：{ban_reason}\n"
        f"⏳ 封禁时长：{ban_time}"
    )
