"""
    眼不见心不烦系列
    md装在vscode老是报错，而且几个rule会反复调用
    嗯！装起来吧
"""

import os
import json
import time
from typing import Dict
from nonebot import get_driver
from nonebot.rule import Rule
from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.event import (Event, GroupMessageEvent, MessageEvent)
from Utils.CustumClass import OfflineFileEvent
from botConfig import GIDS, PAGIDS
SuperUsers:set[str] = get_driver().config.superusers


try:
    with open(file='./Resources/Json/ban.json', mode='r', encoding='utf-8-sig') as f:
        ban_dic:Dict[str,dict[str,int]] = json.load(f)
except:
    raise FileNotFoundError("没有找到ban.json，请检查项目是否完整")
else:
    pass

def check_white_list() -> Rule:
    """
    :说明:

        非封禁用户，私聊消息全都上，群聊消息则判断是否为指定群聊

    :参数:

        无
    """
    async def _check(event:Event) -> bool:
        try:
            return True if event.group_id in GIDS.values() else False   #type:ignore
        except:
            try:
                if event.user_id in ban_dic:    #type:ignore
                    return True if time.time() < ban_dic['QQnum']['Time'] else False
                else:
                    return True
            except:
                return True

    return Rule(_check)    #type:ignore
    
def Check_PA_Groups() -> Rule:
    """
    :说明:

        判断消息是否来源于需要进行图片鉴定的群聊

    :参数:

        无
    """
    async def _PAcheck(event: MessageEvent) -> bool:
        if isinstance(event, GroupMessageEvent):
            if event.group_id in PAGIDS.values():
                return True
            else:
                return False
        else:
            return False
    return Rule(_PAcheck)    #type:ignore

def only_master() -> Rule:
    """
    :说明:

        判定群聊管理员或bot管理员

    :参数:

      * 无
    """
    async def _only_master(bot: Bot, event: Event) -> bool:
        try:
            id = event.user_id  #type:ignore
            if str(id) in SuperUsers:
                return True
        except:
            return False
        else:
            if isinstance(event, GroupMessageEvent):
                return False if (await bot.get_group_member_info(group_id=event.group_id, user_id=event.user_id))['role'] == 'menber' else True
            else:
                return False
    return Rule(_only_master)   #type:ignore

def only_reply() -> Rule:
    """
    :说明:

        判定回复消息

    :参数:

      * 无
    """
    async def _only_reply(event:MessageEvent) -> bool:
        if isinstance(event, MessageEvent):
            try:
                getattr(event.reply,'message')
            except:
                return False
            else:
                return True
        else:
            return False
    return Rule(_only_reply)    #type:ignore

def is_menu() -> Rule:
    """
    :说明:

        判定是否为菜单文件

    :参数:

      * 无
    """
    async def _is_menu(event:OfflineFileEvent) -> bool:
        return True if event.file.name == 'menu.txt' else False
    return Rule(is_menu)    #type:ignore