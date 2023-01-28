"""
    Setu包含的功能：
    1.随机涩图(子功能)
    2.搜素定向涩图(子功能)
    3.调用LoliconAPI，限制调用时间（基础CD:60s，可以调控）
    4.图片存入库中
    5.requests改为https项目
    6.多个匹配指令，例如“来点涩图“、”来点XX涩图“、”整点好东西“之类的
    7.使用数学题防滥用
"""
import asyncio
import random
import re
import traceback
from .handle_setu import random_setu, search_setu
from .misc import RandomSetuMsg, SearchSetuMsg, SetuCommandTypeChecker
from .config import coolDown, coolDownLocal
from Utils.Builder import ExceptionBuilder
from Utils.LimitUtils import mathBuilder
from Utils.CustomRule import check_white_list, only_master
from nonebot import get_driver
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot.adapters.onebot.v11.helpers import Cooldown, CooldownIsolateLevel
from nonebot.plugin import on_command, on_regex

SuperUsers:set[str] = get_driver().config.superusers
global last_time
command_setu = on_command("setu", priority=5, rule=check_white_list() or only_master())
regex_setu_random = on_regex(pattern=r'^[来整]点[涩色活好康][的图儿]$|^[色涩]图来$|^冲[亿1一]发$|^冲$|^[色涩黄]图$', rule=check_white_list() or only_master())
regex_setu_search = on_regex(pattern=r'^[来整]点.\S*[色涩黄]图$|^[来整][几.\S*][张份个]\S*[色涩黄]图$', rule=check_white_list() or only_master())

last_time, resetTime = None, True
download_urls = []
word_to_int = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5
}
level_zh_dic = {
    "1": 'R18',
    "2": '混合',
    "0": '非18'
}


@command_setu.handle(parameterless=[Cooldown(cooldown=coolDown, prompt='太快了太快了会受不了的...', isolate_level=CooldownIsolateLevel.GROUP)])  # 通过命令调控涩图
async def _command_setu(event: MessageEvent, state:T_State):
    global last_time
    """
    命令1：#setu random level num
    命令2：#setu search keywords num
    """
    arg = str(event.get_message()).split()
    try:
        checked_type = SetuCommandTypeChecker(arg)  #进行命令检查
    except:
        await command_setu.finish(MessageSegment.at(event.user_id).text("[参数错误:args]\n传入了不正确的参数......\n请发送#help SETU查看帮助文档"))
    if checked_type == False:
        await command_setu.finish(MessageSegment.at(event.user_id).text("[参数错误:args]\n传入了不正确的参数......\n请发送#help SETU查看帮助文档"))
    else:
        prob = await mathBuilder(int(arg[3]))
        state['answer'] = prob[1] 
        await command_setu.send(f"欸等等！知识是打开宝库的金钥匙！动动脑动动手完成这道数学题吧！\n{prob[0]}")
        state['arg'] = arg

@command_setu.got("ans", prompt="")
async def _handle_command_setu(event: MessageEvent, state:T_State):
    global last_time
    if str(state['ans']) == state['answer']:
        arg = state['arg']
        if arg[1] == 'random':
            Rmodle, level, num = "command", arg[2], int(arg[3])
            level_zh = level_zh_dic[str(level)]
            handle_msg = await RandomSetuMsg(event.user_id,Rmodle,num,level_zh)
            await command_setu.send(handle_msg)
            try:
                setu = await random_setu(Rmodle='random', level=level, num=num)
            except:
                await command_setu.finish(f'[未知错误:Unknown]\n似乎出现了蜜汁错误......涩图拿到了但没完全拿到......\n{ExceptionBuilder(traceback.format_exc())}')
            else:
                pass
        elif arg[1] == 'search':
            Smodle, keywords, num = 'command', arg[2], int(arg[3])
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
        await command_setu.send('Active！！！')
        for msg in setu[1]:
            await command_setu.send(msg)
            await asyncio.sleep(0.1)
        await command_setu.finish()
    else:
        await command_setu.finish("计算题都算不对，才不给你这种baka看涩图！")


@regex_setu_random.handle(parameterless=[Cooldown(cooldown=coolDownLocal, prompt='太快了太快了会受不了的...', isolate_level=CooldownIsolateLevel.GROUP)])  # 正则匹配到随机涩图
async def _regex_setu_random(event: MessageEvent, state:T_State):
    num = random.randint(1, 5)
    prob = await mathBuilder(num)
    state['answer'] = prob[1] 
    state['num'] = num
    await command_setu.send(f"欸等等！知识是打开宝库的金钥匙！动动脑动动手完成这道数学题吧！\n{prob[0]}")


@regex_setu_random.got("ans", prompt="")
async def _handle_regex_setu_random(event: MessageEvent, state:T_State):
    global last_time
    if str(state['ans']) == state['answer']:
        Rmodle, level, num = "regex", "随机", state['num']
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
        await regex_setu_search.finish()
    else:
        await command_setu.finish("计算题都算不对，才不给你这种baka看涩图！")
    
@regex_setu_search.handle(parameterless=[Cooldown(cooldown=coolDown, prompt='太快了太快了会受不了的...', isolate_level=CooldownIsolateLevel.GROUP)])  # 正则匹配到定向涩图
async def _regex_setu_search(event: MessageEvent, state:T_State):
    if re.match(r'^[来整][几.\S*][张份个]\S*[色涩黄]图$', str(event.get_message())):    # 正则匹配1
        key = re.findall(r'^[来整][几.\S*][张份个](\S*?)[色涩黄]图$',str(event.get_message()))[0]
        num = re.findall(r'^[来整]([几.\S*]?)[张份个]\S*[色涩黄]图$',str(event.get_message()))[0]
        try:
            num = int(num)
        except:
            if num == '几':
                num = random.randint(1, 5)
            elif num in word_to_int:
                num = word_to_int[num]
            else:
                await regex_setu_search.finish("这......太多了Senrin会坏掉的哦......")
        else:
            if num > 5:
                await regex_setu_search.finish("这......太多了Senrin会坏掉的哦......")
    else:
        key = re.findall(r'^[来整]点(\S*?)[色涩黄]图$',str(event.get_message()))[0]  # 正则匹配2
        num = 1
    prob = await mathBuilder(num)
    state['answer'] = prob[1] 
    state['key'] = key
    state['num'] = num
    await command_setu.send(f"欸等等！知识是打开宝库的金钥匙！动动脑动动手完成这道数学题吧！\n{prob[0]}")

@regex_setu_search.got("ans", prompt="")
async def _handle_regex_setu_search(event: MessageEvent, state:T_State):
    if str(state['ans']) == state['answer']:
        key = state['key']
        num = state['num']
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
        await regex_setu_search.finish()
