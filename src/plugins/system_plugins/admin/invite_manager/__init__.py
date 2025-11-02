"""
Author: SakuraiCora
Date: 2024-12-30 19:31:20
LastEditors: SakuraiCora
LastEditTime: 2024-12-30 19:32:00
Description: 邀请管理模块
"""

from datetime import datetime

from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, MessageEvent
from nonebot.adapters.onebot.v11.message import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, Depends
from nonebot.permission import SUPERUSER
from nonebot.plugin import CommandGroup, PluginMetadata, on_fullmatch
from nonebot.rule import to_me
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
from src.utils.enmus import (
    GroupStatusEnum,
    InvitationStatusEnum,
    PluginPermissionEnum,
    TriggerTypeEnum,
)
from src.utils.message_builder import NoticeBuilder

name = "邀请管理模块"
description = """
群组管理模块:
  处理群聊邀请事件
""".strip()

usage = f"""
📖 ===== {name} =====

命令前缀: #admin.invite / #邀请管理

1.同意群聊邀请并加入白名单 ✅
  示例: 回复 y / approve / 通过 / 同意 / 批准 
  需要【Senrin】管理员权限

2.拒绝群聊邀请 ❌
  示例: 回复 n / reject / 拒绝 / 驳回 / 反对
  需要【Senrin】管理员权限

3.邀请详情 📝
  info <邀请 ID> / 查看 <邀请 ID>
  示例: #admin.invite info 123
  需要【Senrin】管理员权限

4.状态查询 🔍
  log / 记录
  示例: #admin.invite log <status>
  需要【Senrin】管理员权限

5.状态更新 🛠️
  set <status> <id> / 设置 <status> <id>
  示例: #admin.invite set <status> <id>
  需要【Senrin】管理员权限

6.帮助信息 📖
  help / 帮助
  示例: #admin.invite help
  需要【Senrin】管理员权限

⚠️ 注意事项:
1. 请勿回复无关消息，否则将忽略命令。
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

admin_command_group = CommandGroup("admin")

admin_invite_manage = admin_command_group.command(
    cmd="invite",
    aliases={"邀请管理"},
    permission=SUPERUSER,
    priority=5,
    block=False,
)

invite_approve_reply_matcher = on_fullmatch(
    ("y", "approve", "通过", "同意", "批准"),
    ignorecase=True,
    rule=to_me(),
    permission=SUPERUSER,
    priority=5,
    block=False,
)
invite_reject_reply_matcher = on_fullmatch(
    ("n", "reject", "拒绝", "驳回", "反对"),
    ignorecase=True,
    rule=to_me(),
    permission=SUPERUSER,
    priority=5,
    block=False,
)


@invite_approve_reply_matcher.handle()
async def approve_invitation(
    bot: Bot,
    event: MessageEvent,
    matcher: Matcher,
    session: AsyncSession = Depends(get_system_session, use_cache=False),
):
    invitation_info_dao = InvitationInfoDAO(session)
    invitation_service = InvitationService(
        invitation_info_dao,
        InvitationLogDAO(session),
        InvitationReportMessageDAO(session),
    )
    group_info_dao = GroupInfoDAO(session)
    group_log_dao = GroupLogDAO(session)
    group_service = GroupService(group_info_dao, group_log_dao)
    if event.reply and (
        invitation_report_message := (
            await invitation_service.invitation_report_message_dao.get_report_message(
                str(event.reply.message_id)
            )
        )
    ):
        if (
            invitation_report_message.invitation_info.status
            != InvitationStatusEnum.PENDING
        ):
            await matcher.finish(
                NoticeBuilder.warning(
                    f"邀请 ID 为 {invitation_report_message.invitation_info_id} 的邀请已被管理员 {invitation_report_message.invitation_info.operator_id} 处理，请勿重复操作。"
                )
            )
        if flag := invitation_report_message.invitation_info.flag:
            await bot.set_group_add_request(
                flag=flag,
                sub_type=invitation_report_message.invitation_info.sub_type,
                approve=True,
            )
        await session.commit()
        await init_group_info(session)

        await invitation_service.update_status_with_log(
            invitation_report_message.invitation_info_id,
            event.get_user_id(),
            InvitationStatusEnum.ACCEPT,
        )
        await group_service.update_status_with_log(
            group_id=invitation_report_message.invitation_info.group_id,
            status=GroupStatusEnum.ENABLE,
            operator_id=event.get_user_id(),
            remark="同意邀请自动授权群组",
            effective_time=datetime.now(),
        )
        await session.commit()
        await init_group_info(session)
        await matcher.finish(
            NoticeBuilder.maintenance(
                f"已同意 ID 为 {invitation_report_message.invitation_info_id} 的群聊邀请 ✅\n"
                + await invitation_info_dao.get_unhandled_info_message()
            ),
            reply_message=True,
        )
    else:
        await matcher.finish()


@invite_reject_reply_matcher.handle()
async def reject_invitation(
    bot: Bot,
    event: MessageEvent,
    matcher: Matcher,
    session: AsyncSession = Depends(get_system_session, use_cache=False),
):
    invitation_info_dao = InvitationInfoDAO(session)
    invitation_service = InvitationService(
        invitation_info_dao,
        InvitationLogDAO(session),
        InvitationReportMessageDAO(session),
    )

    if event.reply and (
        invitation_report_message := (
            await invitation_service.invitation_report_message_dao.get_report_message(
                str(event.reply.message_id)
            )
        )
    ):
        if (
            invitation_report_message.invitation_info.status
            != InvitationStatusEnum.PENDING
        ):
            await matcher.finish(
                NoticeBuilder.warning(
                    f"邀请 ID 为 {invitation_report_message.invitation_info_id} 的邀请已被管理员 {invitation_report_message.invitation_info.operator_id} 处理，请勿重复操作。"
                )
            )
        if flag := invitation_report_message.invitation_info.flag:
            await bot.set_group_add_request(
                flag=flag,
                sub_type=invitation_report_message.invitation_info.sub_type,
                approve=False,
            )
        elif (
            group_id := invitation_report_message.invitation_info.group_id
        ) in memory_cache.groups:
            group_info_dao = GroupInfoDAO(session)
            group_log_dao = GroupLogDAO(session)
            group_service = GroupService(group_info_dao, group_log_dao)
            await bot.set_group_leave(group_id=int(group_id))
            await group_service.update_status_with_log(
                group_id=group_id,
                status=GroupStatusEnum.LEAVE,
                operator_id=event.get_user_id(),
                remark="拒绝群聊邀请自动退群",
                effective_time=datetime.max,
            )
            await session.commit()
            await init_group_info(session)
        await invitation_service.update_status_with_log(
            invitation_report_message.invitation_info_id,
            event.get_user_id(),
            InvitationStatusEnum.REJECT,
        )
        await session.commit()
        await init_group_info(session)
        await matcher.finish(
            NoticeBuilder.maintenance(
                f"已拒绝 ID 为 {invitation_report_message.invitation_info_id} 的群聊邀请 ❌\n"
                + await invitation_info_dao.get_unhandled_info_message()
            ),
            reply_message=True,
        )
    else:
        await matcher.finish()


@admin_invite_manage.handle()
async def _(
    bot: Bot,
    event: MessageEvent,
    matcher: Matcher,
    session: AsyncSession = Depends(get_system_session, use_cache=False),
    arg: Message = CommandArg(),
):
    if isinstance(event, GroupMessageEvent):
        await admin_invite_manage.finish(NoticeBuilder.warning("请在私聊中使用此命令"))
    invitation_info_dao = InvitationInfoDAO(session)
    invitation_log_dao = InvitationLogDAO(session)
    invitation_report_message_dao = InvitationReportMessageDAO(session)
    invitation_service = InvitationService(
        invitation_info_dao, invitation_log_dao, invitation_report_message_dao
    )
    group_info_dao = GroupInfoDAO(session)
    group_log_dao = GroupLogDAO(session)
    group_service = GroupService(group_info_dao, group_log_dao)
    args = arg.extract_plain_text().split() or [""]
    match args[0]:
        case "info" | "查看" if len(args) > 1 and (args[1].isdigit()):
            if invitation_info := await invitation_info_dao.get_info_by_id(
                int(args[1])
            ):
                await matcher.finish(
                    NoticeBuilder.success(
                        f"邀请信息\n"
                        f"群组 ID: {invitation_info.group_id}\n"
                        f"群组名称: {invitation_info.group_name}\n"
                        f"邀请者 ID: {invitation_info.inviter_id}\n"
                        f"邀请 flag: {invitation_info.flag}\n"
                        f"创建时间: {invitation_info.create_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"更新时间: {invitation_info.update_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        + await invitation_info_dao.get_unhandled_info_message()
                    )
                )
            else:
                await matcher.finish(NoticeBuilder.warning("该邀请 ID 不存在"))
        case "log" | "记录" if len(args) > 1 and args[1] in (
            "pending",
            "待处理",
        ):
            invitation_info_id_list = [
                invitation_info.id
                for invitation_info in (
                    await invitation_info_dao.get_info_by_status(
                        InvitationStatusEnum.PENDING
                    )
                    or []
                )
            ]
            await matcher.finish(
                NoticeBuilder.maintenance(
                    f"待处理的邀请 ID: {'、'.join(map(lambda x: str(x), invitation_info_id_list))} 🚧\n"
                    + await invitation_info_dao.get_unhandled_info_message()
                )
            )
        case "set" | "设置" if (
            len(args) > 2
            and args[1]
            in (
                "accept",
                "同意",
                "通过",
                "批准",
            )
            and all(map(lambda x: x.isdigit(), args[2:]))
        ):
            handled_invitation_info_id_list = []
            unhandled_invitation_info_id_list = []
            for invitation_info_id in map(int, args[2:]):
                if (
                    invitation_info := await invitation_info_dao.get_info_by_id(
                        invitation_info_id
                    )
                ) and invitation_info.status == InvitationStatusEnum.PENDING:
                    if flag := invitation_info.flag:
                        await bot.set_group_add_request(
                            flag=flag,
                            sub_type=invitation_info.sub_type,
                            approve=True,
                        )
                    await invitation_service.update_status_with_log(
                        invitation_info_id,
                        event.get_user_id(),
                        InvitationStatusEnum.ACCEPT,
                    )
                    await group_service.update_status_with_log(
                        group_id=invitation_info.group_id,
                        status=GroupStatusEnum.ENABLE,
                        operator_id=event.get_user_id(),
                        remark="同意邀请自动授权群组",
                        effective_time=datetime.now(),
                    )
                    await session.commit()
                    await init_group_info(session)
                    handled_invitation_info_id_list.append(invitation_info_id)
                else:
                    unhandled_invitation_info_id_list.append(invitation_info_id)
            await matcher.finish(
                NoticeBuilder.maintenance(
                    f"已同意 ID 为 {'、'.join(map(lambda x: str(x), handled_invitation_info_id_list))} 的邀请 ✅\n"
                    + f"未找到或未处理 ID 为 {'、'.join(map(lambda x: str(x), unhandled_invitation_info_id_list))} 的邀请\n"
                    + await invitation_info_dao.get_unhandled_info_message()
                )
            )
        case "set" | "设置" if (
            len(args) > 2
            and args[1]
            in (
                "reject",
                "拒绝",
                "驳回",
                "反对",
            )
            and all(map(lambda x: x.isdigit(), args[2:]))
        ):
            handled_invitation_info_id_list = []
            unhandled_invitation_info_id_list = []
            for invitation_info_id in map(int, args[2:]):
                if (
                    invitation_info := await invitation_info_dao.get_info_by_id(
                        invitation_info_id
                    )
                ) and invitation_info.status == InvitationStatusEnum.PENDING:
                    if flag := invitation_info.flag:
                        await bot.set_group_add_request(
                            flag=flag,
                            sub_type=invitation_info.sub_type,
                            approve=False,
                        )
                    elif (group_id := invitation_info.group_id) in memory_cache.groups:
                        group_info_dao = GroupInfoDAO(session)
                        group_log_dao = GroupLogDAO(session)
                        group_service = GroupService(group_info_dao, group_log_dao)
                        await bot.set_group_leave(group_id=int(group_id))
                        await group_service.update_status_with_log(
                            group_id=group_id,
                            status=GroupStatusEnum.LEAVE,
                            operator_id=event.get_user_id(),
                            remark="拒绝群聊邀请自动退群",
                            effective_time=datetime.max,
                        )
                        await session.commit()
                        await init_group_info(session)
                    await invitation_service.update_status_with_log(
                        invitation_info_id,
                        event.get_user_id(),
                        InvitationStatusEnum.REJECT,
                    )
                    handled_invitation_info_id_list.append(invitation_info_id)
                else:
                    unhandled_invitation_info_id_list.append(invitation_info_id)
            await matcher.finish(
                NoticeBuilder.maintenance(
                    f"已拒绝 ID 为 {'、'.join(map(lambda x: str(x), handled_invitation_info_id_list))} 的邀请 ❌\n"
                    + f"未找到或未处理 ID 为 {'、'.join(map(lambda x: str(x), unhandled_invitation_info_id_list))} 的邀请\n"
                    + await invitation_info_dao.get_unhandled_info_message()
                )
            )
        case "help" | "帮助" | _:
            await matcher.finish(usage)
