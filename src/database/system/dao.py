"""
Author: SakuraiCora
Date: 2024-12-27 21:22:35
LastEditors: SakuraiCora
LastEditTime: 2025-01-02 16:35:43
Description: None
"""

from datetime import datetime
from typing import Optional, Sequence, final

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database.system.base import (
    SystemInfoDAOBase,
    SystemLogDAOBase,
    SystemReportMessageDAOBase,
    SystemServiceBase,
)
from src.database.system.database import (
    ExceptionInfo,
    ExceptionLog,
    ExceptionReportMessage,
    GroupInfo,
    GroupLog,
    InvitationInfo,
    InvitationLog,
    InvitationReportMessage,
    PluginInfo,
    PluginLog,
    UserInfo,
    UserLog,
)
from src.utils.enmus import (
    ExceptionStatusEnum,
    GroupStatusEnum,
    InvitationStatusEnum,
    OnebotV11EventEnum,
    PluginPermissionEnum,
    TriggerTypeEnum,
    UserStatusEnum,
)


@final
class ExceptionInfoDAO(SystemInfoDAOBase[ExceptionInfo]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_info(
        self,
        user_input: str,
        event_log: str,
        user_id: Optional[str],
        group_id: Optional[str],
        exception_type: str,
        traceback_info: str,
        exception_source: str,
        status: ExceptionStatusEnum,
        operator_id: Optional[str],
    ) -> ExceptionInfo:
        exception_info = await self.session.execute(
            (
                insert(ExceptionInfo)
                .values(
                    user_input=user_input,
                    event_log=event_log,
                    user_id=user_id,
                    group_id=group_id,
                    exception_type=exception_type,
                    traceback_info=traceback_info,
                    exception_source=exception_source,
                    status=status,
                    operator_id=operator_id,
                    update_time=datetime.now(),
                    create_time=datetime.now(),
                )
                .on_conflict_do_update(
                    index_elements=[ExceptionInfo.id],
                    set_=dict(
                        user_input=user_input,
                        event_log=event_log,
                        user_id=user_id,
                        group_id=group_id,
                        exception_type=exception_type,
                        traceback_info=traceback_info,
                        exception_source=exception_source,
                        status=status,
                        operator_id=operator_id,
                        update_time=datetime.now(),
                    ),
                )
            ).returning(ExceptionInfo)
        )

        return exception_info.scalar_one()

    async def get_all_info(self) -> Sequence[ExceptionInfo]:
        return (await self.session.execute(select(ExceptionInfo))).scalars().all()

    async def update_status(
        self, exception_info_id: int, status: ExceptionStatusEnum, operator_id: str
    ) -> ExceptionInfo:
        exception_info = await self.session.execute(
            update(ExceptionInfo)
            .where(ExceptionInfo.id == exception_info_id)
            .values(status=status.value, operator_id=operator_id)
            .returning(ExceptionInfo)
        )

        return exception_info.scalar_one()

    async def get_info_by_status(
        self,
        status: ExceptionStatusEnum,
    ) -> Sequence[ExceptionInfo]:
        return (
            (
                await self.session.execute(
                    select(ExceptionInfo).where(ExceptionInfo.status == status)
                )
            )
            .scalars()
            .all()
        )

    async def get_info_nums(self) -> int:
        return (
            await self.session.execute(select(func.count(ExceptionInfo.id)))
        ).scalar() or 0

    async def get_info_nums_by_status(self, status: ExceptionStatusEnum) -> int:
        return (
            await self.session.execute(
                select(func.count(ExceptionInfo.id)).where(
                    ExceptionInfo.status == status
                )
            )
        ).scalar() or 0

    async def get_info_by_id(self, exception_id: int) -> ExceptionInfo | None:
        return (
            await self.session.execute(
                select(ExceptionInfo).where(ExceptionInfo.id == exception_id)
            )
        ).scalar_one_or_none()

    async def get_unhandled_info_message(self) -> str:
        return (
            f"📊 未处理异常数量: {await self.get_info_nums_by_status(ExceptionStatusEnum.PENDING)} / {await self.get_info_nums()}\n"
            f"🔖 未处理异常 ID: {'、'.join(map(lambda x: str(x.id), await self.get_info_by_status(ExceptionStatusEnum.PENDING))) or '无'}"
        )


class ExceptionLogDAO(SystemLogDAOBase[ExceptionLog]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert_log(
        self,
        exception_info_id: int,
        user_input: str,
        event_log: str,
        user_id: Optional[str],
        group_id: Optional[str],
        exception_type: str,
        traceback_info: str,
        exception_source: str,
        status: ExceptionStatusEnum,
        operator_id: Optional[str],
    ) -> ExceptionLog:
        exception_log = ExceptionLog(
            exception_info_id=exception_info_id,
            user_input=user_input,
            event_log=event_log,
            user_id=user_id,
            group_id=group_id,
            exception_type=exception_type,
            traceback_info=traceback_info,
            exception_source=exception_source,
            status=status,
            operator_id=operator_id,
            create_time=datetime.now(),
        )
        self.session.add(exception_log)

        return exception_log

    async def get_log_nums(self) -> int:
        return (
            await self.session.execute(select(func.count(ExceptionLog.id)))
        ).scalar() or 0


class ExceptionReportMessageDAO(SystemReportMessageDAOBase[ExceptionReportMessage]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_message(
        self,
        report_message_id: Optional[str],
        exception_info: ExceptionInfo,
    ) -> ExceptionReportMessage:
        exception_report_message = (
            await self.session.execute(
                insert(ExceptionReportMessage)
                .values(
                    report_message_id=report_message_id,
                    exception_info_id=exception_info.id,
                )
                .on_conflict_do_update(
                    index_elements=[ExceptionReportMessage.report_message_id],
                    set_=dict(
                        exception_info_id=exception_info.id,
                    ),
                )
                .returning(ExceptionReportMessage)
            )
        ).scalar_one()

        return exception_report_message

    async def get_report_message(
        self,
        report_message_id: str,
    ) -> ExceptionReportMessage | None:
        return (
            await self.session.execute(
                select(ExceptionReportMessage)
                .options(joinedload(ExceptionReportMessage.exception_info))
                .where(ExceptionReportMessage.report_message_id == report_message_id)
            )
        ).scalar_one_or_none()


class ExceptionService(SystemServiceBase):
    def __init__(
        self,
        exception_info_dao: ExceptionInfoDAO,
        exception_log_dao: ExceptionLogDAO,
        exception_report_message_dao: ExceptionReportMessageDAO,
    ) -> None:
        self.exception_info_dao = exception_info_dao
        self.exception_log_dao = exception_log_dao
        self.exception_report_message_dao = exception_report_message_dao

    async def upsert_info_with_log(
        self,
        user_input: str,
        event_log: str,
        user_id: Optional[str],
        group_id: Optional[str],
        exception_type: str,
        traceback_info: str,
        exception_source: str,
        status: ExceptionStatusEnum,
        operator_id: Optional[str],
    ) -> tuple[ExceptionInfo, ExceptionLog]:
        exception_info = await self.exception_info_dao.upsert_info(
            user_input=user_input,
            event_log=event_log,
            user_id=user_id,
            group_id=group_id,
            exception_type=exception_type,
            traceback_info=traceback_info,
            exception_source=exception_source,
            status=status,
            operator_id=operator_id,
        )
        exception_log = await self.exception_log_dao.insert_log(
            exception_info_id=exception_info.id,
            user_input=user_input,
            event_log=event_log,
            user_id=user_id,
            group_id=group_id,
            exception_type=exception_type,
            traceback_info=traceback_info,
            exception_source=exception_source,
            status=status,
            operator_id=operator_id,
        )
        return exception_info, exception_log

    async def relate_with_report_message_id(
        self,
        report_message_id: Optional[str],
        exception_info: ExceptionInfo,
    ) -> None:
        await self.exception_report_message_dao.upsert_message(
            report_message_id=report_message_id,
            exception_info=exception_info,
        )

    async def update_status_with_log(
        self,
        exception_info_id: int,
        operator_id: str,
        status: ExceptionStatusEnum,
    ) -> None:
        exception_info = await self.exception_info_dao.update_status(
            exception_info_id, status, operator_id
        )
        await self.exception_log_dao.insert_log(
            exception_info_id=exception_info.id,
            user_input=exception_info.user_input,
            event_log=exception_info.event_log,
            user_id=exception_info.user_id,
            group_id=exception_info.group_id,
            exception_type=exception_info.exception_type,
            traceback_info=exception_info.traceback_info,
            exception_source=exception_info.exception_source,
            status=status,
            operator_id=operator_id,
        )


class InvitationInfoDAO(SystemInfoDAOBase[InvitationInfo]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_info(
        self,
        group_id: str,
        group_name: Optional[str],
        inviter_id: str,
        flag: Optional[str],
        sub_type: Optional[str],
        operator_id: str,
        status: InvitationStatusEnum,
    ) -> InvitationInfo:
        invitation_info = await self.session.execute(
            insert(InvitationInfo)
            .values(
                group_id=group_id,
                group_name=group_name,
                inviter_id=inviter_id,
                operator_id=operator_id,
                flag=flag,
                sub_type=sub_type,
                status=status.value,
                update_time=datetime.now(),
                create_time=datetime.now(),
            )
            .on_conflict_do_update(
                index_elements=[InvitationInfo.group_id],
                set_=dict(
                    group_id=group_id,
                    group_name=group_name,
                    inviter_id=inviter_id,
                    operator_id=operator_id,
                    flag=flag,
                    status=status.value,
                    update_time=datetime.now(),
                ),
            )
            .returning(InvitationInfo)
        )

        return invitation_info.scalar_one()

    async def get_all_info(self) -> Sequence[InvitationInfo]:
        return (await self.session.execute(select(InvitationInfo))).scalars().all()

    async def update_status(
        self, invitation_info_id: int, status: InvitationStatusEnum
    ) -> InvitationInfo:
        invitation_info = await self.session.execute(
            update(InvitationInfo)
            .where(InvitationInfo.id == invitation_info_id)
            .values(status=status.value)
            .returning(InvitationInfo)
        )

        return invitation_info.scalar_one()

    async def get_info_by_status(
        self,
        status: InvitationStatusEnum,
    ) -> Sequence[InvitationInfo]:
        return (
            (
                await self.session.execute(
                    select(InvitationInfo).where(InvitationInfo.status == status)
                )
            )
            .scalars()
            .all()
        )

    async def get_info_by_id(self, invitation_info_id: int) -> InvitationInfo | None:
        return (
            await self.session.execute(
                select(InvitationInfo).where(InvitationInfo.id == invitation_info_id)
            )
        ).scalar_one_or_none()

    async def get_info_by_group_id(
        self,
        group_id: str,
    ) -> InvitationInfo | None:
        return (
            await self.session.execute(
                select(InvitationInfo).where(InvitationInfo.group_id == group_id)
            )
        ).scalar_one_or_none()

    async def get_info_by_inviter_id(
        self,
        inviter_id: str,
    ) -> Sequence[InvitationInfo]:
        return (
            (
                await self.session.execute(
                    select(InvitationInfo).where(
                        InvitationInfo.inviter_id == inviter_id
                    )
                )
            )
            .scalars()
            .all()
        )

    async def get_info_nums(self) -> int:
        return (
            await self.session.execute(select(func.count(InvitationInfo.id)))
        ).scalar() or 0

    async def get_info_nums_by_status(self, status: InvitationStatusEnum) -> int:
        return (
            await self.session.execute(
                select(func.count(InvitationInfo.id)).where(
                    InvitationInfo.status == status
                )
            )
        ).scalar() or 0

    async def get_unhandled_info_message(self) -> str:
        return (
            f"📊 未处理邀请数量: {await self.get_info_nums_by_status(InvitationStatusEnum.PENDING)} / {await self.get_info_nums()}\n"
            f"🔖 未处理邀请 ID: {'、'.join(map(lambda x: str(x.id), await self.get_info_by_status(InvitationStatusEnum.PENDING))) or '无'}"
        )


class InvitationLogDAO(SystemLogDAOBase[InvitationLog]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert_log(
        self,
        invitation_info_id: int,
        group_id: str,
        group_name: Optional[str],
        inviter_id: str,
        flag: Optional[str],
        sub_type: Optional[str],
        operator_id: str,
        status: InvitationStatusEnum,
    ) -> InvitationLog:
        invitation_log = InvitationLog(
            invitation_info_id=invitation_info_id,
            group_id=group_id,
            group_name=group_name,
            inviter_id=inviter_id,
            flag=flag,
            sub_type=sub_type,
            operator_id=operator_id,
            status=status,
            create_time=datetime.now(),
        )
        self.session.add(invitation_log)

        return invitation_log

    async def get_log_nums(self) -> int:
        return (
            await self.session.execute(select(func.count(InvitationLog.id)))
        ).scalar() or 0


class InvitationReportMessageDAO(SystemReportMessageDAOBase[InvitationReportMessage]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_message(
        self,
        report_message_id: Optional[str],
        invitation_info: InvitationInfo,
    ) -> InvitationReportMessage:
        invitation_report_message = InvitationReportMessage(
            report_message_id=report_message_id,
            invitation_info_id=invitation_info.id,
        )
        self.session.add(invitation_report_message)

        return invitation_report_message

    async def get_report_message(
        self, report_message_id: str
    ) -> InvitationReportMessage:
        return (
            await self.session.execute(
                select(InvitationReportMessage)
                .options(joinedload(InvitationReportMessage.invitation_info))
                .where(InvitationReportMessage.report_message_id == report_message_id)
            )
        ).scalar_one_or_none()


class InvitationService(SystemServiceBase):
    def __init__(
        self,
        invitation_info_dao: InvitationInfoDAO,
        invitation_log_dao: InvitationLogDAO,
        invitation_report_message_dao: InvitationReportMessageDAO,
    ) -> None:
        self.invitation_info_dao = invitation_info_dao
        self.invitation_log_dao = invitation_log_dao
        self.invitation_report_message_dao = invitation_report_message_dao

    async def upsert_info_with_log(
        self,
        group_id: str,
        group_name: Optional[str],
        inviter_id: str,
        flag: Optional[str],
        sub_type: Optional[str],
        operator_id: str,
        status: InvitationStatusEnum,
    ) -> tuple[InvitationInfo, InvitationLog]:
        invitation_info = await self.invitation_info_dao.upsert_info(
            group_id=group_id,
            group_name=group_name,
            inviter_id=inviter_id,
            flag=flag,
            sub_type=sub_type,
            operator_id=operator_id,
            status=status,
        )
        invitation_log = await self.invitation_log_dao.insert_log(
            invitation_info_id=invitation_info.id,
            group_id=group_id,
            group_name=group_name,
            inviter_id=inviter_id,
            flag=flag,
            sub_type=sub_type,
            operator_id=operator_id,
            status=status,
        )
        return invitation_info, invitation_log

    async def relate_with_report_message_id(
        self,
        report_message_id: Optional[str],
        invitation_info: InvitationInfo,
    ) -> None:
        await self.invitation_report_message_dao.upsert_message(
            report_message_id=report_message_id,
            invitation_info=invitation_info,
        )

    async def update_status_with_log(
        self,
        invitation_info_id: int,
        operator_id: str,
        status: InvitationStatusEnum,
    ) -> None:
        invitation_info = await self.invitation_info_dao.update_status(
            invitation_info_id, status
        )
        await self.invitation_log_dao.insert_log(
            invitation_info_id=invitation_info.id,
            group_id=invitation_info.group_id,
            group_name=invitation_info.group_name,
            inviter_id=invitation_info.inviter_id,
            flag=invitation_info.flag,
            sub_type=invitation_info.sub_type,
            operator_id=operator_id,
            status=status,
        )


class GroupInfoDAO(SystemInfoDAOBase[GroupInfo]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_info(
        self,
        group_id: str,
        group_name: Optional[str],
        status: GroupStatusEnum,
        operator_id: Optional[str],
        effective_time: datetime,
        remark: Optional[str] = None,
    ) -> GroupInfo:
        group_info = await self.session.execute(
            insert(GroupInfo)
            .values(
                group_id=group_id,
                group_name=group_name,
                status=status,
                operator_id=operator_id,
                update_time=datetime.now(),
                create_time=datetime.now(),
                effective_time=effective_time,
                remark=remark,
            )
            .on_conflict_do_update(
                index_elements=[GroupInfo.group_id],
                set_=dict(
                    group_id=group_id,
                    group_name=group_name,
                    status=status,
                    operator_id=operator_id,
                    update_time=datetime.now(),
                    effective_time=effective_time,
                    remark=remark,
                ),
            )
            .returning(GroupInfo)
        )

        return group_info.scalar_one()

    async def get_all_info(self) -> Sequence[GroupInfo]:
        return (await self.session.execute(select(GroupInfo))).scalars().all()

    async def update_status(
        self,
        group_id: str,
        status: GroupStatusEnum,
        operator_id: str,
        remark: Optional[str] = None,
    ) -> GroupInfo:
        group_info = await self.session.execute(
            update(GroupInfo)
            .where(GroupInfo.group_id == group_id)
            .values(status=status.value, operator_id=operator_id, remark=remark)
            .returning(GroupInfo)
        )
        return group_info.scalar_one()

    async def update_effective_time(
        self,
        group_id: str,
        effective_time: datetime,
        operator_id: str,
    ) -> GroupInfo:
        group_info = await self.session.execute(
            update(GroupInfo)
            .where(GroupInfo.group_id == group_id)
            .values(effective_time=effective_time, operator_id=operator_id)
            .returning(GroupInfo)
        )
        return group_info.scalar_one()

    async def update_group_name(
        self,
        group_id: str,
        group_name: str,
        operator_id: str,
    ) -> GroupInfo | None:
        group_info = await self.session.execute(
            update(GroupInfo)
            .where(GroupInfo.group_id == group_id, GroupInfo.group_name != group_name)
            .values(group_name=group_name, operator_id=operator_id)
            .returning(GroupInfo)
        )
        return group_info.scalar_one_or_none()

    async def get_info_by_status(
        self,
        status: GroupStatusEnum,
    ) -> Sequence[GroupInfo]:
        return (
            (
                await self.session.execute(
                    select(GroupInfo).where(GroupInfo.status == status)
                )
            )
            .scalars()
            .all()
        )

    async def get_info_by_group_id(self, group_id: str) -> GroupInfo | None:
        return (
            await self.session.execute(
                select(GroupInfo).where(GroupInfo.group_id == group_id)
            )
        ).scalar_one_or_none()


class GroupLogDAO(SystemLogDAOBase[GroupLog]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert_log(
        self,
        group_id: str,
        group_name: Optional[str],
        status: GroupStatusEnum,
        operator_id: Optional[str],
        effective_time: datetime,
        group_info_id: int,
        remark: Optional[str] = None,
    ) -> GroupLog:
        group_log = GroupLog(
            group_id=group_id,
            group_name=group_name,
            status=status,
            operator_id=operator_id,
            effective_time=effective_time,
            create_time=datetime.now(),
            group_info_id=group_info_id,
            remark=remark,
        )
        self.session.add(group_log)

        return group_log


class GroupService(SystemServiceBase):
    def __init__(
        self,
        group_info_dao: GroupInfoDAO,
        group_log_dao: GroupLogDAO,
    ) -> None:
        self.group_info_dao = group_info_dao
        self.group_log_dao = group_log_dao

    async def upsert_info_with_log(
        self,
        group_id: str,
        group_name: Optional[str],
        status: GroupStatusEnum,
        operator_id: Optional[str],
        effective_time: datetime = datetime.now(),
        remark: Optional[str] = None,
    ) -> GroupInfo:
        group_info = await self.group_info_dao.upsert_info(
            group_id=group_id,
            group_name=group_name,
            status=status,
            operator_id=operator_id,
            effective_time=effective_time,
            remark=remark,
        )
        await self.group_log_dao.insert_log(
            group_id=group_id,
            group_name=group_name,
            status=status,
            operator_id=operator_id,
            effective_time=effective_time,
            group_info_id=group_info.id,
            remark=remark,
        )
        return group_info

    async def update_status_with_log(
        self,
        group_id: str,
        status: GroupStatusEnum,
        operator_id: str,
        effective_time: datetime,
        # effective_time: datetime = datetime.now(),
        remark: Optional[str] = None,
    ) -> None:
        group_info = await self.upsert_info_with_log(
            group_id=group_id,
            group_name=None,
            status=status,
            operator_id=operator_id,
            remark=remark,
            effective_time=effective_time,
        )
        await self.group_log_dao.insert_log(
            group_id=group_id,
            group_name=group_info.group_name,
            status=status,
            operator_id=operator_id,
            effective_time=group_info.effective_time,
            group_info_id=group_info.id,
            remark=remark,
        )

    async def update_effective_time_with_log(
        self,
        group_id: str,
        effective_time: datetime,
        operator_id: str,
    ) -> None:
        if group_info := await self.group_info_dao.update_effective_time(
            group_id, effective_time, operator_id
        ):
            await self.group_log_dao.insert_log(
                group_id=group_id,
                group_name=group_info.group_name,
                status=group_info.status,
                operator_id=operator_id,
                effective_time=effective_time,
                group_info_id=group_info.id,
                remark=f"更新群组有效期为{effective_time}",
            )

    async def update_name_with_log(
        self,
        group_id: str,
        group_name: str,
        operator_id: str,
    ) -> None:
        if group_info := await self.group_info_dao.update_group_name(
            group_id, group_name, operator_id
        ):
            await self.group_log_dao.insert_log(
                group_id=group_id,
                group_name=group_info.group_name,
                status=group_info.status,
                operator_id=operator_id,
                effective_time=group_info.effective_time,
                group_info_id=group_info.id,
                remark=group_info.remark,
            )


class UserInfoDAO(SystemInfoDAOBase[UserInfo]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_info(
        self,
        user_id: str,
        user_name: Optional[str],
        status: UserStatusEnum,
        operator_id: str,
        remark: Optional[str] = None,
    ) -> UserInfo:
        user_info_id = await self.session.execute(
            insert(UserInfo)
            .values(
                user_id=user_id,
                user_name=user_name,
                status=status.value,
                operator_id=operator_id,
                update_time=datetime.now(),
                create_time=datetime.now(),
                remark=remark,
            )
            .on_conflict_do_update(
                index_elements=[UserInfo.user_id],
                set_=dict(
                    user_name=user_name,
                    status=status.value,
                    operator_id=operator_id,
                    update_time=datetime.now(),
                    remark=remark,
                ),
            )
            .returning(UserInfo)
        )

        return user_info_id.scalar_one()

    async def get_all_info(self) -> Sequence[UserInfo]:
        return (await self.session.execute(select(UserInfo))).scalars().all()

    async def update_status(
        self,
        user_id: str,
        status: UserStatusEnum,
        operator_id: str,
        remark: Optional[str] = None,
    ) -> UserInfo:
        user_info = await self.session.execute(
            update(UserInfo)
            .where(UserInfo.user_id == user_id)
            .values(status=status.value, operator_id=operator_id, remark=remark)
            .returning(UserInfo)
        )
        return user_info.scalar_one()

    async def update_effective_time(
        self,
        user_id: str,
        effective_time: datetime,
        operator_id: str,
    ) -> UserInfo:
        return (
            await self.session.execute(
                update(UserInfo)
                .where(UserInfo.user_id == user_id)
                .values(effective_time=effective_time, operator_id=operator_id)
                .returning(UserInfo)
            )
        ).scalar_one()

    async def update_user_name(
        self,
        user_id: str,
        user_name: str,
        operator_id: str,
    ) -> UserInfo | None:
        user_info = await self.session.execute(
            update(UserInfo)
            .where(UserInfo.user_id == user_id, UserInfo.user_name != user_name)
            .values(user_name=user_name, operator_id=operator_id)
            .returning(UserInfo)
        )
        return user_info.scalar_one_or_none()

    async def get_info_by_status(
        self,
        status: UserStatusEnum,
    ) -> Sequence[UserInfo]:
        return (
            (
                await self.session.execute(
                    select(UserInfo).where(UserInfo.status == status)
                )
            )
            .scalars()
            .all()
        )

    async def get_info_by_user_id(self, user_id: str) -> UserInfo | None:
        return (
            await self.session.execute(
                select(UserInfo).where(UserInfo.user_id == user_id)
            )
        ).scalar_one_or_none()


class UserLogDAO(SystemLogDAOBase[UserLog]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert_log(
        self,
        user_id: str,
        user_name: Optional[str],
        status: UserStatusEnum,
        operator_id: Optional[str],
        effective_time: datetime,
        user_info_id: int,
        remark: Optional[str] = None,
    ) -> UserLog:
        user_log = UserLog(
            user_id=user_id,
            user_name=user_name,
            status=status,
            operator_id=operator_id,
            effective_time=effective_time,
            create_time=datetime.now(),
            user_info_id=user_info_id,
            remark=remark,
        )
        self.session.add(user_log)

        return user_log


class UserService(SystemServiceBase):
    def __init__(
        self,
        user_info_dao: UserInfoDAO,
        user_log_dao: UserLogDAO,
    ) -> None:
        self.user_info_dao = user_info_dao
        self.user_log_dao = user_log_dao

    async def upsert_info_with_log(
        self,
        user_id: str,
        user_name: Optional[str],
        status: UserStatusEnum,
        operator_id: str,
        remark: Optional[str] = None,
    ) -> tuple[UserInfo, UserLog]:
        user_info = await self.user_info_dao.upsert_info(
            user_id=user_id,
            user_name=user_name,
            status=status,
            operator_id=operator_id,
            remark=remark,
        )
        user_log = await self.user_log_dao.insert_log(
            user_id=user_id,
            user_name=user_name,
            status=status,
            operator_id=operator_id,
            effective_time=user_info.effective_time,
            user_info_id=user_info.id,
            remark=remark,
        )
        return user_info, user_log

    async def update_status_with_log(
        self,
        user_id: str,
        status: UserStatusEnum,
        operator_id: str,
        remark: Optional[str] = None,
    ) -> None:
        user_info = await self.user_info_dao.update_status(
            user_id, status, operator_id, remark
        )
        await self.user_log_dao.insert_log(
            user_id=user_id,
            user_name=user_info.user_name,
            status=status,
            operator_id=operator_id,
            effective_time=user_info.effective_time,
            user_info_id=user_info.id,
            remark=remark,
        )

    async def update_effective_time_with_log(
        self,
        user_id: str,
        effective_time: datetime,
        operator_id: str,
    ) -> None:
        if user_info := await self.user_info_dao.update_effective_time(
            user_id, effective_time, operator_id
        ):
            await self.user_log_dao.insert_log(
                user_id=user_id,
                user_name=user_info.user_name,
                status=user_info.status,
                operator_id=operator_id,
                effective_time=effective_time,
                user_info_id=user_info.id,
                remark=f"更新用户有效期为{effective_time}",
            )

    async def update_name_with_log(
        self,
        user_id: str,
        user_name: str,
        operator_id: str,
    ) -> None:
        if user_info := await self.user_info_dao.update_user_name(
            user_id, user_name, operator_id
        ):
            await self.user_log_dao.insert_log(
                user_id=user_id,
                user_name=user_info.user_name,
                status=user_info.status,
                operator_id=operator_id,
                effective_time=user_info.effective_time,
                user_info_id=user_info.id,
                remark=user_info.remark,
            )


class PluginInfoDAO(SystemInfoDAOBase[PluginInfo]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_info(
        self,
        plugin_raw_name: str,
        plugin_metadata_name: str,
        plugin_module_name: str,
        plugin_description: str,
        plugin_usage: str,
        trigger_type: TriggerTypeEnum,
        plugin_permission: PluginPermissionEnum,
    ) -> PluginInfo:
        plugin_info = (
            await self.session.execute(
                insert(PluginInfo)
                .values(
                    plugin_raw_name=plugin_raw_name,
                    plugin_metadata_name=plugin_metadata_name,
                    plugin_module_name=plugin_module_name,
                    plugin_description=plugin_description,
                    plugin_usage=plugin_usage,
                    trigger_type=trigger_type,
                    plugin_permission=plugin_permission,
                    update_time=datetime.now(),
                    create_time=datetime.now(),
                )
                .on_conflict_do_update(
                    index_elements=[PluginInfo.plugin_raw_name],
                    set_=dict(
                        plugin_raw_name=plugin_raw_name,
                        plugin_metadata_name=plugin_metadata_name,
                        plugin_module_name=plugin_module_name,
                        plugin_description=plugin_description,
                        plugin_usage=plugin_usage,
                        trigger_type=trigger_type,
                        plugin_permission=plugin_permission,
                        update_time=datetime.now(),
                    ),
                )
                .returning(PluginInfo)
            )
        ).scalar_one()

        return plugin_info

    async def get_all_info(self) -> Sequence[PluginInfo]:
        return (await self.session.execute(select(PluginInfo))).scalars().all()

    async def get_info_by_name(self, plugin_name: str) -> PluginInfo | None:
        return (
            await self.session.execute(
                select(PluginInfo).where(PluginInfo.plugin_raw_name == plugin_name)
            )
        ).scalar_one_or_none()

    async def get_info_by_trigger_type(
        self, trigger_type: TriggerTypeEnum
    ) -> Sequence[PluginInfo]:
        return (
            (
                await self.session.execute(
                    select(PluginInfo).where(PluginInfo.trigger_type == trigger_type)
                )
            )
            .scalars()
            .all()
        )

    async def get_info_by_permission(
        self,
        plugin_permission: PluginPermissionEnum,
    ) -> Sequence[PluginInfo]:
        return (
            (
                await self.session.execute(
                    select(PluginInfo).where(
                        PluginInfo.plugin_permission == plugin_permission
                    )
                )
            )
            .scalars()
            .all()
        )


class PluginLogDAO(SystemLogDAOBase[PluginLog]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert_log(
        self,
        plugin_id: int,
        operator_id: str,
        event_json: dict,
        event_type: OnebotV11EventEnum,
    ) -> PluginLog:
        plugin_log = PluginLog(
            plugin_id=plugin_id,
            operator_id=operator_id,
            event_json=event_json,
            event_type=event_type,
            create_time=datetime.now(),
        )
        self.session.add(plugin_log)

        return plugin_log


class PluginService(SystemServiceBase):
    def __init__(
        self,
        session: AsyncSession,
        plugin_info_dao: PluginInfoDAO,
        plugin_log_dao: PluginLogDAO,
    ) -> None:
        self.session = session
        self.plugin_info_dao = plugin_info_dao
        self.plugin_log_dao = plugin_log_dao

    async def upsert_info_with_log(
        self,
        plugin_raw_name: str,
        plugin_metadata_name: str,
        plugin_module_name: str,
        plugin_description: str,
        plugin_usage: str,
        trigger_type: TriggerTypeEnum,
        plugin_permission: PluginPermissionEnum,
        operator_id: str,
        event_json: dict,
        event_type: OnebotV11EventEnum,
    ) -> tuple[PluginInfo, PluginLog]:
        plugin_info = await self.plugin_info_dao.upsert_info(
            plugin_raw_name=plugin_raw_name,
            plugin_metadata_name=plugin_metadata_name,
            plugin_module_name=plugin_module_name,
            plugin_description=plugin_description,
            plugin_usage=plugin_usage,
            trigger_type=trigger_type,
            plugin_permission=plugin_permission,
        )
        plugin_log = await self.plugin_log_dao.insert_log(
            plugin_id=plugin_info.id,
            operator_id=operator_id,
            event_json=event_json,
            event_type=event_type,
        )
        return plugin_info, plugin_log
