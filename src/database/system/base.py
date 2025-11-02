"""
Author: SakuraiCora
Date: 2024-12-29 21:35:48
LastEditors: SakuraiCora
LastEditTime: 2024-12-29 21:35:52
Description: System DAO 抽象类
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from typing import Sequence

T = TypeVar("T")


class SystemInfoDAOBase(ABC, Generic[T]):
    @abstractmethod
    async def upsert_info(self, *args, **kwargs) -> T:
        pass

    @abstractmethod
    async def get_all_info(self) -> Sequence[T]:
        pass


class SystemLogDAOBase(ABC, Generic[T]):
    @abstractmethod
    async def insert_log(self, *args, **kwargs) -> T:
        pass


class SystemReportMessageDAOBase(ABC, Generic[T]):
    @abstractmethod
    async def upsert_message(self, *args, **kwargs) -> T:
        pass

    @abstractmethod
    async def get_report_message(self, *args, **kwargs) -> T:
        pass


class SystemServiceBase(ABC):
    @abstractmethod
    async def upsert_info_with_log(self, *args, **kwargs) -> tuple[T, T]:
        pass

    async def relate_with_report_message_id(self, *args, **kwargs) -> None:
        pass
