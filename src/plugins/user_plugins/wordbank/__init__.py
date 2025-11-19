import asyncio
import json
import random
from datetime import timedelta
from functools import wraps

from nonebot import CommandGroup, get_driver, on_fullmatch
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.event import (
    GroupDecreaseNoticeEvent,
    GroupIncreaseNoticeEvent,
    GroupMessageEvent,
    MessageEvent,
    PokeNotifyEvent,
    PrivateMessageEvent,
)
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import Arg, CommandArg, Depends
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata, on_message, on_type
from nonebot.rule import to_me
from nonebot.typing import T_State
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache.memory_cache import memory_cache
from src.config.general_config import general_config
from src.utils.common_helper import CommonHelper
from src.utils.enums import (
    ApprovalStatusEnum,
    PluginPermissionEnum,
    TriggerTypeEnum,
    VoteOptionEnum,
    VoteStatusEnum,
)
from src.utils.message_builder import AlertTemplate, NoticeBuilder

from .cache import generate_wordbank_cache
from .config import wordbank_config
from .dao import (
    AdditionLogService,
    AdditionService,
    ApprovalDAO,
    ApprovalLogDAO,
    ApprovalResponseService,
    DeletionLogService,
    DeletionService,
    MessageApprovalDAO,
    ResponseDAO,
    ResponseLogService,
    RestorationLogService,
    RestorationService,
    TriggerDAO,
    TriggerLogService,
    WordbankFTSDAO,
    WordbankVoteDAO,
    WordbankVoteLogDAO,
)
from .database import (
    Response,
    SearchArgs,
    Trigger,
    WordbankFTS,
    get_session,
)
from .exceptions import (
    DuplicateTriggerResponseException,
    PermissionDeniedException,
)
from .process import (
    find_first_matching_response,
    generate_wordbank_fts_image_by_pillow,
    generate_wordbank_fts_image_by_playwright,
    message_to_string,
    parse_response_rule_conditions,
    parse_trigger_config,
    process_extra_info,
    select_random_response,
    string_to_message,
    upload_image_to_github,
)

# TODO 迁移操作
# from src..migrate import main as migrate_main

# asyncio.run(migrate_main())

name = "学习词库"
description = """
学习词库:
  添加词条
  删除词条
  搜索词条
""".strip()

usage = f"""
📖 ===== {name} =====

命令前缀: #wordbank

1.添加词条 📝
  添加一条新的词条，请按照提示操作
  示例: #wordbank.add / #添加词条

2.搜索词条 🔍
  提供关键词以搜索词条，请按照提示操作
  示例: #wordbank.search / #搜索词条

3.查看词条信息 👀
  回复相关词条 "info" 或 "详情"，即可查看相关信息

4.查看词条审批历史 🛑
  回复相关词条 "history" 或 "审批历史"，即可查看相关审批历史

5.删除词条 🗑️
  回复相关词条 "del" 或 "删除"，即可按照提示删除相关词条

⚠️ 注意事项:
1. 添加的词条需要【管理员审核通过后】才能启用。
2. 默认规则为：当触发词长度 < 4 时，触发概率为 50%，否则 100%；默认开启群组隔离，即词条在群组之间不互通。
3. 如果普通用户想删除其他人添加的词条，可以在词条下方回复 del，并按照提示发起投票删除。
4. 如需进一步支持，请联系管理员，或加入反馈群「{general_config.support_group_id}」💬。

词条除了龙图、辱骂他人、看了生理不适的图片、以及r18（包括性暗示）都可以任意添加，当然删除权在管理者。如果全群触发的一直加不上去，可以试着改为本群触发，若是还是无法通过审核，则该词条可能不是那么的适合凛凛
乱教东西的话会进行封禁，时长不限，另外凛凛在群聊中给不喜欢的人带来困扰的话，可以选择屏蔽凛凛。

若是给您带来困扰，还请多多谅解
""".strip()

__plugin_meta__ = PluginMetadata(
    name=name,
    description=description,
    usage=usage,
    extra={
        "author": "SakuraiCora",
        "version": "0.1.0",
        "trigger": TriggerTypeEnum.ACTIVE,
        "permission": PluginPermissionEnum.EVERYONE,
    },
)

driver = get_driver()
manage_reply_matcher = on_message(rule=to_me(), priority=5, block=False)

wordbank_command_group = CommandGroup("wordbank", priority=5)
add_cmd = wordbank_command_group.command(
    "add",
    aliases={"添加词条"},
    priority=5,
    block=False,
)
# modify_cmd = wordbank_command_group.command(
#     "modify",
#     aliases={"修改词条"},
#     priority=5,
#     block=False,
# )
restore_cmd = wordbank_command_group.command(
    "restore",
    aliases={"恢复词条"},
    priority=5,
    block=False,
)
search_or_delete_cmd = wordbank_command_group.command(
    "search",
    aliases={"搜索词条", "删除词条"},
    priority=5,
    block=False,
)

vote_support_cmd = wordbank_command_group.command(
    "support",
    aliases={"支持删除"},
    priority=5,
    block=False,
)

vote_status_cmd = wordbank_command_group.command(
    "vote",
    aliases={"查看投票状态"},
    priority=5,
    block=False,
)

delete_trigger_reply_matcher = on_fullmatch(
    ("del trigger", "delete trigger", "删除触发词"),
    ignorecase=True,
    rule=to_me(),
    permission=SUPERUSER,
    priority=5,
    block=False,
)
delete_response_reply_matcher = on_fullmatch(
    ("del", "del response", "delete", "delete response", "删除", "删除响应词"),
    ignorecase=True,
    rule=to_me(),
    priority=5,
    block=False,
)

resotre_trigger_reply_matcher = on_fullmatch(
    ("rst trigger", "restore trigger", "恢复触发词"),
    ignorecase=True,
    rule=to_me(),
    permission=SUPERUSER,
    priority=5,
    block=False,
)
restore_response_reply_matcher = on_fullmatch(
    ("rst", "restore response", "restore", "restore response", "恢复", "恢复响应词"),
    ignorecase=True,
    rule=to_me(),
    priority=5,
    block=False,
)

