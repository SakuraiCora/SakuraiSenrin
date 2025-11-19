from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy import Enum as SQLAEnum
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import (
    Mapped,
    declarative_base,
    mapped_column,
    relationship,
)

from src.config.general_config import general_config
from src.utils.enums import ApprovalStatusEnum, VoteOptionEnum, VoteStatusEnum

Base = declarative_base()

DATABASE_URL = f"postgresql+asyncpg://{general_config.pg_username}:{general_config.pg_password}@{general_config.pg_host}:{general_config.pg_port}/senrin_wordbank"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=general_config.pg_pool_size,
    max_overflow=general_config.pg_max_overflow,
)
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
)


class SearchArgs:
    def __init__(
        self,
        trigger: Optional[str] = None,
        response: Optional[str] = None,
        author: Optional[str] = None,
    ):
        self.trigger = trigger
        self.response = response
        self.author = author


class Trigger(Base):
    __tablename__ = "trigger"
    trigger_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trigger_text: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, unique=True
    )
    trigger_config: Mapped[Dict] = mapped_column(JSON, nullable=False)
    availability: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    extra_info: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    response_items: Mapped[List["Response"]] = relationship(
        "Response", back_populates="trigger_item"
    )
    trigger_logs: Mapped[List["TriggerLog"]] = relationship(
        "TriggerLog", back_populates="trigger_item", lazy="select"
    )


class Response(Base):
    __tablename__ = "response"
    response_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trigger_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trigger.trigger_id"), nullable=False
    )
    response_text: Mapped[str] = mapped_column(String, nullable=False)
    response_rule_conditions: Mapped[Dict] = mapped_column(JSON, nullable=False)
    weight: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
    call_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    availability: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    trigger_item: Mapped["Trigger"] = relationship(
        "Trigger", back_populates="response_items"
    )
    response_logs: Mapped[List["ResponseLog"]] = relationship(
        "ResponseLog", back_populates="response_item", lazy="select"
    )


class TriggerLog(Base):
    __tablename__ = "trigger_log"
    log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[str] = mapped_column(String, nullable=False)
    trigger_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trigger.trigger_id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    call_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )

    trigger_item: Mapped["Trigger"] = relationship(
        "Trigger", back_populates="trigger_logs"
    )


class ResponseLog(Base):
    __tablename__ = "response_log"
    log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[str] = mapped_column(String, nullable=False)
    response_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("response.response_id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    call_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )

    response_item: Mapped["Response"] = relationship(
        "Response", back_populates="response_logs"
    )


class AdditionLog(Base):
    __tablename__ = "addition_log"
    log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trigger_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trigger.trigger_id"), nullable=False
    )
    response_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("response.response_id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    add_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
    add_source: Mapped[Dict] = mapped_column(JSON, nullable=False)
    created_message_id: Mapped[str] = mapped_column(String, nullable=False)

    approval_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("approval.approval_id"), nullable=True
    )

    trigger_item: Mapped["Trigger"] = relationship("Trigger")
    response_item: Mapped["Response"] = relationship("Response")
    approval_item: Mapped["Approval"] = relationship(
        "Approval", back_populates="addition_logs"
    )


class TriggerModifyLog(Base):
    __tablename__ = "trigger_modify_log"
    log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trigger_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trigger.trigger_id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    modify_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
    trigger_text: Mapped[str] = mapped_column(String, nullable=False)
    trigger_config: Mapped[Dict] = mapped_column(JSON, nullable=False)
    success_status: Mapped[bool] = mapped_column(Boolean, nullable=False)

    trigger_item: Mapped["Trigger"] = relationship("Trigger")


