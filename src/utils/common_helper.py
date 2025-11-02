"""
Author: SakuraiCora
Date: 2024-12-21 12:43:47
LastEditors: SakuraiCora
LastEditTime: 2024-12-27 21:40:21
Description: 通用函数
"""

import re
from datetime import timedelta

from httpx import AsyncClient

from src.cache.memory_cache import memory_cache
from src.utils.enmus import (
    GroupStatusEnum,
    UserStatusEnum,
)


class CommonHelper:
    @staticmethod
    async def is_user_valid(user_id: str) -> bool:
        if user := memory_cache.users.get(user_id):
            return user.status == UserStatusEnum.ENABLE
        return True

    @staticmethod
    async def is_group_valid(group_id: str) -> bool:
        if group := memory_cache.groups.get(group_id):
            return group.status == GroupStatusEnum.ENABLE
        return False

    @staticmethod
    def time_to_timedelta(time_str: str) -> timedelta:
        time_units = {
            "d": 86400,
            "h": 3600,
            "m": 60,
            "s": 1,
        }

        total_seconds = 0
        pattern = r"(\d+)([dhms])"
        matches = re.findall(pattern, time_str)

        for value, unit in matches:
            total_seconds += int(value) * time_units[unit]
        if total_seconds <= 0:
            raise ValueError
        return timedelta(seconds=total_seconds)

    @staticmethod
    def split_list(input_list: list, size: int) -> list[list]:
        return [input_list[i : i + size] for i in range(0, len(input_list), size)]

    @staticmethod
    async def get_qq_avatar(user_id: str, size=640) -> bytes:
        async with AsyncClient() as client:
            return (
                await client.get(f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s={size}")
            ).read()
