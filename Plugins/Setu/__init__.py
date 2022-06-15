"""
    Setu包含的功能：
    1.随机涩图(子功能)
    2.搜素定向涩图(子功能)
    3.调用LoliconAPI，限制调用时间（基础CD:100S，做数学题可以减少CD）这个项目就咕咕咕了吧
    4.图片存入库中
    5.requests改为https项目
    6.多个匹配指令，例如“来点涩图“、”来点XX涩图“、”整点好东西“之类的
    7.调控CD    咕咕咕
"""
import asyncio
import random
import re
import datetime
import traceback
from .handle_setu import random_setu, search_setu
from Utils.Builder import RandomSetuMsg, SearchSetuMsg, ExceptionBuilder
from Utils.TimeUtils import Limit
from Utils.CustomRule import check_white_list, only_master
from Utils.TypeChecker import SetuCommandTypeChecker
from nonebot import get_driver
from nonebot.adapters.cqhttp import Bot
from nonebot.adapters.cqhttp.event import MessageEvent
from nonebot.adapters.cqhttp.message import MessageSegment
from nonebot.plugin import on_command, on_regex

SuperUsers:set[str] = get_driver().config.superusers
global last_time
command_setu = on_command("setu", priority=5, rule=check_white_list()&only_master())
regex_setu_random = on_regex(pattern=r'^[来整]点[涩色活好康][的图儿]$|^[色涩]图来$|^冲[亿1一]发$|^冲$|^[色涩黄]图$', rule=check_white_list() or only_master())
regex_setu_search = on_regex(pattern=r'^[来整]点.\S*[色涩黄]图$|^[来整][几.\S*][张份个]\S*[色涩黄]图$', rule=check_white_list()&only_master())

last_time, resetTime = None, True
download_urls = []
word_to_int = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10
}
level_zh_dic = {
    "1": 'R18',
    "2": '混合',
    "0": '非18'
}


@command_setu.handle()  # 通过命令调控涩图
async def _command_setu(bot: Bot, event: MessageEvent, state: dict):
    """
    命令1：#setu random level num
    命令2：#setu search keywords num
    """
    arg = str(event.get_message()).split()
    checked_type = SetuCommandTypeChecker(arg)  #进行命令检查
    if checked_type == False:
        await command_setu.finish(MessageSegment.at(event.user_id).text("[参数错误:args]\n传入了不正确的参数......\n然后指令坏掉了，Senrin处理了个寂寞"))
    else:
        try:
            timeChecker = await Limit(last_time, 30)  #type:ignore    
        except: #初次启动无记录时间
            timeChecker = True
        else:
            pass
        if timeChecker or str(event.user_id) in SuperUsers:
            if arg[0] == 'random':
                Rmodle, level, num = "command", arg[1], int(arg[2])
                level_zh = level_zh_dic[str(level)]
                handle_msg = await RandomSetuMsg(event.user_id,Rmodle,num,level_zh)
                await command_setu.send(handle_msg)
                try:
                    setu = await random_setu(Rmodle='random', level=level, num=num)
                except:
                    await command_setu.finish(f'[未知错误:Unknown]\n似乎出现了蜜汁错误......涩图拿到了但没完全拿到......\n{ExceptionBuilder(traceback.format_exc())}')
                else:
                    pass
            elif arg[0] == 'search':
                Smodle, keywords, num = 'command', arg[1], int(arg[2])
                handle_msg = await SearchSetuMsg(event.user_id,Smodle,keywords,num)
                await command_setu.send(handle_msg)
                try:
                    setu = await search_setu(Keywords=keywords, num=num)
                except:
                    await command_setu.finish(f'[未知错误:Unknown]\n似乎出现了蜜汁错误......涩图拿到了但没完全拿到......\n{ExceptionBuilder(traceback.format_exc())}')
                else:
                    pass
            else:
                setu = (False,[])
            if setu[0] and str(event.user_id) not in SuperUsers: #重置涩图CD(除了超级用户)
                last_time = datetime.datetime.now()
                await command_setu.finish()
        else:
            await command_setu.finish(MessageSegment.at(event.user_id)+MessageSegment.text("涩图CD还没到，Senrin处理了个寂寞"))
    await command_setu.send('Active！！！')
    for msg in setu[1]:
        await command_setu.send(msg)
        await asyncio.sleep(0.1)
    await command_setu.finish()


