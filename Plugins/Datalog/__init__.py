"""
    Datalog包含的功能：
    1.重置模块（自动 手动）
    2.吹氵记录（写入 查询）
"""
import os
import json
import datetime
from nonebot.permission import SUPERUSER
from Utils.CustomRule import check_white_list
from Utils.TypeChecker import ScanNumber
from nonebot import get_bot, on_command, require
from nonebot.adapters.cqhttp import Bot
from nonebot.adapters.cqhttp.event import GroupIncreaseNoticeEvent, GroupMessageEvent, MessageEvent
from nonebot.plugin import on_message, on_notice

from config import GIDS
from .Datalog import *

LogPath = os.path.join(os.getcwd(), 'Resources', 'Json', 'datalog.json')
StartTime = datetime.datetime.now()
scheduler = getattr(require('nonebot_plugin_apscheduler'),'scheduler')  # 定义计划任务
water = on_command("water", priority=5, rule=check_white_list())  # 定义water查询命令
resetLog = on_command("resetLog", priority=5, permission=SUPERUSER)  # 定义手动重置模块
writeLog = on_message(rule=check_white_list(), priority=5)  # 定义吹氵记录增加
addLog = on_notice(priority=5)  # 定义群成员变动

def getMendic() ->dict:
    try:
        with open(LogPath, 'r', encoding="utf-8") as fr:
            return json.load(fr)
    except:
        return {}

@scheduler.scheduled_job('cron', hour="0")  # 计划任务自动重置
async def _scheduled_job():
    bot = get_bot()
    for group_id in GIDS.values():
        _msg = await get_water_list(memdic=getMendic(), groupID=group_id, bot=bot)
        await bot.send_group_msg(group_id=group_id, message=_msg)
        await bot.send_group_msg(group_id=group_id, message="吹水记录已重置")
    await bot.send_private_msg(user_id=int(getattr(bot.config, "OWNER")), message='初始化完毕')
    await start(LogPath)


@resetLog.handle()  # 手动重置
async def _resetLog_getCMD(bot: Bot, event: MessageEvent, state: dict):
    await start(LogPath)
    await resetLog.finish()


@water.handle()  # 发出查询请求
async def _water_get(bot: Bot, event: MessageEvent):
    args = str(event.get_message()).split()
    if args:
        if args[0] == 'list':
            await water.send("[water正常:Succeed]\nLoading...")
            arg = "list"
        else:
            arg = await ScanNumber(event)
    else:
        arg = event.user_id
    _msg = await water_get(arg, LogPath, event, bot)
    await water.finish(_msg)


@addLog.handle()  # 成员变动增加条例
async def _add_new_menber(bot: Bot, event: GroupIncreaseNoticeEvent):
    await add_new_menber(getMendic(), event)
    await addLog.finish()


@writeLog.handle()  # 吹氵记录增加
async def _add_number_of_water(bot: Bot, event: GroupMessageEvent):
    await add_number_of_water(getMendic(), LogPath, bot, event)
    await writeLog.finish()
