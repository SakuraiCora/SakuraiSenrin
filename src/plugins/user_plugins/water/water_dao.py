from datetime import datetime
from typing import Sequence

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.plugins.user_plugins.water.water_database import WaterInfo


class WaterInfoDAO:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_water_info_by_time(self, since_time: datetime) -> Sequence[WaterInfo]:
        return (
            (
                await self.session.execute(
                    select(WaterInfo).where(WaterInfo.created_at >= since_time)
                )
            )
            .scalars()
            .all()
        )

    async def get_water_info_by_user_id(self, user_id: str) -> Sequence[WaterInfo]:
        return (
            (
                await self.session.execute(
                    select(WaterInfo).where(WaterInfo.user_id == user_id)
                )
            )
            .scalars()
            .all()
        )

    async def create_water_info(self, user_id: str, group_id: str) -> WaterInfo:
        return (
            await self.session.execute(
                insert(WaterInfo)
                .values(user_id=user_id, group_id=group_id)
                .returning(WaterInfo)
            )
        ).scalar_one()

    async def get_water_info_by_group_id(self, group_id: str) -> Sequence[WaterInfo]:
        return (
            (
                await self.session.execute(
                    select(WaterInfo).where(WaterInfo.group_id == group_id)
                )
            )
            .scalars()
            .all()
        )

    async def get_water_info_by_user_id_and_group_id(
        self, user_id: str, group_id: str
    ) -> Sequence[WaterInfo]:
        return (
            (
                await self.session.execute(
                    select(WaterInfo).where(
                        WaterInfo.user_id == user_id, WaterInfo.group_id == group_id
                    )
                )
            )
            .scalars()
            .all()
        )

    async def get_user_group_stats(
        self, user_id: str, group_id: str, since_time: datetime
    ):
        """
        获取单个用户在单个群聊中的发言次数、排名、打败了多少群友、当前用户的次数在群聊里面占比
        """
        now_time = datetime.now()
        user_count_stmt = select(func.count()).where(
            WaterInfo.user_id == user_id,
            WaterInfo.group_id == group_id,
            WaterInfo.created_at.between(since_time, now_time),
        )
        user_count = (
            await self.session.execute(user_count_stmt)
        ).scalar_one_or_none() or 0
        group_counts_stmt = (
            select(WaterInfo.user_id, func.count().label("message_count"))
            .where(
                WaterInfo.group_id == group_id,
                WaterInfo.created_at >= since_time,
            )
            .group_by(WaterInfo.user_id)
            .order_by(func.count().desc())
        )
        group_counts = (await self.session.execute(group_counts_stmt)).all()
        user_rank = next(
            (i + 1 for i, (uid, _) in enumerate(group_counts) if uid == user_id), None
        )
        total_users = len(group_counts)
        beaten_users = total_users - user_rank if user_rank else 0
        total_messages = sum(count for _, count in group_counts)
        user_percentage = (
            (user_count / total_messages) * 100 if total_messages > 0 else 0
        )

        return user_count, user_rank, beaten_users, user_percentage

    async def get_user_global_stats(self, user_id: str, since_time: datetime):
        """
        获取单个用户在所有群聊中的发言次数、排名、打败了多少群友、当前用户的次数在所有群聊里面占比
        """
        user_count_stmt = select(func.count()).where(
            WaterInfo.user_id == user_id,
            WaterInfo.created_at >= since_time,
        )
        user_count = await self.session.scalar(user_count_stmt) or 0
        all_groups_counts_stmt = (
            select(WaterInfo.user_id, func.count().label("message_count"))
            .where(WaterInfo.created_at >= since_time)
            .group_by(WaterInfo.user_id)
            .order_by(func.count().desc())
        )
        all_groups_counts = (await self.session.execute(all_groups_counts_stmt)).all()
        user_rank = next(
            (i + 1 for i, (uid, _) in enumerate(all_groups_counts) if uid == user_id),
            None,
        )
        total_users = len(all_groups_counts)
        beaten_users = total_users - user_rank if user_rank else 0
        total_messages = sum(count for _, count in all_groups_counts)
        user_percentage = (
            (user_count / total_messages) * 100 if total_messages > 0 else 0
        )
        return user_count, user_rank, beaten_users, user_percentage