# modify_trigger_reply_matcher = on_fullmatch(
#     ("m trigger", "modify trigger", "修改触发词"),
#     ignorecase=True,
#     rule=to_me(),
#     priority=5,
#     block=False,
# )
# modify_response_reply_matcher = on_fullmatch(
#     ("m", "modify response", "修改", "修改响应词"),
#     ignorecase=True,
#     rule=to_me(),
#     priority=5,
#     block=False,
# )

approve_reply_matcher = on_fullmatch(
    ("y", "approve", "通过", "同意", "批准"),
    ignorecase=True,
    rule=to_me(),
    permission=SUPERUSER,
    priority=5,
    block=False,
)
reject_reply_matcher = on_fullmatch(
    ("n", "reject", "拒绝", "驳回", "反对"),
    ignorecase=True,
    rule=to_me(),
    permission=SUPERUSER,
    priority=5,
    block=False,
)
history_reply_matcher = on_fullmatch(
    ("history", "历史", "历史记录", "审批记录", "审批历史"),
    ignorecase=True,
    rule=to_me(),
    priority=5,
    block=False,
)
info_reply_matcher = on_fullmatch(("info", "详情"), ignorecase=True, rule=to_me())


def handle_event_reply_decorator(func):
    @wraps(func)
    async def wrapper(event: MessageEvent, matcher: Matcher, *args, **kwargs):
        if event.reply:
            try:
                await func(event, matcher, *args, **kwargs)
                await init_wordbank_cache()
            except PermissionDeniedException as e:
                await matcher.finish(e.message, reply_message=True)
            except NoResultFound:
                await matcher.finish()
        await matcher.finish()

    return wrapper


@driver.on_startup
async def init_wordbank_cache():
    global WORDBANK_CACHE
    WORDBANK_CACHE = await generate_wordbank_cache()


@on_type(
    (
        GroupMessageEvent,
        PrivateMessageEvent,
        PokeNotifyEvent,
        GroupIncreaseNoticeEvent,
        GroupDecreaseNoticeEvent,
    ),
    priority=5,
    block=False,
).handle()
async def response_matcher_handle(
    event: GroupMessageEvent
    | PrivateMessageEvent
    | PokeNotifyEvent
    | GroupIncreaseNoticeEvent
    | GroupDecreaseNoticeEvent,
    matcher: Matcher,
    session: AsyncSession = Depends(get_session, use_cache=False),
):
    trigger_log_service = TriggerLogService(session)
    response_log_service = ResponseLogService(session)
    trigger_text = None
    extra_info = None
    current_response_rule: dict = {}

    if isinstance(event, GroupMessageEvent):
        if event.is_tome() and not event.reply:
            extra_info = json.dumps(dict(action="AT_MENTIONED"))
            current_response_rule = {
                "group_id": event.group_id,
                "user_id": event.user_id,
            }
        else:
            trigger_text, _, _ = message_to_string(event.message)
            current_response_rule = {
                "group_id": event.group_id,
                "user_id": event.user_id,
            }
    elif isinstance(event, PrivateMessageEvent):
        trigger_text, _, _ = message_to_string(event.message)
        current_response_rule = {
            "group_id": "any",
            "user_id": event.user_id,
        }
    elif isinstance(event, PokeNotifyEvent) and event.is_tome():
        extra_info = json.dumps(dict(action="POKE_MENTIONED"))
        current_response_rule = {
            "group_id": event.group_id,
            "user_id": event.user_id,
        }
    elif isinstance(event, GroupIncreaseNoticeEvent):
        if event.is_tome():
            ...  # TODO 进群发条消息
        else:
            extra_info = json.dumps(dict(action="GROUP_JOIN"))
            current_response_rule = {
                "group_id": event.group_id,
                "user_id": event.user_id,
            }
    elif isinstance(event, GroupDecreaseNoticeEvent):
        if event.is_tome():
            await matcher.finish()
        else:
            extra_info = json.dumps(dict(action="GROUP_LEAVE"))
            current_response_rule = {
                "group_id": event.group_id,
                "user_id": event.user_id,
            }

    if (
        trigger_text
        and (trigger_cache := WORDBANK_CACHE.message_trigger_cache.get(trigger_text))
    ) or (
        extra_info
        and (trigger_cache := WORDBANK_CACHE.extra_trigger_cache.get(extra_info))
    ):
        current_trigger_status = {}
        for k, v in trigger_cache.trigger_config.items():
            match k:
                case "probability":
                    current_trigger_status["is_trigger_active"] = random.random() < v
                case "lifecycle":
                    current_trigger_status["lifecycle"] = timedelta(seconds=v)
                case _:
                    pass
        if (
            not current_trigger_status.get("is_trigger_active", False)
            or not trigger_cache.availability
        ):
            await matcher.finish()
        current_response_rule["call_count"] = (
            await trigger_log_service.get_trigger_call_count(
                trigger_cache.trigger_id,
                event.get_user_id(),
                current_trigger_status.get("lifecycle"),
            )
            + 1
        )

        response = select_random_response(
            find_first_matching_response(trigger_cache.responses, current_response_rule)
        )
        if response:
            send_message = await string_to_message(response.response_text)
            if extra_info:
                send_message += await process_extra_info(
                    event.get_user_id(), json.loads(extra_info)
                )
            message_id = str((await matcher.send(send_message))["message_id"])
            await response_log_service.log_response_call(
                response.response_id, event.get_user_id(), message_id
            )
            await trigger_log_service.log_trigger_call(
                trigger_cache.trigger_id,
                event.get_user_id(),
                str(message_id) if isinstance(event, MessageEvent) else "-1",
            )
    await matcher.finish()


