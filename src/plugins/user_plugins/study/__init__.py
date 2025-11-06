import asyncio

from nonebot import require
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, MessageEvent
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import Arg, CommandArg, Depends
from nonebot.plugin import PluginMetadata, on_command
from nonebot.typing import T_State
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache.memory_cache import memory_cache
from src.config.general_config import general_config
from src.utils.enums import PluginPermissionEnum, TriggerTypeEnum
from src.utils.message_builder import NoticeBuilder

require("src.plugins.user_plugins.wordbank")

from src.plugins.user_plugins.wordbank import wordbank_add_cmd_insert_to_db  # noqa:E402
from src.plugins.user_plugins.wordbank.config import wordbank_config  # noqa:E402
from src.plugins.user_plugins.wordbank.wordbank_dao import (  # noqa:E402
    AdditionLogService,
    AdditionService,
    ApprovalDAO,
    ApprovalLogDAO,
    MessageApprovalDAO,
    ResponseDAO,
    ResponseLogService,
    TriggerDAO,
    TriggerLogService,
)
from src.plugins.user_plugins.wordbank.wordbank_database import get_session  # noqa:E402
from src.plugins.user_plugins.wordbank.wordbank_process import (  # noqa:E402
    message_to_string,
    upload_image_to_github,
)

name = "学习词库（传统版）"
description = """
学习词库（传统版）：
  添加词条
  删除词条
  搜索词条
""".strip()

