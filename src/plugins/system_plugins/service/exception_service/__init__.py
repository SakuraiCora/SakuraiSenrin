"""
Author: SakuraiCora
Date: 2024-12-30 19:57:04
LastEditors: SakuraiCora
LastEditTime: 2024-12-30 19:59:19
Description: 异常处理
"""

import traceback
from datetime import datetime
from io import BytesIO, StringIO
from typing import Optional

from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.event import Event
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot.matcher import Matcher
from nonebot.message import run_postprocessor
from nonebot.params import Depends
from nonebot.plugin import PluginMetadata
from pil_utils import text2image
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache.memory_cache import memory_cache
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
from src.utils.message_builder import AlertTemplate

name = "异常处理服务"
description = """
异常处理服务:
  记录异常信息
  发送异常报告
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
    bot: Bot,
    event: Event,
    matcher: Matcher,
    exception: Optional[Exception],
    session: AsyncSession = Depends(get_system_session, use_cache=False),
) -> None:
    if exception:
        try:
            user_input = event.get_message().extract_plain_text()
        except Exception:
            user_input = "UNKNOWN"
        event_log = event.get_log_string()
        user_id = str(getattr(event, "user_id", "UNKNOWN"))
        group_id = str(getattr(event, "group_id", "UNKNOWN"))
        exception_type = type(exception).__name__
        exception_source = matcher.module_name or "UNKNOWN"
        create_time = datetime.now()
        with StringIO() as f:
            traceback.print_tb(exception.__traceback__, file=f)
            traceback_info_full = f.getvalue()
            traceback_info_str = "\n".join(traceback_info_full.split("\n")[-2:])
            traceback_info_bytes = BytesIO()
            text2image(traceback_info_full).save(traceback_info_bytes, format="PNG")

        exception_info_dao = ExceptionInfoDAO(session)
        exception_service = ExceptionService(
            exception_info_dao,
            ExceptionLogDAO(session),
            ExceptionReportMessageDAO(session),
        )
        exception_info, _ = await exception_service.upsert_info_with_log(
            user_input=user_input,
            event_log=event_log,
            user_id=user_id,
            group_id=group_id,
            exception_type=exception_type,
            traceback_info=traceback_info_full,
            exception_source=exception_source,
            status=ExceptionStatusEnum.PENDING,
            operator_id=str(event.self_id),
        )

        for super_user_id in memory_cache.super_users:
            report_message_id: str | None = str(
                (
                    await bot.send_private_msg(
                        user_id=int(super_user_id),
                        message=MessageSegment.text(
                            AlertTemplate.build_uncaught_exception_report(
                                exception_id=exception_info.id,
                                pending_nums=await exception_info_dao.get_info_nums_by_status(
                                    ExceptionStatusEnum.PENDING
                                ),
                                total_nums=await exception_info_dao.get_info_nums(),
                                user_input=user_input,
                                event_log=event_log,
                                user_id=user_id,
                                group_id=group_id,
                                exception_type=exception_type,
                                traceback_info=traceback_info_str,
                                exception_source=exception_source,
                                timestamp=create_time,
                            )
                        )
                        + MessageSegment.image(traceback_info_bytes),
                    )
                ).get("message_id")
            )
            await exception_service.relate_with_report_message_id(
                report_message_id=report_message_id,
                exception_info=exception_info,
            )

        await bot.send(
            event=event,
            message=AlertTemplate.build_exception_notification(
                user_input=user_input,
                exception_type=exception_type,
                help_command=f"#help {matcher.plugin_name}",
                timestamp=create_time,
            ),
        )