@add_cmd.handle()
async def wordbank_add_cmd(
    state: T_State, session: AsyncSession = Depends(get_session, use_cache=False)
):
    state["session"] = session
    approval_log_dao = ApprovalLogDAO(session)
    approval_dao = ApprovalDAO(session)
    trigger_log_service = TriggerLogService(session)
    response_log_service = ResponseLogService(session)
    message_approval_dao = MessageApprovalDAO(session)

    state["approval_log_dao"] = approval_log_dao
    state["approval_dao"] = approval_dao
    state["trigger_log_service"] = trigger_log_service
    state["response_log_service"] = response_log_service
    state["message_approval_dao"] = message_approval_dao

    trigger_dao = TriggerDAO(session, trigger_log_service)
    response_dao = ResponseDAO(session, response_log_service)

    state["trigger_dao"] = trigger_dao
    state["response_dao"] = response_dao

    addition_log_service = AdditionLogService(session, approval_log_dao)
    approval_response_service = ApprovalResponseService(
        approval_dao, response_dao, approval_log_dao
    )
    addition_service = AdditionService(
        session, trigger_dao, response_dao, addition_log_service, approval_dao
    )

    state["addition_log_service"] = addition_log_service
    state["approval_response_service"] = approval_response_service
    state["addition_service"] = addition_service


@add_cmd.got(
    "trigger_event",
    prompt=(
        "请选择触发词的触发方式：\n"
        "1.使用特定消息触发，通常是这个模式\n"
        "2.当@凛凛时触发\n"
        "3.当凛凛被戳一戳时触发\n"
        "4.当存在用户退群时触发\n"
        "5.当有新成员加入时触发"
    ),
)
async def wordbank_add_cmd_trigger_event(
    state: T_State, trigger_event: Message = Arg()
):
    match trigger_event.extract_plain_text():
        case "1":
            state["extra_info"] = None
        case "2":
            state["trigger_text"] = None
            state["extra_info"] = json.dumps(dict(action="AT_MENTIONED"))
        case "3":
            state["trigger_text"] = None
            state["extra_info"] = json.dumps(dict(action="POKE_MENTIONED"))
        case "4":
            state["trigger_text"] = None
            state["extra_info"] = json.dumps(dict(action="GROUP_LEAVE"))
        case "5":
            state["trigger_text"] = None
            state["extra_info"] = json.dumps(dict(action="GROUP_JOIN"))
        case _:
            await add_cmd.reject("触发方式选择错误，请重新输入。")


@add_cmd.got("trigger_text", prompt="请输入触发词：")
async def wordbank_add_cmd_trigger_text(state: T_State, trigger_text: Message = Arg()):
    trigger_dao: TriggerDAO = state["trigger_dao"]
    processed_trigger_text, _, image_list = message_to_string(trigger_text)
    state["trigger_text"] = processed_trigger_text
    if trigger := await trigger_dao.get_trigger_by_word_and_extra_info(
        processed_trigger_text, state["extra_info"]
    ):
        state["trigger_config"] = trigger.trigger_config
    await asyncio.gather(*map(lambda x: upload_image_to_github(*x), image_list))


@add_cmd.got("response_text", prompt="请输入响应词：")
async def wordbank_add_cmd_response_text(
    state: T_State, event: MessageEvent, response_text: Message = Arg()
):
    processed_response_text, text_length, image_list = message_to_string(response_text)
    if (
        text_length <= wordbank_config.max_response_text
        or event.get_user_id() in memory_cache.super_users
    ):
        state["response_text"] = processed_response_text
        await asyncio.gather(*map(lambda x: upload_image_to_github(*x), image_list))
    else:
        await add_cmd.reject(
            f"响应词过长，超出了 {wordbank_config.max_response_text} 字限制，请重新输入。"
        )


@add_cmd.got(
    "is_advanced",
    prompt="高级选项中可以对响应规则（群组隔离、用户隔离、调用次数等等）和权重进行配置。是否进入高级选项？是则输入 y，否则输入 n：",
)
async def wordbank_add_cmd_is_advanced(
    state: T_State, event: MessageEvent, is_advanced: Message = Arg()
):
    if is_advanced.extract_plain_text().lower() not in ("y", "n"):
        await add_cmd.reject("输入错误，请重新输入。")
    if isinstance(event, GroupMessageEvent):
        response_rule_conditions = {
            "group_id": {"$eq": event.group_id},
        }
        add_source = {
            "group_id": event.group_id,
            "user_id": event.user_id,
        }
    else:
        response_rule_conditions = {
            "user_id": {"$eq": event.user_id},
        }
        add_source = {
            "user_id": event.user_id,
        }
    if state["trigger_text"] and len(state["trigger_text"]) <= 4:
        probability = 0.5
    else:
        probability = 1.0
    state["add_source"] = add_source
    if is_advanced.extract_plain_text().lower() == "n":
        state["trigger_config"] = {"probability": probability}
        state["response_rule_conditions"] = response_rule_conditions
        state["weight"] = 3


RESPONSE_RULE_CONDITION_PROMPT = """
响应词触发规则配置：
请选择预置响应词的触发规则，与(AND)逻辑请使用半角逗号(,)分割，或(OR)逻辑请使用半角分号(;)分隔：

普通规则：
    1.在本群有效 (群聊状态默认规则，私聊状态不可选择)
    2.对我自己有效 (私聊状态默认规则)
    3.对任意群主有效
    4.对任意管理有效
    5.对任意普通成员有效
    6.对任意会话有效


高级规则：
    a.触发词调用次数大于n
            CALL_COUNT > n
      触发词调用次数小于n
            CALL_COUNT < n
      触发词调用次数在x与y之间
            CALL_COUNT in [x,y]
    b.等级大于n
            LEVEL > n
      等级小于n
            LEVEL < n
      等级在x与y之间
            LEVEL in [x,y]
    c.用户名里有xxx
            xxx in NICKNAME
    d.群名片里有xxx
            xxx in CARD_NAME
    e.qq号里有xxx
            xxx in QQ_NUMBER

如："1,2,6;7" 意为：在本群我自己 at bot 有效，或当 bot 被戳一戳时有效。
如："凛凛 in NICKNAME" 则 bot 会检测其用户名中是否包含 "凛凛"。
""".strip()


@add_cmd.got("response_rule_conditions", prompt=RESPONSE_RULE_CONDITION_PROMPT)
async def wordbank_add_cmd_response_rule_conditions(
    state: T_State, event: MessageEvent, response_rule_conditions: Message = Arg()
):
    preset_rules = {
        "1": {"group_id": {"$eq": event.group_id}}
        if isinstance(event, GroupMessageEvent)
        else {},
        "2": {"user_id": {"$eq": event.user_id}},
        "3": {"role": {"$eq": "owner"}},
        "4": {"role": {"$eq": "admin"}},
        "5": {"role": {"$eq": "member"}},
        "6": {},
    }

    if response_rule_conditions_dict := parse_response_rule_conditions(
        preset_rules, response_rule_conditions.extract_plain_text()
    ):
        state["response_rule_conditions"] = response_rule_conditions_dict
    else:
        await add_cmd.reject("规则解析失败，请重新输入。")


