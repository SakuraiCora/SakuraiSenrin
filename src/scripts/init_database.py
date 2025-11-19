"""
Author: SakuraiCora
Date: 2024-12-28 11:30:19
LastEditors: SakuraiCora
LastEditTime: 2024-12-28 11:31:24
Description: 初始化数据库脚本
"""

from urllib.parse import quote

import nonebot
from nonebot import get_bot
from nonebot.adapters.onebot.v11 import Bot
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.general_config import general_config
from src.database.system.dao import (
    GroupInfoDAO,
    GroupLogDAO,
    GroupService,
    PluginInfoDAO,
    UserInfoDAO,
    UserLogDAO,
    UserService,
)
from src.database.system.database import Base as system_base
from src.database.system.database import (
    GroupStatusEnum,
    PluginPermissionEnum,
    TriggerTypeEnum,
    UserStatusEnum,
)
from src.database.system.database import async_session as system_session
from src.database.system.database import engine as system_engine

PGSQL_URL = f"postgresql+asyncpg://{quote(general_config.pg_username)}:{quote(general_config.pg_password)}@{general_config.pg_host}:{general_config.pg_port}/postgres"


async def create_database():
    async with async_sessionmaker(
        bind=create_async_engine(
            PGSQL_URL,
            echo=False,
            isolation_level="AUTOCOMMIT",
            pool_size=general_config.pg_pool_size,
            max_overflow=general_config.pg_max_overflow,
        ),
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=True,
    )() as session:
        for db in ["senrin_system", "senrin_water", "senrin_wordbank"]:
            if (
                await session.execute(
                    text(f"SELECT 1 FROM pg_database WHERE datname = '{db}';")
                )
            ).scalar_one_or_none():
                continue
            await session.execute(text(f"CREATE DATABASE {db};"))


async def init_system_table():
    async with system_engine.begin() as conn:
        await conn.run_sync(system_base.metadata.create_all)


async def init_system_database():
    async with system_session() as session:
        if (bot := get_bot()) and isinstance(bot, Bot):
            group_info_dao = GroupInfoDAO(session)
            group_log_dao = GroupLogDAO(session)
            group_service = GroupService(group_info_dao, group_log_dao)
            group_dict = {i["group_id"]: i for i in await bot.get_group_list()}
            for group_id in set(group_dict.keys()) - set(
                [int(i.group_id) for i in await group_info_dao.get_all_info()]
            ):
                await group_service.upsert_info_with_log(
                    group_id=str(group_id),
                    group_name=group_dict[group_id]["group_name"],
                    status=GroupStatusEnum.UNAUTH,
                    operator_id=bot.self_id,
                    remark="自启动检测未授权群组",
                )
            for group_item in group_dict.values():
                await group_service.update_name_with_log(
                    group_id=str(group_item["group_id"]),
                    group_name=group_item["group_name"],
                    operator_id=bot.self_id,
                )

            user_info_dao = UserInfoDAO(session)
            user_log_dao = UserLogDAO(session)
            user_service = UserService(user_info_dao, user_log_dao)
            user_dict = {i["user_id"]: i for i in await bot.get_friend_list()}
            for user_id in set(user_dict.keys()) - set(
                [int(i.user_id) for i in await user_info_dao.get_all_info()]
            ):
                await user_service.upsert_info_with_log(
                    user_id=str(user_id),
                    user_name=user_dict[user_id]["nickname"],
                    status=UserStatusEnum.ENABLE,
                    operator_id=bot.self_id,
                    remark="自启动检测新增好友",
                )
            for user_item in user_dict.values():
                await user_service.update_name_with_log(
                    user_id=str(user_item["user_id"]),
                    user_name=user_item["nickname"],
                    operator_id=bot.self_id,
                )
        for plugin in nonebot.get_loaded_plugins():
            plugin_metadata = plugin.metadata
            if not plugin_metadata:
                continue
            try:
                trigger_type = TriggerTypeEnum(plugin_metadata.extra["trigger"])
                plugin_permission = PluginPermissionEnum(
                    plugin_metadata.extra["permission"]
                )
            except ValueError:
                continue
            except KeyError:
                continue
            await PluginInfoDAO(session).upsert_info(
                plugin_raw_name=plugin.name,
                plugin_metadata_name=plugin_metadata.name,
                plugin_module_name=plugin.module_name,
                plugin_description=plugin_metadata.description,
                plugin_usage=plugin_metadata.usage,
                trigger_type=trigger_type,
                plugin_permission=plugin_permission,
            )
        await session.commit()
