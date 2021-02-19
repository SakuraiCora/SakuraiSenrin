"""
    Notices包含的功能：
    1.迎新(不一定是固定的哦~)
    2.禁言检测
    3.运气王检测(bug)
    4.退群检测
    5.处理好友请求
    6.整点报时+通报公告
"""
import datetime
import random
from ...config import post_id, bot_id
from httpx import AsyncClient
from nonebot import get_driver, get_bots
from nonebot.adapters.cqhttp import Bot
from nonebot.adapters.cqhttp.message import Message
from nonebot.adapters.cqhttp.event import (FriendRequestEvent, GroupBanNoticeEvent,
                                           GroupDecreaseNoticeEvent,
                                           GroupIncreaseNoticeEvent,
                                           LuckyKingNotifyEvent)
from nonebot.plugin import on_notice, on_request, require

WelcomeList = ['新人を歓迎する！', '有朋自远方来，不宜用转唬？唬不死再唬！']
scheduler = require('nonebot_plugin_apscheduler').scheduler  # 定义计划任务
member_var = on_notice(priority=5)
ban_members = on_notice(priority=5)
lucky_king = on_notice(priority=5)
friend_add = on_request(priority=5)


@member_var.handle()  # 群成员变化检测  迎新 退群通告
async def _change_menbers(bot: Bot, event):
    if isinstance(event, GroupIncreaseNoticeEvent):  # 增加
        WelcomeTence = random.choice(WelcomeList)
        msg = Message(
            f'[CQ:at,qq={str(event.user_id)}]\n'
            f'{WelcomeTence}\n'
            '我只是个无情的机器人，请通过#help查看帮助\n'
            '顺带一提，年轻人要学会控制自己的欲望~~~'
        )
        await member_var.finish(msg)
    elif isinstance(event, GroupDecreaseNoticeEvent):  # 减少
        if event.operator_id == event.user_id:
            out_time = datetime.datetime.now()
            msg = Message(
                '芜湖~有一位群友起飞了\n'
                '一路飞好吧......\n'
                f'起飞的群友：{str(event.user_id)}\n'
                f'起飞的时间：{out_time}'
            )
            await member_var.finish(msg)
        else:
            out_time = datetime.datetime.now()
            msg = Message(
                '欸？刚刚什么人飞过去了呢？\n'
                '啊！原来是被群管扔出去的呢......\n'
                f'空中飞人：{str(event.user_id)}\n'
                f'起飞时间：{out_time}\n'
            )
            await member_var.finish(msg)


@ban_members.handle()  # 禁言
async def _ban_menbers(bot: Bot, event):
    if isinstance(event, GroupBanNoticeEvent):  # 禁言
        if event.group_id in get_driver().config.GroupList.values():
            if event.duration:
                msg = Message(
                    '欸？好像有人被塞上了口球呢......\n'
                    f'对象：[CQ:at,qq={str(event.user_id)}]\n'
                    f'时长：{str(event.duration)}s'
                )
                await ban_members.finish(msg)
            else:
                msg = Message(
                    '好耶！口球被取下来咯~~~\n'
                    f'对象：[CQ:at,qq={str(event.user_id)}]'
                )
                await ban_members.finish(msg)


# @lucky_king.handle()
# async def _lucky_king(bot: Bot, event):
#     if isinstance(event, LuckyKingNotifyEvent):
#         msg = Message(
#             '好耶！又有运气王欸！\n'
#             '干等着干嘛啊，快继续啊！！！\n'
#             f'[CQ:at,qq={str(event.target_id)}]说的就是宁呐！'
#         )
#         await lucky_king.finish(msg)


@friend_add.handle()
async def _friend_add(bot: Bot, event):
    if isinstance(event, FriendRequestEvent):
        add_time = datetime.datetime.now()
        msg = (
            '上报好友请求：\n'
            f'请求人：{str(event.user_id)}\n'
            f'申请信息：{str(event.comment)}\n'
            f'申请时间：{add_time}'
        )
        await bot.send_private_msg(user_id=post_id, message=msg)


@scheduler.scheduled_job('cron', hour='*')
async def ReportTime():
    async with AsyncClient() as Client:
        host = 'https://v1.hitokoto.cn/?c=f&encode=text'
        response = await Client.get(url=host)
        result = response.text
    bot = get_bots()[bot_id]
    hour = datetime.datetime.now().hour
    msg = (
        "How time flies!\n"
        f"现在是北京时间{hour}：00\n"
        "-----------------------\n"
        f"{result}"
    )
    for GroupID in get_driver().config.GroupList.values():
        await bot.send_group_msg_async(group_id=GroupID, message=msg)