TRIGGER_RULE_CONDITION_PROMPT = """
触发词触发规则配置：
请选择预置触发词的触发规则，仅能选取一个规则：

普通规则：
    1.是高频词，我需要概率触发 (触发词长度 < 4 时默认规则，默认 50%)
    2.不是高频词，我需要必然触发 (100%)

高级规则:
    a.触发概率为n，其中 n 为 0-1 的浮点数，例如 0.67
        P = n
    b.统计近 n 秒钟的触发次数，配合响应规则使用
        T = 3600

如："1" 意为：是高频词，我需要概率触发 (默认 0.5)。
如："P = 0.67" 则该触发词会以 67% 的概率触发。
如："T = 3600" 则该触发词会统计近 3600 秒钟的触发次数，配合响应规则使用。
""".strip()


@add_cmd.got("trigger_config", prompt=TRIGGER_RULE_CONDITION_PROMPT)
async def wordbank_add_cmd_trigger_config(
    state: T_State, trigger_config: Message = Arg()
):
    if parse_trigger_config(trigger_config.extract_plain_text()):
        state["trigger_config"] = parse_trigger_config(
            trigger_config.extract_plain_text()
        )
    else:
        await add_cmd.reject("规则解析失败，请重新输入。")


@add_cmd.got("weight", prompt="请输入响应词的权重，权重为 1-5 之间的数字 (默认 3)：")
async def wordbank_add_cd_weight(state: T_State, weight: Message = Arg()):
    if (weight_text := weight.extract_plain_text()).isdigit() and 1 <= (
        input_weight := int(weight_text)
    ) <= 5:
        state["weight"] = input_weight
    else:
        await add_cmd.reject("权重不合法，请输入 1-5 之间的数字。")


@add_cmd.handle()
async def wordbank_add_cmd_insert_to_db(
    state: T_State, bot: Bot, event: MessageEvent, matcher: Matcher
):
    session: AsyncSession = state["session"]
    trigger_text = state["trigger_text"]
    response_text = state["response_text"]
    trigger_config = state["trigger_config"]
    response_rule_conditions = state["response_rule_conditions"]
    weight = state["weight"]
    add_source = state["add_source"]
    extra_info = state["extra_info"]
    addition_service: AdditionService = state["addition_service"]
    message_approval_dao: MessageApprovalDAO = state["message_approval_dao"]
    if "user_id" in response_rule_conditions:
        priority = 1
    elif "group_id" in response_rule_conditions:
        priority = 2
    else:
        priority = 3
    try:
        approval, response = await addition_service.add_trigger_and_response(
            trigger_text=trigger_text,
            trigger_config=trigger_config,
            response_text=response_text,
            response_rule_conditions=response_rule_conditions,
            extra_info=extra_info,
            weight=weight,
            priority=priority,
            user_id=event.get_user_id(),
            add_source=add_source,
            created_message_id=str(event.message_id),
        )
        await session.commit()
    except DuplicateTriggerResponseException as e:
        await matcher.finish(e.message)
    except PermissionDeniedException:
        await matcher.finish("您没有权限添加该触发词。")
    await init_wordbank_cache()
    report_message = (
        MessageSegment.text("🆕 新增词条提醒\n\n")
        + Message.template("🔑 触发词: {}\n").format(
            await string_to_message(trigger_text) if trigger_text else "无"
        )
        + Message.template("💬 响应词: {}\n").format(
            await string_to_message(response_text) if response_text else "无"
        )
        + MessageSegment.text(f"📄 响应规则: {response.response_rule_conditions}\n")
        + MessageSegment.text(f"⚖️ 权重: {weight}\n")
        + MessageSegment.text(f"🔍 扩展信息: {extra_info}\n")
        + MessageSegment.text(f"👤 用户 ID: {event.get_user_id()}\n")
        + MessageSegment.text(
            f"👥 群聊 ID: {event.group_id if isinstance(event, GroupMessageEvent) else '无'}\n\n"
        )
        + MessageSegment.text("✅ 发送 y 以同意，❌ 发送 n 以拒绝。\n")
        + MessageSegment.text("ℹ️ 您也可以通过发送 #help wordbank 查看完整审批操作")
    )
    for super_user_id in memory_cache.super_users:
        message_id = str(
            (
                await bot.send_private_msg(
                    user_id=int(super_user_id),
                    message=AlertTemplate.build_tip_notification(
                        matcher.plugin_name, report_message
                    ),
                )
            )["message_id"]
        )
        await message_approval_dao.create_message_approval_by_approval_and_message_id(
            approval, message_id
        )
    finish_message = (
        MessageSegment.text("🆕 已添加新词条\n\n")
        + Message.template("🔑 触发词: {}\n").format(
            await string_to_message(trigger_text) if trigger_text else "无"
        )
        + MessageSegment.text(f"⚙️ 触发规则: {trigger_config}\n")
        + Message.template("💬 响应词: {}\n").format(
            await string_to_message(response_text) if response_text else "无"
        )
        + MessageSegment.text(f"📄 响应规则: {response_rule_conditions}\n")
        + MessageSegment.text(f"⚖️ 权重: {weight}\n")
        + MessageSegment.text(f"🔍 扩展信息: {extra_info}\n\n")
        + MessageSegment.text("✨ 词条将在管理员审核通过后启用，请耐心等待。")
    )
    message_id = str((await add_cmd.send(finish_message))["message_id"])
    await message_approval_dao.create_message_approval_by_approval_and_message_id(
        approval, message_id
    )
    await session.commit()
    await add_cmd.finish()


