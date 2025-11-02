from datetime import datetime

from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, PrivateMessageEvent
from nonebot.adapters.onebot.v11.message import Message
from nonebot.matcher import Matcher
from nonebot.params import Arg, Depends
from nonebot.plugin import PluginMetadata, on_command
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache.memory_cache import memory_cache
from src.database.system.dao import (
    GroupInfoDAO,
    GroupLogDAO,
    GroupService,
    InvitationInfoDAO,
)
from src.database.system.database import get_session
from src.utils.enmus import (
    GroupStatusEnum,
    PluginPermissionEnum,
    TriggerTypeEnum,
)
from src.utils.message_builder import AlertTemplate, NoticeBuilder

name = "退群"
description = """
退群:
  退出群聊
""".strip()

usage = f"""
📖 ===== {name} =====

命令前缀: #remove / #退群

退群 👋
  退出群聊
""".strip()

__plugin_meta__ = PluginMetadata(
    name=name,
    description=description,
    usage=usage,
    extra={
        "author": "SakuraiCora",
        "version": "0.1.0",
        "trigger": TriggerTypeEnum.ACTIVE,
        "permission": PluginPermissionEnum.EVERYONE,
        "no_check": True,
    },
)

remove_matcher = on_command("remove", aliases={"退群"}, priority=1, block=True)


@remove_matcher.handle()
async def remove_handle(
    bot: Bot,
    matcher: Matcher,
    event: GroupMessageEvent | PrivateMessageEvent,
    session: AsyncSession = Depends(get_session, use_cache=False),
):
    if isinstance(event, PrivateMessageEvent):
        await matcher.finish(NoticeBuilder.warning("请到群聊中发起退群请求。"))
    if not (
        (
            await bot.get_group_member_info(
                group_id=event.group_id, user_id=event.user_id
            )
        )["role"]
        in ["owner", "admin"]
        or (
            (
                invitation_info := (
                    await InvitationInfoDAO(session).get_info_by_group_id(
                        event.group_id.__str__()
                    )
                )
            )
            and invitation_info.inviter_id == event.get_user_id()
        )
    ):
        await matcher.finish(
            NoticeBuilder.exception(
                "您没有权限发起退群请求，仅群主、管理员、邀请者可以发起。"
            )
        )


@remove_matcher.got(
    "confirm", prompt="是否确认退群？输入 y 或 yes 确认，其他内容取消："
)
async def remove_confirm(
    matcher: Matcher,
    confirm: Message = Arg(),
):
    if confirm.extract_plain_text().lower() in ("y", "yes"):
        matcher.set_arg("confirm", Message("y"))
    else:
        await matcher.finish("已取消退群。")


@remove_matcher.got(
    "reason",
    prompt="请输入退群原因：",
)
async def remove_reason(
    bot: Bot,
    event: GroupMessageEvent,
    matcher: Matcher,
    session: AsyncSession = Depends(get_session, use_cache=False),
    reason: Message = Arg(),
):
    await matcher.send(
        NoticeBuilder.farewell(f"走了走了，再见啦！原因：{reason.extract_plain_text()}")
    )
    await bot.set_group_leave(
        group_id=event.group_id,
    )
    await GroupService(
        GroupInfoDAO(session), GroupLogDAO(session)
    ).update_status_with_log(
        event.group_id.__str__(),
        GroupStatusEnum.LEAVE,
        event.get_user_id(),
        remark="用户主动退群" + reason.extract_plain_text(),
        effective_time=datetime.max,
    )
    report_message = (
        "👋 退群提醒\n"
        f"群组 ID: {event.group_id}\n"
        f"群组名称: {(await bot.get_group_info(group_id=event.group_id))['group_name']}\n"
        f"退群者 ID: {event.user_id}\n"
        f"退群原因: {reason.extract_plain_text()}\n"
    )
    for superuser in memory_cache.super_users:
        await bot.send_private_msg(
            user_id=int(superuser),
            message=AlertTemplate.build_tip_notification(
                matcher.plugin_name, report_message
            ),
        )
    await matcher.finish()
