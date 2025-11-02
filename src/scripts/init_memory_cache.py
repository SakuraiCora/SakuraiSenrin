"""
Author: SakuraiCora
Date: 2024-12-27 22:24:40
LastEditors: SakuraiCora
LastEditTime: 2024-12-28 10:57:55
Description: 初始化内存缓存启动脚本
"""

from nonebot import get_driver
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache.memory_cache import GroupCache, PluginCache, UserCache, memory_cache
from src.database.system.dao import GroupInfoDAO, PluginInfoDAO, UserInfoDAO
from src.database.system.database import (
    TriggerTypeEnum,
    async_session,
)


async def init_group_info(session: AsyncSession):
    for group in await GroupInfoDAO(session).get_all_info():
        memory_cache.groups[group.group_id] = GroupCache(
            id=group.id,
            group_id=group.group_id,
            group_name=group.group_name,
            status=group.status,
            create_time=group.create_time,
            effective_time=group.effective_time,
            remark=group.remark,
        )


async def init_user_info(session: AsyncSession):
    for user in await UserInfoDAO(session).get_all_info():
        memory_cache.users[user.user_id] = UserCache(
            id=user.id,
            user_id=user.user_id,
            user_name=user.user_name,
            status=user.status,
            create_time=user.create_time,
            effective_time=user.effective_time,
            remark=user.remark,
        )


async def init_plugin_info(session: AsyncSession):
    for plugin in await PluginInfoDAO(session).get_all_info():
        memory_cache.plugins[plugin.plugin_raw_name] = PluginCache(
            id=plugin.id,
            plugin_raw_name=plugin.plugin_raw_name,
            plugin_metadata_name=plugin.plugin_metadata_name,
            plugin_module_name=plugin.plugin_module_name,
            plugin_description=plugin.plugin_description,
            plugin_usage=plugin.plugin_usage,
            trigger_type=plugin.trigger_type,
            plugin_permission=plugin.plugin_permission,
            create_time=plugin.create_time,
        )
    for plugin in await PluginInfoDAO(session).get_info_by_trigger_type(
        TriggerTypeEnum.ACTIVE
    ):
        memory_cache.active_plugins[plugin.plugin_permission][
            plugin.plugin_raw_name
        ] = PluginCache(
            id=plugin.id,
            plugin_raw_name=plugin.plugin_raw_name,
            plugin_metadata_name=plugin.plugin_metadata_name,
            plugin_module_name=plugin.plugin_module_name,
            plugin_description=plugin.plugin_description,
            plugin_usage=plugin.plugin_usage,
            trigger_type=plugin.trigger_type,
            plugin_permission=plugin.plugin_permission,
            create_time=plugin.create_time,
        )


async def init_memory_cache():
    async with async_session() as session:
        await init_user_info(session)
        await session.commit()
        await init_group_info(session)
        await init_plugin_info(session)
        memory_cache.super_users = get_driver().config.superusers