@delete_trigger_reply_matcher.handle()
@handle_event_reply_decorator
async def delete_trigger_reply_matcher_handle(
    event: MessageEvent,
    matcher: Matcher,
    session: AsyncSession = Depends(get_session, use_cache=False),
):
    if event.reply:
        trigger_log_service = TriggerLogService(session)
        response_log_service = ResponseLogService(session)
        deletion_log_service = DeletionLogService(session)
        trigger_dao = TriggerDAO(session, trigger_log_service)
        response_dao = ResponseDAO(session, response_log_service)
        approval_dao = ApprovalDAO(session)
        approval_log_dao = ApprovalLogDAO(session)
        deletion_service = DeletionService(
            session,
            trigger_dao,
            response_dao,
            deletion_log_service,
            approval_dao,
            approval_log_dao,
        )
        if not (
            trigger := await trigger_dao.get_trigger_by_message_id(
                str(event.reply.message_id)
            )
        ):
            await matcher.finish()
        await deletion_service.delete_trigger(
            trigger.trigger_id, event.get_user_id(), "回复了删除触发词的指令"
        )
        await matcher.send(
            NoticeBuilder.success(f"已删除触发词 {trigger.trigger_id}"),
            reply_message=True,
        )
        await session.commit()


@delete_response_reply_matcher.handle()
async def delete_response_reply_matcher_handle(
    state: T_State,
    event: MessageEvent,
    matcher: Matcher,
    session: AsyncSession = Depends(get_session, use_cache=False),
):
    if event.reply:
        trigger_log_service = TriggerLogService(session)
        response_log_service = ResponseLogService(session)
        deletion_log_service = DeletionLogService(session)
        trigger_dao = TriggerDAO(session, trigger_log_service)
        response_dao = ResponseDAO(session, response_log_service)
        approval_dao = ApprovalDAO(session)
        approval_log_dao = ApprovalLogDAO(session)
        deletion_service = DeletionService(
            session,
            trigger_dao,
            response_dao,
            deletion_log_service,
            approval_dao,
            approval_log_dao,
        )

        state["deletion_service"] = deletion_service

        if not (
            (
                trigger := await trigger_dao.get_trigger_by_message_id(
                    str(event.reply.message_id)
                )
            )
            and (
                response_log
                := await response_log_service.get_response_log_by_message_id(
                    str(event.reply.message_id)
                )
            )
            and (
                response := await response_dao.get_response_by_id(
                    response_log.response_id
                )
            )
        ):
            await matcher.finish()

        state["trigger"] = trigger
        state["response"] = response
        if (
            event.get_user_id() in memory_cache.super_users
            or event.get_user_id() == response.created_by
        ):
            await deletion_service.delete_response(
                trigger.trigger_id,
                response.response_id,
                event.get_user_id(),
                "回复了删除响应词的指令",
            )
            await session.commit()
            await init_wordbank_cache()
            await matcher.finish(
                NoticeBuilder.success(f"已删除响应词 {response.response_id}"),
                reply_message=True,
            )

        elif vote := await WordbankVoteDAO(
            session
        ).get_vote_by_trigger_id_and_response_id(
            trigger.trigger_id, response.response_id
        ):
            await matcher.finish(
                NoticeBuilder.warning(
                    f"没有权限直接删除当前的响应词，您可以通过投票的方式进行禁用，或加入反馈群「{general_config.support_group_id}」，联系群管删除。\n"
                    f"当前已有投票，投票状态：{vote.vote_status}"
                    f"您可以使用如下命令参与投票：\n"
                    f"#支持删除 {vote.id} \n"
                    f"#查看投票结果 {vote.id}"
                )
            )
            await session.commit()

    else:
        await matcher.finish()


@delete_response_reply_matcher.got(
    "is_vote_active",
    prompt=(
        f"没有权限直接删除当前的响应词，您可以通过投票的方式进行禁用，或加入反馈群「{general_config.support_group_id}」，联系群管删除。\n"
        "是否发起投票？是则输入 y，否则输入 n："
    ),
)
async def delete_response_reply_matcher_vote(
    state: T_State,
    event: MessageEvent,
    matcher: Matcher,
    session: AsyncSession = Depends(get_session, use_cache=False),
    is_vote_active: Message = Arg(),
):
    if is_vote_active.extract_plain_text().lower() not in ("y", "n"):
        await delete_trigger_reply_matcher.reject("输入错误，请重新输入。")
    if is_vote_active.extract_plain_text().lower() == "y":
        vote_dao = WordbankVoteDAO(session)
        vote_log_dao = WordbankVoteLogDAO(session)

        trigger: Trigger = state["trigger"]
        response: Response = state["response"]

        vote = await vote_dao.create_vote(
            message_id=str(event.message_id),
            trigger_id=trigger.trigger_id,
            response_id=response.response_id,
            initiator=event.get_user_id(),
        )
        await vote_log_dao.create_vote_log(
            message_id=str(event.message_id),
            vote_id=vote.id,
            operator=event.get_user_id(),
            option=VoteOptionEnum.SUPPORT,
        )
        await matcher.finish(
            NoticeBuilder.success(
                f"成功发起投票，当支持票数 ≥ {wordbank_config.support_vote_threshold} 时可禁用该词。您可以使用如下命令参与投票：\n"
                f"#支持删除 {vote.id} \n"
                f"#查看投票状态 {vote.id}"
            ),
            reply_message=True,
        )
    else:
        await matcher.finish(NoticeBuilder.success("本次操作已结束。"))


@vote_status_cmd.handle()
async def vote_status_cmd_handle(
    matcher: Matcher,
    session: AsyncSession = Depends(get_session, use_cache=False),
    vote_id: Message = CommandArg(),
):
    wordbank_vote_dao = WordbankVoteDAO(session)
    wordbank_vote_log_dao = WordbankVoteLogDAO(session)
    if (vote_id.extract_plain_text().isdigit()) and (
        vote := await wordbank_vote_dao.get_vote_by_id(
            int(vote_id.extract_plain_text())
        )
    ):
        vote_log = (
            await wordbank_vote_log_dao.get_support_vote_by_vote_id(vote.id) or []
        )
        await matcher.finish(
            NoticeBuilder.info(
                f"投票 id 为 {vote.id} 的投票状态为：{vote.vote_status}，支持票数为 {len(vote_log)}"
            )
        )
    else:
        await matcher.finish(NoticeBuilder.exception("投票ID错误，请重新输入。"))


