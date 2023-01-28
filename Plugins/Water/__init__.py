"""
    群聊发言记录统计
    1.24h内发言次数
    2.自动重置+历史记录
    3.查询排行榜及个人
"""
from nonebot import get_bot, on_command, require
from nonebot.plugin import on_message
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot.adapters.onebot.v11.message import Message, MessageSegment

from Utils.MessageUtils import ScanNumber
from Utils.CustomRule import check_white_list
from.WaterClass import WaterInfo, WaterInfoSub

from botConfig import GIDS

water = on_message(priority=5, rule=check_white_list())
water_cmd = on_command("water", priority=5, rule=check_white_list())
scheduler = getattr(require('nonebot_plugin_apscheduler'),'scheduler') 

@scheduler.scheduled_job('cron', hour="0")
async def _scheduled_job():
    bot = get_bot()
    for group_id in GIDS.values():
        await bot.send_group_msg(group_id=group_id, message=MessageSegment.image(await WaterInfo().getRank(group_id, True)))
        await bot.send_group_msg(group_id=group_id, message="吹水记录已重置")
    await bot.send_private_msg(user_id=int(getattr(bot.config, "OWNER")), message='初始化完毕')

@water_cmd.handle()
async def _water_cmd(event:GroupMessageEvent, args:Message = CommandArg()):
    arg = args.extract_plain_text().split(" ")[0]
    if arg:
        await water.send("[water正常:Succeed]\nLoading...")
        if arg == 'list':
            await water.finish(MessageSegment.image(await WaterInfo().getRank(event.group_id, False)))
        else:
            qq = ScanNumber(event)
            if qq:
                await water.finish(WaterInfoSub(event).getPersonalWater(qq))
            else:
                await water_cmd.finish("[参数错误:args]传入参数过少或错误，请发送#help WTER查看帮助文档")
    else:
        await water.finish(WaterInfoSub(event).getPersonalWater(event.user_id))
@water.handle()
async def _add_water(event:GroupMessageEvent):
    WaterInfoSub(event).add()
    await water.finish()

