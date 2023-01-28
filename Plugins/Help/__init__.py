"""
    帮助文档V1.0.0
    似乎可以用到正则
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment
from Utils.CustomRule import check_white_list
import os
import json


with open('./Resources/HelpTXT/HelpList.txt', 'r', encoding='utf-8-sig') as hp:
    HelpList = hp.read()
with open('./Resources/Json/wordbank.json', 'r', encoding="utf-8") as fr:
    studylib = json.load(fr)
at_msg_reply = studylib['public']['preinstall_words']['at_msg_reply']

help = on_command("help", priority=5, rule=check_white_list())


@help.handle()
async def handle_help(bot: Bot, event: MessageEvent):
    args = str(event.get_message()).split(" ")
    if len(args) > 1:
        await bot.send(event, "get it!")
        if f"{args[1]}.txt" in os.listdir("./Resources/HelpTXT/"):
            with open(f"./Resources/HelpTXT/{args[1]}.txt", mode='r', encoding='utf-8-sig') as files:
                msg = files.read()
        else:
            msg = (f"[参数错误：functionID]\n可恶，Senrin把脑子都掏空了都没找到“{args[1]}”！！！\n")
        await help.finish(msg)
    else:
        msg = (
            MessageSegment.text('[help正常：Succeed]\n嘿嘿！Senrin会的有这些！快输入功能代码获取帮助吧！\n')
            +MessageSegment.at(event.user_id)+MessageSegment.text('Senrin目前支持的功能如下：\n')
            +MessageSegment.text(HelpList)
        )
        await help.send(msg)