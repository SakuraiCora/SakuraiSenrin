"""
    帮助文档V1.0.0
    似乎可以用到正则
    处理被at的信息
"""

from nonebot import on_command, on_message
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.adapters.cqhttp.event import PrivateMessageEvent
from nonebot.adapters.cqhttp.message import Message
from nonebot.rule import to_me
from costrule import check_white_list_all
import os
import json
import random

HelpPath = os.path.join(os.getcwd(), 'DataBase', 'HelpTXT')
StudyPath = os.path.join(os.getcwd(), 'DataBase', 'Json', 'studylib.json')

with open(os.path.join(HelpPath,'HelpList.txt'), 'r', encoding='utf-8-sig') as hp:
    HelpList = hp.read()
with open(StudyPath, 'r', encoding="utf-8") as fr:
    studylib = json.load(fr)
at_msg_reply = studylib['public']['preinstall_words']['at_msg_reply']

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
            '请直接输入功能代码获取帮助~\n'
            f'[CQ:at,qq={event.get_user_id()}]Senrin目前支持的功能如下：\n'
            f'{HelpList}'
        )
        await help.send(Message(msg))


@help.got("functionID")
async def got_funtionID(bot: Bot, event: Event, state: dict):
    functionID = state["functionID"]
    if functionID == "exit":
        await help.finish(f"exit suceed...")
    else:
        try:
            with open(os.path.join(HelpPath, functionID+'.txt'), mode='r', encoding='utf-8-sig') as files:
                msg = files.read()
            await help.send(Message(msg))
        except:
            await help.reject("[参数错误]\n"
                            f"悲乎！没有找到功能代码为 “{functionID}” 的功能......\n"
                            "请重新输入功能代码，或输入 “exit”  来退出帮助文档")
        else:
            await help.finish()

@at_msg.handle()
async def _at_msg(bot: Bot, event: Event):
    if isinstance(event, PrivateMessageEvent):
        return
    else:
        msg = random.choice(at_msg_reply)
        await at_msg.finish(msg)
