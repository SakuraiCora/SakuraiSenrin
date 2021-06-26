"""
    帮助文档V1.0.0
    似乎可以用到正则
    处理被at的信息
"""

from nonebot import on_command, on_message
from nonebot import rule
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.adapters.cqhttp.event import PrivateMessageEvent
from nonebot.adapters.cqhttp.message import Message
from nonebot.rule import to_me
from ...costrule import check_white_list_all
import os
functionList = ['AWHD']
HelpPath = os.path.join(os.getcwd(), 'DataBase', 'HelpTXT')

help = on_command("help", priority=5, rule=check_white_list_all())
at_msg = on_message(rule=to_me() & check_white_list_all(), priority=5)


@help.handle()
async def handle_help(bot: Bot, event: Event, state: dict):
    args = str(event.get_message()).strip()
    if args:
        state["functionID"] = args
        await bot.send(event, "get it!")
    else:
        msg = (
            '请输入对应功能代码获取帮助~\n'
            f'[CQ:at,qq={event.get_user_id()}]Zer0目前支持的功能如下：\n'
            'AWHD   网页版帮助文档'
        )
        await help.send(Message(msg))


@help.got("functionID")
async def got_funtionID(bot: Bot, event: Event, state: dict):
    functionID = state["functionID"]
    if functionID == "exit":
        await help.finish(f"exit suceed...")
    if functionID not in functionList:
        await help.reject(f"[Error 404]\nNo FuntionID as {functionID}!Please try again or input ""exit"" to exit this function.")
    with open(os.path.join(HelpPath, functionID+'.txt'), mode='r', encoding='utf-8-sig') as files:
        msg = files.readline()
    await help.finish(Message(msg))


@at_msg.handle()
async def _at_msg(bot: Bot, event: Event):
    if isinstance(event, PrivateMessageEvent):
        return
    else:
        msg = (
            'nmd叫我搞锤子？'
        )
        await at_msg.finish(msg)
