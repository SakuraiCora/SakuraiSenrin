from datetime import datetime, timedelta
from typing import Dict, Optional, Sequence

from sqlalchemy import and_, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.cache.memory_cache import memory_cache
from plugins.user_plugins.wordbank.database import (
    AdditionLog,
    Approval,
    ApprovalLog,
    DeletionLog,
    MessageApproval,
    Response,
    ResponseLog,
    ResponseModifyLog,
    RestorationLog,
    SearchArgs,
    Trigger,
    TriggerLog,
    TriggerModifyLog,
    WordbankFTS,
    WordbankVote,
    WordbankVoteLog,
)
from plugins.user_plugins.wordbank.exceptions import (
    CannotModifyTriggerRuleConditionsException,
    # DuplicateTriggerResponseException,
    PermissionDeniedException,
)
from plugins.user_plugins.wordbank.process import or_merge_rules
from src.utils.enums import ApprovalStatusEnum, VoteOptionEnum, VoteStatusEnum
from src.utils.message_builder import NoticeBuilder


class TriggerDAO:
    def __init__(self, session: AsyncSession, trigger_log_service: "TriggerLogService"):
        self._session = session
        self._trigger_log_service = trigger_log_service

    async def get_responses_for_trigger(self, trigger_id: int):
        result = await self._session.execute(
            select(Response).where(Response.trigger_id == trigger_id)
        )
        return result.scalars().all()

    async def update_availability(self, trigger_id: int, availability: bool) -> None:
        trigger = await self.get_trigger_by_id(trigger_id)
        if trigger:
            trigger.availability = availability

    async def modify_trigger(
        self,
        trigger_id: int,
        trigger_text: str,
        trigger_config: Dict,
        user_id: str,
    ) -> None:
        success_status = False

        if user_id in memory_cache.super_users:
            await self._session.execute(
                update(Trigger)
                .where(Trigger.trigger_id == trigger_id)
                .values(trigger_text=trigger_text, trigger_config=trigger_config)
            )
            success_status = True

        await self._trigger_log_service.log_trigger_modification(
            trigger_id=trigger_id,
            user_id=user_id,
            trigger_text=trigger_text,
            trigger_config=trigger_config,
            success_status=success_status,
        )

        if not success_status:
            raise PermissionDeniedException(
                NoticeBuilder.exception("您没有权限修改此触发词。")
            )

    async def get_trigger_by_message_id(self, message_id: str) -> Optional[Trigger]:
        return (
            await self._session.execute(
                select(TriggerLog).where(TriggerLog.message_id == message_id)
            )
        ).scalar_one_or_none()

    async def get_trigger_by_id(self, trigger_id: int) -> Optional[Trigger]:
        return (
            await self._session.execute(
                select(Trigger).where(Trigger.trigger_id == trigger_id)
            )
        ).scalar_one_or_none()

    async def get_trigger_by_word_and_extra_info(
        self, trigger_text: str, extra_info: Optional[str]
    ) -> Optional[Trigger]:
        result = await self._session.execute(
            select(Trigger).where(
                and_(
                    Trigger.trigger_text == trigger_text,
                    Trigger.extra_info == extra_info,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_trigger(
        self, trigger_text: str, trigger_config: Dict, extra_info: Optional[str]
    ) -> Trigger:
        return (
            await self._session.execute(
                insert(Trigger)
                .values(
                    trigger_text=trigger_text,
                    trigger_config=trigger_config,
                    extra_info=extra_info,
                )
                .returning(Trigger)
            )
        ).scalar_one()


class TriggerLogService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def log_trigger_call(
        self, trigger_id: int, user_id: str, message_id: str
    ) -> None:
        trigger_log = TriggerLog(
            trigger_id=trigger_id, user_id=user_id, message_id=message_id
        )
        self._session.add(trigger_log)

    async def log_trigger_modification(
        self,
        trigger_id: int,
        user_id: str,
        trigger_text: str,
        trigger_config: Dict,
        success_status: bool,
    ) -> None:
        trigger_modify_log = TriggerModifyLog(
            trigger_id=trigger_id,
            user_id=user_id,
            trigger_text=trigger_text,
            trigger_config=trigger_config,
            success_status=success_status,
        )
        self._session.add(trigger_modify_log)

    async def get_trigger_call_count(
        self, trigger_id: int, user_id: str, time_range: Optional[timedelta]
    ) -> int:
        query = select(func.count(TriggerLog.log_id)).where(
            TriggerLog.trigger_id == trigger_id, TriggerLog.user_id == user_id
        )

        if time_range:
            since_time = datetime.now() - time_range
            query = query.where(TriggerLog.call_time >= since_time)

        return (await self._session.execute(query)).scalar_one()


class ResponseDAO:
    def __init__(
        self, session: AsyncSession, response_log_service: "ResponseLogService"
    ):
        self._session = session
        self._response_log_service = response_log_service

    async def update_availability(self, response_id: int, availability: bool) -> None:
        response = await self.get_response_by_id(response_id)
        if response:
            response.availability = availability

    async def get_response_by_trigger_and_response_text(
        self, trigger_id: int, response_text: str
    ) -> Response:
        result = await self._session.execute(
            select(Response)
            .where(Response.trigger_id == trigger_id)
            .where(Response.response_text == response_text)
        )
        return result.scalar_one_or_none()

    async def log_response_call(self, response_log: ResponseLog) -> None:
        self._session.add(response_log)

    async def modify_response(
        self,
        response_id: int,
        response_text: str,
        response_rule_conditions: Dict,
        weight: int,
        user_id: str,
    ) -> None:
        response = (
            await self._session.execute(
                select(Response).where(Response.response_id == response_id)
            )
        ).scalar_one()

        success_status = False

        if user_id in memory_cache.super_users or user_id == response.created_by:
            await self._session.execute(
                update(Response)
                .where(Response.response_id == response_id)
                .values(
                    response_text=response_text,
                    weight=weight,
                    response_rule_conditions=response_rule_conditions,
                )
            )
            success_status = True

        await self._response_log_service.log_response_modification(
            response_id=response_id,
            user_id=user_id,
            response_text=response_text,
            response_rule_conditions=response_rule_conditions,
            weight=weight,
            success_status=success_status,
        )

        if not success_status:
            raise PermissionDeniedException(
                NoticeBuilder.exception("您没有权限修改此响应词。")
            )

    async def get_response_by_id(self, response_id: int) -> Optional[Response]:
        return (
            await self._session.execute(
                select(Response).where(Response.response_id == response_id)
            )
        ).scalar_one_or_none()

    async def update_response(self, response: Response) -> Response:
        self._session.add(response)
        await self._session.commit()
        return response

    async def create_response(
        self,
        trigger_id: int,
        response_text: str,
        response_rule_conditions: Dict,
        weight: int,
        priority: int,
        user_id: str,
    ) -> Response:
        return (
            await self._session.execute(
                insert(Response)
                .values(
                    trigger_id=trigger_id,
                    response_text=response_text,
                    response_rule_conditions=response_rule_conditions,
                    weight=weight,
                    priority=priority,
                    created_by=user_id,
                )
                .returning(Response)
            )
        ).scalar()

    async def get_entry_property_by_response_id(self, response_id: int) -> str:
        entry_property = (
            await self._session.execute(
                select(Response)
                .options(joinedload(Response.trigger_item))
                .where(Response.response_id == response_id)
            )
        ).scalar_one()
        await self._session.commit()

        response_details = (
            "📋 响应词详细信息:\n"
            f"🆔 响应词 ID: {entry_property.response_id}\n"
            f"⚖️ 响应词权重: {entry_property.weight}\n"
            f"🛠️ 响应规则: {entry_property.response_rule_conditions}\n"
            f"🕒 创建时间: {entry_property.created_at}\n"
            f"👤 创建者: {entry_property.created_by}\n"
            f"✅ 是否可用: {entry_property.availability}\n"
        )

        trigger_details = (
            "🚀 触发词详细信息:\n"
            f"🆔 触发词 ID: {entry_property.trigger_id}\n"
            f"🔧 触发词配置: {entry_property.trigger_item.trigger_config}\n"
        )

        return response_details + "\n" + trigger_details


class ResponseLogService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def log_response_call(
        self, response_id: int, user_id: str, message_id: str
    ) -> None:
        response_log = ResponseLog(
            response_id=response_id,
            user_id=user_id,
            message_id=message_id,
        )
        self._session.add(response_log)

    async def log_response_modification(
        self,
        response_id: int,
        user_id: str,
        response_text: str,
        response_rule_conditions: Dict,
        weight: int,
        success_status: bool,
    ) -> None:
        response_modify_log = ResponseModifyLog(
            response_id=response_id,
            user_id=user_id,
            response_text=response_text,
            response_rule_conditions=response_rule_conditions,
            weight=weight,
            success_status=success_status,
        )
        self._session.add(response_modify_log)

    async def get_response_log_by_message_id(self, message_id: str) -> ResponseLog:
        return (
            await self._session.execute(
                select(ResponseLog).where(ResponseLog.message_id == message_id)
            )
        ).scalar_one()

    async def get_response_call_count(self, response_id: int) -> int:
        return (
            await self._session.execute(
                select(func.count(ResponseLog.log_id)).where(
                    ResponseLog.response_id == response_id
                )
            )
        ).scalar_one()


class ApprovalDAO:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def upsert_approval(self, approval: Approval) -> Approval:
        return (
            await self._session.execute(
                insert(Approval)
                .values(
                    trigger_id=approval.trigger_id,
                    response_id=approval.response_id,
                    current_status=approval.current_status,
                    user_id=approval.user_id,
                    created_at=approval.created_at,
                    updated_at=datetime.now(),
                )
                .on_conflict_do_update(
                    index_elements=[Approval.response_id],
                    set_=dict(
                        trigger_id=approval.trigger_id,
                        response_id=approval.response_id,
                        current_status=approval.current_status,
                        user_id=approval.user_id,
                        updated_at=datetime.now(),
                    ),
                )
                .returning(Approval)
            )
        ).scalar()

    async def update_approval_status(
        self, approval: Approval, new_status: ApprovalStatusEnum
    ):
        approval.current_status = new_status
        approval.updated_at = datetime.now()

    async def get_approval_by_id(self, approval_id: int) -> Approval:
        result = await self._session.execute(
            select(Approval).where(Approval.approval_id == approval_id)
        )
        return result.scalar_one()

    async def get_approval_by_response_id(self, response_id: int):
        result = await self._session.execute(
            select(Approval).where(Approval.response_id == response_id)
        )
        return result.scalar_one()

    async def get_pending_approvals(self):
        result = await self._session.execute(
            select(Approval).where(
                Approval.current_status == ApprovalStatusEnum.PENDING
            )
        )
        return result.scalars().all()


class ApprovalLogDAO:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_approval_log(self, approval_log: ApprovalLog) -> ApprovalLog:
        self._session.add(approval_log)

        return approval_log

    async def get_logs_by_approval_id(self, approval_id: int):
        result = await self._session.execute(
            select(ApprovalLog).where(ApprovalLog.approval_id == approval_id)
        )
        return result.scalars().all()

    async def get_succeed_approved_approval_logs_by_response_id(self, response_id: int):
        result = await self._session.execute(
            select(ApprovalLog)
            .join(Approval, Approval.approval_id == ApprovalLog.approval_id)
            .where(
                Approval.response_id == response_id,
                ApprovalLog.success_status,
                ApprovalLog.status != ApprovalStatusEnum.PENDING,
            )
        )
        return result.scalars().all()

    async def get_approval_by_approval_id(self, approval_id: int) -> Approval:
        return (
            await self._session.execute(
                select(Approval)
                .options(joinedload(Approval.logs))
                .where(Approval.approval_id == approval_id)
            )
        ).scalar_one()


class MessageApprovalDAO:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_message_approval(
        self, message_approval: MessageApproval
    ) -> MessageApproval:
        self._session.add(message_approval)
        return message_approval

    async def create_message_approval_by_approval_and_message_id(
        self, approval: Approval, message_id: str
    ) -> MessageApproval:
        return (
            await self._session.execute(
                (
                    insert(MessageApproval).values(
                        approval_id=approval.approval_id, message_id=message_id
                    )
                ).returning(MessageApproval)
            )
        ).scalar_one()

    async def get_message_approval_by_message_id(
        self, message_id: str
    ) -> MessageApproval:
        return (
            await self._session.execute(
                select(MessageApproval).where(MessageApproval.message_id == message_id)
            )
        ).scalar_one_or_none()


class ApprovalResponseService:
    def __init__(
        self,
        approval_dao: ApprovalDAO,
        response_dao: ResponseDAO,
        approval_log_dao: ApprovalLogDAO,
    ):
        self._approval_dao = approval_dao
        self._response_dao = response_dao
        self._approval_log_dao = approval_log_dao

    async def approval_response(
        self, response_id: int, user_id: str, approval_action: ApprovalStatusEnum
    ):
        approval = await self._approval_dao.get_approval_by_response_id(response_id)
        await self._approval_dao.update_approval_status(approval, approval_action)
        await self._approval_log_dao.create_approval_log(
            ApprovalLog(
                approval_id=approval.approval_id,
                status=approval_action,
                user_id=user_id,
                success_status=True,
            )
        )
        if approval_action == ApprovalStatusEnum.APPROVED:
            await self._response_dao.update_availability(response_id, True)
        else:
            await self._response_dao.update_availability(response_id, False)

    async def get_approval_history_beauty_message(
        self, approval_logs: Sequence[ApprovalLog]
    ) -> str:
        message_parts = []
        message_parts.append("🔍 审批历史记录 🔍")
        message_parts.append("--------------------")

        for log in approval_logs:
            log_message = (
                f"📝 审批ID: {log.approval_id}\n"
                f"📅 审批时间: {log.action_time.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                f"👤 审批人: {log.user_id}\n"
                f"✅ 审批状态: {log.status}\n"
            )
            message_parts.append(log_message)
            message_parts.append("--------------------")

        message_parts.append("🛑 以上是所有历史记录 🛑")

        full_message = "\n".join(message_parts)
        return full_message


class AdditionService:
    def __init__(
        self,
        session: AsyncSession,
        trigger_dao: TriggerDAO,
        response_dao: ResponseDAO,
        addition_log_service: "AdditionLogService",
        approval_dao: ApprovalDAO,
    ):
        self._session = session
        self._trigger_dao = trigger_dao
        self._response_dao = response_dao
        self._addition_log_service = addition_log_service
        self._approval_dao = approval_dao

    async def check_trigger_config(
        self, trigger: Trigger, trigger_config: Dict
    ) -> None:
        if trigger.trigger_config != trigger_config:
            CannotModifyTriggerRuleConditionsException(
                NoticeBuilder.warning("不可覆盖已有的触发规则。")
            )

    async def check_duplicate_trigger_response(
        self, trigger_id: int, response_text: str
    ) -> Response:
        existing_response = (
            await self._response_dao.get_response_by_trigger_and_response_text(
                trigger_id, response_text
            )
        )
        # if existing_response and existing_response.availability:
        #     raise DuplicateTriggerResponseException(
        #         NoticeBuilder.exception("该词条已存在，重复添加要挨揍哦？")
        #     )
        return existing_response

    async def add_trigger_and_response(
        self,
        trigger_text: str,
        trigger_config: Dict,
        response_text: str,
        response_rule_conditions: Dict,
        extra_info: Optional[str],
        weight: int,
        priority: int,
        user_id: str,
        add_source: Dict,
        created_message_id: str,
    ):
        trigger = await self._trigger_dao.get_trigger_by_word_and_extra_info(
            trigger_text, extra_info
        )
        if not trigger:
            trigger = await self._trigger_dao.create_trigger(
                trigger_text, trigger_config, extra_info
            )
            await self._session.commit()
        # else:     # TODO: 修改触发词相关配置实现
        #     await self._trigger_dao.modify_trigger(
        #         trigger.trigger_id, trigger_text, trigger_config, user_id
        #     )
        if exsited_response := await self.check_duplicate_trigger_response(
            trigger.trigger_id, response_text
        ):
            exsited_response.response_rule_conditions = or_merge_rules(
                exsited_response.response_rule_conditions, response_rule_conditions
            )
            response = await self._response_dao.update_response(exsited_response)
        else:
            response = await self._response_dao.create_response(
                trigger_id=trigger.trigger_id,
                response_text=response_text,
                response_rule_conditions=response_rule_conditions,
                weight=weight,
                priority=priority,
                user_id=user_id,
            )
        addition_log = (
            await self._session.execute(
                insert(AdditionLog)
                .values(
                    trigger_id=trigger.trigger_id,
                    response_id=response.response_id,
                    user_id=user_id,
                    add_source=add_source,
                    created_message_id=created_message_id,
                )
                .returning(AdditionLog)
            )
        ).scalar_one()
        approval = await self._approval_dao.upsert_approval(
            Approval(
                trigger_id=trigger.trigger_id,
                response_id=response.response_id,
                current_status=ApprovalStatusEnum.PENDING,
                user_id=user_id,
                created_at=datetime.now(),
            )
        )
        await self._session.commit()
        await self._addition_log_service.log_addition(addition_log)
        await self._addition_log_service.log_approval(
            approval, user_id, ApprovalStatusEnum.PENDING
        )

        return approval, response


class AdditionLogService:
    def __init__(self, session: AsyncSession, approval_log_dao: ApprovalLogDAO):
        self._session = session
        self._approval_log_dao = approval_log_dao

    async def log_addition(self, addition_log: AdditionLog) -> None:
        self._session.add(addition_log)

    async def log_approval(
        self, approval: Approval, user_id: str, status: ApprovalStatusEnum
    ) -> None:
        approval_log = ApprovalLog(
            approval_id=approval.approval_id,
            user_id=user_id,
            status=status,
            success_status=True,
        )
        await self._approval_log_dao.create_approval_log(approval_log)

    async def get_approval_log_by_response_id(self, response_id: int):
        return (
            (
                await self._session.execute(
                    select(AdditionLog)
                    .where(AdditionLog.response_id == response_id)
                    .order_by(AdditionLog.add_time.desc())
                )
            )
            .scalars()
            .all()[0]
        )


class DeletionService:
    def __init__(
        self,
        session: AsyncSession,
        trigger_dao: TriggerDAO,
        response_dao: ResponseDAO,
        deletion_log_service: "DeletionLogService",
        approval_dao: ApprovalDAO,
        approval_log_dao: ApprovalLogDAO,
    ):
        self._session = session
        self._trigger_dao = trigger_dao
        self._response_dao = response_dao
        self._deletion_log_service = deletion_log_service
        self._approval_dao = approval_dao
        self._approval_log_dao = approval_log_dao

    async def delete_trigger(self, trigger_id: int, user_id: str, delete_reason: str):
        success_status = False

        if user_id in memory_cache.super_users:
            await self._trigger_dao.update_availability(trigger_id, False)
            success_status = True

        deletion_log = DeletionLog(
            trigger_id=trigger_id,
            user_id=user_id,
            delete_reason=delete_reason,
            success_status=success_status,
        )
        await self._deletion_log_service.log_deletion(deletion_log)

        if not success_status:
            raise PermissionDeniedException(
                NoticeBuilder.exception("您没有权限删除该触发词。")
            )

    async def delete_response(
        self, trigger_id: int, response_id: int, user_id: str, delete_reason: str
    ):
        await self._response_dao.update_availability(response_id, False)
        approval = await self._approval_dao.get_approval_by_response_id(response_id)
        if approval.current_status == ApprovalStatusEnum.PENDING:
            await self._approval_dao.update_approval_status(
                approval, ApprovalStatusEnum.WITHDRAWN
            )
            await self._approval_log_dao.create_approval_log(
                ApprovalLog(
                    approval_id=approval.approval_id,
                    status=ApprovalStatusEnum.WITHDRAWN,
                    user_id=user_id,
                    success_status=True,
                )
            )

        deletion_log = DeletionLog(
            trigger_id=trigger_id,
            response_id=response_id,
            user_id=user_id,
            delete_reason=delete_reason,
            success_status=True,
        )
        await self._deletion_log_service.log_deletion(deletion_log)


class DeletionLogService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def log_deletion(self, deletion_log: "DeletionLogService") -> None:
        self._session.add(deletion_log)


class RestorationService:
    def __init__(
        self,
        session: AsyncSession,
        trigger_dao: TriggerDAO,
        response_dao: ResponseDAO,
        restoration_log_service: "RestorationLogService",
    ):
        self._session = session
        self._trigger_dao = trigger_dao
        self._response_dao = response_dao
        self._restoration_log_service = restoration_log_service

    async def restore_trigger(
        self, trigger_id: int, user_id: str, restore_reason: Optional[str] = None
    ) -> None:
        success_status = False

        if user_id in memory_cache.super_users:
            await self._trigger_dao.update_availability(trigger_id, True)
            success_status = True

        restoration_log = RestorationLog(
            trigger_id=trigger_id,
            user_id=user_id,
            restore_reason=restore_reason,
            success_status=success_status,
        )
        await self._restoration_log_service.log_restoration(restoration_log)

        if not success_status:
            raise PermissionDeniedException(
                NoticeBuilder.exception("您没有权限恢复该触发词。")
            )

    async def restore_response(
        self,
        trigger_id: int,
        response_id: int,
        user_id: str,
        restore_reason: Optional[str] = None,
    ) -> None:
        success_status = False

        if user_id in memory_cache.super_users:
            await self._response_dao.update_availability(response_id, True)
            success_status = True

        restoration_log = RestorationLog(
            trigger_id=trigger_id,
            response_id=response_id,
            user_id=user_id,
            restore_reason=restore_reason,
            success_status=success_status,
        )
        await self._restoration_log_service.log_restoration(restoration_log)

        if not success_status:
            raise PermissionDeniedException(
                NoticeBuilder.exception("您没有权限恢复该响应词。")
            )


class RestorationLogService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def log_restoration(self, restoration_log: "RestorationLogService") -> None:
        self._session.add(restoration_log)


class WordbankFTSDAO:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def general_search(self, search_args: SearchArgs) -> Sequence[WordbankFTS]:
        query = select(WordbankFTS)
        if search_args.trigger and search_args.trigger.strip():
            query = query.where(
                WordbankFTS.trigger_text.ilike(f"%{search_args.trigger}%")
            )
        if search_args.response and search_args.response.strip():
            query = query.where(
                WordbankFTS.response_text.ilike(f"%{search_args.response}%")
            )
        if search_args.author and search_args.author.strip():
            query = query.where(WordbankFTS.created_by.ilike(f"%{search_args.author}%"))
        return (await self._session.execute(query)).scalars().all()


class WordbankVoteDAO:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_vote(
        self, message_id: str, trigger_id: int, response_id: int, initiator: str
    ) -> WordbankVote:
        return (
            await self._session.execute(
                insert(WordbankVote)
                .values(
                    message_id=message_id,
                    trigger_id=trigger_id,
                    response_id=response_id,
                    initiator=initiator,
                    vote_status=VoteStatusEnum.IN_PROGRESS,
                )
                .returning(WordbankVote)
            )
        ).scalar_one()

    async def get_vote_by_id(self, vote_id: int) -> Optional[WordbankVote]:
        return (
            await self._session.execute(
                select(WordbankVote).where(WordbankVote.id == vote_id)
            )
        ).scalar_one_or_none()

    async def get_vote_by_trigger_id_and_response_id(
        self, trigger_id: int, response_id: int
    ) -> Optional[WordbankVote]:
        return (
            await self._session.execute(
                select(WordbankVote).where(
                    WordbankVote.trigger_id == trigger_id,
                    WordbankVote.response_id == response_id,
                )
            )
        ).scalar_one_or_none()

    async def update_vote_status(
        self, vote_id: int, new_status: VoteStatusEnum
    ) -> None:
        vote = await self.get_vote_by_id(vote_id)
        if vote:
            vote.vote_status = new_status


class WordbankVoteLogDAO:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_vote_log(
        self, message_id: str, vote_id: int, operator: str, option: VoteOptionEnum
    ) -> WordbankVoteLog:
        vote_log = WordbankVoteLog(
            message_id=message_id,
            vote_id=vote_id,
            operator=operator,
            option=option,
        )
        self._session.add(vote_log)

        return vote_log

    async def get_vote_log_by_vote_id(self, vote_id: int) -> Sequence[WordbankVoteLog]:
        return (
            (
                await self._session.execute(
                    select(WordbankVoteLog).where(WordbankVoteLog.vote_id == vote_id)
                )
            )
            .scalars()
            .all()
        )

    async def get_vote_log_by_vote_id_and_operator(
        self, vote_id: int, operator: str
    ) -> Optional[WordbankVoteLog]:
        return (
            await self._session.execute(
                select(WordbankVoteLog).where(
                    WordbankVoteLog.vote_id == vote_id,
                    WordbankVoteLog.operator == operator,
                )
            )
        ).scalar_one_or_none()

    async def get_support_vote_by_vote_id(
        self, vote_id: int
    ) -> Optional[Sequence[WordbankVoteLog]]:
        return (
            (
                await self._session.execute(
                    select(WordbankVoteLog).where(
                        WordbankVoteLog.vote_id == vote_id,
                        WordbankVoteLog.option == VoteOptionEnum.SUPPORT,
                    )
                )
            )
            .scalars()
            .all()
        )