@vote_support_cmd.handle()
async def vote_support_cmd_handle(
    bot: Bot,
    event: MessageEvent,
    matcher: Matcher,
    session: AsyncSession = Depends(get_session, use_cache=False),
    vote_id: Message = CommandArg(),
):
    wordbank_vote_dao = WordbankVoteDAO(session)
    wordbank_vote_log_dao = WordbankVoteLogDAO(session)
    if not (
        (vote_id.extract_plain_text().isdigit())
        and (
            vote := await wordbank_vote_dao.get_vote_by_id(
                int(vote_id.extract_plain_text())
            )
        )
    ):
        await matcher.finish(NoticeBuilder.exception("投票ID错误，请重新输入。"))

    if vote_log := await wordbank_vote_log_dao.get_vote_log_by_vote_id_and_operator(
        vote.id, event.get_user_id()
    ):
        await matcher.finish(
            NoticeBuilder.warning(
                f"您已经参与过投票，请勿重复参与。您的表决态度为：{vote_log.option}"
            )
        )
    await wordbank_vote_log_dao.create_vote_log(
        message_id=str(event.message_id),
        vote_id=vote.id,
        operator=event.get_user_id(),
        option=VoteOptionEnum.SUPPORT,
    )
    support_vote_logs = (
        await wordbank_vote_log_dao.get_support_vote_by_vote_id(vote.id) or []
    )
    if not len(support_vote_logs) >= wordbank_config.support_vote_threshold:
        await matcher.finish(
            MessageSegment.reply(int(vote.message_id))
            + NoticeBuilder.success(
                f"您已成功支持删除词条 {vote.response_id}，投票数量已增加，当前支持票数 {len(support_vote_logs)}"
            )
        )
    await wordbank_vote_dao.update_vote_status(vote.id, VoteStatusEnum.SUPPORT)
    trigger_log_service = TriggerLogService(session)
    response_log_service = ResponseLogService(session)
    deletion_log_service = DeletionLogService(session)
    trigger_dao = TriggerDAO(session, trigger_log_service)
    response_dao = ResponseDAO(session, response_log_service)
    approval_dao = ApprovalDAO(session)
    approval_log_dao = ApprovalLogDAO(session)
    deletion_service = DeletionService(
        session,
        trigger_dao,
        response_dao,
        deletion_log_service,
        approval_dao,
        approval_log_dao,
    )
    trigger = await trigger_dao.get_trigger_by_id(vote.trigger_id)
    response = await response_dao.get_response_by_id(vote.response_id)
    if not trigger or not response:
        await matcher.finish()

    await deletion_service.delete_response(
        vote.trigger_id, vote.response_id, event.get_user_id(), "投票删除"
    )
    await session.commit()
    await init_wordbank_cache()
    message = (
        MessageSegment.text("🗑 删除词条提醒\n\n")
        + Message.template("🔑 触发词: {}\n").format(
            await string_to_message(trigger.trigger_text)
            if trigger.trigger_text
            else "无"
        )
        + Message.template("💬 响应词: {}\n").format(
            await string_to_message(response.response_text)
            if response.response_text
            else "无"
        )
        + MessageSegment.text(f"📄 响应规则: {response.response_rule_conditions}\n")
        + MessageSegment.text(f"⚖️ 权重: {response.weight}\n")
        + MessageSegment.text(f"🔍 扩展信息: {trigger.extra_info}\n")
        + MessageSegment.text(f"👤 用户 ID: {event.get_user_id()}\n")
        + MessageSegment.text(
            f"👥 群聊 ID: {event.group_id if isinstance(event, GroupMessageEvent) else '无'}\n\n"
        )
        # + MessageSegment.text("✅ 可以回复 restore 以恢复删除。") #TODO:相关功能支持
    )
    for super_user in memory_cache.super_users:
        message_id = (  # noqa: F841 #TODO: 后续添加撤销删除的功能
            await bot.send_private_msg(
                user_id=int(super_user),
                message=AlertTemplate.build_tip_notification(
                    matcher.plugin_name, message
                ),
            )
        )["message_id"]

    await matcher.finish(
        MessageSegment.reply(int(vote.message_id))
        + NoticeBuilder.success(
            f"您已成功支持删除词条 {vote.response_id}，投票数量已满足条件，该词条已被禁用。"
        )
    )


@resotre_trigger_reply_matcher.handle()
@handle_event_reply_decorator
async def restore_trigger_reply_matcher_handle(
    event: MessageEvent,
    matcher: Matcher,
    session: AsyncSession = Depends(get_session, use_cache=False),
):
    if event.reply:
        trigger_log_service = TriggerLogService(session)
        response_log_service = ResponseLogService(session)
        restoration_log_service = RestorationLogService(session)
        trigger_dao = TriggerDAO(session, trigger_log_service)
        response_dao = ResponseDAO(session, response_log_service)
        restoration_service = RestorationService(
            session, trigger_dao, response_dao, restoration_log_service
        )
        if not (
            trigger := await trigger_dao.get_trigger_by_message_id(
                str(event.reply.message_id)
            )
        ):
            await matcher.finish()
        await restoration_service.restore_trigger(
            trigger.trigger_id, event.get_user_id(), "回复了恢复触发词的指令"
        )
        await matcher.send(
            NoticeBuilder.success(f"已恢复触发词 {trigger.trigger_id}"),
            reply_message=True,
        )
        await session.commit()


@restore_response_reply_matcher.handle()
@handle_event_reply_decorator
async def resotre_response_reply_matcher_handle(
    event: MessageEvent,
    matcher: Matcher,
    session: AsyncSession = Depends(get_session, use_cache=False),
):
    if event.reply:
        trigger_log_service = TriggerLogService(session)
        response_log_service = ResponseLogService(session)
        restoration_log_service = RestorationLogService(session)
        trigger_dao = TriggerDAO(session, trigger_log_service)
        response_dao = ResponseDAO(session, response_log_service)
        restoration_service = RestorationService(
            session, trigger_dao, response_dao, restoration_log_service
        )
        if not (
            (
                trigger := await trigger_dao.get_trigger_by_message_id(
                    str(event.reply.message_id)
                )
            )
            and (
                response_log
                := await response_log_service.get_response_log_by_message_id(
                    str(event.reply.message_id)
                )
            )
        ):
            await matcher.finish()

        await restoration_service.restore_response(
            trigger.trigger_id,
            response_log.response_id,
            event.get_user_id(),
            "回复了恢复响应词的指令",
        )
        await matcher.send(
            NoticeBuilder.success(f"已恢复响应词 {response_log.response_id}"),
            reply_message=True,
        )
        await session.commit()


