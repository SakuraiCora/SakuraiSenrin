"""
Author: SakuraiCora
Date: 2024-12-28 14:41:29
LastEditors: SakuraiCora
LastEditTime: 2024-12-29 21:31:54
Description: 群组邀请处理
"""

import asyncio
import datetime
import random

from nonebot import on_notice
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.event import (
    GroupIncreaseNoticeEvent,
    GroupRequestEvent,
)
from nonebot.matcher import Matcher
from nonebot.params import Depends
from nonebot.plugin import PluginMetadata, on_request
from nonebot.rule import is_type, to_me
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache.memory_cache import memory_cache
from src.config.general_config import general_config
from src.database.system.dao import (
    GroupInfoDAO,
    GroupLogDAO,
    GroupService,
    InvitationInfoDAO,
    InvitationLogDAO,
    InvitationReportMessageDAO,
    InvitationService,
)
from src.database.system.database import (
    get_session as get_system_session,
)
from src.scripts.init_memory_cache import init_group_info
from src.utils.enums import (
    GroupStatusEnum,
    InvitationStatusEnum,
    PluginPermissionEnum,
    TriggerTypeEnum,
)
from src.utils.message_builder import AlertTemplate

name = "群组邀请处理"
description = """
群组邀请处理:
  邀请事件上报

""".strip()

usage = """

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


async def is_invite_request(event: GroupRequestEvent) -> bool:
    return event.sub_type == "invite"


# async def is_valid_increase_event(event: GroupIncreaseNoticeEvent) -> bool: ...


# async def is_invalid_group(event: GroupIncreaseNoticeEvent) -> bool:
#     return not await CommonHelper.is_group_valid(event.group_id.__str__())


# async def is_valid_invite_request(event: GroupRequestEvent) -> bool:
#     return event.user_id == event.self_id


@on_notice(priority=5, rule=is_type(GroupIncreaseNoticeEvent) & to_me()).handle()
@on_request(priority=5, rule=is_type(GroupRequestEvent) & is_invite_request).handle()
async def _(
    bot: Bot,
    event: GroupRequestEvent | GroupIncreaseNoticeEvent,
    matcher: Matcher,
    session: AsyncSession = Depends(get_system_session, use_cache=False),
):
    group_info_dao = GroupInfoDAO(session)
    group_log_dao = GroupLogDAO(session)
    group_service = GroupService(group_info_dao, group_log_dao)

    inviter_id = (
        event.user_id.__str__()
        if isinstance(event, GroupRequestEvent)
        else event.operator_id.__str__()
    )

    for superuser in memory_cache.super_users:
        await bot.send_private_msg(
            user_id=int(superuser),
            message=event.json(),
        )
        await asyncio.sleep(1)

    if (
        group := await group_info_dao.get_info_by_group_id(event.group_id.__str__())
    ) and (group.status == GroupStatusEnum.BAN):
        await bot.set_group_leave(group_id=event.group_id) if isinstance(
            event, GroupIncreaseNoticeEvent
        ) else await bot.set_group_add_request(
            flag=event.flag,
            sub_type=event.sub_type,
            approve=False,
        )
        await bot.send_private_msg(
            user_id=int(inviter_id),
            message=(
                "🚫 自动拒绝\n"
                f"群组：{event.group_id}\n"
                f"邀请者 ID: {inviter_id}\n"
                "群聊已被拉黑，凛凛不想加入此群组。\n"
                f"如有异议，请及时加入反馈群「{general_config.support_group_id}」并联系群管【加入白名单】"
            ),
        )
        for superuser in memory_cache.super_users:
            await bot.send_private_msg(
                user_id=int(superuser),
                message=AlertTemplate.build_tip_notification(
                    event_name="自动拒绝",
                    event_details=(
                        f"黑名单群组发起邀请，已自动拒绝\n群组：{event.group_id}"
                    ),
                ),
            )
            await asyncio.sleep(1)
        await matcher.finish()

    if isinstance(event, GroupIncreaseNoticeEvent):  # FIXME: 可能存在竞争问题
        if group:
            group_id = group.group_id
            group_name = group.group_name
            status = group.status
        else:
            group_id = event.group_id.__str__()
            group_name = (await bot.get_group_info(group_id=event.group_id)).get(
                "group_name"
            )
            status = GroupStatusEnum.UNAUTH

        await group_service.upsert_info_with_log(
            group_id=group_id,
            group_name=group_name,
            operator_id=event.operator_id.__str__(),
            status=status,
            remark="邀请加群自动记录群信息",
            effective_time=datetime.datetime.now(),
        )
        await session.commit()
        await init_group_info(session)
    invitation_info_dao = InvitationInfoDAO(session)
    invitation_service = InvitationService(
        invitation_info_dao,
        InvitationLogDAO(session),
        InvitationReportMessageDAO(session),
    )

    group_id = event.group_id.__str__()
    group_name: str | None = (await bot.get_group_info(group_id=event.group_id)).get(
        "group_name"
    )

    flag = event.flag if isinstance(event, GroupRequestEvent) else None
    sub_type = event.sub_type
    operator_id = event.self_id.__str__()
    status = InvitationStatusEnum.PENDING

    invitation_info, _ = await invitation_service.upsert_info_with_log(
        group_id=group_id,
        group_name=group_name,
        inviter_id=inviter_id,
        flag=flag,
        sub_type=sub_type,
        operator_id=operator_id,
        status=status,
    )

    await bot.send_private_msg(
        user_id=int(inviter_id),
        message=(
            "📩 谢谢您对凛凛发起的邀请 ^_^\n"
            f"群组 ID: {group_id}\n"
            f"群组名称: {group_name}\n"
            f"邀请者 ID: {inviter_id}\n\n"
            "======重要提示======\n"
            f"请及时加入反馈群「{general_config.support_group_id}」并联系群管【加入白名单】\n"
            f"请及时加入反馈群「{general_config.support_group_id}」并联系群管【加入白名单】\n"
            f"请及时加入反馈群「{general_config.support_group_id}」并联系群管【加入白名单】\n"
            "===================\n\n"
            "否则凛凛将无法在您的群聊中发送消息哦~\n"
            "另外，任何形式的禁言是不被允许的！如需要凛凛退出群聊，切勿直接移除，还请发送【#remove】指令。\n"
            "祝旅途愉快，每一种境遇都是命运的付赠品，还请好好珍惜，也希望能和凛凛相处的开心。\n"
            "—— 来自 SakuraiSenrin (•◡•) /💕"
        ),
    )

    report_message = (
        f"📩 新的邀请事件通知\n"
        f"群组 ID: {group_id}\n"
        f"群组名称: {group_name}\n"
        f"邀请者 ID: {inviter_id}\n"
        f"邀请 flag: {flag}\n\n"
        "回复 y 以同意，发送 n 以拒绝。\n"
        + await invitation_info_dao.get_unhandled_info_message()
    )
    for super_user_id in memory_cache.super_users:
        message_id: str | None = str(
            (
                await bot.send_private_msg(
                    user_id=int(super_user_id),
                    message=AlertTemplate.build_tip_notification(
                        matcher.plugin_name, report_message
                    ),
                )
            )["message_id"]
        )
        await invitation_service.relate_with_report_message_id(
            report_message_id=message_id,
            invitation_info=invitation_info,
        )
        await asyncio.sleep(random.randint(1, 3))
