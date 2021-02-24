"""
    Pixiv包含的功能：
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
import os
import re
import datetime
import aiohttp
from config import lolicon_api, masterList, setu_path
from httpx import AsyncClient
from nonebot import get_driver
from nonebot.adapters.cqhttp import Bot
from nonebot.adapters.cqhttp.event import (
    Event, GroupMessageEvent, PrivateMessageEvent)
from nonebot.adapters.cqhttp.message import Message
from nonebot.plugin import on_command, on_regex

global last_time_command, last_time_Rrandom, resetTime
command_setu = on_command("setu", priority=5)
regex_setu_random = on_regex(
    pattern=r'^[来整]点[涩色活好康][的图儿]$|^[色涩]图来$|^冲[亿1一]发$|^冲$|^[色涩黄]图$')
regex_setu_search = on_regex(
    pattern=r'^[来整]点.\S*[色涩黄]图$|^[来整][几.\S*][张份个]\S*[色涩黄]图$')

last_time_command, last_time_Rrandom, resetTime = '', '', True
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


async def get_setu(modle, level, num, key):  # 定义获取函数
    global resetTime
    setu = []
    if modle == 'random':
        post_data = {"apikey": lolicon_api, "r18": level, "num": num}
    elif modle == 'search':
        post_data = {"apikey": lolicon_api, "keyword": key, "num": num}
    else:
        post_data = {}
    async with AsyncClient(proxies={}) as Client:
        host = "http://api.lolicon.app/setu/"
        response = await Client.post(url=host, params=post_data)
        result = response.json()
    if result['code'] == 404:
        setu = [f'悲！没有符合条件的涩图：{key}']
        resetTime = False
    else:
        quota = result['quota']
        for one in result['data']:
            resetTime = True
            img_url, title, author, pixivID = one['url'], one['title'], one['author'], one['pid']
            tags = one['tags']
            all_tag = ''
            for tag in tags:
                all_tag += f"{tag} "
            PicName = img_url.split("/")[-1]
            way = os.path.join(setu_path, PicName.split("/")[-1])
            download_urls.append(img_url)  # 在全局中储存下载链接
            msg = (f"[CQ:image,file=file:///{way}]\n"
                   f"插画名称：{title}\n"
                   f"插画作者：{author}\n"
                   f"插画ID:{pixivID}\n"
                   f"tags：{all_tag}\n"
                   f"剩余调用次数：{quota}")
            setu.append(msg)

        async def job(session, url):
            way = os.path.join(setu_path, url.split("/")[-1])
            get_pic = await session.get(url)
            get_pic = await get_pic.read()
            with open(way, "wb") as ffs:
                ffs.write(get_pic)
            return str(url)

        async def main(loop, URL, num):
            async with aiohttp.ClientSession() as session:
                num = len(URL)
                tasks = [loop.create_task(job(session, URL[RR]))
                         for RR in range(num)]
                await asyncio.sleep(0.1)
                await asyncio.gather(*tasks)
        loop = asyncio.get_event_loop()
        await main(loop, download_urls, num)
    return setu


async def random_setu(Rmodle, level, num):  # 随机涩图函数封装
    if Rmodle == 'regex':
        pixivID = random.choice(os.listdir(setu_path))
        way = os.path.join(setu_path, pixivID)  # 从本地库整一个
        setu = [f"[CQ:image,file=file:///{way}]"]
    else:
        modle = 'random'
        setu = await get_setu(modle=modle, level=level, num=num, key=None)
    return setu


async def search_setu(Keywords, num):  # 定向涩图函数封装
    modle = 'search'
    setu = await get_setu(modle=modle, level=None, num=num, key=Keywords)
    return setu


@command_setu.handle()  # 通过命令调控涩图   #setu random level num  #setu search keywords num
async def _command_setu(bot: Bot, event: Event, state: dict):
    global last_time_command

    def check_tpye(arg):  # 检查命令格式
        if arg:
            if arg[0] == 'random':
                try:
                    level = int(arg[1])
                    num = int(arg[2])
                except:
                    check_type = False
                else:
                    if level in [1, 2, 0] and num <= 10:
                        check_type = True
                    else:
                        check_type = False
            elif arg[0] == 'search':
                try:
                    num = int(arg[2])
                except:
                    check_type = False
                else:
                    check_type = True if num <= 10 else False
            else:
                check_type = False
        else:
            check_type = False
        return check_type
    if isinstance(event, GroupMessageEvent):
        if event.group_id in [get_driver().config.GroupList['last'], get_driver().config.GroupList['test']]:
            arg = str(event.get_message()).split()
            checked_type = check_tpye(arg)
            if checked_type == False:
                setu = None
                await command_setu.finish(Message(f"[CQ:at,qq={event.user_id}]传入了不正确的参数......\n然后指令坏掉了，Zer0处理了个寂寞"))
            else:
                if arg[0] == 'random':
                    level, num = arg[1], int(arg[2])
                    start_time = datetime.datetime.now()  # 取现在时间
                    # 用于判定程序是否为初次启动，检测last_time是否被赋值
                    if isinstance(last_time_command, datetime.datetime):
                        if (start_time-last_time_command).seconds <= 60:
                            if str(event.user_id) not in masterList:
                                await command_setu.finish("我球球你了让Zer0歇一会儿吧......爪巴涩图很累的说......")
                                return
                            else:
                                await command_setu.send("我爪巴爪巴......这就去......")
                    level_zh = level_zh_dic[str(level)]
                    handle_msg = (
                        f"[CQ:at,qq={event.user_id}]随机涩图触发\n"
                        "触发方式：command\n"
                        f"图片分级：{level_zh}\n"
                        f"图片数量：{num}\n"
                        "Loading......（约15秒钟）"
                    )
                    await command_setu.send(Message(handle_msg))
                    setu = await random_setu(Rmodle='random', level=level, num=num)
                elif arg[0] == 'search':
                    keywords, num = arg[1], int(arg[2])
                    start_time = datetime.datetime.now()  # 取现在时间
                    # 用于判定程序是否为初次启动，检测last_time是否被赋值
                    if isinstance(last_time_command, datetime.datetime):
                        if (start_time-last_time_command).seconds <= 60:
                            if str(event.user_id) not in masterList:
                                await command_setu.finish("我球球你了让Zer0歇一会儿吧......爪巴涩图很累的说......")
                                return
                            else:
                                await command_setu.send("我爪巴爪巴......这就去......")
                    handle_msg = (
                        "定向涩图触发\n"
                        "触发方式：command\n"
                        f"关键词：{keywords}\n"
                        f"图片数量：{num}\n"
                        "Loading......（约15秒钟）"
                    )
                    await command_setu.send(Message(handle_msg))
                    setu = await search_setu(Keywords=keywords, num=num)
                else:
                    setu = None
        else:
            setu = None
    elif isinstance(event, PrivateMessageEvent):
        if str(event.user_id) in masterList:
            arg = str(event.get_message()).split()
            checked_type = check_tpye(arg)
            if checked_type == False:
                setu = None
                await command_setu.finish("传入了不正确的参数......\n然后指令坏掉了，Zer0处理了个寂寞")
            else:
                if arg[0] == 'random':
                    level, num = arg[1], arg[2]
                    level_zh = level_zh_dic[str(level)]
                    handle_msg = (
                        f"[CQ:at,qq={event.user_id}]随机涩图触发\n"
                        "触发方式：command\n"
                        f"图片分级：{level_zh}\n"
                        f"图片数量：{num}\n"
                        "Loading......（约15秒钟）"
                    )
                    await command_setu.send(Message(handle_msg))
                    setu = await random_setu(Rmodle='random', level=level, num=num)
                elif arg[0] == 'search':
                    keywords, num = arg[1], int(arg[2])
                    handle_msg = (
                        "定向涩图触发\n"
                        "触发方式：command\n"
                        f"关键词：{keywords}\n"
                        f"图片数量：{num}\n"
                        "Loading......（约15秒钟）"
                    )
                    await command_setu.send(Message(handle_msg))
                    setu = await search_setu(Keywords=keywords, num=num)
                else:
                    setu = None
        else:
            setu = None
    else:
        setu = None
    if setu:
        await command_setu.send('Active！！！')
        for msg in setu:
            await command_setu.send(Message(msg))
            await asyncio.sleep(0.1)
    if event.get_user_id() not in masterList and resetTime == True:
        last_time_command = datetime.datetime.now()
    download_urls.clear()
    await command_setu.finish()


@regex_setu_random.handle()  # 正则匹配到随机涩图
async def _regex_setu_random(bot: Bot, event: Event, state: dict):
    global last_time_Rrandom
    if isinstance(event, GroupMessageEvent):
        if event.group_id in [get_driver().config.GroupList['last'], get_driver().config.GroupList['test']]:
            start_time = datetime.datetime.now()  # 取现在时间
            # 用于判定程序是否为初次启动，检测last_time是否被赋值
            if isinstance(last_time_Rrandom, datetime.datetime):
                if (start_time-last_time_Rrandom).seconds <= 5:
                    if str(event.user_id) not in masterList:
                        await regex_setu_random.finish("我球球你了让Zer0歇一会儿吧......爪巴涩图很累的说......")
                        return
                    else:
                        await regex_setu_random.send("我爪巴爪巴......这就去......")
            handle_msg = (
                f"[CQ:at,qq={event.user_id}]随机涩图触发\n"
                "触发方式：regex\n"
                "图片分级：随机\n"
                "图片数量：1\n"
                "Loading......（约3秒钟）"
            )
            await regex_setu_random.send(Message(handle_msg))
            setu = await random_setu(Rmodle='regex', level=None, num=1)
        else:
            setu = None
    elif isinstance(event, PrivateMessageEvent):
        if str(event.user_id) in masterList:
            handle_msg = (
                "随机涩图触发\n"
                "触发方式：regex\n"
                "图片分级：随机\n"
                "图片数量：1\n"
                "Loading......（约3秒钟）"
            )
            await regex_setu_random.send(Message(handle_msg))
            setu = await random_setu(Rmodle='regex', level=None, num=1)
        else:
            await regex_setu_random.finish("看尼玛涩图给爷爬！")
            setu = None
    else:
        setu = None
    if setu:
        handle_msg = 'Active！！！'
        await regex_setu_random.send(Message(handle_msg))
        for msg in setu:
            await asyncio.sleep(0.1)
            await regex_setu_random.send(Message(msg))
    download_urls.clear()
    if event.get_user_id() not in masterList and resetTime == True:
        last_time_Rrandom = datetime.datetime.now()
    await regex_setu_random.finish()


@regex_setu_search.handle()  # 正则匹配到定向涩图
async def _regex_setu_search(bot: Bot, event: Event, state: dict):
    global last_time_command

    async def regex_march():
        if re.match(r'^[来整][几.\S*][张份个]\S*[色涩黄]图$', str(event.get_message())):
            key = re.findall(r'^[来整][几.\S*][张份个](\S*?)[色涩黄]图$',
                             str(event.get_message()))[0]
            num = re.findall(r'^[来整]([几.\S*]?)[张份个]\S*[色涩黄]图$',
                             str(event.get_message()))[0]
            if num == '几':
                num = random.randint(1, 10)
            elif num in word_to_int:
                num = word_to_int[num]
            else:
                await regex_setu_search.finish("呐不要意思哦~Zer0这里只有十张以内的涩图呢~~~")
        else:
            key = re.findall(r'^[来整]点(\S*?)[色涩黄]图$',
                             str(event.get_message()))[0]  # 获取关键词
            num = 1
        return (key, num)
    if isinstance(event, GroupMessageEvent):
        if event.group_id in [get_driver().config.GroupList['last'], get_driver().config.GroupList['test']]:
            start_time = datetime.datetime.now()  # 取现在时间
            # 用于判定程序是否为初次启动，检测last_time是否被赋值
            if isinstance(last_time_command, datetime.datetime):
                if (start_time-last_time_command).seconds <= 60:
                    if str(event.user_id) not in masterList:
                        await regex_setu_search.finish("我球球你了让Zer0歇一会儿吧......爪巴涩图很累的说......")
                        return
                    else:
                        await regex_setu_search.send("我爪巴爪巴......这就去......")
            result_march = await regex_march()
            key, num = result_march[0], result_march[1]
            handle_msg = (
                f"[CQ:at,qq={event.user_id}]随机涩图触发\n"
                "触发方式：regex\n"
                f"关键词：{key}\n"
                f"图片数量：{num}\n"
                "Loading......（约10秒钟）"
            )
            await regex_setu_search.send(Message(handle_msg))
            setu = await search_setu(Keywords=key, num=num)
        else:
            setu = None
    elif isinstance(event, PrivateMessageEvent):
        if str(event.user_id) in masterList:
            result_march = await regex_march()
            key, num = result_march[0], result_march[1]
            handle_msg = (
                "定向涩图触发\n"
                "触发方式：regex\n"
                f"关键词：{key}\n"
                f"图片数量：{num}\n"
                "Loading......（约10秒钟）"
            )
            await regex_setu_search.send(Message(handle_msg))
            setu = await search_setu(Keywords=key, num=num)
        else:
            await regex_setu_search.finish("看尼玛涩图给爷爬！")
            setu = None
    else:
        setu = None
    if setu:
        await regex_setu_search.send('Active！！！')
        for msg in setu:
            await asyncio.sleep(0.1)
            await regex_setu_random.send(Message(msg))
    download_urls.clear()
    if event.get_user_id() not in masterList and resetTime == True:
        last_time_command = datetime.datetime.now()
    await regex_setu_search.finish()
