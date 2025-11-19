"""
wordbank 迁移脚本
将原先的 wordbank.json 迁移至 wordbank.sqlite


cache = {
    "trigger1": {
        "p1": [
            {
                "response": "Response for p1",
                "rule": {"user_id": "1", "group_id": "100"},
                "weight": 1,
            },
# 更多响应对象...
        ],
        "p2": [
            {
                "response": "Response for p2",
                "rule": {"user_id": "2", "group_id": "200"},
                "weight": 2,
            },
            # 更多响应对象...
        ],
        # p3, p4, p5 等其他优先级...
    },
    # 更多触发词...
}


"""

import asyncio
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from nonebot.adapters.onebot.v11.message import Message
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from plugins.user_plugins.wordbank.process import (
    message_to_string,
)

from .database import (
    AdditionLog,
    Approval,
    ApprovalLog,
    ApprovalStatusEnum,
    Response,
    Trigger,
)
from .database import (
    Base as wordbank_base,
)
from .database import (
    async_session as wordbank_async_session,
)
from .database import (
    engine as wordbank_engine,
)


async def insert_data(t, rl, session: AsyncSession):
    # for t, rl in migrate_dict.items():
    async with asyncio.Semaphore(1000):
        trigger_text, extra_info, trigger_plain_text = t
        trigger = (
            await session.execute(
                insert(Trigger)
                .values(
                    trigger_text=trigger_text,
                    # plain_text=trigger_plain_text,
                    trigger_config={
                        "probability": 1.0,
                        "lifecycle": 60 * 60.0,
                    }
                    if extra_info
                    and json.loads(extra_info).get("action")
                    in [
                        "GROUP_JOIN",
                        "AT_MENTIONED",
                        "POKE_MENTIONED",
                    ]
                    else {
                        "probability": 1.0
                        if (not trigger_text or len(trigger_text) > 4)
                        else 0.5
                    },
                    availability=True,
                    extra_info=extra_info,
                )
                .returning(Trigger)
            )
        ).scalar_one()
        # await session.flush()
        for r in rl:
            response = (
                await session.execute(
                    insert(Response)
                    .values(
                        trigger_id=trigger.trigger_id,
                        response_text=r["response_text"],
                        # plain_text=r["plain_text"],
                        response_rule_conditions=r["rule_conditions"],
                        priority=r["priority"],
                        created_by=r["created_by"],
                        created_at=r["created_at"],
                        availability=True,
                    )
                    .returning(Response)
                )
            ).scalar_one()

            # await session.flush()

            approval = (
                await session.execute(
                    insert(Approval)
                    .values(
                        trigger_id=trigger.trigger_id,
                        response_id=response.response_id,
                        current_status=ApprovalStatusEnum.APPROVED,
                        user_id="1479559098",
                    )
                    .returning(Approval)
                )
            ).scalar_one()
            # await session.flush()
            await session.execute(
                insert(ApprovalLog).values(
                    approval_id=approval.approval_id,
                    status=ApprovalStatusEnum.PENDING,
                    user_id=r["created_by"],
                    success_status=True,
                )
            )

            approval = ApprovalLog(
                approval_id=approval.approval_id,
                status=ApprovalStatusEnum.APPROVED,
                user_id="1479559098",
                success_status=True,
            )

            approval_log_approved = (
                await session.execute(
                    insert(ApprovalLog)
                    .values(
                        approval_id=approval.approval_id,
                        status=ApprovalStatusEnum.APPROVED,
                        user_id="1479559098",
                        success_status=True,
                    )
                    .returning(ApprovalLog)
                )
            ).scalar_one()

            # await session.flush()
            await session.execute(
                insert(AdditionLog).values(
                    trigger_id=trigger.trigger_id,
                    response_id=response.response_id,
                    user_id=r["created_by"],
                    add_source={"user_id": str(r["created_by"])},
                    created_message_id="-1",
                    approval_id=approval_log_approved.approval_id,
                )
            )


