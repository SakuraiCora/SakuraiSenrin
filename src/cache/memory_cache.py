"""
Author: SakuraiCora
Date: 2024-12-27 22:37:47
LastEditors: SakuraiCora
LastEditTime: 2025-01-02 21:24:35
Description: 内存缓存实现
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.utils.enmus import (
    GroupStatusEnum,
    PluginPermissionEnum,
    TriggerTypeEnum,
    UserStatusEnum,
)


@dataclass
class UserCache:
    id: int
    user_id: str
    user_name: Optional[str]
    status: UserStatusEnum
    create_time: datetime
    effective_time: datetime
    remark: Optional[str]


@dataclass
class GroupCache:
    id: int
    group_id: str
    group_name: Optional[str]
    status: GroupStatusEnum
    create_time: datetime
    effective_time: datetime
    remark: Optional[str]


@dataclass
class PluginCache:
    id: int
    plugin_raw_name: str
    plugin_metadata_name: str
    plugin_module_name: str
    plugin_description: str
    plugin_usage: str
    trigger_type: TriggerTypeEnum
    plugin_permission: PluginPermissionEnum
    create_time: datetime


@dataclass
class MemoryCache:
    users: dict[str, UserCache]
    groups: dict[str, GroupCache]
    plugins: dict[str, PluginCache]
    active_plugins: dict[PluginPermissionEnum, dict[str, PluginCache]]

    super_users: set[str]


memory_cache = MemoryCache(
    users={},
    groups={},
    plugins={},
    active_plugins=defaultdict(dict),
    super_users=set(),
)
