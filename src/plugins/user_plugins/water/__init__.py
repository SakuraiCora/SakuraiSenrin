from datetime import datetime

from nonebot import get_driver
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.event import (
    GroupMessageEvent,
    MessageEvent,
)
from nonebot.params import Depends
from nonebot.plugin import PluginMetadata, on_command, on_message
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.general_config import general_config
from src.plugins.user_plugins.water.config import water_config
from src.plugins.user_plugins.water.water_dao import WaterInfoDAO
from src.plugins.user_plugins.water.water_database import get_session, init_water_info
from src.plugins.user_plugins.water.water_process import (
    generate_water_rank_image_by_pillow,
    generate_water_rank_image_by_playwright,
)
from src.utils.enmus import PluginPermissionEnum, TriggerTypeEnum
from src.utils.message_builder import NoticeBuilder

name = "吹水记录"
description = """
吹水记录模块
""".strip()

usage = f"""
📖 ===== {name} =====

命令前缀: 为了简单一点就不写了

1.查看用户当天的吹水记录 
  #我有多水
  #我在群里有多水

2.查看群聊当天的水王排行榜
  #水王排行榜

⚠️ 注意事项:
1. 时间按照 00:00 开始计数。
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
        "permission": PluginPermissionEnum.EVERYONE,
    },
)

self_global_water_status = on_command("我有多水", priority=5, block=True)
self_group_water_status = on_command(
    "我在本群有多水", aliases={"我在群里有多水"}, priority=5, block=True
)
water_rank = on_command("水王排行榜", aliases={"水王"}, priority=5, block=True)

driver = get_driver()


@driver.on_startup
async def _():
    await init_water_info()


@water_rank.handle()
async def _(
    bot: Bot,
    event: GroupMessageEvent,
    session: AsyncSession = Depends(get_session, use_cache=False),
):
    await water_rank.send(NoticeBuilder.info("正在生成图片，请稍后..."))
    if water_config.use_playwright:
        await water_rank.finish(
            await generate_water_rank_image_by_playwright(
                event.group_id.__str__(),
                await WaterInfoDAO(session).get_water_info_by_time(
                    datetime.now().replace(hour=0, minute=0, second=0)
                ),
            )
        )
    else:
        await water_rank.finish(
            await generate_water_rank_image_by_pillow(
                bot,
                event.group_id.__str__(),
                await WaterInfoDAO(session).get_water_info_by_time(
                    datetime.now().replace(hour=0, minute=0, second=0)
                ),
            )
        )


@self_global_water_status.handle()
async def _(
    event: MessageEvent,
    session: AsyncSession = Depends(get_session, use_cache=False),
):
    (
        user_count,
        user_rank,
        beaten_users,
        user_percentage,
    ) = await WaterInfoDAO(session).get_user_global_stats(
        event.get_user_id(), datetime.now().replace(hour=0, minute=0, second=0)
    )
    await self_global_water_status.finish(
        f"好耶，让我看见你有多水！\n"
        f"嗯~你的在所有用户中排名是 {user_rank}\n"
        f"一共发言 {user_count or 0} 次\n"
        f"占比 {user_percentage}%\n"
        f"击败了 {beaten_users} 位用户！"
    )


@self_group_water_status.handle()
async def _(
    event: GroupMessageEvent,
    session: AsyncSession = Depends(get_session, use_cache=False),
):
    (
        user_count,
        user_rank,
        beaten_users,
        user_percentage,
    ) = await WaterInfoDAO(session).get_user_group_stats(
        event.get_user_id(),
        event.group_id.__str__(),
        datetime.now().replace(hour=0, minute=0, second=0),
    )
    await self_group_water_status.finish(
        f"好耶，让我看见你有多水！\n"
        f"嗯~你的在本群的排名是 {user_rank}\n"
        f"一共发言 {user_count or 0} 次\n"
        f"占比 {user_percentage}%\n"
        f"击败了 {beaten_users} 位群友！"
    )


@on_message(block=False, priority=5).handle()
async def _(
    event: GroupMessageEvent,
    session: AsyncSession = Depends(get_session, use_cache=False),
):
    await WaterInfoDAO(session).create_water_info(
        event.get_user_id(), event.group_id.__str__()
    )
