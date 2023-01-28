"""
    Notices包含的功能：
    1.迎新(不一定是固定的哦~)
    2.禁言检测
    3.运气王检测(bug)
    4.退群检测
    5.处理好友请求
    6.整点报时+通报公告
"""
import json
import datetime
import random
import os
import math
from io import BytesIO
from httpx import AsyncClient
from Utils.CustomRule import check_white_list, GIDS
from Utils.ImageUtils import get_head_img
from nonebot import get_bot
from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot.adapters.onebot.v11.event import (FriendRequestEvent, GroupBanNoticeEvent,
                                           GroupDecreaseNoticeEvent,
                                           GroupIncreaseNoticeEvent,
                                           LuckyKingNotifyEvent)
from nonebot.plugin import on_notice, on_request, require

scheduler = getattr(require('nonebot_plugin_apscheduler'),'scheduler')

with open("./Resources/Json/wordbank.json", 'r', encoding="utf-8") as fr:
    handle_new_member = json.load(fr)['public']['preinstall_words']['handle_new_member']
member_inc = on_notice(priority=5, rule=check_white_list())
member_dec = on_notice(priority=5, rule=check_white_list())
ban_members = on_notice(priority=5, rule=check_white_list())
lucky_king = on_notice(priority=5, rule=check_white_list())
friend_add = on_request(priority=5)
gaokao_time = datetime.datetime(datetime.datetime.now().year, 6, 7)


@member_inc.handle()  # 群成员变化检测  迎新 退群通告
async def _inc_menbers(bot: Bot, event: GroupIncreaseNoticeEvent):
    HeadImg = await get_head_img(event.user_id)
    WelcomeTence = random.choice(handle_new_member)
    msg = (
        MessageSegment.image(BytesIO(HeadImg))
        +MessageSegment.at(event.user_id)
        +MessageSegment.text(f'{WelcomeTence}\n')
        +MessageSegment.text('这里是樱井千凛Senrin，请多指教~\n')
        +MessageSegment.text('可发送#help以获取帮助')
    )
    await member_inc.finish(msg)

@member_dec.handle()
async def _dec_menbers(bot: Bot, event: GroupDecreaseNoticeEvent):
    HeadImg = await get_head_img(event.user_id)
    if event.operator_id == event.user_id:
        msg = (
            MessageSegment.text(f"悲！{event.user_id}润了......\n")
            +MessageSegment.image(BytesIO(HeadImg))
        )
    else:
        msg = (
            MessageSegment.text(f"乐，有幸目击{event.user_id}被杀\n")
            +MessageSegment.image(BytesIO(HeadImg))
        )
    await member_dec.finish(msg)


@ban_members.handle()  # 禁言
async def _ban_menbers(bot: Bot, event: GroupBanNoticeEvent):
    if event.duration:
        msg = (
            MessageSegment.text('好！口球塞上嘿嘿嘿~~~\n')
            +MessageSegment.text('对象：')+MessageSegment.at(event.user_id)
            +MessageSegment.text(f'时长：{str(event.duration)}s')
        )
        await ban_members.finish(msg)
    else:
        msg = (
            MessageSegment.text('可恶，口球怎么掉了！\n')
            +MessageSegment.text('对象：')+MessageSegment.at(event.user_id)
        )
        await ban_members.finish(msg)


@lucky_king.handle()
async def _lucky_king(bot: Bot, event: LuckyKingNotifyEvent):
    msg = (
        MessageSegment.text('有人拿到了大红包是谁我不说（\n')
        +MessageSegment.at(event.target_id)
    )
    await lucky_king.finish(msg)


@friend_add.handle()
async def _friend_add(bot: Bot, event: FriendRequestEvent):
    add_time = datetime.datetime.now()
    msg = (
        '上报好友请求：\n'
        f'请求人：{str(event.user_id)}\n'
        f'申请信息：{str(event.comment)}\n'
        f'申请时间：{add_time}'
    )
    await bot.send_private_msg(user_id=int(getattr(bot.config, "OWNER")), message=msg)
    if event.comment == 'Senrin':
        await bot.set_friend_add_request(flag=event.flag, approve=True)
    else:
        await bot.set_friend_add_request(flag=event.flag, approve=False)


@scheduler.scheduled_job('cron', hour='*')
async def ReportTime():
    async with AsyncClient() as Client:
        host = 'https://v1.hitokoto.cn/?c=f&encode=text'
        response = await Client.get(url=host)
        result = response.text
    bot = get_bot()
    hour = datetime.datetime.now().hour
    gaokao_time = datetime.datetime((datetime.datetime.now().year), 6, 7, 9)
    delta = gaokao_time-datetime.datetime.now()

    # 判定是否为高考期间
    if datetime.datetime.now().month == 6 and datetime.datetime.now().day in [8, 9, 10]:    #   还不信那个地方高考考5天了（
        gk_msg = '高考加油！！！祝高三党们考的全会，蒙的全对，金榜题名，赢得干脆！'
    elif delta.days < 0:    # 次年高考
            gaokao_time = datetime.datetime((datetime.datetime.now().year+1), 6, 7)
            delta = gaokao_time-datetime.datetime.now()
            finger_out = delta.days+1
            gk_msg = f'距离{datetime.datetime.now().year+1}年高考仅有{finger_out}天！\n'
    elif delta.days == 0:  # 24h倒计时+6.7
        gaokao_time = datetime.datetime((datetime.datetime.now().year), 6, 7, 9)
        delta = gaokao_time-datetime.datetime.now()
        if delta.seconds > 0:
            finger_out = math.ceil((delta.seconds)/3600)
            gk_msg = f'距离{datetime.datetime.now().year}年高考仅有{finger_out}小时！\n'
        else:
            gk_msg = '高考加油！！！祝高三党们考的全会，蒙的全对，金榜题名，赢得干脆！'
    else:  # 无特殊情况
        gaokao_time = datetime.datetime((datetime.datetime.now().year), 6, 7)
        delta = gaokao_time-datetime.datetime.now()
        finger_out = delta.days+1
        gk_msg = f'距离{datetime.datetime.now().year}年高考仅有{finger_out}天！\n'
    msg = (
        "How time flies!\n"
        f"现在是北京时间{hour}：00\n"
        f"{gk_msg}"
        "-----------------------\n"
        f"{result}"
    )
    for GroupID in GIDS.values():
        await bot.send_group_msg_async(group_id=GroupID, message=msg)