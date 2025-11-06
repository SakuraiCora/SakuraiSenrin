"""
Author: SakuraiCora
Date: 2024-12-25 18:57:23
LastEditors: SakuraiCora
LastEditTime: 2024-12-30 01:38:29
Description: None
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLAEnum
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.general_config import general_config
from utils.enums import (
    ExceptionStatusEnum,
    GroupStatusEnum,
    InvitationStatusEnum,
    # MemberStatusEnum,
    OnebotV11EventEnum,
    PluginPermissionEnum,
    TriggerTypeEnum,
    UserStatusEnum,
)

Base = declarative_base()


# class ControlLog(Base):
#     __tablename__ = "control_log"
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
#     user_id: Mapped[int] = mapped_column(Integer, nullable=False)
#     group_id: Mapped[int] = mapped_column(Integer, nullable=False)
#     operator_id: Mapped[str] = mapped_column(String, nullable=False)
#     create_time: Mapped[datetime] = mapped_column(
#         DateTime, nullable=False, default=datetime.now
#     )


class ExceptionInfo(Base):
    __tablename__ = "exception_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_input: Mapped[str] = mapped_column(String, nullable=False)
    event_log: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    group_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    exception_type: Mapped[str] = mapped_column(String, nullable=False)
    traceback_info: Mapped[str] = mapped_column(String, nullable=False)
    exception_source: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[ExceptionStatusEnum] = mapped_column(
        SQLAEnum(ExceptionStatusEnum), nullable=False
    )
    operator_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    create_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    report_messages: Mapped[list["ExceptionReportMessage"]] = relationship(
        "ExceptionReportMessage",
        back_populates="exception_info",
        cascade="all, delete-orphan",
    )
    exception_logs: Mapped[list["ExceptionLog"]] = relationship(
        "ExceptionLog", back_populates="exception_info", cascade="all, delete-orphan"
    )


class ExceptionLog(Base):
    __tablename__ = "exception_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exception_info_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exception_info.id"), nullable=False
    )
    user_input: Mapped[str] = mapped_column(String, nullable=False)
    event_log: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    group_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    exception_type: Mapped[str] = mapped_column(String, nullable=False)
    traceback_info: Mapped[str] = mapped_column(String, nullable=False)
    exception_source: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[ExceptionStatusEnum] = mapped_column(
        SQLAEnum(ExceptionStatusEnum), nullable=False
    )
    operator_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    create_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )

    exception_info: Mapped["ExceptionInfo"] = relationship(
        "ExceptionInfo", back_populates="exception_logs"
    )


class ExceptionReportMessage(Base):
    __tablename__ = "exception_report_message"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_message_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    exception_info_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exception_info.id"), nullable=False
    )
    exception_info: Mapped["ExceptionInfo"] = relationship(
        "ExceptionInfo", back_populates="report_messages"
    )


class InvitationInfo(Base):
    __tablename__ = "invitation_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    group_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    inviter_id: Mapped[str] = mapped_column(String, nullable=False)
    flag: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sub_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[InvitationStatusEnum] = mapped_column(
        SQLAEnum(InvitationStatusEnum), nullable=False
    )
    operator_id: Mapped[str] = mapped_column(String, nullable=False)
    create_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    report_messages: Mapped[list["InvitationReportMessage"]] = relationship(
        "InvitationReportMessage",
        back_populates="invitation_info",
        cascade="all, delete-orphan",
    )
    invitation_logs: Mapped[list["InvitationLog"]] = relationship(
        "InvitationLog",
        back_populates="invitation_info",
        cascade="all, delete-orphan",
    )


class InvitationLog(Base):
    __tablename__ = "invitation_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invitation_info_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("invitation_info.id"), nullable=False
    )
    group_id: Mapped[str] = mapped_column(String, nullable=False)
    group_name: Mapped[Optional[str]] = mapped_column(String)
    inviter_id: Mapped[str] = mapped_column(String, nullable=False)
    flag: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sub_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[InvitationStatusEnum] = mapped_column(
        SQLAEnum(InvitationStatusEnum), nullable=False
    )
    operator_id: Mapped[str] = mapped_column(String, nullable=False)
    create_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )

    invitation_info: Mapped["InvitationInfo"] = relationship(
        "InvitationInfo",
        back_populates="invitation_logs",
    )


class InvitationReportMessage(Base):
    __tablename__ = "invitation_report_message"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_message_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    invitation_info_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("invitation_info.id"), nullable=False
    )
    invitation_info: Mapped["InvitationInfo"] = relationship(
        "InvitationInfo", back_populates="report_messages"
    )


class GroupInfo(Base):
    __tablename__ = "group_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    group_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[GroupStatusEnum] = mapped_column(
        SQLAEnum(GroupStatusEnum), nullable=False
    )
    operator_id: Mapped[str] = mapped_column(String, nullable=False)
    effective_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    create_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    remark: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    group_logs: Mapped[list["GroupLog"]] = relationship(
        "GroupLog", back_populates="group_info", cascade="all, delete-orphan"
    )


class GroupLog(Base):
    __tablename__ = "group_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[str] = mapped_column(String, nullable=False)
    group_name: Mapped[Optional[str]] = mapped_column(String)
    status: Mapped[GroupStatusEnum] = mapped_column(
        SQLAEnum(GroupStatusEnum), nullable=False
    )
    operator_id: Mapped[str] = mapped_column(String, nullable=False)
    effective_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    create_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    remark: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    group_info_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("group_info.id"), nullable=False
    )
    group_info: Mapped["GroupInfo"] = relationship(
        "GroupInfo", back_populates="group_logs"
    )


class UserInfo(Base):
    __tablename__ = "user_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    user_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[UserStatusEnum] = mapped_column(
        SQLAEnum(UserStatusEnum), nullable=False
    )
    operator_id: Mapped[str] = mapped_column(String, nullable=False)
    effective_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    create_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    remark: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    user_logs: Mapped[list["UserLog"]] = relationship(
        "UserLog", back_populates="user_info", cascade="all, delete-orphan"
    )


class UserLog(Base):
    __tablename__ = "user_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    user_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[UserStatusEnum] = mapped_column(
        SQLAEnum(UserStatusEnum), nullable=False
    )
    operator_id: Mapped[str] = mapped_column(String, nullable=False)
    effective_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    create_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    remark: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    user_info_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user_info.id"),
        nullable=False,
    )
    user_info: Mapped["UserInfo"] = relationship("UserInfo", back_populates="user_logs")


class PluginInfo(Base):
    __tablename__ = "plugin_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plugin_raw_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    plugin_metadata_name: Mapped[str] = mapped_column(String, nullable=False)
    plugin_module_name: Mapped[str] = mapped_column(String, nullable=False)
    plugin_description: Mapped[str] = mapped_column(String, nullable=False)
    plugin_usage: Mapped[str] = mapped_column(String, nullable=False)
    trigger_type: Mapped[TriggerTypeEnum] = mapped_column(
        SQLAEnum(TriggerTypeEnum), nullable=False
    )
    plugin_permission: Mapped[PluginPermissionEnum] = mapped_column(
        SQLAEnum(PluginPermissionEnum), nullable=False
    )
    create_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    plugin_log: Mapped[list["PluginLog"]] = relationship(
        "PluginLog", back_populates="plugin_info", cascade="all, delete-orphan"
    )


class PluginLog(Base):
    __tablename__ = "plugin_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plugin_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("plugin_info.id"), nullable=False
    )
    operator_id: Mapped[str] = mapped_column(String, nullable=False)
    event_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    event_type: Mapped[OnebotV11EventEnum] = mapped_column(
        SQLAEnum(OnebotV11EventEnum), nullable=False
    )
    create_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    plugin_info: Mapped["PluginInfo"] = relationship(
        "PluginInfo", back_populates="plugin_log"
    )


# class MemberInfo(Base):
#     __tablename__ = "member_info"
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
#     group_id: Mapped[str] = mapped_column(String, nullable=False)
#     user_id: Mapped[str] = mapped_column(String, nullable=False)
#     status: Mapped[MemberStatusEnum] = mapped_column(String, nullable=False)
#     operator_id: Mapped[str] = mapped_column(String, nullable=False)
#     create_time: Mapped[datetime] = mapped_column(
#         DateTime, nullable=False, default=datetime.now
#     )
#     update_time: Mapped[datetime] = mapped_column(
#         DateTime, nullable=False, default=datetime.now
#     )


# class Memberlog(Base):
#     __tablename__ = "member_log"
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
#     group_id: Mapped[int] = mapped_column(Integer, nullable=False)
#     user_id: Mapped[int] = mapped_column(Integer, nullable=False)
#     status: Mapped[MemberStatusEnum] = mapped_column(String, nullable=False)
#     operator_id: Mapped[str] = mapped_column(String, nullable=False)
#     create_time: Mapped[datetime] = mapped_column(
#         DateTime, nullable=False, default=datetime.now
#     )

DATABASE_URL = f"postgresql+asyncpg://{general_config.pg_username}:{general_config.pg_password}@{general_config.pg_host}:{general_config.pg_port}/senrin_system"
engine = create_async_engine(
    DATABASE_URL,
    # echo=True,  # TODO: 删除
    future=True,
    pool_size=general_config.pg_pool_size,
    max_overflow=general_config.pg_max_overflow,
)
async_session = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=True
)


async def get_session():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.commit()
            await session.close()