class ResponseModifyLog(Base):
    __tablename__ = "response_modify_log"
    log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trigger_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trigger.trigger_id"), nullable=False
    )
    response_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("response.response_id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    modify_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
    response_text: Mapped[str] = mapped_column(String, nullable=False)
    response_rule_conditions: Mapped[Dict] = mapped_column(JSON, nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False)
    success_status: Mapped[bool] = mapped_column(Boolean, nullable=False)

    trigger_item: Mapped["Trigger"] = relationship("Trigger")
    response_item: Mapped["Response"] = relationship("Response")


class Approval(Base):
    __tablename__ = "approval"
    approval_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trigger_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("trigger.trigger_id"), nullable=True
    )
    response_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("response.response_id"), nullable=True, unique=True
    )
    current_status: Mapped[ApprovalStatusEnum] = mapped_column(
        SQLAEnum(ApprovalStatusEnum), nullable=False
    )
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )

    trigger_item: Mapped["Trigger"] = relationship("Trigger")
    response_item: Mapped["Response"] = relationship("Response")

    logs: Mapped[list["ApprovalLog"]] = relationship(
        "ApprovalLog", back_populates="approval", cascade="all, delete-orphan"
    )
    addition_logs: Mapped[list["AdditionLog"]] = relationship(
        "AdditionLog", back_populates="approval_item"
    )
    message_approvals: Mapped[list["MessageApproval"]] = relationship(
        "MessageApproval", back_populates="approval"
    )


class ApprovalLog(Base):
    __tablename__ = "approval_log"
    log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    approval_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("approval.approval_id"), nullable=False
    )
    status: Mapped[ApprovalStatusEnum] = mapped_column(
        SQLAEnum(ApprovalStatusEnum), nullable=False
    )
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    action_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
    success_status: Mapped[bool] = mapped_column(Boolean, nullable=False)

    approval: Mapped["Approval"] = relationship("Approval", back_populates="logs")


class MessageApproval(Base):
    __tablename__ = "message_approval"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(String, nullable=False)
    approval_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("approval.approval_id"), nullable=False
    )

    approval: Mapped["Approval"] = relationship(
        "Approval", back_populates="message_approvals"
    )


class DeletionLog(Base):
    __tablename__ = "deletion_log"
    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trigger_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("trigger.trigger_id"), default=0, nullable=True
    )
    response_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("response.response_id"), nullable=True
    )
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    delete_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    delete_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
    success_status: Mapped[bool] = mapped_column(Boolean, nullable=False)

    trigger_item: Mapped["Trigger"] = relationship("Trigger")
    response_item: Mapped["Response"] = relationship(
        "Response", foreign_keys=[response_id], lazy="select"
    )


class RestorationLog(Base):
    __tablename__ = "restoration_log"
    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trigger_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("trigger.trigger_id"), default=0, nullable=True
    )
    response_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("response.response_id"), nullable=True
    )
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    restore_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    restore_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
    success_status: Mapped[bool] = mapped_column(Boolean, nullable=False)

    trigger_item: Mapped["Trigger"] = relationship("Trigger")
    response_item: Mapped["Response"] = relationship(
        "Response", foreign_keys=[response_id], lazy="select"
    )


class WordbankFTS(Base):
    __tablename__ = "wordbank_fts"
    rowid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trigger_id: Mapped[int] = mapped_column(Integer, nullable=False)
    trigger_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    response_id: Mapped[int] = mapped_column(Integer, nullable=False)
    response_text: Mapped[str] = mapped_column(String, nullable=False)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    trigger_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    response_rule_conditions: Mapped[dict] = mapped_column(JSON, nullable=False)
    extra_info: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class WordbankVote(Base):
    __tablename__ = "wordbank_vote"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(String, nullable=False)
    trigger_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trigger.trigger_id"), nullable=False
    )
    response_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("response.response_id"), nullable=False
    )
    initiator: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
    vote_status: Mapped[VoteStatusEnum] = mapped_column(
        SQLAEnum(VoteStatusEnum), nullable=False
    )


class WordbankVoteLog(Base):
    __tablename__ = "wordbank_vote_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(String, nullable=False)
    vote_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("wordbank_vote.id"), nullable=False
    )
    operator: Mapped[str] = mapped_column(String, nullable=False)
    option: Mapped[VoteOptionEnum] = mapped_column(
        SQLAEnum(VoteOptionEnum), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )


class WordbankVoteDeleteMessage(Base):
    __tablename__ = "wordbank_vote_delete_message"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(Integer, nullable=False)
    vote_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("wordbank_vote.id"), nullable=False
    )


async def get_session():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.commit()
            await session.close()
