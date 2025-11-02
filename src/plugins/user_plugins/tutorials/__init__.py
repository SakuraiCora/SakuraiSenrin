"""
Author: SakuraiCora
Date: 2024-12-21 13:16:37
LastEditors: SakuraiCora
LastEditTime: 2025-01-02 17:43:06
Description: 用户帮助模块，后期预计加入 webui
"""

from collections import ChainMap
from itertools import dropwhile

from nonebot.adapters.onebot.v11 import Message
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, MessageEvent
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata, on_command

from src.cache.memory_cache import memory_cache
from src.config.general_config import general_config
from src.utils.enmus import PluginPermissionEnum, TriggerTypeEnum

name = "帮助文档"
description = """
用户帮助文档模块
""".strip()

usage = f"""
📖 ===== {name} =====

命令前缀: #help / #帮助

帮助信息
  示例: #help <插件名 / 别名>

⚠️ 注意事项:
1. 请确保输入的插件名称存在。
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

tutorials_command = on_command("help", aliases={"帮助"}, priority=5, block=False)


@tutorials_command.handle()
async def _(
    bot: Bot, event: MessageEvent, matcher: Matcher, arg: Message = CommandArg()
):
    if await SUPERUSER(bot, event):
        plugin_permission = PluginPermissionEnum.SUPERUSER
    elif isinstance(event, GroupMessageEvent) and event.sender.role:
        plugin_permission = PluginPermissionEnum.GROUPADMIN
    else:
        plugin_permission = PluginPermissionEnum.EVERYONE

    avaliable_plugins_map = ChainMap(
        *[
            memory_cache.active_plugins[filtered_plugin_permission]
            for filtered_plugin_permission in dropwhile(
                lambda x: x != plugin_permission,
                PluginPermissionEnum,
            )
        ][::-1]
    )

    if plugin := avaliable_plugins_map.get(arg.extract_plain_text()):
        await matcher.finish(plugin.plugin_usage)
    else:
        await matcher.finish(
            usage
            + "\n\n🔧 当前可用插件如下:\n\n"
            + "\n".join(
                map(
                    lambda x: f"{x[0]}. {x[1][1].plugin_metadata_name}\n  #help {x[1][0]}",
                    enumerate(
                        avaliable_plugins_map.items(),
                        start=1,
                    ),
                )
            )
        )
