"""
    处理at/poke次数，每小时重置，并发送消息
"""

from nonebot import require
from nonebot.rule import to_me
from nonebot.plugin import on_message, on_notice
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, PokeNotifyEvent

from Utils.CustomRule import check_white_list
from .CovClass import CovInfo, AtInfo, PokeInfo

cov_at = on_message(rule=to_me()&check_white_list(), priority=5)
cov_poke = on_notice(rule=to_me()&check_white_list(), priority=5)

scheduler = getattr(require('nonebot_plugin_apscheduler'),'scheduler') 

@scheduler.scheduled_job('cron', hour="*")
async def _scheduled_job():
    CovInfo().dropTable()

@cov_at.handle()
async def _cov_at(event:GroupMessageEvent):
    ci = AtInfo(event.user_id)
    await cov_at.send(ci.getAtMsg())
    ci.addAt()
    await cov_at.finish()

@cov_poke.handle()
async def _cov_poke(event:PokeNotifyEvent):
    ci = PokeInfo(event.user_id)
    await cov_poke.send(ci.getPokeMsg())
    ci.addPoke()
    await cov_poke.finish()