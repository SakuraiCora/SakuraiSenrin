"""
    Info包含的功能：
    根据有限的信息制作资料卡
"""

import datetime
from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot.plugin import on_command
from Utils.TypeChecker import ScanNumber
from Utils.ImageUtils import get_info_card
from Utils.CustomRule import check_white_list


info = on_command('info', priority=5, rule=check_white_list())


@info.handle()
async def info_get(bot: Bot, event:GroupMessageEvent):
    args = await ScanNumber(event)
    if not args:
        args = event.user_id
    if isinstance(event, GroupMessageEvent) and isinstance(args, int):
        if event.to_me == True:
            QQnum = int(bot.self_id)
        else:  # 个人记录查询
            QQnum = args
        await info.send('[info正常：Succeed]\n在做了在做了在做了在......')
        member_info = await bot.get_group_member_info(group_id=event.group_id, user_id=QQnum)
        dateArray = datetime.datetime.utcfromtimestamp(member_info['join_time'])
        join_time_format = dateArray.strftime("%Y-%m-%d %H:%M:%S")
        save_path = await get_info_card(QQnum, member_info['nickname'], member_info['sex'], member_info['title'], f"LV.{member_info['level']}", join_time_format)
        await info.finish(save_path)
    else:
        await info.finish("[未知错误：Unknown]\n请您高抬贵脚移步至群聊中查询可否？")