usage = f"""
📖 ===== {name} =====

命令前缀: #study

1.添加词条 📝
  添加一条新的词条，可以仅输入 "#study" 进入引导模式
  也可以输入以下命令进行一键添加，对于不全的参数凛凛会通过引导模式进行补全：
  #study <a/m> <t/f> <触发词> <响应词>
  <a/m> 表示触发词的触发方式，可选值为：
    a. 对所有人有效
    m. 仅对自己有效，同词条情况下优先级更高
  <t/f> 表示群组隔离的开关，可选值为：
    t. 开启群组隔离，仅在当前群聊有效 
    f. 关闭群组隔离，所有群聊有效

⚠️ 注意事项:
1. 如果使用一键添加的命令，请确保触发词和响应词中【没有空格】
2. 如果需要更多的自定义选项，请发送「#help wordbank」参考 wordbank 插件的文档。
3. 如需进一步支持，请联系管理员，或加入反馈群「{general_config.support_group_id}」💬。

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

study_command = on_command("study", priority=5, block=False)


@study_command.handle()
async def study_command_add_init(state: T_State, arg: Message = CommandArg()):
    state_keys_and_checker = {
        "trig_mode": (
            lambda x: True if x[0].data.get("text", "").lower() in ("a", "m") else False
        ),
        "group_block": (
            lambda x: True if x[0].data.get("text", "").lower() in ("t", "f") else False
        ),
        "trigger_text": (lambda x: True),
        "response_text": (
            lambda x: True
            if message_to_string(x)[1] <= wordbank_config.max_response_text
            else False
        ),
    }
    command_args = Message()
    for message in arg:
        if message.type == "text":
            command_args.extend(
                [
                    MessageSegment.text(i)
                    for i in message.data["text"].strip().split(" ")
                ]
            )
        else:
            command_args.append(message)
    for i, text_arg in enumerate(command_args[:4]):
        message_text_arg = Message(text_arg)
        state_key = list(state_keys_and_checker.keys())[i]
        state[state_key] = message_text_arg


@study_command.got(
    "trig_mode",
    prompt=(
        "请选择触发词的触发方式：\n"
        "a. 对所有人有效\n"
        "m. 仅对自己有效，同词条情况下优先级更高"
    ),
)
async def study_command_add_trig_mode(state: T_State, trig_mode: Message = Arg()):
    if (trig_mode_text := trig_mode.extract_plain_text().lower()) in ["a", "m"]:
        state["trig_mode"] = trig_mode_text
    else:
        await study_command.reject(
            NoticeBuilder.warning("触发方式输入错误，请重新输入。")
        )


@study_command.got(
    "group_block",
    prompt=(
        "是否开启群组隔离？\n"
        "t. 开启群组隔离，仅在当前群聊有效\n"
        "f. 关闭群组隔离，所有群聊有效"
    ),
)
async def study_command_add_group_block(state: T_State, group_block: Message = Arg()):
    if (group_block_text := group_block.extract_plain_text().lower()) in ("t", "f"):
        state["group_block"] = group_block_text
    else:
        await study_command.reject(
            NoticeBuilder.warning("群组隔离开关输入错误，请重新输入。")
        )


@study_command.got("trigger_text", prompt="请输入触发词")
async def study_command_add_trigger_text(state: T_State, trigger_text: Message = Arg()):
    processed_trigger_text, _, image_list = message_to_string(trigger_text)
    state["trigger_text"] = processed_trigger_text
    await asyncio.gather(*map(lambda x: upload_image_to_github(*x), image_list))


@study_command.got("response_text", prompt="请输入响应词")
async def study_command_add_response_text(
    state: T_State, event: MessageEvent, response_text: Message = Arg()
):
    processed_response_text, response_length, image_list = message_to_string(
        response_text
    )
    if (
        response_length > wordbank_config.max_response_text
        and event.get_user_id() not in memory_cache.super_users
    ):
        await study_command.reject(
            f"响应词过长，超出了 {wordbank_config.max_response_text} 字限制，请重新输入。"
        )

    state["response_text"] = processed_response_text
    await asyncio.gather(*map(lambda x: upload_image_to_github(*x), image_list))


@study_command.got(
    "weight", prompt="请输入响应词的权重，权重为 1-5 之间的数字 (默认 3)："
)
async def wordbank_add_cd_weight(state: T_State, weight: Message = Arg()):
    if (weight_text := weight.extract_plain_text()).isdigit() and 1 <= (
        input_weight := int(weight_text)
    ) <= 5:
        state["weight"] = input_weight
    else:
        await study_command.reject("权重不合法，请输入 1-5 之间的数字。")


@study_command.handle()
async def study_command_add_handle(
    state: T_State,
    bot: Bot,
    event: MessageEvent,
    matcher: Matcher,
    session: AsyncSession = Depends(get_session),
):
    trig_mode = state["trig_mode"]
    group_block = state["group_block"]
    response_rule_conditions = {}

    match (trig_mode, group_block):
        case ("a", "f"):
            response_rule_conditions = {}
        case ("a", "t"):
            response_rule_conditions = (
                {"group_id": {"$eq": event.group_id}}
                if isinstance(event, GroupMessageEvent)
                else {}
            )
        case ("m", "f"):
            response_rule_conditions = {"user_id": {"$eq": event.user_id}}
        case ("m", "t"):
            response_rule_conditions = (
                {"group_id": {"$eq": event.group_id}, "user_id": {"$eq": event.user_id}}
                if isinstance(event, GroupMessageEvent)
                else {"user_id": {"$eq": event.user_id}}
            )
    addition_service = AdditionService(
        session,
        TriggerDAO(session, TriggerLogService(session)),
        ResponseDAO(session, ResponseLogService(session)),
        AdditionLogService(session, ApprovalLogDAO(session)),
        ApprovalDAO(session),
    )
    message_approval_dao = MessageApprovalDAO(session)

    state["session"] = session
    state["trigger_config"] = {"probability": 1.0}
    state["response_rule_conditions"] = response_rule_conditions
    state["add_source"] = (
        {
            "group_id": event.group_id,
            "user_id": event.user_id,
        }
        if isinstance(event, GroupMessageEvent)
        else {
            "user_id": event.user_id,
        }
    )
    state["extra_info"] = None
    state["addition_service"] = addition_service
    state["message_approval_dao"] = message_approval_dao

    await wordbank_add_cmd_insert_to_db(state, bot, event, matcher)
