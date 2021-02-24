"""
    Datalog包含的功能：
    1.重置模块（自动 手动）
    2.吹氵记录（写入 查询）

    memdic样例：
    {
        群号(str):
        {
            QQ号(str):次数(int),
            QQ号(str):次数(int),
            QQ号(str):次数(int),
            QQ号(str):次数(int),
            QQ号(str):次数(int)
        }
            群号(str):
        {
            QQ号(str):次数(int),
            QQ号(str):次数(int),
            QQ号(str):次数(int),
            QQ号(str):次数(int),
            QQ号(str):次数(int)
        }
            群号(str):
        {
            QQ号(str):次数(int),
            QQ号(str):次数(int),
            QQ号(str):次数(int),
            QQ号(str):次数(int),
            QQ号(str):次数(int)
        }
    }
"""
import os
import json
import re
import datetime

from config import bot_id, masterList
from costrule import check_white_list_all, check_white_list_group, only_master
from nonebot import get_bots, get_driver, on_command, require
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.adapters.cqhttp.message import Message
from nonebot.adapters.cqhttp.event import GroupIncreaseNoticeEvent, GroupMessageEvent
from nonebot.plugin import on_message, on_notice

memdic = {}
StartTime = datetime.datetime.now()
scheduler = require('nonebot_plugin_apscheduler').scheduler  # 定义计划任务
water = on_command("water", priority=5,
                   rule=check_white_list_all())  # 定义water查询命令
resetLog = on_command("resetLog", priority=5, rule=only_master())  # 定义手动重置模块
writeLog = on_message(rule=check_white_list_group(), priority=5)  # 定义吹氵记录增加
addLog = on_notice(priority=5)  # 定义群成员变动

try:
    with open(f"{os.getcwd()}\\Data_Base\\datalog.json", 'r', encoding="utf-8") as fr:
        memdic = json.load(fr)
except:
    pass


@scheduler.scheduled_job('cron', hour="0")  # 计划任务自动重置
async def start():
    global StartTime
    StartTime = datetime.datetime.now()
    bot = get_bots()[bot_id]
    for GPRID in get_driver().config.GroupList.values():
        await bot.send_group_msg(group_id=GPRID, message="吹水记录重置")
    await bot.send_private_msg(user_id=int(masterList[0]), message='初始化完毕')
    memdic = {}
    with open(f"{os.getcwd()}\\Data_Base\\datalog.json", 'w', encoding="utf-8") as f:
        json.dump(memdic, f, indent=2, sort_keys=True, ensure_ascii=False)


@resetLog.handle()  # 手动重置
async def resetLog_getCMD(bot: Bot, event: Event, state: dict):
    await start()


@water.handle()  # 发出查询请求
async def water_get(bot: Bot, event):
    args = str(event.get_message()).strip()
    if args and args != 'list':
        try:
            args = re.findall(r"\[CQ:at,qq=(\d+).*?\]", args)  # 正则匹配QQ号
            args = int(args[0])
        except:
            await water.finish("[参数处理错误：args]")  # 异常处理

    if isinstance(event, GroupMessageEvent):
        if args == 'list':  # 排行榜查询
            linedic = memdic[str(event.group_id)]
            findic = reversed(
                sorted(linedic.items(), key=lambda kv: (kv[1], kv[0])))
            a = 0
            pa = "-------氵怪排行榜-------"
            for elem in findic:
                UQID = elem[0]
                ts = elem[1]
                a = a+1
                pa = pa + f"\n{a}.[CQ:at,qq={UQID}] 吹水{ts}次"
                if a == 5:
                    break
            await bot.send_group_msg_async(group_id=int(event.group_id), message=Message(pa))
        elif isinstance(args, int):
            num = memdic[str(event.group_id)][str(args)]
            EndTime = datetime.datetime.now()
            msg = Message(
                "好耶！那就让我来康康宁有多氵\n"
                f"查询对象：[CQ:at,qq={str(args)}]\n"
                f"吹氵次数：{num}\n"
                f"起始时间：{StartTime}\n"
                f"终止时间：{EndTime}"
            )
            await water.finish(msg)
        else:  # 个人记录查询
            num = memdic[str(event.group_id)][str(event.user_id)]
            EndTime = datetime.datetime.now()
            msg = Message(
                "好耶！那就让我来康康宁有多氵\n"
                f"查询对象：[CQ:at,qq={str(event.user_id)}]\n"
                f"吹氵次数：{num}\n"
                f"起始时间：{StartTime}\n"
                f"终止时间：{EndTime}"
            )
            await water.finish(msg)
    else:
        await water.finish("请您高抬贵脚移步至群聊中查询可否？")


@addLog.handle()  # 成员变动增加条例
async def add_new_menber(bot: Bot, event):
    if isinstance(event, GroupIncreaseNoticeEvent):
        memdic[str(event.group_id)][str(event.user_id)] = 0


@writeLog.handle()  # 吹氵记录增加
async def add_number_of_water(bot: Bot, event):
    if isinstance(event, GroupMessageEvent):
        try:
            water_number = memdic[str(event.group_id)][str(
                event.user_id)]  # not found user
        except:
            try:
                memdic[str(event.group_id)][str(
                    event.user_id)] = 1  # not found group
            except:
                memdic[str(event.group_id)] = {}  # add group
                memdic[str(event.group_id)][str(event.user_id)] = 1  # add user
        else:
            water_number = water_number + 1
            memdic[str(event.group_id)][str(event.user_id)] = water_number
            with open(f"{os.getcwd()}\\Data_Base\\datalog.json", 'w', encoding="utf-8") as f:
                json.dump(memdic, f, indent=2,
                          sort_keys=True, ensure_ascii=False)
    else:
        pass