def get_migrate_dict():
    with open(Path(__file__).parent / "wordbank.json", "r", encoding="utf-8") as f:
        wordbank = json.load(f)

    migrate_dict = defaultdict(list)

    for i, j in wordbank.items():
        if i == "group":
            for group_id, j in j.items():
                for trigger_texts, response_list in j.items():
                    for response in response_list:
                        migrate_dict[
                            (
                                message_to_string(Message(trigger_texts))[0],
                                None,
                                Message(trigger_texts).extract_plain_text(),
                            )
                        ].append(
                            {
                                "response_text": message_to_string(
                                    Message(response["value"])
                                )[0],
                                "plain_text": Message(
                                    response["value"]
                                ).extract_plain_text(),
                                "rule_conditions": {"group_id": {"$eq": int(group_id)}}
                                if group_id != "global"
                                else {},
                                "priority": 2 if group_id != "global" else 3,
                                "created_by": response["auth"],
                                "created_at": datetime.strptime(
                                    response["time"], "%Y-%m-%d"
                                ),
                                "trigger_threshold": 0,
                            }
                        )
        elif i == "friend":
            for user_id, j in j.items():
                for trigger_texts, response_list in j.items():
                    for response in response_list:
                        migrate_dict[
                            (
                                message_to_string(Message(trigger_texts))[0],
                                None,
                                Message(trigger_texts).extract_plain_text(),
                            )
                        ].append(
                            {
                                "response_text": message_to_string(
                                    Message(response["value"])
                                )[0],
                                "plain_text": Message(
                                    response["value"]
                                ).extract_plain_text(),
                                "rule_conditions": {"user_id": {"$eq": int(user_id)}},
                                "priority": 1,
                                "created_by": response["auth"],
                                "created_at": datetime.strptime(
                                    response["time"], "%Y-%m-%d"
                                ),
                                "trigger_threshold": 0,
                            }
                        )
        else:
            for i, v in j.items():
                if i == "handle_new_member":
                    for response_text in v:
                        migrate_dict[
                            (None, json.dumps(dict(action="GROUP_JOIN")), None)
                        ].append(
                            {
                                "response_text": message_to_string(
                                    Message(response_text)
                                )[0],
                                "plain_text": Message(
                                    response_text
                                ).extract_plain_text(),
                                "rule_conditions": {},
                                "priority": 1,
                                "created_by": "1479559098",
                                "created_at": datetime.strptime(
                                    "2020-08-13", "%Y-%m-%d"
                                ),
                                "trigger_threshold": 1,
                            }
                        )
                else:
                    if i == "at_msg_reply":
                        trigger_name = json.dumps(dict(action="AT_MENTIONED"))
                    else:
                        trigger_name = json.dumps(dict(action="POKE_MENTIONED"))

                    for th, response_list in v.items():
                        if th == "rage":
                            trigger_threshold = {"$gt": 10}
                        elif th == "annoy":
                            trigger_threshold = {"$range": [6, 10]}
                        else:
                            trigger_threshold = {"$range": [0, 5]}
                        for response_text in response_list:
                            migrate_dict[(None, trigger_name, None)].append(
                                {
                                    "response_text": message_to_string(
                                        Message(response_text)
                                    )[0],
                                    "plain_text": Message(
                                        response_text
                                    ).extract_plain_text(),
                                    "rule_conditions": {
                                        "call_count": trigger_threshold,
                                    },
                                    "priority": 1,
                                    "created_by": "1479559098",
                                    "created_at": datetime.strptime(
                                        "2020-08-13", "%Y-%m-%d"
                                    ),
                                    "trigger_threshold": trigger_threshold,
                                    "trigger_config": {
                                        "probability": 1.0,
                                        "lifecycle": 60 * 60.0,
                                    },
                                }
                            )

    return migrate_dict


async def main():
    async with wordbank_engine.begin() as conn:
        await conn.run_sync(wordbank_base.metadata.create_all)
    async with wordbank_async_session() as session:
        tasks = [insert_data(t, rl, session) for t, rl in get_migrate_dict().items()]
        await asyncio.gather(*tasks)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