@info_reply_matcher.handle()
async def info_reply_matcher_handle(
    event: MessageEvent,
    matcher: Matcher,
    session: AsyncSession = Depends(get_session, use_cache=False),
):
    if event.reply:
        response_log_service = ResponseLogService(session)
        response_dao = ResponseDAO(session, response_log_service)
        response_id = (
            await response_log_service.get_response_log_by_message_id(
                str(event.reply.message_id)
            )
        ).response_id
        info_message = await response_dao.get_entry_property_by_response_id(response_id)
        await matcher.finish(info_message, reply_message=True)


@history_reply_matcher.handle()
async def history_reply_matcher_handle(
    event: MessageEvent,
    matcher: Matcher,
    session: AsyncSession = Depends(get_session, use_cache=False),
):
    if event.reply:
        approval_dao = ApprovalDAO(session)
        approval_log_dao = ApprovalLogDAO(session)
        response_log_service = ResponseLogService(session)
        response_dao = ResponseDAO(session, response_log_service)
        approval_response_service = ApprovalResponseService(
            approval_dao, response_dao, approval_log_dao
        )

        response_id = (
            await response_log_service.get_response_log_by_message_id(
                str(event.reply.message_id)
            )
        ).response_id
        approval_logs = (
            await approval_log_dao.get_succeed_approved_approval_logs_by_response_id(
                response_id
            )
        )
        history_beauty_message = (
            await approval_response_service.get_approval_history_beauty_message(
                approval_logs
            )
        )

        await matcher.finish(history_beauty_message, reply_message=True)


@reject_reply_matcher.handle()
@approve_reply_matcher.handle()
async def approval_reply_matcher_handle(
    state: T_State,
    event: MessageEvent,
    matcher: Matcher,
    session: AsyncSession = Depends(get_session, use_cache=False),
):
    if event.reply:
        state["session"] = session
        approval_dao = ApprovalDAO(session)
        approval_log_dao = ApprovalLogDAO(session)
        response_log_service = ResponseLogService(session)
        message_approval_dao = MessageApprovalDAO(session)
        response_dao = ResponseDAO(session, response_log_service)
        approval_response_service = ApprovalResponseService(
            approval_dao, response_dao, approval_log_dao
        )
        addition_log_service = AdditionLogService(session, approval_log_dao)
        state["response_dao"] = response_dao
        state["addition_log_service"] = addition_log_service
        if not (
            message_approval
            := await message_approval_dao.get_message_approval_by_message_id(
                str(event.reply.message_id)
            )
        ):
            await matcher.finish()
        approval = await approval_dao.get_approval_by_id(message_approval.approval_id)
        response_id = approval.response_id
        if not response_id:
            await matcher.finish()
        approval_logs = (
            await approval_log_dao.get_succeed_approved_approval_logs_by_response_id(
                response_id
            )
        )
        if event.get_message().extract_plain_text() in (
            "y",
            "approve",
            "通过",
            "同意",
            "批准",
        ):
            state["approval_action"] = ApprovalStatusEnum.APPROVED
        else:
            state["approval_action"] = ApprovalStatusEnum.REJECTED
        state["response_id"] = response_id
        state["approval_response_service"] = approval_response_service
        if approval_logs:
            history_beauty_message = (
                await approval_response_service.get_approval_history_beauty_message(
                    approval_logs
                )
            )
            await matcher.send(
                NoticeBuilder.warning("检测到当前响应词已经被审批过：\n")
                + history_beauty_message
            )
        else:
            state["is_continue"] = True
    else:
        await matcher.finish()


@reject_reply_matcher.got(
    "is_continue", prompt="是否继续审批？是则输入 y，否则输入 n："
)
@approve_reply_matcher.got(
    "is_continue", prompt="是否继续审批？是则输入 y，否则输入 n："
)
async def approval_reply_matcher_got(is_continue: Message = Arg()):
    if is_continue.extract_plain_text().lower() == "y":
        pass
    else:
        await approve_reply_matcher.finish(
            NoticeBuilder.approval("审批已取消，若需要重新审批请重新发送消息。"),
            reply_message=True,
        )


@reject_reply_matcher.handle()
@approve_reply_matcher.handle()
async def approval_reply_matcher_handle_approval(
    state: T_State,
    bot: Bot,
    event: MessageEvent,
    matcher: Matcher,
):
    session: AsyncSession = state["session"]
    approval_response_sevice: ApprovalResponseService = state[
        "approval_response_service"
    ]
    response_id = state["response_id"]
    response_dao: ResponseDAO = state["response_dao"]
    approval_action = state["approval_action"]
    addition_log_service: AdditionLogService = state["addition_log_service"]
    await approval_response_sevice.approval_response(
        response_id=state["response_id"],
        user_id=event.get_user_id(),
        approval_action=approval_action,
    )
    info_message = await response_dao.get_entry_property_by_response_id(response_id)
    await session.commit()
    await init_wordbank_cache()
    approval_finish_message = (
        NoticeBuilder.approval(
            f"审批已完成。\n管理员 {event.user_id} {approval_action} 该审批。\n\n"
        )
        + info_message
    )
    await matcher.send(approval_finish_message)
    if wordbank_config.send_approval_message_to_admin:
        for super_user_id in memory_cache.super_users:
            if super_user_id == event.get_user_id():
                continue
            await bot.send_private_msg(
                user_id=int(super_user_id),
                message=approval_finish_message,
            )
    if additional_log := await addition_log_service.get_approval_log_by_response_id(
        response_id
    ):
        if source_group_id := additional_log.add_source.get("group_id"):
            await bot.send_group_msg(
                group_id=source_group_id,
                message=MessageSegment.reply(int(additional_log.created_message_id))
                + MessageSegment.text(approval_finish_message),
            )
        else:
            await bot.send_private_msg(
                user_id=additional_log.add_source["user_id"],
                message=MessageSegment.reply(int(additional_log.created_message_id))
                + MessageSegment.text(approval_finish_message),
            )
    await matcher.finish()


