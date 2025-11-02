"""
Author: SakuraiCora
Date: 2024-12-30 19:28:22
LastEditors: SakuraiCora
LastEditTime: 2024-12-30 19:28:34
Description: 异常管理模块
"""

from io import BytesIO

from nonebot.adapters.onebot.v11.event import (
    GroupMessageEvent,
    MessageEvent,
    PrivateMessageEvent,
)
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot.params import CommandArg, Depends
from nonebot.permission import SUPERUSER
from nonebot.plugin import CommandGroup, PluginMetadata, on_fullmatch
from nonebot.rule import to_me
from pil_utils import text2image
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.general_config import general_config
from src.database.system.dao import (
    ExceptionInfoDAO,
    ExceptionLogDAO,
    ExceptionReportMessageDAO,
    ExceptionService,
)
from src.database.system.database import (
    get_session as get_system_session,
)
from src.utils.enmus import (
    ExceptionStatusEnum,
    PluginPermissionEnum,
    TriggerTypeEnum,
)
from src.utils.message_builder import AlertTemplate, NoticeBuilder

name = "异常管理模块"
description = """
异常管理模块:
  处理异常
  查看异常详情
  清空异常
""".strip()

usage = f"""
📖 ===== {name} =====

命令前缀: #admin.exception / #异常管理

1.标记异常为已处理 🔍
  示例: 回复 p / processed / 已处理 / 完成
  需要【Senrin】管理员权限

2.标记异常为已忽略 🙈
  示例: 回复 i / ignore / 不处理 / 忽略
  需要【Senrin】管理员权限

3.异常详情 📝
  info <异常ID> / 查看 <异常ID>
  示例: #admin.exception info 123
  需要【Senrin】管理员权限

4.状态查询 🔍
  log / 记录
  示例: #admin.exception log <status>
  需要【Senrin】管理员权限

5.状态更新 🛠️
  set <status> <id> / 设置 <status> <id>
  示例: #admin.exception set <status> <id>
  需要【Senrin】管理员权限

6.清空操作 🗑️
  clear / 清空
  示例: #admin.exception clear
  需要【Senrin】管理员权限

7.帮助信息 📖
  help / 帮助
  示例: #admin.exception help
  需要【Senrin】管理员权限

⚠️ 注意事项:
1. 确保输入的异常 ID 是有效的数字。
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

admin_exception_manage = admin_command_group.command(
    cmd="exception",
    aliases={"异常管理"},
    permission=SUPERUSER,
    priority=5,
    block=False,
)

exception_processed_matcher = on_fullmatch(
    ("p", "processed", "已处理", "完成"),
    ignorecase=True,
    rule=to_me(),
    permission=SUPERUSER,
    priority=5,
    block=False,
)
exception_ignore_matcher = on_fullmatch(
    ("i", "ignore", "忽略", "不处理"),
    ignorecase=True,
    rule=to_me(),
    permission=SUPERUSER,
    priority=5,
    block=False,
)


@exception_processed_matcher.handle()
async def _(
    event: PrivateMessageEvent,
    session: AsyncSession = Depends(get_system_session, use_cache=False),
):
    exception_info_dao = ExceptionInfoDAO(session)
    exception_service = ExceptionService(
        exception_info_dao, ExceptionLogDAO(session), ExceptionReportMessageDAO(session)
    )
    if event.reply and (
        exception_report_message := (
            await exception_service.exception_report_message_dao.get_report_message(
                str(event.reply.message_id)
            )
        )
    ):
        await exception_service.update_status_with_log(
            exception_report_message.exception_info_id,
            event.get_user_id(),
            ExceptionStatusEnum.PROCESSED,
        )
        await exception_ignore_matcher.finish(
            NoticeBuilder.maintenance(
                f"已处理 ID 为 {exception_report_message.exception_info_id} 的异常 ⚙️\n"
                + await exception_info_dao.get_unhandled_info_message()
            ),
            reply_message=True,
        )
    await exception_ignore_matcher.finish()


@exception_ignore_matcher.handle()
async def _(
    event: PrivateMessageEvent,
    session: AsyncSession = Depends(get_system_session, use_cache=False),
):
    exception_info_dao = ExceptionInfoDAO(session)
    exception_service = ExceptionService(
        exception_info_dao, ExceptionLogDAO(session), ExceptionReportMessageDAO(session)
    )
    if event.reply and (
        exception_report_message := (
            await exception_service.exception_report_message_dao.get_report_message(
                str(event.reply.message_id)
            )
        )
    ):
        await exception_service.update_status_with_log(
            exception_report_message.exception_info_id,
            event.get_user_id(),
            ExceptionStatusEnum.IGNORE,
        )
        await exception_ignore_matcher.finish(
            NoticeBuilder.maintenance(
                f"已忽略 ID 为 {exception_report_message.exception_info_id} 的异常 🙈\n"
                + await exception_info_dao.get_unhandled_info_message()
            )
        )
    await exception_ignore_matcher.finish()


@admin_exception_manage.handle()
async def _(
    event: MessageEvent,
    session: AsyncSession = Depends(get_system_session, use_cache=False),
    arg: Message = CommandArg(),
):
    if isinstance(event, GroupMessageEvent):
        await admin_exception_manage.finish(
            NoticeBuilder.warning("请在私聊中使用此命令")
        )
    exception_info_dao = ExceptionInfoDAO(session)
    exception_log_dao = ExceptionLogDAO(session)
    exception_report_message_dao = ExceptionReportMessageDAO(session)
    exception_service = ExceptionService(
        exception_info_dao, exception_log_dao, exception_report_message_dao
    )
    args = arg.extract_plain_text().split() or [""]
    match args[0]:
        case "info" | "查看" if len(args) > 1 and (args[1].isdigit()):
            if exception_info := await exception_info_dao.get_info_by_id(int(args[1])):
                exception_bytes_io = BytesIO()
                text2image(exception_info.traceback_info).save(
                    exception_bytes_io, format="PNG"
                )
                await admin_exception_manage.finish(
                    message=MessageSegment.text(
                        AlertTemplate.build_uncaught_exception_report(
                            exception_id=exception_info.id,
                            pending_nums=await exception_info_dao.get_info_nums_by_status(
                                ExceptionStatusEnum.PENDING
                            ),
                            total_nums=await exception_info_dao.get_info_nums(),
                            user_input=exception_info.user_input,
                            event_log=exception_info.event_log,
                            user_id=exception_info.user_id or "UNKNOWN",
                            group_id=exception_info.group_id or "UNKNOWN",
                            exception_type=exception_info.exception_type,
                            traceback_info="\n".join(
                                exception_info.traceback_info.split("\n")[-2:]
                            ),
                            exception_source=exception_info.exception_source,
                            timestamp=exception_info.create_time,
                        )
                    )
                    + MessageSegment.image(exception_bytes_io),
                )
            else:
                await admin_exception_manage.finish(
                    NoticeBuilder.warning("该异常 ID 不存在")
                )
        case "log" | "记录" if len(args) > 1 and args[1] in (
            "processed",
            "已处理",
            "完成",
        ):
            exception_info_id_list = [
                exception_info.id
                for exception_info in (
                    await exception_info_dao.get_info_by_status(
                        ExceptionStatusEnum.PROCESSED
                    )
                    or []
                )
            ]
            await exception_ignore_matcher.finish(
                NoticeBuilder.maintenance(
                    f"已处理的异常 ID: {'、'.join(map(lambda x: str(x), exception_info_id_list))} ⚙️\n"
                    + await exception_info_dao.get_unhandled_info_message()
                )
            )
        case "log" | "记录" if len(args) > 1 and args[1] in (
            "ignore",
            "不处理",
            "忽略",
        ):
            exception_info_id_list = [
                exception_info.id
                for exception_info in (
                    await exception_info_dao.get_info_by_status(
                        ExceptionStatusEnum.IGNORE
                    )
                    or []
                )
            ]
            await exception_ignore_matcher.finish(
                NoticeBuilder.maintenance(
                    f"已忽略的异常 ID: {'、'.join(map(lambda x: str(x), exception_info_id_list))} 🙈\n"
                    + await exception_info_dao.get_unhandled_info_message()
                )
            )
        case "log" | "记录" if len(args) > 1 and args[1] in ("pending", "待处理"):
            exception_info_id_list = [
                exception_info.id
                for exception_info in (
                    await exception_info_dao.get_info_by_status(
                        ExceptionStatusEnum.PENDING
                    )
                    or []
                )
            ]
            await exception_ignore_matcher.finish(
                NoticeBuilder.maintenance(
                    f"待处理的异常 ID: {'、'.join(map(lambda x: str(x), exception_info_id_list))} 🚧\n"
                    + await exception_info_dao.get_unhandled_info_message()
                )
            )
        case "set" | "设置" if (
            len(args) > 2
            and args[1]
            in (
                "processed",
                "已处理",
                "完成",
            )
            and all(map(lambda x: x.isdigit(), args[2:]))
        ):
            handled_exception_info_id_list = []
            unhandled_exception_info_id_list = []
            for exception_info_id in map(int, args[2:]):
                if exception_info := await exception_info_dao.get_info_by_id(
                    exception_info_id
                ):
                    await exception_service.update_status_with_log(
                        exception_info_id,
                        event.get_user_id(),
                        ExceptionStatusEnum.PROCESSED,
                    )
                    handled_exception_info_id_list.append(exception_info_id)
                else:
                    unhandled_exception_info_id_list.append(exception_info_id)
            await exception_ignore_matcher.finish(
                NoticeBuilder.maintenance(
                    f"已处理 ID 为 {'、'.join(map(lambda x: str(x), handled_exception_info_id_list))} 的异常 ⚙️\n"
                    + f"未找到 ID 为 {'、'.join(map(lambda x: str(x), unhandled_exception_info_id_list))} 的异常\n"
                    + await exception_info_dao.get_unhandled_info_message()
                )
            )
        case "set" | "设置" if (
            len(args) > 2
            and args[1]
            in (
                "ignore",
                "不处理",
                "忽略",
            )
            and all(map(lambda x: x.isdigit(), args[2:]))
        ):
            handled_exception_info_id_list = []
            unhandled_exception_info_id_list = []
            for exception_info_id in map(int, args[2:]):
                if exception_info := await exception_info_dao.get_info_by_id(
                    exception_info_id
                ):
                    await exception_service.update_status_with_log(
                        exception_info_id,
                        event.get_user_id(),
                        ExceptionStatusEnum.IGNORE,
                    )
                    handled_exception_info_id_list.append(exception_info_id)
                else:
                    unhandled_exception_info_id_list.append(exception_info_id)
            await exception_ignore_matcher.finish(
                NoticeBuilder.maintenance(
                    f"已忽略 ID 为 {'、'.join(map(lambda x: str(x), handled_exception_info_id_list))} 的异常 🙈\n"
                    + f"未找到 ID 为 {'、'.join(map(lambda x: str(x), unhandled_exception_info_id_list))} 的异常\n"
                    + await exception_info_dao.get_unhandled_info_message()
                )
            )
        case "set" | "设置" if (
            len(args) > 2
            and args[1]
            in (
                "pending",
                "待处理",
            )
            and all(map(lambda x: x.isdigit(), args[2:]))
        ):
            handled_exception_info_id_list = []
            unhandled_exception_info_id_list = []
            for exception_info_id in map(int, args[2:]):
                if exception_info := await exception_info_dao.get_info_by_id(
                    exception_info_id
                ):
                    await exception_service.update_status_with_log(
                        exception_info_id,
                        event.get_user_id(),
                        ExceptionStatusEnum.PENDING,
                    )
                    handled_exception_info_id_list.append(exception_info_id)
                else:
                    unhandled_exception_info_id_list.append(exception_info_id)
            await exception_ignore_matcher.finish(
                NoticeBuilder.maintenance(
                    f"已标记 ID 为 {'、'.join(map(lambda x: str(x), handled_exception_info_id_list))} 的异常 🚧\n"
                    + f"未找到 ID 为 {'、'.join(map(lambda x: str(x), unhandled_exception_info_id_list))} 的异常\n"
                    + await exception_info_dao.get_unhandled_info_message()
                )
            )
        case "clear" | "清空":
            exception_info_id_list = []
            for exception_info in (
                await exception_info_dao.get_info_by_status(ExceptionStatusEnum.PENDING)
                or []
            ):
                await exception_service.update_status_with_log(
                    exception_info.id, event.get_user_id(), ExceptionStatusEnum.IGNORE
                )
                exception_info_id_list.append(exception_info.id)
            await exception_ignore_matcher.finish(
                NoticeBuilder.maintenance(
                    f"已忽略 ID 为 {'、'.join(map(lambda x: str(x), exception_info_id_list))} 的异常 🙈\n"
                    + await exception_info_dao.get_unhandled_info_message()
                )
            )
        case "help" | "帮助" | _:
            await admin_exception_manage.finish(usage)
