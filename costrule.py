"""
    眼不见心不烦系列
    md装在vscode老是报错，而且几个rule会反复调用
    嗯！装起来吧
"""

from nonebot.rule import Rule
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.adapters.cqhttp.event import GroupMessageEvent, PrivateMessageEvent
from nonebot.typing import T_State
from .config import masterList


def check_white_list_all() -> Rule:
    """
    :说明:

        私聊消息全都上，群聊消息则判断是否为指定群聊

    :参数:

        无
    """
    async def _check(bot: Bot, event: Event, state: T_State) -> bool:
        if isinstance(event, GroupMessageEvent):
            if event.group_id in bot.config.GroupList.values():
                return True
            else:
                return False
        elif isinstance(event, PrivateMessageEvent):
            if event.message_type == 'private':
                return True
            else:
                return False
        else:
            return False
    return Rule(_check)


def check_white_list_group() -> Rule:
    """
    :说明:

        群聊消息判断是否为指定群聊

    :参数:

        无
    """
    async def _check(bot: Bot, event: Event, state: T_State) -> bool:
        if isinstance(event, GroupMessageEvent):
            if event.group_id in bot.config.GroupList.values():
                return True
            else:
                return False
        else:
            return False
    return Rule(_check)


def check_white_list_friend() -> Rule:
    """
    :说明:

        私聊消息上

    :参数:

        无
    """
    async def _check(bot: Bot, event: Event, state: T_State) -> bool:
        if isinstance(event, PrivateMessageEvent):
            if event.message_type == 'private':
                return True
            else:
                return False
        else:
            return False
    return Rule(_check)


def only_master() -> Rule:
    """
    :说明:

        判定管理用户

    :参数:

      * 无
    """
    async def _only_master(bot: Bot, event: Event, state: T_State) -> bool:
        if event.get_user_id() in masterList:
            return True
        else:
            return False
    return Rule(_only_master)