@regex_setu_random.handle()  # 正则匹配到随机涩图
async def _regex_setu_random(bot: Bot, event: MessageEvent, state: dict):
    try:
        timeChecker = await Limit(last_time, 30)  #type:ignore    
    except: #初次启动无记录时间
        timeChecker = True
    else:
        pass
    if timeChecker or str(event.user_id) in SuperUsers:
        Rmodle, level, num = "regex", "随机", random.randint(1, 10)
        handle_msg = await RandomSetuMsg(event.user_id,Rmodle,num,level)
        await regex_setu_random.send(handle_msg)
        try:
            setu = await random_setu(Rmodle='regex', level=level, num=num)
        except:
            await command_setu.finish(f'[未知错误:Unknown]\n似乎出现了蜜汁错误......涩图拿到了但没完全拿到......\n{ExceptionBuilder(traceback.format_exc())}')
        else:
            pass
        if setu[1]:
            await regex_setu_search.send('Active！！！')
            for msg in setu[1]:
                await asyncio.sleep(0.1)
                await regex_setu_random.send(msg)
        if setu[0] and str(event.user_id) not in SuperUsers: #重置涩图CD(除了超级用户)
            last_time = datetime.datetime.now()
        await regex_setu_search.finish()
    else:
        await regex_setu_search.finish(MessageSegment.at(event.user_id)+MessageSegment.text("涩图CD还没到，Senrin处理了个寂寞"))


@regex_setu_search.handle()  # 正则匹配到定向涩图
async def _regex_setu_search(bot: Bot, event: MessageEvent, state: dict):
    try:
        timeChecker = await Limit(last_time, 30)  #type:ignore    
    except: #初次启动无记录时间
        timeChecker = True
    else:
        pass
    if timeChecker or str(event.user_id) in SuperUsers:
        if re.match(r'^[来整][几.\S*][张份个]\S*[色涩黄]图$', str(event.get_message())):    # 正则匹配1
            key = re.findall(r'^[来整][几.\S*][张份个](\S*?)[色涩黄]图$',str(event.get_message()))[0]
            num = re.findall(r'^[来整]([几.\S*]?)[张份个]\S*[色涩黄]图$',str(event.get_message()))[0]
            if num == '几':
                num = random.randint(1, 10)
            elif num in word_to_int:
                num = word_to_int[num]
            else:
                await regex_setu_search.finish("这......太多了Senrin会坏掉的哦......")
        else:
            key = re.findall(r'^[来整]点(\S*?)[色涩黄]图$',str(event.get_message()))[0]  # 正则匹配2
            num = 1
        handle_msg = await SearchSetuMsg(event.user_id,'regex',key,num)
        await regex_setu_search.send(handle_msg)
        try:
            setu = await search_setu(Keywords=key, num=num)
        except:
            await command_setu.finish(f'[未知错误:Unknown]\n似乎出现了蜜汁错误......涩图拿到了但没完全拿到......\n{ExceptionBuilder(traceback.format_exc())}')
        else:
            pass
        if setu[1]:
            await regex_setu_search.send('Active！！！')
            for msg in setu[1]:
                await asyncio.sleep(0.1)
                await regex_setu_random.send(msg)
        if setu[0] and str(event.user_id) not in SuperUsers: #重置涩图CD(除了超级用户)
            last_time = datetime.datetime.now()
        await regex_setu_search.finish()
    else:
        await regex_setu_search.finish(MessageSegment.at(event.user_id)+MessageSegment.text("涩图CD还没到，Senrin处理了个寂寞"))