@search_or_delete_cmd.got(
    "search_range",
    prompt=(
        "请输入搜索范围：\n"
        "1.触发词\n"
        "2.响应词\n"
        "3.创建者\n"
        "可以输入多个内容，用空格分隔，例如：'1 2 3'"
    ),
)
async def search_cmd_mode(state: T_State, search_range: Message = Arg()):
    search_mode = ["trigger", "response", "author"]
    for mode in search_range.extract_plain_text().split() or [""]:
        match mode:
            case "1" if "trigger" in search_mode:
                search_mode.remove("trigger")
            case "2" if "response" in search_mode:
                search_mode.remove("response")
            case "3" if "author" in search_mode:
                search_mode.remove("author")
            case _:
                await search_or_delete_cmd.reject("无效的搜索范围，请重新输入。")
    state["search_mode"] = search_mode
    for mode in search_mode:
        state[mode] = None


@search_or_delete_cmd.got("trigger", prompt="请输入需要搜索的触发词：")
async def search_cmd_trigger(state: T_State, trigger: Message = Arg()):
    state["trigger"] = message_to_string(trigger)[0]


@search_or_delete_cmd.got("response", prompt="请输入需要搜索的响应词：")
async def search_cmd_response(state: T_State, response: Message = Arg()):
    state["response"] = message_to_string(response)[0]


@search_or_delete_cmd.got("author", prompt="请输入需要搜索的创建者：")
async def search_cmd_author(state: T_State, author: Message = Arg()):
    state["author"] = author.extract_plain_text()


@search_or_delete_cmd.handle()
async def search_cmd_handle_succeed(
    state: T_State, session: AsyncSession = Depends(get_session, use_cache=False)
):
    if wordbank_fts_list := CommonHelper.split_list(
        input_list=list(
            await WordbankFTSDAO(session).general_search(
                SearchArgs(
                    trigger=state.get("trigger"),
                    response=state.get("response"),
                    author=state.get("author"),
                )
            )
        ),
        size=10,
    ):
        state["wordbank_fts_list"] = wordbank_fts_list
        if len(wordbank_fts_list) > 1:
            await search_or_delete_cmd.send(
                NoticeBuilder.info(
                    f"共有 {len(wordbank_fts_list)} 页词条，请选择页数："
                )
            )
        else:
            state["extra_command"] = Message("page 1")
    else:
        await search_or_delete_cmd.finish(NoticeBuilder.info("没有找到相关的词条。"))


@search_or_delete_cmd.got("extra_command")
async def search_cmd_page_number(
    bot: Bot,
    state: T_State,
    event: MessageEvent,
    extra_command: Message = Arg(),
    session: AsyncSession = Depends(get_session, use_cache=False),
):
    if extra_command.extract_plain_text().lower() == "exit":
        await search_or_delete_cmd.finish("已结束操作。")

    arg_text = extra_command.extract_plain_text()

    if (
        arg_text.startswith("del")
        and (del_indexs := arg_text.removeprefix("del").strip().split())
        and (all(map(lambda x: x.isdigit, del_indexs)))
        and (wordbank_fts_page := state.get("wordbank_fts_page", []))
        and all(
            map(
                lambda x: int(x) - 1 in range(len(wordbank_fts_page)),
                del_indexs,
            )
        )
    ):
        if not await SUPERUSER(bot, event):
            await search_or_delete_cmd.finish(
                NoticeBuilder.warning(
                    "没有权限直接删除当前的响应词，批量删除功能仅凛凛管理员可用！"
                )
            )
        trigger_log_service = TriggerLogService(session)
        response_log_service = ResponseLogService(session)
        deletion_log_service = DeletionLogService(session)
        trigger_dao = TriggerDAO(session, trigger_log_service)
        response_dao = ResponseDAO(session, response_log_service)
        approval_dao = ApprovalDAO(session)
        approval_log_dao = ApprovalLogDAO(session)
        deletion_service = DeletionService(
            session,
            trigger_dao,
            response_dao,
            deletion_log_service,
            approval_dao,
            approval_log_dao,
        )

        wordbank_fts_page: list[WordbankFTS]
        for index in del_indexs:
            trigger_id = wordbank_fts_page[int(index) - 1].trigger_id
            response_id = wordbank_fts_page[int(index) - 1].response_id
            await deletion_service.delete_response(
                trigger_id, response_id, event.get_user_id(), "用户主动搜索删除"
            )
        await session.commit()
        await init_wordbank_cache()
        await search_or_delete_cmd.send(
            NoticeBuilder.success(
                f"已完成操作，删除了编号为 {'、'.join(del_indexs)} 的词条。"
            )
        )
        await search_or_delete_cmd.reject(
            (
                "如需删除相关的词条，请输入「del 词条序号（允许多个，使用空格分割）」\n"
                "如需继续搜索其他页，请输入「page 页数」\n"
                "如需结束操作，请输入「exit」。"
            )
        )
    if (
        (page_number_text := arg_text.removeprefix("page").strip()).isdigit()
    ) and 0 < int(page_number_text) <= len(state["wordbank_fts_list"]):
        await search_or_delete_cmd.send(NoticeBuilder.info("正在生成图片，请稍后..."))
        if general_config.use_playwright:
            await search_or_delete_cmd.send(
                await generate_wordbank_fts_image_by_playwright(
                    state["wordbank_fts_list"], int(page_number_text)
                )
            )
        else:
            await search_or_delete_cmd.send(
                await generate_wordbank_fts_image_by_pillow(
                    state["wordbank_fts_list"], int(page_number_text)
                )
            )
        state["wordbank_fts_page"] = state["wordbank_fts_list"][
            int(page_number_text) - 1
        ]
        await search_or_delete_cmd.reject(
            (
                "如需删除相关的词条，请输入「del 词条序号（允许多个，使用空格分割）」\n"
                "是否继续搜索其他页？如需要请发送「page 页数」\n"
                "如需结束操作，请输入「exit」。"
            )
        )
    else:
        await search_or_delete_cmd.reject(NoticeBuilder.exception("请输入正确的参数。"))
