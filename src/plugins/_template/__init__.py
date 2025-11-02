from nonebot.plugin import PluginMetadata

from src.utils.enmus import PluginPermissionEnum, TriggerTypeEnum

name = "插件名称"
description = """
插件描述
""".strip()

usage = f"""
📖 ===== {name} =====

命令前缀: # / #

子功能
  子功能描述
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
        "no_check": False,
    },
)
