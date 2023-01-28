"""
随机美图，来源：https://iw233.cn/API/
"""
from io import BytesIO
import random
from httpx import AsyncClient
from nonebot.plugin import on_regex
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot.adapters.onebot.v11.helpers import Cooldown, CooldownIsolateLevel
from Utils.CustomRule import check_white_list
from Utils.LimitUtils import mathBuilder

regex_meitu_random = on_regex(pattern=r'^[来整]点[美活好康][的图儿]$|^[美]图来$|^[美]图$|^[来整]点电子核酸$|^电子核酸$', rule=check_white_list())

@regex_meitu_random.handle(parameterless=[Cooldown(cooldown=5, prompt='太快了太快了会受不了的...', isolate_level=CooldownIsolateLevel.GROUP)])
async def _command_setu(event: GroupMessageEvent, state:T_State):
    prob = await mathBuilder(1)
    state['answer'] = prob[1] 
    state['num'] = 1
    await regex_meitu_random.send(f"欸等等！知识是打开宝库的金钥匙！动动脑动动手完成这道数学题吧！\n{prob[0]}")


@regex_meitu_random.got("ans", prompt="")
async def _handle_regex_setu_random(state:T_State):
    if str(state['ans']) == state['answer']:
        await regex_meitu_random.send("[RandomPic正常:Succeed]\nちょっと待ってください......")
        with open('./Resources/MeituTXT/rand.txt','r',encoding='utf-8') as f:
            l = f.read().split('\n')[:-1]
        url = l[random.randint(0,len(l)-2)]
        async with AsyncClient() as Client:
            response_pic = BytesIO((await Client.get(url)).read())
        await regex_meitu_random.finish(MessageSegment.image(response_pic))
    else:
        await regex_meitu_random.finish("计算题都算不对，才不给你这种baka看美图！")